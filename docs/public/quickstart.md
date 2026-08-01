# FfeD-QLC quickstart

## Requirements

Use a clean checkout, the runtime declared by the repository, and its committed lockfiles. Confirm the active branch before installing anything.

```powershell
git status --short --branch
```

## Install

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e .[dev]
npm install
```

## Start

```powershell
npm run dev
.venv\Scripts\ffed-qlc --help
```

## Verify

```powershell
.venv\Scripts\python -m pytest
npm run build
```

## Human acceptance

Inspect the output, logs, test results, and diff. Accept, request a correction, quarantine, or stop; do not silently promote a generated result.
