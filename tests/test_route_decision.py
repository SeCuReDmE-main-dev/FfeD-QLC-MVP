import pytest

from ffed_qlc import (
    build_celebrum_route_decision,
    build_ecn_handoff_packet,
    build_fnpqnn_runtime_payload,
    build_privacy_safe_audit_orb,
    pack_bytes,
)


def _mesh_payload(*, confidence: float = 0.91, context_score: float = 0.2) -> dict:
    return build_fnpqnn_runtime_payload(
        source_id="asset-001",
        qlc_container=pack_bytes(b"route artifact", "passphrase"),
        yolo_detections=[{"class_name": "screen", "confidence_score": confidence}],
        context_signals=[
            {
                "texture_complexity": context_score,
                "entropy_score": context_score,
                "edge_density": context_score,
            }
        ],
    )


def test_route_decision_submits_passed_metadata_to_cerebrum() -> None:
    decision = build_celebrum_route_decision(_mesh_payload())

    assert decision["schema"] == "ffed.qlc.celebrum_route_decision.v1"
    assert decision["action"] == "submit_to_cerebrum"
    assert decision["orchestrator"] == "CeLeBrUm"
    assert decision["runtime_memory_surface"] == "Cerebrum"
    assert decision["raw_payload_embedded"] is False


def test_route_decision_uses_gateway_handoff_when_ecn_destination_exists() -> None:
    orb = build_privacy_safe_audit_orb(orb_id="orb-001", events=[{"label": "safe", "source": "test"}])
    ecn = build_ecn_handoff_packet(orb, destination="ecn://celebrum")

    decision = build_celebrum_route_decision(_mesh_payload(), audit_orb=orb, ecn_packet=ecn)

    assert decision["action"] == "gateway_handoff"
    assert decision["audit_nonce"] == orb["audit_nonce"]
    assert decision["ecn_destination"] == "ecn://celebrum"


def test_route_decision_rejects_raw_activity_fields() -> None:
    payload = _mesh_payload()
    payload["raw_activity"] = "do-not-route"

    with pytest.raises(ValueError, match="raw route field"):
        build_celebrum_route_decision(payload)


def test_route_decision_sends_escalated_guard_to_human_review() -> None:
    decision = build_celebrum_route_decision(_mesh_payload(confidence=0.2, context_score=0.95))

    assert decision["guard_verdict"] == "escalate"
    assert decision["action"] == "human_review"


def test_route_decision_sends_critical_swop_region_to_human_review() -> None:
    payload = build_fnpqnn_runtime_payload(
        source_id="asset-001",
        qlc_container=pack_bytes(b"critical route artifact", "passphrase"),
        yolo_detections=[{"class_name": "license_plate", "confidence_score": 0.98}],
        context_signals=[{"texture_complexity": 0.8, "entropy_score": 0.8, "edge_density": 0.7}],
    )

    decision = build_celebrum_route_decision(payload)

    assert decision["sensitivity_level"] == "critical"
    assert decision["action"] == "human_review"
