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

## FfeD CrypTe Key Manifest v1

Every new `FQLC1` container includes a public-safe manifest:

- source SHA-256 and source length;
- lattice seed fingerprint;
- projection profile and rotational profile;
- chunk policy for the current single-chunk MVP;
- `chunk_key_schedule` using `granular_chunk_key_schedule_v1`;
- crypto profile and claim boundary.

The manifest is authenticated as part of the container header. Editing it causes
normal unpack/verify authentication to fail. It is a recipe fingerprint, not the
secret key and not a quantum-proof certification.

## Granular Chunk Key Schedule v1

`ffed_qlc.key_schedule.derive_chunk_key_schedule(container_or_manifest,
chunk_count)` exposes inspectable per-chunk subkey fingerprints for the public
MVP.

The schedule is deterministic for the same manifest and chunk count, and changes
when source or lattice/projection fingerprints change. It exposes:

- `schema=ffed.qlc.granular_chunk_key_schedule.v1`;
- chunk count;
- derivation label `blake2b_fingerprint_only_mvp`;
- per-chunk `subkey_fingerprint`;
- `key_material_exposed=false`.

This is intentionally not real ECC per particle. It is a verifiable manifest
section for simulator and governance tests while production cryptography remains
bounded to the authenticated container profile.

## Compact Proof Bundle Receipt v1

Passe 4 adds
`ffed_qlc.proof_bundle.build_compact_proof_bundle_receipt()`. It links the QLC
manifest, mesh proof, audit orb, ECN packet, and route decision through stable
fingerprints:

- `bundle_nonce`;
- `artifact_fingerprints`;
- `artifact_count`;
- `receipt_fingerprint`;
- `raw_payload_embedded=false`.

The receipt is a compact MVP coherence record. It is not a distributed ledger,
blockchain, legal notarization, or external cryptographic proof.

## SWOP Before FQLC1

`ffed_qlc.swop_policy.build_sensitivity_weighted_obfuscation_policy()` is a
pre-container policy signal. It recommends where QLC should spend more
structural effort:

- sensitive or critical media regions can map to denser future chunk handling;
- low-sensitivity regions can remain `fast_basic`;
- no raw media, raw OCR, or secret value is embedded in the policy output.

SWOP does not change the current `FQLC1` container format yet. It prepares the
final pass where obfuscation intensity can be tightened into the tool workflow.

## SWOP-to-Chunk Protection Plan v1

Passe 5 adds `ffed_qlc.chunk_protection_plan.build_swop_chunk_protection_plan()`.
It converts SWOP policy regions into chunk allocation guidance:

- logical region index;
- chunk range;
- protection tier;
- obfuscation intensity;
- recommended chunk mode;
- optional subkey fingerprint from the chunk key schedule.

It exposes fingerprints only and does not change `FQLC1`. It is a preparation
layer for the final tightening pass, not ECC per particle, certified adaptive
encryption, or a quantum-proof claim.

## QLC Protection Workflow Bundle v1

`ffed_qlc.workflow.build_qlc_protection_workflow()` is the current protocol
threading layer. It does not change the `FQLC1` container format. It wraps the
existing functions into one inspectable bundle:

- protected intake;
- FNP-QNN mesh payload;
- SWOP and SWOP-to-chunk plan;
- granular chunk key schedule fingerprints;
- privacy-safe audit orb and ECN handoff;
- CeLeBrUm route decision and optional quarantine capsule;
- compact proof receipt;
- reciprocal utility scorecard;
- gateway submission contract.

The gateway submission schema is `ffed.qlc.gateway_submission.v1`. It is the
handoff object used by `fnpqnn gateway qlc-submit` and carries only metadata,
fingerprints, route tags, and the simulator-ready mesh payload.

Do not commit real packed sensitive payloads to the public repository.
