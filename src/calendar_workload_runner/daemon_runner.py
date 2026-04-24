# src/calendar_workload_runner/daemon_runner.py

from __future__ import annotations

import time

from calendar_workload_runner.control_runner import WorkloadController
from calendar_workload_runner.models import RunSchedule
from calendar_workload_runner.settings import Settings
from calendar_workload_runner.sync_calendar import CalendarSyncService


class DaemonRunner:

    def __init__(
        self,
        settings: Settings,
        *,
        sync_interval: int = 900,
        control_interval: int = 60,
    ) -> None:
        self.settings = settings
        self.sync_interval = sync_interval
        self.control_interval = control_interval
        self.sync_service = CalendarSyncService(settings)
        self.workload_controller = WorkloadController(settings)

    def run_once(self) -> tuple[int, str]:
        schedules: list[RunSchedule] = self.sync_service.sync()
        control_message = self.workload_controller.control()
        return len(schedules), control_message

    def run_forever(self) -> None:
        next_sync_at = 0.0
        next_control_at = 0.0

        while True:
            now = time.monotonic()

            if now >= next_sync_at:
                self.sync_service.sync()
                next_sync_at = now + self.sync_interval
            if now >= next_control_at:
                self.workload_controller.control()
                next_control_at = now + self.control_interval

            time.sleep(1.0)
