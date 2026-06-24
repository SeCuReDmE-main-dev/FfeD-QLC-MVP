from ffed_qlc import (
    build_semantic_complexity_map,
    build_sensitivity_weighted_obfuscation_policy,
    build_swop_chunk_protection_plan,
    derive_chunk_key_schedule,
)


def test_chunk_protection_plan_maps_low_swop_to_fast_basic() -> None:
    swop = build_sensitivity_weighted_obfuscation_policy(
        "video",
        detections=[{"class_name": "background", "confidence_score": 0.2}],
    )

    plan = build_swop_chunk_protection_plan(swop)

    assert plan["schema"] == "ffed.qlc.swop_chunk_protection_plan.v1"
    assert plan["planned_chunks"][0]["protection_tier"] == "low"
    assert plan["planned_chunks"][0]["recommended_chunk_mode"] == "fast_basic"
    assert plan["key_material_exposed"] is False


def test_chunk_protection_plan_maps_high_swop_to_sensitive_dense() -> None:
    swop = build_sensitivity_weighted_obfuscation_policy(
        "image",
        detections=[{"class_name": "face", "confidence_score": 0.92}],
    )

    plan = build_swop_chunk_protection_plan(swop)

    assert plan["planned_chunks"][0]["protection_tier"] == "high"
    assert plan["planned_chunks"][0]["recommended_chunk_mode"] == "sensitive_dense"


def test_chunk_protection_plan_maps_critical_swop_to_critical_dense_with_fingerprints_only() -> None:
    detections = [{"class_name": "license_plate", "confidence_score": 0.98}]
    swop = build_sensitivity_weighted_obfuscation_policy(
        "image",
        detections=detections,
        semantic_map=build_semantic_complexity_map(detections),
    )
    schedule = derive_chunk_key_schedule(
        {
            "source_sha256": "abc",
            "lattice_seed_fingerprint": "seed",
            "projection_profile": {"projection_seed_fingerprint": "projection"},
        },
        1,
    )

    plan = build_swop_chunk_protection_plan(swop, chunk_key_schedule=schedule)

    assert plan["planned_chunks"][0]["protection_tier"] == "critical"
    assert plan["planned_chunks"][0]["recommended_chunk_mode"] == "critical_dense"
    assert plan["planned_chunks"][0]["subkey_fingerprint"] == schedule["chunks"][0]["subkey_fingerprint"]
    assert plan["planned_chunks"][0]["key_material_exposed"] is False
