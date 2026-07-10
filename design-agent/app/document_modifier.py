from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class ModificationResult:
    content: str
    strategy: str
    summary: str


class DocumentModifier:
    SECTION_ORDER = [
        "## 1. 목적",
        "## 2. 현재 확정된 내용",
        "## 3. 핵심 규칙",
        "## 4. 플레이 흐름",
        "## 5. 데이터 구조",
        "## 6. 예시",
        "## 7. 현재 구현 상태",
        "## 8. TODO",
    ]

    def modify(self, old: str, relative_path: str, idea: str, plan: str) -> ModificationResult:
        today = datetime.now().strftime("%Y-%m-%d")
        summary = self._summary(idea, plan)
        section = self._target_section(relative_path, idea, plan)
        bullet = self._bullet(summary)

        try:
            body, changed = self._upsert_section_bullet(old, section, bullet)
            if not changed:
                body, changed = self._upsert_section_bullet(old, "## 8. TODO", f"- [ ] {summary}")
            if not changed:
                body = self._append_proposed_changes(old, idea, plan, today)
                strategy = "proposed_changes_fallback"
            else:
                body = self._append_change_log(body, today, summary)
                strategy = "section_update"
            return ModificationResult(content=body, strategy=strategy, summary=summary)
        except Exception:
            return ModificationResult(
                content=self._append_proposed_changes(old, idea, plan, today),
                strategy="proposed_changes_fallback",
                summary=summary,
            )

    def _target_section(self, relative_path: str, idea: str, plan: str) -> str:
        lowered = f"{relative_path}\n{idea}\n{plan}".lower()
        path_name = Path(relative_path).name
        if path_name == "99_TODO.md" or any(word in lowered for word in ["todo", "미정", "보류", "확인 필요"]):
            return "## 8. TODO"
        if path_name == "17_Balance_Rules.md" or any(word in lowered for word in ["밸런스", "balance", "금지", "제한", "무한", "최적해"]):
            return "## 3. 핵심 규칙"
        if any(word in lowered for word in ["flow", "흐름", "루프", "턴", "단계", "시전", "사용"]):
            return "## 4. 플레이 흐름"
        if any(word in lowered for word in ["data", "runtime", "scriptableobject", "필드", "구조"]):
            return "## 5. 데이터 구조"
        if any(word in lowered for word in ["예시", "example", "sample"]):
            return "## 6. 예시"
        return "## 2. 현재 확정된 내용"

    def _upsert_section_bullet(self, markdown: str, heading: str, bullet: str) -> tuple[str, bool]:
        if heading not in markdown:
            markdown = self._insert_section(markdown, heading)

        pattern = re.compile(rf"(?ms)^({re.escape(heading)}\n)(.*?)(?=^##\s+|\Z)")
        match = pattern.search(markdown)
        if not match:
            return markdown, False

        section_body = match.group(2).rstrip()
        normalized = self._normalize_bullet(bullet)
        existing = {self._normalize_bullet(line) for line in section_body.splitlines()}
        if normalized in existing:
            return markdown, True

        if self._is_placeholder_only(section_body):
            new_body = f"\n{bullet}\n\n"
        else:
            new_body = f"{match.group(2).rstrip()}\n{bullet}\n\n"
        return markdown[: match.start(2)] + new_body + markdown[match.end(2) :], True

    def _insert_section(self, markdown: str, heading: str) -> str:
        order_index = self.SECTION_ORDER.index(heading) if heading in self.SECTION_ORDER else len(self.SECTION_ORDER)
        later = self.SECTION_ORDER[order_index + 1 :]
        for later_heading in later:
            match = re.search(rf"(?m)^{re.escape(later_heading)}$", markdown)
            if match:
                return markdown[: match.start()] + f"{heading}\n\n" + markdown[match.start() :]
        tail_match = re.search(r"(?m)^## (?:Proposed Changes|Change Log)\s*$", markdown)
        if tail_match:
            return markdown[: tail_match.start()] + f"{heading}\n\n" + markdown[tail_match.start() :]
        return markdown.rstrip() + f"\n\n{heading}\n\n"

    def _append_change_log(self, markdown: str, today: str, summary: str) -> str:
        entry = f"### {today}\n- {summary}"
        if "## Change Log" not in markdown:
            return markdown.rstrip() + f"\n\n## Change Log\n\n{entry}\n"

        pattern = re.compile(r"(?ms)^## Change Log\n(.*?)(?=^##\s+|\Z)")
        match = pattern.search(markdown)
        if not match:
            return markdown.rstrip() + f"\n\n## Change Log\n\n{entry}\n"

        body = match.group(1).rstrip()
        if summary in body:
            return markdown
        new_body = f"{body}\n\n{entry}\n" if body else f"\n{entry}\n"
        return markdown[: match.start(1)] + new_body + markdown[match.end(1) :]

    def _append_proposed_changes(self, old: str, idea: str, plan: str, today: str) -> str:
        return old.rstrip() + f"""

## Proposed Changes

### {today}

사용자 아이디어:

> {idea}

계획 요약:

{plan.strip()}

---

## Change Log

### {today}
- 사용자 승인에 따라 변경 계획 반영
"""

    def _summary(self, idea: str, plan: str) -> str:
        for source in (plan, idea):
            for raw in source.splitlines():
                line = raw.strip(" -\t")
                if not line or line.startswith(("#", "GDD/")):
                    continue
                if len(line) < 4:
                    continue
                return line[:180]
        return "사용자 아이디어를 문서에 반영"

    def _bullet(self, summary: str) -> str:
        return summary if summary.startswith(("- ", "- [ ] ")) else f"- {summary}"

    def _normalize_bullet(self, line: str) -> str:
        return re.sub(r"\s+", " ", line.strip().lower().lstrip("- [ ]")).strip()

    def _is_placeholder_only(self, body: str) -> bool:
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        if not lines:
            return True
        return all(line in {"TODO", "- TODO: 기존 문서에서 확인 필요", "- [ ] 작성 필요"} or line.startswith("- TODO:") for line in lines)
