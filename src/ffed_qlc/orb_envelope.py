"""Redacted orb and lattice template exports."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

from .admissibility import AdmDecision
from .fractal_measurement import FractalMeasurement
from .penrose_geometry import PenrosePatch
from .plithogenic_gate import PlithogenicTileClass
from .source_functions import compile_source_function_profiles
from .tile_admission import TileAdmissionProfile


ORB_ENVELOPE_SCHEMA = "ffed.qlc.orb_envelope.v1"
LATTICE_EXPORT_SCHEMA = "ffed.qlc.redacted_lattice_export.v1"


class OrbEnvelopeError(ValueError):
    """Raised when an orb export would leak raw data or violate admission."""


@dataclass(frozen=True)
class DataEnvelopeRef:
    """Redacted data reference bound to an admitted tile."""

    chunk_id: str
    chunk_fingerprint: str
    media_type: str = "unknown"
    size_bytes: int | None = None


@dataclass(frozen=True)
class OrbEnvelope:
    """Redacted envelope around accepted local lattice tiles."""

    orb_id: str
    orb_type: str
    accepted_tile_ids: tuple[str, ...]
    suspended_tile_fingerprints: tuple[str, ...]
    rejected_tile_fingerprints: tuple[str, ...]
    tdf_summary: Mapping[str, Any]
    df_profile: Mapping[str, Any]
    plithogenic_profile: Mapping[str, Any]
    source_profile: Mapping[str, Any]
    data_envelope_fingerprint: str
    tile_data_bindings: tuple[Mapping[str, Any], ...]
    warnings: tuple[str, ...]


def build_orb_envelope(
    patch: PenrosePatch,
    admissions: Sequence[TileAdmissionProfile],
    classifications: Sequence[PlithogenicTileClass],
    measurements: Sequence[FractalMeasurement],
    data_refs: Sequence[Mapping[str, Any] | DataEnvelopeRef] | None = None,
    *,
    orb_type: str = "local_lattice_cluster",
) -> OrbEnvelope:
    """Build a deterministic redacted orb from accepted tiles and data refs."""

    admission_by_tile = {profile.tile_id: profile for profile in admissions}
    accepted_tile_ids = tuple(
        tile.tile_id
        for tile in patch.tiles
        if admission_by_tile.get(tile.tile_id)
        and admission_by_tile[tile.tile_id].Adm == AdmDecision.ACCEPT
    )
    suspended = tuple(
        profile.admission_fingerprint
        for profile in admissions
        if profile.Adm == AdmDecision.SUSPEND
    )
    rejected = tuple(
        profile.admission_fingerprint
        for profile in admissions
        if profile.Adm == AdmDecision.REJECT
    )
    refs = tuple(_normalize_data_ref(ref) for ref in (data_refs or []))
    bindings = _bind_data_refs_to_tiles(refs, accepted_tile_ids)
    warnings: list[str] = []
    if suspended:
        warnings.append("suspended_tiles_boundary_warning_only")
    if refs and not accepted_tile_ids:
        warnings.append("data_refs_unbound_no_accepted_tiles")

    data_fingerprint = _fingerprint(
        {
            "accepted_tile_ids": accepted_tile_ids,
            "bindings": bindings,
            "orb_type": orb_type,
        }
    )
    orb_id = "orb-" + _fingerprint(
        {
            "orb_type": orb_type,
            "accepted_tile_ids": accepted_tile_ids,
            "data_envelope_fingerprint": data_fingerprint,
        }
    )[:16]
    return OrbEnvelope(
        orb_id=orb_id,
        orb_type=orb_type,
        accepted_tile_ids=accepted_tile_ids,
        suspended_tile_fingerprints=suspended,
        rejected_tile_fingerprints=rejected,
        tdf_summary=_tdf_summary(admissions),
        df_profile=_df_profile(measurements),
        plithogenic_profile=_plithogenic_profile(classifications),
        source_profile=_source_profile_summary(),
        data_envelope_fingerprint=data_fingerprint,
        tile_data_bindings=bindings,
        warnings=tuple(warnings),
    )


def export_redacted_orb_json(envelope: OrbEnvelope) -> dict[str, Any]:
    """Export orb JSON without plaintext, keys, raw media, or raw source URLs."""

    return {
        "schema": ORB_ENVELOPE_SCHEMA,
        "orb_id": envelope.orb_id,
        "orb_type": envelope.orb_type,
        "accepted_tile_ids": list(envelope.accepted_tile_ids),
        "suspended_tile_fingerprints": list(envelope.suspended_tile_fingerprints),
        "rejected_tile_fingerprints": list(envelope.rejected_tile_fingerprints),
        "tdf_summary": dict(envelope.tdf_summary),
        "df_profile": dict(envelope.df_profile),
        "plithogenic_profile": dict(envelope.plithogenic_profile),
        "source_profile": dict(envelope.source_profile),
        "data_envelope_fingerprint": envelope.data_envelope_fingerprint,
        "tile_data_bindings": [dict(binding) for binding in envelope.tile_data_bindings],
        "warnings": list(envelope.warnings),
        "plaintext_embedded": False,
        "key_material_embedded": False,
        "raw_media_embedded": False,
        "raw_source_urls_included": False,
        "claim_boundary": "orb_envelope_redacted_not_key_storage_or_crypto_certification",
    }


def export_redacted_lattice_json(
    patch: PenrosePatch,
    admissions: Sequence[TileAdmissionProfile],
    envelope: OrbEnvelope,
) -> dict[str, Any]:
    """Export redacted lattice metadata."""

    return {
        "schema": LATTICE_EXPORT_SCHEMA,
        "patch_metadata": dict(patch.metadata),
        "accepted_tile_ids": list(envelope.accepted_tile_ids),
        "admission_ledger_fingerprints": [
            profile.admission_fingerprint for profile in admissions
        ],
        "orb": export_redacted_orb_json(envelope),
        "plaintext_embedded": False,
        "key_material_embedded": False,
        "raw_media_embedded": False,
        "raw_source_urls_included": False,
    }


def export_lattice_template_markdown() -> str:
    """Return reusable markdown template for VAD and related tools."""

    return "\n".join(
        [
            "# FfeD QLC Redacted Lattice Template",
            "",
            "- schema: `ffed.qlc.redacted_lattice_export.v1`",
            "- inputs: accepted tile ids, admission fingerprints, source fingerprints",
            "- forbidden: plaintext, key material, raw media, raw OCR, raw source bodies",
            "- reusable_by: VAD and graph/plithogenic classification tools",
        ]
    )


def export_lattice_json_schema() -> dict[str, Any]:
    """Return compact JSON schema for the redacted lattice export."""

    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "FfeD QLC Redacted Lattice Export",
        "type": "object",
        "required": ["schema", "patch_metadata", "accepted_tile_ids", "orb"],
        "properties": {
            "schema": {"const": LATTICE_EXPORT_SCHEMA},
            "patch_metadata": {"type": "object"},
            "accepted_tile_ids": {"type": "array", "items": {"type": "string"}},
            "admission_ledger_fingerprints": {"type": "array", "items": {"type": "string"}},
            "orb": {"type": "object"},
            "plaintext_embedded": {"const": False},
            "key_material_embedded": {"const": False},
            "raw_media_embedded": {"const": False},
        },
    }


def export_lattice_typescript_shape() -> str:
    """Return TypeScript shape for downstream apps."""

    return "\n".join(
        [
            "export type FfedQlcRedactedLattice = {",
            "  schema: 'ffed.qlc.redacted_lattice_export.v1';",
            "  patch_metadata: Record<string, unknown>;",
            "  accepted_tile_ids: string[];",
            "  admission_ledger_fingerprints: string[];",
            "  orb: Record<string, unknown>;",
            "  plaintext_embedded: false;",
            "  key_material_embedded: false;",
            "  raw_media_embedded: false;",
            "};",
        ]
    )


def export_lattice_python_shape() -> str:
    """Return Python TypedDict shape for downstream tools."""

    return "\n".join(
        [
            "class FfedQlcRedactedLattice(TypedDict):",
            "    schema: Literal['ffed.qlc.redacted_lattice_export.v1']",
            "    patch_metadata: dict[str, object]",
            "    accepted_tile_ids: list[str]",
            "    admission_ledger_fingerprints: list[str]",
            "    orb: dict[str, object]",
            "    plaintext_embedded: Literal[False]",
            "    key_material_embedded: Literal[False]",
            "    raw_media_embedded: Literal[False]",
        ]
    )


def export_vad_reusable_template() -> dict[str, Any]:
    """Return the reusable VAD template bundle."""

    return {
        "markdown": export_lattice_template_markdown(),
        "json_schema": export_lattice_json_schema(),
        "typescript_shape": export_lattice_typescript_shape(),
        "python_shape": export_lattice_python_shape(),
        "raw_payload_allowed": False,
    }


def _normalize_data_ref(ref: Mapping[str, Any] | DataEnvelopeRef) -> DataEnvelopeRef:
    if isinstance(ref, DataEnvelopeRef):
        return ref
    forbidden = {"plaintext", "raw_payload", "raw_media", "key_material", "secret"}
    present_forbidden = sorted(forbidden.intersection(ref))
    if present_forbidden:
        raise OrbEnvelopeError(f"raw or secret data fields are forbidden: {present_forbidden}")
    chunk_id = str(ref.get("chunk_id") or "").strip()
    chunk_fingerprint = str(ref.get("chunk_fingerprint") or "").strip()
    if not chunk_id or not chunk_fingerprint:
        raise OrbEnvelopeError("data refs require chunk_id and chunk_fingerprint")
    return DataEnvelopeRef(
        chunk_id=chunk_id,
        chunk_fingerprint=chunk_fingerprint,
        media_type=str(ref.get("media_type") or "unknown"),
        size_bytes=int(ref["size_bytes"]) if ref.get("size_bytes") is not None else None,
    )


def _bind_data_refs_to_tiles(
    refs: Sequence[DataEnvelopeRef],
    accepted_tile_ids: Sequence[str],
) -> tuple[Mapping[str, Any], ...]:
    if refs and not accepted_tile_ids:
        return tuple()
    bindings: list[dict[str, Any]] = []
    for index, ref in enumerate(refs):
        tile_id = accepted_tile_ids[index % len(accepted_tile_ids)]
        bindings.append(
            {
                "tile_id": tile_id,
                "chunk_id": ref.chunk_id,
                "chunk_fingerprint": ref.chunk_fingerprint,
                "media_type": ref.media_type,
                "size_bytes": ref.size_bytes,
                "binding_fingerprint": _fingerprint(
                    {
                        "tile_id": tile_id,
                        "chunk_id": ref.chunk_id,
                        "chunk_fingerprint": ref.chunk_fingerprint,
                    }
                ),
            }
        )
    return tuple(bindings)


def _tdf_summary(admissions: Sequence[TileAdmissionProfile]) -> dict[str, Any]:
    values = tuple(admissions)
    if not values:
        return {"count": 0}
    return {
        "count": len(values),
        "T_tile_avg": sum(profile.T_tile for profile in values) / len(values),
        "dF_available_count": sum(1 for profile in values if profile.dF_tile is not None),
        "F_tile_max": max(profile.F_tile for profile in values),
        "accepted_count": sum(1 for profile in values if profile.Adm == AdmDecision.ACCEPT),
        "suspended_count": sum(1 for profile in values if profile.Adm == AdmDecision.SUSPEND),
        "rejected_count": sum(1 for profile in values if profile.Adm == AdmDecision.REJECT),
    }


def _df_profile(measurements: Sequence[FractalMeasurement]) -> dict[str, Any]:
    available = [measurement for measurement in measurements if measurement.D_f is not None]
    if not available:
        return {"measurement_count": len(measurements), "available_count": 0}
    return {
        "measurement_count": len(measurements),
        "available_count": len(available),
        "D_f_avg": sum(measurement.D_f or 0.0 for measurement in available) / len(available),
        "D_f_hat_avg": sum(measurement.D_f_hat or 0.0 for measurement in available) / len(available),
        "confidence_avg": sum(measurement.confidence for measurement in available) / len(available),
    }


def _plithogenic_profile(classifications: Sequence[PlithogenicTileClass]) -> dict[str, Any]:
    if not classifications:
        return {"classification_count": 0}
    return {
        "classification_count": len(classifications),
        "C_phi_avg": sum(item.C_phi for item in classifications) / len(classifications),
        "audit_fingerprints": [item.audit_fingerprint for item in classifications],
        "raw_tif_exported": False,
    }


def _source_profile_summary() -> dict[str, Any]:
    profiles = compile_source_function_profiles()
    return {
        "source_count": len(profiles),
        "source_ids": [profile.source_id for profile in profiles],
        "source_fingerprints": [profile.source_fingerprint for profile in profiles],
        "raw_source_urls_included": False,
    }


def _fingerprint(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
