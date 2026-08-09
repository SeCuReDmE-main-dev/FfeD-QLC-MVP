from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from ffed_qlc.missions import MissionEngine, MissionError
from ffed_qlc.curriculum import laboratory_catalog
from ffed_qlc.portfolio import build_portfolio_case_study
from ffed_qlc.storage import AlphaStore
from ffed_qlc.vigil import build_professor_decision, build_vigil_report


def session(role: str, suffix: str) -> dict:
    return {
        "schema": "securedme.education.session-role.v1",
        "session_id": f"session-{suffix}",
        "fingerprint_ref": f"fingerprint-{suffix}",
        "role": role,
        "surface": "teacher" if role == "teacher" else "student",
        "consent_scope": "tool",
        "allowed_tools": ["ffed-qlc"],
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def test_project_mission_vigil_professor_and_portfolio_flow(tmp_path) -> None:
    store = AlphaStore(tmp_path)
    student = store.save_session(session("student_adult", "student"))
    teacher = store.save_session(session("teacher", "teacher"))
    project = store.create_project(student["session_id"], "My defensive orb", "college")
    engine = MissionEngine(store)

    run = engine.start(project["project_id"], "lab-05")
    result = engine.execute(run["run_id"], "trace_apollonian", "neural-graph-small")
    report = build_vigil_report(result["run"], result["evidence"], "codex")
    store.save_report(report)
    decision = build_professor_decision(report["report_id"], teacher["session_id"], "accept", "Evidence is bounded.")
    store.save_decision(decision)
    case_study = build_portfolio_case_study(store, project["project_id"])

    assert result["run"]["state"] == "evidence_ready"
    assert result["evidence"]["external_network_used"] is False
    assert report["human_review_required"] is True
    assert case_study["decisions"] == ["accept"]
    assert case_study["azure_readiness"]["deployment_performed"] is False


def test_mission_rejects_actions_outside_allowlist(tmp_path) -> None:
    store = AlphaStore(tmp_path)
    student = store.save_session(session("student_adult", "student"))
    project = store.create_project(student["session_id"], "Orb", "university")
    engine = MissionEngine(store)
    run = engine.start(project["project_id"], "lab-01")

    with pytest.raises(MissionError, match="allowlist"):
        engine.execute(run["run_id"], "run_shell")


def test_non_teacher_cannot_decide(tmp_path) -> None:
    store = AlphaStore(tmp_path)
    student = store.save_session(session("student_adult", "student"))
    project = store.create_project(student["session_id"], "Orb", "college")
    result = MissionEngine(store).execute(
        MissionEngine(store).start(project["project_id"], "lab-01")["run_id"],
        "inspect_primitives",
    )
    report = store.save_report(build_vigil_report(result["run"], result["evidence"]))
    decision = build_professor_decision(report["report_id"], student["session_id"], "accept")

    with pytest.raises(PermissionError, match="teacher"):
        store.save_decision(decision)


def test_teacher_can_only_reduce_tenebris_budgets(tmp_path) -> None:
    store = AlphaStore(tmp_path)
    student = store.save_session(session("student_adult", "student"))
    teacher = store.save_session(session("teacher", "teacher"))
    project = store.create_project(student["session_id"], "Bounded orb", "college")
    maximums = {"fixture_bytes": 1024, "retry_count": 3}

    effective = store.save_budget_profile(
        project["project_id"], teacher["session_id"], {"retry_count": 1}, maximums
    )
    assert effective == {"fixture_bytes": 1024, "retry_count": 1}
    with pytest.raises(ValueError, match="between 1 and 3"):
        store.save_budget_profile(
            project["project_id"], teacher["session_id"], {"retry_count": 4}, maximums
        )
    with pytest.raises(PermissionError, match="teacher"):
        store.save_budget_profile(
            project["project_id"], student["session_id"], {"retry_count": 1}, maximums
        )


def test_all_nine_laboratories_execute_distinct_bounded_actions(tmp_path) -> None:
    store = AlphaStore(tmp_path)
    student = store.save_session(session("student_adult", "all-labs"))
    project = store.create_project(student["session_id"], "Complete route", "university")
    engine = MissionEngine(store)

    mechanisms = set()
    for lab in laboratory_catalog():
        run = engine.start(project["project_id"], lab["lab_id"])
        result = engine.execute(run["run_id"], lab["allowed_action"])
        assert result["run"]["state"] == "evidence_ready"
        assert result["evidence"]["external_network_used"] is False
        assert result["evidence"]["arbitrary_shell_used"] is False
        mechanisms.add(result["evidence"]["mechanism"])

    assert len(mechanisms) == 9


def test_codex_and_gemini_vigil_vectors_have_contract_parity(tmp_path) -> None:
    store = AlphaStore(tmp_path)
    student = store.save_session(session("student_adult", "provider-parity"))
    project = store.create_project(student["session_id"], "Provider parity", "college")
    engine = MissionEngine(store)
    result = engine.execute(engine.start(project["project_id"], "lab-01")["run_id"], "inspect_primitives")

    codex = build_vigil_report(result["run"], result["evidence"], "codex")
    gemini = build_vigil_report(result["run"], result["evidence"], "gemini")
    ignored = {"report_id", "provider_route", "created_at"}
    assert {key: value for key, value in codex.items() if key not in ignored} == {
        key: value for key, value in gemini.items() if key not in ignored
    }
