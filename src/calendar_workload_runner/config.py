# src/calendar_workload_runner/config.py

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


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


def load_settings() -> Settings:
    base_dir = Path(
        os.getenv(
            "WORKLOAD_RUNNER_BASE_DIR",
            str(Path.home() / ".calendar-workload-runner"),
        )
    )
    logs_dir = base_dir / "logs"
    state_dir = base_dir / "state"

    return Settings(
        base_dir=base_dir,
        db_path=Path(
            os.getenv(
                "WORKLOAD_RUNNER_DB_PATH",
                str(base_dir / "runner.db"),
            )
        ),
        credentials_path=Path(
            os.getenv(
                "GOOGLE_CREDENTIALS_PATH",
                str(base_dir / "credentials.json"),
            )
        ),
        token_path=Path(
            os.getenv(
                "GOOGLE_TOKEN_PATH",
                str(base_dir / "token.json"),
            )
        ),
        logs_dir=logs_dir,
        state_dir=state_dir,
        calendar_id=os.getenv("GOOGLE_CALENDAR_ID", "primary"),
        workload_command=os.getenv("WORKLOAD_RUNNER_COMMAND", ""),
        workload_pid_path=Path(
            os.getenv(
                "WORKLOAD_RUNNER_PID_PATH",
                str(state_dir / "workload.pid"),
            )
        ),
        workload_log_path=Path(
            os.getenv(
                "WORKLOAD_RUNNER_LOG_PATH",
                str(logs_dir / "workload.log"),
            )
        ),
        control_log_path=Path(
            os.getenv(
                "WORKLOAD_RUNNER_CONTROL_LOG_PATH",
                str(logs_dir / "control.log"),
            )
        ),
        sync_log_path=Path(
            os.getenv(
                "WORKLOAD_RUNNER_SYNC_LOG_PATH",
                str(logs_dir / "sync_calendar.log"),
            )
        ),
    )
