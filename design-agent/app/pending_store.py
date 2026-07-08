from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.settings import PROJECT_ROOT, Settings
from app.conversation_store import validate_session_id
from app.web_models import PendingChange, PendingFile


class PendingStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.settings.pending_path.mkdir(parents=True, exist_ok=True)

    def save(self, session_id: str, pending: PendingChange) -> None:
        payload = {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "summary": pending.title,
            "kind": pending.kind,
            "idea": pending.idea,
            "plan": pending.plan,
            "target_files": [self._rel(file.path) for file in pending.files],
            "diff": pending.combined_diff,
            "new_contents": {self._rel(file.path): file.content for file in pending.files},
        }
        self.path(session_id).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self, session_id: str) -> PendingChange | None:
        path = self.path(session_id)
        if not path.exists():
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        files = []
        for rel, content in payload.get("new_contents", {}).items():
            absolute = PROJECT_ROOT / rel
            old = absolute.read_text(encoding="utf-8") if absolute.exists() else ""
            diff = payload.get("diff", "")
            files.append(PendingFile(path=str(absolute), content=content, diff=diff if len(payload.get("new_contents", {})) == 1 else ""))
        if len(files) != 1:
            files = [
                PendingFile(path=str(PROJECT_ROOT / rel), content=content, diff="")
                for rel, content in payload.get("new_contents", {}).items()
            ]
        pending = PendingChange(
            kind=payload.get("kind", "chat"),
            title=payload.get("summary", "Pending Change"),
            files=files,
            idea=payload.get("idea", ""),
            plan=payload.get("plan", ""),
            message=payload.get("summary", ""),
        )
        pending.metadata["stored_diff"] = payload.get("diff", "")
        return pending

    def load_raw(self, session_id: str) -> dict | None:
        path = self.path(session_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def delete(self, session_id: str) -> None:
        path = self.path(session_id)
        if path.exists():
            path.unlink()

    def exists(self, session_id: str) -> bool:
        return self.path(session_id).exists()

    def path(self, session_id: str) -> Path:
        if not validate_session_id(session_id):
            raise ValueError(f"Unsafe session_id: {session_id}")
        return self.settings.pending_path / f"{session_id}.json"

    def delete_all(self) -> int:
        deleted = 0
        for path in self.settings.pending_path.glob("*.json"):
            if not validate_session_id(path.stem):
                continue
            path.unlink()
            deleted += 1
        return deleted

    def _rel(self, path: str) -> str:
        return Path(path).resolve().relative_to(PROJECT_ROOT).as_posix()
