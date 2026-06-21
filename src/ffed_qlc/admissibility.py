from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AdmDecision(str, Enum):
    ACCEPT = "accept"
    SUSPEND = "suspend"
    REJECT = "reject"


@dataclass(frozen=True)
class Evidence:
    """Small public evidence carrier for the MVP."""

    source_id: str
    source_type: str
    trust_score: float
    has_provenance: bool
    claim_scope: str = "bounded_software"


def evaluate_evidence(evidence: Evidence) -> AdmDecision:
    """Evaluate a source through a minimal public admissibility rule.

    This is intentionally simple. It models a public-safe gate:
    provenance first, bounded scope second, trust score third.
    """

    if evidence.claim_scope in {"biological_proof", "clinical_claim", "security_certification"}:
        return AdmDecision.REJECT

    if not evidence.has_provenance:
        return AdmDecision.SUSPEND

    if evidence.trust_score >= 0.75:
        return AdmDecision.ACCEPT

    if evidence.trust_score >= 0.40:
        return AdmDecision.SUSPEND

    return AdmDecision.REJECT

