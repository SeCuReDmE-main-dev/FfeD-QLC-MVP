# FfeD-QLC Alpha Architecture

## Operational path

`Gateway -> diagnostic -> orb project -> nine laboratories -> red/blue mission -> Vigil report -> professor decision -> portfolio`

The Gateway owns the credential-blind session contract. FfeD-QLC stores pseudonymous local learning state in SQLite and immutable generated evidence in a SHA-256-addressed artifact store. A real session cannot start when the Gateway contract is unavailable.

## Security boundary

- ChaCha20-Poly1305 supplies authenticated encryption.
- scrypt supplies passphrase-based key derivation under the single supported alpha profile.
- The geometric layer is an observable structural permutation and learning instrument.
- FQLC1 is an educational research container, not a certified or post-quantum system.
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
| Vigil | Reports and bounded mascot handoffs | Advises; never grades |
| Professor surface | Review, revise, accept, suspend, reject | Final pedagogical decision |

New alpha resources live under `/api/v1`. Historical workbench routes under `/api` remain available during pre-alpha. `/api/v1/health/live` reports process health; `/api/v1/health/ready` additionally requires the Gateway.

