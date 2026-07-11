import { spawn } from "node:child_process";

const baseURL = process.env.PLAYWRIGHT_BASE_URL || "http://127.0.0.1:3000";
const isWindows = process.platform === "win32";
const extraArgs = process.argv.slice(2);
let serverProcess;
let startedServer = false;

async function main() {
  const alreadyRunning = await isServerAvailable();
  if (!alreadyRunning) {
    serverProcess = spawn(
      process.execPath,
      ["./node_modules/next/dist/bin/next", "dev", "--hostname", "127.0.0.1", "--port", "3000"],
      {
        cwd: process.cwd(),
        env: process.env,
        stdio: ["ignore", "pipe", "pipe"]
      }
    );
    startedServer = true;
    serverProcess.stdout.on("data", (chunk) => process.stdout.write(`[E2E Server] ${chunk}`));
    serverProcess.stderr.on("data", (chunk) => process.stderr.write(`[E2E Server] ${chunk}`));
    await waitForServer();
  }

  const playwrightBin = isWindows ? "node_modules\\.bin\\playwright.cmd" : "node_modules/.bin/playwright";
  const exitCode = await runCommand(playwrightBin, ["test", ...extraArgs], {
    ...process.env,
    PLAYWRIGHT_BASE_URL: baseURL,
    PLAYWRIGHT_SKIP_WEBSERVER: "1"
  });
  await stopServer();
  process.exit(exitCode);
}

async function isServerAvailable() {
  try {
    const response = await fetch(baseURL, { method: "GET" });
    return response.ok;
  } catch {
    return false;
  }
}

async function waitForServer() {
  const startedAt = Date.now();
  while (Date.now() - startedAt < 120_000) {
    if (await isServerAvailable()) return;
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  throw new Error(`E2E dev server did not become ready: ${baseURL}`);
}

function runCommand(command, args, env) {
  return new Promise((resolve) => {
    const child = spawn(isWindows ? "cmd.exe" : command, isWindows ? ["/d", "/s", "/c", command, ...args] : args, {
      cwd: process.cwd(),
      env,
      stdio: "inherit"
    });
    child.on("close", (code) => resolve(code ?? 1));
  });
}

function stopServer() {
  if (!startedServer || !serverProcess || serverProcess.killed) return Promise.resolve();
  return new Promise((resolve) => {
    if (isWindows) {
      const killer = spawn("taskkill", ["/pid", String(serverProcess.pid), "/T", "/F"], { stdio: "ignore" });
      killer.on("close", () => resolve());
      return;
    }
    serverProcess.once("close", () => resolve());
    serverProcess.kill("SIGTERM");
    setTimeout(resolve, 1000);
  });
}

process.on("SIGINT", async () => {
  await stopServer();
  process.exit(130);
});

process.on("SIGTERM", async () => {
  await stopServer();
  process.exit(143);
});

main().catch(async (error) => {
  console.error(error);
  await stopServer();
  process.exit(1);
});
