# tests/test_cli.py

from __future__ import annotations

from pathlib import Path

from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from calendar_workload_runner import cli
from calendar_workload_runner.config import Settings
from calendar_workload_runner.models import RunSchedule


def test_cli_main_prints_name(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.argv", ["calendar_workload_runner"])
    cli.main()
    captured = capsys.readouterr()

    assert captured.out.strip() == "calendar-workload-runner"


def test_cli_sync_calendar(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "sys.argv", ["calendar_workload_runner", "sync-calendar"]
    )

    called: dict[str, object] = {}

    def fake_load_settings() -> Settings:
        called["load_settings"] = True

        return Settings(
            base_dir=Path("."),
            db_path=Path("dummy.db"),
            credentials_path=Path("credentials.json"),
            token_path=Path("token.json"),
            logs_dir=Path("logs"),
            state_dir=Path("state"),
            calendar_id="primary",
            workload_command="echo test",
            workload_pid_path=Path("state/workload.pid"),
            workload_log_path=Path("logs/workload.log"),
            control_log_path=Path("logs/control.log"),
            sync_log_path=Path("logs/sync_calendar.log"),
        )

    def fake_initialize_db(db_path: Path) -> None:
        called["initialize_db"] = db_path

    def fake_sync_google_calendar_to_db(
        settings: Settings,
    ) -> list[RunSchedule]:
        called["sync_google_calendar_to_db"] = settings
        return [
            RunSchedule(
                event_id="event-1",
                title="Event 1",
                start_at="2026-04-11T11:00:00+09:00",
                end_at="2026-04-11T12:00:00+09:00",
                updated_at="2026-04-10T10:00:00+09:00",
                is_active=1,
            ),
            RunSchedule(
                event_id="event-2",
                title="Event 2",
                start_at="2026-04-11T13:00:00+09:00",
                end_at="2026-04-11T14:00:00+09:00",
                updated_at="2026-04-10T10:00:00+09:00",
                is_active=1,
            ),
        ]

    monkeypatch.setattr(cli, "load_settings", fake_load_settings)
    monkeypatch.setattr(cli, "initialize_db", fake_initialize_db)
    monkeypatch.setattr(
        cli,
        "sync_google_calendar_to_db",
        fake_sync_google_calendar_to_db,
    )

    cli.main()
    captured = capsys.readouterr()

    assert called["load_settings"] is True
    assert called["initialize_db"] == Path("dummy.db")
    assert "sync_google_calendar_to_db" in called
    assert captured.out.strip() == "synced 2 schedule(s)"


def test_cli_control_runner(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "sys.argv", ["calendar_workload_runner", "control-runner"]
    )

    called: dict[str, object] = {}

    def fake_load_settings() -> Settings:
        called["load_settings"] = True

        return Settings(
            base_dir=Path("."),
            db_path=Path("dummy.db"),
            credentials_path=Path("credentials.json"),
            token_path=Path("token.json"),
            logs_dir=Path("logs"),
            state_dir=Path("state"),
            calendar_id="primary",
            workload_command="echo test",
            workload_pid_path=Path("state/workload.pid"),
            workload_log_path=Path("logs/workload.log"),
            control_log_path=Path("logs/control.log"),
            sync_log_path=Path("logs/sync_calendar.log"),
        )

    def fake_control_workload(settings: Settings) -> str:
        called["control_workload"] = settings
        return "started workload (pid=12345)"

    monkeypatch.setattr(cli, "load_settings", fake_load_settings)
    monkeypatch.setattr(cli, "control_workload", fake_control_workload)

    cli.main()
    captured = capsys.readouterr()

    assert called["load_settings"] is True
    assert "control_workload" in called
    assert captured.out.strip() == "started workload (pid=12345)"
