from __future__ import annotations

from typing import Any, Mapping


ScorecardVerdict = str


def build_reciprocal_utility_scorecard(mesh_payload: Mapping[str, Any]) -> dict[str, Any]:
    """Score the reciprocal proof loop between QLC and the FNP-QNN simulator."""

    plugin_context = _mapping(mesh_payload.get("plugin_context"))
    cpai_context = _mapping(mesh_payload.get("cpai_context"))
    guard = _mapping(plugin_context.get("context_consistency_guard"))
    protection_case = _mapping(plugin_context.get("simulator_protection_case"))

    context_risk_pressure = _context_risk_pressure(guard)
    simulator_support_score = _simulator_support_score(mesh_payload, cpai_context, protection_case)
    qlc_protection_score = _qlc_protection_score(mesh_payload, plugin_context, protection_case)
    overall_verdict = _scorecard_verdict(
        simulator_support_score=simulator_support_score,
        qlc_protection_score=qlc_protection_score,
        context_risk_pressure=context_risk_pressure,
        guard_verdict=str(guard.get("verdict") or "suspend"),
    )
    return {
        "schema": "ffed.qlc.reciprocal_utility_scorecard.v1",
        "simulator_support_score": simulator_support_score,
        "qlc_protection_score": qlc_protection_score,
        "context_risk_pressure": context_risk_pressure,
        "overall_verdict": overall_verdict,
        "proof_mode": str(plugin_context.get("proof_mode") or mesh_payload.get("proof_goal") or "unknown")[:120],
        "claim_boundary": "local_mvp_reciprocity_score_not_scientific_proof_or_security_certification",
    }


def _simulator_support_score(
    mesh_payload: Mapping[str, Any],
    cpai_context: Mapping[str, Any],
    protection_case: Mapping[str, Any],
) -> float:
    signals = [
        bool(mesh_payload.get("run_qnn")),
        bool(mesh_payload.get("hydra_em_enabled")),
        bool(mesh_payload.get("gpcn_set_phi_enabled")),
        bool(mesh_payload.get("plugin_hook_enabled")),
        bool(cpai_context.get("can_connect")),
        bool(cpai_context.get("mesh_enabled")),
        str(protection_case.get("schema") or "") == "ffed.qlc.simulator_protection_case.v1",
    ]
    return _round_score(sum(1 for signal in signals if signal) / len(signals))


def _qlc_protection_score(
    mesh_payload: Mapping[str, Any],
    plugin_context: Mapping[str, Any],
    protection_case: Mapping[str, Any],
) -> float:
    memories = mesh_payload.get("memories") or []
    first_memory = _mapping(memories[0]) if isinstance(memories, list) and memories else {}
    provenance = _mapping(first_memory.get("provenance"))
    qlc = _mapping(provenance.get("qlc"))
    guard = _mapping(plugin_context.get("context_consistency_guard"))
    guarantees = protection_case.get("validated_guarantees") or []
    signals = [
        bool(plugin_context.get("qlc_container_sha256")),
        qlc.get("raw_payload_exposed") is False,
        str(guard.get("schema") or "") == "ffed.qlc.context_consistency_guard.v1",
        isinstance(guarantees, list) and "tampered_qlc_container_fails_authentication" in guarantees,
        str(protection_case.get("claim_boundary") or "").endswith("not_production_security_certification"),
    ]
    return _round_score(sum(1 for signal in signals if signal) / len(signals))


def _context_risk_pressure(guard: Mapping[str, Any]) -> float:
    verdict = str(guard.get("verdict") or "suspend")
    if verdict == "pass":
        return 0.0
    if verdict == "escalate":
        return 1.0
    return 0.5


def _scorecard_verdict(
    *,
    simulator_support_score: float,
    qlc_protection_score: float,
    context_risk_pressure: float,
    guard_verdict: str,
) -> ScorecardVerdict:
    if guard_verdict in {"suspend", "escalate"} or context_risk_pressure >= 0.5:
        return "needs_review"
    if simulator_support_score < 0.75:
        return "simulator_gap"
    if qlc_protection_score < 0.75:
        return "qlc_gap"
    return "reciprocal_pass"


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _round_score(value: float) -> float:
    return round(min(1.0, max(0.0, value)), 4)
