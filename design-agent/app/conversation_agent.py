from __future__ import annotations

from app.change_planner import ChangePlanner
from app.conversation_store import ConversationStore
from app.document_manager import DocumentManager
from app.intent_classifier import IntentClassifier, UserIntent
from app.llm_client import OllamaClient
from app.pending_store import PendingStore
from app.rag_service import RAGService
from app.settings import Settings
from app.web_models import PendingChange, PendingFile


class ConversationAgent:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.store = ConversationStore(self.settings)
        self.rag = RAGService(self.settings)
        self.intent_classifier = IntentClassifier(self.settings)
        self.llm = OllamaClient(self.settings)
        self.manager = DocumentManager(self.settings)
        self.planner = ChangePlanner(self.settings)
        self.pending = PendingStore(self.settings)

    def handle_message(self, session_id: str | None, message: str, write_mode: bool = False) -> dict:
        conversation = self.store.get_or_create(session_id)
        session_id = conversation["session_id"]
        self.store.add_message(session_id, "user", message)
        conversation = self.store.get(session_id)

        intent = self.intent_classifier.classify(message, write_mode=write_mode)
        if intent in {UserIntent.CHANGE_REQUEST, UserIntent.DOC_WRITE, UserIntent.DOC_REORGANIZE}:
            reply, pending_change = self._handle_change_request(conversation, message)
            self.pending.save(session_id, pending_change)
            has_pending = True
        else:
            reply = self._answer(conversation, message, intent)
            has_pending = self.pending.exists(session_id)

        self.store.add_message(session_id, "assistant", reply, intent=intent.value)
        return {
            "session_id": session_id,
            "intent": intent.value,
            "reply": reply,
            "has_pending_change": has_pending,
        }

    def _answer(self, conversation: dict, message: str, intent: UserIntent) -> str:
        if intent == UserIntent.STATUS_CHECK:
            rows = self.rag.status_context()
            prompt_template = self.settings.prompt("status_check.md")
        elif intent == UserIntent.IDEA_REVIEW:
            rows = self.rag.search(message, limit=10)
            prompt_template = self.settings.prompt("idea_review.md")
        else:
            rows = self.rag.search(message, limit=10)
            prompt_template = self.settings.prompt("conversation.md")

        context = self.rag.context_text(rows)
        history = self.store.history_text(conversation)
        prompt = prompt_template.format(
            user_message=message,
            conversation_history=history,
            retrieved_context=context,
        )
        response = self.llm.generate(prompt, self.settings.prompt("system_prompt.md"))
        if response.startswith("[LLM unavailable") or not response.strip():
            return self._fallback_answer(message, intent, rows)
        return response

    def _handle_change_request(self, conversation: dict, message: str) -> tuple[str, PendingChange]:
        source_idea = self._change_source_text(conversation, message)
        context_rows = self.rag.search(source_idea, limit=10)
        plan = self.planner.create_plan(source_idea, context_rows)
        files = []
        for target in plan["targets"]:
            path, _old, new = self.manager.build_update(str(target), source_idea, str(plan["markdown"]))
            old = path.read_text(encoding="utf-8") if path.exists() else ""
            files.append(PendingFile(path=str(path), content=new, diff=self.manager.diff(path, old, new)))
        pending = PendingChange(
            kind="chat",
            title="대화 기반 문서 변경 제안",
            files=files,
            idea=source_idea,
            plan=str(plan["markdown"]),
            message="사용자 승인 전까지 파일은 저장되지 않습니다.",
        )
        reply = f"""{plan["markdown"]}

## 문서 반영 여부

아직 문서에는 저장하지 않았다.
diff를 확인한 뒤 승인하면 snapshot을 만들고 저장한다.
"""
        return reply, pending

    def _change_source_text(self, conversation: dict, message: str) -> str:
        user_messages = [m["content"] for m in conversation.get("messages", []) if m.get("role") == "user"]
        if len(user_messages) <= 1:
            return message
        if any(keyword in message for keyword in ["반영", "저장", "적용", "수정"]):
            previous = user_messages[:-1]
            return "\n".join(previous[-3:]) if previous else message
        return message

    def _fallback_answer(self, message: str, intent: UserIntent, rows: list[dict[str, str]]) -> str:
        docs = self._evidence_line(rows)
        snippets = self._snippet_bullets(rows)
        if intent == UserIntent.STATUS_CHECK:
            return f"""## 현재 상태

지금 문서 기준으로 보면, SpellTalker는 핵심 방향성은 잡혀 있지만 세부 구현 상태와 완료 기준은 아직 문서화가 부족한 상태입니다.
특히 룬/스펠/보상/UI처럼 플레이 경험을 완성하는 부분은 TODO가 남아 있어서, 다음 작업은 "전투가 끝난 뒤 플레이가 계속 이어지는가"를 확인하는 쪽이 좋아 보입니다.

## 완료된 것

{self._filter_snippets(snippets, ["완료", "done", "implemented"], "- TODO: 완료 항목을 체크리스트에서 확인해야 합니다.")}

## 미완성

{self._filter_snippets(snippets, ["미완성", "todo", "필요", "pending"], "- TODO: 미완성 항목을 확인해야 합니다.")}

## 위험 요소

{self._filter_snippets(snippets, ["위험", "부채", "충돌", "금지"], "- 현재 검색된 문맥에서 명시적 위험 요소를 찾지 못했습니다.")}

## 다음 우선순위

{self._filter_snippets(snippets, ["우선순위", "다음", "순서"], "- TODO: 다음 작업 순서를 정리해야 합니다.")}

## 프로토타입 완료 기준 대비

- 현재 문서만으로는 진행률을 숫자로 확정하기 어렵습니다.
- 프로토타입 완료 기준을 `99_TODO.md`에 체크리스트 형태로 더 구체화하는 것을 추천합니다.

근거:

{docs}
"""
        if intent == UserIntent.IDEA_REVIEW:
            targets = self._recommended_targets(message)
            return f"""## 질문 이해

새 기획 아이디어가 SpellTalker의 기존 전투 구조와 충돌하는지, 그리고 어떤 문서에 반영해야 하는지를 묻는 상황으로 이해했습니다.

## 내 의견

좋은 방향입니다.
새 룬이나 새 스펠을 추가하는 방식은 SpellTalker의 핵심 재미인 "카드로 준비하고, 룬으로 조합하고, 스펠로 전투를 해결한다"는 구조와 잘 맞습니다.

다만 이 아이디어는 밸런스 쪽에서 조심해야 합니다. 같은 룬 2개 조합이 너무 효율적이면 플레이어가 다양한 조합을 실험하지 않고 한 조합만 반복할 가능성이 있습니다.

## 기존 문서와 비교

현재 GDD의 큰 원칙은 카드, 룬, 스펠을 독립된 축으로 유지하는 것입니다.
따라서 이 아이디어는 카드가 직접 해결하는 구조가 아니라, 룬 조합을 통해 스펠을 만드는 구조로 유지하면 자연스럽게 들어갈 수 있습니다.

## 충돌 여부

직접 충돌은 없어 보입니다.
다만 아래 조건을 지키지 않으면 기존 원칙과 충돌할 수 있습니다.

## 위험 요소

- 카드가 새 룬이나 스펠을 직접 대체하는 승리 수단이 되면 안 됩니다.
- 카드 덱과 룬 덱이 섞이면 안 됩니다.
- 단일 스펠 반복 최적해, 무한 마나 루프, 영구 스턴 락 가능성을 검토해야 합니다.
- UI가 게임 규칙을 직접 처리하거나 Data와 Runtime이 섞이지 않아야 합니다.

## 추천안

내 추천은 바로 수치까지 확정하지 말고, 아래 순서로 가는 것입니다.

1. 신규 룬의 역할을 먼저 정의합니다.
2. 2룬 조합 스펠을 하나만 프로토타입 후보로 둡니다.
3. 밸런스 문서에 반복 최적해 방지 조건을 추가합니다.

반영 위치는 다음이 적절합니다.

{self._bullets(targets, "- `docs_workspace/GDD/05_Rune_System.md`\n- `docs_workspace/GDD/06_Spell_System.md`\n- `docs_workspace/GDD/17_Balance_Rules.md`")}

## 문서 반영 여부

아직 문서에는 저장하지 않았습니다.
이 방향으로 정리할까요? 원하면 "문서에 반영해줘"라고 말해 주세요.

근거:

{docs}
"""
        if intent == UserIntent.DOC_REORGANIZE:
            targets = self._recommended_reorganize_targets(message)
            return f"""## 질문 이해

특정 GDD 문서에 잘못 섞여 들어간 내용을 원래 책임에 맞는 문서로 분리하려는 요청으로 이해했습니다.

## 내 의견

이건 새 기획 검토가 아니라 문서 구조 정리 작업입니다.
원본 문서에서 룬/스펠과 직접 관련 없는 항목을 빼고, 전투 흐름, 상태 효과, 적 행동, 보상, 맵 같은 책임별 문서로 옮기는 방식이 맞습니다.

## 추천 분리 기준

- 룬 덱, 룬 핸드, 룬 조합: `docs_workspace/GDD/05_Rune_System.md`
- 스펠 예약, 캐스팅, 발동: `docs_workspace/GDD/06_Spell_System.md`
- HP, 전투 시작/종료, 턴 흐름: `docs_workspace/GDD/03_Combat_System.md`
- 버프/디버프/부상: `docs_workspace/GDD/07_Status_Effects.md`
- 적 행동 예고와 적 액션: `docs_workspace/GDD/10_Enemy_Design.md`
- 보상, 골드, 카드 보상: `docs_workspace/GDD/13_Reward_System.md`
- 맵 복귀와 노드 진행: `docs_workspace/GDD/12_Map_System.md`

## 문서 반영 여부

문서 반영 요청으로 처리할 수 있습니다.
저장 전에 diff를 확인한 뒤 승인하면 snapshot을 만들고 저장합니다.

근거:

{self._bullets(targets, docs)}
"""
        return f"""## 질문 이해

질문은 단순히 문서 위치를 찾는 것이 아니라, 현재 기획 판단을 어떻게 잡아야 하는지 묻는 것으로 이해했습니다.

## 내 의견

지금은 새 내용을 바로 확정하기보다, 기존 핵심 구조와 어긋나는지 먼저 확인하는 게 좋습니다.
SpellTalker의 재미는 카드, 룬, 스펠, 액션이 각자 다른 역할을 갖고 맞물리는 데 있으므로, 새 규칙도 이 분업을 해치지 않아야 합니다.

## 기존 문서와 비교

검색된 문서 기준으로는 카드/룬/스펠 분리, UI와 규칙 분리, Data와 Runtime 분리 원칙이 가장 중요한 기준입니다.
따라서 어떤 제안이든 "전투 준비", "룬 조합", "스펠 발동", "밸런스 제한" 중 어디에 속하는지 먼저 나누는 편이 좋습니다.

## 충돌 여부

지금 질문만으로는 직접 충돌을 확정하기 어렵습니다.
다만 카드가 직접 승리 수단으로 강해지거나, 룬 없이 핵심 전투가 성립하거나, UI가 규칙을 처리하는 방향이면 기존 원칙과 충돌합니다.

## 추천안

1. 먼저 이 아이디어가 카드, 룬, 스펠, 액션 중 어디에 속하는지 정합니다.
2. 관련 GDD 문서에 TODO로 둘지, 확정 규칙으로 넣을지 나눕니다.
3. 저장이 필요하면 변경 계획과 diff를 만든 뒤 승인하는 흐름으로 가면 됩니다.

## 문서 반영 여부

아직 문서에는 저장하지 않았습니다.
문서에 반영하려면 "문서에 반영해줘"라고 말해 주세요.

근거:

{docs}
"""

    def _snippet_bullets(self, rows: list[dict[str, str]]) -> list[str]:
        snippets = []
        for row in rows:
            for line in row["document"].splitlines():
                line = line.strip(" -\t")
                if len(line) >= 4 and not line.startswith("#"):
                    snippets.append(line[:180])
                if len(snippets) >= 16:
                    return snippets
        return snippets

    def _filter_snippets(self, snippets: list[str], keywords: list[str], fallback: str) -> str:
        matched = [line for line in snippets if any(keyword.lower() in line.lower() for keyword in keywords)]
        return self._bullets(matched[:8], fallback)

    def _bullets(self, lines: list[str], fallback: str) -> str:
        if not lines:
            return fallback
        return "\n".join(f"- {line}" for line in lines)

    def _evidence_line(self, rows: list[dict[str, str]]) -> str:
        if not rows:
            return "관련 문서 없음"
        seen: set[str] = set()
        names: list[str] = []
        for row in rows:
            path = row["path"]
            if path in seen:
                continue
            seen.add(path)
            names.append(f"`{path}`")
            if len(names) >= 4:
                break
        return ", ".join(names)

    def _recommended_targets(self, message: str) -> list[str]:
        lowered = message.lower()
        targets: list[str] = []
        if any(keyword in lowered for keyword in ["룬", "rune"]):
            targets.append("`docs_workspace/GDD/05_Rune_System.md`")
        if any(keyword in lowered for keyword in ["스펠", "spell", "화염구", "빙결"]):
            targets.append("`docs_workspace/GDD/06_Spell_System.md`")
        if any(keyword in lowered for keyword in ["카드", "card"]):
            targets.append("`docs_workspace/GDD/04_Card_System.md`")
        if any(keyword in lowered for keyword in ["ui", "화면"]):
            targets.append("`docs_workspace/GDD/16_UI_UX.md`")
        targets.append("`docs_workspace/GDD/17_Balance_Rules.md`")
        targets.append("`docs_workspace/GDD/99_TODO.md`")
        return list(dict.fromkeys(targets))

    def _recommended_reorganize_targets(self, message: str) -> list[str]:
        lowered = message.lower()
        targets = ["`docs_workspace/GDD/05_Rune_System.md`"]
        if any(keyword in lowered for keyword in ["스펠", "spell", "캐스팅", "예약"]):
            targets.append("`docs_workspace/GDD/06_Spell_System.md`")
        if any(keyword in lowered for keyword in ["hp", "체력", "전투", "능력치", "스탯", "턴"]):
            targets.append("`docs_workspace/GDD/03_Combat_System.md`")
        if any(keyword in lowered for keyword in ["버프", "디버프", "부상", "상태"]):
            targets.append("`docs_workspace/GDD/07_Status_Effects.md`")
        if any(keyword in lowered for keyword in ["적", "enemy"]):
            targets.append("`docs_workspace/GDD/10_Enemy_Design.md`")
        if any(keyword in lowered for keyword in ["보상", "골드", "reward"]):
            targets.append("`docs_workspace/GDD/13_Reward_System.md`")
        if any(keyword in lowered for keyword in ["맵", "map", "노드"]):
            targets.append("`docs_workspace/GDD/12_Map_System.md`")
        return list(dict.fromkeys(targets))
