from __future__ import annotations

from datetime import datetime, timezone

from app.memory_module.store import EncryptedMemoryStore
from app.schemas.models import ChatResponse, CommandSubmission
from app.services.planner import CommandPlanner
from app.services.queue import TaskQueueManager
from app.voice_module.tts import TextToSpeech


class AssistantOrchestrator:
    def __init__(
        self,
        planner: CommandPlanner,
        queue: TaskQueueManager,
        memory: EncryptedMemoryStore,
        tts: TextToSpeech,
        default_model: str,
    ) -> None:
        self.planner = planner
        self.queue = queue
        self.memory = memory
        self.tts = tts
        self.default_model = default_model

    async def submit_command(
        self,
        message: str,
        requested_language: str,
        model: str | None,
        speak_reply: bool,
        auto_execute: bool,
        store_create_command,
    ) -> CommandSubmission:
        plan, language = await self.planner.plan(message, requested_language, model or self.default_model)
        selected_model = model or self.default_model
        reply = self._build_reply(plan, language)
        command_id = store_create_command(
            command=message,
            language=language,
            reply=reply,
            model=selected_model,
            plan=plan,
            status="queued" if auto_execute and plan.tasks else "planned",
        )
        run_id = None
        if auto_execute and plan.tasks:
            run_id = await self.queue.submit(command_id, plan)
        self.memory.add("command", message, {"language": language, "task_count": len(plan.tasks)})
        self.memory.add("plan", plan.model_dump_json(), {"command_id": command_id})
        if speak_reply:
            self.tts.speak(reply)
        created_at = datetime.now(timezone.utc)
        return CommandSubmission(
            id=command_id,
            command=message,
            language=language,
            model=selected_model,
            reply=reply,
            plan=plan,
            run_id=run_id,
            status="queued" if run_id else "planned",
            created_at=created_at,
        )

    def _build_reply(self, plan, language: str) -> str:
        if not plan.tasks:
            fallback = {
                "hi": "मैंने कोई executable task नहीं पहचाना.",
                "te": "నేను అమలు చేయగల టాస్క్‌ను గుర్తించలేకపోయాను.",
            }
            return fallback.get(language, "I could not identify an executable task.")
        action_summary = ", ".join(task.action.value for task in plan.tasks[:4])
        if len(plan.tasks) > 4:
            action_summary = f"{action_summary}, ..."
        prefix = {
            "hi": "कार्य पंक्ति तैयार है",
            "te": "టాస్క్ క్యూను సిద్ధం చేశాను",
        }.get(language, "Task queue prepared")
        return f"{prefix}: {action_summary}"

    def response_from_submission(self, submission: CommandSubmission) -> ChatResponse:
        return ChatResponse(
            reply=submission.reply,
            language=submission.language,
            model=submission.model,
            plan=submission.plan,
            run_id=submission.run_id,
            status=submission.status,
            created_at=submission.created_at,
        )
