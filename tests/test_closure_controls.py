from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
import pytest

from ffed_qlc.api import create_app
from ffed_qlc.identity import IdentityIntegrationPending, PendingIdentityVerifier, SyntheticTestIdentityVerifier
from ffed_qlc.native_handoff import DisabledNativeHandoffAdapter, NativeHandoffEnvelope, NativeHandoffError, PivotCliHandoffAdapter
from ffed_qlc.runtime_config import RuntimeConfig, normalize_base_url
from ffed_qlc.storage import AlphaStore, SCHEMA_VERSION


class UnavailableGateway:
    def readiness(self) -> dict[str, object]:
        return {"ready": False, "detail": r"C:\private\gateway"}


class ReadyGateway(UnavailableGateway):
    def readiness(self) -> dict[str, object]:
        return {"ready": True}


def _config(**overrides: object) -> RuntimeConfig:
    values: dict[str, object] = {
        "public_stateful_enabled": False,
        "fqlc2_enabled": True,
        "native_handoffs_enabled": False,
        "runtime": "local",
        "cpai_allowed_base_urls": ("http://127.0.0.1:32171",),
    }
    values.update(overrides)
    return RuntimeConfig(**values)


def test_public_readiness_is_available_without_gateway_and_redacts_paths(tmp_path: Path) -> None:
    client = TestClient(create_app(store=AlphaStore(tmp_path), gateway=UnavailableGateway(), config=_config()))
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json()["gateway"] == {
        "ready": False,
        "required_for_public_runtime": False,
        "secret_values_exposed": False,
    }
    assert "private" not in response.text.lower()


def test_stateful_readiness_requires_gateway(tmp_path: Path) -> None:
    client = TestClient(
        create_app(
            store=AlphaStore(tmp_path),
            gateway=UnavailableGateway(),
            identity=SyntheticTestIdentityVerifier(),
            config=_config(public_stateful_enabled=True),
        )
    )
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "GATEWAY_UNAVAILABLE"


def test_invalid_and_oversize_content_length_are_stable_client_errors(tmp_path: Path) -> None:
    client = TestClient(create_app(store=AlphaStore(tmp_path), gateway=ReadyGateway(), config=_config()))
    malformed = client.post("/api/lattice/build", headers={"content-length": "not-a-number"}, content=b"{}")
    oversized = client.post("/api/lattice/build", headers={"content-length": "1000001"}, content=b"{}")
    assert malformed.status_code == 400
    assert malformed.json()["detail"]["code"] == "INVALID_CONTENT_LENGTH"
    assert oversized.status_code == 413
    assert oversized.json()["detail"]["code"] == "REQUEST_TOO_LARGE"


def test_cpai_allowlist_rejects_ssrf_variants_and_training_request(tmp_path: Path) -> None:
    allowed = "http://127.0.0.1:32171"
    config = _config(cpai_allowed_base_urls=(allowed,))
    assert config.require_cpai_url(allowed + "/") == allowed
    for value in (
        "http://169.254.169.254",
        "file:///etc/passwd",
        "http://user:password@127.0.0.1:32171",
        "http://127.0.0.1:32171/admin",
        "http://127.0.0.1:32171?next=http://169.254.169.254",
    ):
        with pytest.raises(ValueError):
            normalize_base_url(value) if value.startswith("file:") or "@" in value or "/admin" in value or "?" in value else config.require_cpai_url(value)
    client = TestClient(create_app(store=AlphaStore(tmp_path), gateway=ReadyGateway(), config=config))
    rejected = client.post("/api/cpai/yolo/training/plan", json={"cpai_url": "http://169.254.169.254"})
    assert rejected.status_code == 400
    assert rejected.json()["detail"]["code"] == "CPAI_ENDPOINT_REJECTED"


def test_fqlc2_web_surface_is_synthetic_and_metadata_only(tmp_path: Path) -> None:
    client = TestClient(create_app(store=AlphaStore(tmp_path), gateway=ReadyGateway(), config=_config()))
    response = client.post(
        "/api/v1/fqlc2/synthetic-roundtrip",
        json={"fixture_id": "synthetic-env-basic", "recipient_count": 2, "signed": True},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["roundtrip_verified"] is True
    assert payload["private_key_exposed"] is False
    assert payload["manifest"]["recipient_identity_exposed"] is False
    inspected = client.post("/api/v1/fqlc2/inspect", json={"container_base64": payload["container_base64"]})
    assert inspected.status_code == 200
    assert inspected.json()["header_sha256"] == payload["manifest"]["header_sha256"]


def test_sqlite_schema_wal_and_concurrent_idempotency(tmp_path: Path) -> None:
    store = AlphaStore(tmp_path)
    with store.connection() as db:
        assert db.execute("SELECT version FROM schema_meta").fetchone()[0] == SCHEMA_VERSION
        assert db.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
    key = "same-idempotency-key-0001"
    digest = hashlib.sha256(b"same payload").hexdigest()
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: store.claim_idempotency_key(key, "mission.execute", digest), range(6)))
    assert results.count(True) == 1
    assert results.count(False) == 5
    with pytest.raises(ValueError, match="different operation"):
        store.claim_idempotency_key(key, "other", digest)


def test_native_handoff_requires_real_ready_receipt(tmp_path: Path) -> None:
    cli = tmp_path / "pivot_cli.py"
    cli.write_text(
        "import json\nprint(json.dumps({'note': {'id': 'native-note-1', 'sha256': 'a' * 64, 'status': 'READY'}}))\n",
        encoding="utf-8",
    )
    envelope = NativeHandoffEnvelope.build(
        target="gemini",
        capability="review_evidence",
        consent_receipt_id="opaque-consent-receipt",
        evidence_refs=["b" * 64],
    )
    receipt = PivotCliHandoffAdapter(cli).dispatch(envelope)
    assert receipt["status"] == "READY"
    assert receipt["native_receipt"]["note_id"] == "native-note-1"
    assert receipt["acknowledged"] is False
    assert receipt["raw_conversation_included"] is False
    assert receipt["secret_values_exposed"] is False


def test_native_handoff_timeout_and_invalid_receipt_are_not_simulated(tmp_path: Path) -> None:
    invalid_receipt_envelope = NativeHandoffEnvelope.build(
        target="codex",
        capability="review_evidence",
        consent_receipt_id="opaque-consent-receipt",
        evidence_refs=["c" * 64],
        deadline_seconds=10,
    )
    invalid = tmp_path / "invalid.py"
    invalid.write_text("print('{}')\n", encoding="utf-8")
    with pytest.raises(NativeHandoffError, match="incomplete"):
        PivotCliHandoffAdapter(invalid).dispatch(invalid_receipt_envelope)

    slow = tmp_path / "slow.py"
    slow.write_text("import time\ntime.sleep(3)\n", encoding="utf-8")
    timeout_envelope = NativeHandoffEnvelope.build(
        target="codex",
        capability="review_evidence",
        consent_receipt_id="opaque-consent-receipt",
        evidence_refs=["c" * 64],
        deadline_seconds=1,
    )
    with pytest.raises(NativeHandoffError) as error:
        PivotCliHandoffAdapter(slow, timeout_seconds=1).dispatch(timeout_envelope)
    assert error.value.code == "NATIVE_HANDOFF_TIMEOUT"


def test_identity_and_handoff_boundaries_reject_incomplete_inputs(tmp_path: Path) -> None:
    with pytest.raises(IdentityIntegrationPending):
        PendingIdentityVerifier().verify(subject_ref="opaque", role="teacher", action="write")
    with pytest.raises(IdentityIntegrationPending):
        SyntheticTestIdentityVerifier().verify(subject_ref="", role="teacher", action="write")
    disabled = DisabledNativeHandoffAdapter()
    assert disabled.ready is False
    valid = NativeHandoffEnvelope.build(
        target="codex",
        capability="review",
        consent_receipt_id="opaque",
        evidence_refs=["d" * 64],
    )
    with pytest.raises(NativeHandoffError) as unavailable:
        disabled.dispatch(valid)
    assert unavailable.value.code == "NATIVE_RUNTIME_UNAVAILABLE"
    assert PivotCliHandoffAdapter(tmp_path / "missing.py").ready is False
    with pytest.raises(NativeHandoffError, match="unavailable"):
        PivotCliHandoffAdapter(tmp_path / "missing.py").dispatch(valid)

    invalid_inputs = [
        {"target": "other"},
        {"capability": ""},
        {"consent_receipt_id": ""},
        {"evidence_refs": ["not-a-hash"]},
        {"deadline_seconds": 0},
    ]
    base = {
        "target": "codex",
        "capability": "review",
        "consent_receipt_id": "opaque",
        "evidence_refs": ["e" * 64],
        "deadline_seconds": 30,
    }
    for change in invalid_inputs:
        with pytest.raises(NativeHandoffError):
            NativeHandoffEnvelope.build(**(base | change))


def test_native_handoff_process_and_json_failures_are_explicit(tmp_path: Path) -> None:
    envelope = NativeHandoffEnvelope.build(
        target="gemini",
        capability="review",
        consent_receipt_id="opaque",
        evidence_refs=["f" * 64],
    )
    failed = tmp_path / "failed.py"
    failed.write_text("raise SystemExit(2)\n", encoding="utf-8")
    with pytest.raises(NativeHandoffError) as process_error:
        PivotCliHandoffAdapter(failed).dispatch(envelope)
    assert process_error.value.code == "NATIVE_HANDOFF_FAILED"

    invalid_json = tmp_path / "invalid-json.py"
    invalid_json.write_text("print('not json')\n", encoding="utf-8")
    with pytest.raises(NativeHandoffError) as json_error:
        PivotCliHandoffAdapter(invalid_json).dispatch(envelope)
    assert json_error.value.code == "INVALID_NATIVE_RECEIPT"
