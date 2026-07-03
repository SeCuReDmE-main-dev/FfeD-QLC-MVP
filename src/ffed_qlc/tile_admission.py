"""T,dF,F tile admission for Penrose QLC builds."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

from .admissibility import AdmDecision
from .fractal_measurement import FractalMeasurement
from .penrose_geometry import PenrosePatch, PenroseTile, validate_penrose_tile
from .plithogenic_gate import PlithogenicTileClass
from .source_functions import REQUIRED_SOURCE_IDS


TDF_ADMISSION_SCHEMA = "ffed.qlc.tile_tdf_admission.v1"


@dataclass(frozen=True)
class TileAdmissionThresholds:
    """Threshold contract for T,dF,F admission."""

    accept_threshold: float = 0.65
    suspend_threshold: float = 0.35
    reject_false_threshold: float = 0.72
    dF_min_build: float = 0.0
    dF_max_build: float = 1.0


@dataclass(frozen=True)
class TileAdmissionProfile:
    """Admission result for one tile."""

    tile_id: str
    tile_type: str
    T_tile: float
    dF_tile: float | None
    F_tile: float
    Adm: AdmDecision
    approved_for_lattice: bool
    reason_codes: tuple[str, ...]
    admission_fingerprint: str
    ledger_entry: Mapping[str, Any]
    raw_tif_exported: bool = False


def compute_t_df_f(
    tile: PenroseTile,
    classification: PlithogenicTileClass,
    fractal_measurement: FractalMeasurement,
    *,
    thresholds: TileAdmissionThresholds | None = None,
    raw_export_requested: bool = False,
) -> TileAdmissionProfile:
    """Compute T_tile, dF_tile, F_tile and final admission decision."""

    active_thresholds = thresholds or TileAdmissionThresholds()
    _validate_thresholds(active_thresholds)
    geometry = validate_penrose_tile(tile)
    reason_codes: list[str] = []

    if not geometry.valid:
        reason_codes.append("invalid_penrose_geometry")
    if len(classification.source_ids) < len(REQUIRED_SOURCE_IDS):
        reason_codes.append("missing_source_function_profile")
    if raw_export_requested:
        reason_codes.append("raw_export_request_rejected")

    dF_tile = fractal_measurement.dF
    if dF_tile is None:
        reason_codes.append("unavailable_dF")
    if fractal_measurement.I_system_source != "I_system^S.fractal_geometry":
        reason_codes.append("non_fractal_i_system_source")

    T_tile = _compute_t_tile(geometry.valid, classification, fractal_measurement)
    F_tile = _compute_f_tile(geometry.valid, classification, fractal_measurement)
    if F_tile >= active_thresholds.reject_false_threshold:
        reason_codes.append("high_F_tile")
    if dF_tile is not None and not (
        active_thresholds.dF_min_build <= dF_tile <= active_thresholds.dF_max_build
    ):
        reason_codes.append("dF_out_of_build_band")

    adm = _admit_from_profile(
        T_tile=T_tile,
        dF_tile=dF_tile,
        F_tile=F_tile,
        thresholds=active_thresholds,
        reason_codes=reason_codes,
    )
    if adm == AdmDecision.ACCEPT:
        reason_codes.append("accepted_true_to_scaffold")
    elif adm == AdmDecision.SUSPEND and not reason_codes:
        reason_codes.append("admission_requires_review")
    elif adm == AdmDecision.REJECT and not reason_codes:
        reason_codes.append("admission_rejected_by_threshold")

    fingerprint_payload = {
        "tile_id": tile.tile_id,
        "tile_type": tile.tile_type,
        "T_tile": round(T_tile, 12),
        "dF_tile": None if dF_tile is None else round(dF_tile, 12),
        "F_tile": round(F_tile, 12),
        "Adm": adm.value,
        "reason_codes": tuple(dict.fromkeys(reason_codes)),
    }
    admission_fingerprint = hashlib.sha256(
        json.dumps(fingerprint_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    ledger_entry = {
        "schema": "ffed.qlc.tile_admission_ledger_entry.v1",
        "tile_id": tile.tile_id,
        "admission_fingerprint": admission_fingerprint,
        "Adm": adm.value,
        "approved_for_lattice": adm == AdmDecision.ACCEPT,
        "reason_codes": list(dict.fromkeys(reason_codes)),
        "raw_tif_exported": False,
    }
    return TileAdmissionProfile(
        tile_id=tile.tile_id,
        tile_type=tile.tile_type,
        T_tile=T_tile,
        dF_tile=dF_tile,
        F_tile=F_tile,
        Adm=adm,
        approved_for_lattice=adm == AdmDecision.ACCEPT,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        admission_fingerprint=admission_fingerprint,
        ledger_entry=ledger_entry,
    )


def approved_lattice_tiles(
    tiles: Iterable[PenroseTile],
    admissions: Iterable[TileAdmissionProfile],
) -> tuple[PenroseTile, ...]:
    """Return only tiles accepted by the T,dF,F gate."""

    accepted_ids = {profile.tile_id for profile in admissions if profile.approved_for_lattice}
    return tuple(tile for tile in tiles if tile.tile_id in accepted_ids)


def build_tile_admission_ledger(
    admissions: Iterable[TileAdmissionProfile],
) -> dict[str, Any]:
    """Build a deterministic admission ledger."""

    entries = sorted(
        (dict(profile.ledger_entry) for profile in admissions),
        key=lambda entry: str(entry["tile_id"]),
    )
    return {
        "schema": "ffed.qlc.tile_admission_ledger.v1",
        "entry_count": len(entries),
        "accepted_count": sum(1 for entry in entries if entry["approved_for_lattice"]),
        "entries": entries,
        "raw_tif_exported": False,
        "claim_boundary": "tdf_admission_ledger_not_raw_tif_or_crypto_certification",
    }


def export_tile_admission_profile(profile: TileAdmissionProfile) -> dict[str, Any]:
    """Export T,dF,F admission without raw universal T/I/F vectors."""

    return {
        "schema": TDF_ADMISSION_SCHEMA,
        "tile_id": profile.tile_id,
        "tile_type": profile.tile_type,
        "T_tile": profile.T_tile,
        "dF_tile": profile.dF_tile,
        "F_tile": profile.F_tile,
        "Adm": profile.Adm.value,
        "approved_for_lattice": profile.approved_for_lattice,
        "reason_codes": list(profile.reason_codes),
        "admission_fingerprint": profile.admission_fingerprint,
        "ledger_entry": dict(profile.ledger_entry),
        "raw_tif_exported": False,
        "claim_boundary": "tile_admission_uses_T_dF_F_not_raw_universal_TIF",
    }


def validate_approved_lattice_only(
    patch: PenrosePatch,
    admissions: Iterable[TileAdmissionProfile],
) -> dict[str, Any]:
    """Validate that the lattice output contains only accepted tiles."""

    approved = approved_lattice_tiles(patch.tiles, admissions)
    return {
        "schema": "ffed.qlc.approved_lattice_filter.v1",
        "input_tile_count": len(patch.tiles),
        "approved_tile_count": len(approved),
        "approved_tile_ids": [tile.tile_id for tile in approved],
        "rejected_or_suspended_count": len(patch.tiles) - len(approved),
    }


def _compute_t_tile(
    geometry_valid: bool,
    classification: PlithogenicTileClass,
    fractal_measurement: FractalMeasurement,
) -> float:
    geometry_score = 1.0 if geometry_valid else 0.0
    fractal_score = fractal_measurement.D_f_hat if fractal_measurement.D_f_hat is not None else 0.0
    return _clamp01(
        geometry_score * 0.30
        + classification.admissibility_score * 0.45
        + fractal_score * 0.25
    )


def _compute_f_tile(
    geometry_valid: bool,
    classification: PlithogenicTileClass,
    fractal_measurement: FractalMeasurement,
) -> float:
    geometry_false = 0.0 if geometry_valid else 1.0
    missing_fractal = 0.0 if fractal_measurement.dF is not None else 0.45
    return _clamp01(
        geometry_false * 0.45
        + classification.C_phi * 0.35
        + (1.0 - classification.admissibility_score) * 0.10
        + missing_fractal
    )


def _admit_from_profile(
    *,
    T_tile: float,
    dF_tile: float | None,
    F_tile: float,
    thresholds: TileAdmissionThresholds,
    reason_codes: Sequence[str],
) -> AdmDecision:
    rejecting_reasons = {
        "invalid_penrose_geometry",
        "missing_source_function_profile",
        "raw_export_request_rejected",
        "high_F_tile",
    }
    if any(reason in rejecting_reasons for reason in reason_codes):
        return AdmDecision.REJECT
    if dF_tile is None:
        return AdmDecision.SUSPEND
    if "non_fractal_i_system_source" in reason_codes or "dF_out_of_build_band" in reason_codes:
        return AdmDecision.SUSPEND
    if T_tile >= thresholds.accept_threshold and F_tile < thresholds.reject_false_threshold:
        return AdmDecision.ACCEPT
    if T_tile >= thresholds.suspend_threshold:
        return AdmDecision.SUSPEND
    return AdmDecision.REJECT


def _validate_thresholds(thresholds: TileAdmissionThresholds) -> None:
    if thresholds.accept_threshold < thresholds.suspend_threshold:
        raise ValueError("accept_threshold must be >= suspend_threshold")
    if thresholds.dF_max_build < thresholds.dF_min_build:
        raise ValueError("dF_max_build must be >= dF_min_build")


def _clamp01(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return min(1.0, max(0.0, numeric))
