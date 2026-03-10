import { test, expect } from "@playwright/test";

test("golden path: home → create wizard → run → run detail", async ({ page }) => {
  // Mock backend APIs at the network layer so we don't need a real API server.
  await page.route("**/api/domain-packs", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify([
        {
          id: "saas_billing",
          name: "SaaS Billing",
          description: "SaaS billing domain",
          category: "SaaS",
          tables_count: 5,
          relationships_count: 4,
        },
      ]),
    });
  });

  await page.route("**/api/scenarios**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ scenarios: [] }),
    });
  });

  await page.route("**/api/preflight", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        valid: true,
        blockers: [],
        warnings: [],
        recommendations: [],
        estimated_rows: 1000,
      }),
    });
  });

  await page.route("**/api/runs/generate", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ run_id: "run_playwright_1", status: "queued" }),
    });
  });

  await page.route("**/api/runs/run_playwright_1", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "run_playwright_1",
        status: "completed",
        run_type: "standard",
        created_at: Date.now() / 1000,
        duration_seconds: 3.2,
        config_summary: { pack: "saas_billing", scale: 1000 },
        artifacts: [
          { type: "dataset", name: "orders.parquet", path: "output/orders.parquet" },
        ],
      }),
    });
  });

  await page.route("**/api/runs/run_playwright_1/timeline", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        run_id: "run_playwright_1",
        status: "completed",
        stages: [
          { name: "plan", duration_seconds: 0.5, status: "completed" },
          { name: "generate", duration_seconds: 2.0, status: "completed" },
        ],
        events: [],
      }),
    });
  });

  await page.route("**/api/runs/run_playwright_1/lineage", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        run_id: "run_playwright_1",
        run_type: "standard",
        scenario_id: null,
        pack: "saas_billing",
      }),
    });
  });

  await page.route("**/api/runs/run_playwright_1/manifest", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        run_id: "run_playwright_1",
        run_type: "standard",
        pack: "saas_billing",
        scale: 1000,
        duration_seconds: 3.2,
      }),
    });
  });

  // Home → Create dataset
  await page.goto("/");
  await expect(page.getByRole("heading", { name: /Data Forge/i })).toBeVisible();
  await page.getByRole("link", { name: /Create dataset/i }).click();

  // Wizard: select pack
  await expect(page.getByText("Choose Input")).toBeVisible();
  await page.getByRole("button", { name: /SaaS Billing/i }).click();
  await page.getByRole("button", { name: /^Next$/ }).click();

  // Use Case
  await expect(page.getByText("Use Case")).toBeVisible();
  await page.getByRole("button", { name: /Demo Data/i }).click();
  await page.getByRole("button", { name: /^Next$/ }).click();

  // Realism
  await expect(page.getByText("Realism")).toBeVisible();
  await page.getByRole("button", { name: /^Next$/ }).click();

  // Export
  await expect(page.getByText("Export")).toBeVisible();
  await page.getByRole("button", { name: /^Next$/ }).click();

  // Review & Run
  await expect(page.getByText("Review & Run")).toBeVisible();
  await page.getByRole("button", { name: /^Run$/ }).click();

  // Navigated to run detail page and see artifacts + lineage/manifest sections
  await expect(page).toHaveURL(/\/runs\/run_playwright_1$/);
  await expect(page.getByText(/Artifacts/i)).toBeVisible();
  await expect(page.getByText(/orders\.parquet/)).toBeVisible();
  await expect(page.getByText(/Lineage/i)).toBeVisible();
  await expect(page.getByText(/Manifest/i)).toBeVisible();
});

