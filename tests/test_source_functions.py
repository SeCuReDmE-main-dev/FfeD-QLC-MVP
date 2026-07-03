from __future__ import annotations

from copy import deepcopy
import json

import pytest

from ffed_qlc.source_functions import (
    REQUIRED_SOURCE_IDS,
    SOURCE_FUNCTION_GRAPH_SCHEMA,
    SourceFunctionError,
    build_source_function_graph,
    compile_source_function_profiles,
    load_source_function_payload,
    require_all_source_function_profiles,
    require_source_function_ids,
)


def test_compiles_exactly_ten_source_function_profiles() -> None:
    profiles = compile_source_function_profiles()

    assert tuple(profile.source_id for profile in profiles) == REQUIRED_SOURCE_IDS
    assert {profile.function.name for profile in profiles} == {
        "f_plithogenic_admission",
        "f_row_matrix_edge",
        "f_connector",
        "f_prevalence_resolve",
        "f_inf_sup_gate",
        "f_graph_state_carrier",
        "f_walk_dispersion",
        "f_multihyperedge_operation",
        "f_fusion_order",
        "f_cut_project_accept",
    }
    assert all(profile.raw_body_stored is False for profile in profiles)
    assert all(profile.ui_visibility == "metadata_only" for profile in profiles)


def test_profiles_are_math_roles_not_ui_tabs() -> None:
    profiles = compile_source_function_profiles()

    by_id = {profile.source_id: profile for profile in profiles}
    assert by_id["S01"].source_role == "attribute_admission"
    assert by_id["S02"].source_role == "row_matrix_edge"
    assert by_id["S03"].source_role == "connector_hyperedge"
    assert by_id["S04"].source_role == "prevalence_resolution"
    assert by_id["S05"].source_role == "inf_sup_gate"
    assert by_id["S06"].source_role == "graph_state_carrier"
    assert by_id["S07"].source_role == "walk_dispersion"
    assert by_id["S08"].source_role == "multihyperedge_operation"
    assert by_id["S09"].source_role == "fusion_order"
    assert by_id["S10"].source_role == "cut_project_accept"
    assert all("ui" not in profile.source_role.casefold() for profile in profiles)
    assert "penrose_lattice" in by_id["S10"].maps_to


def test_source_graph_is_secondary_and_hides_raw_urls_by_default() -> None:
    graph = build_source_function_graph()
    serialized = json.dumps(graph, sort_keys=True)

    assert graph["schema"] == SOURCE_FUNCTION_GRAPH_SCHEMA
    assert graph["graph_role"] == "secondary_provenance_not_lattice_engine"
    assert graph["raw_urls_included"] is False
    assert "https://" not in serialized
    assert "url_fingerprint" in serialized


def test_source_graph_can_include_urls_only_when_explicitly_requested() -> None:
    graph = build_source_function_graph(include_urls=True)
    serialized = json.dumps(graph, sort_keys=True)

    assert graph["raw_urls_included"] is True
    assert "https://digitalrepository.unm.edu/math_fsp/20/" in serialized


def test_requires_profiles_and_rejects_missing_source_profile() -> None:
    selected = require_source_function_ids(["S01", "S10"])
    assert tuple(profile.source_id for profile in selected) == ("S01", "S10")
    assert len(require_all_source_function_profiles()) == 10

    with pytest.raises(SourceFunctionError, match="missing source function profile"):
        require_source_function_ids(["S01", "S11"])


def test_rejects_duplicate_normalized_urls() -> None:
    payload = deepcopy(load_source_function_payload())
    payload["profiles"][1]["url"] = "https://digitalrepository.unm.edu/math_fsp/20"

    with pytest.raises(SourceFunctionError, match="duplicate normalized URL"):
        compile_source_function_profiles(payload)


def test_rejects_raw_body_storage() -> None:
    payload = deepcopy(load_source_function_payload())
    payload["profiles"][0]["raw_body_stored"] = True

    with pytest.raises(SourceFunctionError, match="cannot store raw source bodies"):
        compile_source_function_profiles(payload)


def test_rejects_missing_required_profile() -> None:
    payload = deepcopy(load_source_function_payload())
    payload["profiles"] = payload["profiles"][:-1]

    with pytest.raises(SourceFunctionError, match="exactly 10 profiles"):
        compile_source_function_profiles(payload)
