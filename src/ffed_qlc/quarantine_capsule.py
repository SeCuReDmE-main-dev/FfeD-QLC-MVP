from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence


FORBIDDEN_QUARANTINE_FIELDS = {
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


def build_human_review_quarantine_capsule(
    route_decision: Mapping[str, Any],
    swop_policy: Mapping[str, Any] | None = None,
    audit_orb: Mapping[str, Any] | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """Turn a review or quarantine route into a metadata-only review capsule."""

    _reject_forbidden_fields(route_decision)
    if swop_policy is not None:
        _reject_forbidden_fields(swop_policy)
    if audit_orb is not None:
        _reject_forbidden_fields(audit_orb)

    action = str(route_decision.get("action") or "human_review")
    sensitivity = str(route_decision.get("sensitivity_level") or _mapping(swop_policy).get("sensitivity_level") or "low")
    guard_verdict = str(route_decision.get("guard_verdict") or "suspend")
    reason_codes = _reason_codes(action, guard_verdict, sensitivity, reason)
    return {
        "schema": "ffed.qlc.human_review_quarantine_capsule.v1",
        "route_action": action,
        "guard_verdict": guard_verdict,
        "sensitivity_level": sensitivity,
        "audit_nonce": str(_mapping(audit_orb).get("audit_nonce") or route_decision.get("audit_nonce") or "")[:64],
        "reason_codes": reason_codes,
        "review_priority": _review_priority(action, sensitivity, guard_verdict),
        "fingerprints": {
            "route_decision": _stable_hash(route_decision),
            "swop_policy": _stable_hash(swop_policy) if swop_policy else "",
            "audit_orb": _stable_hash(audit_orb) if audit_orb else "",
        },
        "raw_payload_embedded": False,
        "claim_boundary": "metadata_only_review_capsule_not_surveillance_or_raw_evidence_storage",
    }


def _reason_codes(action: str, guard_verdict: str, sensitivity: str, reason: str | None) -> list[str]:
    codes = [f"route_{action}", f"guard_{guard_verdict}", f"sensitivity_{sensitivity}"]
    if reason:
        codes.append(str(reason).lower().strip().replace(" ", "_")[:80])
    return codes


def _review_priority(action: str, sensitivity: str, guard_verdict: str) -> str:
    if action == "quarantine":
        return "blocking"
    if sensitivity == "critical" or guard_verdict == "escalate":
        return "urgent_review"
    return "review"


def _reject_forbidden_fields(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in FORBIDDEN_QUARANTINE_FIELDS and normalized != "secret_manager_ref":
                raise ValueError(f"raw quarantine field is not allowed: {key}")
            _reject_forbidden_fields(nested)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _reject_forbidden_fields(item)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
