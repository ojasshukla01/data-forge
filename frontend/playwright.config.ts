import type { PlaywrightTestConfig } from "@playwright/test";

const config: PlaywrightTestConfig = {
  testDir: "./tests/e2e",
  timeout: 60_000,
  retries: process.env.CI ? 1 : 0,
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:3000",
    headless: true,
  },
  webServer: {
    command: "npm run dev",
    cwd: ".",
    port: 3000,
    reuseExistingServer: !process.env.CI,
  },
};

export default config;

