import { expect, test } from "@playwright/test";

const laboratories = Array.from({ length: 9 }, (_, index) => ({
  lab_id: `lab-${String(index + 1).padStart(2, "0")}`,
  title: `Laboratory ${index + 1}`,
  difficulty: "foundation",
  allowed_action: "inspect_primitives",
  objective: "Produce bounded evidence.",
  duration_minutes: 45,
  prerequisites: [], proof_required: true, professor_review_required: false,
}));

test.beforeEach(async ({ page }) => {
  await page.route("**/api/v1/**", async (route) => {
    const url = route.request().url();
    const body = url.includes("laboratories")
      ? { laboratories }
      : url.includes("capabilities")
        ? { phase: "pre-alpha", development: "active-public-development", public_stateful_enabled: false, identity_adapter_ready: false, fqlc2_demo_enabled: true, native_handoff_runtime_ready: false }
        : { status: "ready", gateway: { transport: "test" }, storage: "sqlite" };
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(body) });
  });
});

test("renders a stable accessible entry surface", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("Laboratoire d'orbe Vigil")).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Vigil workflow" })).toBeVisible();
  await expect(page.getByRole("button", { name: /Ouvrir la session supervisee/ })).toBeDisabled();
  await expect(page.getByRole("status")).toContainText("verified identity adapter");
  await expect(page.locator("body")).not.toHaveCSS("overflow-x", "scroll");
});
