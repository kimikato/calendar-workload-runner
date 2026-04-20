# src/calendar_workload_runner/cli.py

from __future__ import annotations

import argparse
from pathlib import Path

from calendar_workload_runner.config import load_settings
from calendar_workload_runner.control_runner import control_workload
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
        message = control_workload(settings)
        print(message)
        return

    print("calendar-workload-runner")
