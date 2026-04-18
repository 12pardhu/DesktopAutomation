from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass
class SessionToken:
    value: str
    expires_at: datetime


@dataclass
class LocalAuthService:
    enabled: bool
    password: str
    session_minutes: int = 480
    _sessions: dict[str, SessionToken] = field(default_factory=dict)

    def login(self, password: str) -> str | None:
        if not self.enabled:
            return None
        if password != self.password:
            return None
        token = secrets.token_urlsafe(24)
        self._sessions[token] = SessionToken(
            value=token,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=self.session_minutes),
        )
        return token

    def validate(self, token: str | None) -> bool:
        if not self.enabled:
            return True
        if not token:
            return False
        session = self._sessions.get(token)
        if session is None:
            return False
        if session.expires_at <= datetime.now(timezone.utc):
            self._sessions.pop(token, None)
            return False
        return True
