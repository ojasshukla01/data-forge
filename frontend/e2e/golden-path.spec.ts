import { test, expect } from "@playwright/test";

/**
 * Golden path: custom schema → validate → save → run → lineage
 * Requires API and frontend running. Verifies the full custom-schema flow.
 */
test.describe("golden path: custom schema to run", () => {
  test("create schema, save, run with custom schema, verify provenance", async ({ page }) => {
    // 1. Schema Studio: create new schema
    await page.goto("/schema/studio");
    await expect(page.getByRole("heading", { name: /Schema Studio/i })).toBeVisible({ timeout: 10000 });

    await page.getByRole("button", { name: /New schema/i }).click();

    // 2. Add a table (Form mode, Tables tab)
    await expect(page.getByText(/Schema editor \(form mode\)/i)).toBeVisible({ timeout: 5000 });
    await page.getByRole("button", { name: /Add table/i }).click();

    // 3. Validate
    await page.getByRole("button", { name: /Validate/i }).first().click();
    await page.getByText(/Schema editor|valid|errors?/i).first().waitFor({ state: "visible", timeout: 3000 }).catch(() => {});

    // 4. Save schema
    await page.getByRole("button", { name: /Save schema/i }).first().click();
    await expect(page.getByText(/Schema saved successfully/i)).toBeVisible({ timeout: 10000 });

    // 5. Create Wizard: select custom schema
    await page.goto("/create/wizard");
    await expect(page.getByText(/Choose Input/i)).toBeVisible({ timeout: 10000 });

    await page.getByRole("button", { name: /Custom Schema/i }).click();
    await page.getByRole("button", { name: /New schema/i }).first().waitFor({ state: "visible", timeout: 5000 });

    await page.getByRole("button", { name: /New schema/i }).first().click();

    // 6. Navigate to Review step and run (minimal config)
    await page.getByRole("button", { name: /Next/i }).click();
    await page.getByRole("button", { name: /Next/i }).click();
    await page.getByRole("button", { name: /Next/i }).click();
    await page.getByRole("button", { name: /Next/i }).click();

    await expect(page.getByText(/Review|Schema source/i)).toBeVisible({ timeout: 5000 });

    await page.getByRole("button", { name: /^Run$/i }).click();

    // 7. Wait for redirect to run detail
    await expect(page).toHaveURL(/\/runs\/[a-z0-9-]+/, { timeout: 60000 });

    // 8. Verify run detail shows custom schema provenance
    await expect(page.getByText(/Custom schema|New schema|Schema source/i)).toBeVisible({ timeout: 15000 });

    // 9. Verify lineage card visible (provenance durability)
    await expect(page.getByRole("heading", { name: /Lineage/i })).toBeVisible({ timeout: 5000 });
    await expect(page.getByRole("heading", { name: /Reproducibility manifest/i })).toBeVisible({ timeout: 3000 });
  });

  test("wizard pack path: select pack, run, verify run detail", async ({ page }) => {
    await page.goto("/create/wizard");
    await expect(page.getByText(/Choose Input|Create Dataset/i)).toBeVisible({ timeout: 10000 });
    await page.getByRole("button", { name: /Domain Pack/i }).first().click();
    await expect(page.getByText(/Saas Billing|Ecommerce|Choose a domain pack/i)).toBeVisible({ timeout: 5000 });
    await page.getByRole("button", { name: /Saas Billing/i }).first().click({ timeout: 5000 }).catch(() =>
      page.getByRole("button", { name: /Ecommerce/i }).first().click()
    );
    await page.getByRole("button", { name: /Next/i }).click();
    await page.getByRole("button", { name: /Next/i }).click();
    await page.getByRole("button", { name: /Next/i }).click();
    await page.getByRole("button", { name: /Next/i }).click();
    await expect(page.getByText(/Review|Schema source|Pack/i)).toBeVisible({ timeout: 5000 });
    await page.getByRole("button", { name: /^Run$/i }).click();
    await expect(page).toHaveURL(/\/runs\/[a-z0-9-]+/, { timeout: 60000 });
    await expect(page.getByText(/Pack|Schema source|Lineage|Manifest/i)).toBeVisible({ timeout: 15000 });
  });
});
