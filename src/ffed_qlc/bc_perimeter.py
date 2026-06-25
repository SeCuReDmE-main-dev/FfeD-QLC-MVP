from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


BC_PERIMETER_RECEIPT_SCHEMA = "ffed.qlc.bouncy_castle_perimeter_receipt.v1"
DEFAULT_BCCTL_TIMEOUT_SECONDS = 8.0

_SAFE_TOKEN_RE = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")
_HEX_DIGEST_RE = re.compile(r"^[a-fA-F0-9]{32,128}$")
_SECRETISH_RE = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|credential|password|passphrase|private[_-]?key|secret|token)"
)
_WINDOWS_PATH_RE = re.compile(r"[A-Za-z]:/[^\s\"']+")


class BcctlError(RuntimeError):
    """Raised when the optional Bouncy Castle perimeter provider cannot complete."""


@dataclass(frozen=True)
class BcctlProvider:
    executable: str | None = None
    timeout_seconds: float = DEFAULT_BCCTL_TIMEOUT_SECONDS

    @classmethod
    def from_environment(cls, timeout_seconds: float = DEFAULT_BCCTL_TIMEOUT_SECONDS) -> "BcctlProvider":
        return cls(executable=_resolve_bcctl_executable(), timeout_seconds=timeout_seconds)

    def status(self) -> dict[str, Any]:
        if not self.executable:
            return {
                "provider_available": False,
                "provider": "BouncyCastle",
                "tool": "bcctl",
                "tool_path_source": _tool_path_source(),
                "error": "bcctl executable is not configured or available on PATH",
            }

        version = self._run(["version"], expect_json=False)
        algorithms = self._run(["list-algorithms"], expect_json=False)
        return {
            "provider_available": True,
            "provider": "BouncyCastle",
            "tool": "bcctl",
            "tool_path_source": _tool_path_source(),
            "version": _sanitize_output_text(version.get("stdout", "")),
            "algorithms": [
                _sanitize_output_text(line)
                for line in str(algorithms.get("stdout", "")).splitlines()
                if line.strip()
            ],
            "raw_payload_embedded": False,
        }

    def sign_digest(self, *, key_id: str, context_digest: str, artifact_digest: str) -> dict[str, Any]:
        _validate_key_id(key_id)
        _validate_hex_digest("context_digest", context_digest)
        _validate_hex_digest("artifact_digest", artifact_digest)
        payload = self._run_json(
            [
                "sign",
                "--key-id",
                key_id,
                "--context-digest",
                context_digest.lower(),
                "--artifact-digest",
                artifact_digest.lower(),
                "--output-format",
                "json",
            ]
        )
        if payload.get("status") != "ok":
            raise BcctlError(_error_from_payload(payload))
        signature_b64 = str(payload.get("signature_b64") or "")
        signature_digest = hashlib.sha256(signature_b64.encode("utf-8")).hexdigest()
        return {
            "status": "ok",
            "operation": "sign",
            "provider": "BouncyCastle",
            "tool": "bcctl",
            "key_id": str(payload.get("key_id") or key_id)[:160],
            "algorithm": str(payload.get("algorithm") or "Ed25519")[:80],
            "context_digest": context_digest.lower(),
            "message_digest": artifact_digest.lower(),
            "signature_digest": signature_digest,
            "signature_b64": signature_b64,
            "raw_payload_embedded": False,
        }

    def verify_digest(
        self,
        *,
        key_id: str,
        context_digest: str,
        message_digest: str,
        signature_digest: str,
    ) -> dict[str, Any]:
        _validate_key_id(key_id)
        _validate_hex_digest("context_digest", context_digest)
        _validate_hex_digest("message_digest", message_digest)
        _validate_hex_digest("signature_digest", signature_digest)
        payload = self._run_json(
            [
                "verify",
                "--key-id",
                key_id,
                "--context-digest",
                context_digest.lower(),
                "--message-digest",
                message_digest.lower(),
                "--signature-digest",
                signature_digest.lower(),
                "--output-format",
                "json",
            ]
        )
        if payload.get("status") != "ok":
            raise BcctlError(_error_from_payload(payload))
        return {
            "status": "ok",
            "operation": "verify",
            "provider": "BouncyCastle",
            "tool": "bcctl",
            "key_id": str(payload.get("key_id") or key_id)[:160],
            "verified": bool(payload.get("verified")),
            "context_digest": context_digest.lower(),
            "message_digest": message_digest.lower(),
            "signature_digest": signature_digest.lower(),
            "raw_payload_embedded": False,
        }

    def _run_json(self, args: Sequence[str]) -> Mapping[str, Any]:
        result = self._run(args, expect_json=True)
        payload = result.get("json")
        if not isinstance(payload, Mapping):
            raise BcctlError("bcctl returned an invalid JSON object")
        return payload

    def _run(self, args: Sequence[str], *, expect_json: bool) -> dict[str, Any]:
        if not self.executable:
            raise BcctlError("bcctl executable is not configured or available on PATH")
        command = [self.executable, *args]
        try:
            completed = subprocess.run(
                command,
                shell=False,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise BcctlError("bcctl command timed out") from exc
        except OSError as exc:
            raise BcctlError(_sanitize_output_text(str(exc))) from exc

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        if completed.returncode != 0:
            detail = _payload_error_detail(stdout) or _payload_error_detail(stderr) or "bcctl command failed"
            raise BcctlError(detail)
        if not expect_json:
            return {"stdout": stdout}
        try:
            return {"json": json.loads(stdout)}
        except json.JSONDecodeError as exc:
            raise BcctlError("bcctl returned invalid JSON") from exc


def build_bouncy_castle_perimeter_receipt(
    *,
    key_id: str,
    context_digest: str,
    artifact_digest: str,
    provider: BcctlProvider | None = None,
) -> dict[str, Any]:
    signer = provider or BcctlProvider.from_environment()
    signature = signer.sign_digest(
        key_id=key_id,
        context_digest=context_digest,
        artifact_digest=artifact_digest,
    )
    return {
        "schema": BC_PERIMETER_RECEIPT_SCHEMA,
        "provider": "BouncyCastle",
        "tool": "bcctl",
        "algorithm": signature["algorithm"],
        "operation": "sign",
        "key_id": signature["key_id"],
        "context_digest": signature["context_digest"],
        "artifact_digest": signature["message_digest"],
        "signature_digest": signature["signature_digest"],
        "signature_b64": signature["signature_b64"],
        "raw_payload_embedded": False,
        "claim_boundary": "bouncy_castle_perimeter_signature_over_metadata_digests_not_raw_payload_or_production_certification",
    }


def _resolve_bcctl_executable() -> str | None:
    configured = os.environ.get("FFED_BCCTL_PATH")
    if configured:
        path = Path(configured)
        return str(path) if path.is_file() else None
    return shutil.which("bcctl")


def _tool_path_source() -> str:
    return "FFED_BCCTL_PATH" if os.environ.get("FFED_BCCTL_PATH") else "PATH"


def _validate_key_id(value: str) -> None:
    if not _SAFE_TOKEN_RE.fullmatch(value) or _SECRETISH_RE.search(value):
        raise ValueError("key_id must be a short public-safe token")


def _validate_hex_digest(name: str, value: str) -> None:
    if not _HEX_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public hex digest")


def _payload_error_detail(output: str) -> str | None:
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, Mapping):
        return None
    return _error_from_payload(payload)


def _error_from_payload(payload: Mapping[str, Any]) -> str:
    error = _sanitize_output_text(str(payload.get("error") or "bcctl_error"))
    detail = _sanitize_output_text(str(payload.get("detail") or ""))
    return f"{error}: {detail}" if detail else error


def _sanitize_output_text(value: str) -> str:
    compact = " ".join(value.replace("\\", "/").split())
    compact = _WINDOWS_PATH_RE.sub("[path]", compact)
    compact = _SECRETISH_RE.sub("[redacted]", compact)
    return compact[:240]
