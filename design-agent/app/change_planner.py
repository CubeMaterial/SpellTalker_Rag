from __future__ import annotations

import re

from app.llm_client import OllamaClient
from app.settings import Settings


DEFAULT_TARGETS = [
    "GDD/05_Rune_System.md",
    "GDD/06_Spell_System.md",
    "GDD/17_Balance_Rules.md",
    "GDD/99_TODO.md",
]


class ChangePlanner:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.llm = OllamaClient(self.settings)

    def create_plan(self, idea: str, context_rows: list[dict[str, str]]) -> dict[str, object]:
        context = "\n\n".join(
            f"[{row['path']} / {row['section']}]\n{row['document']}" for row in context_rows
        )
        prompt = f"""사용자 아이디어를 SpellTalker GDD 변경 계획으로 정리하라.

관련 문서:
{context or "검색된 관련 문서 없음"}

사용자 아이디어:
{idea}

반드시 다음 Markdown 형식으로 답하라.

## 변경 계획

### 수정 대상
- GDD/...

### 변경 내용
- ...

### 충돌 가능성
- ...
"""
        response = self.llm.generate(prompt, self.settings.prompt("system_prompt.md"))
        if response.startswith("[LLM unavailable"):
            response = self._fallback_plan(idea)
        targets = self._extract_targets(response)
        return {"markdown": response, "targets": targets}

    def _extract_targets(self, markdown: str) -> list[str]:
        targets = re.findall(r"GDD/[A-Za-z0-9_./-]+\.md", markdown)
        seen: set[str] = set()
        ordered: list[str] = []
        for target in targets + DEFAULT_TARGETS:
            if target not in seen:
                ordered.append(target)
                seen.add(target)
        return ordered

    def _fallback_plan(self, idea: str) -> str:
        return f"""## 변경 계획

### 수정 대상
- GDD/05_Rune_System.md
- GDD/06_Spell_System.md
- GDD/17_Balance_Rules.md
- GDD/99_TODO.md

### 변경 내용
- 사용자 아이디어를 신규 룬, 스펠, 조합 규칙 후보로 기록
- 구체 수치와 실패 판정은 TODO로 보류
- 관련 밸런스 검토 항목 추가

### 충돌 가능성
- 단일 조합 반복 최적해 위험
- 마나 비용과 획득량 검증 필요
- 기존 룬 조합 규칙과 명칭 충돌 여부 확인 필요

### 원문 아이디어
{idea}
"""

