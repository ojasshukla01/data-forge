import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  timeout: process.env.CI ? 90000 : 60000,
  reporter: process.env.CI ? "list" : "list",
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: process.env.CI
    ? undefined
    : [
        {
          command: "python -m uvicorn data_forge.api.main:app --host 127.0.0.1 --port 8000",
          url: "http://127.0.0.1:8000/health",
          reuseExistingServer: true,
          cwd: "..",
        },
        {
          // Match CI: run against production build.
          command: "npm run build && npm run start -- -p 3000",
          url: "http://127.0.0.1:3000",
          reuseExistingServer: true,
          env: {
            NEXT_PUBLIC_API_URL: "http://127.0.0.1:8000",
          },
        },
      ],
});
