from ffed_qlc import (
    build_celebrum_route_decision,
    build_compact_proof_bundle_receipt,
    build_ecn_handoff_packet,
    build_fnpqnn_runtime_payload,
    build_privacy_safe_audit_orb,
    inspect_container,
    pack_bytes,
)


def _artifacts() -> tuple[dict, dict, dict, dict, dict]:
    container = pack_bytes(b"proof bundle artifact", "passphrase")
    manifest = inspect_container(container)["qlc_manifest"]
    mesh = build_fnpqnn_runtime_payload(
        source_id="asset-001",
        qlc_container=container,
        yolo_detections=[{"class_name": "screen", "confidence_score": 0.91}],
        context_signals=[{"texture_complexity": 0.2, "entropy_score": 0.2, "edge_density": 0.2}],
    )
    orb = build_privacy_safe_audit_orb(orb_id="orb-001", events=[{"label": "safe", "source": "test"}])
    ecn = build_ecn_handoff_packet(orb, destination="ecn://celebrum")
    route = build_celebrum_route_decision(mesh, audit_orb=orb, ecn_packet=ecn)
    return manifest, mesh, orb, ecn, route


def test_compact_proof_bundle_receipt_is_deterministic_for_same_inputs() -> None:
    artifacts = _artifacts()
    receipt = build_compact_proof_bundle_receipt(*artifacts)
    same = build_compact_proof_bundle_receipt(*artifacts)

    assert receipt == same
    assert receipt["schema"] == "ffed.qlc.compact_proof_bundle_receipt.v1"
    assert receipt["artifact_count"] == 5
    assert receipt["raw_payload_embedded"] is False


def test_compact_proof_bundle_receipt_changes_when_mesh_changes() -> None:
    manifest, mesh, orb, ecn, route = _artifacts()
    first = build_compact_proof_bundle_receipt(manifest, mesh, orb, ecn, route)
    mesh["epochs"] = 8
    second = build_compact_proof_bundle_receipt(manifest, mesh, orb, ecn, route)

    assert first["artifact_fingerprints"]["mesh_payload"] != second["artifact_fingerprints"]["mesh_payload"]
    assert first["receipt_fingerprint"] != second["receipt_fingerprint"]


def test_compact_proof_bundle_receipt_exposes_fingerprints_only() -> None:
    receipt = build_compact_proof_bundle_receipt(*_artifacts(), bundle_nonce="nonce-001")

    assert receipt["bundle_nonce"] == "nonce-001"
    assert "proof bundle artifact" not in str(receipt)
    assert set(receipt["artifact_fingerprints"]) == {
        "qlc_manifest",
        "mesh_payload",
        "audit_orb",
        "ecn_packet",
        "route_decision",
    }
