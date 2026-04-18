from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticHit:
    id: str
    text: str
    score: float


class LocalVectorMemory:
    """Interface placeholder for Chroma, LanceDB, or FAISS running locally."""

    def search(self, query: str, limit: int = 5) -> list[SemanticHit]:
        return []

    def upsert(self, item_id: str, text: str) -> None:
        return None
