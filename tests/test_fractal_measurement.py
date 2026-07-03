from __future__ import annotations

import pytest

from ffed_qlc import AdmDecision
from ffed_qlc.fractal_measurement import (
    BOX_COUNTING_METHOD,
    FRACTAL_HIERARCHY,
    FractalPath,
    build_fractal_path,
    export_fractal_measurement,
    measure_fractal_path,
    measure_patch_fractal_dimension,
    measure_tile_fractal_path,
    normalize_d_f,
    resolve_i_system_source,
)
from ffed_qlc.penrose_inflation import InflationInput, inflate_penrose_patch


def _patch():
    return inflate_penrose_patch(InflationInput(depth=3, target_tile_count=21, seed="fractal")).patch


def test_tile_and_patch_fractal_dimensions_are_bounded() -> None:
    patch = _patch()
    tile_measurement = measure_tile_fractal_path(
        patch.tiles[0],
        patch,
        carrier_type="fractal_boundary",
    )
    patch_measurement = measure_patch_fractal_dimension(patch)

    assert tile_measurement.status == AdmDecision.ACCEPT
    assert patch_measurement.status == AdmDecision.ACCEPT
    assert tile_measurement.D_f is not None
    assert patch_measurement.D_f is not None
    assert 0.0 <= tile_measurement.D_f_hat <= 1.0
    assert 0.0 <= patch_measurement.D_f_hat <= 1.0
    assert tile_measurement.dF == tile_measurement.D_f_hat
    assert tile_measurement.i_fractal == tile_measurement.D_f_hat


def test_fractal_hierarchy_and_i_system_source_are_preserved() -> None:
    patch = _patch()
    path = build_fractal_path(patch.tiles[0], patch, carrier_type="fractal_cluster")
    measurement = measure_fractal_path(path)
    exported = export_fractal_measurement(measurement)

    assert resolve_i_system_source(path) == "I_system^S.fractal_geometry"
    assert exported["hierarchy"] == FRACTAL_HIERARCHY
    assert exported["I_system_source"] == "I_system^S.fractal_geometry"
    assert exported["method_metadata"]["measurement_is_truth_claim"] is False
    assert exported["claim_boundary"].endswith("not_truth_or_security_certification")


def test_missing_omega_scale_or_method_suspends_measurement() -> None:
    no_omega = FractalPath(
        seed_tile_id="empty",
        carrier_type="fractal_boundary",
        points=tuple(),
        Omega=None,
        scale_range=(0.25, 0.5),
        measurement_method=BOX_COUNTING_METHOD,
    )
    no_scale = FractalPath(
        seed_tile_id="no-scale",
        carrier_type="fractal_boundary",
        points=((0.0, 0.0), (1.0, 1.0)),
        Omega=(0.0, 0.0, 1.0, 1.0),
        scale_range=tuple(),
        measurement_method=BOX_COUNTING_METHOD,
    )
    no_method = FractalPath(
        seed_tile_id="no-method",
        carrier_type="fractal_boundary",
        points=((0.0, 0.0), (1.0, 1.0)),
        Omega=(0.0, 0.0, 1.0, 1.0),
        scale_range=(0.25, 0.5),
        measurement_method=None,
    )

    assert "missing_Omega" in measure_fractal_path(no_omega).reason_codes
    assert "missing_scale_range" in measure_fractal_path(no_scale).reason_codes
    assert "missing_measurement_method" in measure_fractal_path(no_method).reason_codes
    assert measure_fractal_path(no_method).status == AdmDecision.SUSPEND


def test_invalid_bounds_and_unstable_measurement_suspend_or_raise() -> None:
    path = FractalPath(
        seed_tile_id="flat",
        carrier_type="fractal_boundary",
        points=((0.0, 0.0), (1.0, 1.0)),
        Omega=(0.0, 0.0, 1.0, 1.0),
        scale_range=(0.5, 0.5),
        measurement_method=BOX_COUNTING_METHOD,
    )

    with pytest.raises(ValueError, match="D_max"):
        normalize_d_f(1.2, D_min=2.0, D_max=1.0)

    invalid_bounds = measure_fractal_path(path, D_min=2.0, D_max=1.0)
    unstable = measure_fractal_path(path)

    assert invalid_bounds.status == AdmDecision.SUSPEND
    assert "invalid_D_bounds" in invalid_bounds.reason_codes
    assert unstable.status == AdmDecision.SUSPEND
    assert "unstable_measurement" in unstable.reason_codes


def test_non_geometric_contradiction_cannot_assign_df() -> None:
    path = FractalPath(
        seed_tile_id="semantic",
        carrier_type="semantic_contradiction",
        points=((0.0, 0.0), (0.5, 0.5), (1.0, 1.0)),
        Omega=(0.0, 0.0, 1.0, 1.0),
        scale_range=(0.25, 0.5, 1.0),
        measurement_method=BOX_COUNTING_METHOD,
        source="semantic",
    )
    measurement = measure_fractal_path(path)

    assert measurement.status == AdmDecision.SUSPEND
    assert "contradiction_non_geometric" in measurement.reason_codes
    assert measurement.dF is None
    assert measurement.i_fractal is None
