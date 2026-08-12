"""Experimental multi-recipient streaming FQLC2 container.

FQLC2 is deliberately separate from the passphrase-based FQLC1 format.  It
uses RFC 9180 HPKE only to wrap a random content-encryption key and uses an
independently derived ChaCha20-Poly1305 key for bounded streaming frames.
The geometry context is public authenticated context, never key material.
"""

from __future__ import annotations

import hashlib
import io
import os
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Iterable, Mapping, Sequence

import cbor2
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from pyhpke import AEADId, CipherSuite, KDFId, KEMId, KEMKey

from .geometry_trace import DEFAULT_ROOT, build_apollonian_trace


MAGIC = b"FQLC2\x00"
FORMAT_VERSION = 2
DEFAULT_CHUNK_BYTES = 1_048_576
MAX_CHUNK_BYTES = 1_048_576
MAX_HEADER_BYTES = 65_536
MAX_RECIPIENTS = 32
MAX_CHUNKS = 4096
MAX_BYTES_HELPER = 16 * 1024 * 1024
SUITE_NAME = "DHKEM_X25519_HKDF_SHA256/HKDF_SHA256/CHACHA20_POLY1305"

_HEADER_LENGTH = struct.Struct(">I")
_FRAME_HEADER = struct.Struct(">IBI")  # index, final flag, ciphertext length
_SIGNATURE_LENGTH = struct.Struct(">H")


class FQLC2Error(ValueError):
    """Raised when an FQLC2 container or operation violates its contract."""


@dataclass(frozen=True)
class FQLC2Limits:
    chunk_bytes: int = DEFAULT_CHUNK_BYTES
    max_recipients: int = MAX_RECIPIENTS
    max_chunks: int = MAX_CHUNKS

    def validate(self) -> None:
        if not 1 <= self.chunk_bytes <= MAX_CHUNK_BYTES:
            raise FQLC2Error("chunk_bytes is outside the supported range")
        if not 1 <= self.max_recipients <= MAX_RECIPIENTS:
            raise FQLC2Error("max_recipients is outside the supported range")
        if not 1 <= self.max_chunks <= MAX_CHUNKS:
            raise FQLC2Error("max_chunks is outside the supported range")


def generate_recipient_key_pair(passphrase: bytes) -> tuple[bytes, bytes]:
    """Return encrypted private PEM and public PEM without exposing raw keys."""

    if len(passphrase) < 12:
        raise FQLC2Error("private-key passphrase must contain at least 12 bytes")
    private_key = X25519PrivateKey.generate()
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(passphrase),
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def generate_signing_key_pair(passphrase: bytes) -> tuple[bytes, bytes]:
    if len(passphrase) < 12:
        raise FQLC2Error("private-key passphrase must contain at least 12 bytes")
    private_key = Ed25519PrivateKey.generate()
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(passphrase),
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def load_recipient_public_key(data: bytes) -> X25519PublicKey:
    try:
        key = serialization.load_pem_public_key(data)
    except (TypeError, ValueError) as exc:
        raise FQLC2Error("invalid recipient public key") from exc
    if not isinstance(key, X25519PublicKey):
        raise FQLC2Error("recipient key must be X25519")
    return key


def load_recipient_private_key(data: bytes, passphrase: bytes) -> X25519PrivateKey:
    try:
        key = serialization.load_pem_private_key(data, password=passphrase)
    except (TypeError, ValueError) as exc:
        raise FQLC2Error("invalid recipient private key or passphrase") from exc
    if not isinstance(key, X25519PrivateKey):
        raise FQLC2Error("recipient key must be X25519")
    return key


def load_signing_private_key(data: bytes, passphrase: bytes) -> Ed25519PrivateKey:
    try:
        key = serialization.load_pem_private_key(data, password=passphrase)
    except (TypeError, ValueError) as exc:
        raise FQLC2Error("invalid signing private key or passphrase") from exc
    if not isinstance(key, Ed25519PrivateKey):
        raise FQLC2Error("signing key must be Ed25519")
    return key


def pack_stream(
    source: BinaryIO,
    destination: BinaryIO,
    recipients: Sequence[X25519PublicKey],
    *,
    geometry_depth: int = 2,
    limits: FQLC2Limits = FQLC2Limits(),
    signing_key: Ed25519PrivateKey | None = None,
) -> dict[str, Any]:
    """Encrypt one stream for one to 32 recipients."""

    limits.validate()
    if not recipients or len(recipients) > limits.max_recipients:
        raise FQLC2Error("recipient count is outside the configured bound")
    if len({_public_bytes(key) for key in recipients}) != len(recipients):
        raise FQLC2Error("duplicate recipients are not allowed")

    public_context = _geometry_context(geometry_depth)
    context_bytes = _canonical_cbor(public_context)
    context_hash = hashlib.sha256(context_bytes).digest()
    cek = os.urandom(32)
    stanzas = [_wrap_cek(recipient, cek, context_hash) for recipient in recipients]
    header: dict[str, Any] = {
        "version": FORMAT_VERSION,
        "suite": SUITE_NAME,
        "chunk_bytes": limits.chunk_bytes,
        "nonce_prefix": os.urandom(8),
        "context": public_context,
        "stanzas": stanzas,
        "signed": signing_key is not None,
    }
    if signing_key is not None:
        header["signer_public_key"] = signing_key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
    header_bytes = _canonical_cbor(header)
    if len(header_bytes) > MAX_HEADER_BYTES:
        raise FQLC2Error("canonical header exceeds the size bound")
    header_hash = hashlib.sha256(header_bytes).digest()
    stream_key = _derive_stream_key(cek, header_hash)
    aead = ChaCha20Poly1305(stream_key)
    prefix = MAGIC + _HEADER_LENGTH.pack(len(header_bytes)) + header_bytes
    destination.write(prefix)
    signed_digest = hashlib.sha256(prefix)

    current = source.read(limits.chunk_bytes)
    if current is None:
        current = b""
    index = 0
    total_plaintext = 0
    while True:
        if not isinstance(current, bytes):
            current = bytes(current)
        following = source.read(limits.chunk_bytes)
        if following is None:
            following = b""
        final = not following
        if index >= limits.max_chunks:
            raise FQLC2Error("stream exceeds the configured chunk bound")
        nonce = header["nonce_prefix"] + index.to_bytes(4, "big")
        aad = _frame_aad(header_hash, index, final, len(current))
        ciphertext = aead.encrypt(nonce, current, aad)
        frame_header = _FRAME_HEADER.pack(index, int(final), len(ciphertext))
        destination.write(frame_header)
        destination.write(ciphertext)
        signed_digest.update(frame_header)
        signed_digest.update(ciphertext)
        total_plaintext += len(current)
        index += 1
        if final:
            break
        current = following

    if signing_key is None:
        destination.write(b"\x00")
    else:
        signature = signing_key.sign(signed_digest.digest())
        destination.write(b"\x01" + _SIGNATURE_LENGTH.pack(len(signature)) + signature)
    return {
        "schema": "ffed.qlc.fqlc2.pack-receipt.v1",
        "format": "FQLC2",
        "recipient_count": len(recipients),
        "chunk_count": index,
        "plaintext_bytes": total_plaintext,
        "header_sha256": header_hash.hex(),
        "signed": signing_key is not None,
        "geometry_is_key_material": False,
    }


def unpack_stream(
    source: BinaryIO,
    destination: BinaryIO,
    recipient_key: X25519PrivateKey,
    *,
    limits: FQLC2Limits = FQLC2Limits(),
    require_signature: bool = False,
) -> dict[str, Any]:
    """Authenticate and decrypt one stream to a caller-controlled destination."""

    parsed = _read_header(source, limits)
    header, header_bytes, prefix = parsed
    header_hash = hashlib.sha256(header_bytes).digest()
    cek = _unwrap_cek(header, recipient_key, hashlib.sha256(_canonical_cbor(header["context"])).digest())
    aead = ChaCha20Poly1305(_derive_stream_key(cek, header_hash))
    signed_digest = hashlib.sha256(prefix)
    chunks = 0
    total_plaintext = 0
    saw_final = False
    while not saw_final:
        frame_header = _read_exact(source, _FRAME_HEADER.size, "truncated frame header")
        index, final_flag, ciphertext_length = _FRAME_HEADER.unpack(frame_header)
        if index != chunks or final_flag not in (0, 1):
            raise FQLC2Error("frame sequence is invalid")
        if ciphertext_length < 16 or ciphertext_length > limits.chunk_bytes + 16:
            raise FQLC2Error("ciphertext frame length is outside the bound")
        ciphertext = _read_exact(source, ciphertext_length, "truncated ciphertext frame")
        plaintext_length = ciphertext_length - 16
        nonce = header["nonce_prefix"] + index.to_bytes(4, "big")
        aad = _frame_aad(header_hash, index, bool(final_flag), plaintext_length)
        try:
            plaintext = aead.decrypt(nonce, ciphertext, aad)
        except Exception as exc:  # cryptography intentionally normalizes tag failures
            raise FQLC2Error("FQLC2 frame authentication failed") from exc
        destination.write(plaintext)
        signed_digest.update(frame_header)
        signed_digest.update(ciphertext)
        chunks += 1
        total_plaintext += len(plaintext)
        saw_final = bool(final_flag)
        if chunks > limits.max_chunks:
            raise FQLC2Error("stream exceeds the configured chunk bound")

    signed = _verify_signature_footer(source, header, signed_digest.digest(), require_signature)
    if source.read(1):
        raise FQLC2Error("trailing bytes are not allowed")
    return {
        "schema": "ffed.qlc.fqlc2.unpack-receipt.v1",
        "format": "FQLC2",
        "chunk_count": chunks,
        "plaintext_bytes": total_plaintext,
        "header_sha256": header_hash.hex(),
        "signature_verified": signed,
        "geometry_is_key_material": False,
    }


def inspect_stream(source: BinaryIO, *, limits: FQLC2Limits = FQLC2Limits()) -> dict[str, Any]:
    """Return bounded public metadata without opening an HPKE stanza."""

    header, header_bytes, prefix = _read_header(source, limits)
    digest = hashlib.sha256(prefix)
    chunks = 0
    ciphertext_bytes = 0
    saw_final = False
    while not saw_final:
        frame_header = _read_exact(source, _FRAME_HEADER.size, "truncated frame header")
        index, final_flag, ciphertext_length = _FRAME_HEADER.unpack(frame_header)
        if index != chunks or final_flag not in (0, 1):
            raise FQLC2Error("frame sequence is invalid")
        if ciphertext_length < 16 or ciphertext_length > limits.chunk_bytes + 16:
            raise FQLC2Error("ciphertext frame length is outside the bound")
        ciphertext = _read_exact(source, ciphertext_length, "truncated ciphertext frame")
        digest.update(frame_header)
        digest.update(ciphertext)
        chunks += 1
        ciphertext_bytes += ciphertext_length
        saw_final = bool(final_flag)
        if chunks > limits.max_chunks:
            raise FQLC2Error("stream exceeds the configured chunk bound")
    signature_flag = _read_exact(source, 1, "missing signature footer")
    signature_present = signature_flag == b"\x01"
    if signature_present:
        signature_length = _SIGNATURE_LENGTH.unpack(_read_exact(source, 2, "truncated signature length"))[0]
        if signature_length != 64:
            raise FQLC2Error("invalid Ed25519 signature length")
        _read_exact(source, signature_length, "truncated signature")
    elif signature_flag != b"\x00":
        raise FQLC2Error("invalid signature footer")
    if source.read(1):
        raise FQLC2Error("trailing bytes are not allowed")
    return {
        "schema": "ffed.qlc.fqlc2.public-manifest.v1",
        "format": "FQLC2",
        "version": header["version"],
        "suite": header["suite"],
        "recipient_count": len(header["stanzas"]),
        "chunk_bytes": header["chunk_bytes"],
        "chunk_count": chunks,
        "ciphertext_bytes": ciphertext_bytes,
        "header_sha256": hashlib.sha256(header_bytes).hexdigest(),
        "container_body_sha256": digest.hexdigest(),
        "context": _json_safe_context(header["context"]),
        "signature_present": signature_present,
        "raw_payload_exposed": False,
        "recipient_identity_exposed": False,
        "geometry_is_key_material": False,
    }


def pack_bytes_v2(
    plaintext: bytes,
    recipients: Sequence[X25519PublicKey],
    **kwargs: Any,
) -> bytes:
    if len(plaintext) > MAX_BYTES_HELPER:
        raise FQLC2Error("byte helper is limited; use pack_stream for larger inputs")
    source = io.BytesIO(plaintext)
    destination = io.BytesIO()
    pack_stream(source, destination, recipients, **kwargs)
    return destination.getvalue()


def unpack_bytes_v2(container: bytes, recipient_key: X25519PrivateKey, **kwargs: Any) -> bytes:
    if len(container) > MAX_BYTES_HELPER + MAX_HEADER_BYTES + 4096:
        raise FQLC2Error("byte helper is limited; use unpack_stream for larger inputs")
    source = io.BytesIO(container)
    destination = io.BytesIO()
    unpack_stream(source, destination, recipient_key, **kwargs)
    return destination.getvalue()


def inspect_bytes_v2(container: bytes, **kwargs: Any) -> dict[str, Any]:
    return inspect_stream(io.BytesIO(container), **kwargs)


def rotate_stream(
    source: BinaryIO,
    destination: BinaryIO,
    current_key: X25519PrivateKey,
    new_recipients: Sequence[X25519PublicKey],
    *,
    limits: FQLC2Limits = FQLC2Limits(),
    signing_key: Ed25519PrivateKey | None = None,
) -> dict[str, Any]:
    """Repack with a fresh CEK; this cannot revoke plaintext already obtained."""

    with io.BytesIO() as plaintext:
        old_receipt = unpack_stream(source, plaintext, current_key, limits=limits)
        plaintext.seek(0)
        new_receipt = pack_stream(plaintext, destination, new_recipients, limits=limits, signing_key=signing_key)
    return {
        "schema": "ffed.qlc.fqlc2.rotation-receipt.v1",
        "old_header_sha256": old_receipt["header_sha256"],
        "new_header_sha256": new_receipt["header_sha256"],
        "new_recipient_count": new_receipt["recipient_count"],
        "fresh_cek": True,
        "previously_disclosed_plaintext_revoked": False,
    }


def atomic_pack_file(
    input_path: Path,
    output_path: Path,
    recipients: Sequence[X25519PublicKey],
    **kwargs: Any,
) -> dict[str, Any]:
    temporary = output_path.with_name(f".{output_path.name}.{os.getpid()}.tmp")
    try:
        with input_path.open("rb") as source, temporary.open("xb") as destination:
            receipt = pack_stream(source, destination, recipients, **kwargs)
            destination.flush()
            os.fsync(destination.fileno())
        os.replace(temporary, output_path)
        return receipt
    finally:
        temporary.unlink(missing_ok=True)


def atomic_unpack_file(
    input_path: Path,
    output_path: Path,
    recipient_key: X25519PrivateKey,
    **kwargs: Any,
) -> dict[str, Any]:
    temporary = output_path.with_name(f".{output_path.name}.{os.getpid()}.tmp")
    try:
        with input_path.open("rb") as source, temporary.open("xb") as destination:
            receipt = unpack_stream(source, destination, recipient_key, **kwargs)
            destination.flush()
            os.fsync(destination.fileno())
        os.replace(temporary, output_path)
        return receipt
    finally:
        temporary.unlink(missing_ok=True)


def _geometry_context(depth: int) -> dict[str, Any]:
    trace = build_apollonian_trace(depth=depth)
    return {
        "algorithm": trace["algorithm"],
        "root": list(DEFAULT_ROOT),
        "depth": depth,
        "trace_sha256": bytes.fromhex(trace["sha256"]),
        "hierarchy": "I -> I_system^S -> D_f -> dF -> i_fractal",
        "key_material": False,
    }


def _suite() -> CipherSuite:
    return CipherSuite.new(
        KEMId.DHKEM_X25519_HKDF_SHA256,
        KDFId.HKDF_SHA256,
        AEADId.CHACHA20_POLY1305,
    )


def _wrap_cek(recipient: X25519PublicKey, cek: bytes, context_hash: bytes) -> dict[str, bytes]:
    enc, sender = _suite().create_sender_context(
        KEMKey.from_pyca_cryptography_key(recipient),
        info=b"FQLC2/CEK/" + context_hash,
    )
    recipient_ref = os.urandom(16)
    wrapped = sender.seal(cek, aad=context_hash + recipient_ref)
    return {"ref": recipient_ref, "enc": enc, "wrapped_cek": wrapped}


def _unwrap_cek(header: Mapping[str, Any], private_key: X25519PrivateKey, context_hash: bytes) -> bytes:
    for stanza in header["stanzas"]:
        try:
            recipient = _suite().create_recipient_context(
                stanza["enc"],
                KEMKey.from_pyca_cryptography_key(private_key),
                info=b"FQLC2/CEK/" + context_hash,
            )
            cek = recipient.open(stanza["wrapped_cek"], aad=context_hash + stanza["ref"])
            if len(cek) == 32:
                return cek
        except Exception:
            continue
    raise FQLC2Error("recipient key cannot open any FQLC2 stanza")


def _derive_stream_key(cek: bytes, header_hash: bytes) -> bytes:
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=header_hash,
        info=b"FQLC2/stream-key/v1",
    ).derive(cek)


def _frame_aad(header_hash: bytes, index: int, final: bool, plaintext_length: int) -> bytes:
    return b"FQLC2/frame/v1" + header_hash + struct.pack(">IBI", index, int(final), plaintext_length)


def _canonical_cbor(value: Any) -> bytes:
    return cbor2.dumps(value, canonical=True)


def _read_header(source: BinaryIO, limits: FQLC2Limits) -> tuple[dict[str, Any], bytes, bytes]:
    limits.validate()
    magic = _read_exact(source, len(MAGIC), "truncated FQLC2 magic")
    if magic != MAGIC:
        raise FQLC2Error("not an FQLC2 container")
    length_bytes = _read_exact(source, _HEADER_LENGTH.size, "truncated header length")
    header_length = _HEADER_LENGTH.unpack(length_bytes)[0]
    if not 1 <= header_length <= MAX_HEADER_BYTES:
        raise FQLC2Error("header length is outside the bound")
    header_bytes = _read_exact(source, header_length, "truncated FQLC2 header")
    try:
        header = cbor2.loads(header_bytes)
    except Exception as exc:
        raise FQLC2Error("invalid CBOR header") from exc
    if not isinstance(header, dict):
        raise FQLC2Error("FQLC2 header must be a map")
    if _canonical_cbor(header) != header_bytes:
        raise FQLC2Error("FQLC2 header is not deterministic canonical CBOR")
    _validate_header(header, limits)
    return header, header_bytes, magic + length_bytes + header_bytes


def _validate_header(header: Mapping[str, Any], limits: FQLC2Limits) -> None:
    allowed = {"version", "suite", "chunk_bytes", "nonce_prefix", "context", "stanzas", "signed", "signer_public_key"}
    if set(header) - allowed or set(header) < {"version", "suite", "chunk_bytes", "nonce_prefix", "context", "stanzas", "signed"}:
        raise FQLC2Error("FQLC2 header fields are invalid")
    if header["version"] != FORMAT_VERSION or header["suite"] != SUITE_NAME:
        raise FQLC2Error("unsupported FQLC2 version or cipher suite")
    if not isinstance(header["chunk_bytes"], int) or not 1 <= header["chunk_bytes"] <= limits.chunk_bytes:
        raise FQLC2Error("header chunk bound is invalid")
    if not isinstance(header["nonce_prefix"], bytes) or len(header["nonce_prefix"]) != 8:
        raise FQLC2Error("nonce prefix is invalid")
    stanzas = header["stanzas"]
    if not isinstance(stanzas, list) or not 1 <= len(stanzas) <= limits.max_recipients:
        raise FQLC2Error("recipient stanzas are outside the bound")
    refs: set[bytes] = set()
    for stanza in stanzas:
        if not isinstance(stanza, dict) or set(stanza) != {"ref", "enc", "wrapped_cek"}:
            raise FQLC2Error("recipient stanza fields are invalid")
        if not isinstance(stanza["ref"], bytes) or len(stanza["ref"]) != 16 or stanza["ref"] in refs:
            raise FQLC2Error("recipient stanza reference is invalid")
        refs.add(stanza["ref"])
        if not isinstance(stanza["enc"], bytes) or not 16 <= len(stanza["enc"]) <= 256:
            raise FQLC2Error("HPKE encapsulated key is invalid")
        if not isinstance(stanza["wrapped_cek"], bytes) or not 32 <= len(stanza["wrapped_cek"]) <= 256:
            raise FQLC2Error("wrapped CEK is invalid")
    _validate_context(header["context"])
    if not isinstance(header["signed"], bool):
        raise FQLC2Error("signed flag is invalid")
    signer = header.get("signer_public_key")
    if header["signed"] and (not isinstance(signer, bytes) or len(signer) != 32):
        raise FQLC2Error("signed container requires an Ed25519 public key")
    if not header["signed"] and signer is not None:
        raise FQLC2Error("unsigned container cannot declare a signer")


def _validate_context(value: Any) -> None:
    if not isinstance(value, dict) or set(value) != {"algorithm", "root", "depth", "trace_sha256", "hierarchy", "key_material"}:
        raise FQLC2Error("geometry context fields are invalid")
    if value["algorithm"] != "integral_descartes_reflection_bfs_v1":
        raise FQLC2Error("geometry algorithm is unsupported")
    if value["hierarchy"] != "I -> I_system^S -> D_f -> dF -> i_fractal" or value["key_material"] is not False:
        raise FQLC2Error("geometry claim boundary is invalid")
    if not isinstance(value["root"], list) or len(value["root"]) != 4 or any(type(item) is not int for item in value["root"]):
        raise FQLC2Error("geometry root is invalid")
    if type(value["depth"]) is not int or not 0 <= value["depth"] <= 8:
        raise FQLC2Error("geometry depth is invalid")
    if not isinstance(value["trace_sha256"], bytes) or len(value["trace_sha256"]) != 32:
        raise FQLC2Error("geometry trace digest is invalid")


def _verify_signature_footer(source: BinaryIO, header: Mapping[str, Any], digest: bytes, require_signature: bool) -> bool:
    flag = _read_exact(source, 1, "missing signature footer")
    if flag == b"\x00":
        if header["signed"] or require_signature:
            raise FQLC2Error("required FQLC2 signature is missing")
        return False
    if flag != b"\x01" or not header["signed"]:
        raise FQLC2Error("signature footer does not match the header")
    signature_length = _SIGNATURE_LENGTH.unpack(_read_exact(source, 2, "truncated signature length"))[0]
    if signature_length != 64:
        raise FQLC2Error("invalid Ed25519 signature length")
    signature = _read_exact(source, signature_length, "truncated signature")
    try:
        Ed25519PublicKey.from_public_bytes(header["signer_public_key"]).verify(signature, digest)
    except (InvalidSignature, ValueError) as exc:
        raise FQLC2Error("FQLC2 signature verification failed") from exc
    return True


def _read_exact(source: BinaryIO, size: int, message: str) -> bytes:
    value = source.read(size)
    if value is None or len(value) != size:
        raise FQLC2Error(message)
    return bytes(value)


def _public_bytes(key: X25519PublicKey) -> bytes:
    return key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def _json_safe_context(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "algorithm": value["algorithm"],
        "root": list(value["root"]),
        "depth": value["depth"],
        "trace_sha256": value["trace_sha256"].hex(),
        "hierarchy": value["hierarchy"],
        "key_material": False,
    }
