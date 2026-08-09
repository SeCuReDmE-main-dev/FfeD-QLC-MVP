# FfeD-QLC: cross-suite learning path and red/blue cyberrange boundary

Status: architecture research brief  
Date: 2026-08-09  
Scope: education MVP design; no production integration is authorized by this document.

## The progression

FfeD-QLC is not an isolated cryptography dashboard. It is the point where earlier learning becomes an inspectable security artefact. A learner first develops a vocabulary for algorithms, state, graph structure, testing, evidence, and uncertainty. Then the learner builds an orb of laboratory data, defines the algorithm that traverses it, attacks the result, and documents what the experiment supports.

```text
AlgoQuest foundations
  -> Visual Algorithm Designer mastery record
  -> FfeD-QLC Orb Studio
  -> bounded red/blue mission
  -> Vigil evidence report
  -> professor decision and next learning route
```

The `93%` threshold is a configurable professor-owned gateway for a prerequisite pathway. It is not a universal grade, a hidden model decision, or evidence that a student understands cryptography. Before integration, the suite must verify that VAD can emit a versioned mastery record with the learner's consent and an auditable evidence link.

## Orb Studio: what a learner owns

The learner creates a laboratory orb from synthetic components:

- a graph or neural-network-like topology;
- declared nodes, edges, states, constraints, and traversal rules;
- a versioned canonical trace;
- an attack hypothesis;
- a detection expectation;
- a countermeasure proposal;
- a proof bundle naming the limitation.

The learner never provides a real credential, `.env`, private key, production target, or external host. Standard cryptographic primitives and resource budgets remain professor-controlled. The learner can invent, inspect, test, revise, and defend their algorithm without making an unsupported encryption claim.

## Cross-suite contract candidates

| Tool | Specific contribution to FfeD-QLC | Input to share | Output to receive | MVP boundary |
|---|---|---|---|---|
| AlgoQuest | Prerequisite algorithmic reasoning, Qbit profile, learning route | competency tags and completed concepts | recommended preparatory mission | Read only, consented, no hidden grading |
| Visual Algorithm Designer | Verified node/edge algorithm design and mastery evidence | versioned project snapshot plus professor-approved mastery record | Orb Studio starter topology | `93%` is configurable; validate the actual existing event contract first |
| Algorithm Builder | Data-structure, graph, recursion, and complexity exercise material | public exercise or exported algorithm representation | a trace-design challenge | Do not couple to its current legacy runtime until its frontend/backend boundary is repaired |
| FNP-QNN-MVP | Synthetic neural-network graph and controlled simulation context | toy pipeline topology, synthetic events, declared assumptions | red/blue scenario seed | Simulation outputs are learning data, never cryptographic proof |
| FNP-QNN Gateway | Credential-blind policy, contract validation, model/provider boundary | authorized fixture reference and policy ID | refusal or contract audit | No provider secret, cookie, session, or dotenv value crosses the boundary |
| QuaNThoR | Formal reasoning and mathematical proof review | exact Apollonian/graph trace and proposition | proof obligations and contradiction notes | Assistance only; a formal proof status must stay explicit |
| Synthia | Provenance, lexicon, contradiction and professor cockpit patterns | evidence bundle metadata and terms | traceability review / glossary link | Synthia supports traceability; it is not cryptographic or editorial authority |
| V.O.T-Guardian | Incident workflow, alert triage, runbook, and safe stop pattern | synthetic alert/event stream | remediation-runbook exercise | Audio/voice integrations remain separate and use fixtures only |
| Market Guardian / RetailGuard | Adversarial simulation, anomaly/detection exercise, domain-specific blue-team framing | synthetic transaction/sensor event graph | detection and mitigation scenario | No live retail system or surveillance feed |
| Tesla Resonance Recovery Workbench | Evidence gate and source-grounded claim discipline | stated claim, citation, expected evidence | accept/suspend evidence check | Mathematical/scientific evidence gate only, not a security certification |

## Red/blue cyberrange vocabulary

The UI should use an analyst-readable mission format:

```text
authorized scope -> asset -> hypothesis -> simulated technique
-> telemetry -> detection -> countermeasure -> evidence -> limitation -> decision
```

The mission cards may map a technique to MITRE ATT&CK or ATLAS vocabulary and a defensive response to MITRE D3FEND vocabulary. These mappings improve communication with security teams. They do not grant permission to target networks, prescribe a control, or demonstrate the effectiveness of a mitigation.

For neural-network-like systems, the cyberrange uses a local synthetic graph:

```text
data source -> feature transform -> model/inference stage -> output -> event log
```

Permitted learning scenarios include provenance loss, drift, malformed payload handling, toy poisoning/evasion cases, alert false positives, and policy failures. The range rejects network scanning, credential testing, exploit payloads, external IP targets, live model endpoints, and real student data.

## Interface: five panels

1. **Prerequisite gate**: visible VAD/AlgoQuest evidence, required skills, professor override, and reason for entry.
2. **Orb Studio**: learner graph, declared rules, canonical-trace preview, schema/version validation, and static complexity budget.
3. **Mission console**: authorized fixture, attack hypothesis, allowed mutation controls, reset button, and Tenebris stop state.
4. **Detection and defense**: telemetry, observed detection, D3FEND-style defensive vocabulary, remediation candidate, and explicit uncertainty.
5. **Evidence bundle**: command/run metadata, fixture hash, expected vs observed result, limitation, Vigil report, and professor decision.

## Contracts that must exist before integration

```text
mastery_record.v1
  learner_pseudonym, source_tool, competency_tags, score, evidence_ref,
  assessor, consent, issued_at, expires_at, version

orb_project.v1
  synthetic_fixture_ref, graph, traversal_rules, canonicalization_version,
  attack_hypothesis, telemetry_profile, resource_budget, version

mission_run.v1
  authorized_scope, mission_id, fixture_hash, mutation_set, telemetry,
  detection_result, evidence_ref, limitation, decision
```

All records must be schema validated, versioned, minimal, and safe to retain. A record containing a secret, direct identifier, private source content, or external target must be rejected before storage.

## Acceptance criteria for a future implementation proposal

- A VAD mastery record can be validated without reading student source code or personal data.
- A teacher can set, explain, and override the 93% prerequisite threshold.
- Orb Studio produces byte-identical canonical traces for the same fixture and rules.
- A mission starts only with an allowlisted local fixture and fixed Tenebris budget.
- The student can distinguish a simulated attack from an action against a real system.
- The evidence bundle identifies mechanism, evidence, limitation, and a human decision.
- Codex and Gemini accept the same Vigil schema and refuse the same sensitive input categories.

## References

- MITRE D3FEND: <https://d3fend.mitre.org/about/>
- NIST SP 800-115: <https://csrc.nist.gov/pubs/sp/800/115/final>
- NIST AI 100-2: <https://doi.org/10.6028/NIST.AI.100-2>
- NIST AI RMF: <https://doi.org/10.6028/NIST.AI.100-1>
