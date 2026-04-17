# src/calendar_workload_runner/cli.py

from __future__ import annotations

import argparse

from calendar_workload_runner.config import load_settings
from calendar_workload_runner.control_runner import control_workload
from calendar_workload_runner.db import initialize_db
from calendar_workload_runner.sync_calendar import sync_google_calendar_to_db


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="calendar_workload_runner",
        description="Calendar-based workload runner",
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
        initialize_db(settings.db_path)
        schedules = sync_google_calendar_to_db(settings)
        print(f"synced {len(schedules)} schedule(s)")
        return

    if args.command == "control-runner":
        settings = load_settings()
        message = control_workload(settings)
        print(message)
        return

    print("calendar-workload-runner")
