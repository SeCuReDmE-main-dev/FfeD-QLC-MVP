# QLC Structural Transform

Status: public-safe prototype.

This repo now contains a concrete reversible QLC-style data transform:

```text
bytes
  -> deterministic phi/cut-and-project ordering
  -> ChaCha20-Poly1305 encryption
  -> authenticated FQLC1 container
```

The quasicrystal layer is implemented as `phi_cut_project_permutation_v1`.
It ranks each byte position through a deterministic golden-ratio integer
projection, then orders positions by an acceptance-window distance and a
parallel projection score. This makes the payload layout reproducibly
aperiodic for a given key.

Security boundary:

- confidentiality and integrity come from `ChaCha20-Poly1305`;
- the encryption key is derived with `scrypt`;
- the quasicrystal ordering is a structural transformation, not a standalone
  cryptographic proof;
- the public MVP still makes no production security-certification claim.

CLI:

```powershell
$env:FFED_QLC_PASSPHRASE = "replace-with-a-real-local-secret"
ffed-qlc pack --input .\plain.bin --output .\plain.fqlc
ffed-qlc verify --input .\plain.fqlc --output .\plain.manifest.json
ffed-qlc unpack --input .\plain.fqlc --output .\plain.roundtrip.bin
```

`verify` authenticates the container when a passphrase is available and writes a
public-safe record with hashes, transform parameters, sizes, and
`plaintext_bytes_revealed=false`. Use `--no-decrypt` when only a structural
manifest is needed.

Do not commit real packed sensitive payloads to the public repository.
