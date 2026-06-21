# FfeD-QLC MVP

FfeD-QLC MVP is a public software scaffold for a bounded QLC-style admissibility layer, Docker/CodeProject.AI study-case mapping, and observable sandbox execution.

In this public repo, QLC means **Quasicrystal Logic Chamber**: a controlled decision chamber that treats every incoming item as a structured object before it is allowed to enter a project workflow. The MVP does not publish the private research model behind QLC. It exposes the useful public part: classify, contain, observe, and decide.

The product direction is simple: protect complex AI/research workspaces from accidental data mixing, secret leakage, and untraceable evidence reuse while still letting independent project blocks connect like Lego pieces.

It is intentionally bounded: it does not publish private research logic, secrets, biological claims, clinical claims, or security-certification claims. It gives a clean public base that can be discussed, tested, and extended without mixing study-case data.

## Investor Summary

Modern AI development teams connect repositories, Docker services, API keys, data folders, sandbox tools, and observability stacks very quickly. The risk is that sensitive material crosses boundaries before anyone knows what happened.

FfeD-QLC MVP proposes a lightweight control layer:

```text
incoming evidence or execution request
  -> provenance check
  -> secret-boundary check
  -> admissibility decision
  -> sandboxed execution
  -> observable runtime event
```

The first commercial shape is a developer/research operations tool that sits between local project blocks, sandbox execution, and observability. It does not replace Docker, Datadog, E2B, or GitHub. It coordinates them with a strict gate so each project can remain isolated while still being measurable.

## What It Does

- Defines a minimal evidence gate: `accept`, `suspend`, `reject`.
- Maps three local study-case blocks to CodeProject.AI endpoints.
- Keeps the public model tied to provenance, trust score, and bounded claim scope.
- Provides a Docker image and Compose entrypoint.
- Provides tests for the MVP behavior.
- Documents the E2B + Datadog sponsor demo path.

## What The Algorithm Protects

The MVP is designed around the practical problem of public and private key handling in already-existing workspaces.

It protects by policy and workflow:

- real `.env` files are excluded from git;
- secret values are never required in public examples;
- sandbox execution receives only the minimum variables it needs;
- Datadog receives runtime metadata, service tags, and counters, not raw keys;
- evidence without provenance is suspended instead of trusted;
- unbounded claims are rejected instead of promoted;
- each Docker study-case block has its own network and persistent volume.

The intended production version would add secret-pattern scanning, redaction, fingerprint-only audit records, per-repo policy files, and signed decision logs. This public MVP is the first small, testable piece of that larger system.

## What QLC Means Here

QLC is the public name for the decision chamber:

- **Q**: Quasicrystal-inspired structure, meaning non-trivial order without forcing every project into one uniform shape.
- **L**: Logic gate, meaning every item gets an explicit decision.
- **C**: Chamber, meaning each project block has a boundary before it exchanges data with the rest of the mesh.

In practical software terms, QLC is a boundary algorithm for deciding whether a source, execution request, or runtime event should be accepted, suspended, or rejected.

## Docker/CPAI Base Map

| Study case | CPAI URL | Network identifier | Persistent volume |
|---|---|---|---|
| Quasicrystal | `http://localhost:33168` | `block-quasicrystal` | `studycase-cpai-quasicrystal-data` |
| Neutrosophique | `http://localhost:33268` | `block-neutrosophique` | `studycase-cpai-neutrosophique-data` |
| FNP-QNN | `http://localhost:33368` | `block-fnp-qnn` | `studycase-cpai-fnp-qnn-data` |

The mapped CPAI servers can be managed through Portainer CE when the private local infrastructure is running. This repo only documents the public map and does not require Portainer to run the MVP.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Use The CLI

Print the default study-case map:

```bash
ffed-qlc map
```

Evaluate one evidence item:

```bash
ffed-qlc gate --source-id paper-001 --source-type whitepaper --trust-score 0.9 --has-provenance
```

Expected output:

```text
accept
```

An unbounded claim is rejected:

```bash
ffed-qlc gate --source-id claim-001 --trust-score 1.0 --has-provenance --claim-scope biological_proof
```

Expected output:

```text
reject
```

## Docker

Build and run:

```bash
docker compose up --build
```

Or build directly:

```bash
docker build -t ffed-qlc-mvp:local .
docker run --rm ffed-qlc-mvp:local map
```

## E2B + Datadog Sponsor Demo

The sponsor-facing MVP is:

```text
evidence -> admissibility gate -> E2B sandbox run -> Docker/Datadog observability
```

E2B is the isolated execution lane. Datadog is the observability lane. The QLC gate is the control lane between them.

Run an optional E2B sandbox smoke:

```bash
pip install -e ".[e2b]"
python scripts/e2b_run_mvp.py
```

The E2B smoke emits a DogStatsD counter to a local Datadog Agent when reachable:

```text
ffed_qlc.e2b.mvp_run
```

Run Docker while the local Datadog Agent is active:

```bash
docker compose up --build
```

Details:

```text
docs/e2b-datadog-sponsor-demo.md
```

Investor-facing explanation:

```text
docs/investor-brief.md
```

## Test

```bash
pytest
```

## Public Safety Boundary

This repository is public by design. Keep it public-safe:

- no real `.env` files;
- no API keys;
- no private theory notebooks;
- no claims of biological proof;
- no medical/clinical guidance;
- no production security claims without an explicit threat model and tests.

This MVP improves secret hygiene and workflow separation, but it is not yet a complete security product. Production security would require a threat model, automated secret scanning, redaction tests, access-control design, and audit-log hardening.

## Repository Layout

```text
src/ffed_qlc/
  admissibility.py
  docker_map.py
  telemetry.py
  cli.py
tests/
docs/
scripts/
Dockerfile
compose.yaml
```

## License

MIT.
