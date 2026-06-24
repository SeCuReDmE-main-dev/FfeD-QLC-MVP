from __future__ import annotations

from typing import Any, Mapping, Sequence


CONTEXT_METRICS = ("texture_complexity", "entropy_score", "edge_density")
GuardVerdict = str


def build_context_consistency_guard(
    detections: Sequence[Mapping[str, Any]],
    context_signals: Sequence[Mapping[str, Any]] | None = None,
    *,
    min_confidence: float = 0.75,
    high_context_threshold: float = 0.70,
) -> dict[str, Any]:
    """Detect suspicious YOLO/ROI inconsistencies without embedding raw images."""

    signal_by_index = {index: signal for index, signal in enumerate(context_signals or [])}
    regions = []
    for index, detection in enumerate(detections):
        confidence = _clamp01(detection.get("confidence_score", detection.get("confidence", 0.0)))
        signal = signal_by_index.get(index, {})
        context_values = [_clamp01(signal.get(metric)) for metric in CONTEXT_METRICS if signal.get(metric) is not None]
        context_score = sum(context_values) / len(context_values) if context_values else None
        verdict = _region_verdict(confidence, context_score, min_confidence, high_context_threshold)
        regions.append(
            {
                "index": index,
                "label": str(detection.get("class_name") or detection.get("label") or detection.get("name") or "object")[:120],
                "confidence": confidence,
                "context_score": context_score,
                "signals_present": bool(context_values),
                "verdict": verdict,
                "reason": _region_reason(verdict),
            }
        )

    overall = _overall_verdict([region["verdict"] for region in regions])
    return {
        "schema": "ffed.qlc.context_consistency_guard.v1",
        "verdict": overall,
        "min_confidence": _clamp01(min_confidence),
        "high_context_threshold": _clamp01(high_context_threshold),
        "raw_image_embedded": False,
        "security_boundary": "adversarial-evasion policy signal only; not a cryptographic root",
        "regions": regions,
    }


def _region_verdict(
    confidence: float,
    context_score: float | None,
    min_confidence: float,
    high_context_threshold: float,
) -> GuardVerdict:
    if context_score is None:
        return "suspend"
    if confidence < _clamp01(min_confidence) and context_score >= _clamp01(high_context_threshold):
        return "escalate"
    if confidence >= _clamp01(min_confidence):
        return "pass"
    return "suspend"


def _overall_verdict(verdicts: Sequence[GuardVerdict]) -> GuardVerdict:
    if not verdicts:
        return "suspend"
    if "escalate" in verdicts:
        return "escalate"
    if "suspend" in verdicts:
        return "suspend"
    return "pass"


def _region_reason(verdict: GuardVerdict) -> str:
    if verdict == "escalate":
        return "low_detection_confidence_with_high_context_complexity"
    if verdict == "suspend":
        return "insufficient_or_ambiguous_context"
    return "detection_and_context_are_consistent"


def _clamp01(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return min(1.0, max(0.0, numeric))
