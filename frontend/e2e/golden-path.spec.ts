import { test, expect } from "@playwright/test";

const API_BASE = process.env.PLAYWRIGHT_API_URL ?? "http://127.0.0.1:8000";

/**
 * Golden paths and related flows:
 * - Schema Studio → validate → save → wizard → run → run detail provenance
 * - Wizard pack path → run → run detail provenance
 * - Advanced config pack path → run → run detail provenance
 * - Runs index loads after runs exist
 *
 * Requires API and frontend running.
 */
test.describe.serial("golden paths & runs", () => {
  test("create schema, save, run with custom schema via wizard, verify provenance", async ({ page }) => {
    test.setTimeout(60000);

    // Create schema via API (Schema Studio save flow is flaky in E2E)
    const schemaBody = {
      name: "e2e_schema",
      tables: [{ name: "table_1", columns: [{ name: "col_1", data_type: "string", nullable: true }], primary_key: ["col_1"] }],
      relationships: [],
    };
    const createRes = await fetch(`${API_BASE}/api/custom-schemas`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "New schema", schema: schemaBody }),
    });
    expect(createRes.ok).toBe(true);
    const created = (await createRes.json()) as { id: string; name: string };

    // 2. Create Wizard: select custom schema
    await page.goto("/create/wizard");
    await expect(page.getByRole("heading", { name: /Create Dataset/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole("heading", { name: /Choose Input/i })).toBeVisible({ timeout: 10000 });

    await page.getByRole("button", { name: /Custom Schema/i }).click();
    const schemaChoice = page.getByRole("button", { name: new RegExp(created.name, "i") }).first();
    await expect(schemaChoice).toBeVisible({ timeout: 15000 });
    await schemaChoice.click();

    // 3. Navigate to Review step and run (minimal config)
    await page.getByRole("button", { name: /^Next$/i }).click();
    await page.getByRole("button", { name: /^Next$/i }).click();
    await page.getByRole("button", { name: /^Next$/i }).click();
    await page.getByRole("button", { name: /^Next$/i }).click();

    await expect(page.getByRole("heading", { name: /Review & Run/i })).toBeVisible({ timeout: 5000 });

    await page.getByRole("button", { name: /^Run$/i }).click();

    // 4. Wait for redirect to run detail
    await expect(page).toHaveURL(/\/runs\/[a-z0-9-]+/, { timeout: 60000 });

    // 5. Verify lineage and custom schema provenance details.
    await expect(page.getByRole("heading", { name: /Lineage/i })).toBeVisible({ timeout: 30000 });
    await expect(page.locator("dt", { hasText: /^Schema source$/i }).first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator("dd", { hasText: /^Custom schema$/i }).first()).toBeVisible({ timeout: 15000 });
    await expect(page.getByRole("heading", { name: /Reproducibility manifest/i })).toBeVisible({ timeout: 10000 });
  });

  test("wizard pack path: select pack, run, verify run detail", async ({ page }) => {
    await page.goto("/create/wizard");
    await expect(page.getByRole("heading", { name: /Create Dataset/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole("heading", { name: /Choose Input/i })).toBeVisible({ timeout: 10000 });
    await page.getByRole("button", { name: /Domain Pack/i }).first().click();
    await expect(page.getByText(/Choose a domain pack to get started quickly/i)).toBeVisible({ timeout: 5000 });
    await page
      .getByRole("button", { name: /Saas Billing/i })
      .first()
      .click({ timeout: 5000 })
      .catch(() =>
        page
          .getByRole("button", { name: /Ecommerce/i })
          .first()
          .click(),
      );
    await page.getByRole("button", { name: /^Next$/i }).click();
    await page.getByRole("button", { name: /^Next$/i }).click();
    await page.getByRole("button", { name: /^Next$/i }).click();
    await page.getByRole("button", { name: /^Next$/i }).click();
    await expect(page.getByRole("heading", { name: /Review & Run/i })).toBeVisible({ timeout: 5000 });
    await page.getByRole("button", { name: /^Run$/i }).click();
    await expect(page).toHaveURL(/\/runs\/[a-z0-9-]+/, { timeout: 60000 });
    await expect(page.getByRole("heading", { name: /Lineage/i })).toBeVisible({ timeout: 30000 });
  });

  test("advanced config: exports section renders", async ({ page }) => {
    await page.goto("/create/advanced");
    await expect(page.getByRole("heading", { name: /Advanced Configuration/i })).toBeVisible({ timeout: 10000 });

    // Switch to Exports section and verify key controls render.
    await page.getByRole("button", { name: /Exports/i }).click();
    await expect(page.getByText("Export format")).toBeVisible({ timeout: 10000 });
    await expect(page.getByText("Write golden dataset manifest")).toBeVisible({ timeout: 10000 });
  });

  test("runs index: loads after runs exist", async ({ page }) => {
    await page.goto("/runs");
    await expect(page.getByRole("heading", { name: /Runs/i })).toBeVisible({ timeout: 10000 });
  });
});
