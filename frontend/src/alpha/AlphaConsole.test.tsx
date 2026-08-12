import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AlphaConsole } from "./AlphaConsole";

const labs = Array.from({ length: 9 }, (_, index) => ({
  lab_id: `lab-${String(index + 1).padStart(2, "0")}`,
  title: `Laboratory ${index + 1}`,
  difficulty: "foundation",
  allowed_action: "inspect_primitives",
  objective: "Produce bounded evidence.",
  duration_minutes: 45,
  prerequisites: [],
  proof_required: true,
  professor_review_required: false,
}));

afterEach(() => vi.restoreAllMocks());

describe("Vigil alpha console", () => {
  it("shows a trilingual supervised entry surface and real Gateway state", async () => {
    vi.stubGlobal("fetch", vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      const body = url.includes("laboratories")
        ? { laboratories: labs }
        : url.includes("capabilities")
          ? { phase: "pre-alpha", development: "active-public-development", public_stateful_enabled: true, identity_adapter_ready: true, fqlc2_demo_enabled: true, native_handoff_runtime_ready: false }
          : { status: "ready", gateway: { transport: "test" }, storage: "sqlite" };
      return new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } });
    }));

    render(<AlphaConsole orbStudio={<div>Native Penrose canvas</div>} />);

    expect(screen.getByText("Laboratoire d'orbe Vigil")).toBeInTheDocument();
    expect(screen.getByText(/Aucune metrique anterieure/)).toBeInTheDocument();
    expect(await screen.findByText(/Gateway: Pret/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Ouvrir la session supervisee/ })).toBeEnabled();
  });
});
