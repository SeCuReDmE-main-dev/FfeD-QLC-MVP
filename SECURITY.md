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

## Reporting

If you find a secret exposure or unsafe public artifact, open a private disclosure path with the repository owner instead of posting the secret in a public issue.

## Current Limit

This MVP is not a production cryptographic system and is not yet a certified secret-management platform. Treat it as a public scaffold for building and testing the boundary layer.

