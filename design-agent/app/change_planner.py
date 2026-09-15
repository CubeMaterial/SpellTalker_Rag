from __future__ import annotations

import re

from app.llm_client import OllamaClient
from app.settings import Settings


KEYWORD_TARGETS = [
    (["층", "지상", "지하", "진행", "경로", "방향", "분기", "루프"], "GDD/02_Core_Loop.md"),
    (["맵", "노드", "map", "node", "층", "지상", "지하", "경로", "방향", "분기"], "GDD/12_Map_System.md"),
    (["룬", "rune"], "GDD/05_Rune_System.md"),
    (["스펠", "spell", "주문"], "GDD/06_Spell_System.md"),
    (["카드", "card", "덱", "deck"], "GDD/04_Card_System.md"),
    (["전투", "combat", "battle", "피해", "공격", "hp", "체력", "능력치", "스탯", "stats"], "GDD/03_Combat_System.md"),
    (["상태", "버프", "디버프", "부상", "status", "buff", "debuff"], "GDD/07_Status_Effects.md"),
    (["유물", "relic"], "GDD/08_Relic_System.md"),
    (["캐릭터", "character"], "GDD/09_Character_Design.md"),
    (["보스", "boss"], "GDD/11_Boss_Design.md"),
    (["적", "enemy", "몬스터"], "GDD/10_Enemy_Design.md"),
    (["보상", "reward", "골드"], "GDD/13_Reward_System.md"),
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
        keyword_targets = self._keyword_targets(idea)
        candidates.extend(keyword_targets)
        candidates.extend(self._context_targets(context_rows))
        candidates.extend(self._extract_targets(markdown))

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
            filtered = keyword_targets or ["GDD/99_TODO.md"]
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
        return any(
            keyword in lowered
            for keyword in ["대규모", "전체", "전반", "시스템 변경", "rework", "전체 구조", "맵", "층", "지상", "지하", "분기", "보스"]
        )

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
        targets = self._keyword_targets(idea)
        if not targets:
            targets = ["GDD/99_TODO.md"]
        target_lines = "\n".join(f"- {target}" for target in targets[:5])
        lowered = idea.lower()
        if any(keyword in lowered for keyword in ["맵", "층", "지상", "지하", "경로", "방향", "분기", "보스"]):
            change_lines = """- 맵의 층 구조, 진행 방향, 분기 조건을 기획 규칙으로 기록
- 보스 처치 여부에 따른 다음 층 진입 조건을 정리
- 지상/지하 분기와 엔딩 조건을 TODO 또는 확정 규칙으로 분리"""
            conflict_lines = """- 층 이동 조건과 보스 처치 조건의 우선순위 확인 필요
- 지상 4층 진입과 지하 분기 조건이 UI/맵 노드 표현과 충돌하지 않는지 확인 필요
- 진 엔딩 조건이 일반 클리어 조건과 혼동되지 않도록 명칭 정리 필요"""
        else:
            change_lines = """- 사용자 아이디어를 관련 GDD 문서에 기획 후보로 기록
- 구체 수치와 실패 판정은 TODO로 보류
- 관련 시스템과의 충돌 검토 항목 추가"""
            conflict_lines = """- 기존 핵심 루프와 책임 범위 충돌 여부 확인 필요
- UI 표시와 실제 규칙 적용 위치 분리 필요
- 반복 최적해 또는 예외 처리 누락 여부 확인 필요"""
        return f"""## 변경 계획

### 수정 대상
{target_lines}

### 변경 내용
{change_lines}

### 충돌 가능성
{conflict_lines}

### 원문 아이디어
{idea}
"""
