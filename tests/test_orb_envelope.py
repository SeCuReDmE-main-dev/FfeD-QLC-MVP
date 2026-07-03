from __future__ import annotations

import json

import pytest

from ffed_qlc import AdmDecision
from ffed_qlc.fractal_measurement import BOX_COUNTING_METHOD, FRACTAL_HIERARCHY, BoxCount, FractalMeasurement
from ffed_qlc.orb_envelope import (
    LATTICE_EXPORT_SCHEMA,
    ORB_ENVELOPE_SCHEMA,
    OrbEnvelopeError,
    build_orb_envelope,
    export_lattice_json_schema,
    export_lattice_python_shape,
    export_lattice_template_markdown,
    export_lattice_typescript_shape,
    export_redacted_lattice_json,
    export_redacted_orb_json,
    export_vad_reusable_template,
)
from ffed_qlc.penrose_geometry import build_penrose_patch, build_penrose_rhombus
from ffed_qlc.plithogenic_gate import classify_plithogenic_tile
from ffed_qlc.tile_admission import compute_t_df_f


def _measurement(value: float | None = 0.5) -> FractalMeasurement:
    return FractalMeasurement(
        status=AdmDecision.ACCEPT if value is not None else AdmDecision.SUSPEND,
        D_f=1.5 if value is not None else None,
        D_f_hat=value,
        dF=value,
        i_fractal=value,
        D_min=1.0,
        D_max=2.0,
        I_system_source="I_system^S.fractal_geometry" if value is not None else None,
        hierarchy=FRACTAL_HIERARCHY,
        confidence=0.8 if value is not None else 0.0,
        box_counts=(BoxCount(0.25, 8), BoxCount(0.5, 4), BoxCount(1.0, 2)),
        reason_codes=("dF_assigned_from_fractal_source",) if value is not None else ("missing_dF",),
        method_metadata={"method": BOX_COUNTING_METHOD},
        scale_metadata={"scale_count": 3},
    )


def _orb_fixture():
    accepted_tile = build_penrose_rhombus("thick", origin=(0.0, 0.0))
    rejected_tile = build_penrose_rhombus("thin", origin=(3.0, 0.0))
    patch = build_penrose_patch([accepted_tile, rejected_tile])
    accepted_class = classify_plithogenic_tile(accepted_tile)
    rejected_class = classify_plithogenic_tile(rejected_tile, source_function_ids=("S01", "S11"))
    accepted_admission = compute_t_df_f(accepted_tile, accepted_class, _measurement(0.5))
    rejected_admission = compute_t_df_f(rejected_tile, rejected_class, _measurement(0.5))
    measurements = [_measurement(0.5), _measurement(None)]
    envelope = build_orb_envelope(
        patch,
        [accepted_admission, rejected_admission],
        [accepted_class, rejected_class],
        measurements,
        data_refs=[
            {
                "chunk_id": "chunk-001",
                "chunk_fingerprint": "sha256:abc123",
                "media_type": "document",
            }
        ],
    )
    return patch, [accepted_admission, rejected_admission], envelope


def test_orb_links_data_only_to_accepted_tiles_and_tracks_rejected_fingerprints() -> None:
    patch, admissions, envelope = _orb_fixture()

    assert envelope.accepted_tile_ids == (patch.tiles[0].tile_id,)
    assert len(envelope.rejected_tile_fingerprints) == 1
    assert envelope.tile_data_bindings[0]["tile_id"] == patch.tiles[0].tile_id
    assert envelope.tile_data_bindings[0]["chunk_fingerprint"] == "sha256:abc123"
    assert admissions[1].admission_fingerprint in envelope.rejected_tile_fingerprints


def test_redacted_orb_and_lattice_exports_contain_no_plaintext_keys_or_raw_media() -> None:
    patch, admissions, envelope = _orb_fixture()
    orb_json = export_redacted_orb_json(envelope)
    lattice_json = export_redacted_lattice_json(patch, admissions, envelope)
    serialized = json.dumps({"orb": orb_json, "lattice": lattice_json}, sort_keys=True)

    assert orb_json["schema"] == ORB_ENVELOPE_SCHEMA
    assert lattice_json["schema"] == LATTICE_EXPORT_SCHEMA
    assert orb_json["plaintext_embedded"] is False
    assert orb_json["key_material_embedded"] is False
    assert orb_json["raw_media_embedded"] is False
    assert "https://" not in serialized
    assert "secret" not in serialized.casefold()
    assert "plaintext-data" not in serialized


def test_orb_rejects_raw_plaintext_or_key_material_refs() -> None:
    patch, admissions, _envelope = _orb_fixture()
    classification = classify_plithogenic_tile(patch.tiles[0])

    with pytest.raises(OrbEnvelopeError, match="forbidden"):
        build_orb_envelope(
            patch,
            admissions,
            [classification],
            [_measurement(0.5)],
            data_refs=[
                {
                    "chunk_id": "bad",
                    "chunk_fingerprint": "sha256:bad",
                    "plaintext": "plaintext-data",
                }
            ],
        )


def test_orb_id_is_deterministic() -> None:
    _patch, _admissions, first = _orb_fixture()
    _patch, _admissions, second = _orb_fixture()

    assert first.orb_id == second.orb_id
    assert first.data_envelope_fingerprint == second.data_envelope_fingerprint


def test_template_exports_are_vad_reusable() -> None:
    markdown = export_lattice_template_markdown()
    json_schema = export_lattice_json_schema()
    ts_shape = export_lattice_typescript_shape()
    py_shape = export_lattice_python_shape()
    vad = export_vad_reusable_template()

    assert "reusable_by: VAD" in markdown
    assert json_schema["properties"]["plaintext_embedded"]["const"] is False
    assert "FfedQlcRedactedLattice" in ts_shape
    assert "TypedDict" in py_shape
    assert vad["raw_payload_allowed"] is False
