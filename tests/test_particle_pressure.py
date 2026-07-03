from __future__ import annotations

import json

from ffed_qlc.particle_pressure import (
    PARTICLE_DESCRIPTOR_SCHEMA,
    build_audio_particle_descriptor,
    build_image_particle_descriptor,
    build_text_particle_descriptor,
    calculate_z_value,
    export_particle_descriptor,
    fuse_semantic_pressures,
    semantic_pressure_from_context_signals,
    semantic_pressure_from_value,
    semantic_pressure_from_yolo_rois,
    apply_pressure_to_tile_params,
)
from ffed_qlc.penrose_geometry import build_penrose_rhombus, validate_penrose_tile


def test_image_particle_maps_rgba_to_wxyz_without_raw_pixels() -> None:
    descriptor = build_image_particle_descriptor(
        [(255, 0, 0, 255), (0, 255, 0, 128)],
        particle_id="img-1",
    )
    exported = export_particle_descriptor(descriptor)
    serialized = json.dumps(exported, sort_keys=True)

    assert exported["schema"] == PARTICLE_DESCRIPTOR_SCHEMA
    assert exported["media_type"] == "image"
    assert exported["raw_payload_embedded"] is False
    assert all(0.0 <= value <= 1.0 for value in exported["state_wxyz"])
    assert "rgba_histogram" in exported["feature_fingerprints"]
    assert "(255, 0, 0, 255)" not in serialized


def test_text_particle_is_redacted_to_hash_and_features() -> None:
    secret_text = "student private text 123"
    descriptor = build_text_particle_descriptor(secret_text, particle_id="txt-1")
    exported = export_particle_descriptor(descriptor)
    serialized = json.dumps(exported, sort_keys=True)

    assert exported["media_type"] == "text"
    assert exported["payload_fingerprint"]
    assert secret_text not in serialized
    assert exported["raw_payload_embedded"] is False


def test_audio_particle_contract_suspends_without_raw_audio() -> None:
    descriptor = build_audio_particle_descriptor(
        audio_fingerprint="audio-sha256-placeholder",
        duration_seconds=12.5,
        sample_rate_hz=48000,
    )
    exported = export_particle_descriptor(descriptor)

    assert exported["media_type"] == "audio"
    assert exported["status"] == "suspend"
    assert "audio_feature_extractor_not_enabled" in exported["reason_codes"]
    assert exported["raw_payload_embedded"] is False


def test_semantic_pressure_from_yolo_context_and_fusion_is_bounded() -> None:
    yolo_pressure = semantic_pressure_from_yolo_rois(
        [
            {
                "class_name": "face",
                "confidence_score": 0.92,
                "bounding_box_normalized": [0.1, 0.1, 0.4, 0.5],
            }
        ]
    )
    context_pressure = semantic_pressure_from_context_signals(
        [{"texture_complexity": 0.3, "entropy_score": 0.4, "edge_density": 0.2}]
    )
    fused = fuse_semantic_pressures([yolo_pressure, context_pressure])

    assert 0.0 <= yolo_pressure.value <= 1.0
    assert 0.0 <= context_pressure.value <= 1.0
    assert 0.0 <= fused.value <= 1.0
    assert 1.0 <= fused.lattice_density_multiplier <= 2.0
    assert fused.phason_strain_factor >= 0.0
    assert fused.z_modifier >= 0.0
    assert fused.sources == ("yolo_roi", "context_signal")


def test_z_value_is_deterministic_and_clamped() -> None:
    first = calculate_z_value(0.2, 0.3, 0.4, 0.5, z_modifier=0.25)
    second = calculate_z_value(0.2, 0.3, 0.4, 0.5, z_modifier=0.25)
    clamped = calculate_z_value(-10.0, 2.0, 3.0, 4.0, z_modifier=10_000.0)

    assert first == second
    assert 0.0 <= first.normalized_z <= 1.0
    assert 0.0 <= clamped.normalized_z <= 1.0
    assert clamped.clamped is True
    assert clamped.inputs_wxyz == (0.0, 1.0, 1.0, 1.0)


def test_pressure_applies_to_tile_params_without_breaking_penrose_geometry() -> None:
    tile = build_penrose_rhombus("thick")
    pressure = semantic_pressure_from_value(0.75, sources=("unit",))
    pressurized = apply_pressure_to_tile_params(tile, pressure)

    assert validate_penrose_tile(tile).valid is True
    assert pressurized["geometry_preserved"] is True
    assert pressurized["edge_length"] == tile.edge_length
    assert pressurized["raw_payload_embedded"] is False
    assert pressurized["claim_boundary"] == "pressure_changes_metadata_not_penrose_geometry"
