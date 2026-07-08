from __future__ import annotations

import re
from pathlib import Path

from app.settings import PROJECT_ROOT, Settings


class DocumentSearch:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()

    def search(self, query: str, limit: int = 8) -> list[dict[str, str]]:
        keywords = self._keywords(query)
        roots = [
            (1, self.settings.docs_workspace / "GDD"),
            (2, self.settings.docs_workspace / "Dev"),
            (3, self.settings.source_docs),
            (4, self.settings.reports_path),
        ]
        rows: list[tuple[int, int, dict[str, str]]] = []
        for priority, root in roots:
            if not root.exists():
                continue
            for path in sorted(root.rglob("*.md")):
                text = path.read_text(encoding="utf-8")
                chunks = self._chunks(text)
                for chunk in chunks:
                    score = self._score(chunk, path.name, keywords)
                    if score <= 0:
                        continue
                    rows.append(
                        (
                            priority,
                            -score,
                            {
                                "path": path.relative_to(PROJECT_ROOT).as_posix(),
                                "document": chunk[:1600],
                                "section": self._section(chunk),
                            },
                        )
                    )
        rows.sort(key=lambda row: (row[0], row[1], row[2]["path"]))
        return [row[2] for row in rows[:limit]]

    def status_context(self, limit: int = 10) -> list[dict[str, str]]:
        preferred = [
            self.settings.source_docs / "07_Package_Rebuild_Checklist.md",
            self.settings.docs_workspace / "GDD" / "99_TODO.md",
            self.settings.reports_path / "consistency_report.md",
        ]
        rows = []
        for path in preferred:
            if path.exists():
                text = path.read_text(encoding="utf-8")
                rows.append(
                    {
                        "path": path.relative_to(PROJECT_ROOT).as_posix(),
                        "section": self._section(text),
                        "document": text[:2200],
                    }
                )
        if len(rows) < limit:
            rows.extend(self.search("현재 상태 완료 미완성 TODO 우선순위 프로토타입", limit=limit - len(rows)))
        return rows[:limit]

    def context_text(self, rows: list[dict[str, str]]) -> str:
        if not rows:
            return "검색된 관련 문서 없음"
        return "\n\n".join(f"[{row['path']} / {row['section']}]\n{row['document']}" for row in rows)

    def _chunks(self, text: str) -> list[str]:
        sections = re.split(r"(?=^##\s+)", text, flags=re.MULTILINE)
        return [section.strip() for section in sections if section.strip()] or [text]

    def _section(self, text: str) -> str:
        match = re.search(r"^##\s+(.+)$", text, re.MULTILINE)
        if match:
            return match.group(1).strip()
        match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        return match.group(1).strip() if match else "Document"

    def _keywords(self, query: str) -> list[str]:
        tokens = re.findall(r"[A-Za-z0-9_가-힣]+", query.lower())
        return [token for token in tokens if len(token) >= 2]

    def _score(self, chunk: str, filename: str, keywords: list[str]) -> int:
        haystack = f"{filename}\n{chunk}".lower()
        return sum(haystack.count(keyword) for keyword in keywords)

