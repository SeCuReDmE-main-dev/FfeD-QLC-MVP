# Public Scope

FfeD-QLC MVP is a public, bounded software demonstration.

In this repository, QLC means **Quasicrystal Logic Chamber**. The name is public-facing shorthand for a structured decision boundary. The private theory is not part of this MVP.

## Public Algorithm Goal

The algorithm answers a narrow question:

```text
Should this item be accepted, suspended, or rejected before it enters a project workflow?
```

The item can be a source, claim, execution request, runtime event, or future repository artifact.

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

## Production Roadmap

To become a security-grade tool, the MVP would need:

- secret pattern scanning;
- redaction and fingerprint-only logging;
- signed admissibility decisions;
- per-repository policy files;
- Datadog dashboards and monitors;
- E2B sandbox result ingestion;
- tests proving that secrets are not emitted to logs, telemetry, or public artifacts.
