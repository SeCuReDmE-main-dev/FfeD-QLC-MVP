# Passenger deployment boundary

FfeD-QLC is prepared for a same-domain cPanel Passenger release, but deployment is complete only after the cPanel Operator has produced a read-only application inventory, a plan, a dry-run, the exact operator confirmation, and live smoke-test receipts.

## Runtime contract

- `passenger_wsgi.py` exposes FastAPI through `a2wsgi.ASGIMiddleware`.
- Python must be a cPanel-supported 3.10 or 3.11 runtime.
- The release directory is immutable and named by the Git SHA.
- `dist/`, `src/`, `pyproject.toml`, `requirements-alpha.txt`, and `passenger_wsgi.py` belong to the release.
- Runtime settings are injected through the cPanel application configuration from the Settings-governed non-secret catalog. No `.env` file is deployed.
- Hosted runtime settings keep persistent public operations and native handoffs disabled until their separate gates are satisfied.

## Release sequence

1. Query `PassengerApps/list_applications` and the document-root inventory through the cPanel Operator.
2. Refuse to replace or delete an unrelated application. If no slot exists, stop.
3. Upload to a SHA-named staging directory and install pinned requirements in its isolated cPanel environment.
4. Test `passenger_wsgi.application` and the four API health/capability routes before routing traffic.
5. Apply the cPanel Operator plan only with its exact confirmation.
6. Restart Passenger, compare deployed asset hashes, and retain the previous SHA release for rollback.

The repository contains no cPanel credentials. Authentication is leased in memory by the Settings broker, and Datadog remains asynchronous and fail-open.
