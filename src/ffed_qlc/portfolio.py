"""Reproducible public-safe portfolio exports."""

from __future__ import annotations

import uuid
from typing import Any

from .contracts import payload_sha256, utc_now, validate_contract
from .storage import AlphaStore


def build_portfolio_case_study(store: AlphaStore, project_id: str) -> dict[str, Any]:
    bundle = store.project_bundle(project_id)
    evidence_refs = [run["evidence_ref"] for run in bundle["runs"] if run.get("evidence_ref")]
    decisions = [item["decision"] for item in bundle["decisions"]]
    project = bundle["project"]
    payload = {
        "schema": "ffed.qlc.portfolio_case_study.v1",
        "case_study_id": f"case-{uuid.uuid4().hex[:16]}",
        "project_id": project_id,
        "title": project["title"],
        "level": project["level"],
        "evidence_refs": evidence_refs,
        "decisions": decisions,
        "claim_boundary": "supervised_education_alpha_not_security_certification",
        "github_import_mode": "read_only",
        "azure_readiness": {
            "status": "evidence_export_ready",
            "deployment_performed": False,
            "routes": ["codex_openai", "antigravity_gemini"],
        },
        "created_at": utc_now(),
    }
    payload["sha256"] = payload_sha256(payload)
    validate_contract(payload)
    return payload

