# src/calendar_workload_runner/db.py

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Sequence

from calendar_workload_runner.models import RunSchedule


def ensure_runtime_dirs(base_dir: Path) -> None:
    base_dir.mkdir(parents=True, exist_ok=True)
    (base_dir / "logs").mkdir(parents=True, exist_ok=True)
    (base_dir / "state").mkdir(parents=True, exist_ok=True)


def initialize_db(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS run_schedules (
                event_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                start_at TEXT NOT NULL,
                end_at TEXT NOT NULL,
                updated_at TEXT,
                is_active INTEGER NOT NULL DEFAULT 1
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sync_state (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )

        conn.commit()
    finally:
        conn.close()


def upsert_run_schedules(
    db_path: Path, schedules: Sequence[RunSchedule]
) -> None:
    conn = sqlite3.connect(db_path)

    try:
        cur = conn.cursor()

        for schedule in schedules:
            cur.execute(
                """
                INSERT INTO run_schedules (
                    event_id,
                    title,
                    start_at,
                    end_at,
                    updated_at,
                    is_active
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (event_id) DO UPDATE SET
                    title = excluded.title,
                    start_at = excluded.start_at,
                    end_at = excluded.end_at,
                    updated_at = excluded.updated_at,
                    is_active = excluded.is_active
                """,
                (
                    schedule.event_id,
                    schedule.title,
                    schedule.start_at,
                    schedule.end_at,
                    schedule.updated_at,
                    schedule.is_active,
                ),
            )

        conn.commit()
    finally:
        conn.close()


def list_run_schedules(db_path: Path) -> list[RunSchedule]:
    conn = sqlite3.connect(db_path)

    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                event_id,
                title,
                start_at,
                end_at,
                updated_at,
                is_active
            FROM run_schedules
            ORDER BY start_at, event_id
            """
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    return [
        RunSchedule(
            event_id=row[0],
            title=row[1],
            start_at=row[2],
            end_at=row[3],
            updated_at=row[4],
            is_active=row[5],
        )
        for row in rows
    ]


def is_run_allowed_now(db_path: Path, now_iso: str) -> bool:
    conn = sqlite3.connect(db_path)

    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 1
            FROM run_schedules
            WHERE is_active = 1
              AND start_at <= ?
              AND end_at > ?
            LIMIT 1
            """,
            (now_iso, now_iso),
        )
        row = cur.fetchone()
    finally:
        conn.close()

    return row is not None
