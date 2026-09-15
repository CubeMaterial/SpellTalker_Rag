from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

from app.settings import Settings


BRANCH_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


class WorkspaceVersions:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.settings.snapshots_path.mkdir(parents=True, exist_ok=True)
        self.settings.branches_path.mkdir(parents=True, exist_ok=True)

    def list_snapshots(self) -> list[dict[str, str | int]]:
        return self._list_copies(self.settings.snapshots_path, prefix="docs_workspace_")

    def create_snapshot(self) -> Path:
        destination = self._available_path(self.settings.snapshots_path / f"docs_workspace_{now_stamp()}")
        return self._copy_workspace(destination)

    def restore_snapshot(self, name: str) -> Path:
        source = self._copy_path(self.settings.snapshots_path, name)
        safety_snapshot = self.create_snapshot()
        self.save_current_branch()
        self._replace_workspace(source)
        (self.settings.branches_path / ".active").write_text("main", encoding="utf-8")
        self.save_current_branch()
        return safety_snapshot

    def list_branches(self) -> list[dict[str, str | int | bool]]:
        active = self.active_branch()
        branches = self._list_copies(self.settings.branches_path)
        if not any(branch["name"] == "main" for branch in branches):
            branches.insert(
                0,
                {
                    "name": "main",
                    "updated_at": "current",
                    "file_count": self._workspace_file_count(),
                },
            )
        for branch in branches:
            branch["active"] = branch["name"] == active
        return branches

    def active_branch(self) -> str:
        marker = self.settings.branches_path / ".active"
        if not marker.exists():
            return "main"
        value = marker.read_text(encoding="utf-8").strip()
        return value if value and self._valid_branch_name(value) else "main"

    def create_branch(self, name: str) -> Path:
        clean_name = self._validate_branch_name(name)
        if clean_name == "main":
            raise ValueError("main 브랜치는 기본 브랜치로 예약되어 있습니다.")
        destination = self.settings.branches_path / clean_name
        if destination.exists():
            raise ValueError(f"이미 존재하는 브랜치입니다: {clean_name}")
        return self._copy_workspace(destination)

    def save_current_branch(self) -> Path:
        branch = self.active_branch()
        destination = self.settings.branches_path / branch
        if destination.exists():
            shutil.rmtree(destination)
        return self._copy_workspace(destination)

    def switch_branch(self, name: str) -> Path:
        clean_name = self._validate_branch_name(name)
        if clean_name == self.active_branch():
            return self.create_snapshot()
        source = self.settings.branches_path / clean_name
        if not source.exists() or not source.is_dir():
            raise FileNotFoundError(f"브랜치를 찾을 수 없습니다: {clean_name}")
        safety_snapshot = self.create_snapshot()
        self.save_current_branch()
        self._replace_workspace(source)
        (self.settings.branches_path / ".active").write_text(clean_name, encoding="utf-8")
        return safety_snapshot

    def _copy_workspace(self, destination: Path) -> Path:
        if not self.settings.docs_workspace.exists():
            raise FileNotFoundError(f"문서 작업공간을 찾을 수 없습니다: {self.settings.docs_workspace}")
        if destination.exists():
            raise ValueError(f"이미 존재하는 저장 경로입니다: {destination.name}")
        shutil.copytree(self.settings.docs_workspace, destination)
        return destination

    def _replace_workspace(self, source: Path) -> None:
        if not source.exists() or not source.is_dir():
            raise FileNotFoundError(f"복원할 문서 작업공간을 찾을 수 없습니다: {source.name}")
        workspace = self.settings.docs_workspace
        if workspace.exists():
            shutil.rmtree(workspace)
        shutil.copytree(source, workspace)

    def _copy_path(self, root: Path, name: str) -> Path:
        if "/" in name or "\\" in name or ".." in Path(name).parts:
            raise ValueError(f"허용되지 않는 이름입니다: {name}")
        source = (root / name).resolve()
        allowed_root = root.resolve()
        if not (source == allowed_root or allowed_root in source.parents):
            raise ValueError(f"허용되지 않는 경로입니다: {name}")
        if source.is_symlink():
            raise ValueError(f"symlink 경로는 사용할 수 없습니다: {name}")
        return source

    def _list_copies(self, root: Path, prefix: str = "") -> list[dict[str, str | int]]:
        items = []
        for path in sorted(root.iterdir(), reverse=True) if root.exists() else []:
            if not path.is_dir() or path.is_symlink():
                continue
            if prefix and not path.name.startswith(prefix):
                continue
            items.append(
                {
                    "name": path.name,
                    "updated_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
                    "file_count": sum(1 for item in path.rglob("*.md") if item.is_file()),
                }
            )
        return items

    def _workspace_file_count(self) -> int:
        if not self.settings.docs_workspace.exists():
            return 0
        return sum(1 for item in self.settings.docs_workspace.rglob("*.md") if item.is_file())

    def _available_path(self, base: Path) -> Path:
        if not base.exists():
            return base
        for index in range(2, 1000):
            candidate = base.with_name(f"{base.name}_{index}")
            if not candidate.exists():
                return candidate
        raise RuntimeError(f"사용 가능한 저장 이름을 찾지 못했습니다: {base.name}")

    def _validate_branch_name(self, name: str) -> str:
        clean_name = name.strip()
        if not self._valid_branch_name(clean_name):
            raise ValueError("브랜치 이름은 영문/숫자로 시작하고 영문, 숫자, _, - 만 사용할 수 있습니다.")
        return clean_name

    def _valid_branch_name(self, name: str) -> bool:
        return bool(BRANCH_NAME_PATTERN.fullmatch(name))
