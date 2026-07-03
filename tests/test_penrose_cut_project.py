from __future__ import annotations

import json
import math

import pytest

from ffed_qlc.penrose_cut_project import (
    CUT_PROJECT_ENGINE_ID,
    PHI_BASIS_PROFILE,
    CutProjectError,
    CutProjectInput,
    build_phi_basis,
    cut_project_penrose_patch,
    derive_seed_shift,
    generate_cut_project_candidates,
    project_5d_to_2d,
    project_5d_to_internal,
)
from ffed_qlc.penrose_geometry import validate_penrose_patch


def test_phi_basis_projection_and_candidate_bounds() -> None:
    basis = build_phi_basis()
    point = (1, -1, 0, 1, 0)
    physical = project_5d_to_2d(point, basis)
    internal = project_5d_to_internal(point, basis)
    candidates = generate_cut_project_candidates(
        CutProjectInput(target_tile_count=8, grid_radius=1, candidate_cap=100)
    )

    assert len(basis) == 5
    assert all(vector.index == index for index, vector in enumerate(basis))
    assert all(math.isfinite(value) for value in physical + internal)
    assert candidates
    assert all(max(abs(value) for value in candidate.lattice_point) <= 2 for candidate in candidates)
    assert any(candidate.accepted for candidate in candidates)


def test_cut_project_is_deterministic_and_hits_target_count() -> None:
    config = CutProjectInput(target_tile_count=34, grid_radius=3, seed="stable-cut")
    first = cut_project_penrose_patch(config)
    second = cut_project_penrose_patch(config)

    assert first.engine == CUT_PROJECT_ENGINE_ID
    assert first.status == "accept"
    assert first.patch.metadata["tile_count"] == 34
    assert first.patch.metadata["patch_fingerprint"] == second.patch.metadata["patch_fingerprint"]
    assert validate_penrose_patch(first.patch.tiles).valid is True
    assert len(first.accepted_candidates) == 34


def test_cut_project_metadata_is_bounded_and_does_not_overclaim() -> None:
    output = cut_project_penrose_patch(
        CutProjectInput(target_tile_count=21, grid_radius=3, seed="metadata")
    )
    serialized = json.dumps(output.diagnostics, sort_keys=True)

    assert output.diagnostics["schema"] == "ffed.qlc.cut_project_diagnostics.v1"
    assert output.diagnostics["basis_profile"] == PHI_BASIS_PROFILE
    assert output.diagnostics["candidate_count"] <= output.input.candidate_cap
    assert output.diagnostics["accepted_candidate_count"] == 21
    assert output.diagnostics["raw_source_urls_included"] is False
    assert output.diagnostics["raw_payload_included"] is False
    assert "https://" not in serialized
    assert output.diagnostics["claim_boundary"].endswith("not_complete_plane_tiling_or_crypto_proof")
    assert "inflation_reference" in output.diagnostics


def test_cut_project_suspends_missing_window_and_uses_inflation_fallback() -> None:
    output = cut_project_penrose_patch(
        CutProjectInput(
            target_tile_count=13,
            acceptance_window_radius=None,
            seed="missing-window",
        )
    )

    assert output.status == "suspend"
    assert "missing_acceptance_window" in output.diagnostics["suspend_reasons"]
    assert output.fallback is not None
    assert output.fallback.engine == "inflation"
    assert output.patch.metadata["tile_count"] == 13


def test_cut_project_suspends_invalid_basis_or_raises_without_fallback() -> None:
    suspended = cut_project_penrose_patch(
        CutProjectInput(target_tile_count=8, basis_profile="bad_basis")
    )
    assert suspended.status == "suspend"
    assert "invalid_phi_basis" in suspended.diagnostics["suspend_reasons"]

    with pytest.raises(CutProjectError, match="cut-project suspended"):
        cut_project_penrose_patch(
            CutProjectInput(
                target_tile_count=8,
                basis_profile="bad_basis",
                allow_inflation_fallback=False,
            )
        )


def test_seed_shift_is_deterministic_and_candidate_cap_is_enforced() -> None:
    assert derive_seed_shift("same") == derive_seed_shift("same")
    candidates = generate_cut_project_candidates(
        CutProjectInput(target_tile_count=12, grid_radius=3, candidate_cap=12, seed="cap")
    )

    assert len(candidates) == 12
