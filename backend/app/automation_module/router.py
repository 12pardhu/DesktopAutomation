from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.automation_module.platforms import PlatformAutomation
from app.schemas.models import SystemAction


class AutomationRouter:
    def __init__(self, platform_automation: PlatformAutomation) -> None:
        self.platform = platform_automation

    def route(self, text: str) -> SystemAction | None:
        command = text.lower().strip()
        if "delete" in command or "remove file" in command:
            return self._action(
                action="delete_file",
                target=text,
                status="needs_confirmation",
                requires_confirmation=True,
                detail="I can delete files only after explicit confirmation.",
            )
        if command in {"open google", "google", "open google search"}:
            try:
                opened = self.platform.open_url("https://www.google.com")
                return self._action("open_url", opened, "completed", detail="Opened Google")
            except Exception as exc:
                return self._action("open_url", "https://www.google.com", "failed", detail=str(exc))
        site_urls = {
            "open youtube": ("https://www.youtube.com", "YouTube"),
            "open youtube in google": ("https://www.youtube.com", "YouTube"),
            "open youtube in browser": ("https://www.youtube.com", "YouTube"),
            "open gmail": ("https://mail.google.com", "Gmail"),
            "open google mail": ("https://mail.google.com", "Gmail"),
            "open maps": ("https://maps.google.com", "Google Maps"),
        }
        if command in site_urls:
            url, label = site_urls[command]
            try:
                opened = self.platform.open_url(url)
                return self._action("open_url", opened, "completed", detail=f"Opened {label}")
            except Exception as exc:
                return self._action("open_url", url, "failed", detail=str(exc))
        if command in {"open browser", "open web browser"}:
            try:
                opened = self.platform.open_browser()
                return self._action("open_application", opened, "completed", detail=f"Opened {opened}")
            except Exception as exc:
                return self._action("open_application", "browser", "failed", detail=str(exc))
        if command in {"open safari", "open chrome", "open firefox", "open edge"}:
            app_name = {
                "open safari": "Safari",
                "open chrome": "Google Chrome",
                "open firefox": "Firefox",
                "open edge": "Microsoft Edge",
            }[command]
            try:
                opened = self.platform.open_application(app_name)
                return self._action("open_application", opened, "completed", detail=f"Opened {opened}")
            except Exception as exc:
                return self._action("open_application", app_name, "failed", detail=str(exc))
        if command.startswith("open ") and " folder" in command:
            folder_name = command.replace("open", "").replace("folder", "").strip()
            target = self.platform.known_folder(folder_name)
            try:
                opened = self.platform.open_path(target)
                return self._action("open_folder", opened, "completed", detail=f"Opened {opened}")
            except Exception as exc:
                return self._action("open_folder", str(target), "failed", detail=str(exc))
        if command.startswith("search files for "):
            query = command.replace("search files for ", "", 1).strip()
            try:
                results = self.platform.search_files(query)
                detail = "\n".join(str(path) for path in results) if results else "No local files matched."
                return self._action("search_files", query, "completed", detail=detail)
            except Exception as exc:
                return self._action("search_files", query, "failed", detail=str(exc))
        if command in {"open pictures", "open pictures folder", "open photos"}:
            target = self.platform.known_folder("pictures")
            opened = self.platform.open_path(target)
            return self._action("open_folder", opened, "completed", detail=f"Opened {opened}")
        return None

    def _action(
        self,
        action: str,
        target: str,
        status: str,
        requires_confirmation: bool = False,
        detail: str | None = None,
    ) -> SystemAction:
        return SystemAction(
            id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc),
            action=action,
            target=target,
            status=status,
            requires_confirmation=requires_confirmation,
            detail=detail,
        )
