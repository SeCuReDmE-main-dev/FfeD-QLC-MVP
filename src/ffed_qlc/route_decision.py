from __future__ import annotations

from typing import Any, Mapping, Sequence


FORBIDDEN_ROUTE_FIELDS = {
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
}


def build_celebrum_route_decision(
    mesh_payload: Mapping[str, Any],
    audit_orb: Mapping[str, Any] | None = None,
    ecn_packet: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a metadata-only CeLeBrUm route decision envelope."""

    _reject_forbidden_fields(mesh_payload)
    if audit_orb is not None:
        _reject_forbidden_fields(audit_orb)
    if ecn_packet is not None:
        _reject_forbidden_fields(ecn_packet)

    plugin_context = _mapping(mesh_payload.get("plugin_context"))
    guard = _mapping(plugin_context.get("context_consistency_guard"))
    swop = _mapping(plugin_context.get("sensitivity_weighted_obfuscation_policy"))
    guard_verdict = str(guard.get("verdict") or "suspend")
    sensitivity_level = str(swop.get("sensitivity_level") or "low")
    admissible = mesh_payload.get("fractal_admissible") is not False
    has_ecn_destination = bool(_mapping(ecn_packet).get("destination"))

    action = _route_action(
        guard_verdict=guard_verdict,
        sensitivity_level=sensitivity_level,
        admissible=admissible,
        has_ecn_destination=has_ecn_destination,
    )
    return {
        "schema": "ffed.qlc.celebrum_route_decision.v1",
        "orchestrator": "CeLeBrUm",
        "runtime_memory_surface": "Cerebrum",
        "action": action,
        "guard_verdict": guard_verdict,
        "sensitivity_level": sensitivity_level,
        "admissible": admissible,
        "audit_nonce": str(_mapping(audit_orb).get("audit_nonce") or "")[:64],
        "ecn_destination": str(_mapping(ecn_packet).get("destination") or "")[:160],
        "raw_payload_embedded": False,
        "claim_boundary": "metadata_only_orchestrator_decision_not_autonomous_truth_model",
    }


def _route_action(*, guard_verdict: str, sensitivity_level: str, admissible: bool, has_ecn_destination: bool) -> str:
    if not admissible:
        return "quarantine"
    if guard_verdict == "escalate":
        return "human_review"
    if guard_verdict == "suspend":
        return "human_review"
    if sensitivity_level == "critical":
        return "human_review"
    if has_ecn_destination:
        return "gateway_handoff"
    return "submit_to_cerebrum"


def _reject_forbidden_fields(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in FORBIDDEN_ROUTE_FIELDS and normalized != "secret_manager_ref":
                raise ValueError(f"raw route field is not allowed: {key}")
            _reject_forbidden_fields(nested)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _reject_forbidden_fields(item)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
