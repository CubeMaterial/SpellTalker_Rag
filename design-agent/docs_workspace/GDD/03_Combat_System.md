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
- 전투 시작 시 특성, 장비, 유물, 스탯에 따른 전투 시작 효과를 적용한다.
- 준비 단계에서는 카드 드로우, 카드/스펠 예약, 적 행동 예고가 처리된다.
- 실시간 전투 진행 중에는 캐스팅, 카드 사용, 액션, 적 행동이 선 딜레이와 함께 처리된다.
- 턴 종료 시 카드 재생, 상태 효과 처리, 턴 카운트 증가 후 준비 단계로 돌아간다.
- 플레이어 HP가 0이 되면 게임 오버, 모든 적 HP가 0이 되면 전투 승리로 처리한다.
- 힘, 민첩, 지능 같은 능력치는 전투 중 지연 시간, 회피율, 마나 회복, 일부 스펠 효과에 영향을 줄 수 있다.

## 용어

- Mana: Mana
- Action: Action
- Cooldown: Cooldown
- Target: Target
- Injury: Injury


## 3. 핵심 규칙

- Battle Rules
- 전투 시작 효과는 전투 진입 시 한 번 적용한다.
- 전투 종료 조건은 플레이어 HP와 적 전체 HP를 기준으로 판정한다.
- 능력치 효과는 전투 규칙으로 관리하되 카드/룬/스펠 데이터 자체와 섞지 않는다.

## 4. 플레이 흐름

- Battle Node
- 일반 전투가 발생하는 노드.
- 강한 적과 전투하는 노드.
- 던전 마지막에 배치되는 보스 전투 노드.
- Milestone 1 - Core Battle Loop
- [ ] Victory / Defeat flow
- 전투 시작 -> 준비 단계 -> 실시간 전투 진행 -> 턴 종료 -> 준비 단계 순환을 기본 흐름으로 둔다.
- 전투 승리 후에는 적 종류를 기록하고 보상/맵 흐름으로 넘긴다.

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
| PlayerStats | 힘, 민첩, 지능 등 전투에 영향을 주는 정적/전투 중 능력치 | 원문 초안 분리 |
| HP / Injury | 현재 체력과 누적 부상은 분리해서 추적한다. | 원문 초안 분리 |

## 6. 예시

- TODO: 기존 문서에서 예시를 확인해야 한다.

## 7. 현재 구현 상태

- TODO: 07_Package_Rebuild_Checklist.md에서 현재 구현 상태를 확인해야 한다.

## 8. TODO

- [ ] 03_Combat_System.md의 부족한 세부 기획을 기존 문서 기준으로 보강한다.

## Change Log

### 2026-07-15
- 05_Rune_System.md에 섞여 있던 전투 흐름, HP, 능력치 내용을 Combat System으로 분리
