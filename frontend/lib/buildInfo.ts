export const FRONTEND_BUILD_INFO = {
  appVersion: process.env.NEXT_PUBLIC_APP_VERSION || "0.1.0",
  gitCommit: process.env.NEXT_PUBLIC_GIT_COMMIT || "",
  gitCommitShort: (process.env.NEXT_PUBLIC_GIT_COMMIT || "").slice(0, 7),
  gitBranch: process.env.NEXT_PUBLIC_GIT_BRANCH || "",
  buildTime: process.env.NEXT_PUBLIC_BUILD_TIME || ""
};

export function isSameRevision(frontendCommit: string, backendCommit: string) {
  if (!frontendCommit || !backendCommit) return null;
  return frontendCommit.slice(0, 12) === backendCommit.slice(0, 12);
}
