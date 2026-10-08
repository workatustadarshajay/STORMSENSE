import { defineConfig, devices } from "@playwright/test";

// Runs the real thing: the built web app served by the backend, on sample data.
export default defineConfig({
  testDir: "e2e",
  workers: 1,
  fullyParallel: false,
  retries: 0,
  reporter: [["list"]],
  use: { baseURL: "http://localhost:8000", trace: "retain-on-failure" },
  webServer: {
    command: process.env.CI ? "python -m app.main" : "../.venv/bin/python -m app.main",
    cwd: "../backend",
    url: "http://localhost:8000/api/health",
    reuseExistingServer: false,
    // Pinned here so the tests never depend on a developer's local backend/.env.
    env: { DATABRICKS_APP_PORT: "8000", STORMSENSE_MODE: "mock", STORMSENSE_ENVIRONMENT: "local", STORMSENSE_DEV_USER_EMAIL: "ava.planner@stormsense.test" },
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"], viewport: { width: 1280, height: 860 } } },
    { name: "phone", use: { ...devices["Pixel 7"] } },
  ],
});
