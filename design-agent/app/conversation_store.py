from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from app.settings import Settings


SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def validate_session_id(session_id: str) -> bool:
    return bool(SESSION_ID_PATTERN.fullmatch(session_id))


class ConversationStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.settings.conversations_path.mkdir(parents=True, exist_ok=True)

    def create(self) -> dict:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"{stamp}_{uuid4().hex[:6]}"
        data = {
            "session_id": session_id,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "messages": [],
        }
        self.save(data)
        return data

    def get_or_create(self, session_id: str | None) -> dict:
        if not session_id:
            return self.create()
        path = self.path(session_id)
        if not path.exists():
            return self.create()
        return json.loads(path.read_text(encoding="utf-8"))

    def get(self, session_id: str) -> dict:
        path = self.path(session_id)
        if not path.exists():
            raise FileNotFoundError(f"Conversation not found: {session_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def add_message(self, session_id: str, role: str, content: str, intent: str | None = None) -> dict:
        data = self.get(session_id)
        message = {"role": role, "content": content, "created_at": now_iso()}
        if intent:
            message["intent"] = intent
        data["messages"].append(message)
        data["updated_at"] = now_iso()
        self.save(data)
        return data

    def save(self, data: dict) -> None:
        self.path(data["session_id"]).write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list_sessions(self) -> list[dict]:
        sessions = []
        for path in sorted(self.settings.conversations_path.glob("*.json"), reverse=True):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            first_user = next((m["content"] for m in data.get("messages", []) if m.get("role") == "user"), "")
            sessions.append(
                {
                    "session_id": data.get("session_id", path.stem),
                    "updated_at": data.get("updated_at", ""),
                    "title": first_user[:48] or "새 대화",
                    "message_count": len(data.get("messages", [])),
                }
            )
        return sessions

    def history_text(self, data: dict, limit: int = 8) -> str:
        messages = data.get("messages", [])[-limit:]
        return "\n".join(f"{m.get('role')}: {m.get('content')}" for m in messages)

    def path(self, session_id: str) -> Path:
        if not validate_session_id(session_id):
            raise ValueError(f"Unsafe session_id: {session_id}")
        return self.settings.conversations_path / f"{session_id}.json"

    def delete_conversation(self, session_id: str) -> bool:
        path = self.path(session_id)
        if not path.exists():
            return False
        path.unlink()
        return True

    def delete_all_conversations(self) -> int:
        deleted = 0
        for path in self.settings.conversations_path.glob("*.json"):
            if not validate_session_id(path.stem):
                continue
            path.unlink()
            deleted += 1
        return deleted
