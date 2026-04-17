# tests/test_config.py

from __future__ import annotations

from calendar_workload_runner.config import load_settings


def test_load_settings_defaults() -> None:
    settings = load_settings()

    assert settings.calendar_id == "primary"
    assert settings.db_path.name == "runner.db"
    assert settings.workload_pid_path.name == "workload.pid"
