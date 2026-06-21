from ffed_qlc import AdmDecision, Evidence, evaluate_evidence


def test_accepts_bounded_high_trust_evidence_with_provenance() -> None:
    evidence = Evidence(
        source_id="paper-001",
        source_type="whitepaper",
        trust_score=0.9,
        has_provenance=True,
    )

    assert evaluate_evidence(evidence) == AdmDecision.ACCEPT


def test_suspends_missing_provenance() -> None:
    evidence = Evidence(
        source_id="repo-001",
        source_type="github",
        trust_score=0.9,
        has_provenance=False,
    )

    assert evaluate_evidence(evidence) == AdmDecision.SUSPEND


def test_rejects_unbounded_claim_scope() -> None:
    evidence = Evidence(
        source_id="claim-001",
        source_type="note",
        trust_score=1.0,
        has_provenance=True,
        claim_scope="biological_proof",
    )

    assert evaluate_evidence(evidence) == AdmDecision.REJECT

