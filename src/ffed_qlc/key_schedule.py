from __future__ import annotations

import json
from hashlib import blake2b
from typing import Any, Mapping


MAGIC = b"FQLC1\n"
HEADER_LENGTH_BYTES = 4


def derive_chunk_key_schedule(container_or_manifest: bytes | Mapping[str, Any], chunk_count: int) -> dict[str, Any]:
    """Return deterministic chunk subkey fingerprints without exposing key bytes."""

    if chunk_count < 0:
        raise ValueError("chunk_count must be non-negative")
    manifest = _extract_manifest(container_or_manifest)
    source_hash = str(manifest.get("source_sha256") or "")
    lattice_seed = str(manifest.get("lattice_seed_fingerprint") or "")
    projection = manifest.get("projection_profile") or {}
    projection_seed = str(projection.get("projection_seed_fingerprint") or "")
    schedule_seed = f"{source_hash}:{lattice_seed}:{projection_seed}:granular_chunk_key_schedule_v1"
    chunks = [
        {
            "chunk_index": index,
            "subkey_fingerprint": blake2b(f"{schedule_seed}:{index}".encode("utf-8"), digest_size=16).hexdigest(),
            "key_material_exposed": False,
        }
        for index in range(chunk_count)
    ]
    return {
        "schema": "ffed.qlc.granular_chunk_key_schedule.v1",
        "chunk_count": chunk_count,
        "derivation": "blake2b_fingerprint_only_mvp",
        "key_material_exposed": False,
        "chunks": chunks,
    }


def _extract_manifest(container_or_manifest: bytes | Mapping[str, Any]) -> Mapping[str, Any]:
    if isinstance(container_or_manifest, bytes):
        return _manifest_from_container(container_or_manifest)
    if "qlc_manifest" in container_or_manifest and isinstance(container_or_manifest["qlc_manifest"], Mapping):
        return container_or_manifest["qlc_manifest"]
    return container_or_manifest


def _manifest_from_container(container: bytes) -> Mapping[str, Any]:
    if not container.startswith(MAGIC):
        raise ValueError("invalid QLC container magic")
    offset = len(MAGIC)
    if len(container) < offset + HEADER_LENGTH_BYTES:
        raise ValueError("truncated QLC container header")
    header_length = int.from_bytes(container[offset : offset + HEADER_LENGTH_BYTES], "big")
    header_start = offset + HEADER_LENGTH_BYTES
    header_end = header_start + header_length
    if len(container) < header_end:
        raise ValueError("truncated QLC container body")
    try:
        header_str = container[header_start:header_end].decode("utf-8")
        header = json.loads(header_str)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid QLC container header JSON") from exc
    if not isinstance(header, dict):
        raise ValueError("QLC container header must be a JSON object")
    manifest = header.get("qlc_manifest")
    if not isinstance(manifest, Mapping):
        raise ValueError("QLC container has no qlc_manifest")
    return manifest
