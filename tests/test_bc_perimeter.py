from __future__ import annotations

import hashlib
import json
import subprocess

import pytest

from ffed_qlc.bc_perimeter import BcctlError, BcctlProvider


CONTEXT_DIGEST = "a" * 64
ARTIFACT_DIGEST = "b" * 64
SIGNATURE_DIGEST = "c" * 64


def test_bcctl_sign_uses_no_shell_and_public_digest_arguments(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    def fake_run(command, **kwargs):
        calls.append({"command": command, **kwargs})
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {
                    "status": "ok",
                    "operation": "sign",
                    "key_id": "perimeter-key",
                    "algorithm": "Ed25519",
                    "signature_b64": "signed-digest",
                }
            ),
            stderr="",
        )

    monkeypatch.setattr("ffed_qlc.bc_perimeter.subprocess.run", fake_run)
    provider = BcctlProvider(executable="bcctl-test")

    payload = provider.sign_digest(
        key_id="perimeter-key",
        context_digest=CONTEXT_DIGEST,
        artifact_digest=ARTIFACT_DIGEST,
    )

    assert calls[0]["shell"] is False
    assert calls[0]["command"] == [
        "bcctl-test",
        "sign",
        "--key-id",
        "perimeter-key",
        "--context-digest",
        CONTEXT_DIGEST,
        "--artifact-digest",
        ARTIFACT_DIGEST,
        "--output-format",
        "json",
    ]
    assert payload["signature_digest"] == hashlib.sha256(b"signed-digest").hexdigest()
    assert payload["raw_payload_embedded"] is False


def test_bcctl_verify_reports_false_without_treating_it_as_error(monkeypatch) -> None:
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {
                    "status": "ok",
                    "operation": "verify",
                    "key_id": "perimeter-key",
                    "verified": False,
                }
            ),
            stderr="",
        )

    monkeypatch.setattr("ffed_qlc.bc_perimeter.subprocess.run", fake_run)
    provider = BcctlProvider(executable="bcctl-test")

    payload = provider.verify_digest(
        key_id="perimeter-key",
        context_digest=CONTEXT_DIGEST,
        message_digest=ARTIFACT_DIGEST,
        signature_digest=SIGNATURE_DIGEST,
    )

    assert payload["verified"] is False
    assert payload["message_digest"] == ARTIFACT_DIGEST


def test_bcctl_status_does_not_echo_local_tool_path(monkeypatch) -> None:
    def fake_run(command, **kwargs):
        if command[1] == "version":
            return subprocess.CompletedProcess(command, 0, stdout="bcctl 2.6.2-ffed.1 (BouncyCastle)\n", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="Ed25519\nChaCha20-Poly1305\n", stderr="")

    monkeypatch.setenv("FFED_BCCTL_PATH", r".\\bcctl\\bcctl.exe")
    monkeypatch.setattr("ffed_qlc.bc_perimeter.subprocess.run", fake_run)
    provider = BcctlProvider(executable=r".\\bcctl\\bcctl.exe")

    payload = provider.status()

    assert payload["provider_available"] is True
    assert payload["tool_path_source"] == "FFED_BCCTL_PATH"
    assert "C:" not in json.dumps(payload)
    assert "Ed25519" in payload["algorithms"]


def test_bcctl_unavailable_status_is_non_throwing(monkeypatch) -> None:
    monkeypatch.delenv("FFED_BCCTL_PATH", raising=False)
    monkeypatch.setattr("ffed_qlc.bc_perimeter.shutil.which", lambda name: None)

    payload = BcctlProvider.from_environment().status()

    assert payload["provider_available"] is False
    assert payload["tool_path_source"] == "PATH"


def test_bcctl_rejects_invalid_digest_and_secretish_key_id() -> None:
    provider = BcctlProvider(executable="bcctl-test")

    with pytest.raises(ValueError, match="public hex digest"):
        provider.sign_digest(key_id="perimeter-key", context_digest="not hex", artifact_digest=ARTIFACT_DIGEST)

    with pytest.raises(ValueError, match="public-safe token"):
        provider.sign_digest(key_id="api-key", context_digest=CONTEXT_DIGEST, artifact_digest=ARTIFACT_DIGEST)


def test_bcctl_timeout_and_invalid_json_are_sanitized(monkeypatch) -> None:
    def timeout_run(command, **kwargs):
        raise subprocess.TimeoutExpired(command, timeout=1)

    monkeypatch.setattr("ffed_qlc.bc_perimeter.subprocess.run", timeout_run)
    provider = BcctlProvider(executable="bcctl-test", timeout_seconds=1)
    with pytest.raises(BcctlError, match="timed out"):
        provider.sign_digest(key_id="perimeter-key", context_digest=CONTEXT_DIGEST, artifact_digest=ARTIFACT_DIGEST)

    def invalid_json_run(command, **kwargs):
        return subprocess.CompletedProcess(command, 0, stdout="not json", stderr="")

    monkeypatch.setattr("ffed_qlc.bc_perimeter.subprocess.run", invalid_json_run)
    with pytest.raises(BcctlError, match="invalid JSON"):
        provider.sign_digest(key_id="perimeter-key", context_digest=CONTEXT_DIGEST, artifact_digest=ARTIFACT_DIGEST)


def test_bcctl_nonzero_error_redacts_secretish_detail(monkeypatch) -> None:
    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            1,
            stdout=json.dumps({"status": "error", "error": "bad_token", "detail": "API_KEY leaked"}),
            stderr="",
        )

    monkeypatch.setattr("ffed_qlc.bc_perimeter.subprocess.run", fake_run)
    provider = BcctlProvider(executable="bcctl-test")

    with pytest.raises(BcctlError) as exc:
        provider.sign_digest(key_id="perimeter-key", context_digest=CONTEXT_DIGEST, artifact_digest=ARTIFACT_DIGEST)

    assert "API_KEY" not in str(exc.value)
    assert "[redacted]" in str(exc.value)
