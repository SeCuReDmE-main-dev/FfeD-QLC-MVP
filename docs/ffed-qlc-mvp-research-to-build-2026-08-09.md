# FfeD-QLC MVP: research-to-build boundary

Status: research closure brief  
Date: 2026-08-09  
Scope: educational MVP planning only; no cryptographic claim expansion and no production secret handling.

## The current decision

FfeD-QLC should first become a reproducible cryptography-learning laboratory. Its vital loop is intentionally small:

```text
synthetic fixture
  -> inspect a declared mechanism and run one bounded attack/verification
  -> evidence bundle with an explicit limitation and accept|suspend|reject decision
```

The immediate product teaches attribution: students learn which primitive supplies confidentiality, integrity, key derivation, context binding, provenance, or merely visual structure. A professor receives the evidence bundle and remains the authority for grading and stopping an experiment.

## Learner-built orb and red/blue interface

The learner reaches FfeD-QLC through prior work in AlgoQuest and Visual Algorithm Designer. The student builds a synthetic graph, writes traversal rules, creates a versioned trace, attacks it inside a bounded cyberrange, and records a limitation. VAD may act as a visible prerequisite gate when a professor-configured mastery threshold such as `93%` is met and backed by a consented, versioned evidence record.

The interface should look familiar to active red and blue teams: authorized scope, asset, hypothesis, simulated technique, telemetry, detection, countermeasure, evidence, limitation, decision. Missions run only against local fixtures or synthetic neural-network-like graphs. They never scan, exploit, credential-test, or contact a live network.

The full cross-suite map and the contracts required before integration are in [the cross-suite learning-path brief](ffed-qlc-cross-suite-learning-path-2026-08-09.md).

## What is established

- FQLC1 has a tested laboratory baseline built around scrypt, a reversible keyed structural permutation, and ChaCha20-Poly1305.
- ChaCha20-Poly1305 supplies confidentiality and integrity. scrypt raises the cost of guessing a passphrase. The permutation is an experimental structure, not an independently established cryptographic margin.
- The existing orb is a redacted provenance surface. It must never embed plaintext, key material, raw media, or a real `.env` value.
- The strongest future geometry hypothesis is a public, exact, versioned trace used as AAD or HKDF context. It can bind context and separate domains. It does not add secret entropy.
- A real multi-recipient secret-sharing format needs a random content-encryption key, authenticated streaming encryption, standard recipient encapsulation/wrapping, a minimal versioned manifest, and explicit key lifecycle policy.
- Vigil is a pedagogical inspector. It must operate with the same contract for Codex and Gemini and can only return `accept`, `suspend`, or `reject` with evidence and a limitation.

## MVP boundary

### Build toward now

1. Synthetic fixture catalog, immutable hashes, schema versions, and reproducible test manifests.
2. A transparent FQLC1 inspection lab showing header fields, authenticated-data binding, nonce policy, KDF limits, successful decryption and uniform failure paths.
3. A geometry lab that compares visual geometry, reversible permutation, and canonical public context without calling any of them a cipher.
4. Exact Apollonian traversal experiments with deterministic byte serialization, collision/cycle checks, golden vectors, and cross-implementation tests.
5. A paper-model or fixture-only multi-recipient envelope lesson based on standard primitives.
6. Vigil reports using the canonical fields: observation, mechanism, attack, evidence, limitation, decision, safe next action.
7. Professor review, explicit Tenebris resource budgets, and student-visible stop reasons.
8. Orb Studio progression from AlgoQuest and VAD: a learner graph, declared rules, canonical trace, validator, bounded attack scenario, and evidence export.
9. Red/blue cyberrange missions over local fixtures and synthetic neural-network-like graphs with explicit detection and defense vocabulary.

### Research before implementation

- Exact normative Penrose or phason canonicalization.
- Any geometry-derived secret factor.
- A custom multi-recipient container or standalone cryptographic format.
- Security claims beyond the properties of the standard primitives used.
- Any handling of real `.env` values, keys, tokens, private files, or production identities.

### Explicitly reject for MVP

- A "fractal cipher" claim.
- Complexity or visual unpredictability as a security metric.
- Autonomous AI certification, grading, publication, or secret analysis.
- Unbounded KDF, graph, traversal, agent, or retry budgets.
- Hidden dependencies from historical FfeD, FeccD, ReaAaS-N, YOLO, or visual subsystems.

## Ambiguities that must close before code changes

| Boundary | Decision required | Verification that closes it |
|---|---|---|
| Fixture | Exact schema, sensitivity rule, generator, hash and version | A fixture round-trip and schema validation run in CI |
| FQLC1 parser | Header caps, KDF caps, error taxonomy and memory budget | Fuzz/mutation suite rejects malformed input uniformly |
| Geometry | Canonical byte representation and version | Golden vectors match on two implementations/platforms |
| Context | Exact AAD/HKDF fields and domain-separation labels | Differential tests prove field changes cause expected authentication/key separation behavior |
| Envelope | Recipient stanza profile, CEK lifecycle, metadata exposure | Threat-model review and fixture-only add/remove/revoke scenarios |
| Vigil | Provider-neutral request/response schema and parity rubric | Same fixture yields complete bounded reports from Codex and Gemini |
| Tenebris | Limits for fixture size, depth, branches, KDF cost and retries | Limit tests terminate predictably and log a safe stop reason |
| Curriculum | Observable outcome and rubric for each lab | Professor can grade evidence without trusting model prose |
| Prerequisite | VAD mastery record, consent, threshold and professor override | Schema validation plus a visible reason for entry or refusal |
| Orb Studio | Learner-editable graph/rules versus professor-locked safety boundary | Schema validation, golden trace, and fixture-only attack run |
| Cyberrange | Authorized scenario, telemetry, detection and defense mapping | Every mission resets locally and exports no actionable external procedure |

## Engineering contracts

Every future module needs an explicit versioned contract. At minimum:

```text
fixture.v1             synthetic input; no secrets; provenance + hash
geometry_trace.v1      exact canonical bytes; algorithm + parameters + version
orb_public.v1          redacted provenance; no plaintext/key/raw media
vigil_report.v1        observation/mechanism/attack/evidence/limitation/decision
professor_decision.v1  human approval, stop, remediation, audit timestamp
```

The container/envelope contract is deliberately not assigned a version until the HPKE/streaming/key-lifecycle research has produced a complete threat model, schema, vectors, and an external review plan.

## Test hierarchy

1. Unit tests: field validation, bounds, error codes, serialization, permission refusal.
2. Golden vectors: stable expected bytes for exact traces and fixtures.
3. Property tests: round-trip, deterministic canonicalization, mutation rejection, no clear material in an orb.
4. Fuzz/mutation: header length, KDF parameters, malformed stanzas, Unicode and numeric ambiguity, truncation, reordering, replay/downgrade fixtures.
5. Differential tests: independent encoders/platforms produce the same canonical trace.
6. Performance: p50/p95 runtime and peak memory on public synthetic fixtures; budgets are explicit before measuring.
7. Pedagogy: students must attribute a claim to its mechanism and name at least one limitation; polished prose alone never passes.

## Design rule

`Protect your heritage. Secure our legacy.` means preserving the research history while refusing to confuse it with a finished primitive. The archive stays valuable as provenance and hypothesis material. The MVP earns trust by making its mechanics, limits, attacks, and evidence visible.

## Related research artefacts

- `C:\Users\jeans\Desktop\Case study\article ecrit\journalisme_professionnel\10_articles\2026-08-09-ffed-qlc-vigil-geometric-orb\audits\FQLC1_AUDIT.md`
- `C:\Users\jeans\Desktop\Case study\article ecrit\journalisme_professionnel\10_articles\2026-08-09-ffed-qlc-vigil-geometric-orb\architecture\ORB_ARCHITECTURE_DECISION.md`
- `C:\Users\jeans\Desktop\Case study\article ecrit\journalisme_professionnel\10_articles\2026-08-09-ffed-qlc-vigil-geometric-orb\attacks\THREAT_MODEL_AND_ATTACK_MATRIX.md`
- `C:\Users\jeans\Desktop\Case study\article ecrit\journalisme_professionnel\10_articles\2026-08-09-ffed-qlc-vigil-geometric-orb\pedagogy\VIGIL_SPECIFICATION.md`
- `C:\Users\jeans\Desktop\Case study\article ecrit\journalisme_professionnel\10_articles\2026-08-09-ffed-qlc-vigil-geometric-orb\research\DEEP_RESEARCH_9_39_CODING_CLOSURE_PROMPT_FR.md`
