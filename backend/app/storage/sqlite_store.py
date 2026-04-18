from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from app.schemas.models import AnalyticsSummary, CommandHistoryItem, RunRecord, TaskPlan, TaskStepRecord


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def from_iso(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class SQLiteStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()
        try:
            self.path.chmod(0o600)
        except OSError:
            pass

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            conn = sqlite3.connect(self.path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            try:
                yield conn
                conn.commit()
            finally:
                conn.close()

    def _initialize(self) -> None:
        with self.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS commands (
                    id TEXT PRIMARY KEY,
                    command TEXT NOT NULL,
                    language TEXT NOT NULL,
                    reply TEXT NOT NULL,
                    model TEXT NOT NULL,
                    status TEXT NOT NULL,
                    plan_json TEXT NOT NULL,
                    task_count INTEGER NOT NULL DEFAULT 0,
                    run_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    command_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    current_step INTEGER NOT NULL DEFAULT 0,
                    total_steps INTEGER NOT NULL DEFAULT 0,
                    last_message TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(command_id) REFERENCES commands(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS task_steps (
                    id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    step_index INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    parameters_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    message TEXT,
                    result_json TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY(run_id) REFERENCES runs(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )

    def save_settings(self, settings: dict[str, Any]) -> None:
        with self.connection() as conn:
            for key, value in settings.items():
                conn.execute(
                    """
                    INSERT INTO app_settings(key, value)
                    VALUES(?, ?)
                    ON CONFLICT(key) DO UPDATE SET value = excluded.value
                    """,
                    (key, json.dumps(value)),
                )

    def load_settings(self) -> dict[str, Any]:
        with self.connection() as conn:
            rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
        return {row["key"]: json.loads(row["value"]) for row in rows}

    def create_command(
        self,
        command: str,
        language: str,
        reply: str,
        model: str,
        plan: TaskPlan,
        status: str,
    ) -> str:
        command_id = str(uuid.uuid4())
        now = utcnow()
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO commands(id, command, language, reply, model, status, plan_json, task_count, created_at, updated_at)
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    command_id,
                    command,
                    language,
                    reply,
                    model,
                    status,
                    plan.model_dump_json(),
                    len(plan.tasks),
                    to_iso(now),
                    to_iso(now),
                ),
            )
        return command_id

    def attach_run(self, command_id: str, total_steps: int) -> str:
        run_id = str(uuid.uuid4())
        now = utcnow()
        with self.connection() as conn:
            conn.execute(
                """
                INSERT INTO runs(id, command_id, status, total_steps, created_at, updated_at)
                VALUES(?, ?, 'queued', ?, ?, ?)
                """,
                (run_id, command_id, total_steps, to_iso(now), to_iso(now)),
            )
            conn.execute(
                "UPDATE commands SET run_id = ?, status = 'queued', updated_at = ? WHERE id = ?",
                (run_id, to_iso(now), command_id),
            )
        return run_id

    def create_run_steps(self, run_id: str, plan: TaskPlan) -> None:
        with self.connection() as conn:
            for index, task in enumerate(plan.tasks, start=1):
                conn.execute(
                    """
                    INSERT INTO task_steps(id, run_id, step_index, action, parameters_json, status, result_json)
                    VALUES(?, ?, ?, ?, ?, 'queued', '{}')
                    """,
                    (
                        str(uuid.uuid4()),
                        run_id,
                        index,
                        task.action.value,
                        json.dumps(task.model_dump(mode="json")),
                    ),
                )

    def mark_run_running(self, run_id: str) -> None:
        now = utcnow()
        with self.connection() as conn:
            conn.execute(
                "UPDATE runs SET status = 'running', started_at = COALESCE(started_at, ?), updated_at = ? WHERE id = ?",
                (to_iso(now), to_iso(now), run_id),
            )
            conn.execute(
                """
                UPDATE commands
                SET status = 'running', updated_at = ?
                WHERE run_id = ?
                """,
                (to_iso(now), run_id),
            )

    def mark_step_running(self, step_id: str, run_id: str, step_index: int, message: str) -> None:
        now = utcnow()
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE task_steps
                SET status = 'running', started_at = COALESCE(started_at, ?), message = ?
                WHERE id = ?
                """,
                (to_iso(now), message, step_id),
            )
            conn.execute(
                """
                UPDATE runs
                SET current_step = ?, last_message = ?, updated_at = ?
                WHERE id = ?
                """,
                (step_index, message, to_iso(now), run_id),
            )

    def mark_step_complete(self, step_id: str, run_id: str, message: str, result: dict[str, Any]) -> None:
        now = utcnow()
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE task_steps
                SET status = 'completed', finished_at = ?, message = ?, result_json = ?
                WHERE id = ?
                """,
                (to_iso(now), message, json.dumps(result), step_id),
            )
            conn.execute(
                "UPDATE runs SET last_message = ?, updated_at = ? WHERE id = ?",
                (message, to_iso(now), run_id),
            )

    def mark_step_failed(self, step_id: str, run_id: str, message: str, result: dict[str, Any]) -> None:
        now = utcnow()
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE task_steps
                SET status = 'failed', finished_at = ?, message = ?, result_json = ?
                WHERE id = ?
                """,
                (to_iso(now), message, json.dumps(result), step_id),
            )
            conn.execute(
                "UPDATE runs SET status = 'failed', finished_at = ?, last_message = ?, updated_at = ? WHERE id = ?",
                (to_iso(now), message, to_iso(now), run_id),
            )
            conn.execute(
                """
                UPDATE commands
                SET status = 'failed', updated_at = ?
                WHERE run_id = ?
                """,
                (to_iso(now), run_id),
            )

    def mark_run_complete(self, run_id: str, status: str, message: str) -> None:
        now = utcnow()
        with self.connection() as conn:
            conn.execute(
                """
                UPDATE runs
                SET status = ?, finished_at = ?, last_message = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, to_iso(now), message, to_iso(now), run_id),
            )
            conn.execute(
                """
                UPDATE commands
                SET status = ?, updated_at = ?
                WHERE run_id = ?
                """,
                (status, to_iso(now), run_id),
            )

    def get_next_queued_runs(self) -> list[str]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT id FROM runs WHERE status = 'queued' ORDER BY created_at ASC"
            ).fetchall()
        return [row["id"] for row in rows]

    def get_run(self, run_id: str) -> RunRecord | None:
        with self.connection() as conn:
            row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
            if not row:
                return None
            step_rows = conn.execute(
                "SELECT * FROM task_steps WHERE run_id = ? ORDER BY step_index ASC",
                (run_id,),
            ).fetchall()
        return RunRecord(
            id=row["id"],
            command_id=row["command_id"],
            status=row["status"],
            started_at=from_iso(row["started_at"]),
            finished_at=from_iso(row["finished_at"]),
            current_step=row["current_step"],
            total_steps=row["total_steps"],
            last_message=row["last_message"],
            steps=[self._step_from_row(step_row) for step_row in step_rows],
        )

    def list_commands(self, limit: int = 50) -> list[CommandHistoryItem]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT * FROM commands ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            CommandHistoryItem(
                id=row["id"],
                command=row["command"],
                language=row["language"],
                status=row["status"],
                reply=row["reply"],
                model=row["model"],
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                run_id=row["run_id"],
                task_count=row["task_count"],
            )
            for row in rows
        ]

    def list_active_runs(self) -> list[RunRecord]:
        with self.connection() as conn:
            rows = conn.execute(
                "SELECT id FROM runs WHERE status IN ('queued', 'running') ORDER BY created_at ASC"
            ).fetchall()
        return [run for row in rows if (run := self.get_run(row["id"])) is not None]

    def analytics(self) -> AnalyticsSummary:
        with self.connection() as conn:
            total_commands = conn.execute("SELECT COUNT(*) FROM commands").fetchone()[0]
            completed_runs = conn.execute("SELECT COUNT(*) FROM runs WHERE status = 'completed'").fetchone()[0]
            failed_runs = conn.execute("SELECT COUNT(*) FROM runs WHERE status = 'failed'").fetchone()[0]
            queued_runs = conn.execute("SELECT COUNT(*) FROM runs WHERE status = 'queued'").fetchone()[0]
            running_runs = conn.execute("SELECT COUNT(*) FROM runs WHERE status = 'running'").fetchone()[0]
            total_steps = conn.execute("SELECT COUNT(*) FROM task_steps").fetchone()[0]
            top_rows = conn.execute(
                """
                SELECT action, COUNT(*) AS count
                FROM task_steps
                GROUP BY action
                ORDER BY count DESC, action ASC
                LIMIT 5
                """
            ).fetchall()
        attempted = completed_runs + failed_runs
        success_rate = round((completed_runs / attempted) * 100, 2) if attempted else 0.0
        return AnalyticsSummary(
            total_commands=total_commands,
            completed_runs=completed_runs,
            failed_runs=failed_runs,
            queued_runs=queued_runs,
            running_runs=running_runs,
            success_rate=success_rate,
            total_steps=total_steps,
            top_actions=[{"action": row["action"], "count": row["count"]} for row in top_rows],
        )

    def _step_from_row(self, row: sqlite3.Row) -> TaskStepRecord:
        return TaskStepRecord(
            id=row["id"],
            run_id=row["run_id"],
            step_index=row["step_index"],
            action=row["action"],
            parameters=json.loads(row["parameters_json"]),
            status=row["status"],
            started_at=from_iso(row["started_at"]),
            finished_at=from_iso(row["finished_at"]),
            message=row["message"],
            result=json.loads(row["result_json"]),
        )
