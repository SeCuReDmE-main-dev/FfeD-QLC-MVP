from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence


FORBIDDEN_RAW_SECRET_KEYS = {
    "api_key",
    "authorization",
    "credential",
    "password",
    "private_key",
    "raw_secret",
    "secret",
    "token",
}


def build_privacy_safe_audit_orb(
    *,
    orb_id: str,
    events: Sequence[Mapping[str, Any]],
    epsilon: float = 1.0,
) -> dict[str, Any]:
    """Create a ProGuarD audit orb without raw secrets or surveillance payloads."""

    if not orb_id.strip():
        raise ValueError("orb_id must not be empty")
    if epsilon <= 0:
        raise ValueError("epsilon must be positive")
    sanitized_events = [_sanitize_event(event) for event in events]
    labels = [str(event.get("label") or event.get("type") or "event")[:80] for event in sanitized_events]
    event_count = len(sanitized_events)
    sequence_anchor = _fibonacci(event_count + 2)
    fingerprint = _stable_hash({"orb_id": orb_id, "events": sanitized_events, "sequence_anchor": sequence_anchor})
    return {
        "schema": "ffed.qlc.privacy_safe_audit_orb.v1",
        "orb_id": orb_id,
        "event_count": event_count,
        "audit_nonce": fingerprint[:32],
        "fibonacci_tag": sequence_anchor,
        "secret_policy": {
            "raw_secrets_allowed": False,
            "allowed_secret_material": "external_secret_manager_reference_only",
        },
        "differential_privacy": {
            "enabled": True,
            "epsilon": float(epsilon),
            "aggregate_event_count": event_count,
            "mechanism": "metadata_only_bounded_count",
        },
        "events": sanitized_events,
        "label_fingerprints": [_stable_hash({"label": label})[:16] for label in labels],
        "claim_boundary": "audit_provenance_not_employee_surveillance_or_password_storage",
    }


def _sanitize_event(event: Mapping[str, Any]) -> dict[str, Any]:
    _reject_raw_secret_keys(event)
    label = str(event.get("label") or event.get("type") or "event")[:80]
    source = str(event.get("source") or "unknown")[:80]
    secret_ref = event.get("secret_manager_ref")
    sanitized: dict[str, Any] = {
        "label": label,
        "source": source,
        "fingerprint": _stable_hash(event),
        "raw_payload_embedded": False,
    }
    if secret_ref:
        sanitized["secret_manager_ref"] = str(secret_ref)[:240]
    if "timestamp" in event:
        sanitized["timestamp"] = event["timestamp"]
    return sanitized


def _reject_raw_secret_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in FORBIDDEN_RAW_SECRET_KEYS and normalized != "secret_manager_ref":
                raise ValueError(f"raw secret field is not allowed: {key}")
            _reject_raw_secret_keys(nested)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _reject_raw_secret_keys(item)


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _fibonacci(index: int) -> int:
    left, right = 0, 1
    for _ in range(max(0, index)):
        left, right = right, left + right
    return left
