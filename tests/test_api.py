from __future__ import annotations

import json

from fastapi.testclient import TestClient

from ffed_qlc.api import create_app


def test_api_health_and_source_functions_are_redacted() -> None:
    client = TestClient(create_app())

    health = client.get("/api/health")
    sources = client.get("/api/source-functions")
    serialized = json.dumps(sources.json(), sort_keys=True)

    assert health.status_code == 200
    assert health.json()["secret_values_exposed"] is False
    assert sources.status_code == 200
    assert sources.json()["source_count"] == 10
    assert "https://" not in serialized
    assert sources.json()["graph"]["graph_role"] == "secondary_provenance_not_lattice_engine"


def test_api_lattice_classify_validate_orb_and_template() -> None:
    client = TestClient(create_app())
    request = {"engine": "inflation", "target_tile_count": 5, "depth": 3, "seed": "api-test"}

    build = client.post("/api/lattice/build", json=request)
    classify = client.post("/api/lattice/classify", json=request)
    validate = client.post("/api/lattice/validate", json=request)
    orb = client.post("/api/orbs/build", json=request)
    template = client.post("/api/export/lattice-template")

    assert build.status_code == 200
    assert build.json()["schema"] == "ffed.qlc.api.lattice_build.v1"
    assert build.json()["patch_metadata"]["tile_count"] == 5
    assert classify.status_code == 200
    assert classify.json()["classifications"]
    assert validate.status_code == 200
    assert validate.json()["ledger"]["raw_tif_exported"] is False
    assert orb.status_code == 200
    assert orb.json()["schema"] == "ffed.qlc.orb_envelope.v1"
    assert orb.json()["raw_media_embedded"] is False
    assert template.status_code == 200
    assert template.json()["raw_payload_allowed"] is False


def test_api_cpai_yolo_transport_and_training_plan_are_bounded() -> None:
    client = TestClient(create_app())

    status = client.get("/api/cpai/status")
    yolo = client.get("/api/cpai/yolo/probe")
    training_probe = client.get("/api/cpai/yolo/training/probe")
    training_plan = client.post(
        "/api/cpai/yolo/training/plan",
        json={"model_name": "m", "dataset_name": "d", "epochs": 3},
    )

    assert status.json()["dry_run"] is False
    assert yolo.json()["transport_checked"] is True
    assert yolo.json()["raw_image_embedded"] is False
    assert training_probe.json()["training_started"] is False
    assert training_plan.json()["module"] == "TrainingObjectDetectionYOLOv5"
    assert training_plan.json()["training_started"] is False
