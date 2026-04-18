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
        deterministic_plan = self._deterministic_plan(command)
        if deterministic_plan.tasks:
            return deterministic_plan, language
        llm_plan = await self._plan_with_llm(command, language, model or self.default_model)
        if llm_plan and llm_plan.tasks:
            return llm_plan, language
        return self._fallback_plan(command), language

    def _deterministic_plan(self, command: str) -> TaskPlan:
        normalized = command.lower().strip()
        browser_url_match = re.search(
            r"open\s+(google|browser|chrome|edge|firefox|safari)(?:\s+and|\s+then)?\s+(?:type|enter|search)\s+(.+?)\s*(?:in\s+the\s+url|in\s+the\s+url\s+bar|in\s+the\s+search\s+bar|in\s+url|in\s+search|on\s+google)?$",
            normalized,
        )
        browser_url_as_match = re.search(
            r"open\s+(google|browser|chrome|edge|firefox|safari)(?:\s+and|\s+then)?\s+(?:type|enter|search)\s+in\s+the\s+url(?:\s+bar)?\s+as\s+(.+)$",
            normalized,
        )
        if browser_url_as_match:
            browser = browser_url_as_match.group(1).strip()
            raw_target = browser_url_as_match.group(2).strip()
            target = self._normalize_web_target(raw_target)
            tasks: list[TaskDefinition] = []
            if browser == "google":
                tasks.append(TaskDefinition(action=TaskAction.open_url, url=target))
            else:
                tasks.append(TaskDefinition(action=TaskAction.open_app, app=browser))
                tasks.append(TaskDefinition(action=TaskAction.wait, seconds=2))
                tasks.append(TaskDefinition(action=TaskAction.open_url, url=target))
            return TaskPlan(tasks=tasks)
        if browser_url_match:
            browser = browser_url_match.group(1).strip()
            raw_target = re.sub(r"\s+(?:in\s+the\s+url|in\s+the\s+url\s+bar|in\s+the\s+search\s+bar|in\s+url|in\s+search|on\s+google)$", "", browser_url_match.group(2)).strip()
            target = self._normalize_web_target(raw_target)
            tasks: list[TaskDefinition] = []
            if browser == "google":
                tasks.append(TaskDefinition(action=TaskAction.open_url, url=target))
            else:
                tasks.append(TaskDefinition(action=TaskAction.open_app, app=browser))
                tasks.append(TaskDefinition(action=TaskAction.wait, seconds=2))
                tasks.append(TaskDefinition(action=TaskAction.open_url, url=target))
            return TaskPlan(tasks=tasks)

        simple_google_match = re.search(r"open\s+google(?:\s+and\s+open\s+(.+))?$", normalized)
        if simple_google_match:
            suffix = simple_google_match.group(1)
            if suffix:
                return TaskPlan(tasks=[TaskDefinition(action=TaskAction.open_url, url=self._normalize_web_target(suffix))])
            return TaskPlan(tasks=[TaskDefinition(action=TaskAction.open_url, url="https://www.google.com")])

        open_site_match = re.search(r"open\s+(amazon|amazon\.in|youtube|gmail|google maps|maps)$", normalized)
        if open_site_match:
            return TaskPlan(tasks=[TaskDefinition(action=TaskAction.open_url, url=self._normalize_web_target(open_site_match.group(1)))])

        return TaskPlan(tasks=[])

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
        browser_type_match = re.search(
            r"open\s+(.+?)\s+(?:and|then)\s+type(?:\s+in\s+the\s+(?:search|url)\s+bar(?:\s+as)?|\s+)(.+)",
            segment,
        )
        if browser_type_match:
            app = browser_type_match.group(1).strip()
            text = browser_type_match.group(2).strip().strip('"')
            tasks.append(TaskDefinition(action=TaskAction.open_app, app=app))
            tasks.append(TaskDefinition(action=TaskAction.wait, seconds=2))
            if text.lower():
                tasks.append(TaskDefinition(action=TaskAction.open_url, url=self._normalize_web_target(text)))
            else:
                tasks.append(
                    TaskDefinition(
                        action=TaskAction.type_text,
                        text=text,
                        metadata={"target": "browser_url_bar", "submit": True},
                    )
                )
            return tasks
        if segment.startswith("open ") and any(
            word in segment
            for word in (
                "chrome",
                "firefox",
                "edge",
                "notepad",
                "calculator",
                "vlc",
                "terminal",
                "safari",
                "finder",
                "notes",
                "music",
                "preview",
                "word",
                "excel",
                "powerpoint",
                "vs code",
                "vscode",
            )
        ):
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

    def _normalize_web_target(self, text: str) -> str:
        cleaned = text.strip().strip('"').strip("'")
        cleaned = re.sub(r"^(as|for)\s+", "", cleaned)
        cleaned = cleaned.replace(" ", "")
        known_sites = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "amazon": "https://www.amazon.in",
            "amazon.in": "https://www.amazon.in",
            "gmail": "https://mail.google.com",
            "maps": "https://maps.google.com",
            "googlemaps": "https://maps.google.com",
        }
        if cleaned in known_sites:
            return known_sites[cleaned]
        if "." in cleaned and not cleaned.startswith(("http://", "https://")):
            return f"https://{cleaned}"
        return f"https://www.google.com/search?q={cleaned}"
