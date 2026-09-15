# SpellTalker Design Agent

## 목적

로컬 LLM과 RAG를 이용하여 SpellTalker 게임 기획 문서를 대화 기반으로 관리하는 도구.

이 Agent는 Markdown 기반 GDD를 읽고, 사용자의 기획 아이디어와 관련 문서를 검색한 뒤, 변경 계획과 충돌 가능성을 제안한다. 승인된 변경은 스냅샷과 diff 확인을 거쳐 문서에 반영한다.

## 설치

```bash
pip install -r requirements.txt
```

## Ollama 준비

```bash
ollama pull qwen3:14b
ollama pull nomic-embed-text
```

기본 설정은 `.env` 또는 `config/settings.yaml`에서 변경할 수 있다.

```txt
LLM_MODEL=qwen3:14b
EMBEDDING_MODEL=nomic-embed-text
OLLAMA_BASE_URL=http://localhost:11434
```

## 실행

```bash
python main.py init-docs
python main.py build-gdd-from-source
python main.py index
python main.py chat
python main.py check
python main.py desktop
python main.py ui
```

## 명령

- `python main.py init-docs`: 기본 GDD 문서 템플릿 생성
- `python main.py build-gdd-from-source`: `source_docs/`의 기존 Markdown 문서를 분석해 GDD 초안 생성
- `python main.py index`: `docs_workspace/` 아래 Markdown 문서를 ChromaDB에 인덱싱
- `python main.py chat`: 대화형 기획 정리 및 승인 기반 문서 수정
- `python main.py check`: 문서 일관성 검사 리포트 생성
- `python main.py snapshot`: 현재 문서 작업공간 백업
- `python main.py desktop`: 로컬 웹 UI를 별도 데스크톱 창으로 실행
- `python main.py ui`: 로컬 웹 UI 실행

명령 없이 `python main.py`만 실행하면 기본으로 desktop 모드가 실행된다.

## 안전장치

- 문서 수정 전 `storage/snapshots/`에 백업 생성
- 변경 전/후 unified diff 출력
- CLI `y/n` 승인 후 저장
- `.env`, ChromaDB 저장소, 스냅샷, 리포트는 `.gitignore` 처리

## Source Docs 기반 GDD 생성

기존 기획/개발 문서를 `source_docs/`에 넣은 뒤 실행한다.

```bash
python main.py build-gdd-from-source
```

명령은 `docs_workspace/GDD/`를 먼저 백업하고, 생성될 문서 diff를 출력한 뒤 승인 시 저장한다. 원문에서 확인되지 않은 내용은 `TODO`로 남긴다.

## 웹 UI

Windows command 창의 한글 입력 문제를 피하려면 웹 UI를 기본으로 사용한다.

```bash
python main.py ui
```

브라우저에서 `http://localhost:8000`에 접속한다.

- `/chat`: 한글 textarea로 기획 아이디어 입력, 변경 계획 생성, diff 확인
- `/chat`: 세션별 대화, 상태 질문, 아이디어 충돌 검토, 명시적 문서 반영 요청 처리
- `/diff`: 기존 단발 pending 변경 저장 또는 폐기
- `/world`: 게임별 GDD와 분리된 재사용 세계관 정리, 질문, 적합성 검토
- `/docs`: `docs_workspace/`, `source_docs/`, `storage/reports/` Markdown 문서 읽기 전용 보기
- `/workspace`: `docs_workspace/` 백업 생성/복원, 브랜치 생성/전환
- `/data`: `data_sources/` 아래 CSV를 표로 확인/수정하고 Unity용 JSON으로 export
- `Build GDD`: `source_docs/` 기반 GDD 초안 생성
- `Index`: 문서 인덱싱
- `Check`: 일관성 검사 리포트 생성

### Chat Mode

- 기본은 Conversation Mode이며 파일을 수정하지 않는다.
- 사용자가 "문서에 반영해줘", "저장해줘", "적용해줘"처럼 명시하거나 `문서 반영 모드`를 켠 경우에만 Change Proposal Mode로 전환한다.
- Change Proposal Mode에서는 변경 계획과 diff를 만들고, 승인 저장 전에는 실제 Markdown 파일을 덮어쓰지 않는다.
- 대화 기록은 `storage/conversations/`, 세션별 pending diff는 `storage/pending/`에 UTF-8 JSON으로 저장된다.

## CSV Data Tables

캐릭터, 적, 스펠, 아이템 같은 테이블형 데이터는 `data_sources/`에 CSV로 넣는다.

```txt
data_sources/
  characters.csv
  enemies.csv
  spells.csv
  items.csv
```

웹 UI의 `/data`에서 CSV를 표로 확인하고 셀/행을 수정할 수 있다. 저장 시 중복 header, 빈/중복 `id` 같은 기본 검사를 수행한다.

Unity용 JSON은 `Export Unity JSON`으로 생성한다.

```txt
exports/unity/
  characters.json
  enemies.json
  spells.json
  items.json
```

export 형식은 Unity에서 읽기 쉬운 wrapper 구조다.

```json
{
  "table": "spells",
  "source": "spells.csv",
  "exported_at": "2026-07-09T12:00:00",
  "items": []
}
```

## Workspace Backup & Branches

웹 UI의 `/workspace`에서 현재 `docs_workspace/`를 백업하거나, 백업을 다시 불러올 수 있다.
백업을 불러오기 전에는 현재 상태를 새 백업으로 먼저 저장한다.

브랜치는 Git 저장소 전체가 아니라 `docs_workspace/`만 복사해서 관리하는 가벼운 작업공간 분기다.
새 브랜치를 만들면 현재 문서 상태가 `storage/branches/{branch}`에 저장되고, 브랜치 전환 시 현재 브랜치를 저장한 뒤 선택한 브랜치 내용을 `docs_workspace/`로 불러온다.

## Worldbuilding Mode

웹 UI의 `/world`는 게임별 GDD와 분리된 재사용 세계관을 관리한다.
자유롭게 쓴 세계관 메모를 `world_workspace/World_Bible.md`로 정리하고, 나중에 다른 게임 제작 시 이 파일만 가져가 공통 세계관으로 사용할 수 있다.

이 화면에서는 World Bible을 근거로 세계관 질문에 답하거나, 새 게임 설정이 기존 세계관과 맞는지 검토할 수 있다.
