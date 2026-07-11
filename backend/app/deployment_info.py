from __future__ import annotations

import os
import subprocess
from functools import lru_cache


def _safe_text(value: str | None, limit: int = 80) -> str:
    if not value:
        return ""
    return value.strip()[:limit]


def _run_git(args: list[str]) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return _safe_text(result.stdout)


@lru_cache(maxsize=1)
def get_git_metadata() -> dict[str, str | bool]:
    """Return safe deployment revision data without exposing repository secrets."""

    commit = (
        os.getenv("RENDER_GIT_COMMIT")
        or os.getenv("GIT_COMMIT")
        or os.getenv("COMMIT_SHA")
        or os.getenv("VERCEL_GIT_COMMIT_SHA")
        or _run_git(["rev-parse", "HEAD"])
    )
    branch = (
        os.getenv("RENDER_GIT_BRANCH")
        or os.getenv("GIT_BRANCH")
        or os.getenv("VERCEL_GIT_COMMIT_REF")
        or _run_git(["rev-parse", "--abbrev-ref", "HEAD"])
    )
    source = "env" if any(os.getenv(key) for key in ("RENDER_GIT_COMMIT", "GIT_COMMIT", "COMMIT_SHA", "VERCEL_GIT_COMMIT_SHA")) else "git"
    commit = _safe_text(commit, 64)
    branch = _safe_text(branch, 80)
    return {
        "commit": commit,
        "commit_short": commit[:7] if commit else "",
        "branch": branch if branch and branch != "HEAD" else "",
        "source": source if commit else "unavailable",
        "available": bool(commit),
    }
