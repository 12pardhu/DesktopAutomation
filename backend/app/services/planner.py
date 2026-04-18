from __future__ import annotations

import json
import re
from typing import Any

from app.core.language import detect_language
from app.schemas.models import TaskAction, TaskDefinition, TaskPlan


SUPPORTED_ACTIONS = ", ".join(action.value for action in TaskAction)

PLANNER_PROMPT = """You are an offline desktop automation planner.
Convert the user command into JSON only.
Return exactly one object with this shape:
{"tasks":[{"action":"open_app","app":"chrome"}]}

Rules:
- Output valid JSON only.
- No markdown, no explanation.
- Break complex commands into ordered steps.
- Prefer the supported actions only when possible.
- Supported actions: %s
- Use wait with seconds when app launch timing is needed.
- For file search or file open, keep the original filename.
- For directory navigation, use absolute paths if the command contains a path.
""" % SUPPORTED_ACTIONS


class CommandPlanner:
    def __init__(self, llm: Any, default_model: str) -> None:
        self.llm = llm
        self.default_model = default_model

    async def plan(self, command: str, requested_language: str, model: str | None = None) -> tuple[TaskPlan, str]:
        language = detect_language(command, requested_language)
        llm_plan = await self._plan_with_llm(command, language, model or self.default_model)
        if llm_plan and llm_plan.tasks:
            return llm_plan, language
        return self._fallback_plan(command), language

    async def _plan_with_llm(self, command: str, language: str, model: str) -> TaskPlan | None:
        prompt = f"{PLANNER_PROMPT}\nLanguage: {language}\nCommand: {command}\nJSON:"
        try:
            raw = await self.llm.generate(prompt, model=model)
        except Exception:
            return None
        return self._parse_json(raw)

    def _parse_json(self, raw: str) -> TaskPlan | None:
        raw = raw.strip()
        if not raw:
            return None
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(0))
            return TaskPlan.model_validate(data)
        except Exception:
            return None

    def _fallback_plan(self, command: str) -> TaskPlan:
        lowered = command.lower().strip()
        folder_and_file = re.search(
            r"open\s+(.+?)\s+(?:folder|directory)\s+(?:and|then)\s+open\s+([A-Za-z0-9_. -]+\.[A-Za-z0-9]+)",
            lowered,
        )
        if folder_and_file:
            return TaskPlan(
                tasks=[
                    TaskDefinition(action=TaskAction.navigate_directory, path=folder_and_file.group(1).strip()),
                    TaskDefinition(action=TaskAction.search_file, filename=folder_and_file.group(2).strip()),
                    TaskDefinition(action=TaskAction.open_file, filename=folder_and_file.group(2).strip()),
                ]
            )
        search_and_open = re.search(
            r"search(?:\s+file|\s+files)?\s+(?:for\s+)?([A-Za-z0-9_. -]+\.[A-Za-z0-9]+)\s+(?:and|then)\s+open(?:\s+it)?",
            lowered,
        )
        if search_and_open:
            filename = search_and_open.group(1).strip()
            return TaskPlan(
                tasks=[
                    TaskDefinition(action=TaskAction.search_file, filename=filename),
                    TaskDefinition(action=TaskAction.open_file, filename=filename),
                ]
            )
        segments = [segment.strip(" ,.") for segment in re.split(r"\b(?:then|and then|after that)\b", lowered) if segment.strip()]
        tasks: list[TaskDefinition] = []
        for segment in segments or [lowered]:
            tasks.extend(self._segment_tasks(segment))
        if not tasks:
            tasks.append(TaskDefinition(action=TaskAction.wait, seconds=1, metadata={"note": "No direct action matched"}))
        return TaskPlan(tasks=tasks)

    def _segment_tasks(self, segment: str) -> list[TaskDefinition]:
        tasks: list[TaskDefinition] = []
        if segment.startswith("open ") and any(word in segment for word in ("chrome", "firefox", "edge", "notepad", "calculator", "vlc")):
            app = segment.replace("open ", "", 1).strip()
            tasks.append(TaskDefinition(action=TaskAction.open_app, app=app))
            if "youtube" in segment:
                tasks.append(TaskDefinition(action=TaskAction.wait, seconds=2))
                tasks.append(TaskDefinition(action=TaskAction.open_url, url="https://www.youtube.com"))
            return tasks
        if "youtube" in segment:
            tasks.append(TaskDefinition(action=TaskAction.open_url, url="https://www.youtube.com"))
            return tasks
        path_match = re.search(r"([a-zA-Z]:[\\/][^,]+|/[A-Za-z0-9._\-/ ]+)", segment)
        if segment.startswith("open ") and path_match:
            tasks.append(TaskDefinition(action=TaskAction.navigate_directory, path=path_match.group(1).strip()))
            return tasks
        if "search" in segment and "file" in segment:
            filename = self._extract_filename(segment)
            tasks.append(TaskDefinition(action=TaskAction.search_file, filename=filename))
            if segment.startswith("open "):
                tasks.append(TaskDefinition(action=TaskAction.open_file, filename=filename))
            return tasks
        if segment.startswith("type "):
            tasks.append(TaskDefinition(action=TaskAction.type_text, text=segment.replace("type ", "", 1).strip()))
            return tasks
        if segment.startswith("wait "):
            seconds = self._extract_seconds(segment)
            tasks.append(TaskDefinition(action=TaskAction.wait, seconds=seconds))
            return tasks
        if segment.startswith("click"):
            x, y = self._extract_coordinates(segment)
            tasks.append(TaskDefinition(action=TaskAction.click, x=x, y=y))
            return tasks
        if segment.startswith("open ") and self._looks_like_filename(segment):
            filename = self._extract_filename(segment.replace("open ", "", 1))
            tasks.append(TaskDefinition(action=TaskAction.search_file, filename=filename))
            tasks.append(TaskDefinition(action=TaskAction.open_file, filename=filename))
            return tasks
        if segment.startswith("open "):
            target = segment.replace("open ", "", 1).strip()
            if "folder" in target or "/" in target or "\\" in target:
                tasks.append(TaskDefinition(action=TaskAction.navigate_directory, path=target.replace("folder", "").strip()))
            else:
                tasks.append(TaskDefinition(action=TaskAction.open_app, app=target))
            return tasks
        return tasks

    def _extract_filename(self, text: str) -> str:
        match = re.search(r"([A-Za-z0-9_. -]+\.[A-Za-z0-9]+)", text)
        if match:
            return match.group(1).strip()
        cleaned = re.sub(r"^(search|for|file|files|open)\s+", "", text).strip()
        return cleaned

    def _extract_seconds(self, text: str) -> float:
        match = re.search(r"(\d+(?:\.\d+)?)", text)
        return float(match.group(1)) if match else 1.0

    def _extract_coordinates(self, text: str) -> tuple[int | None, int | None]:
        matches = re.findall(r"(\d+)", text)
        if len(matches) >= 2:
            return int(matches[0]), int(matches[1])
        return None, None

    def _looks_like_filename(self, text: str) -> bool:
        return bool(re.search(r"\.[A-Za-z0-9]{1,6}\b", text))
