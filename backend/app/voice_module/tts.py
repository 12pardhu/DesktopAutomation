from __future__ import annotations

import threading

try:
    import pyttsx3
except Exception:  # pragma: no cover - optional dependency
    pyttsx3 = None


class TextToSpeech:
    def __init__(self, engine: str) -> None:
        self.engine = engine
        self._lock = threading.Lock()
        self._driver = pyttsx3.init() if engine == "pyttsx3" and pyttsx3 is not None else None

    def synthesize(self, text: str) -> bytes:
        return text.encode("utf-8")

    def speak(self, text: str) -> None:
        if self._driver is None:
            return
        with self._lock:
            self._driver.say(text)
            self._driver.runAndWait()
