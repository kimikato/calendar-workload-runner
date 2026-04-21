# tests/test_daemon_runner.py

from __future__ import annotations

from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch

from calendar_workload_runner.daemon_runner import DaemonRunner
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


def test_daemon_runner_run_once(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    settings = make_settings(tmp_path)

    called: dict[str, object] = {}

    class FakeCalendarSyncService:
        def __init__(self, settings: Settings) -> None:
            called["sync_settings"] = settings

        def sync(self) -> list[RunSchedule]:
            called["sync"] = True
            return [
                RunSchedule(
                    event_id="event-1",
                    title="Event 1",
                    start_at="2026-04-11T11:00:00+09:00",
                    end_at="2026-04-11T14:00:00+09:00",
                    updated_at="2026-04-10T10:00:00+09:00",
                    is_active=1,
                )
            ]

    class FakeWorkloadController:
        def __init__(self, settings: Settings) -> None:
            called["controller_settings"] = settings

        def control(self) -> str:
            called["control"] = True
            return "idle"

    monkeypatch.setattr(
        "calendar_workload_runner.daemon_runner.CalendarSyncService",
        FakeCalendarSyncService,
    )

    monkeypatch.setattr(
        "calendar_workload_runner.daemon_runner.WorkloadController",
        FakeWorkloadController,
    )

    runner = DaemonRunner(settings)
    synced_count, control_message = runner.run_once()

    assert "sync_settings" in called
    assert "controller_settings" in called
    assert called["sync"] is True
    assert called["control"] is True
    assert synced_count == 1
    assert control_message == "idle"
