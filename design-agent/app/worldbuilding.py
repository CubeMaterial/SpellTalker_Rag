from __future__ import annotations

import difflib
import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.llm_client import OllamaClient
from app.settings import Settings


WORLD_BIBLE_NAME = "World_Bible.md"


WORLD_TEMPLATE = """# World Bible

## 1. 핵심 정체성

TODO

## 2. 세계의 기원과 역사

TODO

## 3. 지역과 세력

TODO

## 4. 종족, 존재, 인물

TODO

## 5. 규칙, 마법, 기술

TODO

## 6. 갈등과 금기

TODO

## 7. 게임 적용 메모

TODO

## 8. 미정과 질문

- [ ] 작성 필요
"""


@dataclass
class WorldResult:
    content: str
    diff: str
    saved_path: Path


class WorldbuildingService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.llm = OllamaClient(self.settings)
        self.settings.world_workspace.mkdir(parents=True, exist_ok=True)

    @property
    def bible_path(self) -> Path:
        return self.settings.world_workspace / WORLD_BIBLE_NAME

    def ensure_bible(self) -> Path:
        if not self.bible_path.exists():
            self.bible_path.write_text(WORLD_TEMPLATE, encoding="utf-8")
        return self.bible_path

    def read_bible(self) -> str:
        return self.ensure_bible().read_text(encoding="utf-8")

    def organize_and_save(self, raw_text: str) -> WorldResult:
        raw_text = raw_text.strip()
        if not raw_text:
            raise ValueError("정리할 세계관 내용을 입력하세요.")
        old = self.read_bible()
        organized = self._organize(raw_text, old)
        new = self._merge(old, organized, raw_text)
        self._snapshot_current()
        self.bible_path.write_text(new, encoding="utf-8")
        return WorldResult(
            content=new,
            diff=self._diff(old, new),
            saved_path=self.bible_path,
        )

    def answer(self, question: str) -> str:
        question = question.strip()
        if not question:
            raise ValueError("질문을 입력하세요.")
        bible = self.read_bible()
        prompt = f"""아래 세계관 바이블만 근거로 사용자 질문에 답하라.
바이블에서 확인되지 않는 내용은 추측하지 말고 "세계관 문서에 아직 없다"고 말하라.
다른 게임에도 재사용 가능한 설정인지, 특정 게임 전용 설정인지 구분해서 답하라.

세계관 바이블:
{bible}

질문:
{question}
"""
        response = self.llm.generate(prompt, self._system_prompt())
        if response.startswith("[LLM unavailable") or not response.strip():
            return self._fallback_answer(question, bible)
        return response

    def check_fit(self, setting_text: str) -> str:
        setting_text = setting_text.strip()
        if not setting_text:
            raise ValueError("검토할 설정을 입력하세요.")
        bible = self.read_bible()
        prompt = f"""아래 신규 설정이 세계관 바이블과 어긋나는지 검토하라.

출력 형식:
## 적합성
- 맞음 / 주의 / 충돌 중 하나

## 근거
- 세계관 바이블에서 확인되는 근거

## 충돌 또는 빈틈
- 충돌 가능성 또는 아직 정의되지 않은 내용

## 정리 제안
- 세계관에 맞추려면 어떻게 바꾸면 좋은지

세계관 바이블:
{bible}

신규 설정:
{setting_text}
"""
        response = self.llm.generate(prompt, self._system_prompt())
        if response.startswith("[LLM unavailable") or not response.strip():
            return self._fallback_check(setting_text, bible)
        return response

    def _organize(self, raw_text: str, old: str) -> str:
        prompt = f"""사용자가 자유롭게 쓴 세계관 메모를 재사용 가능한 World Bible 항목으로 정리하라.
특정 게임의 시스템 수치보다 세계관의 정체성, 역사, 지역, 세력, 존재, 규칙, 갈등, 미정 질문을 우선한다.
이미 있는 세계관과 모순될 가능성이 있으면 "미정과 질문"에 남겨라.

기존 World Bible:
{old}

새 세계관 메모:
{raw_text}

반드시 아래 Markdown 섹션으로만 답하라.

## 핵심 정체성
- ...

## 세계의 기원과 역사
- ...

## 지역과 세력
- ...

## 종족, 존재, 인물
- ...

## 규칙, 마법, 기술
- ...

## 갈등과 금기
- ...

## 게임 적용 메모
- ...

## 미정과 질문
- [ ] ...
"""
        response = self.llm.generate(prompt, self._system_prompt())
        if response.startswith("[LLM unavailable") or not response.strip():
            return self._fallback_organize(raw_text)
        return response

    def _merge(self, old: str, organized: str, raw_text: str) -> str:
        today = datetime.now().strftime("%Y-%m-%d")
        cleaned_old = self._strip_placeholders(old)
        entry = f"""

## 정리 기록

### {today}

{organized.strip()}

<details>
<summary>원문 메모</summary>

{raw_text.strip()}

</details>
"""
        if "## 정리 기록" in cleaned_old:
            body, records = cleaned_old.split("## 정리 기록", 1)
            return body.rstrip() + "\n\n## 정리 기록" + records.rstrip() + "\n\n" + entry.split("## 정리 기록", 1)[1].lstrip()
        return cleaned_old.rstrip() + entry

    def _strip_placeholders(self, text: str) -> str:
        lines = []
        for line in text.splitlines():
            if line.strip() in {"TODO", "- [ ] 작성 필요"}:
                continue
            lines.append(line)
        return "\n".join(lines).strip() + "\n"

    def _snapshot_current(self) -> None:
        if not self.bible_path.exists():
            return
        snapshot_dir = self.settings.world_workspace / "snapshots"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination = snapshot_dir / f"World_Bible_{stamp}.md"
        if destination.exists():
            destination = snapshot_dir / f"World_Bible_{stamp}_2.md"
        shutil.copy2(self.bible_path, destination)

    def _diff(self, old: str, new: str) -> str:
        return "".join(
            difflib.unified_diff(
                old.splitlines(keepends=True),
                new.splitlines(keepends=True),
                fromfile=f"{self.bible_path} (before)",
                tofile=f"{self.bible_path} (after)",
            )
        )

    def _fallback_organize(self, raw_text: str) -> str:
        sentences = [line.strip(" -\t") for line in re.split(r"[\n.]+", raw_text) if line.strip()]
        bullets = "\n".join(f"- {sentence}" for sentence in sentences[:12]) or "- 세계관 메모 추가"
        return f"""## 핵심 정체성
{bullets}

## 세계의 기원과 역사
- TODO: 원문에서 역사 정보를 더 분리해야 합니다.

## 지역과 세력
- TODO: 지역, 국가, 조직, 세력 정보를 더 분리해야 합니다.

## 종족, 존재, 인물
- TODO: 주요 존재와 인물 정보를 더 분리해야 합니다.

## 규칙, 마법, 기술
- TODO: 세계의 고유 규칙을 더 분리해야 합니다.

## 갈등과 금기
- TODO: 충돌 가능성과 금기를 더 분리해야 합니다.

## 게임 적용 메모
- 다른 게임에서도 재사용할 수 있도록 게임 시스템 수치와 세계관 설정을 분리해야 합니다.

## 미정과 질문
- [ ] 이 설정이 모든 게임에 공통으로 적용되는지, 특정 게임 전용 변주인지 확인 필요
"""

    def _fallback_answer(self, question: str, bible: str) -> str:
        matches = self._matching_lines(question, bible)
        if not matches:
            return "세계관 문서에서 직접 근거를 찾지 못했습니다. 먼저 World Bible에 해당 설정을 정리해두는 것이 좋습니다."
        return "세계관 문서에서 관련 근거는 다음과 같습니다.\n\n" + "\n".join(f"- {line}" for line in matches[:8])

    def _fallback_check(self, setting_text: str, bible: str) -> str:
        matches = self._matching_lines(setting_text, bible)
        if not matches:
            return """## 적합성
- 주의

## 근거
- 현재 World Bible에서 직접 연결되는 근거를 찾지 못했습니다.

## 충돌 또는 빈틈
- 충돌이라고 단정할 수는 없지만, 세계관 문서에 아직 정의되지 않은 설정입니다.

## 정리 제안
- 이 설정이 공통 세계관 규칙인지, 특정 게임 전용 변주인지 먼저 기록하세요.
"""
        return """## 적합성
- 주의

## 근거
""" + "\n".join(f"- {line}" for line in matches[:8]) + """

## 충돌 또는 빈틈
- 자동 fallback 검토라서 직접적인 충돌 여부는 확정하지 못했습니다.

## 정리 제안
- 위 근거와 새 설정의 차이를 World Bible의 미정과 질문에 남겨두는 것을 추천합니다.
"""

    def _matching_lines(self, query: str, bible: str) -> list[str]:
        keywords = [token for token in re.findall(r"[A-Za-z0-9_가-힣]+", query.lower()) if len(token) >= 2]
        matches = []
        for line in bible.splitlines():
            clean = line.strip(" -#\t")
            if len(clean) < 4:
                continue
            lowered = clean.lower()
            if any(keyword in lowered for keyword in keywords):
                matches.append(clean[:220])
        return matches

    def _system_prompt(self) -> str:
        return "너는 여러 게임에 재사용 가능한 세계관 바이블을 정리하는 설정 편집자다. 근거 없는 확정은 피하고, 공통 세계관과 게임별 변주를 구분한다."
