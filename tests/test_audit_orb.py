import pytest

from ffed_qlc import build_privacy_safe_audit_orb


def test_privacy_safe_audit_orb_keeps_only_fingerprints_and_refs() -> None:
    orb = build_privacy_safe_audit_orb(
        orb_id="worker-orb-001",
        events=[
            {
                "label": "login",
                "source": "managed-workstation",
                "timestamp": "2026-06-24T13:00:00Z",
                "secret_manager_ref": "vault://team/app/login",
            }
        ],
        epsilon=0.8,
    )

    assert orb["schema"] == "ffed.qlc.privacy_safe_audit_orb.v1"
    assert orb["secret_policy"]["raw_secrets_allowed"] is False
    assert orb["events"][0]["raw_payload_embedded"] is False
    assert orb["events"][0]["secret_manager_ref"] == "vault://team/app/login"
    assert "fingerprint" in orb["events"][0]
    assert orb["differential_privacy"]["enabled"] is True
    assert orb["claim_boundary"] == "audit_provenance_not_employee_surveillance_or_password_storage"


def test_privacy_safe_audit_orb_rejects_raw_passwords() -> None:
    with pytest.raises(ValueError, match="raw secret field"):
        build_privacy_safe_audit_orb(
            orb_id="worker-orb-001",
            events=[{"label": "login", "password": "do-not-store-this"}],
        )
