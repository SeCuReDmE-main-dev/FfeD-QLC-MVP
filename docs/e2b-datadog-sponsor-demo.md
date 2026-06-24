# E2B + Datadog Sponsor Demo

This public MVP can be presented as an observed sandbox evaluation loop.

## Goal

Show that a study-case tool can:

1. run a bounded admissibility check;
2. execute a sandboxed verification in E2B;
3. emit Docker logs and tags to Datadog;
4. keep private research and secrets out of the public repository.

## Why This Matters

The sponsor value is not "another script." The value is a repeatable control loop for complex AI workspaces:

```text
decide what is safe -> execute in isolation -> observe without leaking secrets
```

That loop is the smallest testable product surface for a larger key-protection and research-governance platform.

## E2B

Set the key locally:

```bash
E2B_API_KEY=e2b_...
```

Run:

```bash
pip install -e ".[e2b]"
python scripts/e2b_run_mvp.py
```

Expected logical result:

```text
accept
reject
E2B MVP run completed.
```

The script also emits a DogStatsD counter when the local Datadog Agent is reachable:

```text
ffed_qlc.e2b.mvp_run
```

The workflow threading layer also exposes typed counters through
`emit_qlc_workflow_counter()`:

```text
ffed_qlc.workflow.started
ffed_qlc.workflow.accepted
ffed_qlc.workflow.review_required
ffed_qlc.gateway.submit.ok
ffed_qlc.gateway.submit.failed
ffed_qlc.e2b.audit.pass
ffed_qlc.e2b.audit.fail
```

Default tags stay redacted and metadata-only:

```text
qlc_schema
media_type
swop_level
route_action
simulator_status
gateway_mode
e2b_enabled
```

Default tags:

```text
service:ffed-qlc-mvp
source:e2b
result:success|failure
```

## Datadog

Run the Docker MVP while the local Datadog Agent is active:

```bash
docker compose up --build
```

Filter in Datadog by:

```text
service:ffed-qlc-mvp
studycase_block_id:public-ffed-qlc-mvp
studycase_mesh_role:public-mvp
```

## Sponsor MVP Definition

The MVP is not a full theory engine. It is an observed execution layer:

```text
evidence -> admissibility gate -> sandbox run -> Docker/Datadog observability
```

That is the smallest useful product because a sponsor can verify that the workflow is isolated, observable, repeatable, and public-safe.

## Key Protection Boundary

The demo should never print or transmit real key values. The acceptable public data is:

- variable names;
- service names;
- Docker labels;
- success/failure status;
- non-secret counters;
- non-secret provenance identifiers.

Real values stay in the local `.env` or a future secret manager.
