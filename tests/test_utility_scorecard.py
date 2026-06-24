from ffed_qlc import build_fnpqnn_runtime_payload, build_reciprocal_utility_scorecard, pack_bytes


def _mesh_payload(*, guard_context: bool = True) -> dict:
    context = [{"texture_complexity": 0.2, "entropy_score": 0.3, "edge_density": 0.2}] if guard_context else None
    return build_fnpqnn_runtime_payload(
        source_id="asset-001",
        qlc_container=pack_bytes(b"simulator artifact", "passphrase"),
        yolo_detections=[{"class_name": "screen", "confidence_score": 0.92}],
        context_signals=context,
        known_mesh_servers=["node-01"],
    )


def test_scorecard_passes_complete_reciprocal_payload() -> None:
    scorecard = build_reciprocal_utility_scorecard(_mesh_payload())

    assert scorecard["schema"] == "ffed.qlc.reciprocal_utility_scorecard.v1"
    assert scorecard["overall_verdict"] == "reciprocal_pass"
    assert scorecard["simulator_support_score"] >= 0.75
    assert scorecard["qlc_protection_score"] >= 0.75
    assert scorecard["context_risk_pressure"] == 0.0


def test_scorecard_reports_simulator_gap_when_runtime_flags_are_absent() -> None:
    payload = _mesh_payload()
    payload["run_qnn"] = False
    payload["hydra_em_enabled"] = False
    payload["gpcn_set_phi_enabled"] = False
    payload["plugin_hook_enabled"] = False

    scorecard = build_reciprocal_utility_scorecard(payload)

    assert scorecard["overall_verdict"] == "simulator_gap"


def test_scorecard_reports_qlc_gap_when_protection_signals_are_absent() -> None:
    payload = _mesh_payload()
    payload["plugin_context"]["qlc_container_sha256"] = ""
    payload["plugin_context"]["simulator_protection_case"]["validated_guarantees"] = []

    scorecard = build_reciprocal_utility_scorecard(payload)

    assert scorecard["overall_verdict"] == "qlc_gap"


def test_scorecard_needs_review_for_suspended_context_guard() -> None:
    scorecard = build_reciprocal_utility_scorecard(_mesh_payload(guard_context=False))

    assert scorecard["overall_verdict"] == "needs_review"
    assert scorecard["context_risk_pressure"] == 0.5
