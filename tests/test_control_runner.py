# tests/test_control_runner.py

from __future__ import annotations

from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch

from calendar_workload_runner.control_runner import WorkloadController
from calendar_workload_runner.db import RunScheduleRepository
from calendar_workload_runner.models import RunSchedule
from calendar_workload_runner.settings import Settings


def make_settings(
    tmp_path: Path,
    workload_command: str = "echo test",
) -> Settings:
    return Settings(
        base_dir=tmp_path,
        db_path=tmp_path / "runner.db",
        credentials_path=tmp_path / "credentials.json",
        token_path=tmp_path / "token.json",
        logs_dir=tmp_path / "logs",
        state_dir=tmp_path / "state",
        calendar_id="primary",
        workload_command=workload_command,
        workload_pid_path=tmp_path / "state" / "workload.pid",
        workload_log_path=tmp_path / "logs" / "workload.log",
        control_log_path=tmp_path / "logs" / "control.log",
        sync_log_path=tmp_path / "logs" / "sync_calendar.log",
    )


def test_parse_command_returns_parts(tmp_path: Path) -> None:
    settings = make_settings(tmp_path, workload_command="echo hello")
    controller = WorkloadController(settings)

    assert controller.parse_command() == ["echo", "hello"]


def test_parse_command_returns_empty_list_for_blank(tmp_path: Path) -> None:
    settings = make_settings(tmp_path, workload_command="")
    controller = WorkloadController(settings)

    assert controller.parse_command() == []


def test_write_and_read_pid(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    controller = WorkloadController(settings)

    controller.write_pid(12345)

    assert controller.read_pid() == 12345


def test_read_pid_returns_none_when_missing(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    controller = WorkloadController(settings)

    assert controller.read_pid() is None


def test_remove_pid_deletes_file(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    controller = WorkloadController(settings)

    controller.write_pid(12345)
    controller.remove_pid()

    assert settings.workload_pid_path.exists() is False


def test_controll_starts_workload_when_allowed(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    settings = make_settings(tmp_path)
    repository = RunScheduleRepository(settings.db_path)
    controller = WorkloadController(settings)

    monkeypatch.setattr(
        controller,
        "get_now_iso",
        lambda: "2026-04-11T12:00:00+09:00",
    )
    monkeypatch.setattr(
        controller,
        "start_workload",
        lambda: 12345,
    )

    repository.initialize()
    repository.upsert_run_schedules(
        [
            RunSchedule(
                event_id="event-1",
                title="Family out",
                start_at="2026-04-11T11:00:00+09;00",
                end_at="2026-04-11T14:00:00+09:00",
                updated_at="2026-04-10T10:00:00+09:00",
                is_active=1,
            )
        ]
    )

    message = controller.control()

    assert message == "started workload (pid=12345)"
