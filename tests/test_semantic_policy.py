from ffed_qlc import build_semantic_complexity_map


def test_semantic_complexity_map_applies_high_confidence_rule() -> None:
    policy = build_semantic_complexity_map(
        [
            {
                "class_name": "face",
                "confidence_score": 0.91,
                "bounding_box_normalized": [0.5, 0.5, 0.2, 0.3],
            }
        ]
    )

    region = policy["regions"][0]
    assert region["applied"] is True
    assert region["parameters"]["lattice_density_multiplier"] == 2.0
    assert region["parameters"]["phason_strain_factor"] == 1.5
    assert region["phason_strain_gradient"]["enabled"] is True
    assert policy["security_boundary"].endswith("not a cryptographic root")


def test_semantic_complexity_map_defaults_low_confidence_detection() -> None:
    policy = build_semantic_complexity_map([{"class_name": "license_plate", "confidence_score": 0.2}])

    region = policy["regions"][0]
    assert region["applied"] is False
    assert region["parameters"]["lattice_density_multiplier"] == 1.0
    assert region["phason_strain_gradient"]["enabled"] is False
