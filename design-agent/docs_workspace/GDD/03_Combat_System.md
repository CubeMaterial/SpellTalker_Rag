# Combat System

## 1. 목적

이 문서는 `03_Combat_System.md`에 해당하는 `Combat System` 영역을 정리한다. 기존 문서에서 확인된 기준: 카드가 현재 전투 중 다시 사용할 수 없도록 완전히 제거되는 상태.

## 2. 현재 확정된 내용

- 카드가 현재 전투 중 다시 사용할 수 없도록 완전히 제거되는 상태.
- 주요 공격 및 전투 효과의 중심 수단이다.
- Injury
- Battle Node
- 일반 전투가 발생하는 노드.
- 강한 적과 전투하는 노드.
- 던전 마지막에 배치되는 보스 전투 노드.
- Injury System
- Injury는 일반 HP와 별도로 추적되는 누적 손상 상태다.
- 일부 스킬이나 효과는 Injury를 참조하거나 소비할 수 있다.
- Battle Rules
- Victory
- 전투 중 모든 적을 처치하면 승리한다.
- Defeat
- 플레이어 HP가 0 이하가 되면 패배한다.
- 전투 승리 후:
- 전투 진입
- 전투 승패 판정
- 전투 보상 획득
- Milestone 1 - Core Battle Loop
- 전투 시작 가능
- [ ] BattleManager
- [ ] PlayerRuntime
- [ ] EnemyRuntime
- [ ] Victory / Defeat flow
- [ ] CardDeckRuntime
- [ ] RuneDeckRuntime
- 전투 후 보상 선택 가능

## 용어

- Mana: Mana
- Action: Action
- Cooldown: Cooldown
- Target: Target
- Injury: Injury


## 3. 핵심 규칙

- Battle Rules

## 4. 플레이 흐름

- Battle Node
- 일반 전투가 발생하는 노드.
- 강한 적과 전투하는 노드.
- 던전 마지막에 배치되는 보스 전투 노드.
- Milestone 1 - Core Battle Loop
- [ ] Victory / Defeat flow

## 5. 데이터 구조

| 항목 | 설명 | 비고 |
|---|---|---|
| Mana | Mana | 기존 용어 문서 기준 |
| Action | Action | 기존 용어 문서 기준 |
| Cooldown | Cooldown | 기존 용어 문서 기준 |
| Target | Target | 기존 용어 문서 기준 |
| Injury | Injury | 기존 용어 문서 기준 |
| TODO | [ ] PlayerRuntime | 원문 확인 필요 |
| TODO | [ ] EnemyRuntime | 원문 확인 필요 |
| TODO | [ ] CardDeckRuntime | 원문 확인 필요 |
| TODO | [ ] RuneDeckRuntime | 원문 확인 필요 |

## 6. 예시

- TODO: 기존 문서에서 예시를 확인해야 한다.

## 7. 현재 구현 상태

- TODO: 07_Package_Rebuild_Checklist.md에서 현재 구현 상태를 확인해야 한다.

## 8. TODO

- [ ] 03_Combat_System.md의 부족한 세부 기획을 기존 문서 기준으로 보강한다.
