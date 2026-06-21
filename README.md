# FfeD-QLC MVP

FfeD-QLC MVP is a small public software scaffold for a bounded QLC-style admissibility layer and a Docker/CodeProject.AI study-case map.

It is intentionally modest: it does not publish private research logic, secrets, biological claims, clinical claims, or security-certification claims. It gives a clean public base that can be discussed, tested, and extended without mixing study-case data.

## What It Does

- Defines a minimal evidence gate: `accept`, `suspend`, `reject`.
- Maps three local study-case blocks to CodeProject.AI endpoints.
- Keeps the public model tied to provenance, trust score, and bounded claim scope.
- Provides a Docker image and Compose entrypoint.
- Provides tests for the MVP behavior.

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

## Repository Layout

```text
src/ffed_qlc/
  admissibility.py
  docker_map.py
  cli.py
tests/
docs/
Dockerfile
compose.yaml
```

## License

MIT.

