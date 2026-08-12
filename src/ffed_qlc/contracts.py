"""Versioned, credential-blind contracts for the FfeD-QLC alpha."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Mapping


FRACTAL_HIERARCHY = ("I", "I_system^S", "D_f", "dF", "i_fractal")
ROLES = ("student_minor", "student_adult", "teacher")
PROVIDERS = ("codex", "gemini")
DECISIONS = ("accept", "suspend", "reject", "revise")

SCHEMA_REQUIRED: dict[str, tuple[str, ...]] = {
    "securedme.education.session-role.v1": (
        "session_id", "fingerprint_ref", "role", "surface", "consent_scope",
        "allowed_tools", "expires_at",
    ),
    "ffed.qlc.fixture.v1": (
        "fixture_id", "title", "kind", "sha256", "difficulty", "provenance",
    ),
    "ffed.qlc.geometry_trace.v1": (
        "trace_id", "algorithm", "steps", "collisions", "cycles", "sha256",
    ),
    "ffed.qlc.orb_public.v1": (
        "orb_id", "project_id", "geometry_profile", "evidence_refs", "claim_boundary",
    ),
    "ffed.qlc.orb_project.v1": (
        "project_id", "session_id", "title", "level", "status", "created_at",
    ),
    "ffed.qlc.mission_run.v1": (
        "run_id", "project_id", "lab_id", "state", "attempt_count", "created_at",
    ),
    "ffed.qlc.vigil_report.v1": (
        "report_id", "run_id", "observation", "mechanism", "attack", "evidence",
        "limitation", "decision", "safe_next_action", "provider_route",
    ),
    "ffed.qlc.professor_decision.v1": (
        "decision_id", "report_id", "teacher_session_id", "decision", "created_at",
    ),
    "ffed.qlc.learning_evidence.v1": (
        "evidence_id", "project_id", "artifact_sha256", "claim", "limitation",
    ),
    "ffed.qlc.portfolio_case_study.v1": (
        "case_study_id", "project_id", "title", "evidence_refs", "decisions", "sha256",
    ),
}

FORBIDDEN_KEYS = {
    ".env", "api_key", "browser_session", "client_secret", "cookie", "oauth_token",
    "password", "raw_chat_log", "raw_prompt", "roster", "secret", "session_cookie",
    "student_email", "student_id", "student_name", "token",
}
ALLOWED_SAFETY_FLAGS = {
    "raw_secret_stored", "raw_payload_embedded", "raw_payload_exposed", "raw_values_printed",
    "secret_values_exposed",
}


class ContractError(ValueError):
    """Raised when an alpha contract crosses its safety boundary."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def payload_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def validate_contract(payload: Mapping[str, Any], expected_schema: str | None = None) -> None:
    schema = str(payload.get("schema", ""))
    if expected_schema and schema != expected_schema:
        raise ContractError(f"expected schema {expected_schema}")
    if schema not in SCHEMA_REQUIRED:
        raise ContractError("unsupported contract schema")
    missing = [field for field in SCHEMA_REQUIRED[schema] if payload.get(field) in (None, "", [])]
    if missing:
        raise ContractError(f"missing contract fields: {', '.join(missing)}")
    reject_secret_material(payload)
    if schema == "securedme.education.session-role.v1":
        role = str(payload["role"])
        if role not in ROLES:
            raise ContractError("unsupported Education role")
        expected_surface = "teacher" if role == "teacher" else "student"
        if payload.get("surface") != expected_surface:
            raise ContractError("role and surface do not match")
    if schema == "ffed.qlc.vigil_report.v1":
        if payload.get("provider_route") != "ffed-deterministic-engine":
            raise ContractError("unsupported Vigil provider route")
        if payload.get("decision") not in DECISIONS:
            raise ContractError("unsupported Vigil recommendation")
    if schema == "ffed.qlc.professor_decision.v1" and payload.get("decision") not in DECISIONS:
        raise ContractError("unsupported professor decision")


def reject_secret_material(value: Any) -> None:
    for key, nested in _walk(value):
        normalized = key.lower()
        if normalized in ALLOWED_SAFETY_FLAGS:
            if nested is not False:
                raise ContractError(f"{key} must remain false")
            continue
        if normalized in FORBIDDEN_KEYS or normalized.startswith("raw_"):
            raise ContractError(f"forbidden field: {key}")


def contract_schemas() -> dict[str, dict[str, Any]]:
    """Return portable JSON Schema documents for Python and TypeScript clients."""
    schemas: dict[str, dict[str, Any]] = {}
    for schema, required in SCHEMA_REQUIRED.items():
        schemas[schema] = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": schema,
            "type": "object",
            "required": ["schema", *required],
            "properties": {"schema": {"const": schema}},
            "additionalProperties": True,
        }
    return schemas


def _walk(value: Any):
    if isinstance(value, Mapping):
        for key, nested in value.items():
            yield str(key), nested
            yield from _walk(nested)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _walk(item)
