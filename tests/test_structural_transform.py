import hashlib

import pytest

from ffed_qlc import QLCTransformError, inspect_container, pack_bytes, quasicrystal_coordinates, unpack_bytes, verify_container


def test_pack_unpack_round_trip() -> None:
    plaintext = b"FfeD QLC structural transform payload" * 4

    container = pack_bytes(plaintext, "correct horse battery staple")

    assert container != plaintext
    assert unpack_bytes(container, "correct horse battery staple") == plaintext


def test_unpack_rejects_wrong_passphrase() -> None:
    container = pack_bytes(b"secret", "right-passphrase")

    with pytest.raises(QLCTransformError):
        unpack_bytes(container, "wrong-passphrase")


def test_inspect_container_returns_public_safe_manifest() -> None:
    container = pack_bytes(b"secret", "passphrase")

    manifest = inspect_container(container)

    assert manifest["magic"] == "FQLC1"
    assert manifest["container_size_bytes"] == len(container)
    assert manifest["plaintext_length"] == 6
    assert manifest["raw_payload_exposed"] is False
    assert manifest["qlc_manifest"]["schema"] == "ffed.qlc.crypte_key_manifest.v1"
    assert manifest["qlc_manifest"]["chunk_policy"]["planned_key_schedule"] == "hkdf_subkeys_per_chunk_v2"
    assert "secret" not in str(manifest)


def test_verify_container_authenticates_and_fingerprints_plaintext() -> None:
    plaintext = b"secret"
    container = pack_bytes(plaintext, "passphrase")

    record = verify_container(container, "passphrase")

    assert record["valid"] is True
    assert record["plaintext_sha256"] == hashlib.sha256(plaintext).hexdigest()
    assert record["plaintext_bytes_revealed"] is False
    assert record["qlc_manifest"]["source_sha256"] == hashlib.sha256(plaintext).hexdigest()


def test_quasicrystal_coordinates_are_deterministic() -> None:
    first = quasicrystal_coordinates(16, "demo")
    second = quasicrystal_coordinates(16, "demo")

    assert first == second
    assert sorted(source_index for _, source_index, _ in first) == list(range(16))
