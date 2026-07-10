from __future__ import annotations

from app.document_search import DocumentSearch
from app.rag import RagStore
from app.settings import Settings


class RAGService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.rag = RagStore(self.settings)
        self.fallback = DocumentSearch(self.settings)

    def search(self, query: str, limit: int | None = None, min_results: int = 3) -> list[dict[str, str]]:
        top_k = limit or self.settings.top_k
        rows = self._normalize_rows(self.rag.search(query, top_k=top_k), source="rag")
        if len(rows) >= min_results:
            return rows[:top_k]

        fallback_rows = self._normalize_rows(self.fallback.search(query, limit=top_k), source="fallback")
        return self._merge(rows, fallback_rows, top_k)

    def status_context(self, limit: int = 10) -> list[dict[str, str]]:
        rows = self.search(
            "현재 상태 완료 미완성 TODO 우선순위 프로토타입 구현 상태 위험 요소",
            limit=limit,
            min_results=3,
        )
        if len(rows) >= min(3, limit):
            return rows[:limit]

        return self._merge(rows, self._normalize_rows(self.fallback.status_context(limit), source="fallback"), limit)

    def context_text(self, rows: list[dict[str, str]]) -> str:
        if not rows:
            return "검색된 관련 문서 없음"
        return "\n\n".join(f"[{row['path']} / {row['section']}]\n{row['document']}" for row in rows)

    def _normalize_rows(self, rows: list[dict[str, str]], source: str) -> list[dict[str, str]]:
        normalized = []
        for row in rows:
            path = row.get("path", "")
            if source == "rag" and path and not path.startswith(("docs_workspace/", "source_docs/", "storage/")):
                path = f"docs_workspace/{path}"
            normalized.append(
                {
                    "document": row.get("document", ""),
                    "path": path,
                    "section": row.get("section", "Document"),
                    "distance": row.get("distance", ""),
                    "source": source,
                }
            )
        return normalized

    def _merge(self, primary: list[dict[str, str]], fallback: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
        seen: set[tuple[str, str]] = set()
        merged: list[dict[str, str]] = []
        for row in primary + fallback:
            key = (row.get("path", ""), row.get("section", ""))
            if key in seen:
                continue
            seen.add(key)
            merged.append(row)
            if len(merged) >= limit:
                break
        return merged
