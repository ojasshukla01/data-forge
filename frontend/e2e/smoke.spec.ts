import { test, expect } from "@playwright/test";

test.describe("smoke", () => {
  test("homepage loads", async ({ page }) => {
    await page.goto("/");
    await expect(page).toHaveTitle(/Data Forge|data-forge/i);
  });

  test("create wizard loads", async ({ page }) => {
    await page.goto("/create/wizard");
    await expect(page.getByRole("heading", { name: /Create Dataset/i })).toBeVisible({ timeout: 10000 });
    await expect(page.getByRole("heading", { name: /Choose Input/i })).toBeVisible({ timeout: 10000 });
  });
});
