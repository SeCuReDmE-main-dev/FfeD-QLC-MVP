"""Bounded native handoffs through the existing private Obsidian pivot CLI."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import uuid
from typing import Protocol, Sequence

from .contracts import utc_now


PIVOT_CLI = Path(r"C:\Users\jeans\.gemini\config\plugins\gemini-memory-systeme\scripts\pivot_cli.py")


class NativeHandoffError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class NativeHandoffEnvelope:
    handoff_id: str
    correlation_id: str
    target: str
    capability: str
    consent_receipt_id: str
    evidence_refs: tuple[str, ...]
    deadline_seconds: int
    status: str = "PLANNED"
    created_at: str = ""

    @classmethod
    def build(
        cls,
        *,
        target: str,
        capability: str,
        consent_receipt_id: str,
        evidence_refs: Sequence[str],
        deadline_seconds: int = 30,
    ) -> "NativeHandoffEnvelope":
        normalized_target = target.strip().lower()
        if normalized_target not in {"codex", "gemini"}:
            raise NativeHandoffError("INVALID_TARGET", "target must be codex or gemini")
        if not capability or len(capability) > 80:
            raise NativeHandoffError("INVALID_CAPABILITY", "capability is required and bounded")
        if not consent_receipt_id or len(consent_receipt_id) > 120:
            raise NativeHandoffError("CONSENT_REQUIRED", "a bounded consent receipt is required")
        refs = tuple(str(item).lower() for item in evidence_refs)
        if not refs or len(refs) > 8 or any(len(item) != 64 or any(char not in "0123456789abcdef" for char in item) for item in refs):
            raise NativeHandoffError("INVALID_EVIDENCE", "one to eight SHA-256 evidence references are required")
        if not 1 <= deadline_seconds <= 120:
            raise NativeHandoffError("INVALID_DEADLINE", "deadline must be between 1 and 120 seconds")
        return cls(
            handoff_id=f"handoff-{uuid.uuid4().hex[:16]}",
            correlation_id=f"corr-{uuid.uuid4().hex[:16]}",
            target=normalized_target,
            capability=capability.strip(),
            consent_receipt_id=consent_receipt_id.strip(),
            evidence_refs=refs,
            deadline_seconds=deadline_seconds,
            created_at=utc_now(),
        )

    def redacted_mapping(self) -> dict[str, object]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        payload["schema"] = "ffed.qlc.native-handoff.v1"
        payload["raw_conversation_included"] = False
        payload["secret_values_exposed"] = False
        payload["sha256"] = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return payload


class NativeHandoffAdapter(Protocol):
    @property
    def ready(self) -> bool: ...

    def dispatch(self, envelope: NativeHandoffEnvelope) -> dict[str, object]: ...


class DisabledNativeHandoffAdapter:
    @property
    def ready(self) -> bool:
        return False

    def dispatch(self, envelope: NativeHandoffEnvelope) -> dict[str, object]:
        del envelope
        raise NativeHandoffError("NATIVE_RUNTIME_UNAVAILABLE", "native Codex/Gemini runtime is unavailable")


class PivotCliHandoffAdapter:
    def __init__(self, cli_path: Path = PIVOT_CLI, *, timeout_seconds: int = 30) -> None:
        self.cli_path = cli_path.resolve()
        self.timeout_seconds = timeout_seconds

    @property
    def ready(self) -> bool:
        return self.cli_path.is_file()

    def dispatch(self, envelope: NativeHandoffEnvelope) -> dict[str, object]:
        if not self.ready:
            raise NativeHandoffError("NATIVE_RUNTIME_UNAVAILABLE", "pivot CLI is unavailable")
        summary = (
            f"FfeD-QLC native handoff {envelope.handoff_id}; capability={envelope.capability}; "
            f"consent_receipt={envelope.consent_receipt_id}; evidence_count={len(envelope.evidence_refs)}."
        )
        command = [
            sys.executable,
            str(self.cli_path),
            "handoff",
            "--from-agent", "jean",
            "--to-agent", envelope.target,
            "--summary", summary,
            "--correlation-id", envelope.correlation_id,
        ]
        for reference in envelope.evidence_refs:
            command.extend(["--action-item", f"Review evidence SHA-256 {reference} without requesting raw private content."])
        try:
            process = subprocess.run(
                command,
                cwd=self.cli_path.parent,
                capture_output=True,
                text=True,
                timeout=min(self.timeout_seconds, envelope.deadline_seconds),
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise NativeHandoffError("NATIVE_HANDOFF_TIMEOUT", "native handoff timed out") from exc
        if process.returncode != 0:
            raise NativeHandoffError("NATIVE_HANDOFF_FAILED", "native handoff runtime rejected the request")
        try:
            receipt = json.loads(process.stdout)
        except json.JSONDecodeError as exc:
            raise NativeHandoffError("INVALID_NATIVE_RECEIPT", "native runtime returned an invalid receipt") from exc
        note = receipt.get("note") if isinstance(receipt, dict) else None
        if not isinstance(note, dict) or note.get("status") != "READY" or not note.get("id") or not note.get("sha256"):
            raise NativeHandoffError("INVALID_NATIVE_RECEIPT", "native handoff receipt is incomplete")
        return envelope.redacted_mapping() | {
            "status": "READY",
            "native_receipt": {
                "note_id": note["id"],
                "sha256": note["sha256"],
                "status": note["status"],
            },
            "acknowledged": False,
        }
