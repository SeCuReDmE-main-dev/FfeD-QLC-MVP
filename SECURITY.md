# Security Policy

## SecuredMe Education Governance Alignment

- Current phase: pre-alpha / in development.
- Repository license: Secured Educational Cybersecurity License 2.0 (SECL-2.0), local metadata reference LicenseRef-SECL-2.0.
- Official AI-assisted classroom routes: Codex/OpenAI and Antigravity/Gemini only.
- Do not add Ollama Cloud, uncensored local AI, raw-token student flows, or unknown agent providers as official school routes.
- Cybersecurity, fraud-awareness, protection, or abuse-prevention behavior must stay defensive and supervised.
- Preserve human-review boundaries; do not claim production, clinical, regulatory, enforcement, safety-critical, or autonomous authority readiness.
- Private modified copies, broken forks, and unreviewed rewrites are not a maintainer support obligation.


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

## Optional Bouncy Castle Perimeter

The optional `bcctl` integration uses Bouncy Castle through an external local
tool to sign public metadata digests. It is a perimeter integrity receipt for
workflow bundles, not a replacement for the QLC structural transform,
ChaCha20-Poly1305, scrypt key derivation, or future production threat modeling.

The provider boundary is strict:

- pass only key IDs, context digests, artifact/message digests, and signature
  digests;
- never pass raw files, plaintext, passphrases, API keys, `.env` values, private
  corpus text, screenshots, or raw simulator payloads;
- keep provider failures sanitized and do not echo local filesystem paths in
  public status output;
- leave normal QLC commands functional when `bcctl` is not configured.

See `docs/bouncy-castle-perimeter.md`.

## Reporting

If you find a secret exposure or unsafe public artifact, open a private disclosure path with the repository owner instead of posting the secret in a public issue.

## Current Limit

This MVP is not a production cryptographic system and is not yet a certified secret-management platform. Treat it as a public scaffold for building and testing the boundary layer.
