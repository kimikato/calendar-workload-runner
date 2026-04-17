# calendar-workload-runner

A Google Calendar-based workload runner for WSL and other local environments.

This project is designed to control heavy local workloads based on calendar-defined time windows.
Typical examples include CPU-intensive or noisy workloads such as mining, batch AI jobs, BOINC clients, or long-running encoding tasks.

## Status

This project is currently in active development.

Implemented so far:

- Project structure and development tooling
- Python 3.12-based local development environment
- Strict type checking with mypy
- Linting with flake8
- Tests with pytest
- SQLite-based schedule storage
- RunSchedule model and `run_schedules` table
- Basic Google Calendar event normalization
- Filtering of timed events vs all-day events
- Filtering of cancelled events
- Syncing normalized calendar events into SQLite

Planned / in progress:

- CLI subcommands for calendar sync
- Workload start/stop control
- PID-based process management
- Windows Task Scheduler + WSL execution flow
- End-to-end automation for calendar-driven workload control

## Motivation

Traditional schedulers such as cron or Windows Task Scheduler are great for fixed recurring jobs.

However, some local workloads are better controlled by real-life schedules:

- Run only while family members are away
- Avoid noisy workloads during certain hours
- Follow irregular availability defined in Google Calendar
- Dynamically react to changed schedules without manually editing task definitions

This project aims to fill that gap.

## Suitable workloads

This project is intended for heavy local workloads that should run only during calendar-defined time windows.

Examples:

- Cryptocurrency mining workloads such as XMRig
- BOINC or similar distributed computing clients
- Long-running video encoding jobs
- Batch AI inference jobs
- Other CPU-intensive local jobs that are noisy or intrusive

## Not suitable workloads

This project is not intended for workloads that are better handled by traditional schedulers or that require strict uninterrupted execution.

Examples:

- Regular backups that can be scheduled with cron or Task Scheduler
- Real-time services or always-on daemons
- Jobs that must not be interrupted once started
- Mission-critical tasks requiring strict reliability guarantees
- Tasks that need second-level responsiveness

## Requirements

- Python 3.12+
- Google Calendar API credentials
- SQLite
- A local environment such as:
    - WSL2 on Windows
    - Linux
    - macOS (for development)

## Development setup

```bash
pyenv local 3.12.13
python3.12 -m venv .venv
source .venv/bin/activate
make init
make check
```

## Development commands

```bash
make init
make lint
make typecheck
make test
make check
make coverage
make coverage-html
make format
make clean
```

## Project layout

```text
src/calendar_workload_runner/
├── cli.py
├── config.py
├── db.py
├── models.py
└── sync_calendar.py

tests/
├── test_cli.py
├── test_config.py
├── test_db.py
└── test_sync_calendar.py
```

## Current data model

### RunSchedule

RunSchedule is the normalized internal model used by the runner.

Fields:

- event_id
- title
- start_at
- end_at
- updated_at
- is_active

### SQLite tables

Currently used tables:

- run_schedules
- sync_state

## Google Calendar event handling

The current implementation normalizes Google Calendar event-like dictionaries into RunSchedule records.

Current befavior:

- accepts timed events with start.dateTime and end.dateTime
- ignores all-day events using start.date / end.date
- ignores cancelled events
- stores normalized schedules into SQLite

## Configuration

The project currently uses a Settings dataclass in config.py.

Main settings include:

- base directory
- database path
- Google credentials path
- calendar id
- workload command
- workload PID path
- workload log path
- sync log path

Environment variables currently supported include:

- WORKLOAD_RUNNER_BASE_DIR
- WORKLOAD_RUNNER_DB_PATH
- GOOGLE_CREDENTIALS_PATH
- GOOGLE_TOKEN_PATH
- GOOGLE_CALENDAR_ID
- WORKLOAD_RUNNER_COMMAND
- WORKLOAD_RUNNER_PID_PATH
- WORKLOAD_RUNNER_LOG_PATH
- WORKLOAD_RUNNER_CONTROL_LOG_PATH
- WORKLOAD_RUNNER_SYNC_LOG_PATH

## Notes on Google API typing

The project uses strict typing where practical, but some Google client library calls are dynamically typed.

In those areas, local casts and minimal ignores are used to keep the codebase maintainable while preserving strict checks for project code.

## Roadmap

Short-term goals:

1. Add a CLI command for syncing Google Calendar events into SQLite
2. Implement workload control based on the current time window
3. Add PID-based workload start/stop logic
4. Integrate with Windows Task Scheduler and WSL
5. DOcument real-world setup examples

Possible future extensions:

- Multiple workload definitions
- Labels or filters for selecting relevant calendar events
- Supervisor mode for continuous background execution
- Improved logging and state tracking
- Support for additional calendar-driven automation flows

## License

MIT
