from __future__ import annotations

import os
import platform
import subprocess
import webbrowser
from pathlib import Path


class PlatformAutomation:
    def __init__(self) -> None:
        self.system = platform.system().lower()

    def open_path(self, path: Path) -> str:
        target = path.expanduser().resolve()
        if not target.exists():
            raise FileNotFoundError(str(target))
        self._system_open(target)
        return str(target)

    def open_application(self, name: str) -> str:
        normalized = name.strip()
        if self.system == "darwin":
            subprocess.Popen(["open", "-a", normalized])
        elif self.system == "windows":
            subprocess.Popen([normalized], shell=False)
        else:
            subprocess.Popen([normalized], shell=False)
        return normalized

    def open_url(self, url: str) -> str:
        webbrowser.open(url, new=2)
        return url

    def known_folder(self, name: str) -> Path:
        home = Path.home()
        normalized = name.lower().strip()
        mapping = {
            "pictures": home / "Pictures",
            "photos": home / "Pictures",
            "downloads": home / "Downloads",
            "documents": home / "Documents",
            "desktop": home / "Desktop",
            "music": home / "Music",
            "videos": home / "Videos",
            "home": home,
        }
        return mapping.get(normalized, home / name)

    def resolve_directory(self, raw_path: str) -> Path:
        candidate = Path(raw_path).expanduser()
        if candidate.exists():
            return candidate.resolve()
        if ":" not in raw_path and not raw_path.startswith("/"):
            guessed = self.known_folder(raw_path.replace("folder", "").strip())
            return guessed.resolve() if guessed.exists() else guessed
        return candidate

    def search_files(self, query: str, search_root: Path | None = None, max_results: int = 20) -> list[Path]:
        root_path = search_root or Path.home()
        matches: list[Path] = []
        lowered = query.lower()
        for root, dirs, files in os.walk(root_path):
            dirs[:] = [name for name in dirs if not name.startswith(".")]
            for name in files:
                if lowered in name.lower():
                    matches.append(Path(root) / name)
                    if len(matches) >= max_results:
                        return matches
        return matches

    def open_file_match(self, filename: str, search_root: Path | None = None) -> str:
        matches = self.search_files(filename, search_root=search_root, max_results=1)
        if not matches:
            raise FileNotFoundError(filename)
        self._system_open(matches[0])
        return str(matches[0])

    def _system_open(self, target: Path) -> None:
        if self.system == "darwin":
            subprocess.Popen(["open", str(target)])
        elif self.system == "windows":
            os.startfile(str(target))  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(target)])
