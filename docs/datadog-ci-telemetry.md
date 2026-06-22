# Datadog CI telemetry

The GitHub Actions workflow `.github/workflows/ci-datadog.yml` runs public unit
tests, checks the public-safe boundary, and emits a minimal Datadog CI marker
when the repository or organization secret `DD_API_KEY` is configured.

The metric payload is public-safe. It contains only status and repository
metadata; it must never include raw prompts, payloads, keys, private notebooks, or
`.env` values.

## Metrics

- `ffed_qlc.ci.validation` — gauge, `1` when validation succeeds and `0` when it fails.
- `ffed_qlc.ci.run` — count, increments once per workflow run.

## Monitor tags

- `team:fnp-qnn`
- `service:ffed-qlc-mvp`
- `repo:ffed-qlc-mvp`
- `env:alpha-local`
- `component:ci`
- `managed_by:github-actions`

After the metric is visible in Datadog, create a monitor such as:

```text
min(last_15m):min:ffed_qlc.ci.validation{repo:ffed-qlc-mvp,service:ffed-qlc-mvp,env:alpha-local} < 1
```
