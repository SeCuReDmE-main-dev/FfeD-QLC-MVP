export type Language = "fr" | "en" | "es";
export type Surface = "prerequisites" | "orb" | "mission" | "defense" | "evidence" | "professor";
export type Role = "student_minor" | "student_adult" | "teacher";
export type Provider = "codex" | "gemini";

export type Session = {
  session_id: string;
  fingerprint_ref: string;
  role: Role;
  surface: "student" | "teacher";
  provider_route: Provider;
};

export type Project = {
  schema: string;
  project_id: string;
  session_id: string;
  title: string;
  level: string;
  status: string;
};

export type Laboratory = {
  lab_id: string;
  title: string;
  difficulty: string;
  allowed_action: string;
  objective: string;
  duration_minutes: number;
  prerequisites: string[];
  proof_required: boolean;
  professor_review_required: boolean;
};

export type MissionRun = {
  schema: string;
  run_id: string;
  project_id: string;
  lab_id: string;
  state: string;
  attempt_count: number;
  evidence_ref?: string;
};

export type VigilReport = {
  schema: string;
  report_id: string;
  run_id: string;
  observation: string;
  mechanism: string;
  attack: string;
  evidence: { sha256: string; lab_id: string };
  limitation: string;
  decision: string;
  safe_next_action: string;
  provider_route: string;
  human_review_required: boolean;
};

