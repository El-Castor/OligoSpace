import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: "line",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  use: {
    launchOptions: { args: ["--unsafely-treat-insecure-origin-as-secure=http://caddy:8080"] },
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://caddy:8080",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  outputDir: "/tmp/oligospace-playwright-results",
});
