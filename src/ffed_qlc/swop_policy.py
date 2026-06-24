from __future__ import annotations

from typing import Any, Literal, Mapping, Sequence


MediaType = Literal["image", "document", "video"]
SensitivityLevel = Literal["low", "medium", "high", "critical"]

CONTEXT_METRICS = ("texture_complexity", "entropy_score", "edge_density")
FORBIDDEN_SWOP_FIELDS = {
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
LABEL_BASE_SENSITIVITY: dict[str, float] = {
    "license_plate": 0.95,
    "id_card": 0.95,
    "qr_code": 0.90,
    "wallet": 0.90,
    "private_key": 1.0,
    "token": 1.0,
    "secret": 1.0,
    "face": 0.78,
    "document_text": 0.62,
    "screen": 0.55,
    "terminal": 0.70,
    "dashboard": 0.55,
    "default": 0.25,
}
CRITICAL_LABELS = {"license_plate", "id_card", "qr_code", "wallet", "private_key", "token", "secret"}
HIGH_LABELS = {"face", "terminal"}


def build_sensitivity_weighted_obfuscation_policy(
    media_type: MediaType,
    detections: Sequence[Mapping[str, Any]] | None = None,
    context_signals: Sequence[Mapping[str, Any]] | None = None,
    semantic_map: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Recommend QLC obfuscation intensity from media metadata only."""

    active_media_type = _normalize_media_type(media_type)
    _reject_forbidden_fields(detections or [])
    _reject_forbidden_fields(context_signals or [])
    if semantic_map is not None:
        _reject_forbidden_fields(semantic_map)

    semantic_regions = _semantic_regions_by_index(semantic_map or {})
    signal_by_index = {index: signal for index, signal in enumerate(context_signals or [])}
    regions = []
    for index, detection in enumerate(detections or []):
        label = str(detection.get("class_name") or detection.get("label") or detection.get("name") or "default")[:120]
        confidence = _clamp01(detection.get("confidence_score", detection.get("confidence", 0.0)))
        context_score = _context_score(signal_by_index.get(index, {}))
        semantic_boost = _semantic_boost(semantic_regions.get(index, {}))
        sensitivity_score = _sensitivity_score(label, confidence, context_score, semantic_boost)
        sensitivity_level = _sensitivity_level(sensitivity_score)
        regions.append(
            {
                "index": index,
                "label": label,
                "confidence": confidence,
                "context_score": context_score,
                "semantic_boost": semantic_boost,
                "sensitivity_score": sensitivity_score,
                "sensitivity_level": sensitivity_level,
                "obfuscation_intensity": _obfuscation_intensity(sensitivity_level),
                "recommended_chunk_mode": _chunk_mode(active_media_type, sensitivity_level),
            }
        )

    max_level = _max_sensitivity(region["sensitivity_level"] for region in regions)
    return {
        "schema": "ffed.qlc.sensitivity_weighted_obfuscation_policy.v1",
        "media_type": active_media_type,
        "sensitivity_level": max_level,
        "obfuscation_intensity": _obfuscation_intensity(max_level),
        "recommended_chunk_mode": _chunk_mode(active_media_type, max_level),
        "raw_media_embedded": False,
        "regions": regions,
        "claim_boundary": "metadata_only_obfuscation_policy_signal_not_cryptographic_certification",
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
            if normalized in FORBIDDEN_SWOP_FIELDS and normalized != "secret_manager_ref":
                raise ValueError(f"raw SWOP field is not allowed: {key}")
            _reject_forbidden_fields(nested)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _reject_forbidden_fields(item)


def _semantic_regions_by_index(semantic_map: Mapping[str, Any]) -> dict[int, Mapping[str, Any]]:
    regions = semantic_map.get("regions") or []
    if not isinstance(regions, Sequence) or isinstance(regions, (str, bytes, bytearray)):
        return {}
    output: dict[int, Mapping[str, Any]] = {}
    for fallback_index, region in enumerate(regions):
        if isinstance(region, Mapping):
            output[int(region.get("index", fallback_index))] = region
    return output


def _context_score(signal: Mapping[str, Any]) -> float:
    values = [_clamp01(signal.get(metric)) for metric in CONTEXT_METRICS if signal.get(metric) is not None]
    return round(sum(values) / len(values), 4) if values else 0.0


def _semantic_boost(region: Mapping[str, Any]) -> float:
    if not region:
        return 0.0
    parameters = region.get("parameters") or {}
    if not isinstance(parameters, Mapping):
        parameters = {}
    density = _clamp01((_to_float(parameters.get("lattice_density_multiplier", 1.0), 1.0) - 1.0) / 1.0)
    strain = _clamp01(_to_float(parameters.get("phason_strain_factor", 0.0), 0.0) / 1.5)
    applied = 1.0 if region.get("applied") is True else 0.0
    return round((density * 0.45) + (strain * 0.35) + (applied * 0.20), 4)


def _sensitivity_score(label: str, confidence: float, context_score: float, semantic_boost: float) -> float:
    base = LABEL_BASE_SENSITIVITY.get(label, LABEL_BASE_SENSITIVITY["default"])
    score = (base * 0.40) + (confidence * 0.25) + (context_score * 0.25) + (semantic_boost * 0.10)
    if label in CRITICAL_LABELS and confidence >= 0.85:
        score = max(score, 0.84)
    if label in HIGH_LABELS and confidence >= 0.85:
        score = max(score, 0.62)
    if label == "document_text" and confidence >= 0.75 and context_score >= 0.80:
        score = max(score, 0.83)
    return round(_clamp01(score), 4)


def _sensitivity_level(score: float) -> SensitivityLevel:
    if score >= 0.78:
        return "critical"
    if score >= 0.60:
        return "high"
    if score >= 0.42:
        return "medium"
    return "low"


def _max_sensitivity(levels: Sequence[str]) -> SensitivityLevel:
    order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
    max_level = "low"
    for level in levels:
        if order.get(level, 0) > order[max_level]:
            max_level = level
    return max_level  # type: ignore[return-value]


def _obfuscation_intensity(level: str) -> str:
    return {
        "low": "baseline",
        "medium": "elevated",
        "high": "strong",
        "critical": "maximum",
    }.get(level, "baseline")


def _chunk_mode(media_type: MediaType, level: str) -> str:
    if level == "critical":
        return "critical_dense"
    if level == "high":
        return "sensitive_dense"
    if level == "medium":
        return "balanced"
    return "fast_basic"


def _clamp01(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return min(1.0, max(0.0, numeric))


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
