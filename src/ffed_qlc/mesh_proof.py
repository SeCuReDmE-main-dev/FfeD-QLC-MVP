from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Literal, Mapping, Sequence


ProofMode = Literal[
    "simulator_supports_qlc_complexity",
    "qlc_protects_simulator_mvp",
]
CanonicalProofMode = Literal["simulator_supports_qlc_complexity", "qlc_protects_simulator_mvp"]


@dataclass(frozen=True)
class YOLODetection:
    label: str
    confidence: float
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "YOLODetection":
        box = payload.get("bounding_box_normalized") or payload.get("box") or [0.0, 0.0, 0.0, 0.0]
        if not isinstance(box, Sequence) or isinstance(box, (str, bytes, bytearray)):
            box = [0.0, 0.0, 0.0, 0.0]
        padded = list(box[:4]) + [0.0, 0.0, 0.0, 0.0]
        return cls(
            label=str(payload.get("class_name") or payload.get("label") or payload.get("name") or "object")[:120],
            confidence=_clamp01(payload.get("confidence_score", payload.get("confidence", 0.0))),
            x=_clamp01(padded[0]),
            y=_clamp01(padded[1]),
            width=_clamp01(padded[2]),
            height=_clamp01(padded[3]),
        )

    @property
    def area(self) -> float:
        return _clamp01(self.width * self.height)


def build_celebrum_roi_map(
    yolo_detections: Sequence[Mapping[str, Any] | YOLODetection] | None = None,
) -> dict[str, Any]:
    """Build the CeLeBrUm ROI/semantic map from YOLO metadata only."""

    detections = [_normalize_detection(item) for item in (yolo_detections or [])]
    items = [
        {
            "label": detection.label,
            "confidence": detection.confidence,
            "box": [detection.x, detection.y, detection.width, detection.height],
            "area": detection.area,
            "priority": "high" if detection.confidence >= 0.75 or detection.area >= 0.25 else "normal",
        }
        for detection in detections
    ]
    semantic_score = _semantic_score(detections)
    return {
        "schema": "ffed.qlc.celebrum_roi_map.v1",
        "orchestrator": "CeLeBrUm",
        "perception_source": "YOLO",
        "runtime_memory_surface": "Cerebrum",
        "detection_count": len(items),
        "semantic_score": semantic_score,
        "regions": items,
        "policy": {
            "raw_image_embedded": False,
            "redaction_mode": "roi_metadata_only",
            "simulator_handoff": "metadata_to_POST_/cerebrum/runtime/run",
        },
    }


def build_fnpqnn_runtime_payload(
    *,
    source_id: str,
    qlc_container: bytes,
    yolo_detections: Sequence[Mapping[str, Any] | YOLODetection] | None = None,
    codeproject_url: str = "http://localhost:32168",
    known_mesh_servers: Sequence[str] | None = None,
    epochs: int = 4,
    proof_mode: ProofMode = "simulator_supports_qlc_complexity",
) -> dict[str, Any]:
    """Build the simulator payload proving QLC utility through FNP-QNN.

    The payload is shaped for FNP-QNN `POST /cerebrum/runtime/run`. It lets the
    CeLeBrUm-facing route submit QLC container complexity, YOLO perception,
    CPAI mesh routing, LVFM graph formation, and Hydra/GPCN simulation signals
    in one run. CeLeBrUm is the orchestrator; Cerebrum is the simulator runtime
    endpoint and memory shape.
    """

    detections = [_normalize_detection(item) for item in (yolo_detections or [])]
    active_proof_mode = _normalize_proof_mode(proof_mode)
    roi_map = build_celebrum_roi_map(detections)
    container_sha256 = hashlib.sha256(qlc_container).hexdigest()
    structural_score = _structural_score(qlc_container)
    semantic_score = _semantic_score(detections)
    mesh_servers = list(known_mesh_servers or [])
    nodes_active = max(1, 1 + len(mesh_servers))
    protection_case = _simulator_protection_case(
        mode=active_proof_mode,
        container_sha256=container_sha256,
        container_size_bytes=len(qlc_container),
    )

    memories: list[dict[str, Any]] = [
        {
            "modality": "stimuli",
            "starting_time": 0.0,
            "ending_time": 1.0,
            "value": structural_score,
            "label": "qlc-container",
            "source": "ffed-qlc-mvp",
            "payload_ref": source_id,
            "provenance": {
                "bridge": "qlc-to-fnpqnn-gateway",
                "target_endpoint": "POST /cerebrum/runtime/run",
                "qlc": {
                    "container_sha256": container_sha256,
                    "container_size_bytes": len(qlc_container),
                    "structural_score": structural_score,
                    "raw_payload_exposed": False,
                },
                "gateway": {
                    "repo": "fnpqnn_gateway_MVP",
                    "codeproject_url": codeproject_url,
                    "codeproject_hook": "codeproject-ai-mesh",
                    "orchestrator": "CeLeBrUm",
                    "runtime_memory_surface": "Cerebrum",
                },
                "simulator_protection_case": protection_case,
            },
        }
    ]
    for index, detection in enumerate(detections, start=1):
        memories.append(
            {
                "modality": "vision",
                "starting_time": float(index),
                "ending_time": float(index) + 1.0,
                "value": _clamp01((detection.confidence * 0.7) + (detection.area * 0.3)),
                "label": detection.label,
                "source": "codeproject-ai-yolo",
                "payload_ref": f"{source_id}:yolo:{index}",
                "provenance": {
                    "bridge": "codeproject-yolo-to-celebrum-to-cerebrum",
                    "orchestrator": "CeLeBrUm",
                    "runtime_memory_surface": "Cerebrum",
                    "confidence": detection.confidence,
                    "box": [detection.x, detection.y, detection.width, detection.height],
                    "area": detection.area,
                    "privacy_note": "detection metadata only; image bytes not embedded",
                },
            }
        )

    lattice_seed = int(container_sha256[:8], 16)
    fractal_dimension = 1.0 + _clamp01((structural_score + semantic_score) / 2.0)
    local_load = _clamp01((structural_score * 0.6) + (semantic_score * 0.4))
    return {
        "memories": memories,
        "label": 1.0,
        "epochs": max(0, min(256, int(epochs))),
        "run_qnn": True,
        "fractal_dimension": fractal_dimension,
        "fractal_dimension_min": 1.0,
        "fractal_dimension_max": 2.0,
        "fractal_admissible": True,
        "fractal_measurement_method": "qlc-container-structural-score",
        "fractal_scale": "container-and-yolo-metadata",
        "plugin_hook_enabled": True,
        "plugin_set": "mvp5",
        "plugin_context": {
            "source": "ffed-qlc-mvp",
            "orchestrator": "CeLeBrUm",
            "runtime_memory_surface": "Cerebrum",
            "qlc_container_sha256": container_sha256,
            "yolo_detection_count": len(detections),
            "celebrum_roi_map": roi_map,
            "semantic_score": semantic_score,
            "structural_score": structural_score,
            "proof_mode": active_proof_mode,
            "simulator_protection_case": protection_case,
        },
        "cpai_context": {
            "route": "qlc-gateway-codeproject-fnpqnn",
            "nodes_visible": nodes_active,
            "nodes_active": nodes_active,
            "local_load": local_load,
            "forwarded_load": _clamp01(max(0.0, local_load - 0.65)),
            "can_connect": True,
            "mesh_enabled": True,
            "privacy_class": "public_safe_metadata",
            "codeproject_url": codeproject_url,
            "known_mesh_servers": mesh_servers,
        },
        "plithogenic_enabled": True,
        "revolutionary_topology_enabled": True,
        "neutro_algebra_enabled": True,
        "hydra_em_enabled": True,
        "gpcn_set_phi_enabled": True,
        "orch_or_simulation_enabled": True,
        "quasicrystal_projection_enabled": True,
        "lattice_seed": lattice_seed,
        "microtubule_proxy_count": max(1, min(256, len(detections) + 4)),
        "microtubule_coupling_strength": _clamp01(0.35 + semantic_score),
        "plithogenic_contradiction_threshold": 0.35,
        "observation_scale_min": 0.01,
        "observation_scale_max": 1.0,
        "proof_goal": _proof_goal(active_proof_mode),
        "concept_remap": {
            "old_design_role": "ReaAaS-n",
            "mvp_runtime_role": "CeLeBrUm",
            "distinction": "CeLeBrUm routes and judges YOLO-derived observations; Cerebrum is the FNP-QNN runtime/memory endpoint.",
        },
    }


def _normalize_proof_mode(proof_mode: ProofMode) -> CanonicalProofMode:
    if proof_mode == "qlc_protects_simulator_mvp":
        return "qlc_protects_simulator_mvp"
    return "simulator_supports_qlc_complexity"


def _proof_goal(proof_mode: CanonicalProofMode) -> str:
    if proof_mode == "qlc_protects_simulator_mvp":
        return "demonstrate_qlc_mvp_by_protecting_fnpqnn_simulator_artifacts"
    return "prove_fnpqnn_mvp_supports_complex_qlc_protocol"


def _simulator_protection_case(
    *,
    mode: CanonicalProofMode,
    container_sha256: str,
    container_size_bytes: int,
) -> dict[str, Any]:
    protected_surface = {
        "repo": "FNP-QNN-MVP",
        "runtime_surface": "Cerebrum",
        "primary_endpoint": "POST /cerebrum/runtime/run",
        "secondary_profiles": [
            "POST /fnp-qnn/hydra-em-gpcn/runtime/profile",
            "POST /fnp-qnn/plithogenic/runtime/profile",
            "POST /fnp-qnn/revolutionary-topology/runtime/profile",
            "POST /fnp-qnn/neutro-algebra/profile",
        ],
    }
    guarantees = [
        "simulator_input_can_be_packed_before_submission",
        "runtime_output_can_be_fingerprinted_without_exposing_payload",
        "tampered_qlc_container_fails_authentication",
        "audit_record_contains_hashes_and_policy_not_raw_secrets",
        "yolo_or_mesh_metadata_remains_metadata_only",
    ]
    return {
        "schema": "ffed.qlc.simulator_protection_case.v1",
        "mode": mode,
        "mvp_coupling": "reciprocal_proof_loop_between_FfeD_QLC_MVP_and_FNP_QNN_MVP",
        "reciprocal_proof": {
            "fnp_qnn_proves": "it_can_support_measure_and_route_a_complex_protocol_like_qlc",
            "qlc_proves": "it_can_protect_fnp_qnn_inputs_outputs_runtime_snapshots_and_mesh_handoffs",
        },
        "protected_surface": protected_surface,
        "qlc_container_sha256": container_sha256,
        "qlc_container_size_bytes": container_size_bytes,
        "simulator_role": "supports_and_measures_complex_qlc_protocol"
        if mode == "simulator_supports_qlc_complexity"
        else "protected_runtime_surface_for_qlc_mvp_demonstration",
        "qlc_role": "protection_layer_for_simulator_artifacts"
        if mode == "qlc_protects_simulator_mvp"
        else "complex_protocol_subject_supported_by_simulator",
        "validated_guarantees": guarantees,
        "claim_boundary": "protocol_validity_surface_for_public_mvp_not_production_security_certification",
    }


def build_gateway_command_plan(
    *,
    qlc_payload_path: str,
    codeproject_url: str = "http://localhost:32168",
    fnpqnn_url: str = "http://localhost:8000",
) -> dict[str, Any]:
    """Return the exact handoff commands for the three-repo integration."""

    return {
        "gateway_repo": "fnpqnn_gateway_MVP",
        "simulator_repo": "FNP-QNN-MVP",
        "qlc_repo": "FfeD-QLC-MVP",
        "commands": {
            "activate_celebrum_codeproject_mesh": [
                "fnpqnn",
                "gateway",
                "activate",
                "--tool",
                "codeproject-ai-mesh",
                "--fingerprint",
                "fp-celebrum-codeproject",
                "--accept-fingerprint",
                "--codeproject-url",
                codeproject_url,
                "--dry-run",
            ],
            "check_codeproject_mesh": [
                "fnpqnn",
                "codeproject",
                "mesh-status",
                "--url",
                codeproject_url,
                "--dry-run",
            ],
            "check_yolo": [
                "fnpqnn",
                "codeproject",
                "yolo-status",
                "--url",
                codeproject_url,
                "--dry-run",
            ],
            "start_simulator_api": [
                "python",
                "-m",
                "fnp_qnn_cli.main",
                "api",
                "serve",
            ],
            "post_payload": [
                "Invoke-RestMethod",
                "-Method",
                "Post",
                "-ContentType",
                "application/json",
                "-InFile",
                qlc_payload_path,
                "-Uri",
                f"{fnpqnn_url.rstrip('/')}/cerebrum/runtime/run",
            ],
        },
    }


def _normalize_detection(item: Mapping[str, Any] | YOLODetection) -> YOLODetection:
    if isinstance(item, YOLODetection):
        return item
    return YOLODetection.from_mapping(item)


def _semantic_score(detections: Sequence[YOLODetection]) -> float:
    if not detections:
        return 0.0
    weighted = sum((detection.confidence * 0.8) + (detection.area * 0.2) for detection in detections)
    return _clamp01(weighted / max(1, len(detections)))


def _structural_score(data: bytes) -> float:
    if not data:
        return 0.0
    unique_ratio = len(set(data)) / 256.0
    transitions = sum(1 for left, right in zip(data, data[1:]) if left != right)
    transition_ratio = transitions / max(1, len(data) - 1)
    return _clamp01((unique_ratio * 0.45) + (transition_ratio * 0.55))


def _clamp01(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0.0
    return min(1.0, max(0.0, numeric))
