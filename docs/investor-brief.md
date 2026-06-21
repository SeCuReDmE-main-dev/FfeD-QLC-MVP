# Investor Brief

## One-Line Description

FfeD-QLC is the first public MVP around **Quasicrystal Lattice Cryptography**, a protocol direction for long-term data protection through structural transformation, sandboxed verification, and observable key-safe workflows.

Primary research attribution identifier: https://orcid.org/0009-0007-2904-0443

## Problem

AI builders now work across many connected surfaces:

- local Docker services;
- GitHub repositories;
- `.env` files and API keys;
- observability tools;
- sandbox execution providers;
- research datasets and notes.

The failure mode is not only hacking. It is accidental boundary collapse: a private key lands in a public repo, a sensitive claim enters a public demo, a sandbox receives more environment than it needs, or logs become a data leak.

## Proposed Product

FfeD-QLC introduces a small control layer before execution and publication:

```text
source or request
  -> provenance check
  -> secret-boundary check
  -> admissibility gate
  -> isolated execution
  -> observable event
```

The MVP currently exposes the first version of this gate as:

```text
accept | suspend | reject
```

## What QLC Means

QLC means **Quasicrystal Lattice Cryptography**.

The core thesis is that future data security should not depend only on conventional encryption calls around otherwise uncontrolled workflows. QLC explores a layered protection model where data is transformed, classified, contained, and observed before it is allowed to move between project blocks.

For investors, the important part is not the full mathematical detail. The important part is the product behavior:

- each project block keeps its own boundary;
- public and private keys stay out of public artifacts and telemetry;
- connections are allowed only through visible interfaces;
- evidence and execution requests are classified before use;
- uncertain material is suspended;
- unbounded claims are rejected;
- runtime behavior is observable.

The MVP does not claim that QLC is already a standardized quantum-resistant cryptosystem. It positions QLC as a long-term, post-quantum-aware protocol research lane with a practical first product: key-safe workflow governance for AI and research systems.

## Why E2B And Datadog

E2B gives the product an isolated execution lane. It lets the system run a check without trusting the local machine or exposing the full workspace.

Datadog gives the product an observability lane. It lets the team and sponsor see that containers ran, checks executed, and the workflow produced measurable events.

Together:

```text
QLC decides -> E2B executes -> Datadog observes
```

## Secret Protection Strategy

The MVP protects existing public/private keys through workflow constraints:

- `.env` files are excluded from git;
- public examples contain only variable names;
- sandbox scripts require explicit variables rather than inheriting the full environment;
- logs and counters contain tags, not secret values;
- Docker blocks have separate networks and volumes;
- evidence without provenance is suspended.

The next version should add:

- automatic secret-pattern detection;
- redaction before logs and telemetry;
- fingerprint-only audit records;
- signed decision logs;
- per-repository policy files.

## What The MVP Proves

The MVP proves a small but valuable loop:

1. A public repo can define a bounded admissibility algorithm.
2. A Docker image can run the same logic reproducibly.
3. E2B can run a sandboxed smoke check.
4. Datadog can observe runtime events and Docker labels.
5. Study-case blocks can remain separated while still being mapped.

## What It Does Not Claim

This MVP is not yet a complete security platform. It does not claim production-grade key protection, compliance certification, or automated remediation. Those require threat modeling, scanning coverage, policy enforcement, and audit hardening.

It also does not disclose the full QLC structural transformation logic. The public repository is designed to attract review, sponsorship, and investment interest without giving away the private protocol core.

## Sponsor Demo

The sponsor demo should show:

- `pytest` passing;
- Docker image emitting the study-case map;
- E2B sandbox returning `accept` and `reject` examples;
- Datadog Agent receiving Docker/container telemetry;
- public repo contains no real `.env` or private key values.
