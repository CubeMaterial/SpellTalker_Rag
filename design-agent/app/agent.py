from __future__ import annotations

from app.change_planner import ChangePlanner
from app.document_manager import DocumentManager
from app.rag_service import RAGService
from app.settings import Settings


class DesignAgent:
    def __init__(self) -> None:
        self.settings = Settings()
        self.rag = RAGService(self.settings)
        self.planner = ChangePlanner(self.settings)
        self.documents = DocumentManager(self.settings)

    def chat(self) -> None:
        print("SpellTalker Design Agent")
        print("기획 아이디어를 입력하세요. 종료하려면 q 또는 quit를 입력하세요.")
        while True:
            idea = input("\nidea> ").strip()
            if idea.lower() in {"q", "quit", "exit"}:
                break
            if not idea:
                continue

            context = self.rag.search(idea)
            plan = self.planner.create_plan(idea, context)
            print("\n" + str(plan["markdown"]))

            approve = input("\n이 변경 계획을 문서에 반영할까요? [y/N] ").strip().lower()
            if approve != "y":
                print("변경하지 않았습니다.")
                continue

            self.documents.snapshot_docs()
            updates = [
                self.documents.build_update(target, idea, str(plan["markdown"]))
                for target in plan["targets"]
            ]
            for path, old, new in updates:
                print("\n" + self.documents.diff(path, old, new))

            save = input("\n위 diff를 저장할까요? [y/N] ").strip().lower()
            if save != "y":
                print("저장하지 않았습니다. 스냅샷만 생성되었습니다.")
                continue

            for path, _old, new in updates:
                self.documents.save(path, new)
            print(f"{len(updates)}개 문서를 저장했습니다. 필요하면 `python main.py index`를 다시 실행하세요.")
