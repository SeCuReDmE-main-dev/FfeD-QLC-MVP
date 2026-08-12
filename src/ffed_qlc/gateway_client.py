"""Credential-blind adapter to the canonical SecuredMe Education Gateway."""

from __future__ import annotations

import os
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping

from .contracts import ContractError, validate_contract


class GatewayUnavailable(RuntimeError):
    """Raised when the mandatory Education Gateway cannot be loaded."""


class GatewayClient:
    """Use the sibling Gateway contract implementation without reading credentials."""

    def __init__(self, gateway_root: str | Path | None = None) -> None:
        configured = gateway_root or os.getenv("FFED_QLC_GATEWAY_ROOT")
        self.gateway_root = (
            Path(configured).expanduser()
            if configured
            else Path(__file__).resolve().parents[3] / "fnpqnn_gateway_MVP"
        )
        self._module: ModuleType | None = None

    def readiness(self) -> dict[str, Any]:
        try:
            module = self._load_contract_module()
        except GatewayUnavailable as exc:
            return {"ready": False, "code": "gateway_unavailable", "detail": str(exc)}
        return {
            "ready": callable(getattr(module, "validate_session_role", None)),
            "transport": "credential_blind_python_contract",
            "gateway_configured": True,
            "secret_values_exposed": False,
        }

    def validate_session(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        validate_contract(payload, "securedme.education.session-role.v1")
        module = self._load_contract_module()
        errors = module.validate_session_role(payload)
        if errors:
            raise ContractError(f"Gateway rejected session: {errors}")
        return dict(payload)

    def build_session(
        self,
        role: str,
        fingerprint_ref: str,
        consent_scope: str,
        allowed_tools: list[str],
    ) -> dict[str, Any]:
        module = self._load_contract_module()
        payload = module.build_session_role(
            role,
            fingerprint_ref=fingerprint_ref,
            consent_scope=consent_scope,
            allowed_tools=allowed_tools,
        )
        if not payload.pop("success", False):
            raise ContractError(f"Gateway could not build session: {payload.pop('errors', [])}")
        payload.pop("errors", None)
        return self.validate_session(payload)

    def suite_registry(self) -> list[dict[str, Any]]:
        self._load_contract_module()
        try:
            module = __import__("fnpqnn_gateway_mvp.suite_auth", fromlist=["*"])
        except Exception as exc:
            raise GatewayUnavailable("Gateway suite registry could not be loaded") from exc
        return [repo.as_dict() for repo in module.EDUCATION_SUITE_REPOS if repo.role != "auth_enforcer"]

    def _load_contract_module(self) -> ModuleType:
        if self._module is not None:
            return self._module
        module_path = self.gateway_root / "fnpqnn_gateway_mvp" / "algoquest_companion.py"
        package_root = self.gateway_root / "fnpqnn_gateway_mvp"
        if not module_path.exists() or not package_root.exists():
            raise GatewayUnavailable(f"Gateway contract module not found at {module_path}")
        # Import through the package so its reviewed relative imports remain intact.
        import sys

        root = str(self.gateway_root.resolve())
        if root not in sys.path:
            sys.path.insert(0, root)
        try:
            self._module = __import__("fnpqnn_gateway_mvp.algoquest_companion", fromlist=["*"])
        except Exception as exc:  # pragma: no cover - exact import failure is environment-specific
            raise GatewayUnavailable("Gateway contract module could not be loaded") from exc
        return self._module
