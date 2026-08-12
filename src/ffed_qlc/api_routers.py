"""Router factories for the public, alpha, FQLC2, and legacy API surfaces."""

from __future__ import annotations

import base64
import binascii
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from fastapi import APIRouter, HTTPException

from .api_models import (
    FQLC2InspectRequest,
    FQLC2RoundtripRequest,
    LegacyHandoffRequest,
    LatticeRequest,
    MissionExecuteRequest,
    MissionStartRequest,
    NativeHandoffRequest,
    ProfessorBudgetRequest,
    ProfessorDecisionRequest,
    ProjectRequest,
    SessionBootstrapRequest,
    TrainingPlanRequest,
    VigilRequest,
)
from .contracts import ContractError, contract_schemas
from .cpai_yolo import plan_yolo_training, probe_cpai_status, probe_yolo_detection_routes, probe_yolo_training_module
from .curriculum import TENEBRIS_BUDGETS, diagnostic_path, fixture_catalog, laboratory_catalog, synthetic_fixture_bytes
from .fqlc2 import FQLC2Error, FQLC2Limits, inspect_bytes_v2, pack_bytes_v2, unpack_bytes_v2
from .fractal_measurement import measure_tile_fractal_path
from .gateway_client import GatewayClient, GatewayUnavailable
from .identity import IdentityVerifier
from .missions import MissionEngine, MissionError
from .native_handoff import NativeHandoffAdapter, NativeHandoffEnvelope, NativeHandoffError
from .orb_envelope import build_orb_envelope, export_redacted_orb_json, export_vad_reusable_template
from .penrose_cut_project import CutProjectInput, cut_project_penrose_patch
from .penrose_geometry import PenrosePatch, tile_metadata
from .penrose_inflation import InflationInput, inflate_penrose_patch
from .plithogenic_gate import classify_plithogenic_tile, export_plithogenic_tile_classification
from .portfolio import build_portfolio_case_study
from .runtime_config import RuntimeConfig
from .source_functions import build_source_function_graph, compile_source_function_profiles
from .storage import AlphaStore
from .tile_admission import build_tile_admission_ledger, compute_t_df_f, export_tile_admission_profile
from .vigil import WAKEUP_KIT, build_professor_decision, build_vigil_report
from .geometry_trace import build_apollonian_trace


def public_router(
    *,
    gateway: GatewayClient,
    store: AlphaStore,
    identity: IdentityVerifier,
    handoff: NativeHandoffAdapter,
    config: RuntimeConfig,
) -> APIRouter:
    router = APIRouter()

    @router.get("/api/health")
    def legacy_health() -> dict[str, Any]:
        return {"status": "ok", "service": "ffed-qlc", "runtime": config.runtime, "secret_values_exposed": False}

    @router.get("/api/v1/health/live")
    def live() -> dict[str, Any]:
        return {"status": "live", "service": "ffed-qlc-alpha", "version": "v1", "secret_values_exposed": False}

    @router.get("/api/v1/health/ready")
    def ready() -> dict[str, Any]:
        result = gateway.readiness()
        if config.public_stateful_enabled and not result.get("ready"):
            raise _http_error(503, "GATEWAY_UNAVAILABLE", "Gateway readiness failed")
        return {
            "status": "ready",
            "gateway": {
                "ready": bool(result.get("ready")),
                "required_for_public_runtime": config.public_stateful_enabled,
                "secret_values_exposed": False,
            },
            "storage": str(store.db_path.name),
            "secret_values_exposed": False,
        }

    @router.get("/api/v1/capabilities")
    def capabilities() -> dict[str, object]:
        return config.capabilities(identity_ready=identity.ready, native_runtime_ready=handoff.ready)

    @router.get("/api/v1/contracts")
    def contracts() -> dict[str, Any]:
        return {"schemas": contract_schemas(), "wakeup_kit": WAKEUP_KIT}

    @router.get("/api/v1/fixtures")
    def fixtures() -> dict[str, Any]:
        return {"fixtures": fixture_catalog(), "raw_fixture_content_exposed": False}

    @router.get("/api/v1/laboratories")
    def laboratories() -> dict[str, Any]:
        return {"laboratories": laboratory_catalog()}

    return router


def alpha_router(
    *,
    gateway: GatewayClient,
    store: AlphaStore,
    identity: IdentityVerifier,
    handoff: NativeHandoffAdapter,
    config: RuntimeConfig,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1")
    missions = MissionEngine(store)

    def require_stateful(action: str) -> None:
        if not config.public_stateful_enabled or not identity.ready:
            raise _http_error(503, "IDENTITY_INTEGRATION_PENDING", f"{action} requires the verified identity adapter")

    @router.post("/session/bootstrap")
    def session_bootstrap(request: SessionBootstrapRequest) -> dict[str, Any]:
        require_stateful("session bootstrap")
        identity.verify(subject_ref=request.fingerprint_ref, role=request.role, action="session.bootstrap")
        try:
            session = gateway.build_session(request.role, request.fingerprint_ref, request.consent_scope, ["ffed-qlc"])
            session["provider_route"] = request.provider_route
            store.save_session(session)
        except (ContractError, GatewayUnavailable) as exc:
            raise _http_error(503, "GATEWAY_REJECTED", str(exc)) from exc
        return {"session": session, "diagnostic": diagnostic_path(request.has_prior_metrics)}

    @router.post("/projects")
    def create_project(request: ProjectRequest) -> dict[str, Any]:
        require_stateful("project creation")
        try:
            return store.create_project(request.session_id, request.title, request.level)
        except KeyError as exc:
            raise _http_error(404, "SESSION_NOT_FOUND", str(exc)) from exc

    @router.get("/projects")
    def list_projects(session_id: str) -> dict[str, Any]:
        require_stateful("project listing")
        return {"projects": store.list_projects(session_id)}

    @router.post("/missions")
    def start_mission(request: MissionStartRequest) -> dict[str, Any]:
        require_stateful("mission start")
        try:
            return missions.start(request.project_id, request.lab_id)
        except (MissionError, KeyError) as exc:
            raise _http_error(400, "MISSION_REJECTED", str(exc)) from exc

    @router.post("/missions/{run_id}/actions")
    def execute_mission(run_id: str, request: MissionExecuteRequest) -> dict[str, Any]:
        require_stateful("mission execution")
        try:
            return missions.execute(run_id, request.action, request.fixture_id, request.idempotency_key)
        except (MissionError, KeyError, ValueError) as exc:
            raise _http_error(400, "MISSION_REJECTED", str(exc)) from exc

    @router.post("/missions/{run_id}/vigil")
    def report_mission(run_id: str, request: VigilRequest) -> dict[str, Any]:
        require_stateful("Vigil report")
        try:
            run = store.get_run(run_id)
            if not run.get("evidence_ref"):
                raise MissionError("mission evidence is required")
            evidence = store.read_artifact(run["evidence_ref"])
            report = store.save_report(build_vigil_report(run, evidence))
            if request.handoff_target:
                if not config.native_handoffs_enabled or not handoff.ready:
                    report["native_handoff"] = {"status": "NATIVE_RUNTIME_UNAVAILABLE"}
                else:
                    envelope = NativeHandoffEnvelope.build(
                        target=request.handoff_target,
                        capability="vigil_report_review",
                        consent_receipt_id=f"session:{run['project_id']}",
                        evidence_refs=[evidence["sha256"]],
                    )
                    report["native_handoff"] = handoff.dispatch(envelope)
            return report
        except (MissionError, KeyError, ValueError, ContractError, NativeHandoffError) as exc:
            code = exc.code if isinstance(exc, NativeHandoffError) else "VIGIL_REJECTED"
            raise _http_error(400, code, str(exc)) from exc

    @router.post("/professor/decisions")
    def professor_decision(request: ProfessorDecisionRequest) -> dict[str, Any]:
        require_stateful("professor decision")
        try:
            return store.save_decision(
                build_professor_decision(request.report_id, request.teacher_session_id, request.decision, request.note)
            )
        except (PermissionError, KeyError, ContractError) as exc:
            raise _http_error(403, "PROFESSOR_AUTHORITY_REQUIRED", str(exc)) from exc

    @router.post("/professor/budgets")
    def professor_budgets(request: ProfessorBudgetRequest) -> dict[str, Any]:
        require_stateful("professor budget")
        try:
            effective = store.save_budget_profile(request.project_id, request.teacher_session_id, request.budgets, TENEBRIS_BUDGETS)
            return {"project_id": request.project_id, "budgets": effective, "maximums": TENEBRIS_BUDGETS}
        except PermissionError as exc:
            raise _http_error(403, "PROFESSOR_AUTHORITY_REQUIRED", str(exc)) from exc
        except (KeyError, ValueError) as exc:
            raise _http_error(400, "BUDGET_REJECTED", str(exc)) from exc

    @router.get("/professor/budgets/{project_id}")
    def project_budgets(project_id: str) -> dict[str, Any]:
        require_stateful("professor budget read")
        try:
            return {"project_id": project_id, "budgets": store.get_budget_profile(project_id, TENEBRIS_BUDGETS), "maximums": TENEBRIS_BUDGETS}
        except KeyError as exc:
            raise _http_error(404, "PROJECT_NOT_FOUND", str(exc)) from exc

    @router.get("/handoffs/registry")
    def handoff_registry() -> dict[str, Any]:
        try:
            return {"apps": gateway.suite_registry()}
        except GatewayUnavailable as exc:
            raise _http_error(503, "GATEWAY_UNAVAILABLE", str(exc)) from exc

    @router.post("/handoffs/native")
    def native_handoff(request: NativeHandoffRequest) -> dict[str, object]:
        require_stateful("native handoff")
        if not config.native_handoffs_enabled or not handoff.ready:
            raise _http_error(503, "NATIVE_RUNTIME_UNAVAILABLE", "native Codex/Gemini runtime is unavailable")
        try:
            envelope = NativeHandoffEnvelope.build(
                target=request.target,
                capability=request.capability,
                consent_receipt_id=request.consent_receipt_id,
                evidence_refs=request.evidence_refs,
                deadline_seconds=request.deadline_seconds,
            )
            return handoff.dispatch(envelope)
        except NativeHandoffError as exc:
            raise _http_error(503, exc.code, str(exc)) from exc

    @router.post("/handoffs")
    def legacy_handoff(request: LegacyHandoffRequest) -> dict[str, object]:
        del request
        raise _http_error(
            410,
            "NATIVE_HANDOFF_CONTRACT_REQUIRED",
            "legacy planned handoffs were removed; use /api/v1/handoffs/native with consent and evidence references",
        )

    @router.get("/portfolio/{project_id}")
    def portfolio(project_id: str) -> dict[str, Any]:
        require_stateful("portfolio")
        try:
            return build_portfolio_case_study(store, project_id)
        except (KeyError, ContractError) as exc:
            raise _http_error(404, "PROJECT_NOT_FOUND", str(exc)) from exc

    return router


def fqlc2_router(config: RuntimeConfig) -> APIRouter:
    router = APIRouter(prefix="/api/v1/fqlc2")

    @router.post("/synthetic-roundtrip")
    def synthetic_roundtrip(request: FQLC2RoundtripRequest) -> dict[str, Any]:
        if not config.fqlc2_enabled:
            raise _http_error(503, "FQLC2_DISABLED", "FQLC2 is disabled by Settings")
        fixture = synthetic_fixture_bytes(request.fixture_id)
        if request.recipient_count > config.fqlc2_max_recipients:
            raise _http_error(400, "RECIPIENT_LIMIT_EXCEEDED", "recipient count exceeds the Settings-governed bound")
        recipients = [X25519PrivateKey.generate() for _ in range(request.recipient_count)]
        signing_key = Ed25519PrivateKey.generate() if request.signed else None
        limits = FQLC2Limits(chunk_bytes=config.fqlc2_chunk_bytes, max_recipients=config.fqlc2_max_recipients)
        container = pack_bytes_v2(fixture, [key.public_key() for key in recipients], signing_key=signing_key, limits=limits)
        recovered = unpack_bytes_v2(container, recipients[0], require_signature=request.signed, limits=limits)
        if recovered != fixture:
            raise _http_error(500, "FQLC2_ROUNDTRIP_FAILED", "synthetic roundtrip did not match")
        return {
            "schema": "ffed.qlc.fqlc2.synthetic-roundtrip.v1",
            "manifest": inspect_bytes_v2(container, limits=limits),
            "container_base64": base64.b64encode(container).decode("ascii"),
            "synthetic_fixture": True,
            "roundtrip_verified": True,
            "private_key_exposed": False,
            "secret_values_exposed": False,
        }

    @router.post("/inspect")
    def inspect_container(request: FQLC2InspectRequest) -> dict[str, Any]:
        if not config.fqlc2_enabled:
            raise _http_error(503, "FQLC2_DISABLED", "FQLC2 is disabled by Settings")
        try:
            container = base64.b64decode(request.container_base64, validate=True)
            return inspect_bytes_v2(container, limits=FQLC2Limits(chunk_bytes=config.fqlc2_chunk_bytes, max_recipients=config.fqlc2_max_recipients))
        except (binascii.Error, FQLC2Error) as exc:
            raise _http_error(400, "INVALID_FQLC2_CONTAINER", str(exc)) from exc

    return router


def legacy_math_router(config: RuntimeConfig) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/source-functions")
    def source_functions() -> dict[str, Any]:
        profiles = compile_source_function_profiles()
        return {"source_count": len(profiles), "source_ids": [profile.source_id for profile in profiles], "graph": build_source_function_graph(profiles)}

    @router.post("/lattice/build")
    def lattice_build(request: LatticeRequest) -> dict[str, Any]:
        patch = _build_patch(request)
        return {"schema": "ffed.qlc.api.lattice_build.v1", "patch_metadata": dict(patch.metadata), "tiles": [tile_metadata(tile) for tile in patch.tiles]}

    @router.post("/lattice/classify")
    def lattice_classify(request: LatticeRequest) -> dict[str, Any]:
        patch = _build_patch(request)
        classifications = [classify_plithogenic_tile(tile) for tile in patch.tiles]
        return {"schema": "ffed.qlc.api.lattice_classify.v1", "patch_fingerprint": patch.metadata["patch_fingerprint"], "classifications": [export_plithogenic_tile_classification(item) for item in classifications]}

    @router.post("/lattice/validate")
    def lattice_validate(request: LatticeRequest) -> dict[str, Any]:
        patch = _build_patch(request)
        _, _, admissions = _classify_measure_admit(patch)
        return {"schema": "ffed.qlc.api.lattice_validate.v1", "patch_fingerprint": patch.metadata["patch_fingerprint"], "admissions": [export_tile_admission_profile(item) for item in admissions], "ledger": build_tile_admission_ledger(admissions)}

    @router.post("/orbs/build")
    def orbs_build(request: LatticeRequest) -> dict[str, Any]:
        patch = _build_patch(request)
        classifications, measurements, admissions = _classify_measure_admit(patch)
        return export_redacted_orb_json(build_orb_envelope(patch, admissions, classifications, measurements))

    @router.post("/export/lattice-template")
    def lattice_template() -> dict[str, Any]:
        return export_vad_reusable_template()

    @router.post("/v1/geometry/apollonian")
    def apollonian(depth: int = 3) -> dict[str, Any]:
        return build_apollonian_trace(depth=depth)

    @router.get("/cpai/status")
    def cpai_status() -> dict[str, Any]:
        url = config.require_cpai_url(config.cpai_allowed_base_urls[0])
        return probe_cpai_status(url, dry_run=False, timeout_seconds=2.0)

    @router.get("/cpai/yolo/probe")
    def yolo_probe() -> dict[str, Any]:
        url = config.require_cpai_url(config.cpai_allowed_base_urls[0])
        return probe_yolo_detection_routes(url, dry_run=False)

    @router.get("/cpai/yolo/training/probe")
    def training_probe() -> dict[str, Any]:
        url = config.require_cpai_url(config.cpai_allowed_base_urls[0])
        return probe_yolo_training_module(url, dry_run=True)

    @router.post("/cpai/yolo/training/plan")
    def training_plan(request: TrainingPlanRequest) -> dict[str, Any]:
        try:
            url = config.require_cpai_url(request.cpai_url)
        except ValueError as exc:
            raise _http_error(400, "CPAI_ENDPOINT_REJECTED", str(exc)) from exc
        return plan_yolo_training(cpai_url=url, model_name=request.model_name, dataset_name=request.dataset_name, epochs=request.epochs, requires_ui_confirmation=request.require_confirmation)

    return router


def _build_patch(request: LatticeRequest) -> PenrosePatch:
    if request.engine == "cut_project":
        return cut_project_penrose_patch(CutProjectInput(target_tile_count=request.target_tile_count, seed=request.seed)).patch
    return inflate_penrose_patch(InflationInput(depth=request.depth, target_tile_count=request.target_tile_count, seed=request.seed)).patch


def _classify_measure_admit(patch: PenrosePatch):
    classifications = [classify_plithogenic_tile(tile) for tile in patch.tiles]
    measurements = [measure_tile_fractal_path(tile, patch, carrier_type="fractal_boundary") for tile in patch.tiles]
    admissions = [compute_t_df_f(tile, classification, measurement) for tile, classification, measurement in zip(patch.tiles, classifications, measurements)]
    return classifications, measurements, admissions


def _http_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message, "secret_values_exposed": False})
