import type { Capabilities, Laboratory, MissionRun, Project, Provider, Role, Session, VigilReport } from "./types";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "content-type": "application/json" },
    ...init,
  });
  const payload = (await response.json()) as T & { detail?: unknown };
  if (!response.ok) {
    const detail = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail ?? payload);
    throw new Error(detail);
  }
  return payload;
}

export async function checkReadiness() {
  return api<{ status: string; gateway: { transport: string }; storage: string }>("/api/v1/health/ready");
}

export async function loadCapabilities() {
  return api<Capabilities>("/api/v1/capabilities");
}

export async function bootstrapSession(role: Role, provider: Provider, fingerprint: string) {
  return api<{ session: Session; diagnostic: { starting_lab: string; absence_is_failure: boolean } }>(
    "/api/v1/session/bootstrap",
    { method: "POST", body: JSON.stringify({ role, provider_route: provider, fingerprint_ref: fingerprint }) },
  );
}

export async function loadLaboratories() {
  return api<{ laboratories: Laboratory[] }>("/api/v1/laboratories");
}

export async function createProject(sessionId: string, title: string, level: string) {
  return api<Project>("/api/v1/projects", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, title, level }),
  });
}

export async function startMission(projectId: string, labId: string) {
  return api<MissionRun>("/api/v1/missions", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, lab_id: labId }),
  });
}

export async function executeMission(runId: string, action: string) {
  return api<{ run: MissionRun; evidence: Record<string, unknown>; artifact: { sha256: string } }>(
    `/api/v1/missions/${runId}/actions`,
    { method: "POST", body: JSON.stringify({ action, fixture_id: "synthetic-env-basic" }) },
  );
}

export async function createVigilReport(runId: string) {
  return api<VigilReport>(`/api/v1/missions/${runId}/vigil`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

export async function submitDecision(reportId: string, teacherSessionId: string, decision: string, note: string) {
  return api<Record<string, unknown>>("/api/v1/professor/decisions", {
    method: "POST",
    body: JSON.stringify({ report_id: reportId, teacher_session_id: teacherSessionId, decision, note }),
  });
}

export async function saveTenebrisBudgets(
  projectId: string,
  teacherSessionId: string,
  budgets: Record<string, number>,
) {
  return api<{ project_id: string; budgets: Record<string, number>; maximums: Record<string, number> }>(
    "/api/v1/professor/budgets",
    {
      method: "POST",
      body: JSON.stringify({ project_id: projectId, teacher_session_id: teacherSessionId, budgets }),
    },
  );
}

export async function loadPortfolio(projectId: string) {
  return api<Record<string, unknown>>(`/api/v1/portfolio/${projectId}`);
}
