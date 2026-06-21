# Security Policy

## Public MVP Boundary

This repository is public. Do not commit:

- real `.env` files;
- private API keys;
- Datadog API keys;
- E2B API keys;
- private research notebooks;
- sensitive datasets;
- credentials, tokens, cookies, or session material.

## Secret Handling Model

The MVP protects secrets by workflow separation:

- public examples contain variable names, not values;
- Docker labels and Datadog tags must not contain secrets;
- sandbox runs should receive only the exact variables required;
- logs should contain success/failure state, not raw secret material;
- `.env` files are ignored by git.

## Image And Screenshot Redaction

Images can contain secrets even when the filename looks harmless. Before images are committed, sent to a sandbox, or referenced in public documentation:

- run object detection for sensitive regions such as screens, documents, QR codes, dashboards, and terminals;
- run OCR and secret-pattern scanning on visible text;
- use solid redaction for real keys and credentials;
- emit only fingerprints, counts, and decision IDs to observability tools;
- do not send unredacted screenshots to Datadog logs.

See `docs/yolo-secret-redaction.md`.

## Reporting

If you find a secret exposure or unsafe public artifact, open a private disclosure path with the repository owner instead of posting the secret in a public issue.

## Current Limit

This MVP is not a production cryptographic system and is not yet a certified secret-management platform. Treat it as a public scaffold for building and testing the boundary layer.
