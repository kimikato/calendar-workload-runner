# tests/test_control_runner.py

from __future__ import annotations

from pathlib import Path

from calendar_workload_runner.control_runner import (
    parse_command,
    read_pid,
    remove_pid,
    write_pid,
)
from calendar_workload_runner.settings import Settings


def make_settings(tmp_path: Path) -> Settings:
    return Settings(
        base_dir=tmp_path,
        db_path=tmp_path / "runner.db",
        credentials_path=tmp_path / "credentials.json",
        token_path=tmp_path / "token.json",
        logs_dir=tmp_path / "logs",
        state_dir=tmp_path / "state",
        calendar_id="primary",
        workload_command="echo test",
        workload_pid_path=tmp_path / "state" / "workload.pid",
        workload_log_path=tmp_path / "logs" / "workload.log",
        control_log_path=tmp_path / "logs" / "control.log",
        sync_log_path=tmp_path / "logs" / "sync_calendar.log",
    )


def test_parse_command_returns_parts() -> None:
    command = "echo hello"
    assert parse_command(command) == ["echo", "hello"]


def test_parse_command_returns_empty_list_for_blank() -> None:
    assert parse_command("") == []
    assert parse_command("   ") == []


def test_write_and_read_pid(tmp_path: Path) -> None:
    pid_path = tmp_path / "state" / "workload.pid"

    write_pid(pid_path, 12345)

    assert read_pid(pid_path) == 12345


def test_read_pid_returns_none_when_missing(tmp_path: Path) -> None:
    pid_path = tmp_path / "state" / "workload.pid"

    assert read_pid(pid_path) is None


def test_remove_pid_deletes_file(tmp_path: Path) -> None:
    pid_path = tmp_path / "state" / "workload.pid"

    write_pid(pid_path, 12345)
    remove_pid(pid_path)

    assert pid_path.exists() is False
