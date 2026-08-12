"""Narrow identity seam owned by the separate identity implementation task."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class IdentityIntegrationPending(PermissionError):
    code = "IDENTITY_INTEGRATION_PENDING"


@dataclass(frozen=True)
class VerifiedIdentity:
    subject_ref: str
    role: str
    synthetic: bool = False


class IdentityVerifier(Protocol):
    @property
    def ready(self) -> bool: ...

    def verify(self, *, subject_ref: str, role: str, action: str) -> VerifiedIdentity: ...


class PendingIdentityVerifier:
    @property
    def ready(self) -> bool:
        return False

    def verify(self, *, subject_ref: str, role: str, action: str) -> VerifiedIdentity:
        del subject_ref, role, action
        raise IdentityIntegrationPending("verified identity adapter is not available")


class SyntheticTestIdentityVerifier:
    """Explicit dependency for tests; never selected from the public environment."""

    @property
    def ready(self) -> bool:
        return True

    def verify(self, *, subject_ref: str, role: str, action: str) -> VerifiedIdentity:
        if not subject_ref or role not in {"student_minor", "student_adult", "teacher"} or not action:
            raise IdentityIntegrationPending("synthetic test identity is incomplete")
        return VerifiedIdentity(subject_ref=f"synthetic:{subject_ref}", role=role, synthetic=True)
