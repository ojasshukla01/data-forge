import { test, expect } from "@playwright/test";

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
    // 1. Schema Studio: create new schema
    await page.goto("/schema/studio");
    await expect(page.getByRole("heading", { name: /Schema Studio/i })).toBeVisible({ timeout: 10000 });

    await page.getByRole("button", { name: "New schema", exact: true }).click();

    // 2. Switch to Form mode (default is Visual), add a table and a primary key column
    await page.getByRole("button", { name: /^Form$/i }).click();
    await expect(page.getByRole("button", { name: /Add table/i })).toBeVisible({ timeout: 5000 });
    await page.getByRole("button", { name: /Add table/i }).click();
    // addTable switches to Columns tab; add column and set as PK for valid schema
    await expect(page.getByRole("button", { name: /Add column/i })).toBeVisible({ timeout: 3000 });
    await page.getByRole("button", { name: /Add column/i }).click();
    await page.getByRole("checkbox", { name: /^PK$/i }).first().check();

    // 3. Validate — wait for valid result so Save is enabled
    await page.getByRole("button", { name: /Validate/i }).first().click();
    await expect(page.getByText(/Schema valid|✓ Schema valid/i)).toBeVisible({ timeout: 8000 });

    // 4. Save schema — wait for Save to be enabled, then click
    const saveBtn = page.getByRole("button", { name: /Save schema/i }).first();
    await expect(saveBtn).toBeEnabled({ timeout: 5000 });
    await saveBtn.click();
    await expect(page.getByText(/Schema saved successfully/i)).toBeVisible({ timeout: 15000 });

    // 5. Create Wizard: select custom schema
    await page.goto("/create/wizard");
    await expect(page.getByRole("heading", { name: /Create Dataset/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole("heading", { name: /Choose Input/i })).toBeVisible({ timeout: 10000 });

    await page.getByRole("button", { name: /Custom Schema/i }).click();
    const schemaChoice = page.getByRole("button", { name: /^New schema\b/i }).first();
    await expect(schemaChoice).toBeVisible({ timeout: 15000 });
    await schemaChoice.click();

    // 6. Navigate to Review step and run (minimal config)
    await page.getByRole("button", { name: /^Next$/i }).click();
    await page.getByRole("button", { name: /^Next$/i }).click();
    await page.getByRole("button", { name: /^Next$/i }).click();
    await page.getByRole("button", { name: /^Next$/i }).click();

    await expect(page.getByRole("heading", { name: /Review & Run/i })).toBeVisible({ timeout: 5000 });

    await page.getByRole("button", { name: /^Run$/i }).click();

    // 7. Wait for redirect to run detail
    await expect(page).toHaveURL(/\/runs\/[a-z0-9-]+/, { timeout: 60000 });

    // 8. Verify lineage and custom schema provenance details.
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
