"""Local FastAPI surface for the Penrose QLC workbench."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .contracts import ContractError, contract_schemas, utc_now
from .curriculum import TENEBRIS_BUDGETS, diagnostic_path, fixture_catalog, laboratory_catalog
from .gateway_client import GatewayClient, GatewayUnavailable
from .geometry_trace import build_apollonian_trace
from .missions import MissionEngine, MissionError
from .portfolio import build_portfolio_case_study
from .storage import AlphaStore
from .vigil import build_handoff_request, build_professor_decision, build_vigil_report, WAKEUP_KIT

from .fractal_measurement import measure_tile_fractal_path
from .cpai_yolo import (
    DEFAULT_CPAI_URL,
    probe_cpai_status,
    probe_yolo_detection_routes,
    probe_yolo_training_module,
    plan_yolo_training,
)
from .orb_envelope import (
    build_orb_envelope,
    export_redacted_orb_json,
    export_vad_reusable_template,
)
from .penrose_cut_project import CutProjectInput, cut_project_penrose_patch
from .penrose_geometry import PenrosePatch, tile_metadata
from .penrose_inflation import InflationInput, inflate_penrose_patch
from .plithogenic_gate import classify_plithogenic_tile, export_plithogenic_tile_classification
from .source_functions import build_source_function_graph, compile_source_function_profiles
from .tile_admission import (
    build_tile_admission_ledger,
    compute_t_df_f,
    export_tile_admission_profile,
)


MAX_REQUEST_BYTES = 1_000_000
LOCAL_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
)


class LatticeRequest(BaseModel):
    engine: str = Field(default="inflation", pattern="^(inflation|cut_project)$")
    target_tile_count: int = Field(default=8, ge=1, le=200)
    depth: int = Field(default=3, ge=0, le=8)
    seed: str = "api"


class TrainingPlanRequest(BaseModel):
    cpai_url: str = "http://localhost:32168"
    model_name: str = "ffed-qlc-yolo"
    dataset_name: str = "ffed-qlc-metadata-only"
    epochs: int = Field(default=10, ge=1, le=1000)
    require_confirmation: bool = True


class SessionBootstrapRequest(BaseModel):
    role: str = Field(pattern="^(student_minor|student_adult|teacher)$")
    fingerprint_ref: str = Field(min_length=8, max_length=128)
    consent_scope: str = Field(default="tool", pattern="^(tool|suite)$")
    provider_route: str = Field(default="codex", pattern="^(codex|gemini)$")
    has_prior_metrics: bool = False


class ProjectRequest(BaseModel):
    session_id: str
    title: str = Field(min_length=1, max_length=120)
    level: str = Field(default="college", pattern="^(secondary_5|college|university)$")


class MissionStartRequest(BaseModel):
    project_id: str
    lab_id: str = Field(pattern="^lab-0[1-9]$")


class MissionExecuteRequest(BaseModel):
    action: str
    fixture_id: str | None = None


class VigilRequest(BaseModel):
    provider_route: str = Field(default="deterministic", pattern="^(deterministic|codex|gemini)$")


class ProfessorDecisionRequest(BaseModel):
    report_id: str
    teacher_session_id: str
    decision: str = Field(pattern="^(accept|suspend|reject|revise)$")
    note: str = Field(default="", max_length=1000)


class ProfessorBudgetRequest(BaseModel):
    project_id: str
    teacher_session_id: str
    budgets: dict[str, int]


class HandoffRequest(BaseModel):
    project_id: str
    target_slug: str
    mascot: str = Field(min_length=1, max_length=80)
    metric_names: list[str] = Field(default_factory=list, max_length=8)


def create_app(
    *,
    store: AlphaStore | None = None,
    gateway: GatewayClient | None = None,
) -> FastAPI:
    """Create the local-only FastAPI app."""

    app = FastAPI(
        title="FfeD QLC Penrose Lattice Workbench API",
        version="0.1.0",
        description="Local pre-alpha API for Penrose QLC math and redacted exports.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(LOCAL_CORS_ORIGINS),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["content-type"],
    )
    alpha_store = store or AlphaStore()
    gateway_client = gateway or GatewayClient()
    mission_engine = MissionEngine(alpha_store)

    @app.middleware("http")
    async def request_size_cap(request: Request, call_next):  # type: ignore[no-untyped-def]
        length = request.headers.get("content-length")
        if length is not None and int(length) > MAX_REQUEST_BYTES:
            raise HTTPException(
                status_code=413,
                detail={"code": "request_too_large", "max_bytes": MAX_REQUEST_BYTES},
            )
        return await call_next(request)

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "ffed-qlc-penrose-workbench",
            "runtime": "local",
            "secret_values_exposed": False,
        }

    @app.get("/api/v1/health/live")
    def live() -> dict[str, Any]:
        return {"status": "live", "service": "ffed-qlc-alpha", "version": "v1"}

    @app.get("/api/v1/health/ready")
    def ready() -> dict[str, Any]:
        result = gateway_client.readiness()
        if not result.get("ready"):
            raise HTTPException(status_code=503, detail=result)
        return {"status": "ready", "gateway": result, "storage": "sqlite"}

    @app.get("/api/v1/contracts")
    def contracts() -> dict[str, Any]:
        return {"schemas": contract_schemas(), "wakeup_kit": WAKEUP_KIT}

    @app.post("/api/v1/session/bootstrap")
    def session_bootstrap(request: SessionBootstrapRequest) -> dict[str, Any]:
        try:
            session = gateway_client.build_session(
                request.role,
                request.fingerprint_ref,
                request.consent_scope,
                ["ffed-qlc"],
            )
            session["provider_route"] = request.provider_route
            alpha_store.save_session(session)
        except (ContractError, GatewayUnavailable) as exc:
            raise HTTPException(status_code=503, detail={"code": "gateway_rejected", "message": str(exc)}) from exc
        return {"session": session, "diagnostic": diagnostic_path(request.has_prior_metrics)}

    @app.get("/api/v1/fixtures")
    def fixtures() -> dict[str, Any]:
        return {"fixtures": fixture_catalog(), "raw_fixture_content_exposed": False}

    @app.get("/api/v1/laboratories")
    def laboratories() -> dict[str, Any]:
        return {"laboratories": laboratory_catalog()}

    @app.post("/api/v1/geometry/apollonian")
    def apollonian(depth: int = 3) -> dict[str, Any]:
        return build_apollonian_trace(depth=depth)

    @app.post("/api/v1/projects")
    def create_project(request: ProjectRequest) -> dict[str, Any]:
        try:
            return alpha_store.create_project(request.session_id, request.title, request.level)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/projects")
    def list_projects(session_id: str) -> dict[str, Any]:
        return {"projects": alpha_store.list_projects(session_id)}

    @app.post("/api/v1/missions")
    def start_mission(request: MissionStartRequest) -> dict[str, Any]:
        try:
            return mission_engine.start(request.project_id, request.lab_id)
        except (MissionError, KeyError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/missions/{run_id}/actions")
    def execute_mission(run_id: str, request: MissionExecuteRequest) -> dict[str, Any]:
        try:
            return mission_engine.execute(run_id, request.action, request.fixture_id)
        except (MissionError, KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/missions/{run_id}/vigil")
    def report_mission(run_id: str, request: VigilRequest) -> dict[str, Any]:
        try:
            run = alpha_store.get_run(run_id)
            if not run.get("evidence_ref"):
                raise MissionError("mission evidence is required")
            evidence = alpha_store.read_artifact(run["evidence_ref"])
            report = build_vigil_report(run, evidence, request.provider_route)
            return alpha_store.save_report(report)
        except (MissionError, KeyError, ValueError, ContractError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/v1/professor/decisions")
    def professor_decision(request: ProfessorDecisionRequest) -> dict[str, Any]:
        try:
            decision = build_professor_decision(request.report_id, request.teacher_session_id, request.decision, request.note)
            return alpha_store.save_decision(decision)
        except (PermissionError, KeyError, ContractError) as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

    @app.post("/api/v1/professor/budgets")
    def professor_budgets(request: ProfessorBudgetRequest) -> dict[str, Any]:
        try:
            effective = alpha_store.save_budget_profile(
                request.project_id,
                request.teacher_session_id,
                request.budgets,
                TENEBRIS_BUDGETS,
            )
            return {"project_id": request.project_id, "budgets": effective, "maximums": TENEBRIS_BUDGETS}
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/v1/professor/budgets/{project_id}")
    def project_budgets(project_id: str) -> dict[str, Any]:
        try:
            return {
                "project_id": project_id,
                "budgets": alpha_store.get_budget_profile(project_id, TENEBRIS_BUDGETS),
                "maximums": TENEBRIS_BUDGETS,
            }
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/v1/handoffs/registry")
    def handoff_registry() -> dict[str, Any]:
        try:
            return {"apps": gateway_client.suite_registry()}
        except GatewayUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.post("/api/v1/handoffs")
    def handoff(request: HandoffRequest) -> dict[str, Any]:
        try:
            app_entry = next((item for item in gateway_client.suite_registry() if item.get("slug") == request.target_slug), None)
        except GatewayUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        if app_entry is None:
            return build_handoff_request({}, request.mascot, request.metric_names, request.project_id)
        return build_handoff_request(app_entry, request.mascot, request.metric_names, request.project_id)

    @app.get("/api/v1/portfolio/{project_id}")
    def portfolio(project_id: str) -> dict[str, Any]:
        try:
            return build_portfolio_case_study(alpha_store, project_id)
        except (KeyError, ContractError) as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/api/source-functions")
    def source_functions() -> dict[str, Any]:
        profiles = compile_source_function_profiles()
        return {
            "source_count": len(profiles),
            "source_ids": [profile.source_id for profile in profiles],
            "graph": build_source_function_graph(profiles),
        }

    @app.post("/api/lattice/build")
    def lattice_build(request: LatticeRequest) -> dict[str, Any]:
        patch = _build_patch(request)
        return {
            "schema": "ffed.qlc.api.lattice_build.v1",
            "patch_metadata": dict(patch.metadata),
            "tiles": [tile_metadata(tile) for tile in patch.tiles],
        }

    @app.post("/api/lattice/classify")
    def lattice_classify(request: LatticeRequest) -> dict[str, Any]:
        patch = _build_patch(request)
        classifications = [classify_plithogenic_tile(tile) for tile in patch.tiles]
        return {
            "schema": "ffed.qlc.api.lattice_classify.v1",
            "patch_fingerprint": patch.metadata["patch_fingerprint"],
            "classifications": [
                export_plithogenic_tile_classification(item) for item in classifications
            ],
        }

    @app.post("/api/lattice/validate")
    def lattice_validate(request: LatticeRequest) -> dict[str, Any]:
        patch = _build_patch(request)
        _classifications, _measurements, admissions = _classify_measure_admit(patch)
        return {
            "schema": "ffed.qlc.api.lattice_validate.v1",
            "patch_fingerprint": patch.metadata["patch_fingerprint"],
            "admissions": [export_tile_admission_profile(item) for item in admissions],
            "ledger": build_tile_admission_ledger(admissions),
        }

    @app.post("/api/orbs/build")
    def orbs_build(request: LatticeRequest) -> dict[str, Any]:
        patch = _build_patch(request)
        classifications, measurements, admissions = _classify_measure_admit(patch)
        envelope = build_orb_envelope(patch, admissions, classifications, measurements)
        return export_redacted_orb_json(envelope)

    @app.post("/api/export/lattice-template")
    def lattice_template() -> dict[str, Any]:
        return export_vad_reusable_template()

    @app.get("/api/cpai/status")
    def cpai_status(cpai_url: str = DEFAULT_CPAI_URL) -> dict[str, Any]:
        return probe_cpai_status(cpai_url, dry_run=False, timeout_seconds=2.0)

    @app.get("/api/cpai/yolo/probe")
    def yolo_probe(cpai_url: str = DEFAULT_CPAI_URL) -> dict[str, Any]:
        return probe_yolo_detection_routes(cpai_url, dry_run=False)

    @app.get("/api/cpai/yolo/training/probe")
    def training_probe(cpai_url: str = DEFAULT_CPAI_URL) -> dict[str, Any]:
        return probe_yolo_training_module(cpai_url, dry_run=True)

    @app.post("/api/cpai/yolo/training/plan")
    def training_plan(request: TrainingPlanRequest) -> dict[str, Any]:
        return plan_yolo_training(
            cpai_url=request.cpai_url,
            model_name=request.model_name,
            dataset_name=request.dataset_name,
            epochs=request.epochs,
            requires_ui_confirmation=request.require_confirmation,
        )

    static_dir = Path(os.getenv("FFED_QLC_STATIC_DIR", Path(__file__).resolve().parents[2] / "dist"))
    if static_dir.joinpath("index.html").exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")

    return app


def _build_patch(request: LatticeRequest) -> PenrosePatch:
    if request.engine == "cut_project":
        return cut_project_penrose_patch(
            CutProjectInput(
                target_tile_count=request.target_tile_count,
                seed=request.seed,
            )
        ).patch
    return inflate_penrose_patch(
        InflationInput(
            depth=request.depth,
            target_tile_count=request.target_tile_count,
            seed=request.seed,
        )
    ).patch


def _classify_measure_admit(patch: PenrosePatch):
    classifications = [classify_plithogenic_tile(tile) for tile in patch.tiles]
    measurements = [
        measure_tile_fractal_path(tile, patch, carrier_type="fractal_boundary")
        for tile in patch.tiles
    ]
    admissions = [
        compute_t_df_f(tile, classification, measurement)
        for tile, classification, measurement in zip(patch.tiles, classifications, measurements)
    ]
    return classifications, measurements, admissions


app = create_app()
