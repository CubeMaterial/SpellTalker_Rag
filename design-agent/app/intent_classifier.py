from __future__ import annotations

from enum import Enum

from app.llm_client import OllamaClient
from app.settings import Settings


class UserIntent(str, Enum):
    QUESTION = "question"
    STATUS_CHECK = "status_check"
    IDEA_REVIEW = "idea_review"
    CHANGE_REQUEST = "change_request"
    DOC_READ = "doc_read"
    DOC_WRITE = "doc_write"
    UNKNOWN = "unknown"


class IntentClassifier:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.llm = OllamaClient(self.settings)

    def classify(self, message: str, write_mode: bool = False) -> UserIntent:
        lowered = message.lower()
        if write_mode:
            return UserIntent.CHANGE_REQUEST
        if self._contains(lowered, ["문서에 반영", "gdd에 추가", "저장해", "저장해줘", "적용해", "문서 수정", "문서에 추가"]):
            return UserIntent.CHANGE_REQUEST
        if self._contains(lowered, ["현재", "어디까지", "진행", "완성까지", "남았", "상태", "완료", "미완성"]):
            return UserIntent.STATUS_CHECK
        if self._contains(lowered, ["문제", "충돌", "검토", "위험", "괜찮", "아이디어", "추가하고", "만들고 싶"]):
            return UserIntent.IDEA_REVIEW
        if self._contains(lowered, ["보여줘", "읽어", "문서", "내용", "열어줘"]) and not self._contains(lowered, ["수정", "반영", "저장"]):
            return UserIntent.DOC_READ
        if message.strip().endswith("?") or message.strip().endswith("어?") or message.strip().endswith("야?"):
            return UserIntent.QUESTION

        fallback = self._llm_fallback(message)
        return fallback or UserIntent.QUESTION

    def _contains(self, text: str, keywords: list[str]) -> bool:
        return any(keyword in text for keyword in keywords)

    def _llm_fallback(self, message: str) -> UserIntent | None:
        prompt = f"""다음 사용자 입력의 의도를 하나만 골라라.

가능한 값:
- question
- status_check
- idea_review
- change_request
- doc_read
- doc_write
- unknown

사용자 입력:
{message}

값 하나만 출력하라.
"""
        response = self.llm.generate(prompt)
        if response.startswith("[LLM unavailable"):
            return None
        value = response.strip().split()[0].strip("`.,")
        try:
            return UserIntent(value)
        except ValueError:
            return None
