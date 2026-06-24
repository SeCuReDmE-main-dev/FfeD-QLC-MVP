from ffed_qlc import build_context_consistency_guard


def test_context_guard_passes_high_confidence_normal_roi() -> None:
    guard = build_context_consistency_guard(
        [{"class_name": "face", "confidence_score": 0.91}],
        [{"texture_complexity": 0.3, "entropy_score": 0.4, "edge_density": 0.2}],
    )

    assert guard["verdict"] == "pass"
    assert guard["regions"][0]["verdict"] == "pass"
    assert guard["raw_image_embedded"] is False


def test_context_guard_escalates_low_confidence_high_context() -> None:
    guard = build_context_consistency_guard(
        [{"class_name": "background", "confidence_score": 0.32}],
        [{"texture_complexity": 0.92, "entropy_score": 0.88, "edge_density": 0.79}],
    )

    assert guard["verdict"] == "escalate"
    assert guard["regions"][0]["reason"] == "low_detection_confidence_with_high_context_complexity"


def test_context_guard_suspends_missing_context() -> None:
    guard = build_context_consistency_guard([{"class_name": "document_text", "confidence_score": 0.4}])

    assert guard["verdict"] == "suspend"
    assert guard["regions"][0]["signals_present"] is False
