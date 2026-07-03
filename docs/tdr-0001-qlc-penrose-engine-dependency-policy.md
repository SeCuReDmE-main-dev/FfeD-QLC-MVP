# TDR 0001: QLC Penrose Engine Dependency Policy

Status: accepted for pre-alpha implementation.

## Context

The QLC Penrose Plithogenic Workbench must turn the source digests into
measurable functions: source-function profiles, Penrose thin/thick rhombi,
plithogenic classification, fractal path measurement, `D_f -> D_f_hat -> dF`,
tile admission, orb envelopes, and redacted exports.

The existing repository already has a working Python package, CLI, FQLC1
container, workflow bundle, audit orb, gateway handoff, and 104 passing tests.
The new math engine must strengthen that base without replacing `FQLC1` or
introducing avoidable dependency risk.

## Decision

Use a Python-stdlib-first implementation for the first Penrose/plithogenic math
pass.

- Core geometry, inflation, cut-and-project, source profiles, box-counting, and
  admission logic must use the standard library first.
- Keep `cryptography` as the existing FQLC1 dependency; do not replace or
  rewrite the current authenticated container.
- Do not add NumPy/SciPy/networkx for the first engine pass unless a measured
  test case proves standard-library code is insufficient.
- Add FastAPI only when the Python math engine has passing unit tests and a
  stable CLI/export contract.
- Add React/Vite/TypeScript only after the engine returns real lattice,
  admission, and orb data through stable interfaces.
- Keep CPAI/YOLO integration metadata-only; do not vendor or copy CodeProject
  AI Server.

## Rationale

- The requested mechanism is math-contract sensitive. Small dependency choices
  can hide implementation shortcuts behind library objects before the project
  has verified its own variables and invariants.
- Current tests already validate secret-safe workflow behavior. The first
  implementation pass should preserve that evidence and add focused math tests.
- Standard-library code keeps the public MVP easy to audit and avoids large
  install surface while the model is still pre-alpha.

## Revisit Trigger

Re-evaluate adding a numerical or graph library only when one of these becomes
true:

- target lattice size exceeds a measured standard-library performance budget;
- box-counting or adjacency reconstruction becomes the dominant test/runtime
  bottleneck;
- frontend graph rendering requires a dedicated visualization dependency;
- a new API contract proves a library reduces code complexity without weakening
  the math boundaries.

## Boundaries

- This TDR is not a cryptographic security claim.
- This TDR does not authorize changes to `FQLC1`.
- This TDR does not authorize raw source, raw media, raw OCR, raw `T/I/F`, or
  secret export.
