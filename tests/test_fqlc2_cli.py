from __future__ import annotations

import json
from pathlib import Path

from ffed_qlc.cli import main


def test_fqlc2_cli_keygen_pack_inspect_verify_unpack_and_rotate(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FQLC2_TEST_PASSPHRASE", "fixture-only-passphrase-123")
    source = tmp_path / "source.txt"
    source.write_text("synthetic FQLC2 CLI fixture", encoding="utf-8")
    first_private = tmp_path / "first-private.pem"
    first_public = tmp_path / "first-public.pem"
    second_private = tmp_path / "second-private.pem"
    second_public = tmp_path / "second-public.pem"

    for private_key, public_key in ((first_private, first_public), (second_private, second_public)):
        assert main([
            "fqlc2-keygen",
            "--private-output", str(private_key),
            "--public-output", str(public_key),
            "--passphrase-env", "FQLC2_TEST_PASSPHRASE",
        ]) == 0
        assert b"ENCRYPTED PRIVATE KEY" in private_key.read_bytes()

    container = tmp_path / "source.fqlc2"
    assert main([
        "fqlc2-pack", "--input", str(source), "--output", str(container),
        "--recipient-public-key", str(first_public),
    ]) == 0

    manifest = tmp_path / "manifest.json"
    assert main(["fqlc2-inspect", "--input", str(container), "--output", str(manifest)]) == 0
    assert json.loads(manifest.read_text(encoding="utf-8"))["format"] == "FQLC2"

    verification = tmp_path / "verification.json"
    assert main([
        "fqlc2-verify", "--input", str(container),
        "--recipient-private-key", str(first_private),
        "--passphrase-env", "FQLC2_TEST_PASSPHRASE",
        "--output", str(verification),
    ]) == 0
    assert json.loads(verification.read_text(encoding="utf-8"))["signature_verified"] is False

    recovered = tmp_path / "recovered.txt"
    assert main([
        "fqlc2-unpack", "--input", str(container), "--output", str(recovered),
        "--recipient-private-key", str(first_private),
        "--passphrase-env", "FQLC2_TEST_PASSPHRASE",
    ]) == 0
    assert recovered.read_bytes() == source.read_bytes()

    rotated = tmp_path / "rotated.fqlc2"
    assert main([
        "fqlc2-rotate", "--input", str(container), "--output", str(rotated),
        "--current-private-key", str(first_private),
        "--current-passphrase-env", "FQLC2_TEST_PASSPHRASE",
        "--recipient-public-key", str(second_public),
    ]) == 0
    rotated_recovered = tmp_path / "rotated-recovered.txt"
    assert main([
        "fqlc2-unpack", "--input", str(rotated), "--output", str(rotated_recovered),
        "--recipient-private-key", str(second_private),
        "--passphrase-env", "FQLC2_TEST_PASSPHRASE",
    ]) == 0
    assert rotated_recovered.read_bytes() == source.read_bytes()
