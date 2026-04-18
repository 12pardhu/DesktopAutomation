from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.schemas.models import MemoryRecord
from app.security_module.crypto import LocalEncryptor


class EncryptedMemoryStore:
    def __init__(self, path: Path, encryptor: LocalEncryptor) -> None:
        self.path = path
        self.encryptor = encryptor
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def list_records(self) -> list[MemoryRecord]:
        payload = self._load()
        return [MemoryRecord(**item) for item in payload.get("records", [])]

    def add(self, kind: str, content: str, metadata: dict[str, Any] | None = None) -> MemoryRecord:
        record = MemoryRecord(
            id=str(uuid.uuid4()),
            kind=kind,
            content=content,
            created_at=datetime.now(timezone.utc),
            metadata=metadata or {},
        )
        payload = self._load()
        payload.setdefault("records", []).append(record.model_dump(mode="json"))
        self._save(payload)
        return record

    def recent_context(self, limit: int = 8) -> str:
        records = self.list_records()[-limit:]
        if not records:
            return "No prior memory."
        return "\n".join(f"- [{item.kind}] {item.content}" for item in records)

    def clear(self) -> None:
        self._save({"records": []})

    def _load(self) -> dict[str, Any]:
        if not self.path.exists() or self.path.stat().st_size == 0:
            return {"records": []}
        return json.loads(self.encryptor.decrypt_text(self.path.read_bytes()))

    def _save(self, payload: dict[str, Any]) -> None:
        self.path.write_bytes(self.encryptor.encrypt_text(json.dumps(payload, ensure_ascii=False)))
