# src/calendar_workload_runner/sync_calendar.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, TypedDict, cast

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from calendar_workload_runner.config import Settings
from calendar_workload_runner.db import upsert_run_schedules
from calendar_workload_runner.models import RunSchedule

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class CalendarEventTime(TypedDict, total=False):
    dateTime: str
    date: str
    timeZone: str


class CalendarEvent(TypedDict, total=False):
    id: str
    status: str
    summary: str
    updated: str
    start: CalendarEventTime
    end: CalendarEventTime


class CalendarResponse(TypedDict, total=False):
    items: list[CalendarEvent]
    nextPageToken: str
    summary: str
    timeZone: str
    updated: str


def get_credentials(settings: Settings) -> Credentials:
    creds: Credentials | None = None

    if settings.token_path.exists():
        creds = Credentials.from_authorized_user_file(  # type: ignore[no-untyped-call]
            str(settings.token_path),
            SCOPES,
        )

    if creds is None or not creds.valid:
        if creds is not None:
            creds_any = cast(Any, creds)
            if creds.expired and creds_any.refresh_token:
                creds_any.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(settings.credentials_path),
                    SCOPES,
                )
                new_creds = flow.run_local_server(port=0)
                creds = cast(Credentials, new_creds)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(settings.credentials_path),
                SCOPES,
            )
            new_creds = flow.run_local_server(port=0)
            creds = cast(Credentials, new_creds)

        assert creds is not None
        settings.token_path.write_text(
            creds.to_json(), encoding="utf-8"  # type: ignore[no-untyped-call]
        )

    assert creds is not None
    return creds


def fetch_calendar_response(
    settings: Settings,
    time_min: datetime,
    time_max: datetime,
) -> CalendarResponse:
    creds = get_credentials(settings)

    service: Any = build(
        "calendar",
        "v3",
        credentials=creds,
    )

    response: Any = (
        service.events()
        .list(
            calendarId=settings.calendar_id,
            timeMin=time_min.isoformat(),
            timeMax=time_max.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    return cast(CalendarResponse, response)


def extract_items(response: CalendarResponse) -> list[CalendarEvent]:
    items = response.get("items", [])

    if not isinstance(items, list):
        return []

    return items


def is_timed_event(item: CalendarEvent) -> bool:
    start = item.get("start")
    end = item.get("end")

    if start is None or end is None:
        return False

    start_datetime = start.get("dateTime")
    end_datetime = end.get("dateTime")

    return isinstance(start_datetime, str) and isinstance(end_datetime, str)


def normalize_event(item: CalendarEvent) -> RunSchedule | None:
    if not is_timed_event(item):
        return None

    status = item.get("status")
    if status == "cancelled":
        return None

    event_id = item.get("id")
    start = item.get("start")
    end = item.get("end")
    updated_at = item.get("updated")

    if not isinstance(event_id, str) or event_id == "":
        return None
    if start is None or end is None:
        return None

    start_at_value = start.get("dateTime")
    end_at_value = end.get("dateTime")

    if not isinstance(start_at_value, str) or start_at_value == "":
        return None
    if not isinstance(end_at_value, str) or end_at_value == "":
        return None
    if updated_at is not None and not isinstance(updated_at, str):
        return None

    title = item.get("summary", "")
    if not isinstance(title, str):
        title = ""

    return RunSchedule(
        event_id=event_id,
        title=title,
        start_at=start_at_value,
        end_at=end_at_value,
        updated_at=updated_at or "",
        is_active=1,
    )


def normalize_events(items: list[CalendarEvent]) -> list[RunSchedule]:
    schedules: list[RunSchedule] = []

    for item in items:
        schedule = normalize_event(item)
        if schedule is not None:
            schedules.append(schedule)

    return schedules


def sync_events_to_db(
    db_path: Path,
    items: list[CalendarEvent],
) -> list[RunSchedule]:
    schedules = normalize_events(items)
    upsert_run_schedules(db_path=db_path, schedules=schedules)
    return schedules


def sync_google_calendar_to_db(
    settings: Settings,
    *,
    lookback_days: int = 1,
    lookahead_days: int = 3,
) -> list[RunSchedule]:
    now = datetime.now(timezone.utc)
    time_min = now - timedelta(days=lookback_days)
    time_max = now + timedelta(days=lookahead_days)

    response = fetch_calendar_response(
        settings=settings,
        time_min=time_min,
        time_max=time_max,
    )
    items = extract_items(response)
    return sync_events_to_db(settings.db_path, items)
