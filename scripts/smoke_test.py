#!/usr/bin/env python3
"""Cloud deployment smoke test for AI営業秘書.

This script avoids proposal/PPT/PDF generation so it can run against
production-like environments without customer-data mutations or OpenAI spend.
It never prints passwords, tokens, or request bodies.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


REQUIRED_HEALTH_FIELDS = {
    "status",
    "app_version",
    "environment",
    "auth_configured",
    "db_connected",
    "db_type",
    "db_tables_count",
    "ai_api",
    "mock_ai",
    "pptx",
    "pdf",
    "timestamp",
    "pilot_mode",
    "pilot_max_users",
    "maintenance_mode",
    "migration_current",
    "migration_head",
    "migration_ready",
}


@dataclass
class HttpResult:
    status: int
    headers: dict[str, str]
    text: str
    json_body: dict[str, Any] | None


class SmokeTest:
    def __init__(self) -> None:
        self.failures = 0
        self.warnings = 0

    def pass_(self, label: str, detail: str = "") -> None:
        print(f"PASS {label}{' - ' + detail if detail else ''}")

    def fail(self, label: str, detail: str = "") -> None:
        self.failures += 1
        print(f"FAIL {label}{' - ' + detail if detail else ''}")

    def warn(self, label: str, detail: str = "") -> None:
        self.warnings += 1
        print(f"WARN {label}{' - ' + detail if detail else ''}")

    def skip(self, label: str, detail: str = "") -> None:
        print(f"SKIP {label}{' - ' + detail if detail else ''}")


def env(name: str) -> str:
    return os.getenv(name, "").strip()


def env_bool(name: str) -> bool | None:
    value = env(name).lower()
    if value in {"true", "1", "yes"}:
        return True
    if value in {"false", "0", "no"}:
        return False
    return None


def normalize_base(url: str) -> str:
    return url.rstrip("/")


def request(
    method: str,
    url: str,
    *,
    data: dict[str, Any] | None = None,
    token: str | None = None,
    timeout: int = 20,
) -> HttpResult:
    body = json.dumps(data).encode("utf-8") if data is not None else None
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            text = res.read().decode("utf-8", errors="replace")
            return HttpResult(res.status, dict(res.headers), text, parse_json(text))
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        return HttpResult(exc.code, dict(exc.headers), text, parse_json(text))
    except Exception as exc:
        return HttpResult(0, {}, exc.__class__.__name__, None)


def parse_json(text: str) -> dict[str, Any] | None:
    try:
        parsed = json.loads(text)
    except Exception:
        return None
    return parsed if isinstance(parsed, dict) else None


def login(backend_url: str, email: str, password: str) -> tuple[str, dict[str, Any], HttpResult]:
    result = request("POST", f"{backend_url}/api/auth/login", data={"email": email, "password": password})
    body = result.json_body or {}
    token = str(body.get("token") or "")
    user = body.get("user") if isinstance(body.get("user"), dict) else {}
    return token, user, result


def viewer_generation_guard(backend_url: str, token: str) -> HttpResult:
    return request(
        "POST",
        f"{backend_url}/api/analyze",
        token=token,
        data={
            "project_brief": "Smoke test viewer guard only. This request must be rejected before generation.",
            "client_company_info": "Smoke test",
            "budget_range": "未定",
            "desired_launch_timing": "要確認",
        },
    )


def main() -> int:
    smoke = SmokeTest()
    frontend_url = normalize_base(env("FRONTEND_URL"))
    backend_url = normalize_base(env("BACKEND_URL"))
    email = env("SMOKE_TEST_EMAIL")
    password = env("SMOKE_TEST_PASSWORD")
    viewer_email = env("SMOKE_VIEWER_EMAIL")
    viewer_password = env("SMOKE_VIEWER_PASSWORD")
    disabled_email = env("SMOKE_DISABLED_EMAIL")
    disabled_password = env("SMOKE_DISABLED_PASSWORD")
    expected_pilot_mode = env_bool("SMOKE_EXPECT_PILOT_MODE")

    missing = [
        name
        for name, value in {
            "FRONTEND_URL": frontend_url,
            "BACKEND_URL": backend_url,
            "SMOKE_TEST_EMAIL": email,
            "SMOKE_TEST_PASSWORD": password,
        }.items()
        if not value
    ]
    if missing:
        print(f"FAIL Configuration - missing environment variables: {', '.join(missing)}")
        return 2

    started = time.time()

    frontend = request("GET", frontend_url, timeout=20)
    if 200 <= frontend.status < 400:
        smoke.pass_("Frontend", f"status={frontend.status}")
    else:
        smoke.fail("Frontend", f"status={frontend.status}")

    health = request("GET", f"{backend_url}/health")
    body = health.json_body or {}
    if health.status == 200 and body:
        smoke.pass_("Backend health", f"status={body.get('status', 'unknown')}")
    else:
        smoke.fail("Backend health", f"status={health.status}")

    missing_fields = sorted(REQUIRED_HEALTH_FIELDS - set(body.keys()))
    if missing_fields:
        smoke.fail("Health fields", f"missing={', '.join(missing_fields)}")
    else:
        smoke.pass_("Health fields")

    for label, field, expected in [
        ("Auth configured", "auth_configured", True),
        ("Database connection", "db_connected", True),
        ("PPTX capability", "pptx", "available"),
        ("PDF capability", "pdf", "available"),
    ]:
        actual = body.get(field)
        if actual == expected:
            smoke.pass_(label, f"{field}={actual}")
        else:
            smoke.fail(label, f"{field}={actual}")

    if body.get("mock_ai") is True:
        smoke.pass_("Mock AI mode")
    else:
        smoke.warn("Mock AI mode", "off; smoke test still avoids generation calls")
    if body.get("migration_ready") is True:
        smoke.pass_("Migration readiness", f"current={body.get('migration_current')}, head={body.get('migration_head')}")
    else:
        smoke.fail("Migration readiness", f"current={body.get('migration_current')}, head={body.get('migration_head')}")

    live = request("GET", f"{backend_url}/health/live")
    smoke.pass_("Live health") if live.status == 200 else smoke.fail("Live health", f"status={live.status}")

    ready = request("GET", f"{backend_url}/health/ready")
    smoke.pass_("Ready health") if ready.status == 200 else smoke.fail("Ready health", f"status={ready.status}")

    pilot_status = request("GET", f"{backend_url}/api/pilot/status")
    pilot_body = pilot_status.json_body or {}
    pilot = pilot_body.get("pilot") if isinstance(pilot_body.get("pilot"), dict) else {}
    pilot_mode = bool(pilot.get("pilot_mode"))
    if pilot_status.status == 200:
        smoke.pass_("Pilot Mode status", f"pilot_mode={pilot_mode}")
    else:
        smoke.fail("Pilot Mode status", f"status={pilot_status.status}")
    if expected_pilot_mode is not None and pilot_mode != expected_pilot_mode:
        smoke.fail("Pilot Mode expected value", f"expected={expected_pilot_mode}, actual={pilot_mode}")

    token, user, login_result = login(backend_url, email, password)
    role = str(user.get("role") or "")
    if login_result.status == 200 and token and role:
        smoke.pass_("Login API", f"role={role}")
    else:
        smoke.fail("Login API", f"status={login_result.status}")

    current_org_id = 0
    current_workspace_id = 0
    if token:
        context = request("GET", f"{backend_url}/api/organizations/context", token=token)
        context_body = context.json_body or {}
        current = context_body.get("current") if isinstance(context_body.get("current"), dict) else {}
        current_org_id = int(current.get("organization_id") or 0)
        current_workspace_id = int(current.get("workspace_id") or 0)
        if context.status == 200 and current_org_id and current_workspace_id:
            smoke.pass_("Current organization/workspace", f"organization={current_org_id}, workspace={current_workspace_id}")
        else:
            smoke.fail("Current organization/workspace", f"status={context.status}")

        if current_org_id and current_workspace_id:
            allowed_switch = request(
                "PATCH",
                f"{backend_url}/api/organizations/context",
                token=token,
                data={"organization_id": current_org_id, "workspace_id": current_workspace_id},
            )
            if allowed_switch.status == 200:
                smoke.pass_("Allowed workspace switch", "current workspace re-selected")
            else:
                smoke.fail("Allowed workspace switch", f"status={allowed_switch.status}")

        forbidden_org = env("SMOKE_FORBIDDEN_ORGANIZATION_ID")
        forbidden_workspace = env("SMOKE_FORBIDDEN_WORKSPACE_ID")
        if forbidden_org and forbidden_workspace:
            forbidden_switch = request(
                "PATCH",
                f"{backend_url}/api/organizations/context",
                token=token,
                data={"organization_id": int(forbidden_org), "workspace_id": int(forbidden_workspace)},
            )
            if forbidden_switch.status in {403, 404}:
                smoke.pass_("Disallowed workspace switch rejection", f"status={forbidden_switch.status}")
            else:
                smoke.fail("Disallowed workspace switch rejection", f"status={forbidden_switch.status}")
        else:
            smoke.skip("Disallowed workspace switch rejection", "set SMOKE_FORBIDDEN_ORGANIZATION_ID and SMOKE_FORBIDDEN_WORKSPACE_ID")

        crm = request("GET", f"{backend_url}/api/projects/crm", token=token)
        if crm.status == 200:
            smoke.pass_("Current workspace projects", "/api/projects/crm")
        else:
            smoke.fail("Current workspace projects", f"status={crm.status}")

        other_project_id = env("SMOKE_OTHER_WORKSPACE_PROJECT_ID")
        if other_project_id:
            other_project = request("GET", f"{backend_url}/api/projects/{other_project_id}", token=token)
            if other_project.status in {403, 404}:
                smoke.pass_("Other workspace project IDOR rejection", f"status={other_project.status}")
            else:
                smoke.fail("Other workspace project IDOR rejection", f"status={other_project.status}")
        else:
            smoke.skip("Other workspace project IDOR rejection", "set SMOKE_OTHER_WORKSPACE_PROJECT_ID")

        beautiful_status = request("GET", f"{backend_url}/api/beautiful-ai/status", token=token)
        if beautiful_status.status == 200:
            smoke.pass_("Beautiful.ai status", "reachable")
        else:
            smoke.fail("Beautiful.ai status", f"status={beautiful_status.status}")

    if pilot_mode and role != "admin":
        if user.get("pilot_enabled") is True:
            smoke.pass_("Pilot-enabled user login")
        else:
            smoke.fail("Pilot-enabled user login", "primary smoke user is not pilot_enabled")

    if pilot_mode and disabled_email and disabled_password:
        _, _, disabled_login = login(backend_url, disabled_email, disabled_password)
        if disabled_login.status in {401, 403}:
            smoke.pass_("Pilot-disabled login rejection", f"status={disabled_login.status}")
        else:
            smoke.fail("Pilot-disabled login rejection", f"status={disabled_login.status}")
    elif pilot_mode:
        smoke.skip("Pilot-disabled login rejection", "set SMOKE_DISABLED_EMAIL and SMOKE_DISABLED_PASSWORD")
    else:
        smoke.skip("Pilot-disabled login rejection", "Pilot Mode is off")

    unauth = request("GET", f"{backend_url}/api/auth/status")
    if unauth.status in {401, 403}:
        smoke.pass_("Unauthenticated protected API rejection", f"status={unauth.status}")
    else:
        smoke.fail("Unauthenticated protected API rejection", f"status={unauth.status}")

    if token and role in {"admin", "manager", "member"}:
        crm = request("GET", f"{backend_url}/api/projects/crm", token=token)
        smoke.pass_("Authenticated core API", "/api/projects/crm") if crm.status == 200 else smoke.fail("Authenticated core API", f"status={crm.status}")
    elif token:
        smoke.skip("Authenticated core API", f"primary smoke user role is {role}")

    viewer_token = token if role == "viewer" else ""
    if not viewer_token and viewer_email and viewer_password:
        viewer_token, viewer_user, viewer_login = login(backend_url, viewer_email, viewer_password)
        if viewer_login.status != 200 or str(viewer_user.get("role") or "") != "viewer":
            viewer_token = ""
            smoke.fail("Viewer login", "SMOKE_VIEWER_EMAIL must be a viewer account")

    if viewer_token:
        guarded = viewer_generation_guard(backend_url, viewer_token)
        if guarded.status in {401, 403}:
            smoke.pass_("Viewer generation guard", f"status={guarded.status}")
        else:
            smoke.fail("Viewer generation guard", f"status={guarded.status}")
    else:
        smoke.skip("Viewer generation guard", "set SMOKE_VIEWER_EMAIL and SMOKE_VIEWER_PASSWORD")

    elapsed = round(time.time() - started, 2)
    if smoke.failures:
        print(f"Smoke test finished with {smoke.failures} failure(s), {smoke.warnings} warning(s) in {elapsed}s.")
        return 1
    print(f"Smoke test finished successfully with {smoke.warnings} warning(s) in {elapsed}s.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
