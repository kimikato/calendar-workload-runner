# src/calendar_workload_runner/control_runner.py

from __future__ import annotations

import os
import shlex
import signal
import subprocess
from datetime import datetime, timezone

from calendar_workload_runner.db import RunScheduleRepository
from calendar_workload_runner.settings import Settings


class WorkloadController:

    def __init__(
        self,
        settings: Settings,
        repository: RunScheduleRepository | None = None,
    ) -> None:
        self.settings = settings
        self.repository = repository or RunScheduleRepository(settings.db_path)

    def control(self) -> str:
        self.repository.initialize()

        now_iso = self.get_now_iso()
        allowed = self.repository.is_run_allowed_now(now_iso)

        pid = self.read_pid()
        running = pid is not None and self.is_process_running(pid)

        if allowed:
            if running and pid is not None:
                message = f"already running (pid={pid})"
                self.write_control_log(message)
                return message

            new_pid = self.start_workload()
            message = f"started workload (pid={new_pid})"
            self.write_control_log(message)
            return message

        if running and pid is not None:
            self.stop_workload(pid)
            message = f"stopped workload (pid={pid})"
            self.write_control_log(message)
            return message

        if pid is not None and not running:
            self.remove_pid()

        message = "idle"
        self.write_control_log(message)
        return message

    def get_now_iso(self) -> str:
        return datetime.now(timezone.utc).astimezone().isoformat()

    def parse_command(self) -> list[str]:
        return shlex.split(self.settings.workload_command)

    def read_pid(self) -> int | None:
        pid_path = self.settings.workload_pid_path

        if not pid_path.exists():
            return None

        text = pid_path.read_text(encoding="utf-8").strip()
        if text == "":
            return None

        try:
            return int(text)
        except ValueError:
            return None

    def write_pid(self, pid: int) -> None:
        pid_path = self.settings.workload_pid_path
        pid_path.parent.mkdir(parents=True, exist_ok=True)
        pid_path.write_text(f"{pid}\n", encoding="utf-8")

    def remove_pid(self) -> None:
        pid_path = self.settings.workload_pid_path
        if pid_path.exists():
            pid_path.unlink()

    def is_process_running(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        else:
            return True

    def start_workload(self) -> int:
        command = self.parse_command()
        if not command:
            raise ValueError("WORKLOAD_RUNNER_COMMAND is empty")

        self.settings.logs_dir.mkdir(parents=True, exist_ok=True)

        with self.settings.workload_log_path.open(
            "a", encoding="utf-8"
        ) as log_file:
            process = subprocess.Popen(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

        self.write_pid(process.pid)
        return process.pid

    def stop_workload(self, pid: int) -> None:
        os.killpg(pid, signal.SIGTERM)
        self.remove_pid()

    def write_control_log(self, message: str) -> None:
        self.settings.logs_dir.mkdir(parents=True, exist_ok=True)

        timestamp = self.get_now_iso()
        with self.settings.control_log_path.open(
            "a", encoding="utf-8"
        ) as log_file:
            log_file.write(f"[{timestamp}] {message}\n")
