from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import re

import pytest

from ffed_qlc.contracts import ContractError, contract_schemas, validate_contract
from ffed_qlc.curriculum import diagnostic_path, fixture_catalog, laboratory_catalog
from ffed_qlc.geometry_trace import build_apollonian_trace


def test_contract_registry_contains_all_public_alpha_contracts() -> None:
    schemas = contract_schemas()

    assert len(schemas) == 10
    assert "ffed.qlc.vigil_report.v1" in schemas
    assert schemas["ffed.qlc.orb_project.v1"]["additionalProperties"] is True


def test_python_and_typescript_contract_ids_are_identical() -> None:
    source = (Path(__file__).parents[1] / "frontend" / "src" / "alpha" / "contracts.ts").read_text(encoding="utf-8")
    typescript_ids = set(re.findall(r'"((?:securedme\.education|ffed\.qlc)\.[^"]+\.v1)"', source))
    assert typescript_ids == set(contract_schemas())


def test_session_contract_rejects_secret_fields_and_role_mismatch() -> None:
    payload = {
        "schema": "securedme.education.session-role.v1",
        "session_id": "session-safe",
        "fingerprint_ref": "fingerprint-redacted",
        "role": "student_adult",
        "surface": "student",
        "consent_scope": "tool",
        "allowed_tools": ["ffed-qlc"],
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    }
    validate_contract(payload)

    with pytest.raises(ContractError, match="forbidden field"):
        validate_contract(payload | {"api_key": "not-allowed"})
    with pytest.raises(ContractError, match="role and surface"):
        validate_contract(payload | {"surface": "teacher"})


def test_negative_raw_payload_flag_is_allowed_but_true_is_rejected() -> None:
    from ffed_qlc.contracts import reject_secret_material

    reject_secret_material({"raw_payload_exposed": False})
    with pytest.raises(ContractError, match="must remain false"):
        reject_secret_material({"raw_payload_exposed": True})


def test_curriculum_has_nine_bounded_labs_and_safe_baseline() -> None:
    labs = laboratory_catalog()
    fixtures = fixture_catalog()

    assert [lab["lab_id"] for lab in labs] == [f"lab-{index:02d}" for index in range(1, 10)]
    assert all(lab["proof_required"] for lab in labs)
    assert all(fixture["real_secret_content"] is False for fixture in fixtures)
    assert diagnostic_path(False)["absence_is_failure"] is False
    assert diagnostic_path(False)["starting_lab"] == "lab-01"


def test_apollonian_trace_is_exact_deterministic_and_bounded() -> None:
    first = build_apollonian_trace(depth=3)
    second = build_apollonian_trace(depth=3)

    assert first == second
    assert first["floating_point_used"] is False
    assert first["steps"]
    assert all(step["descartes_valid"] for step in first["steps"])
    assert len(first["steps"]) <= 4096
