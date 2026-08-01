"""Local FastAPI surface for the Penrose QLC workbench."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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


def create_app() -> FastAPI:
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
