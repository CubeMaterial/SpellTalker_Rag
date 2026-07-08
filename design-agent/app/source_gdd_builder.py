from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from app.document_manager import GDD_DOCUMENTS, DocumentManager
from app.settings import Settings


COMMON_SECTIONS = [
    "## 1. 목적",
    "## 2. 현재 확정된 내용",
    "## 3. 핵심 규칙",
    "## 4. 플레이 흐름",
    "## 5. 데이터 구조",
    "## 6. 예시",
    "## 7. 현재 구현 상태",
    "## 8. TODO",
]

GLOSSARY_TERMS = [
    "Card Deck",
    "Hand",
    "Discard Pile",
    "Regeneration",
    "Regen Count",
    "Exhaust",
    "Mana",
    "Rune",
    "Spell",
    "Action",
    "Cooldown",
    "Target",
    "Intent",
    "Buff",
    "Debuff",
    "Injury",
    "Node",
]


SOURCE_TO_TARGETS = {
    "00_README.md": ["00_GDD_Index.md", "01_Game_Overview.md"],
    "01_Glossary.md": [
        "00_GDD_Index.md",
        "03_Combat_System.md",
        "04_Card_System.md",
        "05_Rune_System.md",
        "06_Spell_System.md",
        "07_Status_Effects.md",
        "12_Map_System.md",
    ],
    "02_Game Spec.md": [
        "03_Combat_System.md",
        "07_Status_Effects.md",
        "12_Map_System.md",
        "13_Reward_System.md",
        "14_Shop_Rest_Event.md",
        "15_Codex_World.md",
    ],
    "03_Contents Rule.md": [
        "04_Card_System.md",
        "05_Rune_System.md",
        "06_Spell_System.md",
        "07_Status_Effects.md",
        "10_Enemy_Design.md",
        "11_Boss_Design.md",
        "17_Balance_Rules.md",
    ],
    "04_Architecture.md": ["16_UI_UX.md", "17_Balance_Rules.md", "99_TODO.md"],
    "06_Plans.md": [
        "02_Core_Loop.md",
        "03_Combat_System.md",
        "04_Card_System.md",
        "05_Rune_System.md",
        "06_Spell_System.md",
        "12_Map_System.md",
        "13_Reward_System.md",
        "99_TODO.md",
    ],
    "07_Package_Rebuild_Checklist.md": [
        "02_Core_Loop.md",
        "03_Combat_System.md",
        "04_Card_System.md",
        "05_Rune_System.md",
        "06_Spell_System.md",
        "12_Map_System.md",
        "13_Reward_System.md",
        "16_UI_UX.md",
        "17_Balance_Rules.md",
        "99_TODO.md",
    ],
}


TARGET_KEYWORDS = {
    "00_GDD_Index.md": [
        "genre",
        "장르",
        "engine",
        "엔진",
        "prototype",
        "프로토타입",
        "scope",
        "범위",
        "system",
        "시스템",
        "loop",
        "루프",
    ],
    "01_Game_Overview.md": ["genre", "장르", "overview", "개요", "scope", "범위", "prototype", "프로토타입", "technology", "기술"],
    "02_Core_Loop.md": ["loop", "루프", "milestone", "마일스톤", "battle", "reward", "map", "전투", "보상", "맵"],
    "03_Combat_System.md": ["combat", "battle", "전투", "victory", "defeat", "승리", "패배", "time", "시간", "injury"],
    "04_Card_System.md": ["card", "deck", "hand", "discard", "regen", "exhaust", "mana", "카드", "덱", "핸드", "마나"],
    "05_Rune_System.md": ["rune", "rune deck", "combination", "룬", "조합"],
    "06_Spell_System.md": ["spell", "fireball", "mana cost", "스펠", "주문", "마나 비용", "조합"],
    "07_Status_Effects.md": ["status", "buff", "debuff", "injury", "상태", "버프", "디버프", "부상"],
    "08_Relic_System.md": ["relic", "유물"],
    "09_Character_Design.md": ["character", "player", "캐릭터", "플레이어"],
    "10_Enemy_Design.md": ["enemy", "intent", "target", "적 설계", "적 행동", "몬스터", "의도", "타겟"],
    "11_Boss_Design.md": ["boss", "보스"],
    "12_Map_System.md": ["map", "node", "맵", "노드", "progress"],
    "13_Reward_System.md": ["reward", "보상", "gold", "card reward", "rune reward"],
    "14_Shop_Rest_Event.md": ["shop", "rest", "event", "상점", "휴식", "이벤트"],
    "15_Codex_World.md": ["codex", "world", "lore", "백과", "세계관"],
    "16_UI_UX.md": ["ui", "ux", "input", "output", "입력", "출력", "manager", "runtime"],
    "17_Balance_Rules.md": ["balance", "rule", "forbidden", "loop", "mana", "밸런스", "규칙", "금지", "무한"],
    "99_TODO.md": ["todo", "plan", "milestone", "checklist", "debt", "미정", "계획", "부채", "우선순위"],
}


STATUS_KEYWORDS = ["done", "complete", "완료", "implemented", "구현", "todo", "미완성", "pending", "priority", "우선순위", "debt", "부채"]
FLOW_KEYWORDS = ["flow", "loop", "turn", "phase", "node", "progress", "흐름", "루프", "턴", "단계", "노드", "진행"]
RULE_KEYWORDS = ["rule", "must", "forbid", "never", "규칙", "금지", "반드시", "제한", "분리"]
DATA_KEYWORDS = ["data", "field", "id", "type", "value", "scriptableobject", "runtime", "데이터", "필드", "구조"]
EXAMPLE_KEYWORDS = ["example", "예시", "sample"]


@dataclass(frozen=True)
class SourceDocument:
    path: Path
    relative_name: str
    text: str
    lines: list[str]


class SourceGddBuilder:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.manager = DocumentManager(self.settings)

    def run(self) -> None:
        print("[1/5] source_docs 문서 로딩 중...")
        sources = self.load_sources()
        if not sources:
            print(f"source_docs에 Markdown 문서가 없습니다: {self.settings.source_docs}")
            return
        for source in sources:
            print(f"- {source.relative_name}")

        print("\n[2/5] GDD 매핑 생성 중...")
        mapped = self.map_sources(sources)

        print("\n[3/5] 문서 초안 생성 중...")
        drafts = self.build_drafts(mapped, sources)
        for path in drafts:
            print(f"- GDD/{path.name}")

        print("\n[4/5] diff 생성 중...")
        self.manager.snapshot_docs()
        updates = []
        for path, new in drafts.items():
            old = path.read_text(encoding="utf-8") if path.exists() else ""
            diff = self.manager.diff(path, old, new)
            updates.append((path, new, diff))
            if diff.strip():
                print("\n" + diff)
            else:
                print(f"\n변경 없음: {path}")

        approve = input("\n[5/5] 저장하시겠습니까? (y/n) ").strip().lower()
        if approve != "y":
            print("저장하지 않았습니다. snapshot만 생성되었습니다.")
            return

        for path, new, _diff in updates:
            self.manager.save(path, new)
        print(f"{len(updates)}개 GDD 문서를 저장했습니다.")

    def load_sources(self) -> list[SourceDocument]:
        self.settings.source_docs.mkdir(parents=True, exist_ok=True)
        sources = []
        for path in sorted(self.settings.source_docs.rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            sources.append(
                SourceDocument(
                    path=path,
                    relative_name=path.relative_to(self.settings.source_docs).as_posix(),
                    text=text,
                    lines=self._candidate_lines(text, path),
                )
            )
        return sources

    def map_sources(self, sources: list[SourceDocument]) -> dict[str, list[str]]:
        mapped = {filename: [] for filename, _title in GDD_DOCUMENTS}
        by_name = {source.relative_name: source for source in sources}
        for source_name, targets in SOURCE_TO_TARGETS.items():
            source = by_name.get(source_name)
            if not source:
                continue
            for target in targets:
                mapped[target].extend(self._select_lines(source.lines, TARGET_KEYWORDS.get(target, []), limit=28))
        for target in mapped:
            mapped[target] = self._dedupe(mapped[target])
        return mapped

    def build_drafts(self, mapped: dict[str, list[str]], sources: list[SourceDocument]) -> dict[Path, str]:
        gdd_dir = self.settings.docs_workspace / "GDD"
        gdd_dir.mkdir(parents=True, exist_ok=True)
        glossary = self._extract_glossary(sources)
        drafts: dict[Path, str] = {}
        for filename, title in GDD_DOCUMENTS:
            path = gdd_dir / filename
            if filename == "00_GDD_Index.md":
                drafts[path] = self._build_index(mapped, sources)
            elif filename == "99_TODO.md":
                drafts[path] = self._build_todo(mapped, sources)
            else:
                drafts[path] = self._build_document(filename, title, mapped.get(filename, []), glossary)
        return drafts

    def _build_index(self, mapped: dict[str, list[str]], sources: list[SourceDocument]) -> str:
        project_lines = self._dedupe(mapped.get("00_GDD_Index.md", []))
        summary = self._summary_fields(project_lines)
        rows = "\n".join(
            f"| {filename} | {description} | 초안 |"
            for filename, description in GDD_DOCUMENTS
            if filename != "00_GDD_Index.md"
        )
        prototype = self._section_from_lines(project_lines, ["prototype", "프로토타입", "scope", "범위"], "- TODO: 기존 문서에서 프로토타입 범위를 확인해야 한다.")
        full_scope = self._section_from_lines(project_lines, ["scope", "범위", "전체"], "- TODO: 기존 문서에서 전체 개발 범위를 확인해야 한다.")
        unknowns = self._collect_todos(sources, limit=12)
        source_list = "\n".join(f"- `{source.relative_name}`" for source in sources)
        return f"""# SpellTalker GDD Index

## 문서 목적

이 문서는 SpellTalker의 게임 기획 문서 목차다.

## 프로젝트 요약

- 장르: {summary.get("genre", "TODO")}
- 엔진: {summary.get("engine", "TODO")}
- 개발 단계: {summary.get("stage", "TODO")}
- 핵심 루프: {summary.get("loop", "TODO")}

## GDD 문서 목록

| 문서 | 설명 | 상태 |
|---|---|---|
{rows}

## 현재 프로토타입 범위

{prototype}

## 전체 개발 범위

{full_scope}

## 주요 미정 사항

{self._bullets(unknowns, "- TODO: 기존 문서에서 주요 미정 사항을 확인해야 한다.")}

## 반영한 기존 문서

{source_list}
"""

    def _build_document(self, filename: str, title: str, lines: list[str], glossary: dict[str, str]) -> str:
        purpose = self._purpose(filename, title, lines)
        confirmed = self._bullets(lines, "- TODO: 기존 문서에서 확정 내용을 확인해야 한다.")
        rules = self._bullets(self._filter(lines, RULE_KEYWORDS), "- TODO: 기존 문서에서 핵심 규칙을 확인해야 한다.")
        flow = self._bullets(self._filter(lines, FLOW_KEYWORDS), "- TODO: 기존 문서에서 플레이 흐름을 확인해야 한다.")
        data = self._data_table(self._filter(lines, DATA_KEYWORDS), glossary, filename)
        examples = self._bullets(self._filter(lines, EXAMPLE_KEYWORDS), "- TODO: 기존 문서에서 예시를 확인해야 한다.")
        status = self._bullets(self._filter(lines, STATUS_KEYWORDS), "- TODO: 07_Package_Rebuild_Checklist.md에서 현재 구현 상태를 확인해야 한다.")
        todos = self._todo_lines(lines, filename)
        terms = self._terms_section(glossary, filename)
        return f"""# {title}

## 1. 목적

{purpose}

## 2. 현재 확정된 내용

{confirmed}

{terms}
## 3. 핵심 규칙

{rules}

## 4. 플레이 흐름

{flow}

## 5. 데이터 구조

{data}

## 6. 예시

{examples}

## 7. 현재 구현 상태

{status}

## 8. TODO

{self._bullets(todos, "- [ ] 부족한 내용을 작성한다.")}
"""

    def _build_todo(self, mapped: dict[str, list[str]], sources: list[SourceDocument]) -> str:
        lines = self._dedupe(mapped.get("99_TODO.md", []) + self._collect_todos(sources, limit=80))
        planning = self._filter(lines, ["plan", "milestone", "기획", "계획", "마일스톤"])
        content = self._filter(lines, ["content", "card", "rune", "spell", "enemy", "boss", "콘텐츠", "카드", "룬", "스펠", "적", "보스"])
        system = self._filter(lines, ["system", "runtime", "manager", "combat", "reward", "map", "시스템", "전투", "보상", "맵"])
        ui = self._filter(lines, ["ui", "ux", "input", "output", "입력", "출력"])
        implementation = self._filter(lines, ["check", "done", "complete", "implemented", "구현", "완료", "확인"])
        debt = self._filter(lines, ["debt", "architecture", "dependency", "monobehaviour", "부채", "아키텍처", "의존성"])
        next_steps = self._filter(lines, ["next", "priority", "order", "다음", "우선순위", "순서"])
        return f"""# TODO

## 1. 기획 미정

{self._checkboxes(planning)}

## 2. 콘텐츠 미정

{self._checkboxes(content)}

## 3. 시스템 미정

{self._checkboxes(system)}

## 4. UI 미정

{self._checkboxes(ui)}

## 5. 구현 확인 필요

{self._checkboxes(implementation)}

## 6. 아키텍처 부채

{self._checkboxes(debt)}

## 7. 다음 작업 순서

{self._checkboxes(next_steps)}
"""

    def _candidate_lines(self, text: str, path: Path) -> list[str]:
        candidates: list[str] = []
        title_names = {
            path.stem.lower(),
            path.stem.replace("_", " ").lower(),
            re.sub(r"^\d+[_\s-]*", "", path.stem).replace("_", " ").lower(),
        }
        normalized_stem = re.sub(r"^\d+[_\s-]*", "", path.stem).replace("_", " ").lower()
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line in {"---", "***"}:
                continue
            if line.startswith("```"):
                continue
            line = re.sub(r"^#{1,6}\s*", "", line)
            line = re.sub(r"^[-*+]\s+", "", line)
            line = re.sub(r"^\d+[.)]\s+", "", line)
            line = re.sub(r"\s+", " ", line).strip()
            if len(line) < 2:
                continue
            if line.lower() in title_names:
                continue
            if len(line) <= 60 and line.lower() in normalized_stem:
                continue
            candidates.append(line[:220])
        return candidates

    def _select_lines(self, lines: list[str], keywords: list[str], limit: int) -> list[str]:
        selected = [line for line in lines if self._matches(line, keywords)]
        return selected[:limit]

    def _filter(self, lines: list[str], keywords: list[str], limit: int = 12) -> list[str]:
        return [line for line in lines if self._matches(line, keywords)][:limit]

    def _matches(self, line: str, keywords: list[str]) -> bool:
        lowered = line.lower()
        return any(keyword.lower() in lowered for keyword in keywords)

    def _dedupe(self, lines: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for line in lines:
            normalized = line.lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(line)
        return deduped

    def _bullets(self, lines: list[str], fallback: str) -> str:
        if not lines:
            return fallback
        return "\n".join(f"- {line}" for line in lines)

    def _checkboxes(self, lines: list[str]) -> str:
        if not lines:
            return "- [ ] 기존 문서에서 확인 필요"
        return "\n".join(f"- [ ] {line}" for line in self._dedupe(lines)[:14])

    def _section_from_lines(self, lines: list[str], keywords: list[str], fallback: str) -> str:
        return self._bullets(self._filter(lines, keywords, limit=10), fallback)

    def _todo_lines(self, lines: list[str], filename: str) -> list[str]:
        todos = self._filter(lines, ["todo", "미정", "필요", "pending", "not yet", "미완성"], limit=8)
        if not todos:
            todos = [f"{filename}의 부족한 세부 기획을 기존 문서 기준으로 보강한다."]
        return [line if line.startswith("[ ]") else f"[ ] {line}" for line in todos]

    def _collect_todos(self, sources: list[SourceDocument], limit: int) -> list[str]:
        lines: list[str] = []
        for source in sources:
            lines.extend(self._filter(source.lines, ["todo", "미정", "필요", "pending", "not yet", "미완성", "priority", "우선순위"], limit=limit))
        return self._dedupe(lines)[:limit]

    def _summary_fields(self, lines: list[str]) -> dict[str, str]:
        fields = {
            "genre": self._first_value(lines, ["genre", "장르"]),
            "engine": self._first_value(lines, ["engine", "엔진", "unity"]),
            "stage": self._first_value(lines, ["개발 단계", "prototype", "프로토타입", "stage", "단계"]),
            "loop": self._first_value(lines, ["핵심 루프", "loop", "루프"]),
        }
        return {key: value for key, value in fields.items() if value}

    def _first_value(self, lines: list[str], keywords: list[str]) -> str:
        for line in lines:
            lowered = line.lower()
            for keyword in keywords:
                label = keyword.lower()
                if lowered.startswith(f"{label}:") or lowered.startswith(f"{label}："):
                    return line.split(":", 1)[-1].split("：", 1)[-1].strip()
        for line in lines:
            if self._matches(line, keywords):
                return line
        return ""

    def _purpose(self, filename: str, title: str, lines: list[str]) -> str:
        first = lines[0] if lines else ""
        if first:
            return f"이 문서는 `{filename}`에 해당하는 `{title}` 영역을 정리한다. 기존 문서에서 확인된 기준: {first}"
        return f"이 문서는 `{filename}`에 해당하는 `{title}` 영역을 정리한다. TODO: 기존 문서에서 목적을 확인해야 한다."

    def _data_table(self, lines: list[str], glossary: dict[str, str], filename: str) -> str:
        rows: list[str] = []
        for term, definition in glossary.items():
            if self._term_belongs_to_file(term, filename):
                rows.append(f"| {term} | {definition} | 기존 용어 문서 기준 |")
        for line in lines[:8]:
            rows.append(f"| TODO | {line} | 원문 확인 필요 |")
        if not rows:
            rows.append("| TODO | 기존 문서에서 데이터 항목 확인 필요 | TODO |")
        return "| 항목 | 설명 | 비고 |\n|---|---|---|\n" + "\n".join(rows)

    def _extract_glossary(self, sources: list[SourceDocument]) -> dict[str, str]:
        glossary: dict[str, str] = {}
        glossary_doc = next((source for source in sources if source.relative_name == "01_Glossary.md"), None)
        if not glossary_doc:
            return glossary
        for term in GLOSSARY_TERMS:
            pattern = re.compile(rf"^\s*(?:[-*]\s*)?(?:\*\*)?{re.escape(term)}(?:\*\*)?\s*[:：\-–]\s*(.+)$", re.IGNORECASE)
            for raw in glossary_doc.text.splitlines():
                match = pattern.search(raw.strip())
                if match:
                    glossary[term] = match.group(1).strip()
                    break
            if term not in glossary:
                for line in glossary_doc.lines:
                    if term.lower() in line.lower():
                        glossary[term] = line
                        break
        return glossary

    def _terms_section(self, glossary: dict[str, str], filename: str) -> str:
        rows = [
            f"- {term}: {definition}"
            for term, definition in glossary.items()
            if self._term_belongs_to_file(term, filename)
        ]
        if not rows:
            return ""
        return "## 용어\n\n" + "\n".join(rows) + "\n\n"

    def _term_belongs_to_file(self, term: str, filename: str) -> bool:
        groups = {
            "04_Card_System.md": ["Card Deck", "Hand", "Discard Pile", "Regeneration", "Regen Count", "Exhaust", "Mana"],
            "05_Rune_System.md": ["Rune"],
            "06_Spell_System.md": ["Spell", "Action", "Cooldown", "Target", "Mana"],
            "07_Status_Effects.md": ["Buff", "Debuff", "Injury"],
            "10_Enemy_Design.md": ["Intent", "Target"],
            "12_Map_System.md": ["Node"],
            "03_Combat_System.md": ["Action", "Cooldown", "Target", "Injury", "Mana"],
        }
        return term in groups.get(filename, [])
