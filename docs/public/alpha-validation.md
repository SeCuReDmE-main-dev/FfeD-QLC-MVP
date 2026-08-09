# Alpha Validation Record

This record describes the executable validation boundary for the supervised FfeD-QLC alpha.

## Verified locally

- 184 Python tests pass, including all nine bounded laboratories.
- Python and TypeScript expose the same ten versioned contract identifiers.
- Codex and Gemini Vigil vectors have equivalent contract content outside provider, identifier and timestamp fields.
- Vitest component and contract tests pass.
- Playwright passes on desktop and mobile viewports.
- The Vite production build and frontend smoke check pass.
- MkDocs builds in strict mode.
- `npm audit` reports zero known vulnerabilities and `pip check` reports no broken requirements.
- The multi-stage Docker image builds successfully.
- Docker Compose reaches `healthy` with the reviewed Gateway package supplied through a named BuildKit context.
- A real Gateway integration check returns readiness, creates a pseudonymous session and exposes the eleven-tool suite registry without credential values.

## Professor-enforced limits

The professor surface can reduce the project retry and geometry-trace budgets. The API validates every Tenebris field against the immutable alpha maximums. A student session cannot update these limits.

## Remaining boundary

This validation demonstrates internal consistency, bounded execution and reproducibility of the educational alpha. It is not a cryptographic audit, certification, production hardening review or post-quantum claim. External targets, arbitrary shell execution, real `.env` files and provider credentials remain outside the alpha.
