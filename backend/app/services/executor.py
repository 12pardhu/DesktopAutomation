from __future__ import annotations

import asyncio
import platform as platform_module
import subprocess
from pathlib import Path
from typing import Any

from app.automation_module.platforms import PlatformAutomation
from app.schemas.models import TaskAction, TaskDefinition

try:
    import pyautogui
except Exception:  # pragma: no cover - optional dependency
    pyautogui = None


class TaskExecutor:
    def __init__(self, platform: PlatformAutomation) -> None:
        self.platform = platform
        self.current_directory = Path.home()
        self.system = platform_module.system().lower()

    def reset_context(self) -> None:
        self.current_directory = Path.home()

    async def execute(self, task: TaskDefinition) -> tuple[str, dict[str, Any]]:
        action = task.action
        if action == TaskAction.open_app:
            app = task.app or ""
            opened = self.platform.open_application(app)
            return f"Opened application {opened}", {"app": opened}
        if action == TaskAction.navigate_directory:
            raw_path = task.path or ""
            target = self.platform.resolve_directory(raw_path)
            opened = self.platform.open_path(target)
            self.current_directory = Path(opened)
            return f"Opened directory {opened}", {"path": opened}
        if action == TaskAction.search_file:
            filename = task.filename or ""
            matches = self.platform.search_files(filename, search_root=self.current_directory)
            return f"Found {len(matches)} file(s) for {filename}", {"matches": [str(match) for match in matches]}
        if action == TaskAction.open_file:
            filename = task.filename or ""
            opened = self.platform.open_file_match(filename, search_root=self.current_directory)
            return f"Opened file {opened}", {"path": opened}
        if action == TaskAction.type_text:
            text = task.text or ""
            if pyautogui is not None:
                if task.metadata.get("target") == "browser_url_bar" and self.system == "darwin":
                    pyautogui.hotkey("command", "l")
                    await asyncio.sleep(0.2)
                pyautogui.write(text, interval=0.02)
                if task.metadata.get("submit"):
                    pyautogui.press("enter")
                return f"Typed text: {text}", {"text": text}
            if self.system == "darwin":
                self._type_text_macos(text, task.metadata)
                return f"Typed text: {text}", {"text": text}
            raise RuntimeError("Keyboard automation is not available. Install pyautogui or use macOS fallback.")
        if action == TaskAction.click:
            if pyautogui is None:
                raise RuntimeError("pyautogui is not installed for mouse automation.")
            if task.x is not None and task.y is not None:
                pyautogui.click(task.x, task.y, button=task.button or "left")
                return f"Clicked at ({task.x}, {task.y})", {"x": task.x, "y": task.y, "button": task.button}
            pyautogui.click(button=task.button or "left")
            return "Clicked current cursor position", {"button": task.button}
        if action == TaskAction.wait:
            seconds = task.seconds or 1
            await asyncio.sleep(seconds)
            return f"Waited for {seconds} seconds", {"seconds": seconds}
        if action == TaskAction.open_url:
            if not task.url:
                raise RuntimeError("Missing url for open_url action.")
            opened = self.platform.open_url(task.url)
            return f"Opened URL {opened}", {"url": opened}
        raise RuntimeError(f"Unsupported action: {action.value}")

    def _type_text_macos(self, text: str, metadata: dict[str, Any]) -> None:
        escaped_text = text.replace("\\", "\\\\").replace('"', '\\"')
        commands: list[str] = []
        if metadata.get("target") == "browser_url_bar":
            commands.append('key code 37 using command down')
            commands.append("delay 0.2")
        commands.append(f'keystroke "{escaped_text}"')
        if metadata.get("submit"):
            commands.append("key code 36")
        script = [
            'tell application "System Events"',
            *[f"  {command}" for command in commands],
            "end tell",
        ]
        subprocess.run(["osascript", "-e", "\n".join(script)], check=True)
