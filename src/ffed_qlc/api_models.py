"""Versioned request models for the FfeD-QLC API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .cpai_yolo import DEFAULT_CPAI_URL


class LatticeRequest(BaseModel):
    engine: str = Field(default="inflation", pattern="^(inflation|cut_project)$")
    target_tile_count: int = Field(default=8, ge=1, le=200)
    depth: int = Field(default=3, ge=0, le=8)
    seed: str = Field(default="api", min_length=1, max_length=120)


class TrainingPlanRequest(BaseModel):
    cpai_url: str = DEFAULT_CPAI_URL
    model_name: str = Field(default="ffed-qlc-yolo", min_length=1, max_length=120)
    dataset_name: str = Field(default="ffed-qlc-metadata-only", min_length=1, max_length=120)
    epochs: int = Field(default=10, ge=1, le=1000)
    require_confirmation: bool = True


class SessionBootstrapRequest(BaseModel):
    role: str = Field(pattern="^(student_minor|student_adult|teacher)$")
    fingerprint_ref: str = Field(min_length=8, max_length=128)
    consent_scope: str = Field(default="tool", pattern="^(tool|suite)$")
    provider_route: str = Field(default="codex", pattern="^(codex|gemini)$")
    has_prior_metrics: bool = False


class ProjectRequest(BaseModel):
    session_id: str = Field(min_length=8, max_length=128)
    title: str = Field(min_length=1, max_length=120)
    level: str = Field(default="college", pattern="^(secondary_5|college|university)$")


class MissionStartRequest(BaseModel):
    project_id: str = Field(min_length=8, max_length=128)
    lab_id: str = Field(pattern="^lab-0[1-9]$")


class MissionExecuteRequest(BaseModel):
    action: str = Field(min_length=1, max_length=80)
    fixture_id: str | None = Field(default=None, max_length=120)
    idempotency_key: str | None = Field(default=None, min_length=16, max_length=120)


class VigilRequest(BaseModel):
    handoff_target: str | None = Field(default=None, pattern="^(codex|gemini)$")


class ProfessorDecisionRequest(BaseModel):
    report_id: str = Field(min_length=8, max_length=128)
    teacher_session_id: str = Field(min_length=8, max_length=128)
    decision: str = Field(pattern="^(accept|suspend|reject|revise)$")
    note: str = Field(default="", max_length=1000)


class ProfessorBudgetRequest(BaseModel):
    project_id: str = Field(min_length=8, max_length=128)
    teacher_session_id: str = Field(min_length=8, max_length=128)
    budgets: dict[str, int]


class NativeHandoffRequest(BaseModel):
    target: str = Field(pattern="^(codex|gemini)$")
    capability: str = Field(min_length=1, max_length=80)
    consent_receipt_id: str = Field(min_length=1, max_length=120)
    evidence_refs: list[str] = Field(min_length=1, max_length=8)
    deadline_seconds: int = Field(default=30, ge=1, le=120)


class LegacyHandoffRequest(BaseModel):
    project_id: str = Field(min_length=1, max_length=128)
    target_slug: str = Field(min_length=1, max_length=120)
    mascot: str = Field(min_length=1, max_length=80)
    metric_names: list[str] = Field(default_factory=list, max_length=8)


class FQLC2RoundtripRequest(BaseModel):
    fixture_id: str = Field(default="synthetic-env-basic", pattern="^synthetic-[a-z0-9-]+$")
    recipient_count: int = Field(default=1, ge=1, le=3)
    signed: bool = False


class FQLC2InspectRequest(BaseModel):
    container_base64: str = Field(min_length=1, max_length=1_500_000)
