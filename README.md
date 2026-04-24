# calendar-workload-runner

**English** | [日本語](README.ja.md)

![Tests](https://github.com/kimikato/calendar-workload-runner/actions/workflows/tests.yml/badge.svg?branch=main)
[![Coverage](https://img.shields.io/codecov/c/github/kimikato/calendar-workload-runner/main?label=coverage&logo=codecov)](https://codecov.io/gh/kimikato/calendar-workload-runner)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A CLI tool that starts and stops a workload command based on events from Google Calendar.

Currently, it supports the following:

- Sync scheduled events from Google Calendar into SQLite
- Decide whether a workload should be running at the current time
- Start or stop the `workload` command accordingly
- Run `sync` and `control` together through a `daemon` command
- Generate a `settings.json` template

## Intended Use Case

A typical use case looks like this:

- Create scheduled events in Google Calendar
- Run a workload only during those scheduled time windows
- Stop the workload automatically outside those windows

## Requirements

- Python 3.12+
- SQLite3
- A Google account and access to Google Calendar API

## Installation

For development:

```bash
python -m venv .venv
source .venv/bin/activate
make init
```

## Google Calendar API Setup

Before using this tool, set up the following in Google Cloud:

- Create a project
- Enable Google Calendar API
- Configure the OAuth consent screen
- Create OAuth client credentials for a desktop application
- Download `credentials.json`

## Initial Setup

### 1. Generate `settings.json`

```bash
calendar_workload_runner generate --output ./settings.json
```

If the file already exists, the command will fail. To overwrite it, use `--force`.

```bash
calendar_workload_runner generate --output ./settings.json --force
```

### 2. Edit `settings.json` as needed

Example generated file:

```json
{
    "base_dir": "/Users/yourname/.calendar-workload-runner",
    "db_path": "/Users/yourname/.calendar-workload-runner/runner.db",
    "credentials_path": "/Users/yourname/.calendar-workload-runner/credentials.json",
    "token_path": "/Users/yourname/.calendar-workload-runner/token.json",
    "logs_dir": "/Users/yourname/.calendar-workload-runner/logs",
    "state_dir": "/Users/yourname/.calendar-workload-runner/state",
    "calendar_id": "primary",
    "workload_command": "sleep 3000",
    "workload_pid_path": "/Users/yourname/.calendar-workload-runner/state/workload.pid",
    "workload_log_path": "/Users/yourname/.calendar-workload-runner/logs/workload.log",
    "control_log_path": "/Users/yourname/.calendar-workload-runner/logs/control.log",
    "sync_log_path": "/Users/yourname/.calendar-workload-runner/logs/sync_calendar.log",
    "sync_interval_seconds": 900,
    "control_interval_seconds": 60
}
```

### 3. Place `credentials.json`

Put the OAuth credentials file downloaded from Google Cloud at the path specified by `credentials_path`.

By default:

```text
~/.calendar-workload-runner/credentials.json
```

## First Authentication

The first time you run `sync-calendar` or `daemon --once`, a browser window will open for Google authentication.

After successful authentication, `token.json` will be created automatically.

## Commands

### Generate a `settings.json` template

```bash
calendar_workload_runner generate --output ./settings.json
```

### Sync calendar events

```bash
calendar_workload_runner --config ./settings.json sync-calendar
```

This fetches events from Google Calendar and stores them in SQLite.

### Start or stop the workload based on the current time

```bash
calendar_workload_runner --config ./settings.json control-runner
```

Example outputs:

```text
started workload (pid=12345)
already running (pid=12345)
stopped workload (pid=12345)
idle
```

### Run sync and control once

```bash
calendar_workload_runner --config ./settings.json daemon --once
```

Example outputs:

```text
synced 1 schedule(s)
started workload (pid=12345)
```

```text
synced 1 schedule(s)
already running (pid=12345)
```

```text
synced 1 schedule(s)
stopped workload (pid=12345)
```

```text
synced 1 schedule(s)
idle
```

### Run sync and control continuously

```bash
calendar_workload_runner --config ./settings.json daemon
```

**By default, the daemon uses these settings from `settings.json`:**

- `sync_interval_seconds`
- `control_interval_seconds`

You can override them from the command line:

```bash
calendar_workload_runner --config ./settings.json daemon \
  --sync-interval 900 \
  --control-interval 60
```

## Main `settings.json` Fields

### `calendar_id`

The Google Calendar ID to use. In many cases, `primary` is sufficient.

### `workload_command`

The command to start when the current time is inside a scheduled event.

Example:

```json
"workload_command": "sleep 3000"
```

### `sync_interval_seconds`

How often the daemon should sync events from Google Calendar, in seconds.

Example:

```json
"sync_interval_seconds": 900
```

### `control_interval_seconds`

How often the daemon should check whether the workload should be running, in seconds.

Example:

```json
"control_interval_seconds": 60
```

## Default File Layout

By default, the following files are used:

```text
~/.calendar-workload-runner/
├── credentials.json
├── token.json
├── runner.db
├── logs/
│   ├── workload.log
│   ├── control.log
│   └── sync_calendar.log
└── state/
    └── workload.pid
```

## Development Commands

### Run lint, type checks, and tests

```bash
make check
```

### Run coverage

```bash
make coverage
```

## Current Status

Implemented so far:

- Settings management via `Settings`
- SQLite-based schedule storage
- Google Calendar `sync`
- `workload` start/stop control
- `daemon` command
- `settings.json` template generation

Error handling and failure-path behavior can still be improved in future iterations.

## License

MIT
