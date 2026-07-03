from __future__ import annotations

import json

import pytest

from ffed_qlc import AdmDecision
from ffed_qlc.penrose_geometry import PenroseTile, build_penrose_rhombus
from ffed_qlc.plithogenic_gate import (
    PLITHOGENIC_TILE_CLASS_SCHEMA,
    classify_plithogenic_tile,
    export_plithogenic_tile_classification,
    inf_sup_gate,
    numeric_dissimilarity_vector,
    phi_weighted_contradiction,
    prevalence_resolve,
)


def test_valid_tile_accepts_true_to_scaffold_profile() -> None:
    tile = build_penrose_rhombus("thick")
    classification = classify_plithogenic_tile(tile, neighbor_tiles=[tile, tile], connector_size=2)

    assert classification.Adm == AdmDecision.ACCEPT
    assert classification.admission_precheck is True
    assert classification.C_phi >= 0.0
    assert all(isinstance(value, float) for value in classification.Contr)
    assert "true_to_scaffold" in classification.reason_codes
    assert classification.raw_tif_exported is False


def test_missing_provenance_suspends_profile() -> None:
    tile = build_penrose_rhombus("thin")
    classification = classify_plithogenic_tile(tile, provenance_present=False)

    assert classification.Adm == AdmDecision.SUSPEND
    assert "missing_provenance" in classification.reason_codes


def test_invalid_geometry_or_unsafe_claim_rejects_profile() -> None:
    invalid = PenroseTile(
        tile_id="bad",
        tile_type="thin",
        vertices=((0.0, 0.0), (1.0, 0.0), (1.0, 0.1), (0.0, 0.1)),
    )
    invalid_class = classify_plithogenic_tile(invalid)
    unsafe_class = classify_plithogenic_tile(
        build_penrose_rhombus("thick"),
        claim_scope="security_certification",
    )

    assert invalid_class.Adm == AdmDecision.REJECT
    assert "invalid_penrose_geometry" in invalid_class.reason_codes
    assert unsafe_class.Adm == AdmDecision.REJECT
    assert "unsafe_claim_scope" in unsafe_class.reason_codes


def test_export_has_plithogenic_values_but_no_raw_tif() -> None:
    classification = classify_plithogenic_tile(build_penrose_rhombus("thick"))
    exported = export_plithogenic_tile_classification(classification)
    serialized = json.dumps(exported, sort_keys=True)

    assert exported["schema"] == PLITHOGENIC_TILE_CLASS_SCHEMA
    assert exported["raw_tif_exported"] is False
    assert "Contr" in exported
    assert "C_phi" in exported
    assert "T_tile" not in serialized
    assert "I_tile" not in serialized
    assert "F_tile" not in serialized
    assert exported["claim_boundary"].endswith("not_raw_tif_or_security_certification")


def test_numeric_contradiction_inf_sup_and_prevalence_are_deterministic() -> None:
    contradiction = numeric_dissimilarity_vector((1.0, 0.25, 0.5), (1.0, 1.0, 0.0))
    c_phi = phi_weighted_contradiction(contradiction)
    gate = inf_sup_gate((1.0, 0.25, 0.5))
    winner = prevalence_resolve(
        {"low": 0.95, "preferred": 0.40},
        ["preferred", "low"],
    )

    assert contradiction == pytest.approx((0.0, 0.75, 0.5))
    assert 0.0 <= c_phi <= 1.0
    assert gate.lower_bound == 0.25
    assert gate.upper_bound == 1.0
    assert gate.admission_confidence == pytest.approx(0.25)
    assert winner == ("preferred", 0.40)


def test_missing_source_profile_rejects_tile() -> None:
    classification = classify_plithogenic_tile(
        build_penrose_rhombus("thick"),
        source_function_ids=("S01", "S11"),
    )

    assert classification.Adm == AdmDecision.REJECT
    assert "missing_source_function_profile" in classification.reason_codes
    assert classification.source_ids == tuple()
