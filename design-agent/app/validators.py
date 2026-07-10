from __future__ import annotations

from datetime import datetime

from app.document_manager import DocumentManager
from app.llm_client import OllamaClient
from app.rag_service import RAGService
from app.settings import Settings


RULES = [
    ("카드 직접 승리 수단", ["카드로 직접 피해", "카드 공격", "카드가 적을 처치"]),
    ("카드 덱과 룬 덱 혼합", ["카드 덱과 룬 덱을 합친", "카드/룬 공용 덱", "통합 덱"]),
    ("룬 없는 핵심 전투", ["룬 없이 전투", "스펠 없이 승리", "카드만으로 전투"]),
    ("단일 스펠 반복 최적해", ["반복 사용하면 최적", "한 스펠만 반복", "무한 반복"]),
    ("UI가 게임 규칙 처리", ["UI에서 데미지 계산", "UI가 규칙 처리", "UI에서 전투 판정"]),
    ("Data와 Runtime 혼합", ["ScriptableObject에 현재 HP", "SO에 런타임", "데이터에 현재 상태"]),
]


class ConsistencyChecker:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.documents = DocumentManager(self.settings)
        self.llm = OllamaClient(self.settings)
        self.rag = RAGService(self.settings)

    def run(self) -> str:
        self.settings.reports_path.mkdir(parents=True, exist_ok=True)
        combined = []
        findings = []
        for path in self.documents.markdown_files():
            text = path.read_text(encoding="utf-8")
            rel = path.relative_to(self.settings.docs_workspace).as_posix()
            combined.append(f"# FILE: {rel}\n{text}")
            for name, patterns in RULES:
                hits = [pattern for pattern in patterns if pattern in text]
                if hits:
                    findings.append(f"- `{rel}`: {name} 의심 표현 발견: {', '.join(hits)}")

        prompt = self.settings.prompt("consistency_checker.md")
        rag_rows = self.rag.search(
            "카드 직접 승리 수단 카드 덱 룬 덱 혼합 무한 마나 무한 드로우 영구 스턴 UI 게임 규칙 Runtime ScriptableObject 충돌",
            limit=12,
            min_results=4,
        )
        rag_context = self.rag.context_text(rag_rows)
        llm_input = f"{rag_context}\n\n## 규칙 기반 의심 항목\n{chr(10).join(findings) if findings else '- 없음'}"
        llm_report = self.llm.generate(llm_input, prompt) if combined else ""
        if llm_report.startswith("[LLM unavailable") or not llm_report:
            llm_report = self._fallback_report(findings)

        report = f"""# SpellTalker Consistency Report

Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{llm_report.strip()}

## 규칙 기반 스캔

{chr(10).join(findings) if findings else "- 명시적인 충돌 표현을 찾지 못했습니다."}
"""
        path = self.settings.reports_path / "consistency_report.md"
        path.write_text(report, encoding="utf-8")
        return str(path)

    def _fallback_report(self, findings: list[str]) -> str:
        return f"""## 문제 요약

로컬 LLM 응답을 사용할 수 없어 규칙 기반 키워드 검사로 대체했습니다.

## 충돌 항목

{chr(10).join(findings) if findings else "- 발견된 항목 없음"}

## 수정 제안

- 카드는 마나와 전투 준비 수단으로 유지합니다.
- 스펠은 룬 조합 기반 핵심 전투 수단으로 유지합니다.
- UI 문서는 표시와 입력 전달 책임으로 제한합니다.
- ScriptableObject에는 정적 데이터만 두고 Runtime 상태는 별도 객체로 분리합니다.

## TODO

- LLM 모델을 실행한 뒤 `python main.py check`를 다시 실행해 문맥 기반 검사를 수행합니다.
"""
