export const CONTRACT_IDS = [
  "securedme.education.session-role.v1",
  "ffed.qlc.fixture.v1",
  "ffed.qlc.geometry_trace.v1",
  "ffed.qlc.orb_public.v1",
  "ffed.qlc.orb_project.v1",
  "ffed.qlc.mission_run.v1",
  "ffed.qlc.vigil_report.v1",
  "ffed.qlc.professor_decision.v1",
  "ffed.qlc.learning_evidence.v1",
  "ffed.qlc.portfolio_case_study.v1",
] as const;

const forbidden = new Set([
  ".env", "api_key", "browser_session", "client_secret", "cookie", "oauth_token", "password",
  "raw_chat_log", "raw_prompt", "roster", "secret", "session_cookie", "student_email",
  "student_id", "student_name", "token",
]);

export function assertCredentialBlind(value: unknown): void {
  walk(value);
}

function walk(value: unknown): void {
  if (Array.isArray(value)) {
    value.forEach(walk);
    return;
  }
  if (!value || typeof value !== "object") return;
  for (const [key, nested] of Object.entries(value)) {
    const normalized = key.toLowerCase();
    if (forbidden.has(normalized) || normalized.startsWith("raw_")) {
      if (["raw_secret_stored", "raw_payload_embedded", "raw_payload_exposed", "raw_values_printed", "secret_values_exposed"].includes(normalized) && nested === false) continue;
      throw new Error(`forbidden field: ${key}`);
    }
    walk(nested);
  }
}
