from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from .audit_orb import build_privacy_safe_audit_orb
from .chunk_protection_plan import build_swop_chunk_protection_plan
from .ecn_handoff import build_ecn_handoff_packet
from .key_schedule import derive_chunk_key_schedule
from .mesh_proof import build_fnpqnn_runtime_payload
from .proof_bundle import build_compact_proof_bundle_receipt
from .protected_intake import build_multimodal_protected_intake_descriptor
from .quarantine_capsule import build_human_review_quarantine_capsule
from .route_decision import build_celebrum_route_decision
from .structural_transform import inspect_container
from .utility_scorecard import build_reciprocal_utility_scorecard


WORKFLOW_SCHEMA = "ffed.qlc.protection_workflow_bundle.v1"
GATEWAY_SUBMISSION_SCHEMA = "ffed.qlc.gateway_submission.v1"
LOOP_RECEIPT_SCHEMA = "ffed.qlc.gateway_celebrum_loop_receipt.v1"
RUNTIME_ENDPOINT = "POST /cerebrum/runtime/run"

FORBIDDEN_WORKFLOW_FIELDS = {
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


def build_qlc_protection_workflow(
    *,
    source_id: str,
    qlc_container: bytes,
    media_type: str = "image",
    detections: Sequence[Mapping[str, Any]] | None = None,
    context_signals: Sequence[Mapping[str, Any]] | None = None,
    codeproject_url: str = "http://localhost:32168",
    known_mesh_servers: Sequence[str] | None = None,
    epochs: int = 4,
    proof_mode: str = "simulator_supports_qlc_complexity",
    audit_events: Sequence[Mapping[str, Any]] | None = None,
    audit_orb_id: str | None = None,
    ecn_destination: str = "ecn://celebrum",
    ecn_urgency: str = "normal",
    chunk_count: int | None = None,
) -> dict[str, Any]:
    """Assemble the QLC metadata-only protection workflow bundle."""

    if not source_id.strip():
        raise ValueError("source_id must not be empty")
    if not qlc_container:
        raise ValueError("qlc_container must not be empty")
    active_detections = list(detections or [])
    active_context = list(context_signals or [])
    _reject_forbidden_fields(active_detections)
    _reject_forbidden_fields(active_context)
    if audit_events is not None:
        _reject_forbidden_fields(audit_events)

    source_fingerprint = hashlib.sha256(qlc_container).hexdigest()
    inspection = inspect_container(qlc_container)
    qlc_manifest = _mapping(inspection.get("qlc_manifest"))
    intake = build_multimodal_protected_intake_descriptor(
        media_type=media_type,
        source_id=source_id,
        source_fingerprint=source_fingerprint,
        detections=active_detections,
        context_signals=active_context,
    )
    mesh_payload = build_fnpqnn_runtime_payload(
        source_id=source_id,
        qlc_container=qlc_container,
        yolo_detections=active_detections,
        context_signals=active_context,
        media_type=media_type,
        codeproject_url=codeproject_url,
        known_mesh_servers=known_mesh_servers,
        epochs=epochs,
        proof_mode=proof_mode,  # type: ignore[arg-type]
    )
    plugin_context = _mapping(mesh_payload.get("plugin_context"))
    swop_policy = _mapping(plugin_context.get("sensitivity_weighted_obfuscation_policy"))
    active_chunk_count = max(1, int(chunk_count if chunk_count is not None else _default_chunk_count(swop_policy)))
    chunk_key_schedule = derive_chunk_key_schedule(qlc_container, active_chunk_count)
    chunk_protection_plan = build_swop_chunk_protection_plan(swop_policy, chunk_key_schedule)

    audit_orb = build_privacy_safe_audit_orb(
        orb_id=audit_orb_id or f"{source_id}:workflow",
        events=list(audit_events or _default_audit_events(source_id, mesh_payload, swop_policy)),
    )
    ecn_packet = build_ecn_handoff_packet(audit_orb, urgency=ecn_urgency, destination=ecn_destination)
    route_decision = build_celebrum_route_decision(mesh_payload, audit_orb=audit_orb, ecn_packet=ecn_packet)
    quarantine_capsule = None
    if route_decision.get("action") in {"human_review", "quarantine"}:
        quarantine_capsule = build_human_review_quarantine_capsule(
            route_decision,
            swop_policy=swop_policy,
            audit_orb=audit_orb,
            reason="workflow_route_requires_review",
        )
    proof_receipt = build_compact_proof_bundle_receipt(
        qlc_manifest,
        mesh_payload,
        audit_orb=audit_orb,
        ecn_packet=ecn_packet,
        route_decision=route_decision,
    )
    utility_scorecard = build_reciprocal_utility_scorecard(mesh_payload)
    workflow_fingerprint = _fingerprint(
        {
            "intake": intake,
            "mesh_payload": mesh_payload,
            "chunk_protection_plan": chunk_protection_plan,
            "audit_orb": audit_orb,
            "ecn_packet": ecn_packet,
            "route_decision": route_decision,
            "proof_receipt": proof_receipt,
            "utility_scorecard": utility_scorecard,
        }
    )
    gateway_submission = {
        "schema": GATEWAY_SUBMISSION_SCHEMA,
        "source_workflow_schema": WORKFLOW_SCHEMA,
        "workflow_fingerprint": workflow_fingerprint,
        "source_id": source_id[:160],
        "target_endpoint": RUNTIME_ENDPOINT,
        "simulator_runtime": "Cerebrum",
        "orchestrator": "CeLeBrUm",
        "mesh_payload": mesh_payload,
        "mesh_payload_fingerprint": _fingerprint(mesh_payload),
        "route_action": str(route_decision.get("action") or "submit_to_cerebrum"),
        "raw_payload_embedded": False,
        "claim_boundary": "gateway_submission_contract_for_mvp_runtime_not_raw_media_or_secret_transfer",
    }
    return {
        "schema": WORKFLOW_SCHEMA,
        "source_id": source_id[:160],
        "media_type": intake["media_type"],
        "workflow_fingerprint": workflow_fingerprint,
        "raw_media_embedded": False,
        "raw_payload_embedded": False,
        "artifacts": {
            "intake_descriptor": intake,
            "qlc_manifest": qlc_manifest,
            "mesh_payload": mesh_payload,
            "chunk_key_schedule": chunk_key_schedule,
            "swop_chunk_protection_plan": chunk_protection_plan,
            "audit_orb": audit_orb,
            "ecn_packet": ecn_packet,
            "route_decision": route_decision,
            "quarantine_capsule": quarantine_capsule,
            "proof_bundle_receipt": proof_receipt,
            "reciprocal_utility_scorecard": utility_scorecard,
        },
        "gateway_submission": gateway_submission,
        "claim_boundary": "metadata_only_qlc_workflow_threading_not_production_security_or_quantum_proof_certification",
    }


def build_gateway_celebrum_loop_receipt(
    workflow_bundle: Mapping[str, Any],
    simulator_result: Mapping[str, Any],
) -> dict[str, Any]:
    """Link a gateway simulator result back into the CeLeBrUm route decision."""

    _reject_forbidden_fields(workflow_bundle)
    _reject_forbidden_fields(simulator_result)
    if workflow_bundle.get("schema") != WORKFLOW_SCHEMA:
        raise ValueError("loop receipt requires a QLC protection workflow bundle")
    artifacts = _mapping(workflow_bundle.get("artifacts"))
    route_decision = _mapping(artifacts.get("route_decision"))
    swop_policy = _mapping(_mapping(artifacts.get("mesh_payload")).get("plugin_context")).get(
        "sensitivity_weighted_obfuscation_policy",
        {},
    )
    simulator_status = str(simulator_result.get("status") or "unknown")[:80]
    guard_verdict = str(route_decision.get("guard_verdict") or "suspend")
    sensitivity_level = str(_mapping(swop_policy).get("sensitivity_level") or route_decision.get("sensitivity_level") or "low")
    route_action = _loop_action(
        prior_action=str(route_decision.get("action") or "human_review"),
        simulator_status=simulator_status,
        guard_verdict=guard_verdict,
        sensitivity_level=sensitivity_level,
    )
    return {
        "schema": LOOP_RECEIPT_SCHEMA,
        "workflow_fingerprint": str(workflow_bundle.get("workflow_fingerprint") or "")[:64],
        "simulator_status": simulator_status,
        "route_action": route_action,
        "prior_route_action": str(route_decision.get("action") or "")[:80],
        "guard_verdict": guard_verdict,
        "sensitivity_level": sensitivity_level,
        "fingerprints": {
            "workflow_bundle": _fingerprint(workflow_bundle),
            "gateway_submission": _fingerprint(workflow_bundle.get("gateway_submission") or {}),
            "simulator_result": _fingerprint(_safe_simulator_result(simulator_result)),
            "route_decision": _fingerprint(route_decision),
        },
        "raw_payload_embedded": False,
        "claim_boundary": "gateway_celebrum_loop_receipt_for_mvp_feedback_not_raw_runtime_evidence",
    }


def _default_audit_events(
    source_id: str,
    mesh_payload: Mapping[str, Any],
    swop_policy: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "label": "qlc-workflow-built",
            "source": "ffed-qlc-mvp",
            "source_id": source_id,
            "mesh_payload_fingerprint": _fingerprint(mesh_payload),
            "swop_level": str(swop_policy.get("sensitivity_level") or "low"),
        }
    ]


def _default_chunk_count(swop_policy: Mapping[str, Any]) -> int:
    regions = swop_policy.get("regions") or []
    if isinstance(regions, Sequence) and not isinstance(regions, (str, bytes, bytearray)):
        return len(regions) or 1
    return 1


def _loop_action(*, prior_action: str, simulator_status: str, guard_verdict: str, sensitivity_level: str) -> str:
    if simulator_status not in {"ok", "accepted", "success"}:
        return "human_review"
    if guard_verdict == "escalate" or sensitivity_level == "critical":
        return "quarantine"
    if prior_action in {"gateway_handoff", "submit_to_cerebrum"}:
        return prior_action
    return "human_review"


def _safe_simulator_result(simulator_result: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "status": str(simulator_result.get("status") or "unknown")[:80],
        "runtime_fingerprint": _fingerprint(simulator_result.get("runtime") or {}),
        "persistence_fingerprint": _fingerprint(simulator_result.get("persistence") or {}),
    }


def _reject_forbidden_fields(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in FORBIDDEN_WORKFLOW_FIELDS and normalized != "secret_manager_ref":
                raise ValueError(f"raw workflow field is not allowed: {key}")
            _reject_forbidden_fields(nested)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _reject_forbidden_fields(item)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
