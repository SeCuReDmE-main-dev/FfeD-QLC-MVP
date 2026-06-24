from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class SemanticComplexityRule:
    lattice_density_multiplier: float
    phason_strain_factor: float
    z_value_modifier: float
    gradient_width: int = 3


DEFAULT_SEMANTIC_COMPLEXITY_RULES: dict[str, SemanticComplexityRule] = {
    "face": SemanticComplexityRule(2.0, 1.5, 10.0, 5),
    "license_plate": SemanticComplexityRule(1.8, 1.2, 8.0, 4),
    "document_text": SemanticComplexityRule(1.5, 1.0, 5.0, 3),
    "screen": SemanticComplexityRule(1.4, 0.8, 4.0, 3),
    "default": SemanticComplexityRule(1.0, 0.0, 0.0, 1),
}


def build_semantic_complexity_map(
    detections: Sequence[Mapping[str, Any]],
    *,
    min_confidence: float = 0.75,
    rules: Mapping[str, SemanticComplexityRule] | None = None,
) -> dict[str, Any]:
    """Translate YOLO/CeLeBrUm ROI metadata into bounded QLC complexity policy."""

    active_rules = dict(rules or DEFAULT_SEMANTIC_COMPLEXITY_RULES)
    default_rule = active_rules["default"]
    regions = []
    for index, detection in enumerate(detections):
        label = str(detection.get("class_name") or detection.get("label") or detection.get("name") or "default")
        confidence = _clamp01(detection.get("confidence_score", detection.get("confidence", 0.0)))
        rule = active_rules.get(label, default_rule)
        applied = confidence >= _clamp01(min_confidence)
        if not applied:
            rule = default_rule
        regions.append(
            {
                "index": index,
                "label": label,
                "confidence": confidence,
                "applied": applied,
                "parameters": {
                    "lattice_density_multiplier": rule.lattice_density_multiplier,
                    "phason_strain_factor": rule.phason_strain_factor,
                    "z_value_modifier": rule.z_value_modifier,
                },
                "phason_strain_gradient": {
                    "enabled": applied and rule.phason_strain_factor > 0.0,
                    "gradient_width": rule.gradient_width,
                    "boundary_policy": "smooth_complexity_transition",
                },
            }
        )
    return {
        "schema": "ffed.qlc.semantic_complexity_map.v1",
        "source": "CeLeBrUm ROI metadata",
        "min_confidence": _clamp01(min_confidence),
        "security_boundary": "semantic policy input only; not a cryptographic root",
        "regions": regions,
    }


def _clamp01(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return min(1.0, max(0.0, numeric))
