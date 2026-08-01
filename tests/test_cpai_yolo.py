from __future__ import annotations

import json

from ffed_qlc.cpai_yolo import (
    DEFAULT_CPAI_URL,
    TRAINING_MODULE,
    plan_yolo_training,
    probe_cpai_status,
    probe_yolo_detection_routes,
    probe_yolo_training_module,
    yolo_detections_to_roi_pressure,
)


def test_cpai_status_dry_run_and_unavailable_probe_are_metadata_only() -> None:
    dry_run = probe_cpai_status()
    unavailable = probe_cpai_status("http://127.0.0.1:9", dry_run=False, timeout_seconds=0.01)

    assert DEFAULT_CPAI_URL == "http://127.0.0.1:32171"
    assert dry_run["cpai_url"] == DEFAULT_CPAI_URL
    assert dry_run["dry_run"] is True
    assert dry_run["raw_payload_embedded"] is False
    assert unavailable["dry_run"] is False
    assert unavailable["available"] is False
    assert unavailable["status"] == "unavailable"


def test_yolo_route_and_training_probes_do_not_copy_server_or_start_training() -> None:
    routes = probe_yolo_detection_routes()
    training = probe_yolo_training_module()

    assert "/v1/vision/detection" in routes["routes"]
    assert routes["server_copied"] is False
    assert routes["raw_image_embedded"] is False
    assert training["module"] == TRAINING_MODULE
    assert training["training_started"] is False
    assert training["raw_image_embedded"] is False


def test_yolo_training_plan_is_metadata_only_and_requires_confirmation() -> None:
    plan = plan_yolo_training(model_name="qlc-model", dataset_name="qlc-dataset", epochs=5)
    serialized = json.dumps(plan, sort_keys=True)

    assert plan["module"] == TRAINING_MODULE
    assert plan["steps"] == ["create_dataset", "train_model", "resume_training"]
    assert plan["requires_ui_confirmation"] is True
    assert plan["training_started"] is False
    assert plan["metadata_only"] is True
    assert "raw_image" in serialized
    assert "image-bytes" not in serialized


def test_yolo_detections_convert_to_roi_pressure_and_friction_hints() -> None:
    payload = yolo_detections_to_roi_pressure(
        [
            {
                "class_name": "face",
                "confidence_score": 0.9,
                "bounding_box_normalized": [0.1, 0.2, 0.3, 0.4],
            }
        ]
    )

    assert payload["roi_map"]["detection_count"] == 1
    assert payload["roi_map"]["policy"]["raw_image_embedded"] is False
    assert 0.0 <= payload["semantic_pressure"]["value"] <= 1.0
    assert payload["friction_hints"]["bounded"] is True
    assert payload["raw_image_embedded"] is False
