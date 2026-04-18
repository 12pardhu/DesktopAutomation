from __future__ import annotations

from app.automation_module.router import AutomationRouter
from app.llm_module.provider import LLMProvider
from app.memory_module.store import EncryptedMemoryStore


SYSTEM_PROMPT = """You are a private offline desktop assistant.
Rules:
- Never suggest cloud services or internet access.
- Reply in the user's language when possible.
- Ask for confirmation before destructive file or system actions.
- Keep answers concise and actionable.
"""


class AssistantService:
    def __init__(
        self,
        llm: LLMProvider,
        memory: EncryptedMemoryStore,
        automation: AutomationRouter,
        default_model: str,
    ) -> None:
        self.llm = llm
        self.memory = memory
        self.automation = automation
        self.default_model = default_model

    async def handle_message(self, message: str, language: str, model: str | None = None) -> tuple[str, list[dict]]:
        action = self.automation.route(message)
        if action:
            result = action.model_dump(mode="json")
            self.memory.add("system_action", f"{action.action}: {action.target}", {"status": action.status})
            if action.status == "completed":
                return f"Done: {action.detail or action.target}", [result]
            return action.detail or "This action needs confirmation.", [result]

        context = self.memory.recent_context()
        prompt = f"{SYSTEM_PROMPT}\nLanguage: {language}\nLocal memory:\n{context}\n\nUser: {message}\nAssistant:"
        try:
            reply = await self.llm.generate(prompt, model=model or self.default_model)
        except Exception:
            reply = (
                "I could not reach the local LLM. Start Ollama and make sure the selected model is installed, "
                "or use a desktop command such as 'open google' or 'open pictures folder'."
            )
        self.memory.add("conversation", f"User: {message}\nAssistant: {reply}", {"language": language})
        return reply, []
