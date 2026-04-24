# src/calendar_workload_runner/sync_calendar.py

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, TypedDict, cast

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from calendar_workload_runner.db import RunScheduleRepository
from calendar_workload_runner.models import RunSchedule
from calendar_workload_runner.settings import Settings

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


class CalendarSyncService:

    def __init__(
        self,
        settings: Settings,
        repository: RunScheduleRepository | None = None,
    ) -> None:
        self.settings = settings
        self.repository = repository or RunScheduleRepository(settings.db_path)

    def get_credentials(self) -> Credentials:
        creds: Credentials | None = None

        if self.settings.token_path.exists():
            creds = Credentials.from_authorized_user_file(  # type: ignore[no-untyped-call]
                str(self.settings.token_path),
                SCOPES,
            )

        if creds is None or not creds.valid:
            if creds is not None:
                creds_any = cast(Any, creds)
                if creds.expired and creds_any.refresh_token:
                    creds_any.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.settings.credentials_path),
                        SCOPES,
                    )
                    new_creds = flow.run_local_server(port=0)
                    creds = cast(Credentials, new_creds)
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.settings.credentials_path),
                    SCOPES,
                )
                new_creds = flow.run_local_server(port=0)
                creds = cast(Credentials, new_creds)

            assert creds is not None
            self.settings.token_path.write_text(
                creds.to_json(),  # type: ignore[no-untyped-call]
                encoding="utf-8",
            )

        assert creds is not None
        return creds

    def fetch_calendar_response(
        self,
        time_min: datetime,
        time_max: datetime,
    ) -> CalendarResponse:
        creds = self.get_credentials()

        service: Any = build(
            "calendar",
            "v3",
            credentials=creds,
        )

        response: Any = (
            service.events()
            .list(
                calendarId=self.settings.calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        return cast(CalendarResponse, response)

    def sync(
        self,
        *,
        lookback_days: int = 1,
        lookahead_days: int = 3,
    ) -> list[RunSchedule]:
        self.repository.initialize()

        now = datetime.now(timezone.utc)
        time_min = now - timedelta(days=lookback_days)
        time_max = now + timedelta(days=lookahead_days)

        response = self.fetch_calendar_response(
            time_min=time_min,
            time_max=time_max,
        )
        items = extract_items(response)
        schedules = normalize_events(items)
        self.repository.upsert_run_schedules(schedules)

        return schedules


def is_timed_event(item: CalendarEvent) -> bool:
    start = item.get("start")
    end = item.get("end")

    if start is None or end is None:
        return False

    start_datetime = start.get("dateTime")
    end_datetime = end.get("dateTime")

    return isinstance(
        start_datetime,
        str,
    ) and isinstance(
        end_datetime,
        str,
    )


def extract_items(response: CalendarResponse) -> list[CalendarEvent]:
    items = response.get("items", [])

    if not isinstance(items, list):
        return []

    return items


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
