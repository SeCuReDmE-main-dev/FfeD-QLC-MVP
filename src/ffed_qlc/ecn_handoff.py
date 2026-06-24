from __future__ import annotations

from typing import Any, Mapping, Sequence


FORBIDDEN_ECN_FIELDS = {
    "api_key",
    "authorization",
    "browsing_history",
    "credential",
    "full_activity_dump",
    "password",
    "private_key",
    "raw_activity",
    "raw_browsing_history",
    "raw_payload",
    "raw_secret",
    "screenshot",
    "screenshots",
    "secret",
    "token",
}


def build_ecn_handoff_packet(
    audit_orb: Mapping[str, Any],
    *,
    urgency: str = "normal",
    destination: str = "ecn://default",
) -> dict[str, Any]:
    """Convert a privacy-safe audit orb into a filtered ECN handoff packet."""

    _reject_forbidden_fields(audit_orb)
    if audit_orb.get("schema") != "ffed.qlc.privacy_safe_audit_orb.v1":
        raise ValueError("ECN handoff requires a privacy-safe audit orb")
    events = audit_orb.get("events") or []
    if not isinstance(events, Sequence) or isinstance(events, (str, bytes, bytearray)):
        raise ValueError("audit orb events must be a sequence")
    event_fingerprints = []
    for event in events:
        if not isinstance(event, Mapping):
            continue
        if event.get("raw_payload_embedded") is not False:
            raise ValueError("ECN handoff accepts metadata-only events")
        event_fingerprints.append(str(event.get("fingerprint") or "")[:64])
    return {
        "schema": "ffed.qlc.ecn_handoff_packet.v1",
        "destination": str(destination)[:160],
        "urgency": _normalize_urgency(urgency),
        "audit_nonce": str(audit_orb.get("audit_nonce") or "")[:64],
        "orb_id": str(audit_orb.get("orb_id") or "")[:120],
        "event_count": int(audit_orb.get("event_count") or len(event_fingerprints)),
        "fibonacci_tag": audit_orb.get("fibonacci_tag"),
        "label_fingerprints": list(audit_orb.get("label_fingerprints") or []),
        "event_fingerprints": event_fingerprints,
        "raw_payload_embedded": False,
        "claim_boundary": "ecn_metadata_handoff_not_raw_activity_or_secret_transfer",
    }


def _reject_forbidden_fields(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in FORBIDDEN_ECN_FIELDS and normalized != "secret_manager_ref":
                raise ValueError(f"raw ECN field is not allowed: {key}")
            _reject_forbidden_fields(nested)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _reject_forbidden_fields(item)


def _normalize_urgency(value: str) -> str:
    normalized = (value or "normal").lower().strip()
    if normalized not in {"low", "normal", "high", "critical"}:
        return "normal"
    return normalized
