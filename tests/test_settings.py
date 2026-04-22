# tests/test_settings.py

from __future__ import annotations

import json
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch

from calendar_workload_runner.settings import Settings


def test_settings_load_defaults(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    monkeypatch.setenv("WORKLOAD_RUNNER_BASE_DIR", str(tmp_path / "runtime"))

    settings = Settings.load()

    assert settings.base_dir == tmp_path / "runtime"
    assert settings.db_path == tmp_path / "runtime" / "runner.db"
    assert settings.logs_dir == tmp_path / "runtime" / "logs"
    assert settings.state_dir == tmp_path / "runtime" / "state"
    assert settings.sync_interval_seconds == 900
    assert settings.control_interval_seconds == 60


def test_settings_load_from_json(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.json"
    config_path.write_text(
        json.dumps(
            {
                "base_dir": str(tmp_path / "app"),
                "calendar_id": "test-calendar",
                "workload_command": "sleep 10",
                "sync_interval_seconds": 900,
                "control_interval_seconds": 60,
            }
        ),
        encoding="utf-8",
    )

    settings = Settings.load(config_path)

    assert settings.base_dir == tmp_path / "app"
    assert settings.calendar_id == "test-calendar"
    assert settings.workload_command == "sleep 10"
    assert settings.sync_interval_seconds == 900
    assert settings.control_interval_seconds == 60


def test_settings_ensure_runtime_paths(tmp_path: Path) -> None:
    config_path = tmp_path / "settings.json"
    config_path.write_text(
        json.dumps(
            {
                "base_dir": str(tmp_path / "app"),
            }
        ),
        encoding="utf-8",
    )

    settings = Settings.load(config_path)

    assert settings.base_dir.exists() is True
    assert settings.logs_dir.exists() is True
    assert settings.state_dir.exists() is True
