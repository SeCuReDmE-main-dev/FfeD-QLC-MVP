import {
  Activity, BookOpenCheck, Boxes, CheckCircle2, Database, FlaskConical, GraduationCap,
  Languages, Play, Radar, ShieldCheck, UserRoundCheck,
} from "lucide-react";
import { type ReactNode, useEffect, useMemo, useState } from "react";
import {
  bootstrapSession, checkReadiness, createProject, createVigilReport, executeMission,
  loadCapabilities, loadLaboratories, loadPortfolio, saveTenebrisBudgets, startMission, submitDecision,
} from "./api";
import { labTitle, t } from "./i18n";
import type { Capabilities, Laboratory, Language, MissionRun, Project, Provider, Role, Session, Surface, VigilReport } from "./types";

const surfaces: Array<{ key: Surface; icon: typeof Radar; label: keyof ReturnType<typeof t> }> = [
  { key: "prerequisites", icon: BookOpenCheck, label: "prerequisites" },
  { key: "orb", icon: Boxes, label: "orb" },
  { key: "mission", icon: FlaskConical, label: "mission" },
  { key: "defense", icon: ShieldCheck, label: "defense" },
  { key: "evidence", icon: Database, label: "evidence" },
  { key: "professor", icon: GraduationCap, label: "professor" },
];

export function AlphaConsole({ orbStudio }: { orbStudio: ReactNode }) {
  const [language, setLanguage] = useState<Language>("fr");
  const [surface, setSurface] = useState<Surface>("prerequisites");
  const [ready, setReady] = useState(false);
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);
  const [role, setRole] = useState<Role>("student_adult");
  const [provider, setProvider] = useState<Provider>("codex");
  const [fingerprint, setFingerprint] = useState("learner-local-demo");
  const [session, setSession] = useState<Session | null>(null);
  const [teacherSession, setTeacherSession] = useState<Session | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [projectTitle, setProjectTitle] = useState("My geometric defense orb");
  const [labs, setLabs] = useState<Laboratory[]>([]);
  const [selectedLab, setSelectedLab] = useState("lab-01");
  const [run, setRun] = useState<MissionRun | null>(null);
  const [report, setReport] = useState<VigilReport | null>(null);
  const [portfolio, setPortfolio] = useState<Record<string, unknown> | null>(null);
  const [retryBudget, setRetryBudget] = useState(3);
  const [traceBudget, setTraceBudget] = useState(4096);
  const [budgetSaved, setBudgetSaved] = useState(false);
  const [decisionNote, setDecisionNote] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const text = t(language);
  const lab = useMemo(() => labs.find((item) => item.lab_id === selectedLab), [labs, selectedLab]);

  useEffect(() => {
    void checkReadiness().then(() => setReady(true)).catch(() => setReady(false));
    void loadCapabilities().then(setCapabilities).catch((caught: Error) => setError(caught.message));
    void loadLaboratories().then((value) => setLabs(value.laboratories)).catch((caught: Error) => setError(caught.message));
  }, []);

  async function task(key: string, action: () => Promise<void>) {
    setBusy(key); setError("");
    try { await action(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Operation failed"); }
    finally { setBusy(""); }
  }

  async function openSession() {
    await task("session", async () => {
      const value = await bootstrapSession(role, provider, fingerprint);
      setSession(value.session);
      setSurface("prerequisites");
    });
  }

  async function makeProject() {
    if (!session) return;
    await task("project", async () => {
      setProject(await createProject(session.session_id, projectTitle, "college"));
      setSurface("mission");
    });
  }

  async function beginLab() {
    if (!project) return;
    await task("start", async () => setRun(await startMission(project.project_id, selectedLab)));
  }

  async function performLab() {
    if (!run || !lab) return;
    await task("execute", async () => {
      const value = await executeMission(run.run_id, lab.allowed_action);
      setRun(value.run);
    });
  }

  async function makeReport() {
    if (!run) return;
    await task("report", async () => {
      setReport(await createVigilReport(run.run_id));
      setSurface("defense");
    });
  }

  async function openTeacherSession() {
    await task("teacher", async () => {
      const value = await bootstrapSession("teacher", provider, "teacher-local-demo");
      setTeacherSession(value.session);
    });
  }

  async function applyBudgets() {
    if (!project || !teacherSession) return;
    await task("budgets", async () => {
      await saveTenebrisBudgets(project.project_id, teacherSession.session_id, {
        retry_count: retryBudget,
        trace_steps: traceBudget,
      });
      setBudgetSaved(true);
    });
  }

  return (
    <div className="alpha-console">
      <header className="alpha-header">
        <div className="alpha-brand">
          <span className="vigil-mark"><Radar aria-hidden="true" /></span>
          <div><strong>{text.title}</strong><small>{text.subtitle}</small></div>
        </div>
        <div className="alpha-status">
          <span className={ready ? "status-good" : "status-bad"}><Activity size={15} /> {text.gateway}: {ready ? text.connected : text.disconnected}</span>
          <button type="button" onClick={() => setLanguage(language === "fr" ? "en" : language === "en" ? "es" : "fr")} title="Language">
            <Languages size={16} /> {language.toUpperCase()}
          </button>
        </div>
      </header>

      <nav className="alpha-nav" aria-label="Vigil workflow">
        {surfaces.map((item) => {
          const Icon = item.icon;
          return <button key={item.key} type="button" className={surface === item.key ? "active" : ""} onClick={() => setSurface(item.key)}>
            <Icon size={17} /><span>{text[item.label]}</span>
          </button>;
        })}
      </nav>

      {error ? <div className="alpha-error" role="alert">{error}</div> : null}

      {surface === "orb" ? <div className="embedded-orb">{orbStudio}</div> : null}
      {surface === "prerequisites" ? <section className="alpha-page">
        <div className="page-heading"><span>01 / GATEWAY</span><h1>{text.prerequisites}</h1><p>{text.noHistory}</p></div>
        <div className="alpha-grid two">
          <div className="alpha-panel">
            <h2>{text.start}</h2>
            <label>{text.fingerprint}<input value={fingerprint} onChange={(event) => setFingerprint(event.target.value)} /></label>
            <label>{text.role}<select value={role} onChange={(event) => setRole(event.target.value as Role)}><option value="student_adult">{text.adult}</option><option value="student_minor">{text.minor}</option></select></label>
            <label>{text.provider}<select value={provider} onChange={(event) => setProvider(event.target.value as Provider)}><option value="codex">Codex / OpenAI</option><option value="gemini">Antigravity / Gemini</option></select></label>
            <button className="primary-command" type="button" disabled={!ready || !capabilities?.public_stateful_enabled || busy === "session"} onClick={openSession}><UserRoundCheck size={17} />{busy === "session" ? "..." : text.start}</button>
            {capabilities && !capabilities.public_stateful_enabled ? <p className="alpha-boundary-note" role="status">Pre-alpha — active public development. Stateful classroom workflows await the verified identity adapter.</p> : null}
          </div>
          <div className="alpha-panel boundary-panel"><h2>{text.boundary}</h2><ul><li>{text.synthetic}</li><li>{text.noShell}</li><li>{text.teacherOwns}</li><li>{text.geometryClaim}</li></ul></div>
        </div>
        {session ? <div className="session-strip"><CheckCircle2 size={18} /> {session.role} / {session.provider_route} / {session.session_id}</div> : null}
        {session ? <div className="alpha-panel project-form"><h2>{text.project}</h2><input value={projectTitle} onChange={(event) => setProjectTitle(event.target.value)} /><button type="button" onClick={makeProject} disabled={busy === "project"}>{text.create}</button></div> : null}
      </section> : null}

      {surface === "mission" ? <section className="alpha-page">
        <div className="page-heading"><span>03 / RED + BLUE</span><h1>{text.labs}</h1><p>{project ? `${project.title} / ${project.level}` : text.createFirst}</p></div>
        <div className="lab-layout"><div className="lab-list">{labs.map((item) => <button key={item.lab_id} className={selectedLab === item.lab_id ? "selected" : ""} type="button" onClick={() => setSelectedLab(item.lab_id)}><span>{item.lab_id}</span><strong>{labTitle(language, item.lab_id, item.title)}</strong><small>{item.difficulty} / {item.duration_minutes} min</small></button>)}</div>
        <div className="alpha-panel mission-console"><div className="console-title"><FlaskConical size={19} /><span>{lab ? labTitle(language, lab.lab_id, lab.title) : ""}</span><b>{run?.state ?? "not_started"}</b></div><p>{lab?.objective}</p><dl><dt>{text.allowed}</dt><dd>{lab?.allowed_action}</dd><dt>{text.fixture}</dt><dd>synthetic-env-basic</dd><dt>{text.review}</dt><dd>{lab?.professor_review_required ? text.teacherRequired : text.evidenceGate}</dd></dl><div className="command-row"><button type="button" disabled={!project || busy === "start"} onClick={beginLab}><Play size={16} />{text.run}</button><button type="button" disabled={!run || run.state === "evidence_ready" || busy === "execute"} onClick={performLab}>{text.execute}</button><button type="button" disabled={run?.state !== "evidence_ready" || busy === "report"} onClick={makeReport}>{text.report}</button></div></div></div>
      </section> : null}

      {surface === "defense" ? <section className="alpha-page"><div className="page-heading"><span>04 / VIGIL</span><h1>{text.defense}</h1><p>{text.limitation}</p></div>{report ? <div className="report-grid">{(["observation", "mechanism", "attack", "limitation", "decision", "safe_next_action"] as const).map((field) => <article key={field}><span>{field.replaceAll("_", " ")}</span><p>{String(report[field])}</p></article>)}</div> : <EmptyState title={text.noReport} detail={text.finishFirst} />}</section> : null}

      {surface === "evidence" ? <section className="alpha-page"><div className="page-heading"><span>05 / PORTFOLIO</span><h1>{text.proof}</h1><p>{text.portfolioSummary}</p></div><button className="primary-command" type="button" disabled={!project} onClick={() => project && task("portfolio", async () => setPortfolio(await loadPortfolio(project.project_id)))}><Database size={17} />{text.download}</button>{portfolio ? <pre className="portfolio-json">{JSON.stringify(portfolio, null, 2)}</pre> : null}</section> : null}

      {surface === "professor" ? <section className="alpha-page"><div className="page-heading"><span>06 / HUMAN REVIEW</span><h1>{text.professor}</h1><p>{text.vigilDecides}</p></div><div className="alpha-grid two"><div className="alpha-panel"><button type="button" onClick={openTeacherSession} disabled={!capabilities?.public_stateful_enabled || busy === "teacher"}>{text.openTeacher}</button>{teacherSession ? <div className="session-strip"><CheckCircle2 size={18} />{teacherSession.session_id}</div> : null}<textarea aria-label={text.note} placeholder={text.note} value={decisionNote} onChange={(event) => setDecisionNote(event.target.value)} /><div className="decision-row">{["accept", "suspend", "revise", "reject"].map((decision) => <button key={decision} type="button" disabled={!teacherSession || !report} onClick={() => teacherSession && report && task("decision", async () => { await submitDecision(report.report_id, teacherSession.session_id, decision, decisionNote); })}>{decision}</button>)}</div></div><div className="alpha-panel"><h2>{text.limits}</h2><p>{text.limitsHelp}</p><label>{text.retries}<input type="number" min="1" max="3" value={retryBudget} onChange={(event) => { setRetryBudget(Number(event.target.value)); setBudgetSaved(false); }} /></label><label>{text.trace}<input type="number" min="1" max="4096" value={traceBudget} onChange={(event) => { setTraceBudget(Number(event.target.value)); setBudgetSaved(false); }} /></label><button type="button" disabled={!teacherSession || !project || busy === "budgets"} onClick={applyBudgets}>{text.apply}</button>{budgetSaved ? <div className="session-strip"><CheckCircle2 size={18} />{text.enforced}</div> : null}</div></div></section> : null}
    </div>
  );
}

function EmptyState({ title, detail }: { title: string; detail: string }) {
  return <div className="alpha-panel empty-state"><ShieldCheck size={30} /><strong>{title}</strong><span>{detail}</span></div>;
}
