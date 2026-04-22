# src/calendar_workload_runner/settings.py

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    db_path: Path
    credentials_path: Path
    token_path: Path
    logs_dir: Path
    state_dir: Path
    calendar_id: str
    workload_command: str
    workload_pid_path: Path
    workload_log_path: Path
    control_log_path: Path
    sync_log_path: Path
    sync_interval_seconds: int
    control_interval_seconds: int

    def ensure_runtime_paths(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.credentials_path.parent.mkdir(parents=True, exist_ok=True)
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.workload_pid_path.parent.mkdir(parents=True, exist_ok=True)
        self.workload_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.control_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.sync_log_path.parent.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_dir": str(self.base_dir),
            "db_path": str(self.db_path),
            "credentials_path": str(self.credentials_path),
            "token_path": str(self.token_path),
            "logs_dir": str(self.logs_dir),
            "state_dir": str(self.state_dir),
            "calendar_log": str(self.calendar_id),
            "workload_command": str(self.workload_command),
            "workload_pid_path": str(self.workload_pid_path),
            "workload_log_path": str(self.workload_log_path),
            "control_log_path": str(self.control_log_path),
            "sync_log_path": str(self.sync_log_path),
            "sync_interval_seconds": self.sync_interval_seconds,
            "control_interval_seconds": self.control_interval_seconds,
        }

    @classmethod
    def default(cls) -> Settings:
        base_dir = Path.home() / ".calendar-workload-runner"
        logs_dir = base_dir / "logs"
        state_dir = base_dir / "state"

        settings = cls(
            base_dir=base_dir,
            db_path=base_dir / "runner.db",
            credentials_path=base_dir / "credentials.json",
            token_path=base_dir / "token.json",
            logs_dir=logs_dir,
            state_dir=state_dir,
            calendar_id="primary",
            workload_command="sleep 3000",
            workload_pid_path=state_dir / "workload.pid",
            workload_log_path=logs_dir / "workload.log",
            control_log_path=logs_dir / "control.log",
            sync_log_path=logs_dir / "sync_calendar.log",
            sync_interval_seconds=900,
            control_interval_seconds=60,
        )
        settings.ensure_runtime_paths()
        return settings

    @classmethod
    def load(cls, config_path: Path | None = None) -> Settings:
        data = cls._load_json(config_path) if config_path is not None else {}

        base_dir = Path(
            cls._get_str(
                data,
                "base_dir",
                os.getenv(
                    "WORKLOAD_RUNNER_BASE_DIR",
                    str(Path.home() / ".calendar-workload-runner"),
                ),
            )
        )

        logs_dir = Path(
            cls._get_str(
                data,
                "logs_dir",
                str(base_dir / "logs"),
            )
        )
        state_dir = Path(
            cls._get_str(
                data,
                "state_dir",
                str(base_dir / "state"),
            )
        )

        settings = cls(
            base_dir=base_dir,
            db_path=Path(
                cls._get_str(
                    data,
                    "db_path",
                    os.getenv(
                        "WORKLOAD_RUNNER_DB_PATH",
                        str(base_dir / "runner.db"),
                    ),
                )
            ),
            credentials_path=Path(
                cls._get_str(
                    data,
                    "credentials_path",
                    os.getenv(
                        "GOOGLE_CREDENTIALS_PATH",
                        str(base_dir / "credentials.json"),
                    ),
                )
            ),
            token_path=Path(
                cls._get_str(
                    data,
                    "token_path",
                    os.getenv(
                        "GOOGLE_TOKEN_PATH",
                        str(base_dir / "token.json"),
                    ),
                )
            ),
            logs_dir=logs_dir,
            state_dir=state_dir,
            calendar_id=cls._get_str(
                data,
                "calendar_id",
                os.getenv("GOOGLE_CALENDAR_ID", "primary"),
            ),
            workload_command=cls._get_str(
                data,
                "workload_command",
                os.getenv("WORKLOAD_RUNNER_COMMAND", ""),
            ),
            workload_pid_path=Path(
                cls._get_str(
                    data,
                    "workload_pid_path",
                    os.getenv(
                        "WORKLOAD_RUNNER_PID_PATH",
                        str(state_dir / "workload.pid"),
                    ),
                )
            ),
            workload_log_path=Path(
                cls._get_str(
                    data,
                    "workload_log_path",
                    os.getenv(
                        "WORKLOAD_RUNNER_LOG_PATH",
                        str(logs_dir / "workload.log"),
                    ),
                )
            ),
            control_log_path=Path(
                cls._get_str(
                    data,
                    "control_log_path",
                    os.getenv(
                        "WORKLOAD_RUNNER_CONTROL_LOG_PATH",
                        str(logs_dir / "control.log"),
                    ),
                )
            ),
            sync_log_path=Path(
                cls._get_str(
                    data,
                    "sync_log_path",
                    os.getenv(
                        "WORKLOAD_RUNNER_SYNC_LOG_PATH",
                        str(logs_dir / "sync_calendar.log"),
                    ),
                )
            ),
            sync_interval_seconds=cls._get_int(
                data,
                "sync_interval_seconds",
                int(os.getenv("WORKLOAD_RUNNER_SYNC_INTERVAL_SECONDS", "900")),
            ),
            control_interval_seconds=cls._get_int(
                data,
                "control_interval_seconds",
                int(
                    os.getenv("WORKLOAD_RUNNER_CONTROL_INTERVAL_SECONDS", "60")
                ),
            ),
        )

        settings.ensure_runtime_paths()
        return settings

    @staticmethod
    def _load_json(config_path: Path) -> dict[str, Any]:
        text = config_path.read_text(encoding="utf-8")
        loaded = json.loads(text)

        if not isinstance(loaded, dict):
            raise ValueError("settings JSON root must be an object")

        return loaded

    @staticmethod
    def _get_str(data: dict[str, Any], key: str, default: str) -> str:
        value = data.get(key, default)
        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")
        return value

    @staticmethod
    def _get_int(data: dict[str, Any], key: str, default: int) -> int:
        value = data.get(key, default)
        if not isinstance(value, int):
            raise ValueError(f"{key} must be an integer")
        return value
