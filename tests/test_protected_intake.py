import pytest

from ffed_qlc import build_multimodal_protected_intake_descriptor


def test_intake_descriptor_accepts_image_metadata_only() -> None:
    descriptor = build_multimodal_protected_intake_descriptor(
        "image",
        "image-001",
        "sha256:abc",
        detections=[{"class_name": "face", "confidence_score": 0.91}],
        context_signals=[{"texture_complexity": 0.3, "entropy_score": 0.2, "edge_density": 0.4}],
    )

    assert descriptor["schema"] == "ffed.qlc.multimodal_protected_intake_descriptor.v1"
    assert descriptor["media_type"] == "image"
    assert descriptor["region_count"] == 1
    assert descriptor["raw_media_embedded"] is False
    assert descriptor["detector_metadata"]["labels"] == ["face"]


def test_intake_descriptor_counts_document_pages_and_video_frames() -> None:
    document = build_multimodal_protected_intake_descriptor(
        "document",
        "doc-001",
        "sha256:doc",
        detections=[
            {"class_name": "document_text", "page_index": 1},
            {"class_name": "document_text", "page_index": 2},
        ],
    )
    video = build_multimodal_protected_intake_descriptor(
        "video",
        "video-001",
        "sha256:video",
        detections=[
            {"class_name": "face", "frame_index": 12},
            {"class_name": "screen", "frame_index": 13},
        ],
    )

    assert document["page_count"] == 2
    assert document["frame_count"] == 0
    assert video["frame_count"] == 2
    assert video["page_count"] == 0


@pytest.mark.parametrize("field", ["raw_image", "image_bytes", "raw_ocr", "video_bytes", "password", "token", "secret"])
def test_intake_descriptor_rejects_raw_media_ocr_and_secrets(field: str) -> None:
    with pytest.raises(ValueError, match="raw intake field"):
        build_multimodal_protected_intake_descriptor(
            "image",
            "image-001",
            "sha256:abc",
            detections=[{"class_name": "screen", field: "raw"}],
        )
