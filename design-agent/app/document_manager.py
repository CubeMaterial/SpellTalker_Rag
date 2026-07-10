from __future__ import annotations

import difflib
import shutil
from datetime import datetime
from pathlib import Path

from app.document_modifier import DocumentModifier
from app.settings import Settings


GDD_DOCUMENTS = [
    ("00_GDD_Index.md", "GDD Index"),
    ("01_Game_Overview.md", "Game Overview"),
    ("02_Core_Loop.md", "Core Loop"),
    ("03_Combat_System.md", "Combat System"),
    ("04_Card_System.md", "Card System"),
    ("05_Rune_System.md", "Rune System"),
    ("06_Spell_System.md", "Spell System"),
    ("07_Status_Effects.md", "Status Effects"),
    ("08_Relic_System.md", "Relic System"),
    ("09_Character_Design.md", "Character Design"),
    ("10_Enemy_Design.md", "Enemy Design"),
    ("11_Boss_Design.md", "Boss Design"),
    ("12_Map_System.md", "Map System"),
    ("13_Reward_System.md", "Reward System"),
    ("14_Shop_Rest_Event.md", "Shop Rest Event"),
    ("15_Codex_World.md", "Codex World"),
    ("16_UI_UX.md", "UI UX"),
    ("17_Balance_Rules.md", "Balance Rules"),
    ("99_TODO.md", "TODO"),
]


TEMPLATE = """# {title}

## 1. 목적

TODO

## 2. 핵심 규칙

TODO

## 3. 플레이 흐름

TODO

## 4. 데이터 구조

TODO

## 5. 예시

TODO

## 6. TODO

- [ ] 작성 필요
"""


class DocumentManager:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.modifier = DocumentModifier()

    def init_docs(self) -> list[Path]:
        created: list[Path] = []
        gdd_dir = self.settings.docs_workspace / "GDD"
        gdd_dir.mkdir(parents=True, exist_ok=True)
        (self.settings.docs_workspace / "Dev").mkdir(parents=True, exist_ok=True)

        for filename, title in GDD_DOCUMENTS:
            path = gdd_dir / filename
            if path.exists():
                continue
            path.write_text(TEMPLATE.format(title=title), encoding="utf-8")
            created.append(path)
        return created

    def markdown_files(self) -> list[Path]:
        if not self.settings.docs_workspace.exists():
            return []
        return sorted(self.settings.docs_workspace.rglob("*.md"))

    def snapshot_docs(self) -> Path:
        self.settings.snapshots_path.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination = self.settings.snapshots_path / f"docs_workspace_{stamp}"
        shutil.copytree(self.settings.docs_workspace, destination, dirs_exist_ok=True)
        return destination

    def build_update(self, relative_path: str, idea: str, plan: str) -> tuple[Path, str, str]:
        path = self.settings.docs_workspace / relative_path
        old = path.read_text(encoding="utf-8") if path.exists() else TEMPLATE.format(title=Path(relative_path).stem)
        new = self.modifier.modify(old, relative_path, idea, plan).content
        return path, old, new

    def _append_change(self, old: str, addition: str, today: str) -> str:
        if "## Change Log" in old:
            body, log = old.split("## Change Log", 1)
            log_entry = f"## Change Log{log.rstrip()}\n\n### {today}\n- 변경 계획 업데이트\n"
            return body.rstrip() + "\n\n" + addition.split("## Change Log", 1)[0].rstrip() + "\n\n---\n\n" + log_entry
        return old.rstrip() + addition

    def diff(self, path: Path, old: str, new: str) -> str:
        return "".join(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile=f"{path} (before)",
                tofile=f"{path} (after)",
            )
        )

    def save(self, path: Path, content: str) -> None:
        self.validate_save_path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def validate_relative_save_path(self, raw_path: str) -> Path:
        candidate = Path(raw_path)
        if candidate.is_absolute():
            raise ValueError(f"Absolute save path is not allowed: {raw_path}")
        if ".." in candidate.parts:
            raise ValueError(f"Parent traversal is not allowed: {raw_path}")
        return self.validate_save_path((self.settings.docs_workspace.parent / candidate).resolve())

    def validate_save_path(self, path: Path) -> Path:
        if path.suffix.lower() != ".md":
            raise ValueError(f"Only Markdown files can be saved: {path}")

        raw_parts = path.parts
        if ".." in raw_parts:
            raise ValueError(f"Parent traversal is not allowed: {path}")

        candidate = path.resolve()
        allowed_root = self.settings.docs_workspace.resolve()
        if not (candidate == allowed_root or allowed_root in candidate.parents):
            raise ValueError(f"Save path is outside docs_workspace: {path}")

        self._reject_symlink_path(candidate, allowed_root)
        return candidate

    def _reject_symlink_path(self, candidate: Path, allowed_root: Path) -> None:
        relative = candidate.relative_to(allowed_root)
        current = allowed_root
        for part in relative.parts:
            current = current / part
            if current.exists() and current.is_symlink():
                raise ValueError(f"Symlink save path is not allowed: {candidate}")
