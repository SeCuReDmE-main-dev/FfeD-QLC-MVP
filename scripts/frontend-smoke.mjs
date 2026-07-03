import { existsSync, readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";

const root = process.cwd();
const app = readFileSync(join(root, "frontend", "src", "App.tsx"), "utf8");
const css = readFileSync(join(root, "frontend", "src", "styles.css"), "utf8");
const dist = join(root, "dist");

const requiredLabels = [
  "Build Penrose Patch",
  "Classify Sources",
  "Validate Lattice",
  "Build Orb",
  "Export Template",
  "Zoom in",
  "Zoom out",
  "Reset view",
  "Filter accepted",
  "Save layout",
  "Download graph snapshot",
];

const failures = [];
if (!existsSync(join(dist, "index.html"))) failures.push("dist/index.html missing");
if (!existsSync(join(dist, "assets"))) failures.push("dist/assets missing");
if (existsSync(join(dist, "assets")) && !readdirSync(join(dist, "assets")).some((name) => name.endsWith(".js"))) {
  failures.push("built JS asset missing");
}
for (const label of requiredLabels) {
  if (!app.includes(label)) failures.push(`missing UI control: ${label}`);
}
for (const expected of [".lattice-svg", "@media (max-width: 980px)", "@media (max-width: 620px)", "overflow-wrap"]) {
  if (!css.includes(expected)) failures.push(`missing responsive/style guard: ${expected}`);
}

if (failures.length) {
  console.error(JSON.stringify({ ok: false, failures }, null, 2));
  process.exit(1);
}

console.log(JSON.stringify({ ok: true, checked: "frontend build and responsive smoke" }));
