"""SQLite state and content-addressed evidence storage for the local alpha."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import uuid
from pathlib import Path
from typing import Any, Mapping

from .contracts import canonical_json, reject_secret_material, utc_now, validate_contract


SCHEMA_VERSION = 2
MAX_ARTIFACT_BYTES = 1_048_576


class AlphaStore:
    def __init__(self, root: str | Path | None = None) -> None:
        default = Path(os.getenv("LOCALAPPDATA", Path.home())) / "SecuredMe" / "FfeD-QLC"
        self.root = Path(root or os.getenv("FFED_QLC_DATA_DIR", default)).expanduser().resolve()
        self.artifacts = self.root / "artifacts"
        self.db_path = self.root / "alpha.sqlite3"
        self.root.mkdir(parents=True, exist_ok=True)
        self.artifacts.mkdir(parents=True, exist_ok=True)
        self._migrate()

    def connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def save_session(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        validate_contract(payload, "securedme.education.session-role.v1")
        with self.connection() as db:
            db.execute(
                """INSERT OR REPLACE INTO sessions
                (session_id, fingerprint_ref, role, surface, consent_scope, allowed_tools_json, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    payload["session_id"], payload["fingerprint_ref"], payload["role"], payload["surface"],
                    payload["consent_scope"], canonical_json(payload["allowed_tools"]), payload["expires_at"],
                    payload.get("created_at", utc_now()),
                ),
            )
        return dict(payload)

    def create_project(self, session_id: str, title: str, level: str) -> dict[str, Any]:
        project = {
            "schema": "ffed.qlc.orb_project.v1",
            "project_id": f"project-{uuid.uuid4().hex[:16]}",
            "session_id": session_id,
            "title": title.strip(),
            "level": level,
            "status": "diagnostic",
            "created_at": utc_now(),
        }
        validate_contract(project)
        with self.connection() as db:
            self._require_session(db, session_id)
            db.execute(
                "INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (project["project_id"], session_id, project["title"], level, project["status"], "{}", project["created_at"], project["created_at"]),
            )
        return project

    def list_projects(self, session_id: str) -> list[dict[str, Any]]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT project_id, session_id, title, level, status, created_at, updated_at FROM projects WHERE session_id=? ORDER BY created_at DESC",
                (session_id,),
            ).fetchall()
        return [dict(row) | {"schema": "ffed.qlc.orb_project.v1"} for row in rows]

    def save_run(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        validate_contract(payload, "ffed.qlc.mission_run.v1")
        with self.connection() as db:
            self._require_project(db, str(payload["project_id"]))
            db.execute(
                """INSERT OR REPLACE INTO mission_runs
                (run_id, project_id, lab_id, state, attempt_count, evidence_ref, report_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    payload["run_id"], payload["project_id"], payload["lab_id"], payload["state"],
                    payload["attempt_count"], payload.get("evidence_ref"), payload.get("report_id"),
                    payload["created_at"], payload.get("updated_at", utc_now()),
                ),
            )
        return dict(payload)

    def get_run(self, run_id: str) -> dict[str, Any]:
        with self.connection() as db:
            row = db.execute("SELECT * FROM mission_runs WHERE run_id=?", (run_id,)).fetchone()
        if row is None:
            raise KeyError("mission run not found")
        return dict(row) | {"schema": "ffed.qlc.mission_run.v1"}

    def save_report(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        validate_contract(payload, "ffed.qlc.vigil_report.v1")
        with self.connection() as db:
            db.execute(
                "INSERT OR REPLACE INTO reports VALUES (?, ?, ?, ?)",
                (payload["report_id"], payload["run_id"], canonical_json(payload), utc_now()),
            )
            db.execute("UPDATE mission_runs SET report_id=?, updated_at=? WHERE run_id=?", (payload["report_id"], utc_now(), payload["run_id"]))
        return dict(payload)

    def save_decision(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        validate_contract(payload, "ffed.qlc.professor_decision.v1")
        with self.connection() as db:
            teacher = db.execute("SELECT role FROM sessions WHERE session_id=?", (payload["teacher_session_id"],)).fetchone()
            if teacher is None or teacher["role"] != "teacher":
                raise PermissionError("a teacher session is required")
            db.execute(
                "INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?)",
                (payload["decision_id"], payload["report_id"], payload["teacher_session_id"], payload["decision"], payload.get("note", ""), payload["created_at"]),
            )
        return dict(payload)

    def save_budget_profile(
        self,
        project_id: str,
        teacher_session_id: str,
        requested: Mapping[str, int],
        maximums: Mapping[str, int],
    ) -> dict[str, int]:
        unknown = set(requested) - set(maximums)
        if unknown:
            raise ValueError(f"unknown Tenebris budget: {sorted(unknown)[0]}")
        effective = dict(maximums)
        for key, value in requested.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 1 or value > maximums[key]:
                raise ValueError(f"Tenebris budget {key} must be between 1 and {maximums[key]}")
            effective[key] = value
        with self.connection() as db:
            teacher = db.execute("SELECT role FROM sessions WHERE session_id=?", (teacher_session_id,)).fetchone()
            if teacher is None or teacher["role"] != "teacher":
                raise PermissionError("a teacher session is required")
            self._require_project(db, project_id)
            db.execute(
                """INSERT OR REPLACE INTO budget_profiles
                (project_id, teacher_session_id, budgets_json, updated_at) VALUES (?, ?, ?, ?)""",
                (project_id, teacher_session_id, canonical_json(effective), utc_now()),
            )
        return effective

    def get_budget_profile(self, project_id: str, defaults: Mapping[str, int]) -> dict[str, int]:
        with self.connection() as db:
            self._require_project(db, project_id)
            row = db.execute("SELECT budgets_json FROM budget_profiles WHERE project_id=?", (project_id,)).fetchone()
        return dict(defaults) if row is None else json.loads(row["budgets_json"])

    def save_artifact(self, value: Mapping[str, Any], media_type: str = "application/json") -> dict[str, Any]:
        reject_secret_material(value)
        data = canonical_json(value).encode("utf-8")
        if len(data) > MAX_ARTIFACT_BYTES:
            raise ValueError("artifact exceeds Tenebris fixture budget")
        digest = hashlib.sha256(data).hexdigest()
        path = self.artifacts / digest[:2] / f"{digest}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(data)
        with self.connection() as db:
            db.execute("INSERT OR IGNORE INTO artifacts VALUES (?, ?, ?, ?, ?)", (digest, media_type, len(data), str(path), utc_now()))
        return {"sha256": digest, "media_type": media_type, "size_bytes": len(data), "path": str(path)}

    def read_artifact(self, digest: str) -> dict[str, Any]:
        with self.connection() as db:
            row = db.execute("SELECT path FROM artifacts WHERE sha256=?", (digest,)).fetchone()
        if row is None:
            raise KeyError("artifact not found")
        path = Path(row["path"]).resolve()
        if self.artifacts not in path.parents:
            raise ValueError("artifact path escaped the store")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("artifact integrity check failed")
        return json.loads(data.decode("utf-8"))

    def project_bundle(self, project_id: str) -> dict[str, Any]:
        with self.connection() as db:
            project = db.execute("SELECT * FROM projects WHERE project_id=?", (project_id,)).fetchone()
            if project is None:
                raise KeyError("project not found")
            runs = [dict(row) for row in db.execute("SELECT * FROM mission_runs WHERE project_id=? ORDER BY created_at", (project_id,))]
            reports = [dict(row) for row in db.execute("SELECT payload_json FROM reports WHERE run_id IN (SELECT run_id FROM mission_runs WHERE project_id=?)", (project_id,))]
            decisions = [dict(row) for row in db.execute("SELECT * FROM decisions WHERE report_id IN (SELECT report_id FROM mission_runs WHERE project_id=?)", (project_id,))]
        payload = {
            "schema": "ffed.qlc.project_bundle.v1",
            "project": dict(project),
            "runs": runs,
            "reports": [json.loads(row["payload_json"]) for row in reports],
            "decisions": decisions,
            "raw_secret_stored": False,
        }
        payload["sha256"] = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
        return payload

    def _migrate(self) -> None:
        if self.db_path.exists():
            backup = self.db_path.with_suffix(".sqlite3.bak")
            if not backup.exists():
                shutil.copy2(self.db_path, backup)
        with self.connection() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_meta (version INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY, fingerprint_ref TEXT NOT NULL, role TEXT NOT NULL,
                    surface TEXT NOT NULL, consent_scope TEXT NOT NULL, allowed_tools_json TEXT NOT NULL,
                    expires_at TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS projects (
                    project_id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(session_id),
                    title TEXT NOT NULL, level TEXT NOT NULL, status TEXT NOT NULL, orb_json TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS mission_runs (
                    run_id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(project_id),
                    lab_id TEXT NOT NULL, state TEXT NOT NULL, attempt_count INTEGER NOT NULL,
                    evidence_ref TEXT, report_id TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS reports (
                    report_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES mission_runs(run_id),
                    payload_json TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS decisions (
                    decision_id TEXT PRIMARY KEY, report_id TEXT NOT NULL REFERENCES reports(report_id),
                    teacher_session_id TEXT NOT NULL REFERENCES sessions(session_id), decision TEXT NOT NULL,
                    note TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS artifacts (
                    sha256 TEXT PRIMARY KEY, media_type TEXT NOT NULL, size_bytes INTEGER NOT NULL,
                    path TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS budget_profiles (
                    project_id TEXT PRIMARY KEY REFERENCES projects(project_id),
                    teacher_session_id TEXT NOT NULL REFERENCES sessions(session_id),
                    budgets_json TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                """
            )
            if db.execute("SELECT COUNT(*) FROM schema_meta").fetchone()[0] == 0:
                db.execute("INSERT INTO schema_meta VALUES (?)", (SCHEMA_VERSION,))
            else:
                db.execute("UPDATE schema_meta SET version=?", (SCHEMA_VERSION,))

    @staticmethod
    def _require_session(db: sqlite3.Connection, session_id: str) -> None:
        if db.execute("SELECT 1 FROM sessions WHERE session_id=?", (session_id,)).fetchone() is None:
            raise KeyError("session not found")

    @staticmethod
    def _require_project(db: sqlite3.Connection, project_id: str) -> None:
        if db.execute("SELECT 1 FROM projects WHERE project_id=?", (project_id,)).fetchone() is None:
            raise KeyError("project not found")
