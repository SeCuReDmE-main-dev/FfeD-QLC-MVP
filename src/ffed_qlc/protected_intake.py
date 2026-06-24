from __future__ import annotations

import hashlib
import json
from typing import Any, Literal, Mapping, Sequence


MediaType = Literal["image", "document", "video"]
FORBIDDEN_INTAKE_FIELDS = {
    "api_key",
    "authorization",
    "credential",
    "image_bytes",
    "ocr_text",
    "password",
    "private_key",
    "raw_image",
    "raw_ocr",
    "raw_payload",
    "raw_secret",
    "screenshot",
    "screenshots",
    "secret",
    "token",
    "video_bytes",
}


def build_multimodal_protected_intake_descriptor(
    media_type: MediaType,
    source_id: str,
    source_fingerprint: str,
    detections: Sequence[Mapping[str, Any]] | None = None,
    context_signals: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Normalize media intake metadata before SWOP without embedding raw media."""

    active_media_type = _normalize_media_type(media_type)
    if not source_id.strip():
        raise ValueError("source_id must not be empty")
    if not source_fingerprint.strip():
        raise ValueError("source_fingerprint must not be empty")
    active_detections = list(detections or [])
    active_context = list(context_signals or [])
    _reject_forbidden_fields(active_detections)
    _reject_forbidden_fields(active_context)

    labels = [_label_for(detection) for detection in active_detections]
    return {
        "schema": "ffed.qlc.multimodal_protected_intake_descriptor.v1",
        "media_type": active_media_type,
        "source_id": source_id[:160],
        "source_fingerprint": source_fingerprint[:128],
        "region_count": len(active_detections),
        "page_count": _unique_count(active_detections, "page_index") if active_media_type == "document" else 0,
        "frame_count": _unique_count(active_detections, "frame_index") if active_media_type == "video" else 0,
        "detector_metadata": {
            "detection_count": len(active_detections),
            "context_signal_count": len(active_context),
            "labels": sorted(set(labels)),
            "detection_fingerprints": [_stable_hash(detection)[:16] for detection in active_detections],
        },
        "raw_media_embedded": False,
        "claim_boundary": "metadata_only_multimodal_intake_not_yolo_ocr_or_video_engine",
    }


def _normalize_media_type(media_type: str) -> MediaType:
    normalized = (media_type or "image").lower().strip()
    if normalized not in {"image", "document", "video"}:
        raise ValueError("media_type must be image, document, or video")
    return normalized  # type: ignore[return-value]


def _reject_forbidden_fields(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in FORBIDDEN_INTAKE_FIELDS and normalized != "secret_manager_ref":
                raise ValueError(f"raw intake field is not allowed: {key}")
            _reject_forbidden_fields(nested)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _reject_forbidden_fields(item)


def _label_for(detection: Mapping[str, Any]) -> str:
    return str(detection.get("class_name") or detection.get("label") or detection.get("name") or "object")[:120]


def _unique_count(detections: Sequence[Mapping[str, Any]], key: str) -> int:
    values = {str(detection.get(key)) for detection in detections if detection.get(key) is not None}
    return len(values)


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
