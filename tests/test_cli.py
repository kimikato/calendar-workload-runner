# tests/test_cli.py

from __future__ import annotations

from pathlib import Path

from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from calendar_workload_runner import cli
from calendar_workload_runner.models import RunSchedule
from calendar_workload_runner.settings import Settings


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
            sync_interval_seconds=900,
            control_interval_seconds=60,
        )

    class FakeCalendarSyncService:
        def __init__(self, settings: Settings) -> None:
            called["service_settings"] = settings

        def sync(self) -> list[RunSchedule]:
            called["sync"] = True
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
    monkeypatch.setattr(cli, "CalendarSyncService", FakeCalendarSyncService)

    cli.main()
    captured = capsys.readouterr()

    assert called["load_settings"] is True
    assert "service_settings" in called
    assert called["sync"] is True
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
            sync_interval_seconds=900,
            control_interval_seconds=60,
        )

    class FakeWorkloadController:
        def __init__(self, settings: Settings) -> None:
            called["controller_settings"] = settings

        def control(self) -> str:
            called["control"] = True
            return "started workload (pid=12345)"

    monkeypatch.setattr(cli, "load_settings", fake_load_settings)
    monkeypatch.setattr(cli, "WorkloadController", FakeWorkloadController)

    cli.main()
    captured = capsys.readouterr()

    assert called["load_settings"] is True
    assert "controller_settings" in called
    assert called["control"] is True
    assert captured.out.strip() == "started workload (pid=12345)"


def test_cli_daemon_once(
    monkeypatch: MonkeyPatch,
    capsys: CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "sys.argv",
        [
            "calendar_workload_runner",
            "daemon",
            "--once",
            "--sync-interval",
            "900",
            "--control-interval",
            "60",
        ],
    )

    called: dict[str, object] = {}

    def fake_load_settings(config_path: Path | None = None) -> Settings:
        called["load_settings"] = config_path

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
            sync_interval_seconds=900,
            control_interval_seconds=60,
        )

    class FakeDaemonRunner:

        def __init__(
            self,
            settings: Settings,
            *,
            sync_interval: int = 900,
            control_interval: int = 60,
        ) -> None:
            called["runner_settings"] = settings
            called["sync_interval"] = sync_interval
            called["control_interval"] = control_interval

        def run_once(self) -> tuple[int, str]:
            called["run_once"] = True
            return 2, "idle"

    monkeypatch.setattr(cli, "load_settings", fake_load_settings)
    monkeypatch.setattr(cli, "DaemonRunner", FakeDaemonRunner)

    cli.main()
    captured = capsys.readouterr()

    assert "runner_settings" in called
    assert called["sync_interval"] == 900
    assert called["control_interval"] == 60
    assert called["run_once"] is True
    assert captured.out.strip() == "synced 2 schedule(s)\nidle"


def test_cli_generate(
    tmp_path: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    output_path = tmp_path / "settings.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "calendar_workload_runner",
            "generate",
            "--output",
            str(output_path),
        ],
    )

    cli.main()
    captured = capsys.readouterr()

    assert output_path.exists() is True
    text = output_path.read_text(encoding="utf-8")
    assert '"calendar_id": "primary"' in text
    assert '"sync_interval_seconds": 900' in text
    assert '"control_interval_seconds": 60' in text
    assert captured.out.strip() == f"generated settings file: {output_path}"
