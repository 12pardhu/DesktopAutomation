from __future__ import annotations

import asyncio
import contextlib

from app.schemas.models import TaskDefinition, TaskPlan
from app.services.executor import TaskExecutor
from app.storage.sqlite_store import SQLiteStore


class TaskQueueManager:
    def __init__(self, store: SQLiteStore, executor: TaskExecutor) -> None:
        self.store = store
        self.executor = executor
        self.queue: asyncio.Queue[str] = asyncio.Queue()
        self._worker_task: asyncio.Task[None] | None = None
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        for run_id in self.store.get_next_queued_runs():
            await self.queue.put(run_id)
        self._worker_task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker_task

    async def submit(self, command_id: str, plan: TaskPlan) -> str:
        run_id = self.store.attach_run(command_id, total_steps=len(plan.tasks))
        self.store.create_run_steps(run_id, plan)
        await self.queue.put(run_id)
        return run_id

    async def _worker(self) -> None:
        while True:
            run_id = await self.queue.get()
            try:
                await self._process_run(run_id)
            finally:
                self.queue.task_done()

    async def _process_run(self, run_id: str) -> None:
        run = self.store.get_run(run_id)
        if run is None or run.status not in {"queued", "running"}:
            return
        self.executor.reset_context()
        self.store.mark_run_running(run_id)
        latest_message = "No tasks were executed."
        for step in run.steps:
            if step.status == "completed":
                continue
            message = f"Executing {step.action} ({step.step_index}/{run.total_steps})"
            self.store.mark_step_running(step.id, run_id, step.step_index, message)
            try:
                result_message, result = await self.executor.execute(TaskDefinition.model_validate(step.parameters))
            except Exception as exc:
                self.store.mark_step_failed(step.id, run_id, str(exc), {"error": str(exc)})
                return
            self.store.mark_step_complete(step.id, run_id, result_message, result)
            latest_message = result_message
        self.store.mark_run_complete(run_id, "completed", latest_message)
