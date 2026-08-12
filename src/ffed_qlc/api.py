"""FastAPI application factory for the FfeD-QLC pre-alpha runtime."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api_routers import alpha_router, fqlc2_router, legacy_math_router, public_router
from .api_security import RequestSizeLimitMiddleware
from .gateway_client import GatewayClient
from .identity import IdentityVerifier, PendingIdentityVerifier
from .native_handoff import DisabledNativeHandoffAdapter, NativeHandoffAdapter, PivotCliHandoffAdapter
from .runtime_config import RuntimeConfig
from .storage import AlphaStore


LOCAL_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
)


def create_app(
    *,
    store: AlphaStore | None = None,
    gateway: GatewayClient | None = None,
    identity: IdentityVerifier | None = None,
    handoff: NativeHandoffAdapter | None = None,
    config: RuntimeConfig | None = None,
) -> FastAPI:
    runtime = config or RuntimeConfig.from_environment()
    alpha_store = store or AlphaStore()
    gateway_client = gateway or GatewayClient()
    identity_verifier = identity or PendingIdentityVerifier()
    if handoff is None:
        handoff_adapter: NativeHandoffAdapter = (
            PivotCliHandoffAdapter() if runtime.runtime == "local" and runtime.native_handoffs_enabled else DisabledNativeHandoffAdapter()
        )
    else:
        handoff_adapter = handoff

    app = FastAPI(
        title="FfeD QLC Penrose Lattice Workbench API",
        version="0.2.0-prealpha",
        description="Pre-alpha active public development API with bounded synthetic workflows.",
    )
    app.add_middleware(RequestSizeLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(LOCAL_CORS_ORIGINS),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["content-type"],
    )
    app.include_router(public_router(gateway=gateway_client, store=alpha_store, identity=identity_verifier, handoff=handoff_adapter, config=runtime))
    app.include_router(alpha_router(gateway=gateway_client, store=alpha_store, identity=identity_verifier, handoff=handoff_adapter, config=runtime))
    app.include_router(fqlc2_router(runtime))
    app.include_router(legacy_math_router(runtime))

    static_dir = Path(os.getenv("FFED_QLC_STATIC_DIR", Path(__file__).resolve().parents[2] / "dist"))
    if static_dir.joinpath("index.html").exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
    return app


app = create_app()
