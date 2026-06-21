# E2B MicroVM QLC Architecture

Primary research attribution: [ORCID 0009-0007-2904-0443](https://orcid.org/0009-0007-2904-0443).

This document defines the public-safe architecture for running a QLC experiment inside an isolated E2B sandbox while keeping secrets out of logs and public artifacts.

## Goal

Use an isolated E2B execution lane to build and test the public QLC boundary layer without mixing local study-case data, private keys, or unpublished theory into the public repository.

```text
local controller
  -> admissibility gate
  -> minimal sanitized input bundle
  -> E2B sandbox execution
  -> QLC structural envelope experiment
  -> fingerprint-only result
  -> DogStatsD/Datadog runtime metric
  -> accept, suspend, or reject decision
```

## Secret Rule

Private keys are never protected by geometry alone in the public MVP.

The correct boundary is:

- the real private key stays in a secret manager, local `.env`, hardware-backed store, or short-lived sandbox environment variable;
- public logs receive only fingerprints, hashes, decision IDs, or redacted status;
- the QLC layer can transform metadata, provenance, shard layout, admissibility state, or derived non-secret carriers;
- Datadog receives counters and tags, never raw keys;
- E2B receives only the minimum inputs required for the run.

## 4D Hilbert Geometry Layer

The "4D Hilbert" idea is treated as an experimental representation layer:

```text
key provenance fingerprint
  -> phi/quasicrystal coordinate carrier
  -> 4D Hilbert-indexed chamber state
  -> admissibility and tamper-evidence checks
```

This can be useful for:

- deterministic placement of non-secret shards;
- visualizing key-handling state without exposing key material;
- assigning challenge coordinates for later verification;
- building a tamper-evident audit model;
- separating public explanation from private protocol details.

It is not yet a public cryptographic proof, certified key vault, or replacement for standard encryption.

## E2B Runtime Pattern

The E2B sandbox should be used as a short-lived builder and test cell:

1. Start a sandbox from the public MVP template.
2. Inject only non-secret fixtures, or short-lived secret variables when absolutely needed.
3. Run the QLC gate and structural-envelope experiment.
4. Emit `ffed_qlc.e2b.mvp_run` and related non-secret counters to DogStatsD.
5. Export only redacted artifacts, hashes, and decision records.
6. Destroy or expire the sandbox.

## Datadog Runtime View

Datadog should observe:

- sandbox start and finish;
- admissibility decisions;
- rejected/suspended evidence counts;
- redaction pass/fail counts;
- Docker block identity;
- service health.

Datadog should not observe:

- private keys;
- `.env` values;
- raw images that may contain secrets;
- unredacted OCR text;
- unpublished QLC transformation internals.

## Build Priority

The first investor-facing MVP is not a full cryptosystem. It is the boundary product:

```text
classify -> redact -> sandbox -> observe -> decide
```

That is concrete, testable, sponsor-readable, and useful before the deeper QLC protocol is published.
