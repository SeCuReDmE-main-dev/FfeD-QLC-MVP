"""Non-secret runtime configuration injected through governed Settings."""

from __future__ import annotations

from dataclasses import dataclass
import os
from urllib.parse import urlsplit, urlunsplit

from .cpai_yolo import DEFAULT_CPAI_URL


def normalize_base_url(value: str) -> str:
    parsed = urlsplit(str(value).strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("CodeProject.AI URL must be an absolute HTTP(S) base URL without credentials")
    if parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
        raise ValueError("CodeProject.AI URL must not include a path, query, or fragment")
    host = parsed.hostname.lower()
    port = f":{parsed.port}" if parsed.port is not None else ""
    return urlunsplit((parsed.scheme.lower(), host + port, "", "", ""))


@dataclass(frozen=True)
class RuntimeConfig:
    public_stateful_enabled: bool = False
    fqlc2_enabled: bool = True
    native_handoffs_enabled: bool = False
    fqlc2_chunk_bytes: int = 1_048_576
    fqlc2_max_recipients: int = 32
    runtime: str = "local"
    cpai_allowed_base_urls: tuple[str, ...] = (DEFAULT_CPAI_URL,)

    @classmethod
    def from_environment(cls) -> "RuntimeConfig":
        raw_urls = os.getenv("FFED_QLC_CPAI_ALLOWED_BASE_URLS", DEFAULT_CPAI_URL)
        urls = tuple(dict.fromkeys(normalize_base_url(item) for item in raw_urls.split(",") if item.strip()))
        if not urls:
            urls = (normalize_base_url(DEFAULT_CPAI_URL),)
        return cls(
            public_stateful_enabled=_boolean("FFED_QLC_PUBLIC_STATEFUL_ENABLED", False),
            fqlc2_enabled=_boolean("FFED_QLC_FQLC2_ENABLED", True),
            native_handoffs_enabled=_boolean("FFED_QLC_NATIVE_HANDOFFS_ENABLED", False),
            fqlc2_chunk_bytes=_bounded_integer("FFED_QLC_FQLC2_CHUNK_BYTES", 1_048_576, 1, 1_048_576),
            fqlc2_max_recipients=_bounded_integer("FFED_QLC_FQLC2_MAX_RECIPIENTS", 32, 1, 32),
            runtime=os.getenv("FFED_QLC_RUNTIME", "local").strip().lower() or "local",
            cpai_allowed_base_urls=urls,
        )

    def require_cpai_url(self, value: str) -> str:
        normalized = normalize_base_url(value)
        allowed = {normalize_base_url(item) for item in self.cpai_allowed_base_urls}
        if normalized not in allowed:
            raise ValueError("CodeProject.AI endpoint is not in the Settings-governed allowlist")
        return normalized

    def capabilities(self, *, identity_ready: bool, native_runtime_ready: bool) -> dict[str, object]:
        return {
            "schema": "ffed.qlc.capabilities.v1",
            "phase": "pre-alpha",
            "development": "active-public-development",
            "runtime": self.runtime,
            "public_stateful_enabled": self.public_stateful_enabled and identity_ready,
            "identity_adapter_ready": identity_ready,
            "fqlc2_demo_enabled": self.fqlc2_enabled,
            "fqlc2_chunk_bytes": self.fqlc2_chunk_bytes,
            "fqlc2_max_recipients": self.fqlc2_max_recipients,
            "native_handoff_runtime_ready": self.native_handoffs_enabled and native_runtime_ready,
            "cpai_endpoint_count": len(self.cpai_allowed_base_urls),
            "secret_values_exposed": False,
        }


def _boolean(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _bounded_integer(name: str, default: int, minimum: int, maximum: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        parsed = int(value, 10)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if not minimum <= parsed <= maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")
    return parsed
