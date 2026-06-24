from __future__ import annotations

import base64
import hashlib
import json
import os
from dataclasses import dataclass
from hashlib import blake2b

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


MAGIC = b"FQLC1\n"
HEADER_LENGTH_BYTES = 4
GOLDEN_64 = 0x9E3779B97F4A7C15
GOLDEN_64_ALT = 0xD1B54A32D192ED03
MASK_64 = (1 << 64) - 1
MID_64 = 1 << 63


class QLCTransformError(ValueError):
    """Raised when a QLC container cannot be parsed or authenticated."""


@dataclass(frozen=True)
class QLCTransformConfig:
    """Public-safe parameters for the reversible structural transform."""

    kdf_n: int = 2**14
    kdf_r: int = 8
    kdf_p: int = 1


def pack_bytes(
    plaintext: bytes,
    passphrase: str,
    *,
    associated_data: bytes = b"",
    config: QLCTransformConfig | None = None,
) -> bytes:
    """Pack bytes into an authenticated QLC-style container.

    The quasicrystal-inspired layer is a deterministic structural permutation.
    Confidentiality and integrity come from standard ChaCha20-Poly1305 with a
    scrypt-derived key.
    """

    if not passphrase:
        raise ValueError("passphrase must not be empty")

    active_config = config or QLCTransformConfig()
    salt = os.urandom(16)
    nonce = os.urandom(12)
    key = _derive_key(passphrase, salt, active_config)
    order = _quasicrystal_order(len(plaintext), key)
    transformed = _permute(plaintext, order)

    header = {
        "version": 1,
        "transform": "phi_cut_project_permutation_v1",
        "cipher": "ChaCha20-Poly1305",
        "kdf": "scrypt",
        "kdf_n": active_config.kdf_n,
        "kdf_r": active_config.kdf_r,
        "kdf_p": active_config.kdf_p,
        "salt": _b64(salt),
        "nonce": _b64(nonce),
        "plaintext_length": len(plaintext),
    }
    header_bytes = _encode_header(header)
    aad = _container_aad(header_bytes, associated_data)
    ciphertext = ChaCha20Poly1305(key).encrypt(nonce, transformed, aad)
    return MAGIC + len(header_bytes).to_bytes(HEADER_LENGTH_BYTES, "big") + header_bytes + ciphertext


def unpack_bytes(
    container: bytes,
    passphrase: str,
    *,
    associated_data: bytes = b"",
) -> bytes:
    """Authenticate and unpack a QLC-style container."""

    if not passphrase:
        raise ValueError("passphrase must not be empty")

    header, header_bytes, ciphertext = _split_container(container)
    config = QLCTransformConfig(
        kdf_n=int(header["kdf_n"]),
        kdf_r=int(header["kdf_r"]),
        kdf_p=int(header["kdf_p"]),
    )
    salt = base64.b64decode(header["salt"])
    nonce = base64.b64decode(header["nonce"])
    key = _derive_key(passphrase, salt, config)
    aad = _container_aad(header_bytes, associated_data)

    try:
        transformed = ChaCha20Poly1305(key).decrypt(nonce, ciphertext, aad)
    except InvalidTag as exc:
        raise QLCTransformError("container authentication failed") from exc

    expected_length = int(header["plaintext_length"])
    if len(transformed) != expected_length:
        raise QLCTransformError("container length does not match header")

    order = _quasicrystal_order(expected_length, key)
    return _unpermute(transformed, order)


def inspect_container(container: bytes) -> dict[str, object]:
    """Return non-secret metadata from a QLC container.

    This is safe for simulator/audit handoff: it exposes fingerprints and public
    transform parameters, never plaintext or key material.
    """

    header, _header_bytes, ciphertext = _split_container(container)
    return {
        "magic": MAGIC.decode("ascii").strip(),
        "container_size_bytes": len(container),
        "container_sha256": hashlib.sha256(container).hexdigest(),
        "ciphertext_sha256": hashlib.sha256(ciphertext).hexdigest(),
        "plaintext_length": int(header["plaintext_length"]),
        "version": int(header["version"]),
        "transform": str(header["transform"]),
        "cipher": str(header["cipher"]),
        "kdf": str(header["kdf"]),
        "kdf_n": int(header["kdf_n"]),
        "kdf_r": int(header["kdf_r"]),
        "kdf_p": int(header["kdf_p"]),
        "raw_payload_exposed": False,
    }


def verify_container(
    container: bytes,
    passphrase: str,
    *,
    associated_data: bytes = b"",
) -> dict[str, object]:
    """Authenticate a container and return a public-safe verification record."""

    plaintext = unpack_bytes(container, passphrase, associated_data=associated_data)
    record = inspect_container(container)
    record.update(
        {
            "valid": True,
            "plaintext_sha256": hashlib.sha256(plaintext).hexdigest(),
            "plaintext_bytes_revealed": False,
        }
    )
    return record


def quasicrystal_coordinates(length: int, passphrase: str, *, salt: bytes | None = None) -> list[tuple[int, int, int]]:
    """Return deterministic public coordinates for demos and tests.

    These coordinates are not secrets and should not be used as a key. They are
    a small observable view of the same cut-and-project ordering idea used by
    the transform.
    """

    if length < 0:
        raise ValueError("length must be non-negative")
    demo_salt = salt if salt is not None else b"public-demo-salt"
    key = _derive_key(passphrase or "demo", demo_salt, QLCTransformConfig())
    order = _quasicrystal_order(length, key)
    return [(rank, source_index, _window_distance(source_index, key)) for rank, source_index in enumerate(order)]


def _derive_key(passphrase: str, salt: bytes, config: QLCTransformConfig) -> bytes:
    kdf = Scrypt(salt=salt, length=32, n=config.kdf_n, r=config.kdf_r, p=config.kdf_p)
    return kdf.derive(passphrase.encode("utf-8"))


def _quasicrystal_order(length: int, key: bytes) -> list[int]:
    if length < 0:
        raise ValueError("length must be non-negative")
    return sorted(range(length), key=lambda index: _rank_tuple(index, key))


def _rank_tuple(index: int, key: bytes) -> tuple[int, int, int, int]:
    seed = _seed64(key, b"rank")
    seed_alt = _seed64(key, b"rank-alt")
    a = ((index + 1) * GOLDEN_64 + seed) & MASK_64
    b = ((index + 1) * GOLDEN_64_ALT + seed_alt) & MASK_64
    window_distance = abs(a - MID_64) + abs(b - MID_64)
    parallel_projection = (a ^ _rotate_left_64(b, 17) ^ ((index + 1) * GOLDEN_64)) & MASK_64
    return (window_distance, parallel_projection, a, index)


def _window_distance(index: int, key: bytes) -> int:
    return _rank_tuple(index, key)[0]


def _seed64(key: bytes, label: bytes) -> int:
    digest = blake2b(label, key=key, digest_size=8).digest()
    return int.from_bytes(digest, "big")


def _rotate_left_64(value: int, shift: int) -> int:
    return ((value << shift) | (value >> (64 - shift))) & MASK_64


def _permute(data: bytes, order: list[int]) -> bytes:
    return bytes(data[index] for index in order)


def _unpermute(data: bytes, order: list[int]) -> bytes:
    output = bytearray(len(data))
    for transformed_index, original_index in enumerate(order):
        output[original_index] = data[transformed_index]
    return bytes(output)


def _encode_header(header: dict[str, object]) -> bytes:
    return json.dumps(header, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _split_container(container: bytes) -> tuple[dict[str, object], bytes, bytes]:
    if not container.startswith(MAGIC):
        raise QLCTransformError("invalid QLC container magic")
    offset = len(MAGIC)
    if len(container) < offset + HEADER_LENGTH_BYTES:
        raise QLCTransformError("truncated QLC container header")
    header_length = int.from_bytes(container[offset : offset + HEADER_LENGTH_BYTES], "big")
    header_start = offset + HEADER_LENGTH_BYTES
    header_end = header_start + header_length
    if len(container) < header_end:
        raise QLCTransformError("truncated QLC container body")
    header_bytes = container[header_start:header_end]
    try:
        header = json.loads(header_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise QLCTransformError("invalid QLC container header JSON") from exc
    _validate_header(header)
    return header, header_bytes, container[header_end:]


def _validate_header(header: dict[str, object]) -> None:
    required = {
        "version",
        "transform",
        "cipher",
        "kdf",
        "kdf_n",
        "kdf_r",
        "kdf_p",
        "salt",
        "nonce",
        "plaintext_length",
    }
    missing = required.difference(header)
    if missing:
        raise QLCTransformError(f"missing QLC header fields: {', '.join(sorted(missing))}")
    if header["version"] != 1:
        raise QLCTransformError("unsupported QLC container version")
    if header["transform"] != "phi_cut_project_permutation_v1":
        raise QLCTransformError("unsupported QLC transform")
    if header["cipher"] != "ChaCha20-Poly1305" or header["kdf"] != "scrypt":
        raise QLCTransformError("unsupported QLC cryptographic profile")


def _container_aad(header_bytes: bytes, associated_data: bytes) -> bytes:
    return MAGIC + header_bytes + associated_data


def _b64(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")
