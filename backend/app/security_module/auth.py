from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceAuthResult:
    authenticated: bool
    reason: str


class VoiceAuthenticator:
    """Lightweight placeholder for local speaker verification.

    Replace the passphrase check with a local speaker embedding model such as
    SpeechBrain or Resemblyzer when you bundle voice biometric enrollment.
    """

    def __init__(self, enrolled_phrase_hash: str | None = None) -> None:
        self._enrolled_phrase_hash = enrolled_phrase_hash

    def verify_phrase(self, transcript: str) -> VoiceAuthResult:
        if not self._enrolled_phrase_hash:
            return VoiceAuthResult(True, "voice auth not enrolled")
        normalized = " ".join(transcript.lower().split())
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        if digest == self._enrolled_phrase_hash:
            return VoiceAuthResult(True, "phrase matched")
        return VoiceAuthResult(False, "voice passphrase did not match")
