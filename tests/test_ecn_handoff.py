import pytest

from ffed_qlc import build_ecn_handoff_packet, build_privacy_safe_audit_orb


def test_ecn_handoff_accepts_privacy_safe_audit_orb() -> None:
    orb = build_privacy_safe_audit_orb(
        orb_id="orb-001",
        events=[{"label": "runtime-export", "source": "fnp-qnn", "secret_manager_ref": "vault://sim/runtime"}],
    )

    packet = build_ecn_handoff_packet(orb, urgency="high", destination="ecn://ops")

    assert packet["schema"] == "ffed.qlc.ecn_handoff_packet.v1"
    assert packet["urgency"] == "high"
    assert packet["destination"] == "ecn://ops"
    assert packet["raw_payload_embedded"] is False
    assert packet["event_count"] == 1
    assert packet["event_fingerprints"][0]


def test_ecn_handoff_rejects_raw_activity_dump() -> None:
    orb = build_privacy_safe_audit_orb(orb_id="orb-001", events=[{"label": "safe", "source": "test"}])
    unsafe = dict(orb)
    unsafe["raw_activity"] = "visited every page"

    with pytest.raises(ValueError, match="raw ECN field"):
        build_ecn_handoff_packet(unsafe)


def test_ecn_handoff_rejects_non_metadata_events() -> None:
    orb = build_privacy_safe_audit_orb(orb_id="orb-001", events=[{"label": "safe", "source": "test"}])
    unsafe = dict(orb)
    unsafe["events"] = [dict(orb["events"][0], raw_payload_embedded=True)]

    with pytest.raises(ValueError, match="metadata-only"):
        build_ecn_handoff_packet(unsafe)
