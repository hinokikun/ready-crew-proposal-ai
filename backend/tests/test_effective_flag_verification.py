from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys

from app import main
from app.config import settings


def test_startup_logs_effective_false_flags_once(monkeypatch, caplog):
    monkeypatch.setattr(main, "init_db", lambda: None)
    monkeypatch.setattr(main, "get_db_health", lambda: {"db_tables_count": 0})
    object.__setattr__(settings, "presentation_master_v3_renderer_mvp_shadow_enabled", False)
    object.__setattr__(settings, "presentation_master_v3_renderer_mvp_enabled", False)

    with caplog.at_level("INFO", logger=main.logger.name):
        asyncio.run(_run_lifespan_once())

    records = [record for record in caplog.records if record.getMessage() == "presentation_shadow_runtime_config"]
    assert len(records) == 1
    assert records[0].shadow_enabled is False
    assert records[0].pmv3_enabled is False


def test_startup_logs_isolated_true_false_values(monkeypatch, caplog):
    monkeypatch.setattr(main, "init_db", lambda: None)
    monkeypatch.setattr(main, "get_db_health", lambda: {"db_tables_count": 0})
    object.__setattr__(settings, "presentation_master_v3_renderer_mvp_shadow_enabled", True)
    object.__setattr__(settings, "presentation_master_v3_renderer_mvp_enabled", False)
    with caplog.at_level("INFO", logger=main.logger.name):
        main._log_runtime_flag_config()
    record = next(record for record in caplog.records if record.getMessage() == "presentation_shadow_runtime_config")
    assert record.shadow_enabled is True
    assert record.pmv3_enabled is False
    object.__setattr__(settings, "presentation_master_v3_renderer_mvp_shadow_enabled", False)


def test_logger_failure_does_not_block_startup(monkeypatch):
    monkeypatch.setattr(main.logger, "info", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("logger")))
    main._log_runtime_flag_config()


def test_environment_only_change_does_not_change_cached_settings(monkeypatch):
    object.__setattr__(settings, "presentation_master_v3_renderer_mvp_shadow_enabled", False)
    monkeypatch.setenv("PRESENTATION_MASTER_V3_RENDERER_MVP_SHADOW_ENABLED", "true")
    assert settings.presentation_master_v3_renderer_mvp_shadow_enabled is False


def test_fresh_process_uses_updated_environment():
    code = "import json; from app.config import settings; print(json.dumps({'shadow': settings.presentation_master_v3_renderer_mvp_shadow_enabled, 'pmv3': settings.presentation_master_v3_renderer_mvp_enabled}))"
    env = dict(os.environ)
    env["PRESENTATION_MASTER_V3_RENDERER_MVP_SHADOW_ENABLED"] = "true"
    env["PRESENTATION_MASTER_V3_RENDERER_MVP_ENABLED"] = "false"
    result = subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True, env=env)
    assert json.loads(result.stdout) == {"shadow": True, "pmv3": False}

    env["PRESENTATION_MASTER_V3_RENDERER_MVP_SHADOW_ENABLED"] = "false"
    result = subprocess.run([sys.executable, "-c", code], check=True, capture_output=True, text=True, env=env)
    assert json.loads(result.stdout) == {"shadow": False, "pmv3": False}


async def _run_lifespan_once():
    async with main.lifespan(main.app):
        pass
