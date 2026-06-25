from __future__ import annotations

import os
import re
import socket
from typing import Any, Mapping


QLC_WORKFLOW_METRICS = {
    "started": "ffed_qlc.workflow.started",
    "accepted": "ffed_qlc.workflow.accepted",
    "review_required": "ffed_qlc.workflow.review_required",
    "gateway_submit_ok": "ffed_qlc.gateway.submit.ok",
    "gateway_submit_failed": "ffed_qlc.gateway.submit.failed",
    "e2b_audit_pass": "ffed_qlc.e2b.audit.pass",
    "e2b_audit_fail": "ffed_qlc.e2b.audit.fail",
}


def _sanitize(value: str, *, limit: int = 120) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.\-/]", "_", str(value)).strip("_.-/")
    cleaned = re.sub(r"_+", "_", cleaned)
    return (cleaned[:limit] or "unknown")


def emit_dogstatsd_counter(name: str, value: int = 1, tags: tuple[str, ...] = ()) -> None:
    host = os.environ.get("DD_DOGSTATSD_HOST", "127.0.0.1")
    port = int(os.environ.get("DD_DOGSTATSD_PORT", "8125"))
    safe_name = _sanitize(name, limit=200)
    safe_tags = [_sanitize(t) for t in tags]
    tag_suffix = f"|#{','.join(safe_tags)}" if safe_tags else ""
    payload = f"{safe_name}:{value}|c{tag_suffix}".encode("utf-8")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(payload, (host, port))


def emit_qlc_workflow_counter(
    event: str,
    *,
    workflow_bundle: Mapping[str, Any] | None = None,
    simulator_result: Mapping[str, Any] | None = None,
    gateway_mode: str = "dry_run",
    e2b_enabled: bool = False,
    extra_tags: tuple[str, ...] = (),
) -> None:
    """Emit a typed QLC workflow DogStatsD counter with redacted tags only."""

    metric_name = QLC_WORKFLOW_METRICS.get(event, event)
    tags = _workflow_tags(workflow_bundle or {}, simulator_result or {}, gateway_mode, e2b_enabled)
    emit_dogstatsd_counter(metric_name, tags=(*tags, *extra_tags))


def _workflow_tags(
    workflow_bundle: Mapping[str, Any],
    simulator_result: Mapping[str, Any],
    gateway_mode: str,
    e2b_enabled: bool,
) -> tuple[str, ...]:
    artifacts = workflow_bundle.get("artifacts") if isinstance(workflow_bundle.get("artifacts"), Mapping) else {}
    gateway_submission = (
        workflow_bundle.get("gateway_submission") if isinstance(workflow_bundle.get("gateway_submission"), Mapping) else {}
    )
    mesh_payload = artifacts.get("mesh_payload") if isinstance(artifacts, Mapping) and isinstance(artifacts.get("mesh_payload"), Mapping) else {}
    plugin_context = mesh_payload.get("plugin_context") if isinstance(mesh_payload.get("plugin_context"), Mapping) else {}
    swop = (
        plugin_context.get("sensitivity_weighted_obfuscation_policy")
        if isinstance(plugin_context.get("sensitivity_weighted_obfuscation_policy"), Mapping)
        else {}
    )
    route_decision = artifacts.get("route_decision") if isinstance(artifacts, Mapping) and isinstance(artifacts.get("route_decision"), Mapping) else {}
    return (
        f"qlc_schema:{_tag_value(str(workflow_bundle.get('schema') or 'unknown'))}",
        f"media_type:{_tag_value(str(workflow_bundle.get('media_type') or 'unknown'))}",
        f"swop_level:{_tag_value(str(swop.get('sensitivity_level') or 'unknown'))}",
        f"route_action:{_tag_value(str(route_decision.get('action') or gateway_submission.get('route_action') or 'unknown'))}",
        f"simulator_status:{_tag_value(str(simulator_result.get('status') or 'not_run'))}",
        f"gateway_mode:{_tag_value(gateway_mode)}",
        f"e2b_enabled:{str(bool(e2b_enabled)).lower()}",
    )


def _tag_value(value: str) -> str:
    safe = value.lower().replace(" ", "_").replace(":", "_").replace(",", "_")
    return safe[:120] or "unknown"
