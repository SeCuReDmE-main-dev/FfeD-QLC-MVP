"""Plithogenic classification gate for Penrose tiles."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

from .admissibility import AdmDecision
from .penrose_geometry import PHI, PenroseTile, validate_penrose_tile
from .source_functions import (
    REQUIRED_SOURCE_IDS,
    SourceFunctionError,
    SourceFunctionProfile,
    require_source_function_ids,
)


PLITHOGENIC_TILE_CLASS_SCHEMA = "ffed.qlc.plithogenic_tile_class.v1"


@dataclass(frozen=True)
class PlithogenicTileClass:
    """Numeric plithogenic classification for one Penrose tile."""

    tile_id: str
    tile_type: str
    Attr: tuple[str, ...]
    Val: tuple[float, ...]
    Dom: tuple[float, ...]
    Contr: tuple[float, ...]
    C_phi: float
    Adm: AdmDecision
    admissibility_score: float
    source_ids: tuple[str, ...]
    source_contradiction: float
    tile_edge_friction: float
    tile_neighbor_friction: float
    connector_friction: float
    admission_precheck: bool
    reason_codes: tuple[str, ...]
    audit_fingerprint: str
    raw_tif_exported: bool = False


@dataclass(frozen=True)
class InfSupGate:
    """Infimum/supremum confidence gate for numeric attribute values."""

    lower_bound: float
    upper_bound: float
    interval_width: float
    admission_confidence: float


def classify_plithogenic_tile(
    tile: PenroseTile,
    *,
    source_function_ids: Iterable[str] = REQUIRED_SOURCE_IDS,
    neighbor_tiles: Sequence[PenroseTile] | None = None,
    connector_size: int = 1,
    provenance_present: bool = True,
    claim_scope: str = "bounded_research",
) -> PlithogenicTileClass:
    """Classify a tile through numeric plithogenic contradiction and friction."""

    requested_source_ids = tuple(source_function_ids)
    reason_codes: list[str] = []
    try:
        source_profiles = require_source_function_ids(requested_source_ids)
    except SourceFunctionError:
        source_profiles = tuple()
        reason_codes.append("missing_source_function_profile")

    geometry = validate_penrose_tile(tile)
    if not geometry.valid:
        reason_codes.append("invalid_penrose_geometry")
    if not provenance_present:
        reason_codes.append("missing_provenance")
    if claim_scope in {"security_certification", "quantum_proof", "production_crypto_claim"}:
        reason_codes.append("unsafe_claim_scope")

    attr = (
        "tile_type",
        "edge_balance",
        "angle_profile",
        "source_profile",
        "friction",
    )
    val = _tile_values(tile, source_profiles, geometry.valid, neighbor_tiles, connector_size)
    dom = (1.0, 1.0, 1.0, 1.0, 0.0)
    contr = numeric_dissimilarity_vector(val, dom)
    c_phi = phi_weighted_contradiction(contr)
    edge_friction = _edge_friction(geometry)
    neighbor_friction = _neighbor_friction(neighbor_tiles)
    connector_friction = _connector_friction(connector_size)
    source_contr = source_contradiction(source_profiles, requested_source_ids)
    inf_sup = inf_sup_gate(val)

    admissibility_score = _clamp01(
        (1.0 - c_phi) * 0.45
        + inf_sup.admission_confidence * 0.20
        + (1.0 - source_contr) * 0.20
        + (1.0 - ((edge_friction + neighbor_friction + connector_friction) / 3.0)) * 0.15
    )
    admission_precheck = (
        geometry.valid
        and provenance_present
        and bool(source_profiles)
        and "unsafe_claim_scope" not in reason_codes
    )
    adm = _admission_decision(admission_precheck, admissibility_score, reason_codes)
    if adm == AdmDecision.ACCEPT:
        reason_codes.append("true_to_scaffold")
    elif adm == AdmDecision.SUSPEND and "missing_provenance" not in reason_codes:
        reason_codes.append("plithogenic_score_requires_review")
    elif adm == AdmDecision.REJECT and not reason_codes:
        reason_codes.append("plithogenic_score_below_reject_threshold")

    audit_payload = {
        "tile_id": tile.tile_id,
        "tile_type": tile.tile_type,
        "Attr": attr,
        "Contr": [round(value, 12) for value in contr],
        "C_phi": round(c_phi, 12),
        "Adm": adm.value,
        "reason_codes": reason_codes,
        "source_ids": tuple(profile.source_id for profile in source_profiles),
    }
    audit_fingerprint = hashlib.sha256(
        json.dumps(audit_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return PlithogenicTileClass(
        tile_id=tile.tile_id,
        tile_type=tile.tile_type,
        Attr=attr,
        Val=val,
        Dom=dom,
        Contr=contr,
        C_phi=c_phi,
        Adm=adm,
        admissibility_score=admissibility_score,
        source_ids=tuple(profile.source_id for profile in source_profiles),
        source_contradiction=source_contr,
        tile_edge_friction=edge_friction,
        tile_neighbor_friction=neighbor_friction,
        connector_friction=connector_friction,
        admission_precheck=admission_precheck,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        audit_fingerprint=audit_fingerprint,
    )


def numeric_dissimilarity_vector(
    values: Sequence[float],
    dominant_values: Sequence[float],
) -> tuple[float, ...]:
    """Return per-attribute numeric contradiction values in [0, 1]."""

    if len(values) != len(dominant_values):
        raise ValueError("values and dominant_values must have the same length")
    return tuple(
        _clamp01(abs(_clamp01(value) - _clamp01(dominant)))
        for value, dominant in zip(values, dominant_values)
    )


def phi_weighted_contradiction(contradictions: Sequence[float]) -> float:
    """Compute a phi-weighted contradiction scalar."""

    if not contradictions:
        return 1.0
    weights = [PHI ** (index / max(1, len(contradictions) - 1)) for index in range(len(contradictions))]
    weighted_sum = sum(_clamp01(value) * weight for value, weight in zip(contradictions, weights))
    return _clamp01(weighted_sum / sum(weights))


def prevalence_resolve(
    candidates: Mapping[str, float],
    prevalence_order: Sequence[str],
) -> tuple[str, float]:
    """Resolve conflicting candidates by prevalence order, then score."""

    if not candidates:
        raise ValueError("candidates must not be empty")
    order_index = {name: index for index, name in enumerate(prevalence_order)}
    return min(
        ((name, _clamp01(score)) for name, score in candidates.items()),
        key=lambda item: (order_index.get(item[0], len(order_index)), -item[1], item[0]),
    )


def inf_sup_gate(values: Sequence[float]) -> InfSupGate:
    """Compute interval width and confidence from plithogenic values."""

    if not values:
        return InfSupGate(0.0, 1.0, 1.0, 0.0)
    bounded = tuple(_clamp01(value) for value in values)
    lower = min(bounded)
    upper = max(bounded)
    width = _clamp01(upper - lower)
    return InfSupGate(
        lower_bound=lower,
        upper_bound=upper,
        interval_width=width,
        admission_confidence=1.0 - width,
    )


def source_contradiction(
    source_profiles: Sequence[SourceFunctionProfile],
    requested_source_ids: Sequence[str],
) -> float:
    """Return contradiction introduced by missing or low-weight source profiles."""

    if not requested_source_ids:
        return 1.0
    present_ids = {profile.source_id for profile in source_profiles}
    missing_ratio = 1.0 - (len(present_ids) / len(tuple(requested_source_ids)))
    if not source_profiles:
        return 1.0
    average_weight = sum(profile.source_weight for profile in source_profiles) / len(source_profiles)
    return _clamp01((missing_ratio * 0.70) + ((1.0 - average_weight) * 0.30))


def export_plithogenic_tile_classification(
    classification: PlithogenicTileClass,
) -> dict[str, Any]:
    """Export plithogenic classification without raw T/I/F values."""

    return {
        "schema": PLITHOGENIC_TILE_CLASS_SCHEMA,
        "tile_id": classification.tile_id,
        "tile_type": classification.tile_type,
        "Attr": list(classification.Attr),
        "Val": [round(value, 12) for value in classification.Val],
        "Dom": [round(value, 12) for value in classification.Dom],
        "Contr": [round(value, 12) for value in classification.Contr],
        "C_phi": round(classification.C_phi, 12),
        "Adm": classification.Adm.value,
        "admissibility_score": round(classification.admissibility_score, 12),
        "source_ids": list(classification.source_ids),
        "friction": {
            "tile_edge": classification.tile_edge_friction,
            "tile_neighbor": classification.tile_neighbor_friction,
            "connector": classification.connector_friction,
        },
        "reason_codes": list(classification.reason_codes),
        "audit_fingerprint": classification.audit_fingerprint,
        "raw_tif_exported": False,
        "claim_boundary": "plithogenic_classification_not_raw_tif_or_security_certification",
    }


def _tile_values(
    tile: PenroseTile,
    source_profiles: Sequence[SourceFunctionProfile],
    geometry_valid: bool,
    neighbor_tiles: Sequence[PenroseTile] | None,
    connector_size: int,
) -> tuple[float, float, float, float, float]:
    geometry = validate_penrose_tile(tile)
    type_value = 1.0 if tile.tile_type == "thick" else 1.0 / PHI
    length_span = max(geometry.edge_lengths) - min(geometry.edge_lengths)
    edge_balance = 1.0 - _clamp01(length_span)
    angle_profile = 1.0 if geometry_valid else 0.0
    source_profile = _clamp01(len(source_profiles) / len(REQUIRED_SOURCE_IDS))
    friction = (1.0 - _neighbor_friction(neighbor_tiles) + 1.0 - _connector_friction(connector_size)) / 2.0
    return (
        _clamp01(type_value),
        _clamp01(edge_balance),
        _clamp01(angle_profile),
        _clamp01(source_profile),
        _clamp01(1.0 - friction),
    )


def _edge_friction(geometry: Any) -> float:
    if not geometry.valid:
        return 1.0
    length_span = max(geometry.edge_lengths) - min(geometry.edge_lengths)
    return _clamp01(length_span)


def _neighbor_friction(neighbor_tiles: Sequence[PenroseTile] | None) -> float:
    count = len(neighbor_tiles or [])
    if count == 0:
        return 0.25
    return _clamp01(abs(count - 2) / 4.0)


def _connector_friction(connector_size: int) -> float:
    if connector_size < 1:
        return 1.0
    return _clamp01(max(0, connector_size - 5) / 10.0)


def _admission_decision(
    admission_precheck: bool,
    admissibility_score: float,
    reason_codes: Sequence[str],
) -> AdmDecision:
    if "unsafe_claim_scope" in reason_codes or "invalid_penrose_geometry" in reason_codes:
        return AdmDecision.REJECT
    if "missing_source_function_profile" in reason_codes:
        return AdmDecision.REJECT
    if "missing_provenance" in reason_codes:
        return AdmDecision.SUSPEND
    if not admission_precheck:
        return AdmDecision.SUSPEND
    if admissibility_score >= 0.65:
        return AdmDecision.ACCEPT
    if admissibility_score >= 0.35:
        return AdmDecision.SUSPEND
    return AdmDecision.REJECT


def _clamp01(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return min(1.0, max(0.0, numeric))
