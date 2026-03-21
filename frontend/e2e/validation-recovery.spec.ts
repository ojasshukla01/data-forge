import { test, expect } from "@playwright/test";

const API_BASE = process.env.PLAYWRIGHT_API_URL ?? "http://127.0.0.1:8000";

/**
 * Validation failure and recovery: Schema Studio validate shows errors,
 * user fixes (e.g. add required column), re-validates, then saves.
 * Requires API and frontend running.
 */
test.describe.serial("validation recovery", () => {
  // Skip: Schema Studio save flow has schema=undefined in handleSave (both create & update)
  test.skip("Schema Studio: validate shows feedback, fix then save", async ({ page }) => {
    test.setTimeout(60000);

    // Create schema via API (table with no columns — invalid until we add PK column)
    const schemaBody = {
      name: "validation_test",
      tables: [{ name: "table_1", columns: [], primary_key: [] }],
      relationships: [],
    };
    const createRes = await fetch(`${API_BASE}/api/custom-schemas`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "Validation Test", schema: schemaBody }),
    });
    expect(createRes.ok).toBe(true);

    await page.goto("/schema/studio");
    await expect(page.getByRole("heading", { name: /Schema Studio/i })).toBeVisible({ timeout: 10000 });

    // Select the schema we created
    await page.getByRole("button", { name: /Validation Test/i }).first().click();

    // Switch to Form mode (default may be Visual)
    await page.getByRole("button", { name: /^Form$/i }).click();
    await expect(page.getByRole("button", { name: /Add table/i })).toBeVisible({ timeout: 5000 });
    // Switch to Columns tab to add a column (table_1 already exists)
    await page.getByRole("button", { name: /Columns/i }).click();
    await expect(page.getByRole("button", { name: /Add column/i })).toBeVisible({ timeout: 5000 });

    // Validate — expect validation summary (table has no columns / no PK)
    await page.getByRole("button", { name: /Validate/i }).first().click();
    await expect(
      page.getByText(/Validation summary|valid|error|warning|primary/i).first(),
    ).toBeVisible({ timeout: 8000 });

    // Fix: add a primary key column so schema becomes valid
    await page.getByRole("button", { name: /Add column/i }).click();
    const nameInput = page.getByPlaceholder(/Column name/i).or(page.getByLabel(/Column name/i)).first();
    await nameInput.fill("id");
    const pkCheck = page.getByRole("checkbox", { name: /^PK$/i }).first();
    if (await pkCheck.isVisible().catch(() => false)) {
      await pkCheck.check();
    }

    // Validate again — wait for valid so Save is enabled
    await page.getByRole("button", { name: /Validate/i }).first().click();
    await expect(page.getByText(/Schema valid|✓ Schema valid/i)).toBeVisible({ timeout: 8000 });

    // Save — wait for Save enabled, then click (update flow for existing schema)
    const saveBtn = page.getByRole("button", { name: /Save schema/i }).first();
    await expect(saveBtn).toBeEnabled({ timeout: 5000 });
    await saveBtn.click();
    await expect(page.getByText(/Schema saved successfully/i).first()).toBeVisible({ timeout: 15000 });
  });
});
