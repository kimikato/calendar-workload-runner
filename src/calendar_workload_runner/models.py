# src/calendar_workload_runner/models.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunSchedule:
    event_id: str
    title: str
    start_at: str
    end_at: str
    updated_at: str
    is_active: int
