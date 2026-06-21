# Public Scope

FfeD-QLC MVP is a public, bounded software demonstration.

In this repository, QLC means **Quasicrystal Lattice Cryptography**. It is a research protocol direction for long-term data protection using structural transformation patterns inspired by quasicrystal lattice geometry. The private theory is not part of this MVP.

Attribution: https://orcid.org/0009-0007-2904-0443

## Public Algorithm Goal

The public MVP answers a narrow operational question:

```text
Should this item be accepted, suspended, or rejected before it enters a protected QLC workflow?
```

The item can be a source, claim, execution request, runtime event, or future repository artifact.

## Coherent Public Definition

Quasicrystal Lattice Cryptography is presented here as a protocol concept for protecting data by combining:

- structural data transformation;
- project-level containment;
- provenance-aware admissibility;
- sandboxed execution;
- observable but non-secret telemetry.

This MVP does not claim quantum resistance as a proven property. It frames QLC as a protocol under development whose design goal is long-term resilience, including post-quantum threat awareness.

## Included

- Minimal admissibility gate: `accept`, `suspend`, `reject`.
- Docker/CPAI study-case block map.
- Small CLI for printing the map and evaluating one evidence item.
- Tests for the public behavior.
- Optional E2B sandbox demo script.
- Datadog-friendly Docker labels and DogStatsD counter emission.

## Key Protection Intent

This MVP is aimed at protecting already-existing public/private keys and project boundaries by changing the workflow:

- secrets stay in local `.env` files;
- public code receives variable names, never real values;
- Docker blocks are separated by named networks and volumes;
- Datadog receives tags and counters, not secret values;
- E2B runs receive only the minimum environment needed for a sandbox test;
- uncertain evidence is suspended rather than silently trusted.

This is not a substitute for a production secret manager. It is a policy and execution layer that can later integrate with one.

## Excluded

- Secrets and `.env` values.
- Private research notes.
- Biological proof claims.
- Clinical or medical claims.
- Production security certification claims.
- Upstream changes to third-party repositories.
- Full secret scanning and redaction engine.
- Signed audit ledger.
- Access-control service.
- Full QLC structural transformation logic.

## Production Roadmap

To become a security-grade tool, the MVP would need:

- secret pattern scanning;
- redaction and fingerprint-only logging;
- signed admissibility decisions;
- per-repository policy files;
- Datadog dashboards and monitors;
- E2B sandbox result ingestion;
- tests proving that secrets are not emitted to logs, telemetry, or public artifacts.
