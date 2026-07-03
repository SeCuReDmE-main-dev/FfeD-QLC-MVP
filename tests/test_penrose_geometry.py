from __future__ import annotations

import math

import pytest

from ffed_qlc.penrose_geometry import (
    PHI,
    THICK_ANGLES_DEGREES,
    THIN_ANGLES_DEGREES,
    PenroseGeometryError,
    PenroseTile,
    build_penrose_patch,
    build_penrose_rhombus,
    compute_adjacency,
    deterministic_sort_tiles,
    deterministic_tile_id,
    expected_area_for_type,
    matching_profile_for_tile,
    tile_metadata,
    validate_penrose_patch,
    validate_penrose_tile,
)


def test_thin_and_thick_rhombi_use_canonical_penrose_geometry() -> None:
    thin = build_penrose_rhombus("thin", edge_length=2.0)
    thick = build_penrose_rhombus("thick", edge_length=2.0)

    assert PHI == pytest.approx((1.0 + math.sqrt(5.0)) / 2.0)
    assert THIN_ANGLES_DEGREES == (36.0, 144.0, 36.0, 144.0)
    assert THICK_ANGLES_DEGREES == (72.0, 108.0, 72.0, 108.0)

    thin_validation = validate_penrose_tile(thin)
    thick_validation = validate_penrose_tile(thick)

    assert thin_validation.valid is True
    assert thick_validation.valid is True
    assert thin_validation.angles_degrees == pytest.approx(THIN_ANGLES_DEGREES)
    assert thick_validation.angles_degrees == pytest.approx(THICK_ANGLES_DEGREES)
    assert thin_validation.edge_lengths == pytest.approx((2.0, 2.0, 2.0, 2.0))
    assert thick_validation.edge_lengths == pytest.approx((2.0, 2.0, 2.0, 2.0))
    assert thin_validation.area == pytest.approx(expected_area_for_type("thin", 2.0))
    assert thick_validation.area == pytest.approx(expected_area_for_type("thick", 2.0))


def test_tile_id_metadata_matching_and_sort_are_deterministic() -> None:
    left = build_penrose_rhombus("thin", origin=(0.0, 0.0), orientation_degrees=36.0)
    duplicate = build_penrose_rhombus("thin", origin=(0.0, 0.0), orientation_degrees=36.0)
    right = build_penrose_rhombus("thick", origin=(4.0, 0.0), orientation_degrees=72.0)

    assert left.tile_id == duplicate.tile_id
    assert left.tile_id == deterministic_tile_id("thin", left.vertices)
    assert [tile.tile_id for tile in deterministic_sort_tiles([right, left])] == sorted(
        [left.tile_id, right.tile_id]
    )

    metadata = tile_metadata(left)
    matching_profile = matching_profile_for_tile(left)
    assert metadata["schema"] == "ffed.qlc.penrose_tile_metadata.v1"
    assert metadata["tile_type"] == "thin"
    assert metadata["matching_profile"]["edge_labels"] == ["e0", "e1", "e2", "e3"]
    assert matching_profile["claim_boundary"].endswith("not_crypto_certification")


def test_invalid_geometry_rejects_unequal_edges_angle_and_order() -> None:
    valid = build_penrose_rhombus("thin")
    bad_vertices = (
        valid.vertices[0],
        valid.vertices[1],
        (valid.vertices[2][0] + 0.4, valid.vertices[2][1]),
        valid.vertices[3],
    )
    bad = PenroseTile(
        tile_id="bad-thin",
        tile_type="thin",
        vertices=bad_vertices,
        edge_length=1.0,
    )
    validation = validate_penrose_tile(bad)

    assert validation.valid is False
    assert "unequal_edges" in validation.reasons
    assert "invalid_angle_profile" in validation.reasons

    reversed_tile = PenroseTile(
        tile_id="reversed",
        tile_type="thin",
        vertices=tuple(reversed(valid.vertices)),  # type: ignore[arg-type]
        edge_length=1.0,
    )
    assert "polygon_order_not_counter_clockwise" in validate_penrose_tile(reversed_tile).reasons


def test_self_crossing_polygon_is_rejected() -> None:
    bowtie = PenroseTile(
        tile_id="bowtie",
        tile_type="thick",
        vertices=((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0)),
        edge_length=1.0,
    )

    validation = validate_penrose_tile(bowtie)

    assert validation.valid is False
    assert "self_crossing_polygon" in validation.reasons


def test_patch_adjacency_duplicate_guard_and_metadata() -> None:
    tile_a = build_penrose_rhombus("thick", origin=(0.0, 0.0), orientation_degrees=0.0)
    shared_start = tile_a.vertices[2]
    tile_b = build_penrose_rhombus(
        "thick",
        origin=shared_start,
        orientation_degrees=-108.0,
    )

    adjacency = compute_adjacency([tile_b, tile_a])
    assert len(adjacency) == 1
    assert {adjacency[0].tile_a, adjacency[0].tile_b} == {tile_a.tile_id, tile_b.tile_id}

    patch = build_penrose_patch([tile_b, tile_a], patch_id="unit-patch")
    assert patch.metadata["schema"] == "ffed.qlc.penrose_patch_metadata.v1"
    assert patch.metadata["patch_id"] == "unit-patch"
    assert patch.metadata["tile_count"] == 2
    assert patch.metadata["tile_type_counts"]["thick"] == 2
    assert patch.metadata["adjacency_count"] == 1
    assert patch.metadata["claim_boundary"].endswith("not_security_or_quantum_proof")

    duplicate_validation = validate_penrose_patch([tile_a, tile_a])
    assert duplicate_validation.valid is False
    assert "duplicate_tile_id" in duplicate_validation.reasons
    assert "duplicate_tile_geometry" in duplicate_validation.reasons

    with pytest.raises(PenroseGeometryError, match="duplicate_tile"):
        build_penrose_patch([tile_a, tile_a])
