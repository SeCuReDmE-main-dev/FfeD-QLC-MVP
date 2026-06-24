from __future__ import annotations

from typing import Any, Mapping, Sequence


def build_swop_chunk_protection_plan(
    swop_policy: Mapping[str, Any],
    chunk_key_schedule: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Convert SWOP regions into a future chunk protection allocation plan."""

    if swop_policy.get("schema") != "ffed.qlc.sensitivity_weighted_obfuscation_policy.v1":
        raise ValueError("SWOP chunk plan requires a SWOP policy")
    schedule_chunks = _schedule_chunks(chunk_key_schedule or {})
    regions = swop_policy.get("regions") or []
    if not isinstance(regions, Sequence) or isinstance(regions, (str, bytes, bytearray)):
        regions = []
    planned_chunks = [
        _planned_chunk(region, schedule_chunks)
        for region in regions
        if isinstance(region, Mapping)
    ]
    if not planned_chunks:
        planned_chunks = [_default_chunk(swop_policy, schedule_chunks)]
    return {
        "schema": "ffed.qlc.swop_chunk_protection_plan.v1",
        "source_policy_schema": str(swop_policy.get("schema") or ""),
        "media_type": str(swop_policy.get("media_type") or "image")[:40],
        "chunk_count": len(planned_chunks),
        "planned_chunks": planned_chunks,
        "key_material_exposed": False,
        "claim_boundary": "swop_to_chunk_allocation_plan_not_ecc_particle_or_quantum_proof_certification",
    }


def _planned_chunk(region: Mapping[str, Any], schedule_chunks: Mapping[int, Mapping[str, Any]]) -> dict[str, Any]:
    chunk_index = int(region.get("index") or 0)
    schedule = schedule_chunks.get(chunk_index, {})
    sensitivity = str(region.get("sensitivity_level") or "low")
    return {
        "logical_region_index": chunk_index,
        "chunk_range": [chunk_index, chunk_index],
        "label": str(region.get("label") or "region")[:120],
        "protection_tier": sensitivity,
        "obfuscation_intensity": str(region.get("obfuscation_intensity") or _intensity(sensitivity)),
        "recommended_chunk_mode": str(region.get("recommended_chunk_mode") or _chunk_mode(sensitivity)),
        "subkey_fingerprint": str(schedule.get("subkey_fingerprint") or "")[:64],
        "key_material_exposed": False,
    }


def _default_chunk(swop_policy: Mapping[str, Any], schedule_chunks: Mapping[int, Mapping[str, Any]]) -> dict[str, Any]:
    sensitivity = str(swop_policy.get("sensitivity_level") or "low")
    schedule = schedule_chunks.get(0, {})
    return {
        "logical_region_index": 0,
        "chunk_range": [0, 0],
        "label": "default",
        "protection_tier": sensitivity,
        "obfuscation_intensity": str(swop_policy.get("obfuscation_intensity") or _intensity(sensitivity)),
        "recommended_chunk_mode": str(swop_policy.get("recommended_chunk_mode") or _chunk_mode(sensitivity)),
        "subkey_fingerprint": str(schedule.get("subkey_fingerprint") or "")[:64],
        "key_material_exposed": False,
    }


def _schedule_chunks(schedule: Mapping[str, Any]) -> dict[int, Mapping[str, Any]]:
    chunks = schedule.get("chunks") or []
    if not isinstance(chunks, Sequence) or isinstance(chunks, (str, bytes, bytearray)):
        return {}
    output: dict[int, Mapping[str, Any]] = {}
    for fallback_index, chunk in enumerate(chunks):
        if isinstance(chunk, Mapping):
            output[int(chunk.get("chunk_index", fallback_index))] = chunk
    return output


def _intensity(sensitivity: str) -> str:
    return {
        "low": "baseline",
        "medium": "elevated",
        "high": "strong",
        "critical": "maximum",
    }.get(sensitivity, "baseline")


def _chunk_mode(sensitivity: str) -> str:
    return {
        "low": "fast_basic",
        "medium": "balanced",
        "high": "sensitive_dense",
        "critical": "critical_dense",
    }.get(sensitivity, "fast_basic")
