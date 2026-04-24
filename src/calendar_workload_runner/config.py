# src/calendar_workload_runner/config.py

from __future__ import annotations

from pathlib import Path

from calendar_workload_runner.settings import Settings


def load_settings(config_path: Path | None = None) -> Settings:
    return Settings.load(config_path=config_path)
