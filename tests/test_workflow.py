from __future__ import annotations

import pytest

from ffed_qlc import (
    build_gateway_celebrum_loop_receipt,
    build_qlc_protection_workflow,
    emit_qlc_workflow_counter,
    pack_bytes,
)


def _container() -> bytes:
    return pack_bytes(b"workflow payload for qlc threading", "passphrase")


def test_qlc_protection_workflow_threads_all_artifacts() -> None:
    bundle = build_qlc_protection_workflow(
        source_id="asset-001",
        qlc_container=_container(),
        media_type="image",
        detections=[{"class_name": "face", "confidence_score": 0.91}],
        context_signals=[{"texture_complexity": 0.2, "entropy_score": 0.2, "edge_density": 0.2}],
        ecn_destination="",
    )

    assert bundle["schema"] == "ffed.qlc.protection_workflow_bundle.v1"
    assert bundle["contract_version"] == "qlc-wiring-contract.v2"
    artifacts = bundle["artifacts"]
    assert artifacts["intake_descriptor"]["raw_media_embedded"] is False
    assert artifacts["mesh_payload"]["plugin_context"]["context_consistency_guard"]["verdict"] == "pass"
    assert artifacts["chunk_key_schedule"]["key_material_exposed"] is False
    assert artifacts["swop_chunk_protection_plan"]["key_material_exposed"] is False
    assert artifacts["audit_orb"]["events"][0]["raw_payload_embedded"] is False
    assert artifacts["ecn_packet"]["raw_payload_embedded"] is False
    assert artifacts["route_decision"]["action"] == "submit_to_cerebrum"
    assert artifacts["quarantine_capsule"] is None
    assert artifacts["proof_bundle_receipt"]["artifact_count"] == 5
    assert artifacts["reciprocal_utility_scorecard"]["schema"] == "ffed.qlc.reciprocal_utility_scorecard.v1"
    assert bundle["gateway_submission"]["schema"] == "ffed.qlc.gateway_submission.v1"
    assert bundle["gateway_submission"]["contract_version"] == "qlc-wiring-contract.v2"
    assert bundle["gateway_submission"]["target_endpoint"] == "POST /cerebrum/runtime/run"


def test_qlc_protection_workflow_quarantines_critical_route() -> None:
    bundle = build_qlc_protection_workflow(
        source_id="asset-002",
        qlc_container=_container(),
        media_type="image",
        detections=[{"class_name": "license_plate", "confidence_score": 0.96}],
        context_signals=[{"texture_complexity": 0.9, "entropy_score": 0.9, "edge_density": 0.9}],
    )

    route = bundle["artifacts"]["route_decision"]
    capsule = bundle["artifacts"]["quarantine_capsule"]
    assert route["action"] == "human_review"
    assert route["sensitivity_level"] == "critical"
    assert capsule["review_priority"] == "urgent_review"


def test_qlc_protection_workflow_rejects_raw_media_or_secrets() -> None:
    with pytest.raises(ValueError, match="raw workflow field"):
        build_qlc_protection_workflow(
            source_id="asset-003",
            qlc_container=_container(),
            detections=[{"class_name": "face", "confidence": 0.9, "raw_image": "not-allowed"}],
        )

    with pytest.raises(ValueError, match="raw workflow field"):
        build_qlc_protection_workflow(
            source_id="asset-004",
            qlc_container=_container(),
            audit_events=[{"label": "bad", "token": "not-allowed"}],
        )


def test_gateway_celebrum_loop_receipt_compacts_simulator_result() -> None:
    bundle = build_qlc_protection_workflow(
        source_id="asset-005",
        qlc_container=_container(),
        detections=[{"class_name": "screen", "confidence_score": 0.9}],
        context_signals=[{"texture_complexity": 0.1, "entropy_score": 0.1, "edge_density": 0.1}],
        ecn_destination="",
    )
    receipt = build_gateway_celebrum_loop_receipt(
        bundle,
        {"status": "ok", "runtime": {"feature_dimension": 8}, "raw_payload_embedded": False},
    )

    assert receipt["schema"] == "ffed.qlc.gateway_celebrum_loop_receipt.v1"
    assert receipt["route_action"] == "submit_to_cerebrum"
    assert receipt["fingerprints"]["simulator_result"]
    assert "feature_dimension" not in str(receipt["fingerprints"])
    assert receipt["raw_payload_embedded"] is False


def test_emit_qlc_workflow_counter_uses_typed_metric(monkeypatch) -> None:
    emitted: list[tuple[str, int, tuple[str, ...]]] = []

    def fake_emit(name: str, value: int = 1, tags: tuple[str, ...] = ()) -> None:
        emitted.append((name, value, tags))

    monkeypatch.setattr("ffed_qlc.telemetry.emit_dogstatsd_counter", fake_emit)
    bundle = build_qlc_protection_workflow(
        source_id="asset-006",
        qlc_container=_container(),
        detections=[{"class_name": "face", "confidence_score": 0.9}],
        context_signals=[{"texture_complexity": 0.1, "entropy_score": 0.1, "edge_density": 0.1}],
    )

    emit_qlc_workflow_counter("accepted", workflow_bundle=bundle, simulator_result={"status": "ok"})

    assert emitted[0][0] == "ffed_qlc.workflow.accepted"
    assert "qlc_schema:ffed.qlc.protection_workflow_bundle.v1" in emitted[0][2]
    assert "simulator_status:ok" in emitted[0][2]
