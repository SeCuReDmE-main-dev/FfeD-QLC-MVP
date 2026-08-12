# FfeD-QLC Alpha Architecture

## Operational path

`Gateway -> diagnostic -> orb project -> nine laboratories -> red/blue mission -> Vigil report -> professor decision -> portfolio`

The Gateway owns the credential-blind session contract. FfeD-QLC stores pseudonymous local learning state in SQLite and immutable generated evidence in a SHA-256-addressed artifact store. Public read-only and synthetic surfaces do not require the Gateway. Persistent classroom operations require both the Gateway and a verified `IdentityVerifier`; the default `PendingIdentityVerifier` refuses them with `IDENTITY_INTEGRATION_PENDING`.

## Security boundary

- ChaCha20-Poly1305 supplies authenticated encryption.
- scrypt supplies passphrase-based key derivation under the single supported alpha profile.
- The geometric layer is an observable structural permutation and learning instrument.
- FQLC1 is an educational research container, not a certified or post-quantum system.
- FQLC2 is a distinct experimental container. HPKE wraps a fresh CEK for each opaque recipient stanza; authenticated frames bind the canonical header hash, sequence, length and final marker. Geometry is authenticated public context and never key material.
- FQLC2 private keys and user documents are CLI-only. The API exposes only synthetic roundtrip and bounded public metadata inspection.
- Only synthetic fixtures are accepted by the mission engine.
- Network targets, arbitrary shell commands, real `.env` files, credentials and private student records are outside the alpha.

The hierarchy remains `I -> I_system^S -> D_f -> dF -> i_fractal` throughout measurement and evidence generation.

## Components

| Component | Responsibility | Authority boundary |
| --- | --- | --- |
| Gateway | Role, consent, pseudonymous session, tool registry | Never forwards credentials |
| SQLite store | Projects, mission state, reports, decisions | Local state only |
| Artifact store | Immutable generated JSON evidence | SHA-256 verified |
| Mission engine | Allowlisted deterministic actions | No shell or external target |
| Vigil | Deterministic reports and native receipt-backed handoffs | Advises; never grades or pretends a model was called |
| IdentityVerifier | Stable seam for the separate identity task | Pending implementation refuses persistent mutations |
| FQLC2 CLI | Key generation, pack, inspect, verify, unpack and full rotation | Experimental; private keys never enter the Web API |
| Professor surface | Review, revise, accept, suspend, reject | Final pedagogical decision |

New pre-alpha resources live under `/api/v1`. Historical workbench routes under `/api` remain available during pre-alpha. `/api/v1/health/live` reports process health. `/api/v1/health/ready` requires the Gateway only when persistent public workflows are enabled; otherwise it reports the Gateway as an explicit degraded dependency without blocking the public synthetic surface.
