from __future__ import annotations

import re

from app.llm_client import OllamaClient
from app.settings import Settings


KEYWORD_TARGETS = [
    (["룬", "rune"], "GDD/05_Rune_System.md"),
    (["스펠", "spell", "주문"], "GDD/06_Spell_System.md"),
    (["카드", "card", "덱", "deck"], "GDD/04_Card_System.md"),
    (["전투", "combat", "battle", "피해", "공격"], "GDD/03_Combat_System.md"),
    (["상태", "버프", "디버프", "부상", "status", "buff", "debuff"], "GDD/07_Status_Effects.md"),
    (["유물", "relic"], "GDD/08_Relic_System.md"),
    (["캐릭터", "character"], "GDD/09_Character_Design.md"),
    (["적", "enemy", "몬스터"], "GDD/10_Enemy_Design.md"),
    (["보스", "boss"], "GDD/11_Boss_Design.md"),
    (["맵", "노드", "map", "node"], "GDD/12_Map_System.md"),
    (["보상", "reward"], "GDD/13_Reward_System.md"),
    (["상점", "휴식", "이벤트", "shop", "rest", "event"], "GDD/14_Shop_Rest_Event.md"),
    (["세계관", "codex", "world", "lore"], "GDD/15_Codex_World.md"),
    (["ui", "ux", "화면", "입력", "출력"], "GDD/16_UI_UX.md"),
    (["밸런스", "balance", "무한", "금지", "제한", "최적해"], "GDD/17_Balance_Rules.md"),
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
        targets = self._select_targets(response, idea, context_rows)
        return {"markdown": response, "targets": targets}

    def _extract_targets(self, markdown: str) -> list[str]:
        targets = re.findall(r"GDD/[A-Za-z0-9_./-]+\.md", markdown)
        targets.extend(re.findall(r"docs_workspace/(GDD/[A-Za-z0-9_./-]+\.md)", markdown))
        return self._dedupe(targets)

    def _select_targets(self, markdown: str, idea: str, context_rows: list[dict[str, str]]) -> list[str]:
        candidates = []
        candidates.extend(self._extract_targets(markdown))
        candidates.extend(self._context_targets(context_rows))
        candidates.extend(self._keyword_targets(idea))

        include_todo = self._needs_todo(idea, markdown)
        include_balance = self._needs_balance(idea, markdown)
        filtered = []
        for target in candidates:
            if target == "GDD/99_TODO.md" and not include_todo:
                continue
            if target == "GDD/17_Balance_Rules.md" and not include_balance:
                continue
            filtered.append(target)
        filtered = self._dedupe(filtered)
        if not filtered:
            filtered = self._keyword_targets(idea) or ["GDD/99_TODO.md"]
        max_targets = 5 if self._is_large_change(idea, markdown) else 3
        return filtered[:max_targets]

    def _context_targets(self, context_rows: list[dict[str, str]]) -> list[str]:
        targets = []
        for row in context_rows:
            path = row.get("path", "")
            match = re.search(r"(GDD/[A-Za-z0-9_./-]+\.md)", path)
            if match:
                targets.append(match.group(1))
        return targets[:3]

    def _keyword_targets(self, text: str) -> list[str]:
        lowered = text.lower()
        targets = [target for keywords, target in KEYWORD_TARGETS if any(keyword.lower() in lowered for keyword in keywords)]
        if self._needs_todo(text, ""):
            targets.append("GDD/99_TODO.md")
        return self._dedupe(targets)

    def _needs_todo(self, idea: str, markdown: str) -> bool:
        lowered = self._semantic_text(idea, markdown)
        return any(keyword in lowered for keyword in ["todo", "미정", "보류", "확인 필요", "나중", "후속"])

    def _needs_balance(self, idea: str, markdown: str) -> bool:
        lowered = self._semantic_text(idea, markdown)
        return any(keyword in lowered for keyword in ["밸런스", "balance", "무한", "금지", "제한", "최적해", "반복"])

    def _is_large_change(self, idea: str, markdown: str) -> bool:
        lowered = self._semantic_text(idea, markdown)
        return any(keyword in lowered for keyword in ["대규모", "전체", "전반", "시스템 변경", "rework", "전체 구조"])

    def _semantic_text(self, idea: str, markdown: str) -> str:
        text = f"{idea}\n{markdown}".lower()
        text = re.sub(r"(?:docs_workspace/)?gdd/[a-z0-9_./-]+\.md", "", text)
        return text

    def _dedupe(self, targets: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for target in targets:
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
