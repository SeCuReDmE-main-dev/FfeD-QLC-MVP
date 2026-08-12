from __future__ import annotations

import io
import struct

import cbor2
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from pyhpke import AEADId, CipherSuite, KDFId, KEMId, KEMKey

from ffed_qlc.fqlc2 import (
    FQLC2Error,
    FQLC2Limits,
    MAGIC,
    MAX_RECIPIENTS,
    SUITE_NAME,
    atomic_pack_file,
    atomic_unpack_file,
    generate_recipient_key_pair,
    generate_signing_key_pair,
    inspect_bytes_v2,
    load_recipient_private_key,
    load_recipient_public_key,
    load_signing_private_key,
    pack_bytes_v2,
    pack_stream,
    rotate_stream,
    unpack_bytes_v2,
    unpack_stream,
)


def _replace_header(container: bytes, header: object, *, canonical: bool = True) -> bytes:
    old_length = struct.unpack(">I", container[len(MAGIC):len(MAGIC) + 4])[0]
    body_start = len(MAGIC) + 4 + old_length
    encoded = cbor2.dumps(header, canonical=canonical)
    return MAGIC + struct.pack(">I", len(encoded)) + encoded + container[body_start:]


def _header(container: bytes) -> dict:
    length = struct.unpack(">I", container[len(MAGIC):len(MAGIC) + 4])[0]
    return cbor2.loads(container[len(MAGIC) + 4:len(MAGIC) + 4 + length])


def test_rfc9180_appendix_a2_base_vector() -> None:
    """Verify the exact X25519/HKDF-SHA256/ChaCha RFC 9180 Base vector."""

    suite = CipherSuite.new(
        KEMId.DHKEM_X25519_HKDF_SHA256,
        KDFId.HKDF_SHA256,
        AEADId.CHACHA20_POLY1305,
    )
    recipient = X25519PrivateKey.from_private_bytes(
        bytes.fromhex("8057991eef8f1f1af18f4a9491d16a1ce333f695d4db8e38da75975c4478e0fb")
    )
    context = suite.create_recipient_context(
        bytes.fromhex("1afa08d3dec047a643885163f1180476fa7ddb54c6a8029ea33f95796bf2ac4a"),
        KEMKey.from_pyca_cryptography_key(recipient),
        info=bytes.fromhex("4f6465206f6e2061204772656369616e2055726e"),
    )
    plaintext = context.open(
        bytes.fromhex(
            "1c5250d8034ec2b784ba2cfd69dbdb8af406cfe3ff938e131f0def8c8b60b4db"
            "21993c62ce81883d2dd1b51a28"
        ),
        aad=bytes.fromhex("436f756e742d30"),
    )
    assert plaintext == bytes.fromhex("4265617574792069732074727574682c20747275746820626561757479")


def test_signed_multi_recipient_roundtrip_and_public_manifest() -> None:
    first = X25519PrivateKey.generate()
    second = X25519PrivateKey.generate()
    signer = Ed25519PrivateKey.generate()
    plaintext = b"FQLC2 educational fixture" * 10

    container = pack_bytes_v2(
        plaintext,
        [first.public_key(), second.public_key()],
        signing_key=signer,
    )

    assert unpack_bytes_v2(container, first, require_signature=True) == plaintext
    assert unpack_bytes_v2(container, second, require_signature=True) == plaintext
    manifest = inspect_bytes_v2(container)
    assert manifest["format"] == "FQLC2"
    assert manifest["suite"] == SUITE_NAME
    assert manifest["recipient_count"] == 2
    assert manifest["signature_present"] is True
    assert manifest["raw_payload_exposed"] is False
    assert manifest["recipient_identity_exposed"] is False
    assert manifest["context"]["hierarchy"] == "I -> I_system^S -> D_f -> dF -> i_fractal"
    assert manifest["context"]["key_material"] is False


def test_wrong_recipient_is_rejected() -> None:
    recipient = X25519PrivateKey.generate()
    wrong = X25519PrivateKey.generate()
    container = pack_bytes_v2(b"fixture", [recipient.public_key()])

    with pytest.raises(FQLC2Error, match="cannot open"):
        unpack_bytes_v2(container, wrong)


def test_empty_file_uses_one_authenticated_final_frame() -> None:
    recipient = X25519PrivateKey.generate()
    container = pack_bytes_v2(b"", [recipient.public_key()])

    assert unpack_bytes_v2(container, recipient) == b""
    assert inspect_bytes_v2(container)["chunk_count"] == 1


def test_frame_tamper_truncation_and_trailing_bytes_are_rejected() -> None:
    recipient = X25519PrivateKey.generate()
    container = pack_bytes_v2(b"bounded fixture", [recipient.public_key()])
    header_length = struct.unpack(">I", container[len(MAGIC):len(MAGIC) + 4])[0]
    frame_start = len(MAGIC) + 4 + header_length
    tampered = bytearray(container)
    tampered[frame_start + 9] ^= 1

    with pytest.raises(FQLC2Error, match="authentication failed"):
        unpack_bytes_v2(bytes(tampered), recipient)
    with pytest.raises(FQLC2Error):
        unpack_bytes_v2(container[:-2], recipient)
    with pytest.raises(FQLC2Error, match="trailing bytes"):
        unpack_bytes_v2(container + b"x", recipient)


def test_frame_sequence_change_is_rejected_before_decryption() -> None:
    recipient = X25519PrivateKey.generate()
    limits = FQLC2Limits(chunk_bytes=8)
    source = io.BytesIO(b"0123456789abcdef")
    destination = io.BytesIO()
    pack_stream(source, destination, [recipient.public_key()], limits=limits)
    container = bytearray(destination.getvalue())
    header_length = struct.unpack(">I", container[len(MAGIC):len(MAGIC) + 4])[0]
    frame_start = len(MAGIC) + 4 + header_length
    container[frame_start + 3] = 1  # first frame index becomes 1

    with pytest.raises(FQLC2Error, match="frame sequence"):
        unpack_stream(io.BytesIO(container), io.BytesIO(), recipient, limits=limits)


def test_signature_is_optional_but_requirement_is_enforced() -> None:
    recipient = X25519PrivateKey.generate()
    unsigned = pack_bytes_v2(b"fixture", [recipient.public_key()])
    assert unpack_bytes_v2(unsigned, recipient) == b"fixture"
    with pytest.raises(FQLC2Error, match="signature is missing"):
        unpack_bytes_v2(unsigned, recipient, require_signature=True)

    signed = bytearray(pack_bytes_v2(b"fixture", [recipient.public_key()], signing_key=Ed25519PrivateKey.generate()))
    signed[-1] ^= 1
    with pytest.raises(FQLC2Error, match="signature verification failed"):
        unpack_bytes_v2(bytes(signed), recipient, require_signature=True)


def test_rotation_uses_fresh_header_and_new_recipient() -> None:
    current = X25519PrivateKey.generate()
    replacement = X25519PrivateKey.generate()
    original = pack_bytes_v2(b"rotate me", [current.public_key()])
    destination = io.BytesIO()

    receipt = rotate_stream(io.BytesIO(original), destination, current, [replacement.public_key()])
    rotated = destination.getvalue()

    assert receipt["fresh_cek"] is True
    assert receipt["old_header_sha256"] != receipt["new_header_sha256"]
    assert receipt["previously_disclosed_plaintext_revoked"] is False
    assert unpack_bytes_v2(rotated, replacement) == b"rotate me"
    with pytest.raises(FQLC2Error):
        unpack_bytes_v2(rotated, current)


def test_duplicate_and_excess_recipient_sets_are_rejected() -> None:
    recipient = X25519PrivateKey.generate()
    with pytest.raises(FQLC2Error, match="duplicate"):
        pack_bytes_v2(b"fixture", [recipient.public_key(), recipient.public_key()])

    recipients = [X25519PrivateKey.generate().public_key() for _ in range(MAX_RECIPIENTS + 1)]
    with pytest.raises(FQLC2Error, match="recipient count"):
        pack_bytes_v2(b"fixture", recipients)


def test_noncanonical_or_unknown_header_is_rejected() -> None:
    recipient = X25519PrivateKey.generate()
    container = pack_bytes_v2(b"fixture", [recipient.public_key()])
    header_length = struct.unpack(">I", container[len(MAGIC):len(MAGIC) + 4])[0]
    header_start = len(MAGIC) + 4
    header_end = header_start + header_length
    header = cbor2.loads(container[header_start:header_end])
    header["unknown"] = "rejected"
    hostile = cbor2.dumps(header, canonical=True)
    rebuilt = MAGIC + struct.pack(">I", len(hostile)) + hostile + container[header_end:]

    with pytest.raises(FQLC2Error, match="header fields"):
        inspect_bytes_v2(rebuilt)


def test_streaming_reader_is_always_called_with_a_bound() -> None:
    recipient = X25519PrivateKey.generate()

    class BoundedReader(io.BytesIO):
        def read(self, size: int = -1) -> bytes:
            assert size >= 0
            return super().read(size)

    source = BoundedReader(b"x" * 64)
    destination = io.BytesIO()
    limits = FQLC2Limits(chunk_bytes=7)
    pack_stream(source, destination, [recipient.public_key()], limits=limits)

    output = io.BytesIO()
    unpack_stream(io.BytesIO(destination.getvalue()), output, recipient, limits=limits)
    assert output.getvalue() == b"x" * 64


def test_key_generation_loading_and_type_rejection() -> None:
    passphrase = b"correct horse battery staple"
    recipient_private, recipient_public = generate_recipient_key_pair(passphrase)
    signing_private, signing_public = generate_signing_key_pair(passphrase)
    assert isinstance(load_recipient_public_key(recipient_public), type(X25519PrivateKey.generate().public_key()))
    assert isinstance(load_recipient_private_key(recipient_private, passphrase), X25519PrivateKey)
    assert isinstance(load_signing_private_key(signing_private, passphrase), Ed25519PrivateKey)

    for generator in (generate_recipient_key_pair, generate_signing_key_pair):
        with pytest.raises(FQLC2Error, match="passphrase"):
            generator(b"short")
    with pytest.raises(FQLC2Error, match="invalid recipient public"):
        load_recipient_public_key(b"not a PEM")
    with pytest.raises(FQLC2Error, match="must be X25519"):
        load_recipient_public_key(signing_public)
    with pytest.raises(FQLC2Error, match="invalid recipient private"):
        load_recipient_private_key(recipient_private, b"wrong passphrase")
    with pytest.raises(FQLC2Error, match="must be X25519"):
        load_recipient_private_key(signing_private, passphrase)
    with pytest.raises(FQLC2Error, match="invalid signing private"):
        load_signing_private_key(signing_private, b"wrong passphrase")
    with pytest.raises(FQLC2Error, match="must be Ed25519"):
        load_signing_private_key(recipient_private, passphrase)


@pytest.mark.parametrize(
    "limits, message",
    [
        (FQLC2Limits(chunk_bytes=0), "chunk_bytes"),
        (FQLC2Limits(max_recipients=0), "max_recipients"),
        (FQLC2Limits(max_chunks=0), "max_chunks"),
    ],
)
def test_limits_fail_closed(limits: FQLC2Limits, message: str) -> None:
    with pytest.raises(FQLC2Error, match=message):
        limits.validate()


def test_file_helpers_are_atomic_and_leave_no_temporary_files(tmp_path) -> None:
    passphrase = b"correct horse battery staple"
    private_pem, public_pem = generate_recipient_key_pair(passphrase)
    recipient = load_recipient_private_key(private_pem, passphrase)
    source = tmp_path / "source.bin"
    container = tmp_path / "source.fqlc2"
    recovered = tmp_path / "recovered.bin"
    source.write_bytes(b"atomic fixture" * 100)

    packed = atomic_pack_file(source, container, [load_recipient_public_key(public_pem)])
    unpacked = atomic_unpack_file(container, recovered, recipient)
    assert packed["plaintext_bytes"] == len(source.read_bytes())
    assert unpacked["plaintext_bytes"] == len(recovered.read_bytes())
    assert recovered.read_bytes() == source.read_bytes()
    assert not list(tmp_path.glob(".*.tmp"))


def test_stream_none_reads_and_chunk_limit_fail_closed() -> None:
    recipient = X25519PrivateKey.generate()

    class NoneReader:
        def __init__(self) -> None:
            self.calls = 0

        def read(self, size: int) -> bytes | None:
            self.calls += 1
            return None

    destination = io.BytesIO()
    pack_stream(NoneReader(), destination, [recipient.public_key()])
    assert unpack_bytes_v2(destination.getvalue(), recipient) == b""

    with pytest.raises(FQLC2Error, match="chunk bound"):
        pack_stream(
            io.BytesIO(b"three"),
            io.BytesIO(),
            [recipient.public_key()],
            limits=FQLC2Limits(chunk_bytes=2, max_chunks=1),
        )


def test_byte_helpers_reject_oversize_without_allocating_large_payloads(monkeypatch) -> None:
    import ffed_qlc.fqlc2 as module

    recipient = X25519PrivateKey.generate()
    monkeypatch.setattr(module, "MAX_BYTES_HELPER", 4)
    with pytest.raises(FQLC2Error, match="byte helper"):
        pack_bytes_v2(b"12345", [recipient.public_key()])
    with pytest.raises(FQLC2Error, match="byte helper"):
        unpack_bytes_v2(b"x" * (4 + module.MAX_HEADER_BYTES + 4097), recipient)


def test_parser_rejects_magic_length_type_noncanonical_and_invalid_cbor() -> None:
    recipient = X25519PrivateKey.generate()
    container = pack_bytes_v2(b"fixture", [recipient.public_key()])
    with pytest.raises(FQLC2Error, match="not an FQLC2"):
        inspect_bytes_v2(b"WRONG!" + container[len(MAGIC):])
    with pytest.raises(FQLC2Error, match="header length"):
        inspect_bytes_v2(MAGIC + struct.pack(">I", 0))
    with pytest.raises(FQLC2Error, match="invalid CBOR"):
        inspect_bytes_v2(MAGIC + struct.pack(">I", 1) + b"\x1a")
    with pytest.raises(FQLC2Error, match="must be a map"):
        inspect_bytes_v2(MAGIC + struct.pack(">I", 1) + b"\x80")

    header = _header(container)
    header["version"] = 2
    noncanonical = _replace_header(container, header, canonical=False)
    if noncanonical == _replace_header(container, header, canonical=True):
        # A deliberately non-minimal integer preserves the decoded value but is not canonical.
        encoded = cbor2.dumps(header, canonical=True).replace(b"\x02", b"\x18\x02", 1)
        old = struct.unpack(">I", container[len(MAGIC):len(MAGIC) + 4])[0]
        noncanonical = MAGIC + struct.pack(">I", len(encoded)) + encoded + container[len(MAGIC) + 4 + old:]
    with pytest.raises(FQLC2Error, match="canonical CBOR"):
        inspect_bytes_v2(noncanonical)


@pytest.mark.parametrize(
    "mutation, message",
    [
        (lambda h: h.update(version=3), "version or cipher"),
        (lambda h: h.update(chunk_bytes=0), "chunk bound"),
        (lambda h: h.update(nonce_prefix=b"short"), "nonce prefix"),
        (lambda h: h.update(stanzas=[]), "recipient stanzas"),
        (lambda h: h["stanzas"][0].update(extra=b"x"), "stanza fields"),
        (lambda h: h["stanzas"][0].update(ref=b"short"), "stanza reference"),
        (lambda h: h["stanzas"][0].update(enc=b"short"), "encapsulated key"),
        (lambda h: h["stanzas"][0].update(wrapped_cek=b"short"), "wrapped CEK"),
        (lambda h: h.update(signed="yes"), "signed flag"),
        (lambda h: h.update(signed=True), "requires an Ed25519"),
        (lambda h: h.update(signer_public_key=b"x" * 32), "unsigned container"),
        (lambda h: h.update(context={}), "geometry context fields"),
        (lambda h: h["context"].update(algorithm="other"), "algorithm is unsupported"),
        (lambda h: h["context"].update(hierarchy="collapsed"), "claim boundary"),
        (lambda h: h["context"].update(root=[1, 2]), "root is invalid"),
        (lambda h: h["context"].update(depth=9), "depth is invalid"),
        (lambda h: h["context"].update(trace_sha256=b"short"), "trace digest"),
    ],
)
def test_header_field_validation(mutation, message: str) -> None:
    recipient = X25519PrivateKey.generate()
    container = pack_bytes_v2(b"fixture", [recipient.public_key()])
    header = _header(container)
    mutation(header)
    with pytest.raises(FQLC2Error, match=message):
        inspect_bytes_v2(_replace_header(container, header))


def test_duplicate_stanza_refs_and_frame_metadata_are_rejected() -> None:
    recipient = X25519PrivateKey.generate()
    limits = FQLC2Limits(chunk_bytes=4)
    container = pack_bytes_v2(b"12345678", [recipient.public_key()], limits=limits)
    header = _header(container)
    header["stanzas"].append(dict(header["stanzas"][0]))
    with pytest.raises(FQLC2Error, match="stanza reference"):
        inspect_bytes_v2(_replace_header(container, header), limits=limits)

    header_length = struct.unpack(">I", container[len(MAGIC):len(MAGIC) + 4])[0]
    frame_start = len(MAGIC) + 4 + header_length
    bad_length = bytearray(container)
    bad_length[frame_start + 5:frame_start + 9] = struct.pack(">I", 15)
    with pytest.raises(FQLC2Error, match="frame length"):
        inspect_bytes_v2(bytes(bad_length), limits=limits)
    with pytest.raises(FQLC2Error, match="frame length"):
        unpack_bytes_v2(bytes(bad_length), recipient, limits=limits)
    with pytest.raises(FQLC2Error, match="chunk bound"):
        inspect_bytes_v2(container, limits=FQLC2Limits(chunk_bytes=4, max_chunks=1))


def test_signature_footer_shape_is_strict() -> None:
    recipient = X25519PrivateKey.generate()
    unsigned = bytearray(pack_bytes_v2(b"fixture", [recipient.public_key()]))
    unsigned[-1] = 2
    with pytest.raises(FQLC2Error, match="signature footer"):
        unpack_bytes_v2(bytes(unsigned), recipient)
    with pytest.raises(FQLC2Error, match="signature footer"):
        inspect_bytes_v2(bytes(unsigned))

    signed = bytearray(pack_bytes_v2(b"fixture", [recipient.public_key()], signing_key=Ed25519PrivateKey.generate()))
    signed[-66:-64] = struct.pack(">H", 63)
    with pytest.raises(FQLC2Error, match="signature length"):
        unpack_bytes_v2(bytes(signed), recipient)
    with pytest.raises(FQLC2Error, match="signature length"):
        inspect_bytes_v2(bytes(signed))
