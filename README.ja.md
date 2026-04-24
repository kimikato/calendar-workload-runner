# calendar-workload-runner

[English](README.md) | **日本語**

![Tests](https://github.com/kimikato/calendar-workload-runner/actions/workflows/tests.yml/badge.svg?branch=main)
[![Coverage](https://img.shields.io/codecov/c/github/kimikato/calendar-workload-runner/main?label=coverage&logo=codecov)](https://codecov.io/gh/kimikato/calendar-workload-runner)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Google Calendar の予定をもとに、指定したコマンドを起動・停止するための CLI ツールです。

現在は以下の機能を持ちます。

- Google Calendar から予定を同期する
- 現在時刻が予定内かどうかを判定して `workload` を起動・停止する
- `sync` と `control` をまとめて実行する `daemon` コマンドを持つ
- `settings.json` の雛形を生成できる

## 想定している用途

たとえば以下のような使い方を想定しています。

- Google Calendar に「作業時間」を登録しておく
- その予定の時間だけ、WSL 上で `workload` を動かす
- 予定外の時間になったら `workload` を停止する

## 動作環境

- Python 3.12+
- SQLite3
- Google アカウントがあり、Google Calendar API を利用できること

## インストール

開発環境では以下のようにセットアップします。

```bash
python -m venv .venv
source .venv/bin/activate
make init
```

## Google Calendar API の準備

事前に Google Cloud で以下の設定を行っておく必要があります。

- プロジェクトの作成
- Google Calendar API を有効化
- OAuth 同意画面の設定
- デスクトップアプリ用の OAuth クライアント作成
- `credentials.json` のダウンロード

## 初期設定

### 1. `settings.json` を生成する

```bash
calendar_workload_runner generate --output ./settings.json
```

既に同名ファイルが存在する場合はエラーになります。上書きしたい場合は `--force` を使います。

```bash
calendar_workload_runner generate --output ./settings.json --force
```

### 2. `settings.json` を必要に応じて編集する

生成される例:

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

### 3. `credentials.json` を配置する

`settings.json` の `credentials_path` で指定した場所に、Google Cloud から取得した `credentials.json` を配置します。

デフォルトでは以下のようになります。

```text
~/.calendar-workload-runner/credentials.json
```

## 初回認証

最初に `sync-calendar` または `daemon --once` を実行すると、ブラウザが開いて Google アカウント認証が走ります。

認証に成功すると、`token.json` が生成されます。

## コマンド一覧

### `settings.json` の雛形を生成する

```bash
calendar_workload_runner generate --output ./settings.json
```

### カレンダー予定を同期する

```bash
calendar_workload_runner --config ./settings.json sync-calendar
```

成功すると、Google Calendar から取得した予定が SQLite に保存されます。

### 現在時刻に応じて `workload` を起動・停止する

```bash
calendar_workload_runner --config ./settings.json control-runner
```

出力例:

```text
started workload (pid=12345)
already running (pid=12345)
stopped workload (pid=12345)
idle
```

### `sync` と `control` を1回だけまとめて実行する

```bash
calendar_workload_runner --config ./settings.json daemon --once
```

出力例:

```text
synced 1 schedule(s)
started workload (pid=12345)
```

または

```text
synced 1 schedule(s)
already running (pid=12345)
```

または

```text
synced 1 schedule(s)
stopped workload (pid=12345)
```

または

```text
synced 1 schedule(s)
idle
```

### `sync` と `control` を一定間隔で繰り返し実行する

```bash
calendar_workload_runner --config ./settings.json daemon
```

`settings.json` 内の以下の設定が利用されます。

- `sync_interval_seconds`
- `control_interval_seconds`

CLI 引数で上書きもできます。

```bash
calendar_workload_runner --config ./settings.json daemon \
  --sync-interval 900 \
  --control-interval 60
```

## `settings.json` の主な項目

### `calendar_id`

利用する Google Calendar の ID です。通常は `primary` で構いません。

### `workload_command`

起動したいコマンドです。

例:

```json
"workload_command": "sleep 3000"
```

### `sync_interval_seconds`

`daemon` 実行時に、何秒ごとに Google Calendar の同期を行うかを表します。

例:

```json
"sync_interval_seconds": 900
```

### `control_interval_seconds`

`daemon` 実行時に、何秒ごとに `workload` の起動・停止判定を行うかを表します。

例:

```json
"control_interval_seconds": 60
```

## 初期ファイルレイアウト

デフォルトでは以下のようなファイル構成を利用します。

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

## 開発用コマンド

### テスト・型チェック・lint

```bash
make check
```

### カバレッジ確認

```bash
make coverage
```

## 現在のステータス

現在は以下が実装済みです。

- `Settings` クラスによる設定管理
- SQLite によるスケジュール保存
- Google Calendar との同期
- `workload` の起動・停止制御
- `daemon` コマンド
- `settings.json` 雛形生成

異常系やエラーハンドリングについては、今後さらに改善していく予定です。

## ライセンス

MIT
