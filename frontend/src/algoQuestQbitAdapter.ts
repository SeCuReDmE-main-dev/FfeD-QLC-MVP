const OUTBOX_KEY = "securedme.education.algoquest.outbox.v1";

export type AlgoQuestLearningEvent = {
  schema: "securedme.education.student-learning-event.v1";
  app_slug: "ffed-qlc";
  artifact_ref: string;
  skill_area: "ffed_qlc_reasoning";
  difficulty_band: "beginner";
  score: number;
  threshold: 93;
  attempt_count: 1;
  blocked_reason: string;
  next_step_hint: string;
  qbit_help_accepted: false;
  risk_flags: string[];
  contract_version: "v1";
  raw_secret_stored: false;
  dry_run: true;
};

export function buildAlgoQuestLearningEvent(artifactRef: string, score = 93): AlgoQuestLearningEvent {
  return {
    schema: "securedme.education.student-learning-event.v1",
    app_slug: "ffed-qlc",
    artifact_ref: artifactRef,
    skill_area: "ffed_qlc_reasoning",
    difficulty_band: "beginner",
    score,
    threshold: 93,
    attempt_count: 1,
    blocked_reason: "",
    next_step_hint: "Open AlgoQuest to plan the next QLC reasoning step.",
    qbit_help_accepted: false,
    risk_flags: [],
    contract_version: "v1",
    raw_secret_stored: false,
    dry_run: true,
  };
}

export function emitAlgoQuestLearningEvent(artifactRef: string, score = 93): AlgoQuestLearningEvent {
  const event = buildAlgoQuestLearningEvent(artifactRef, score);
  const current = JSON.parse(window.localStorage.getItem(OUTBOX_KEY) || "[]") as unknown;
  const records = Array.isArray(current) ? current : [];
  window.localStorage.setItem(OUTBOX_KEY, JSON.stringify([event, ...records].slice(0, 25)));
  return event;
}

export { OUTBOX_KEY };
