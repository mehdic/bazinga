import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 1,
  workers: 1,
  reporter: process.env.CI
    ? [
        ["list"],
        ["json", { outputFile: "test-results.json" }],
        ["html", { open: "never" }],
      ]
    : "list",
  timeout: 30000,
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        launchOptions: {
          args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"],
        },
      },
    },
  ],
  webServer: {
    command: "npm run dev:all",
    url: "http://localhost:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
    env: {
      // Explicitly set the database path for tests
      // This tells the app where to find the database that tests will seed
      DATABASE_URL: `${process.cwd()}/bazinga/bazinga.db`,
    },
  },
});
