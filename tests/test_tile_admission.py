from __future__ import annotations

import json

from ffed_qlc import AdmDecision
from ffed_qlc.fractal_measurement import BOX_COUNTING_METHOD, FRACTAL_HIERARCHY, BoxCount, FractalMeasurement
from ffed_qlc.penrose_geometry import PenroseTile, build_penrose_patch, build_penrose_rhombus
from ffed_qlc.plithogenic_gate import classify_plithogenic_tile
from ffed_qlc.tile_admission import (
    TDF_ADMISSION_SCHEMA,
    TileAdmissionThresholds,
    approved_lattice_tiles,
    build_tile_admission_ledger,
    compute_t_df_f,
    export_tile_admission_profile,
    validate_approved_lattice_only,
)


def _measurement(dF: float | None = 0.5, *, source: str | None = "I_system^S.fractal_geometry") -> FractalMeasurement:
    return FractalMeasurement(
        status=AdmDecision.ACCEPT if dF is not None else AdmDecision.SUSPEND,
        D_f=1.5 if dF is not None else None,
        D_f_hat=dF,
        dF=dF,
        i_fractal=dF,
        D_min=1.0,
        D_max=2.0,
        I_system_source=source,
        hierarchy=FRACTAL_HIERARCHY,
        confidence=0.85 if dF is not None else 0.0,
        box_counts=(BoxCount(0.25, 8), BoxCount(0.5, 4), BoxCount(1.0, 2)),
        reason_codes=("dF_assigned_from_fractal_source",) if dF is not None else ("missing_dF",),
        method_metadata={"method": BOX_COUNTING_METHOD},
        scale_metadata={"scale_count": 3},
    )


def test_valid_thin_and_thick_tiles_are_accepted() -> None:
    thin = build_penrose_rhombus("thin")
    thick = build_penrose_rhombus("thick")

    thin_profile = compute_t_df_f(thin, classify_plithogenic_tile(thin), _measurement(0.45))
    thick_profile = compute_t_df_f(thick, classify_plithogenic_tile(thick), _measurement(0.55))

    assert thin_profile.Adm == AdmDecision.ACCEPT
    assert thick_profile.Adm == AdmDecision.ACCEPT
    assert thin_profile.approved_for_lattice is True
    assert thick_profile.approved_for_lattice is True
    assert "accepted_true_to_scaffold" in thin_profile.reason_codes


def test_invalid_angle_and_unequal_edge_reject() -> None:
    invalid = PenroseTile(
        tile_id="bad-angle",
        tile_type="thin",
        vertices=((0.0, 0.0), (1.0, 0.0), (1.4, 0.2), (0.0, 0.6)),
    )
    classification = classify_plithogenic_tile(invalid)
    profile = compute_t_df_f(invalid, classification, _measurement(0.5))

    assert profile.Adm == AdmDecision.REJECT
    assert "invalid_penrose_geometry" in profile.reason_codes


def test_missing_source_and_raw_export_request_reject() -> None:
    tile = build_penrose_rhombus("thick")
    missing_source = classify_plithogenic_tile(tile, source_function_ids=("S01", "S11"))
    profile = compute_t_df_f(tile, missing_source, _measurement(0.5))
    raw_profile = compute_t_df_f(
        tile,
        classify_plithogenic_tile(tile),
        _measurement(0.5),
        raw_export_requested=True,
    )

    assert profile.Adm == AdmDecision.REJECT
    assert "missing_source_function_profile" in profile.reason_codes
    assert raw_profile.Adm == AdmDecision.REJECT
    assert "raw_export_request_rejected" in raw_profile.reason_codes


def test_flat_or_overcomplex_df_suspends_admission() -> None:
    tile = build_penrose_rhombus("thin")
    classification = classify_plithogenic_tile(tile)
    thresholds = TileAdmissionThresholds(dF_min_build=0.1, dF_max_build=0.8)

    flat = compute_t_df_f(tile, classification, _measurement(0.0), thresholds=thresholds)
    overcomplex = compute_t_df_f(tile, classification, _measurement(0.95), thresholds=thresholds)
    unavailable = compute_t_df_f(tile, classification, _measurement(None))
    non_fractal = compute_t_df_f(tile, classification, _measurement(0.5, source=None))

    assert flat.Adm == AdmDecision.SUSPEND
    assert overcomplex.Adm == AdmDecision.SUSPEND
    assert unavailable.Adm == AdmDecision.SUSPEND
    assert non_fractal.Adm == AdmDecision.SUSPEND
    assert "dF_out_of_build_band" in flat.reason_codes
    assert "dF_out_of_build_band" in overcomplex.reason_codes
    assert "unavailable_dF" in unavailable.reason_codes
    assert "non_fractal_i_system_source" in non_fractal.reason_codes


def test_export_and_ledger_are_redacted_and_stable() -> None:
    tile = build_penrose_rhombus("thick")
    profile = compute_t_df_f(tile, classify_plithogenic_tile(tile), _measurement(0.5))
    exported = export_tile_admission_profile(profile)
    ledger = build_tile_admission_ledger([profile])
    serialized = json.dumps(exported, sort_keys=True)

    assert exported["schema"] == TDF_ADMISSION_SCHEMA
    assert exported["raw_tif_exported"] is False
    assert "I_tile" not in serialized
    assert ledger["entry_count"] == 1
    assert ledger["accepted_count"] == 1
    assert ledger["raw_tif_exported"] is False


def test_approved_lattice_filter_returns_only_accepted_tiles() -> None:
    accepted_tile = build_penrose_rhombus("thick", origin=(0.0, 0.0))
    rejected_tile = build_penrose_rhombus("thin", origin=(3.0, 0.0))
    patch = build_penrose_patch([accepted_tile, rejected_tile])
    accepted = compute_t_df_f(
        accepted_tile,
        classify_plithogenic_tile(accepted_tile),
        _measurement(0.5),
    )
    rejected = compute_t_df_f(
        rejected_tile,
        classify_plithogenic_tile(rejected_tile, source_function_ids=("S01", "S11")),
        _measurement(0.5),
    )

    approved = approved_lattice_tiles(patch.tiles, [accepted, rejected])
    filter_receipt = validate_approved_lattice_only(patch, [accepted, rejected])

    assert tuple(tile.tile_id for tile in approved) == (accepted_tile.tile_id,)
    assert filter_receipt["approved_tile_count"] == 1
    assert filter_receipt["rejected_or_suspended_count"] == 1
