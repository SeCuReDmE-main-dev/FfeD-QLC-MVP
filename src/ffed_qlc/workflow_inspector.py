from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from .workflow import GATEWAY_SUBMISSION_SCHEMA, WORKFLOW_SCHEMA


WORKFLOW_INSPECTION_SCHEMA = "ffed.qlc.workflow_inspection.v1"

FORBIDDEN_INSPECTION_FIELDS = {
    "api_key",
    "authorization",
    "browsing_history",
    "credential",
    "full_activity_dump",
    "image_bytes",
    "ocr_text",
    "password",
    "private_key",
    "raw_activity",
    "raw_browsing_history",
    "raw_image",
    "raw_ocr",
    "raw_payload",
    "raw_secret",
    "screenshot",
    "screenshots",
    "secret",
    "token",
    "video_bytes",
}


def inspect_qlc_workflow_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a QLC workflow/gateway bundle and return a compact public summary."""

    _reject_forbidden_fields(bundle)
    submission = _extract_submission(bundle)
    mesh_payload = _mapping(submission.get("mesh_payload"))
    plugin_context = _mapping(mesh_payload.get("plugin_context"))
    swop = _mapping(plugin_context.get("sensitivity_weighted_obfuscation_policy"))
    artifacts = _mapping(bundle.get("artifacts"))
    route_decision = _mapping(artifacts.get("route_decision"))
    route_action = str(route_decision.get("action") or submission.get("route_action") or "unknown")[:80]
    raw_flags = {
        "bundle_raw_media_embedded": bool(bundle.get("raw_media_embedded", False)),
        "bundle_raw_payload_embedded": bool(bundle.get("raw_payload_embedded", False)),
        "submission_raw_payload_embedded": bool(submission.get("raw_payload_embedded", False)),
        "mesh_raw_payload_exposed": bool(mesh_payload.get("raw_payload_exposed", False)),
    }
    redaction_verdict = "metadata_only_pass" if not any(raw_flags.values()) else "review_required"
    return {
        "success": redaction_verdict == "metadata_only_pass",
        "schema": WORKFLOW_INSPECTION_SCHEMA,
        "bundle_schema": str(bundle.get("schema") or submission.get("schema") or "")[:120],
        "workflow_fingerprint": str(submission.get("workflow_fingerprint") or bundle.get("workflow_fingerprint") or "")[:64],
        "media_type": str(bundle.get("media_type") or swop.get("media_type") or "unknown")[:40],
        "swop_level": str(swop.get("sensitivity_level") or "unknown")[:40],
        "route_action": route_action,
        "target_endpoint": str(submission.get("target_endpoint") or "POST /cerebrum/runtime/run")[:120],
        "redaction_verdict": redaction_verdict,
        "raw_flags": raw_flags,
        "fingerprints": {
            "bundle": _fingerprint(bundle),
            "gateway_submission": _fingerprint(submission),
            "mesh_payload": str(submission.get("mesh_payload_fingerprint") or _fingerprint(mesh_payload))[:64],
            "route_decision": _fingerprint(route_decision),
        },
        "raw_payload_embedded": False,
        "claim_boundary": "metadata_only_workflow_inspection_not_runtime_or_cryptographic_certification",
    }


def _extract_submission(bundle: Mapping[str, Any]) -> Mapping[str, Any]:
    if bundle.get("schema") == WORKFLOW_SCHEMA:
        submission = _mapping(bundle.get("gateway_submission"))
    elif bundle.get("schema") == GATEWAY_SUBMISSION_SCHEMA:
        submission = bundle
    else:
        raise ValueError("QLC inspection requires a protection workflow bundle or gateway submission")
    if submission.get("schema") != GATEWAY_SUBMISSION_SCHEMA:
        raise ValueError("QLC gateway submission schema is missing")
    if not isinstance(submission.get("mesh_payload"), Mapping):
        raise ValueError("QLC gateway submission requires mesh_payload")
    return submission


def _reject_forbidden_fields(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in FORBIDDEN_INSPECTION_FIELDS and normalized != "secret_manager_ref":
                raise ValueError(f"raw QLC workflow field is not allowed: {key}")
            _reject_forbidden_fields(nested)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _reject_forbidden_fields(item)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
