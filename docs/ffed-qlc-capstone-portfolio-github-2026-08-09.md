# FfeD-QLC capstone portfolio and GitHub evidence boundary

Status: design contract for research closure  
Date: 2026-08-09  
Scope: read-only evidence intake proposal; no GitHub connector or write integration is enabled by this document.

## Capstone role

FfeD-QLC belongs near the end of the SecuredMe Education path. It opens a personal portfolio route for a learner who has accumulated work over years, including work from the fifth year onward. The product does not manufacture achievement. It turns approved evidence of work into an explainable defence-of-systems case study:

```text
previous learning evidence
  -> consented portfolio snapshot
  -> learner-built laboratory orb
  -> bounded red/blue verification mission
  -> evidence bundle and professor decision
  -> personal portfolio entry
```

The portfolio entry shows what the learner built, which mechanism was tested, what failed, what was improved, and what remains unproven. That is a stronger professional demonstration than a decorative score.

## GitHub is an evidence source, not an automatic judge

The current FfeD-QLC repository already uses GitHub as a public project surface and includes a redacted-orb model plus a local AlgoQuest learning-event stub. The stub is currently a dry-run local record, not a verified cross-tool progression service. A future integration must keep this distinction visible.

### Allowed read-only evidence

- repository identity, selected branch, commit SHA, and release tag;
- selected public files or a learner-approved local snapshot;
- test command, test result summary, coverage/quality artefact when available;
- issues, pull requests, code-review evidence, and changelog references selected by the learner;
- dependency manifest and security-policy references;
- generated FfeD-QLC fixture, canonical trace, redacted orb, and Vigil report.

### Excluded evidence

- secrets, `.env`, credentials, private keys, cookies, browser sessions, tokens, private repositories without explicit consent, raw student chat logs, hidden telemetry, full commit history by default, and automatic write access.

### Human control

The learner chooses the repository and the artefacts to include. The professor approves the portfolio entry. The system stores references and hashes where possible, rather than copying whole repositories. A learner can remove an entry or revoke a source connection. No score, AI statement, or GitHub activity count is treated as a proof of cybersecurity competence by itself.

## Evidence record contracts to research

```text
learning_evidence.v1
  source_tool, competency_tags, evidence_ref, artifact_hash,
  learner_consent, assessor, status, issued_at, version

github_portfolio_snapshot.v1
  repository_url, selected_ref, commit_sha, selected_artifacts,
  test_summary_ref, security_policy_ref, learner_consent,
  imported_at, source_visibility, version

capstone_orb_project.v1
  prerequisite_evidence_refs, synthetic_fixture_ref, graph,
  traversal_rules, canonicalization_version, mission_ref,
  redacted_orb_ref, evidence_bundle_ref, professor_decision

portfolio_case_study.v1
  title, learner_approved_summary, mechanisms_tested,
  attacks_run, findings, limitations, evidence_refs,
  public_visibility, professor_approval, version
```

Every contract is versioned and schema validated. `learner_consent` and `public_visibility` are mandatory. A record with a secret, a direct identifier, an external target, or a raw private payload is rejected before it can enter an orb or portfolio.

## Cross-suite flow

1. AlgoQuest exposes the learning route and prerequisite concepts.
2. VAD exposes an approved graph or algorithm artefact. The existing FfeD-QLC event shape uses a threshold of `93` in dry-run mode; a future integration must replace the stub only through a documented consented contract and a professor-configurable threshold.
3. Algorithm Builder contributes data-structure, graph, recursion, and complexity reasoning.
4. FNP-QNN contributes a synthetic neural-network-like pipeline, never an operational system.
5. QuaNThoR supplies proof obligations and contradiction notes.
6. Synthia supplies provenance and lexicon review without becoming an authority for the claim.
7. V.O.T-Guardian and Market Guardian supply safe incident, alert, detection, and remediation mission shapes.
8. Tesla Workbench supplies source/evidence gates.
9. FNP-QNN Gateway enforces credential-blind and provider-boundary rules.
10. FfeD-QLC combines only the approved references into the Orb Studio evidence bundle.

## Acceptance criteria for a future build

- A student can select a prior project artefact without granting repository write access.
- A portfolio snapshot shows the exact selected revision, evidence references, consent, and visibility.
- VAD's 93% threshold is visibly configured and may be overridden by a professor with a reason.
- A capstone mission accepts only an approved synthetic fixture and a declared local scope.
- The generated orb remains redacted: no plaintext, key material, raw media, or raw source URLs.
- A portfolio entry includes at least one limitation and one human decision.
- Removing consent prevents future use while preserving only the audit record required by the stated retention policy.

## Claim boundary

Allowed: "This portfolio demonstrates a student-designed, bounded security-learning experiment with reproducible evidence."

Not allowed: "This portfolio certifies the student's cybersecurity ability" or "this orb cryptographically protects a system" without a directly supported mechanism and the appropriate independent review.
