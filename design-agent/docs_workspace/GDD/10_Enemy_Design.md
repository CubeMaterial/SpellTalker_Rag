# Enemy Design

## 1. 목적

이 문서는 `10_Enemy_Design.md`에 해당하는 `Enemy Design` 영역을 정리한다. 기존 문서에서 확인된 기준: Enemy Design Rules

## 2. 현재 확정된 내용

- Enemy Design Rules
- 적 Intent는 읽을 수 있어야 하지만, 대응이 단순 반복만 되면 안 된다.
- 적은 일반, 엘리트, 보스 등급으로 구분한다.
- 적의 머리 위 행동 아이콘으로 다음 행동과 기대 피해를 예고한다.
- 준비 단계에서 적은 특정 상태가 아닌 이상 즉시 행동하지 않고 예약된 행동을 유지한다.
- 실시간 전투에서 적은 AI에 따라 행동하고, 행동 종료 후 다음 행동 예고를 갱신한다.

## 용어

- Target: Target
- Intent: Intent


## 3. 핵심 규칙

- Enemy Design Rules
- 적 행동은 플레이어가 대응할 수 있도록 예고되어야 한다.
- 모든 적 액션에는 선 딜레이가 존재한다.

## 4. 플레이 흐름

- 준비 단계 행동 예고 -> 실시간 전투에서 예약 행동 수행 -> 다음 행동 예고 갱신 순서로 처리한다.

## 5. 데이터 구조

| 항목 | 설명 | 비고 |
|---|---|---|
| Target | Target | 기존 용어 문서 기준 |
| Intent | Intent | 기존 용어 문서 기준 |
| EnemyRank | 일반, 엘리트, 보스 등 적 종류 | 원문 초안 분리 |
| EnemyAction | 선 딜레이와 의도를 가진 적 행동 | 원문 초안 분리 |

## 6. 예시

- TODO: 기존 문서에서 예시를 확인해야 한다.

## 7. 현재 구현 상태

- TODO: 07_Package_Rebuild_Checklist.md에서 현재 구현 상태를 확인해야 한다.

## 8. TODO

- [ ] 10_Enemy_Design.md의 부족한 세부 기획을 기존 문서 기준으로 보강한다.

## Change Log

### 2026-07-15
- 05_Rune_System.md에 섞여 있던 적 행동 예고, 적 액션, 적 등급 내용을 Enemy Design으로 분리
