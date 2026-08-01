import {
  Box,
  Brain,
  Database,
  Download,
  FileJson,
  Filter,
  GraduationCap,
  Network,
  Play,
  RotateCcw,
  Save,
  SearchCheck,
  ShieldCheck,
  SlidersHorizontal,
  Waypoints,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { emitAlgoQuestLearningEvent } from "./algoQuestQbitAdapter";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

type TabKey =
  | "lattice"
  | "gate"
  | "source"
  | "cpai"
  | "handoff"
  | "manifest"
  | "template";

type TileMetadata = {
  tile_id: string;
  tile_type: "thin" | "thick";
  vertices: [number, number][];
  centroid: [number, number];
  area: number;
  bounding_box: [number, number, number, number];
  matching_profile: {
    edge_signatures: string[];
    orientation_degrees: number;
  };
};

type LatticeBuildResponse = {
  schema: string;
  patch_metadata: {
    tile_count: number;
    patch_fingerprint: string;
    tile_type_counts: Record<string, number>;
    adjacency_count: number;
  };
  tiles: TileMetadata[];
};

type ClassificationResponse = {
  classifications: Array<{
    tile_id: string;
    Adm: string;
    C_phi: number;
    reason_codes: string[];
  }>;
};

type ValidationResponse = {
  admissions: Array<{
    tile_id: string;
    Adm: string;
    T_tile: number;
    dF_tile: number | null;
    F_tile: number;
    reason_codes: string[];
  }>;
  ledger: {
    accepted_count: number;
    entry_count: number;
    raw_tif_exported: boolean;
  };
};

type SourceGraphResponse = {
  source_count: number;
  source_ids: string[];
  graph: {
    nodes: Array<Record<string, unknown>>;
    edges: Array<Record<string, unknown>>;
  };
};

type OrbResponse = {
  schema: string;
  orb_id: string;
  accepted_tile_ids: string[];
  raw_media_embedded: boolean;
};

type CpaiStatus = {
  status?: string;
  dry_run?: boolean;
  module?: string;
  training_started?: boolean;
};

type UtilityTheme = "night" | "day";
type UtilityLanguage = "en" | "fr" | "es";
type UtilityAccess = "base" | "autism-calm" | "adhd-sprint" | "deep-work";

const LANGUAGE_ORDER: UtilityLanguage[] = ["en", "fr", "es"];
const LANGUAGE_LABELS: Record<UtilityLanguage, string> = {
  en: "Language: EN",
  fr: "Langue : FR",
  es: "Idioma: ES",
};

const ACCESS_ORDER: UtilityAccess[] = ["base", "autism-calm", "adhd-sprint", "deep-work"];
const ACCESS_LABELS: Record<UtilityAccess, string> = {
  base: "Access: Base",
  "autism-calm": "Access: Autism Calm",
  "adhd-sprint": "Access: ADHD Sprint",
  "deep-work": "Access: Deep Work",
};

function UtilityDock() {
  const [language, setLanguage] = useState<UtilityLanguage>(() => {
    const saved = localStorage.getItem("securedme.ffedqlc.language") as UtilityLanguage | null;
    return saved && LANGUAGE_ORDER.includes(saved) ? saved : "en";
  });
  const [theme, setTheme] = useState<UtilityTheme>(() =>
    localStorage.getItem("securedme.ffedqlc.theme") === "night" ? "night" : "day",
  );
  const [access, setAccess] = useState<UtilityAccess>(() => {
    const saved = localStorage.getItem("securedme.ffedqlc.access") as UtilityAccess | null;
    return saved && ACCESS_ORDER.includes(saved) ? saved : "base";
  });

  useEffect(() => {
    localStorage.setItem("securedme.ffedqlc.language", language);
    document.documentElement.lang = language;
    document.documentElement.dataset.lang = language;
  }, [language]);

  useEffect(() => {
    localStorage.setItem("securedme.ffedqlc.theme", theme);
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    localStorage.setItem("securedme.ffedqlc.access", access);
    document.documentElement.dataset.accessProfile = access;
  }, [access]);

  const nextLanguage = () => {
    const currentIndex = LANGUAGE_ORDER.indexOf(language);
    setLanguage(LANGUAGE_ORDER[(currentIndex + 1) % LANGUAGE_ORDER.length]);
  };

  const nextAccess = () => {
    const currentIndex = ACCESS_ORDER.indexOf(access);
    setAccess(ACCESS_ORDER[(currentIndex + 1) % ACCESS_ORDER.length]);
  };

  return (
    <aside className="utility-dock" aria-label="SecuredMe display and accessibility preferences">
      <button
        type="button"
        onClick={nextLanguage}
        className="utility-dock-button"
        aria-label={`Language preference: ${language.toUpperCase()}. Activate for next language.`}
      >
        {LANGUAGE_LABELS[language]}
      </button>
      <button
        type="button"
        onClick={() => setTheme((current) => (current === "night" ? "day" : "night"))}
        className="utility-dock-button"
        aria-label={`Theme: ${theme}. Activate to switch theme.`}
      >
        Theme: {theme === "night" ? "Night" : "Day"}
      </button>
      <button
        type="button"
        onClick={nextAccess}
        className="utility-dock-button"
        aria-label={`Accessibility profile: ${ACCESS_LABELS[access]}. Activate for next profile.`}
      >
        {ACCESS_LABELS[access]}
      </button>
      <a
        href="https://securedme.ca/pay/"
        target="_blank"
        rel="noopener noreferrer"
        className="utility-dock-button utility-dock-support"
      >
        Support SecuredMe
      </a>
    </aside>
  );
}

const tabs: Array<{ key: TabKey; label: string; icon: typeof Box }> = [
  { key: "lattice", label: "Lattice", icon: Box },
  { key: "gate", label: "Plithogenic Gate", icon: ShieldCheck },
  { key: "source", label: "Source Graph", icon: Network },
  { key: "cpai", label: "YOLO / CPAI", icon: SearchCheck },
  { key: "handoff", label: "Education Handoff", icon: GraduationCap },
  { key: "manifest", label: "QLC Manifest", icon: FileJson },
  { key: "template", label: "Template", icon: Database },
];

export function App() {
  const [activeTab, setActiveTab] = useState<TabKey>("lattice");
  const [engine, setEngine] = useState<"inflation" | "cut_project">("inflation");
  const [targetTileCount, setTargetTileCount] = useState(21);
  const [zoom, setZoom] = useState(1);
  const [filterAcceptedOnly, setFilterAcceptedOnly] = useState(false);
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lattice, setLattice] = useState<LatticeBuildResponse | null>(null);
  const [classifications, setClassifications] = useState<ClassificationResponse | null>(null);
  const [validation, setValidation] = useState<ValidationResponse | null>(null);
  const [sources, setSources] = useState<SourceGraphResponse | null>(null);
  const [orb, setOrb] = useState<OrbResponse | null>(null);
  const [template, setTemplate] = useState<Record<string, unknown> | null>(null);
  const [cpai, setCpai] = useState<Record<string, CpaiStatus>>({});
  const [selectedTileId, setSelectedTileId] = useState<string | null>(null);
  const [algoQuestStatus, setAlgoQuestStatus] = useState("AlgoQuest event pending");

  const request = useMemo(
    () => ({
      engine,
      target_tile_count: targetTileCount,
      depth: Math.min(8, Math.max(0, Math.ceil(Math.log2(targetTileCount)))),
      seed: "frontend",
    }),
    [engine, targetTileCount],
  );

  const selectedTile = useMemo(
    () => lattice?.tiles.find((tile) => tile.tile_id === selectedTileId) || lattice?.tiles[0],
    [lattice, selectedTileId],
  );

  const visibleTiles = useMemo(() => {
    if (!lattice) return [];
    if (!filterAcceptedOnly || !validation) return lattice.tiles;
    const accepted = new Set(
      validation.admissions.filter((item) => item.Adm === "accept").map((item) => item.tile_id),
    );
    return lattice.tiles.filter((tile) => accepted.has(tile.tile_id));
  }, [filterAcceptedOnly, lattice, validation]);

  useEffect(() => {
    void fetchSources();
    void buildLattice();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function api<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`, {
      headers: { "content-type": "application/json" },
      ...options,
    });
    if (!response.ok) {
      throw new Error(`${response.status} ${response.statusText}`);
    }
    return (await response.json()) as T;
  }

  async function runAction<T>(key: string, fn: () => Promise<T>): Promise<T | null> {
    setLoading(key);
    setError(null);
    try {
      return await fn();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "request failed");
      return null;
    } finally {
      setLoading(null);
    }
  }

  async function fetchSources() {
    const result = await runAction("sources", () => api<SourceGraphResponse>("/api/source-functions"));
    if (result) setSources(result);
  }

  async function buildLattice() {
    const result = await runAction("build", () =>
      api<LatticeBuildResponse>("/api/lattice/build", {
        method: "POST",
        body: JSON.stringify(request),
      }),
    );
    if (result) {
      setLattice(result);
      setSelectedTileId(result.tiles[0]?.tile_id ?? null);
    }
  }

  async function classifySources() {
    const result = await runAction("classify", () =>
      api<ClassificationResponse>("/api/lattice/classify", {
        method: "POST",
        body: JSON.stringify(request),
      }),
    );
    if (result) setClassifications(result);
  }

  async function validateLattice() {
    const result = await runAction("validate", () =>
      api<ValidationResponse>("/api/lattice/validate", {
        method: "POST",
        body: JSON.stringify(request),
      }),
    );
    if (result) setValidation(result);
  }

  async function buildOrb() {
    const result = await runAction("orb", () =>
      api<OrbResponse>("/api/orbs/build", {
        method: "POST",
        body: JSON.stringify(request),
      }),
    );
    if (result) setOrb(result);
  }

  async function exportTemplate() {
    const result = await runAction("template", () =>
      api<Record<string, unknown>>("/api/export/lattice-template", { method: "POST" }),
    );
    if (result) setTemplate(result);
    downloadJson("ffed-qlc-template.json", result ?? {});
  }

  async function probeCpai(kind: "status" | "yolo" | "training") {
    const path =
      kind === "status"
        ? "/api/cpai/status"
        : kind === "yolo"
          ? "/api/cpai/yolo/probe"
          : "/api/cpai/yolo/training/probe";
    const result = await runAction(kind, () => api<CpaiStatus>(path));
    if (result) setCpai((current) => ({ ...current, [kind]: result }));
  }

  async function planTraining() {
    const result = await runAction("trainingPlan", () =>
      api<CpaiStatus>("/api/cpai/yolo/training/plan", {
        method: "POST",
        body: JSON.stringify({ model_name: "ffed-qlc-yolo", dataset_name: "ffed-qlc", epochs: 10 }),
      }),
    );
    if (result) setCpai((current) => ({ ...current, trainingPlan: result }));
  }

  function downloadJson(filename: string, payload: unknown) {
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  function saveLayout() {
    localStorage.setItem(
      "ffed-qlc-layout",
      JSON.stringify({ engine, targetTileCount, zoom, filterAcceptedOnly }),
    );
  }

  function sendPatchToAlgoQuest() {
    if (!lattice) {
      return;
    }
    const fingerprint = lattice.patch_metadata.patch_fingerprint.slice(0, 16);
    const event = emitAlgoQuestLearningEvent(`ffed-qlc:lattice:${fingerprint}`, 93);
    setAlgoQuestStatus(`AlgoQuest event ready: ${event.artifact_ref}`);
  }

  return (
    <div className="app-shell">
      <aside className="sidebar" aria-label="Source function profiles">
        <div className="brand-block">
          <Waypoints size={24} aria-hidden="true" />
          <div>
            <h1>Penrose QLC Lattice Workbench</h1>
            <p>pre-alpha research surface</p>
          </div>
        </div>
        <div className="source-summary">
          <span>Source functions</span>
          <strong>{sources?.source_count ?? 0}</strong>
        </div>
        <div className="source-list">
          {(sources?.source_ids ?? []).map((sourceId) => (
            <button key={sourceId} className="source-pill" type="button" title="Function provenance id">
              <Network size={14} aria-hidden="true" />
              {sourceId}
            </button>
          ))}
        </div>

        <div className="stitch-sidebar-card">
          <div className="stitch-card-header">
            <div>
              <span className={`stitch-live-dot${lattice || validation ? "" : " is-idle"}`}></span>
              <span>LATTICE TELEMETRY</span>
            </div>
            <span>{lattice || validation ? "LIVE" : "IDLE"}</span>
          </div>
          <div className="stitch-metrics-compact">
            <div className="stitch-metric-item">
              <span>Tiles</span>
              <strong>{lattice?.patch_metadata.tile_count ?? 0}</strong>
            </div>
            <div className="stitch-metric-item">
              <span>Accepted</span>
              <strong>{validation?.ledger.accepted_count ?? 0}</strong>
            </div>
            <div className="stitch-metric-item">
              <span>Engine</span>
              <strong>{engine}</strong>
            </div>
            <div className="stitch-metric-item">
              <span>Status</span>
              <strong>{validation ? "VALIDATED" : lattice ? "BUILT" : "IDLE"}</strong>
            </div>
          </div>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <nav className="tabs" aria-label="Workbench tabs">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.key}
                  className={activeTab === tab.key ? "tab active" : "tab"}
                  type="button"
                  onClick={() => setActiveTab(tab.key)}
                  title={tab.label}
                >
                  <Icon size={16} aria-hidden="true" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
          <div className="status-strip">
            <span>{lattice?.patch_metadata.tile_count ?? 0} tiles</span>
            <span>{validation?.ledger.accepted_count ?? 0} accepted</span>
            <span>{engine}</span>
          </div>
        </header>

        <section className="control-band" aria-label="Lattice controls">
          <label>
            Engine
            <select value={engine} onChange={(event) => setEngine(event.target.value as typeof engine)}>
              <option value="inflation">Inflation</option>
              <option value="cut_project">Cut-project</option>
            </select>
          </label>
          <label>
            Tiles
            <input
              min={1}
              max={200}
              type="number"
              value={targetTileCount}
              onChange={(event) => setTargetTileCount(Number(event.target.value))}
            />
          </label>
          <ActionButton icon={Play} label="Build Penrose Patch" loading={loading === "build"} onClick={buildLattice} />
          <ActionButton
            icon={Brain}
            label="Classify Sources"
            loading={loading === "classify"}
            onClick={classifySources}
            disabled={!lattice}
          />
          <ActionButton
            icon={ShieldCheck}
            label="Validate Lattice"
            loading={loading === "validate"}
            onClick={validateLattice}
            disabled={!lattice}
          />
          <ActionButton
            icon={Database}
            label="Build Orb"
            loading={loading === "orb"}
            onClick={buildOrb}
            disabled={!validation}
          />
          <ActionButton icon={Download} label="Export Template" loading={loading === "template"} onClick={exportTemplate} />
          <ActionButton
            icon={GraduationCap}
            label="Send Patch to AlgoQuest"
            onClick={sendPatchToAlgoQuest}
            disabled={!lattice}
          />
          <span className="algoquest-status" role="status">{algoQuestStatus}</span>
        </section>

        {error ? <div className="error-banner">{error}</div> : null}

        <div className="work-grid">
          <section className="canvas-panel" aria-label="Lattice canvas">
            <div className="panel-toolbar">
              <IconButton icon={ZoomIn} label="Zoom in" onClick={() => setZoom((value) => Math.min(2.5, value + 0.15))} />
              <IconButton icon={ZoomOut} label="Zoom out" onClick={() => setZoom((value) => Math.max(0.5, value - 0.15))} />
              <IconButton icon={RotateCcw} label="Reset view" onClick={() => setZoom(1)} />
              <IconButton icon={Filter} label="Filter accepted" onClick={() => setFilterAcceptedOnly((value) => !value)} />
              <IconButton icon={Save} label="Save layout" onClick={saveLayout} />
              <IconButton
                icon={Download}
                label="Download graph snapshot"
                onClick={() => downloadJson("ffed-qlc-lattice.json", lattice ?? {})}
                disabled={!lattice}
              />
            </div>
            <LatticeCanvas tiles={visibleTiles} zoom={zoom} selectedTileId={selectedTile?.tile_id} onSelect={setSelectedTileId} />
          </section>

          <aside className="inspector" aria-label="Inspector">
            <h2>{activeTabLabel(activeTab)}</h2>
            {activeTab === "lattice" ? <TileInspector tile={selectedTile} lattice={lattice} /> : null}
            {activeTab === "gate" ? <GateInspector classifications={classifications} validation={validation} /> : null}
            {activeTab === "source" ? <SourceInspector sources={sources} /> : null}
            {activeTab === "cpai" ? (
              <CpaiInspector cpai={cpai} onProbe={probeCpai} onPlanTraining={planTraining} loading={loading} />
            ) : null}
            {activeTab === "handoff" ? <HandoffInspector /> : null}
            {activeTab === "manifest" ? <ManifestInspector lattice={lattice} orb={orb} /> : null}
            {activeTab === "template" ? <TemplateInspector template={template} /> : null}
          </aside>
        </div>

        <section className="ledger" aria-label="Evidence ledger">
          <h2>Evidence Ledger</h2>
          <div className="ledger-grid">
            {(validation?.admissions ?? []).slice(0, 12).map((item) => (
              <button key={item.tile_id} type="button" className={`ledger-row ${item.Adm}`} onClick={() => setSelectedTileId(item.tile_id)}>
                <span>{item.tile_id}</span>
                <strong>{item.Adm}</strong>
                <small>T {item.T_tile.toFixed(2)} / dF {item.dF_tile?.toFixed(2) ?? "suspend"} / F {item.F_tile.toFixed(2)}</small>
              </button>
            ))}
          </div>
        </section>
      </main>
      <UtilityDock />
    </div>
  );
}

function ActionButton({
  icon: Icon,
  label,
  loading,
  disabled,
  onClick,
}: {
  icon: typeof Play;
  label: string;
  loading?: boolean;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button className="action-button" type="button" onClick={onClick} disabled={disabled || loading} title={label}>
      <Icon size={16} aria-hidden="true" />
      <span>{loading ? "Working" : label}</span>
    </button>
  );
}

function IconButton({
  icon: Icon,
  label,
  disabled,
  onClick,
}: {
  icon: typeof ZoomIn;
  label: string;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button className="icon-button" type="button" onClick={onClick} disabled={disabled} title={label} aria-label={label}>
      <Icon size={17} aria-hidden="true" />
    </button>
  );
}

function LatticeCanvas({
  tiles,
  zoom,
  selectedTileId,
  onSelect,
}: {
  tiles: TileMetadata[];
  zoom: number;
  selectedTileId?: string;
  onSelect: (tileId: string) => void;
}) {
  const bounds = useMemo(() => {
    if (!tiles.length) return { minX: 0, minY: 0, width: 10, height: 10 };
    const xs = tiles.flatMap((tile) => tile.vertices.map((point) => point[0]));
    const ys = tiles.flatMap((tile) => tile.vertices.map((point) => point[1]));
    const minX = Math.min(...xs);
    const minY = Math.min(...ys);
    return { minX, minY, width: Math.max(1, Math.max(...xs) - minX), height: Math.max(1, Math.max(...ys) - minY) };
  }, [tiles]);

  const scale = 46 * zoom;
  const viewWidth = Math.max(420, bounds.width * scale + 70);
  const viewHeight = Math.max(320, bounds.height * scale + 70);

  return (
    <svg className="lattice-svg" viewBox={`0 0 ${viewWidth} ${viewHeight}`} role="img" aria-label="Penrose rhombus lattice">
      <rect width={viewWidth} height={viewHeight} rx="6" />
      {tiles.map((tile) => {
        const points = tile.vertices
          .map(([x, y]) => `${(x - bounds.minX) * scale + 32},${(y - bounds.minY) * scale + 32}`)
          .join(" ");
        return (
          <polygon
            key={tile.tile_id}
            points={points}
            className={`${tile.tile_type} ${tile.tile_id === selectedTileId ? "selected" : ""}`}
            onClick={() => onSelect(tile.tile_id)}
          />
        );
      })}
    </svg>
  );
}

function TileInspector({ tile, lattice }: { tile?: TileMetadata; lattice: LatticeBuildResponse | null }) {
  if (!tile) return <p className="muted">Build a patch to inspect tile variables.</p>;
  return (
    <dl className="kv">
      <dt>Tile</dt>
      <dd>{tile.tile_id}</dd>
      <dt>Type</dt>
      <dd>{tile.tile_type}</dd>
      <dt>Area</dt>
      <dd>{tile.area.toFixed(4)}</dd>
      <dt>Orientation</dt>
      <dd>{tile.matching_profile.orientation_degrees.toFixed(2)}</dd>
      <dt>Patch</dt>
      <dd>{lattice?.patch_metadata.patch_fingerprint.slice(0, 16)}</dd>
    </dl>
  );
}

function GateInspector({ classifications, validation }: { classifications: ClassificationResponse | null; validation: ValidationResponse | null }) {
  return (
    <div className="stack">
      <Metric label="Classified" value={classifications?.classifications.length ?? 0} />
      <Metric label="Accepted" value={validation?.ledger.accepted_count ?? 0} />
      <Metric label="Raw T/I/F" value={validation?.ledger.raw_tif_exported ? "blocked" : "absent"} />
    </div>
  );
}

function SourceInspector({ sources }: { sources: SourceGraphResponse | null }) {
  return (
    <div className="stack">
      <Metric label="Profiles" value={sources?.source_count ?? 0} />
      <Metric label="Graph nodes" value={sources?.graph.nodes.length ?? 0} />
      <Metric label="Graph edges" value={sources?.graph.edges.length ?? 0} />
    </div>
  );
}

function CpaiInspector({
  cpai,
  onProbe,
  onPlanTraining,
  loading,
}: {
  cpai: Record<string, CpaiStatus>;
  onProbe: (kind: "status" | "yolo" | "training") => void;
  onPlanTraining: () => void;
  loading: string | null;
}) {
  return (
    <div className="stack">
      <ActionButton icon={SearchCheck} label="Probe CPAI" loading={loading === "status"} onClick={() => onProbe("status")} />
      <ActionButton icon={SlidersHorizontal} label="Check YOLO" loading={loading === "yolo"} onClick={() => onProbe("yolo")} />
      <ActionButton icon={Brain} label="Check Training" loading={loading === "training"} onClick={() => onProbe("training")} />
      <ActionButton icon={FileJson} label="Plan YOLO Training" loading={loading === "trainingPlan"} onClick={onPlanTraining} />
      <pre>{JSON.stringify(cpai, null, 2)}</pre>
    </div>
  );
}

function HandoffInspector() {
  return (
    <div className="stack">
      <Metric label="Slug" value="ffed-qlc" />
      <Metric label="Domain" value="ffed-qlc.securedme.ca" />
      <Metric label="Status" value="pre-alpha" />
      <Metric label="Hierarchy" value="I -> I_system^S -> D_f -> dF -> i_fractal" />
    </div>
  );
}

function ManifestInspector({ lattice, orb }: { lattice: LatticeBuildResponse | null; orb: OrbResponse | null }) {
  return (
    <pre>{JSON.stringify({ patch: lattice?.patch_metadata, orb }, null, 2)}</pre>
  );
}

function TemplateInspector({ template }: { template: Record<string, unknown> | null }) {
  return <pre>{JSON.stringify(template ?? { status: "Export Template has not run yet" }, null, 2)}</pre>;
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function activeTabLabel(tab: TabKey) {
  return tabs.find((item) => item.key === tab)?.label ?? "Inspector";
}
