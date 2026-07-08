# Agents

## Primary Rule
항상 GLOSSARY.md, GAME_SPEC.md, CONTENT_RULES.md, ARCHITECTURE.md를 먼저 읽고 작업한다.

## Implementation Rules
- 문서에 없는 시스템을 임의로 추가하지 않는다.
- 데이터와 런타임 상태를 섞지 않는다.
- Card System과 Rune System을 별개로 구현한다.
- UI에서 게임 규칙을 직접 처리하지 않는다.
- ScriptableObject에는 런타임 상태를 넣지 않는다.

## Workflow
1. 작업 목표 확인
2. 관련 문서 확인
3. 최소 구현 범위 설정
4. 컴파일 가능한 코드 작성
5. 변경 파일 요약
6. 남은 TODO 기록

## Code Style Rules
- public 필드 남용 금지
- 명확한 책임 분리 유지
- 큰 클래스보다 작은 역할 단위 우선
- 하드코딩된 수치 최소화
- 데이터 테이블 참조 우선

## Forbidden
- 규칙을 문서와 다르게 구현하는 것
- 카드와 룬 덱을 하나의 공용 덱처럼 처리하는 것
- 테스트 없이 핵심 로직을 크게 변경하는 것