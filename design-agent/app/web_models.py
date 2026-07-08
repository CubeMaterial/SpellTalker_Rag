from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PendingFile:
    path: str
    content: str
    diff: str


@dataclass
class PendingChange:
    kind: str
    title: str
    files: list[PendingFile]
    idea: str = ""
    plan: str = ""
    message: str = ""
    metadata: dict[str, str] = field(default_factory=dict)

    @property
    def combined_diff(self) -> str:
        return "\n".join(file.diff for file in self.files if file.diff.strip())

