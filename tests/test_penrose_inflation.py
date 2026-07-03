from __future__ import annotations

import json

import pytest

from ffed_qlc.penrose_geometry import PenroseGeometryError, validate_penrose_patch
from ffed_qlc.penrose_inflation import (
    PHI,
    SUBSTITUTION_MATRIX,
    InflationInput,
    PlannedTile,
    build_initial_inflation_patch,
    export_inflation_manifest,
    inflate_penrose_patch,
    substitute_thick,
    substitute_thin,
)


def test_substitution_contracts_match_matrix() -> None:
    thick_children = substitute_thick(PlannedTile("thick", "root", 0, None))
    thin_children = substitute_thin(PlannedTile("thin", "root", 0, None))

    assert SUBSTITUTION_MATRIX == ((2, 1), (1, 1))
    assert [child.tile_type for child in thick_children] == ["thick", "thick", "thin"]
    assert [child.tile_type for child in thin_children] == ["thick", "thin"]
    assert all(child.parent_lineage == "root" for child in thick_children + thin_children)


def test_depth_zero_returns_minimal_valid_patch() -> None:
    config = InflationInput(depth=0, target_tile_count=1, seed="depth-zero")
    patch = build_initial_inflation_patch(config)
    output = inflate_penrose_patch(config)

    assert patch.metadata["tile_count"] == 1
    assert patch.metadata["tile_type_counts"] == {"thin": 0, "thick": 1}
    assert output.engine == "inflation"
    assert output.generation_index == 0
    assert len(output.tiles) == 1
    assert validate_penrose_patch(output.tiles).valid is True


def test_depth_one_preserves_lineage_edge_labels_and_counts() -> None:
    output = inflate_penrose_patch(InflationInput(depth=1, target_tile_count=10, seed="depth-one"))

    assert output.generation_index == 1
    assert len(output.tiles) == 3
    assert output.diagnostics["thick_count"] == 2
    assert output.diagnostics["thin_count"] == 1
    assert output.diagnostics["edge_labels_preserved"] is True
    assert output.diagnostics["geometry_valid"] is True
    assert all(tile.metadata["engine"] == "inflation" for tile in output.tiles)
    assert all("lineage" in tile.metadata for tile in output.tiles)
    assert len(output.patch.adjacency) >= 1


def test_inflation_builds_hundreds_with_target_cap_and_phi_ratio() -> None:
    output = inflate_penrose_patch(
        InflationInput(depth=6, target_tile_count=144, seed="hundreds")
    )

    assert len(output.tiles) == 144
    assert output.generation_index <= 6
    assert output.diagnostics["geometry_valid"] is True
    assert output.diagnostics["thick_count"] > output.diagnostics["thin_count"]
    assert output.diagnostics["thick_thin_ratio"] == pytest.approx(PHI, rel=0.08)
    assert validate_penrose_patch(output.tiles).valid is True


def test_inflation_seed_and_manifest_are_deterministic_and_redacted() -> None:
    config = InflationInput(depth=4, target_tile_count=55, seed="stable")
    first = inflate_penrose_patch(config)
    second = inflate_penrose_patch(config)
    other = inflate_penrose_patch(InflationInput(depth=4, target_tile_count=55, seed="other"))

    assert first.patch.metadata["patch_fingerprint"] == second.patch.metadata["patch_fingerprint"]
    assert first.patch.metadata["patch_fingerprint"] != other.patch.metadata["patch_fingerprint"]

    manifest = export_inflation_manifest(first)
    serialized = json.dumps(manifest, sort_keys=True)
    assert manifest["raw_source_urls_included"] is False
    assert manifest["raw_payload_included"] is False
    assert "https://" not in serialized
    assert manifest == export_inflation_manifest(second)


def test_inflation_rejects_invalid_config_and_missing_sources() -> None:
    with pytest.raises(PenroseGeometryError, match="target_tile_count"):
        inflate_penrose_patch(InflationInput(target_tile_count=0))

    with pytest.raises(PenroseGeometryError, match="depth exceeds max_depth"):
        inflate_penrose_patch(InflationInput(depth=9))

    with pytest.raises(ValueError, match="missing source function profile"):
        inflate_penrose_patch(InflationInput(source_function_ids=("S01", "S11")))
