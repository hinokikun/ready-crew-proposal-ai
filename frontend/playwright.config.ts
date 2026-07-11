import { defineConfig, devices } from "@playwright/test";
import { existsSync } from "node:fs";
import { join } from "node:path";

const command = process.platform === "win32" ? "npm.cmd run dev" : "npm run dev";
const skipWebServer = process.env.PLAYWRIGHT_SKIP_WEBSERVER === "1";
const localHeadlessShell = process.env.LOCALAPPDATA
  ? join(process.env.LOCALAPPDATA, "ms-playwright", "chromium_headless_shell-1228", "chrome-headless-shell-win64", "chrome-headless-shell.exe")
  : "";
const localExecutablePath = process.platform === "win32" && !process.env.CI && existsSync(localHeadlessShell) ? localHeadlessShell : undefined;
const browserChannel = process.env.PLAYWRIGHT_CHANNEL || (!localExecutablePath && process.platform === "win32" && !process.env.CI ? "chrome" : undefined);

export default defineConfig({
  testDir: "./e2e",
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  timeout: 30_000,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  expect: {
    timeout: 8_000
  },
  use: {
    baseURL: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:3000",
    channel: browserChannel,
    launchOptions: localExecutablePath ? { executablePath: localExecutablePath } : undefined,
    screenshot: "only-on-failure",
    trace: "on-first-retry",
    video: "retain-on-failure"
  },
  webServer: skipWebServer
    ? undefined
    : {
        command,
        gracefulShutdown: { signal: "SIGTERM", timeout: 500 },
        url: process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:3000",
        reuseExistingServer: true,
        timeout: 120_000
      },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] }
    }
  ]
});
