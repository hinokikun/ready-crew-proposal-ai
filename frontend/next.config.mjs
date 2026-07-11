import path from "node:path";
import { execSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function safeCommand(command) {
  try {
    return execSync(command, { cwd: __dirname, stdio: ["ignore", "pipe", "ignore"] }).toString().trim();
  } catch {
    return "";
  }
}

const frontendBuildTime = process.env.NEXT_PUBLIC_BUILD_TIME || new Date().toISOString();
const frontendGitCommit =
  process.env.NEXT_PUBLIC_GIT_COMMIT ||
  process.env.VERCEL_GIT_COMMIT_SHA ||
  safeCommand("git rev-parse HEAD");
const frontendGitBranch =
  process.env.NEXT_PUBLIC_GIT_BRANCH ||
  process.env.VERCEL_GIT_COMMIT_REF ||
  safeCommand("git rev-parse --abbrev-ref HEAD");

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  outputFileTracingRoot: __dirname,
  env: {
    NEXT_PUBLIC_APP_VERSION: process.env.NEXT_PUBLIC_APP_VERSION || process.env.npm_package_version || "0.1.0",
    NEXT_PUBLIC_BUILD_TIME: frontendBuildTime,
    NEXT_PUBLIC_GIT_COMMIT: frontendGitCommit,
    NEXT_PUBLIC_GIT_BRANCH: frontendGitBranch
  }
};

export default nextConfig;


