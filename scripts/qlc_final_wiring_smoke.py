from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from ffed_qlc import inspect_qlc_workflow_bundle


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_REPOS = ROOT.parent
DEFAULT_BUNDLE = ROOT / "tests" / "fixtures" / "qlc_contract" / "qlc_workflow_image.json"
DEFAULT_GATEWAY_REPO = PUBLIC_REPOS / "fnpqnn_gateway_MVP"
DEFAULT_FNP_REPO = PUBLIC_REPOS / "FNP-QNN-MVP"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Final QLC -> Gateway -> FNP-QNN local wiring smoke runner.")
    parser.add_argument("--bundle", default=str(DEFAULT_BUNDLE))
    parser.add_argument("--gateway-repo", default=str(DEFAULT_GATEWAY_REPO))
    parser.add_argument("--fnp-repo", default=str(DEFAULT_FNP_REPO))
    parser.add_argument("--simulator-url", default="http://localhost:8000")
    parser.add_argument("--real-submit", action="store_true")
    parser.add_argument("--skip-fnp-testclient", action="store_true")
    args = parser.parse_args(argv)

    bundle_path = Path(args.bundle)
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    inspection = inspect_qlc_workflow_bundle(bundle)
    gateway = _run_gateway(bundle, Path(args.gateway_repo), args.simulator_url, real_submit=args.real_submit)
    fnp_runtime = (
        {"skipped": True, "reason": "--skip-fnp-testclient"}
        if args.skip_fnp_testclient
        else _run_fnp_testclient(bundle, Path(args.fnp_repo))
    )
    success = bool(inspection.get("success")) and bool(gateway.get("success")) and bool(fnp_runtime.get("success", True))
    print(
        json.dumps(
            {
                "success": success,
                "schema": "ffed.qlc.final_wiring_smoke.v1",
                "bundle": str(bundle_path),
                "contract_version": inspection.get("contract_version"),
                "route_action": inspection.get("route_action"),
                "swop_level": inspection.get("swop_level"),
                "inspect": _compact_inspection(inspection),
                "gateway": _compact_gateway(gateway),
                "fnp_runtime": fnp_runtime,
                "raw_payload_embedded": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if success else 1


def _run_gateway(bundle: dict[str, Any], gateway_repo: Path, simulator_url: str, *, real_submit: bool) -> dict[str, Any]:
    if gateway_repo.exists():
        sys.path.insert(0, str(gateway_repo))
    try:
        from fnpqnn_gateway_mvp.qlc_submit import qlc_submit
    except Exception as exc:
        return {"success": False, "stage": "gateway_import", "error": _compact_error(exc)}
    return qlc_submit(bundle, simulator_url=simulator_url, dry_run=not real_submit, timeout=5)


def _run_fnp_testclient(bundle: dict[str, Any], fnp_repo: Path) -> dict[str, Any]:
    if fnp_repo.exists():
        sys.path.insert(0, str(fnp_repo))
    try:
        from fastapi.testclient import TestClient
        from api.main import app
    except Exception as exc:
        return {"success": False, "stage": "fnp_import", "error": _compact_error(exc)}
    mesh_payload = bundle["gateway_submission"]["mesh_payload"]
    response = TestClient(app).post("/cerebrum/runtime/run", json=mesh_payload)
    if response.status_code != 200:
        return {"success": False, "stage": "fnp_runtime", "status_code": response.status_code, "body": response.text[:240]}
    body = response.json()
    runtime = body.get("runtime") or {}
    qlc_runtime = runtime.get("qlc_runtime") or {}
    return {
        "success": body.get("status") == "ok",
        "simulator_status": body.get("status"),
        "qlc_runtime_schema": qlc_runtime.get("schema"),
        "contract_version": qlc_runtime.get("contract_version"),
        "media_type": qlc_runtime.get("media_type"),
        "swop_level": qlc_runtime.get("swop_level"),
        "mesh_payload_fingerprint_present": bool(qlc_runtime.get("mesh_payload_fingerprint")),
        "raw_payload_embedded": bool(qlc_runtime.get("raw_payload_embedded", True)),
    }


def _compact_inspection(inspection: dict[str, Any]) -> dict[str, Any]:
    return {
        "success": inspection.get("success"),
        "schema": inspection.get("schema"),
        "bundle_schema": inspection.get("bundle_schema"),
        "contract_version": inspection.get("contract_version"),
        "workflow_fingerprint": inspection.get("workflow_fingerprint"),
        "redaction_verdict": inspection.get("redaction_verdict"),
    }


def _compact_gateway(gateway: dict[str, Any]) -> dict[str, Any]:
    return {
        "success": gateway.get("success"),
        "gateway_status": gateway.get("gateway_status"),
        "simulator_status": gateway.get("simulator_status"),
        "submission_fingerprint": gateway.get("submission_fingerprint"),
        "route_action": gateway.get("route_action"),
        "raw_payload_echoed": gateway.get("raw_payload_echoed", False),
    }


def _compact_error(exc: BaseException) -> str:
    return f"{type(exc).__name__}: {str(exc).replace(chr(10), ' ')[:180]}"


if __name__ == "__main__":
    raise SystemExit(main())
