# src/calendar_workload_runner/cli.py

from __future__ import annotations

import argparse
import json
from pathlib import Path

from calendar_workload_runner.config import load_settings
from calendar_workload_runner.control_runner import WorkloadController
from calendar_workload_runner.daemon_runner import DaemonRunner
from calendar_workload_runner.settings import Settings
from calendar_workload_runner.sync_calendar import CalendarSyncService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calendar_workload_runner",
        description="Calendar-based workload runner",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        help="Path to settings JSON file",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "sync-calendar",
        help="Sync Google Calendar events into SQLite",
    )
    subparsers.add_parser(
        "control-runner",
        help="Start or stop workload based on current schedule",
    )

    daemon_parser = subparsers.add_parser(
        "daemon",
        help="Run calendar sync and workload control loop",
    )
    daemon_parser.add_argument(
        "--sync-interval",
        type=int,
        default=900,
        help="Sync interval in seconds",
    )
    daemon_parser.add_argument(
        "--control-interval",
        type=int,
        default=60,
        help="Control interval in second",
    )
    daemon_parser.add_argument(
        "--once",
        action="store_true",
        help="Run sync and control once, then exit",
    )

    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate a default settings JSON file",
    )
    generate_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("settings.json"),
        help="Output path for generated settings JSON",
    )
    generate_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output file if it already exists",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "sync-calendar":
        settings = load_settings()
        service = CalendarSyncService(settings)
        schedules = service.sync()
        print(f"synced {len(schedules)} schedule(s)")
        return

    if args.command == "control-runner":
        settings = load_settings()
        controller = WorkloadController(settings)
        message = controller.control()
        print(message)
        return

    if args.command == "daemon":
        settings = load_settings()
        runner = DaemonRunner(
            settings,
            sync_interval=args.sync_interval,
            control_interval=args.control_interval,
        )

        if args.once:
            synced_count, control_message = runner.run_once()
            print(f"synced {synced_count} schedule(s)")
            print(control_message)
            return

        runner.run_forever()
        return

    if args.command == "generate":
        output_path: Path = args.output
        if output_path.exists() and not args.force:
            raise FileExistsError(
                f"{output_path} already exists. Use --force to overwrite."
            )

        settings = Settings.default()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(settings.to_dict(), indent=2, ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )
        print(f"generated settings file: {output_path}")
        return

    print("calendar-workload-runner")
