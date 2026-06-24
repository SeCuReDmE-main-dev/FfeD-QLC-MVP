from ffed_qlc import build_celebrum_roi_map, build_fnpqnn_runtime_payload, build_gateway_command_plan, pack_bytes


def test_celebrum_roi_map_is_metadata_only() -> None:
    roi_map = build_celebrum_roi_map(
        [
            {
                "class_name": "screen",
                "confidence_score": 0.82,
                "bounding_box_normalized": [0.1, 0.2, 0.3, 0.4],
            }
        ]
    )

    assert roi_map["orchestrator"] == "CeLeBrUm"
    assert roi_map["perception_source"] == "YOLO"
    assert roi_map["runtime_memory_surface"] == "Cerebrum"
    assert roi_map["detection_count"] == 1
    assert roi_map["policy"]["raw_image_embedded"] is False


def test_mesh_proof_payload_targets_fnpqnn_runtime() -> None:
    container = pack_bytes(b"payload", "passphrase")

    payload = build_fnpqnn_runtime_payload(
        source_id="asset-001",
        qlc_container=container,
        yolo_detections=[
            {
                "class_name": "face",
                "confidence_score": 0.91,
                "bounding_box_normalized": [0.5, 0.5, 0.2, 0.3],
            }
        ],
        known_mesh_servers=["ai-node-01"],
    )

    assert payload["run_qnn"] is True
    assert payload["hydra_em_enabled"] is True
    assert payload["gpcn_set_phi_enabled"] is True
    assert payload["orch_or_simulation_enabled"] is True
    assert payload["cpai_context"]["nodes_active"] == 2
    assert payload["memories"][0]["provenance"]["target_endpoint"] == "POST /cerebrum/runtime/run"
    assert payload["memories"][0]["provenance"]["gateway"]["orchestrator"] == "CeLeBrUm"
    assert payload["memories"][0]["provenance"]["gateway"]["runtime_memory_surface"] == "Cerebrum"
    assert payload["memories"][1]["source"] == "codeproject-ai-yolo"
    assert payload["memories"][1]["provenance"]["bridge"] == "codeproject-yolo-to-celebrum-to-cerebrum"
    assert payload["concept_remap"]["mvp_runtime_role"] == "CeLeBrUm"
    assert payload["plugin_context"]["celebrum_roi_map"]["policy"]["raw_image_embedded"] is False
    semantic_map = payload["plugin_context"]["semantic_complexity_map"]
    assert semantic_map["schema"] == "ffed.qlc.semantic_complexity_map.v1"
    assert semantic_map["regions"][0]["parameters"]["lattice_density_multiplier"] == 2.0
    assert semantic_map["regions"][0]["phason_strain_gradient"]["enabled"] is True


def test_gateway_command_plan_names_codeproject_and_fnpqnn() -> None:
    plan = build_gateway_command_plan(qlc_payload_path="qlc-runtime.json")

    assert plan["gateway_repo"] == "fnpqnn_gateway_MVP"
    assert "codeproject-ai-mesh" in plan["commands"]["activate_celebrum_codeproject_mesh"]
    assert "mesh-status" in plan["commands"]["check_codeproject_mesh"]
    assert "http://localhost:8000/cerebrum/runtime/run" in plan["commands"]["post_payload"]


def test_mesh_proof_names_qlc_mvp_protects_simulator_side() -> None:
    container = pack_bytes(b"simulator runtime artifact", "passphrase")

    payload = build_fnpqnn_runtime_payload(
        source_id="runtime-artifact-001",
        qlc_container=container,
        proof_mode="qlc_protects_simulator_mvp",
    )

    protection_case = payload["plugin_context"]["simulator_protection_case"]
    assert payload["proof_goal"] == "demonstrate_qlc_mvp_by_protecting_fnpqnn_simulator_artifacts"
    assert payload["plugin_context"]["proof_mode"] == "qlc_protects_simulator_mvp"
    assert protection_case["protected_surface"]["runtime_surface"] == "Cerebrum"
    assert protection_case["qlc_role"] == "protection_layer_for_simulator_artifacts"
    assert protection_case["mvp_coupling"] == "reciprocal_proof_loop_between_FfeD_QLC_MVP_and_FNP_QNN_MVP"
    assert "tampered_qlc_container_fails_authentication" in protection_case["validated_guarantees"]


def test_mesh_proof_names_simulator_support_side_of_reciprocal_loop() -> None:
    container = pack_bytes(b"qlc complex protocol event", "passphrase")

    payload = build_fnpqnn_runtime_payload(
        source_id="qlc-event-001",
        qlc_container=container,
        proof_mode="simulator_supports_qlc_complexity",
    )

    protection_case = payload["plugin_context"]["simulator_protection_case"]
    assert payload["proof_goal"] == "prove_fnpqnn_mvp_supports_complex_qlc_protocol"
    assert payload["plugin_context"]["proof_mode"] == "simulator_supports_qlc_complexity"
    assert protection_case["simulator_role"] == "supports_and_measures_complex_qlc_protocol"
    assert protection_case["qlc_role"] == "complex_protocol_subject_supported_by_simulator"
    assert protection_case["reciprocal_proof"]["fnp_qnn_proves"].startswith("it_can_support")
