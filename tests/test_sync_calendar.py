# tests/test_sync_calendar.py

from __future__ import annotations

from pathlib import Path

from calendar_workload_runner.db import initialize_db, list_run_schedules
from calendar_workload_runner.sync_calendar import (
    CalendarEvent,
    CalendarResponse,
    extract_items,
    is_timed_event,
    normalize_event,
    normalize_events,
    sync_events_to_db,
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


def test_sync_events_to_db(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    initialize_db(db_path)

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
        }
    ]

    schedules = sync_events_to_db(db_path, items)

    assert len(schedules) == 1

    saved = list_run_schedules(db_path)
    assert len(saved) == 1
    assert saved[0].event_id == "event-1"


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
