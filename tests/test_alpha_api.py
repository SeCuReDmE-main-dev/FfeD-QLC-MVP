from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from ffed_qlc.api import create_app
from ffed_qlc.identity import SyntheticTestIdentityVerifier
from ffed_qlc.runtime_config import RuntimeConfig
from ffed_qlc.storage import AlphaStore


class FakeGateway:
    def readiness(self):
        return {"ready": True, "transport": "test-contract", "secret_values_exposed": False}

    def build_session(self, role, fingerprint_ref, consent_scope, allowed_tools):
        return {
            "schema": "securedme.education.session-role.v1",
            "session_id": f"session-{role}",
            "fingerprint_ref": fingerprint_ref,
            "role": role,
            "surface": "teacher" if role == "teacher" else "student",
            "consent_scope": consent_scope,
            "allowed_tools": allowed_tools,
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

    def suite_registry(self):
        return [
            {"slug": "algoquest", "app": "AlgoQuest"},
            {"slug": "visual-algorithm", "app": "Visual Algorithm", "mascot": "RaySight"},
        ]


def test_v1_api_executes_the_student_flow(tmp_path) -> None:
    client = TestClient(create_app(
        store=AlphaStore(tmp_path),
        gateway=FakeGateway(),
        identity=SyntheticTestIdentityVerifier(),
        config=RuntimeConfig(public_stateful_enabled=True),
    ))
    assert client.get("/api/v1/health/ready").status_code == 200
    assert len(client.get("/api/v1/laboratories").json()["laboratories"]) == 9

    bootstrap = client.post(
        "/api/v1/session/bootstrap",
        json={"role": "student_adult", "fingerprint_ref": "fingerprint-redacted", "has_prior_metrics": False},
    )
    assert bootstrap.status_code == 200
    assert bootstrap.json()["diagnostic"]["starting_lab"] == "lab-01"

    project = client.post(
        "/api/v1/projects",
        json={"session_id": bootstrap.json()["session"]["session_id"], "title": "API orb", "level": "college"},
    ).json()
    run = client.post("/api/v1/missions", json={"project_id": project["project_id"], "lab_id": "lab-01"}).json()
    execution = client.post(
        f"/api/v1/missions/{run['run_id']}/actions",
        json={"action": "inspect_primitives", "fixture_id": "synthetic-env-basic"},
    )
    report = client.post(f"/api/v1/missions/{run['run_id']}/vigil", json={})

    assert execution.status_code == 200
    assert report.status_code == 200
    assert report.json()["provider_route"] == "ffed-deterministic-engine"
    assert report.json()["native_model_called"] is False


def test_legacy_planned_handoff_is_explicitly_retired(tmp_path) -> None:
    client = TestClient(create_app(store=AlphaStore(tmp_path), gateway=FakeGateway()))
    response = client.post(
        "/api/v1/handoffs",
        json={"project_id": "project-x", "target_slug": "missing", "mascot": "Unknown", "metric_names": ["mastery"]},
    )

    assert response.status_code == 410
    assert response.json()["detail"]["code"] == "NATIVE_HANDOFF_CONTRACT_REQUIRED"


def test_public_stateful_routes_remain_closed_without_identity_adapter(tmp_path) -> None:
    client = TestClient(create_app(store=AlphaStore(tmp_path), gateway=FakeGateway()))

    capabilities = client.get("/api/v1/capabilities").json()
    assert capabilities["public_stateful_enabled"] is False
    response = client.post(
        "/api/v1/session/bootstrap",
        json={"role": "student_adult", "fingerprint_ref": "fingerprint-redacted"},
    )
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "IDENTITY_INTEGRATION_PENDING"
