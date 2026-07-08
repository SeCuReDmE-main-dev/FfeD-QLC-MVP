"""AlgoQuest/Qbit Education adapter hook for FfeD-QLC."""

APP_SLUG = "ffed-qlc"
HUB_SLUG = "algoquest"


def build_learning_event_stub(artifact_ref: str, *, score: float = 93) -> dict:
    return {
        "schema": "securedme.education.student-learning-event.v1",
        "app_slug": APP_SLUG,
        "artifact_ref": artifact_ref,
        "skill_area": "ffed_qlc_reasoning",
        "difficulty_band": "beginner",
        "score": score,
        "threshold": 93,
        "attempt_count": 1,
        "blocked_reason": "",
        "next_step_hint": "Open AlgoQuest to plan the next QLC reasoning step.",
        "qbit_help_accepted": False,
        "risk_flags": [],
        "contract_version": "v1",
        "raw_secret_stored": False,
        "dry_run": True,
    }
