# src/calendar_workload_runner/control_runner.py

from __future__ import annotations

import os
import shlex
import signal
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from calendar_workload_runner.db import initialize_db, is_run_allowed_now
from calendar_workload_runner.settings import Settings


def get_now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat()


def parse_command(command: str) -> list[str]:
    return shlex.split(command)


def read_pid(pid_path: Path) -> int | None:
    if not pid_path.exists():
        return None

    text = pid_path.read_text(encoding="utf-8").strip()
    if text == "":
        return None

    try:
        return int(text)
    except ValueError:
        return None


def write_pid(pid_path: Path, pid: int) -> None:
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(f"{pid}\n", encoding="utf-8")


def remove_pid(pid_path: Path) -> None:
    if pid_path.exists():
        pid_path.unlink()


def is_process_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    else:
        return True


def start_workload(settings: Settings) -> int:
    command = parse_command(settings.workload_command)
    if not command:
        raise ValueError("WORKLOAD_RUNNER_COMMAND is empty")

    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    with settings.workload_log_path.open("a", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            command,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    write_pid(settings.workload_pid_path, process.pid)
    return process.pid


def stop_workload(pid: int, pid_path: Path) -> None:
    os.killpg(pid, signal.SIGTERM)
    remove_pid(pid_path)


def write_control_log(settings: Settings, message: str) -> None:
    settings.logs_dir.mkdir(parents=True, exist_ok=True)

    timestamp = get_now_iso()
    with settings.control_log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")


def control_workload(settings: Settings) -> str:
    initialize_db(settings.db_path)

    now_iso = get_now_iso()
    allowed = is_run_allowed_now(settings.db_path, now_iso)

    pid = read_pid(settings.workload_pid_path)
    running = pid is not None and is_process_running(pid)

    if allowed:
        if running and pid is not None:
            message = f"already running (pid={pid})"
            write_control_log(settings, message)
            return message

        new_pid = start_workload(settings)
        message = f"started workload (pid={new_pid})"
        write_control_log(settings, message)
        return message

    if running and pid is not None:
        stop_workload(pid, settings.workload_pid_path)
        message = f"stopped workload (pid={pid})"
        write_control_log(settings, message)
        return message

    if pid is not None and not running:
        remove_pid(settings.workload_pid_path)

    message = "idle"
    write_control_log(settings, message)
    return message
