import pytest

from ffed_qlc import (
    build_celebrum_route_decision,
    build_fnpqnn_runtime_payload,
    build_human_review_quarantine_capsule,
    build_privacy_safe_audit_orb,
    pack_bytes,
)


def _critical_route() -> tuple[dict, dict, dict]:
    mesh = build_fnpqnn_runtime_payload(
        source_id="asset-001",
        qlc_container=pack_bytes(b"critical capsule artifact", "passphrase"),
        yolo_detections=[{"class_name": "license_plate", "confidence_score": 0.98}],
        context_signals=[{"texture_complexity": 0.8, "entropy_score": 0.8, "edge_density": 0.7}],
    )
    route = build_celebrum_route_decision(mesh)
    swop = mesh["plugin_context"]["sensitivity_weighted_obfuscation_policy"]
    orb = build_privacy_safe_audit_orb(orb_id="orb-001", events=[{"label": "review", "source": "test"}])
    return route, swop, orb


def test_quarantine_capsule_builds_urgent_review_from_human_review_route() -> None:
    route, swop, orb = _critical_route()

    capsule = build_human_review_quarantine_capsule(route, swop_policy=swop, audit_orb=orb, reason="critical sensitivity")

    assert capsule["schema"] == "ffed.qlc.human_review_quarantine_capsule.v1"
    assert capsule["route_action"] == "human_review"
    assert capsule["review_priority"] == "urgent_review"
    assert capsule["audit_nonce"] == orb["audit_nonce"]
    assert "critical_sensitivity" in capsule["reason_codes"]
    assert capsule["raw_payload_embedded"] is False


def test_quarantine_capsule_builds_blocking_priority_for_quarantine_route() -> None:
    route, swop, orb = _critical_route()
    route = dict(route)
    route["action"] = "quarantine"

    capsule = build_human_review_quarantine_capsule(route, swop_policy=swop, audit_orb=orb)

    assert capsule["route_action"] == "quarantine"
    assert capsule["review_priority"] == "blocking"


@pytest.mark.parametrize("field", ["raw_activity", "browsing_history", "raw_image", "raw_ocr", "password", "token", "secret"])
def test_quarantine_capsule_rejects_raw_review_material(field: str) -> None:
    route, _swop, _orb = _critical_route()
    unsafe = dict(route)
    unsafe[field] = "raw"

    with pytest.raises(ValueError, match="raw quarantine field"):
        build_human_review_quarantine_capsule(unsafe)
