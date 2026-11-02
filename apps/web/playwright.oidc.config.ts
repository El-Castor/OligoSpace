import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e-oidc",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 180_000,
  expect: { timeout: 20_000 },
  reporter: "./e2e-oidc/sanitized-reporter.ts",
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL,
    ignoreHTTPSErrors: true,
    actionTimeout: 20_000,
    navigationTimeout: 30_000,
    trace: "off",
    screenshot: "off",
    video: "off",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  outputDir: "/tmp/oligospace-oidc-results",
});
