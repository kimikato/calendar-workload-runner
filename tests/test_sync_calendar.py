# tests/test_sync_calendar.py

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from _pytest.monkeypatch import MonkeyPatch

from calendar_workload_runner.db import RunScheduleRepository
from calendar_workload_runner.settings import Settings
from calendar_workload_runner.sync_calendar import (
    CalendarEvent,
    CalendarResponse,
    CalendarSyncService,
    extract_items,
    is_timed_event,
    normalize_event,
    normalize_events,
)


def test_is_timed_event_true() -> None:
    item: CalendarEvent = {
        "start": {"dateTime": "2026-04-11T11:00:00+09:00"},
        "end": {"dateTime": "2026-04-11T14:00:00+09:00"},
    }

    assert is_timed_event(item) is True


def test_is_timed_event_false_for_all_day_event() -> None:
    item: CalendarEvent = {
        "start": {"date": "2026-04-11"},
        "end": {"date": "2026-04-12"},
    }

    assert is_timed_event(item) is False


def test_normalize_event_returns_run_schedule() -> None:
    item: CalendarEvent = {
        "id": "event-1",
        "summary": "Family out",
        "status": "confirmed",
        "updated": "2026-04-10T09:00:00+09:00",
        "start": {
            "dateTime": "2026-04-11T11:00:00+09:00",
            "timeZone": "Asia/Tokyo",
        },
        "end": {
            "dateTime": "2026-04-11T14:00:00+09:00",
            "timeZone": "Asia/Tokyo",
        },
    }

    schedule = normalize_event(item)

    assert schedule is not None
    assert schedule.event_id == "event-1"
    assert schedule.title == "Family out"
    assert schedule.start_at == "2026-04-11T11:00:00+09:00"
    assert schedule.end_at == "2026-04-11T14:00:00+09:00"
    assert schedule.updated_at == "2026-04-10T09:00:00+09:00"
    assert schedule.is_active == 1


def test_normalize_event_returns_none_for_cancelled_event() -> None:
    item: CalendarEvent = {
        "id": "event-1",
        "summary": "Family out",
        "status": "cancelled",
        "updated": "2026-04-10T09:00:00+09:00",
        "start": {
            "dateTime": "2026-04-11T11:00:00+09:00",
            "timeZone": "Asia/Tokyo",
        },
        "end": {
            "dateTime": "2026-04-11T14:00:00+09:00",
            "timeZone": "Asia/Tokyo",
        },
    }

    schedule = normalize_event(item)

    assert schedule is None


def test_normalize_event_returns_none_when_id_is_missing() -> None:
    item: CalendarEvent = {
        "summary": "Family out",
        "status": "confirmed",
        "updated": "2026-04-10T09:00:00+09:00",
        "start": {
            "dateTime": "2026-04-11T11:00:00+09:00",
            "timeZone": "Asia/Tokyo",
        },
        "end": {
            "dateTime": "2026-04-11T14:00:00+09:00",
            "timeZone": "Asia/Tokyo",
        },
    }

    schedule = normalize_event(item)

    assert schedule is None


def test_normalize_events_filters_invalid_items() -> None:
    items: list[CalendarEvent] = [
        {
            "id": "event-1",
            "summary": "Family out",
            "status": "confirmed",
            "updated": "2026-04-10T09:00:00+09:00",
            "start": {
                "dateTime": "2026-04-11T11:00:00+09:00",
                "timeZone": "Asia/Tokyo",
            },
            "end": {
                "dateTime": "2026-04-11T14:00:00+09:00",
                "timeZone": "Asia/Tokyo",
            },
        },
        {
            "id": "event-2",
            "summary": "All day event",
            "status": "confirmed",
            "updated": "2026-04-10T09:00:00+09:00",
            "start": {"date": "2026-04-11"},
            "end": {"date": "2026-04-12"},
        },
        {
            "id": "event-3",
            "summary": "Cancelled",
            "status": "cancelled",
            "updated": "2026-04-10T09:00:00+09:00",
            "start": {
                "dateTime": "2026-04-11T15:00:00+09:00",
                "timeZone": "Asia/Tokyo",
            },
            "end": {
                "dateTime": "2026-04-11T18:00:00+09:00",
                "timeZone": "Asia/Tokyo",
            },
        },
    ]

    schedules = normalize_events(items)

    assert len(schedules) == 1
    assert schedules[0].event_id == "event-1"


def test_extract_items_returns_items_from_response() -> None:
    response: CalendarResponse = {
        "items": [
            {
                "id": "event-1",
                "summary": "Family out",
                "status": "confirmed",
                "updated": "2026-04-10T09:00:00+09:00",
                "start": {
                    "dateTime": "2026-04-11T11:00:00+09:00",
                    "timeZone": "Asia/Tokyo",
                },
                "end": {
                    "dateTime": "2026-04-11T14:00:00+09:00",
                    "timeZone": "Asia/Tokyo",
                },
            }
        ]
    }

    items = extract_items(response)

    assert len(items) == 1
    assert items[0].get("id") == "event-1"


def test_extract_items_returns_empty_list_when_missing() -> None:
    response: CalendarResponse = {}

    items = extract_items(response)

    assert items == []


def test_calendar_sync_service_sync(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    settings = Settings(
        base_dir=tmp_path,
        db_path=tmp_path / "runner.db",
        credentials_path=tmp_path / "credentials.json",
        token_path=tmp_path / "token.json",
        logs_dir=tmp_path / "logs",
        state_dir=tmp_path / "state",
        calendar_id="primary",
        workload_command="echo test",
        workload_pid_path=tmp_path / "state" / "workload.pid",
        workload_log_path=tmp_path / "logs" / "workload.log",
        control_log_path=tmp_path / "logs" / "control.log",
        sync_log_path=tmp_path / "logs" / "sync_calendar.log",
    )
    repository = RunScheduleRepository(settings.db_path)
    service = CalendarSyncService(settings, repository=repository)

    def fake_fetch_calendar_response(
        time_min: datetime,
        time_max: datetime,
    ) -> CalendarResponse:
        return {
            "items": [
                {
                    "id": "event-1",
                    "summary": "Family out",
                    "status": "confirmed",
                    "updated": "2026-04-10T09:00:00+09:00",
                    "start": {
                        "dateTime": "2026-04-11T11:00:00+09:00",
                        "timeZone": "Asia/Tokyo",
                    },
                    "end": {
                        "dateTime": "2026-04-11T14:00:00+09:00",
                        "timeZone": "Asia/Tokyo",
                    },
                }
            ]
        }

    monkeypatch.setattr(
        service,
        "fetch_calendar_response",
        fake_fetch_calendar_response,
    )

    schedules = service.sync()

    assert len(schedules) == 1

    saved = repository.list_run_schedules()
    assert len(saved) == 1
    assert saved[0].event_id == "event-1"
