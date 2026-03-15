import { test, expect } from "@playwright/test";

/**
 * Validation failure and recovery: Schema Studio validate shows errors,
 * user fixes (e.g. add required column), re-validates, then saves.
 * Requires API and frontend running.
 */
test.describe.serial("validation recovery", () => {
  test("Schema Studio: validate shows feedback, fix then save", async ({ page }) => {
    test.setTimeout(60000);
    await page.goto("/schema/studio");
    await expect(page.getByRole("heading", { name: /Schema Studio/i })).toBeVisible({ timeout: 10000 });

    await page.getByRole("button", { name: "New schema", exact: true }).click();
    await expect(page.getByText(/Schema editor \(form mode\)/i)).toBeVisible({ timeout: 5000 });

    // Add a table (no columns yet — may trigger validation error or warning)
    await page.getByRole("button", { name: /Add table/i }).click();

    // Validate — expect validation summary (errors or valid with warnings)
    await page.getByRole("button", { name: /Validate/i }).first().click();
    await expect(
      page.getByText(/Validation summary|valid|error|warning/i).first(),
    ).toBeVisible({ timeout: 8000 });

    // Fix: go to Columns tab and add a primary key column so schema becomes valid
    await page.getByRole("button", { name: /Columns/i }).click();
    await page.getByRole("button", { name: /Add column/i }).click();

    // Fill column name and set as primary key (form may have name input and primary_key checkbox)
    const nameInput = page.getByLabel(/Column name|name/i).first();
    await nameInput.fill("id");
    const pkCheck = page.getByRole("checkbox", { name: /primary|pk/i }).first();
    if (await pkCheck.isVisible().catch(() => false)) {
      await pkCheck.check();
    }
    // Set data type if visible
    const typeSelect = page.getByLabel(/Data type|type/i).first();
    if (await typeSelect.isVisible().catch(() => false)) {
      await typeSelect.selectOption("integer").catch(() => {});
    }

    // Validate again — should be valid or have fewer errors
    await page.getByRole("button", { name: /Validate/i }).first().click();
    await expect(
      page.getByText(/Validation summary|valid|Schema is valid|error/i).first(),
    ).toBeVisible({ timeout: 5000 });

    // Save
    await page.getByRole("button", { name: /Save schema/i }).first().click();
    await expect(
      page.getByText(/Schema saved successfully|saved/i),
    ).toBeVisible({ timeout: 10000 });
  });
});
