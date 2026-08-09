"""Synthetic fixtures, Tenebris budgets, and the nine-laboratory curriculum."""

from __future__ import annotations

import hashlib
from typing import Any


TENEBRIS_BUDGETS = {
    "fixture_bytes": 1_048_576,
    "graph_nodes": 256,
    "graph_edges": 1024,
    "trace_steps": 4096,
    "mission_seconds": 10,
    "retry_count": 3,
}

_FIXTURE_BODIES = {
    "synthetic-env-basic": "DEMO_SERVICE_URL=https://training.invalid\nDEMO_ACCESS_VALUE=placeholder-only\n",
    "neural-graph-small": "input->hidden_a\ninput->hidden_b\nhidden_a->output\nhidden_b->output\n",
    "tampered-envelope": "FQLC1 educational malformed envelope fixture",
}


def fixture_catalog() -> list[dict[str, Any]]:
    entries = [
        ("synthetic-env-basic", "Synthetic configuration", "synthetic_env", "foundation"),
        ("neural-graph-small", "Synthetic neural-like graph", "graph", "applied"),
        ("tampered-envelope", "Tampered FQLC1 specimen", "container", "applied"),
    ]
    return [
        {
            "schema": "ffed.qlc.fixture.v1",
            "fixture_id": fixture_id,
            "title": title,
            "kind": kind,
            "sha256": hashlib.sha256(_FIXTURE_BODIES[fixture_id].encode("utf-8")).hexdigest(),
            "size_bytes": len(_FIXTURE_BODIES[fixture_id].encode("utf-8")),
            "difficulty": difficulty,
            "provenance": "securedme_curated_synthetic_fixture",
            "real_secret_content": False,
            "external_target": False,
        }
        for fixture_id, title, kind, difficulty in entries
    ]


def synthetic_fixture_bytes(fixture_id: str) -> bytes:
    try:
        return _FIXTURE_BODIES[fixture_id].encode("utf-8")
    except KeyError as exc:
        raise ValueError("unknown synthetic fixture") from exc


def laboratory_catalog() -> list[dict[str, Any]]:
    definitions = (
        ("lab-01", "Primitive boundaries", "foundation", "inspect_primitives", "Identify what scrypt and AEAD provide."),
        ("lab-02", "Inspect FQLC1", "foundation", "inspect_fqlc1", "Read a public header without exposing content."),
        ("lab-03", "Metadata pressure", "foundation", "classify_metadata", "Separate useful metadata from avoidable disclosure."),
        ("lab-04", "Geometric permutation", "applied", "compare_permutation", "Measure structural permutation without calling it encryption."),
        ("lab-05", "Apollonian trace", "applied", "trace_apollonian", "Verify integer Descartes reflections and cycles."),
        ("lab-06", "Bounded red mission", "applied", "run_bounded_attack", "Test malformed synthetic inputs under Tenebris limits."),
        ("lab-07", "Blue correction", "advanced", "apply_defense", "Correct one observable weakness and preserve evidence."),
        ("lab-08", "Suite handoff", "advanced", "request_handoff", "Request only the minimum metric from a remote mascot."),
        ("lab-09", "Capstone orb", "capstone", "export_portfolio", "Assemble a reviewed orb and portfolio evidence bundle."),
    )
    return [
        {
            "lab_id": lab_id,
            "title": title,
            "difficulty": difficulty,
            "allowed_action": action,
            "objective": objective,
            "duration_minutes": 45 if difficulty != "capstone" else 120,
            "prerequisites": [] if lab_id == "lab-01" else [f"lab-{int(lab_id[-2:]) - 1:02d}"],
            "proof_required": True,
            "professor_review_required": lab_id in {"lab-06", "lab-07", "lab-08", "lab-09"},
        }
        for lab_id, title, difficulty, action, objective in definitions
    ]


def diagnostic_path(has_prior_metrics: bool) -> dict[str, Any]:
    return {
        "schema": "ffed.qlc.diagnostic_path.v1",
        "prior_metrics_available": has_prior_metrics,
        "starting_lab": "lab-04" if has_prior_metrics else "lab-01",
        "absence_is_failure": False,
        "route_reason": "prior_evidence" if has_prior_metrics else "local_baseline",
    }
