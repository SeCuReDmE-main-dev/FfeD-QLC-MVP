from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def build_compact_proof_bundle_receipt(
    qlc_manifest: Mapping[str, Any],
    mesh_payload: Mapping[str, Any],
    audit_orb: Mapping[str, Any] | None = None,
    ecn_packet: Mapping[str, Any] | None = None,
    route_decision: Mapping[str, Any] | None = None,
    *,
    bundle_nonce: str | None = None,
) -> dict[str, Any]:
    """Link QLC proof artifacts through fingerprints without embedding payloads."""

    artifacts = {
        "qlc_manifest": _fingerprint(qlc_manifest),
        "mesh_payload": _fingerprint(mesh_payload),
        "audit_orb": _fingerprint(audit_orb) if audit_orb else "",
        "ecn_packet": _fingerprint(ecn_packet) if ecn_packet else "",
        "route_decision": _fingerprint(route_decision) if route_decision else "",
    }
    active_nonce = str(bundle_nonce or _fingerprint(artifacts)[:32])[:64]
    receipt_fingerprint = _fingerprint({"artifacts": artifacts, "bundle_nonce": active_nonce})
    return {
        "schema": "ffed.qlc.compact_proof_bundle_receipt.v1",
        "bundle_nonce": active_nonce,
        "artifact_fingerprints": artifacts,
        "artifact_count": sum(1 for value in artifacts.values() if value),
        "receipt_fingerprint": receipt_fingerprint,
        "raw_payload_embedded": False,
        "claim_boundary": "compact_mvp_coherence_receipt_not_ledger_blockchain_or_legal_notarization",
    }


def _fingerprint(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
