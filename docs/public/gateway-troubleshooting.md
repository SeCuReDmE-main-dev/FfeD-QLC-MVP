# Gateway Troubleshooting

1. Confirm `FFED_QLC_GATEWAY_ROOT` points to the `fnpqnn_gateway_MVP` repository.
2. Confirm `fnpqnn_gateway_mvp/algoquest_companion.py` is present.
3. Call `/api/v1/health/live`; `200` confirms the FfeD-QLC process is alive.
4. Call `/api/v1/health/ready`; `503` means the mandatory Gateway contract is unavailable.
5. Never bypass readiness by manufacturing a session in the browser or SQLite.

The adapter imports the reviewed Gateway contract module and invokes its validator. It does not read `.env`, browser state, provider cookies or API keys.

Compose supplies `../fnpqnn_gateway_MVP` as a named BuildKit context and copies only its Python package into `/gateway`. The Gateway dependency is immutable at runtime and credential files are not copied. SQLite data remains in a named volume.

For a direct build outside Compose, provide the same context explicitly:

```powershell
docker build --build-context gateway=../fnpqnn_gateway_MVP -t ffed-qlc-mvp:local .
```
