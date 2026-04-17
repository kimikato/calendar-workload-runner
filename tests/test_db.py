# tests/test_db.py

from __future__ import annotations

from pathlib import Path

from calendar_workload_runner.db import (
    initialize_db,
    is_run_allowed_now,
    list_run_schedules,
    upsert_run_schedules,
)
from calendar_workload_runner.models import RunSchedule


def test_initialize_db_creates_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"

    initialize_db(db_path)

    schedules = list_run_schedules(db_path)
    assert schedules == []


def test_upsert_and_list_run_schedules(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    initialize_db(db_path)

    schedule = RunSchedule(
        event_id="event-1",
        title="Family out",
        start_at="2026-04-11T11:00:00+09:00",
        end_at="2026-04-11T14:00:00+09:00",
        updated_at="2026-04-10T10:00:00+09:00",
        is_active=1,
    )

    upsert_run_schedules(db_path, [schedule])

    schedules = list_run_schedules(db_path)

    assert schedules == [schedule]


def test_is_run_allowed_now(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    initialize_db(db_path)

    schedule = RunSchedule(
        event_id="event-1",
        title="Family out",
        start_at="2026-04-11T11:00:00+09:00",
        end_at="2026-04-11T14:00:00+09:00",
        updated_at="2026-04-10T10:00:00+09:00",
        is_active=1,
    )

    upsert_run_schedules(db_path, [schedule])

    assert is_run_allowed_now(db_path, "2026-04-11T12:00:00+09:00") is True
    assert is_run_allowed_now(db_path, "2026-04-11T10:59:59+09:00") is False
    assert is_run_allowed_now(db_path, "2026-04-11T14:00:00+09:00") is False
