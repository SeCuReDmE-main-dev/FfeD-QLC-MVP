import hashlib

import pytest

from ffed_qlc import QLCTransformError, inspect_container, pack_bytes, quasicrystal_coordinates, unpack_bytes, verify_container
from ffed_qlc.structural_transform import HEADER_LENGTH_BYTES, MAGIC, MAX_HEADER_BYTES, MAX_PLAINTEXT_BYTES


def test_pack_unpack_round_trip() -> None:
    plaintext = b"FfeD QLC structural transform payload" * 4

    container = pack_bytes(plaintext, "correct horse battery staple")

    assert container != plaintext
    assert unpack_bytes(container, "correct horse battery staple") == plaintext


def test_unpack_rejects_wrong_passphrase() -> None:
    container = pack_bytes(b"secret", "right-passphrase")

    with pytest.raises(QLCTransformError):
        unpack_bytes(container, "wrong-passphrase")


def test_inspect_container_rejects_malformed_non_utf8_header() -> None:
    header = b"\xff\xff"
    container = MAGIC + len(header).to_bytes(HEADER_LENGTH_BYTES, "big") + header

    with pytest.raises(QLCTransformError, match="invalid QLC container header JSON"):
        inspect_container(container)


def test_inspect_container_rejects_non_object_header() -> None:
    header = b"[]"
    container = MAGIC + len(header).to_bytes(HEADER_LENGTH_BYTES, "big") + header

    with pytest.raises(QLCTransformError, match="QLC header must be a JSON object"):
        inspect_container(container)


def test_inspect_container_returns_public_safe_manifest() -> None:
    container = pack_bytes(b"secret", "passphrase")

    manifest = inspect_container(container)

    assert manifest["magic"] == "FQLC1"
    assert manifest["container_size_bytes"] == len(container)
    assert manifest["plaintext_length"] == 6
    assert manifest["raw_payload_exposed"] is False
    assert manifest["qlc_manifest"]["schema"] == "ffed.qlc.crypte_key_manifest.v1"
    assert manifest["qlc_manifest"]["chunk_policy"]["planned_key_schedule"] == "granular_chunk_key_schedule_v1"
    schedule = manifest["qlc_manifest"]["chunk_key_schedule"]
    assert schedule["schema"] == "ffed.qlc.granular_chunk_key_schedule.v1"
    assert schedule["chunk_count"] == 1
    assert schedule["key_material_exposed"] is False
    assert "subkey_fingerprint" in schedule["chunks"][0]
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


def test_fqlc1_rejects_unbounded_header_and_plaintext() -> None:
    header_length = (MAX_HEADER_BYTES + 1).to_bytes(HEADER_LENGTH_BYTES, "big")
    with pytest.raises(QLCTransformError, match="header length"):
        inspect_container(MAGIC + header_length)

    with pytest.raises(ValueError, match="fixture budget"):
        pack_bytes(b"x" * (MAX_PLAINTEXT_BYTES + 1), "passphrase")


def test_fqlc1_rejects_hostile_kdf_profile_before_derivation() -> None:
    container = pack_bytes(b"safe", "passphrase")
    offset = len(MAGIC)
    header_length = int.from_bytes(container[offset : offset + HEADER_LENGTH_BYTES], "big")
    start = offset + HEADER_LENGTH_BYTES
    import json

    header = json.loads(container[start : start + header_length])
    header["kdf_n"] = 2**30
    encoded = json.dumps(header, sort_keys=True, separators=(",", ":")).encode()
    hostile = MAGIC + len(encoded).to_bytes(HEADER_LENGTH_BYTES, "big") + encoded + container[start + header_length :]

    with pytest.raises(QLCTransformError, match="scrypt profile"):
        inspect_container(hostile)
