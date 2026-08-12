"""Provider-neutral Vigil reporting and bounded suite handoffs."""

from __future__ import annotations

import uuid
from typing import Any, Mapping

from .contracts import PROVIDERS, payload_sha256, utc_now, validate_contract


WAKEUP_KIT = {
    "schema": "ffed.qlc.vigil-wakeup-kit.v1",
    "identity": "Vigil",
    "role": "defensive educational orchestrator",
    "providers": list(PROVIDERS),
    "required_output": "ffed.qlc.vigil_report.v1",
    "rules": [
        "Use only the supplied synthetic evidence.",
        "Distinguish observation, mechanism, evidence, and limitation.",
        "Never grade, certify, publish, or claim production security.",
        "Request remote mascots only through a bounded Gateway handoff.",
    ],
}


def build_vigil_report(run: Mapping[str, Any], evidence: Mapping[str, Any]) -> dict[str, Any]:
    report = {
        "schema": "ffed.qlc.vigil_report.v1",
        "report_id": f"report-{uuid.uuid4().hex[:16]}",
        "run_id": run["run_id"],
        "observation": evidence["observation"],
        "mechanism": evidence["mechanism"],
        "attack": evidence["attack"],
        "evidence": {"sha256": evidence["sha256"], "lab_id": evidence["lab_id"]},
        "limitation": evidence["limitation"],
        "decision": "suspend" if run["state"] != "evidence_ready" else "accept",
        "safe_next_action": "professor_review" if run["lab_id"] in {"lab-06", "lab-07", "lab-08", "lab-09"} else "continue_curriculum",
        "provider_route": "ffed-deterministic-engine",
        "native_model_called": False,
        "human_review_required": True,
        "created_at": utc_now(),
        "raw_secret_stored": False,
    }
    validate_contract(report)
    return report


def validate_provider_report(payload: Mapping[str, Any]) -> dict[str, Any]:
    validate_contract(payload, "ffed.qlc.vigil_report.v1")
    return dict(payload)


def build_handoff_request(app: Mapping[str, Any], mascot: str, metric_names: list[str], project_id: str) -> dict[str, Any]:
    if len(metric_names) > 8:
        raise ValueError("handoff metric budget exceeded")
    payload = {
        "schema": "ffed.qlc.vigil-handoff.v1",
        "handoff_id": f"handoff-{uuid.uuid4().hex[:16]}",
        "project_id": project_id,
        "target_app": app.get("slug", "not_available"),
        "target_mascot": mascot,
        "requested_metrics": metric_names,
        "full_history_requested": False,
        "raw_conversation_requested": False,
        "credential_requested": False,
        "status": "planned" if app else "not_available",
    }
    payload["sha256"] = payload_sha256(payload)
    return payload


def build_professor_decision(report_id: str, teacher_session_id: str, decision: str, note: str = "") -> dict[str, Any]:
    payload = {
        "schema": "ffed.qlc.professor_decision.v1",
        "decision_id": f"decision-{uuid.uuid4().hex[:16]}",
        "report_id": report_id,
        "teacher_session_id": teacher_session_id,
        "decision": decision,
        "note": note,
        "created_at": utc_now(),
    }
    validate_contract(payload)
    return payload
