import pytest

from ffed_qlc import build_semantic_complexity_map, build_sensitivity_weighted_obfuscation_policy


def test_swop_marks_high_confidence_face_as_high_strong_image_region() -> None:
    detections = [{"class_name": "face", "confidence_score": 0.93}]
    swop = build_sensitivity_weighted_obfuscation_policy("image", detections=detections)

    assert swop["schema"] == "ffed.qlc.sensitivity_weighted_obfuscation_policy.v1"
    assert swop["media_type"] == "image"
    assert swop["sensitivity_level"] == "high"
    assert swop["obfuscation_intensity"] == "strong"
    assert swop["recommended_chunk_mode"] == "sensitive_dense"
    assert swop["raw_media_embedded"] is False


def test_swop_marks_high_confidence_license_plate_as_critical_maximum() -> None:
    detections = [{"class_name": "license_plate", "confidence_score": 0.98}]
    semantic_map = build_semantic_complexity_map(detections)
    swop = build_sensitivity_weighted_obfuscation_policy("image", detections=detections, semantic_map=semantic_map)

    assert swop["sensitivity_level"] == "critical"
    assert swop["obfuscation_intensity"] == "maximum"
    assert swop["recommended_chunk_mode"] == "critical_dense"


def test_swop_marks_document_text_with_high_entropy_as_critical() -> None:
    detections = [{"class_name": "document_text", "confidence_score": 0.92}]
    context = [{"texture_complexity": 0.86, "entropy_score": 0.96, "edge_density": 0.76}]
    semantic_map = build_semantic_complexity_map(detections)

    swop = build_sensitivity_weighted_obfuscation_policy(
        "document",
        detections=detections,
        context_signals=context,
        semantic_map=semantic_map,
    )

    assert swop["media_type"] == "document"
    assert swop["sensitivity_level"] == "critical"
    assert swop["obfuscation_intensity"] == "maximum"


def test_swop_marks_normal_document_text_as_medium_balanced() -> None:
    swop = build_sensitivity_weighted_obfuscation_policy(
        "document",
        detections=[{"class_name": "document_text", "confidence_score": 0.74}],
        context_signals=[{"texture_complexity": 0.20, "entropy_score": 0.25, "edge_density": 0.18}],
    )

    assert swop["sensitivity_level"] == "medium"
    assert swop["recommended_chunk_mode"] == "balanced"


def test_swop_marks_sensitive_video_frame_as_dense_chunk_mode() -> None:
    swop = build_sensitivity_weighted_obfuscation_policy(
        "video",
        detections=[{"class_name": "face", "confidence_score": 0.90, "frame_index": 12}],
    )

    assert swop["media_type"] == "video"
    assert swop["regions"][0]["recommended_chunk_mode"] == "sensitive_dense"


def test_swop_marks_non_sensitive_video_frame_as_fast_basic() -> None:
    swop = build_sensitivity_weighted_obfuscation_policy(
        "video",
        detections=[{"class_name": "background", "confidence_score": 0.30, "frame_index": 12}],
    )

    assert swop["sensitivity_level"] == "low"
    assert swop["recommended_chunk_mode"] == "fast_basic"


@pytest.mark.parametrize("field", ["raw_image", "image_bytes", "raw_ocr", "video_bytes", "password", "token", "secret"])
def test_swop_rejects_raw_sensitive_fields(field: str) -> None:
    with pytest.raises(ValueError, match="raw SWOP field"):
        build_sensitivity_weighted_obfuscation_policy("image", detections=[{"class_name": "screen", field: "raw"}])
