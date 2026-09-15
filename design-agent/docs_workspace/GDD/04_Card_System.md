# Card System

## 1. 목적

이 문서는 `04_Card_System.md`에 해당하는 `Card System` 영역을 정리한다. 기존 문서에서 확인된 기준: Card Deck

## 2. 현재 확정된 내용

- Card Deck
- 카드가 저장된 드로우 더미.
- Hand
- 플레이어가 현재 사용할 수 있는 카드 목록.
- Discard Pile
- 사용된 카드가 이동하는 더미.
- Regeneration
- 카드가 Discard Pile에서 다시 Card Deck으로 돌아오는 메커니즘.
- Regen Count
- 카드가 Card Deck으로 복귀하기까지 남은 턴 수.
- Exhaust
- 카드가 현재 전투 중 다시 사용할 수 없도록 완전히 제거되는 상태.
- Mana
- 주로 카드 사용을 통해 획득한다.
- 룬은 별도의 덱 구조로 관리된다.
- Rune Deck
- Rune Hand
- Rune Discard Pile
- 카드 및 스펠과 별도로 존재한다.
- 카드, 스펠, 액션이 영향을 미치는 대상.
- 카드 구매, 제거, 강화 등을 수행하는 노드.
- Mana Design Rules
- 카드만 반복하여 무한 마나를 만드는 구조를 금지한다.
- 마나 수급 속도는 룬 운용과 스펠 사용 템포를 압도하면 안 된다.
- 카드 구매, 제거, 강화 중 핵심 기능만 제공한다.
- 무한 마나 루프
- 카드만으로 승리하는 구조
- [ ] BattleManager
- [ ] TurnManager
- Milestone 2 - Card System
- 카드 드로우 가능
- 카드 사용 가능
- 마나 획득 가능
- 카드 버림 가능
- 카드 재생 가능
- [ ] CardData
- [ ] CardDeckRuntime
- [ ] CardSystem
- [ ] Hand UI
- Rune Hand 5개 유지 가능
- [ ] RuneDeckRuntime
- [ ] Rune Hand UI
- 마나 소모 가능
- 준비 단계에서 손패가 5장이 되도록 카드를 드로우한다.
- 손패가 5장 이상이면 1장만 드로우한다.
- 덱에 카드가 없을 때 추가 드로우가 필요하면 피해를 받는 규칙을 검토한다.
- 사용한 카드는 묘지/버림 더미로 이동하고, 카드 기능은 큐에 쌓아 순차 처리한다.
- 턴 종료 시 묘지의 카드는 재생 수치를 증가시키고, 재생 완료 시 덱 아래로 돌아간다.

## 용어

- Card Deck: Card Deck
- Hand: Hand
- Discard Pile: Discard Pile
- Regeneration: Regeneration
- Regen Count: Regen Count
- Exhaust: Exhaust
- Mana: Mana


## 3. 핵심 규칙

- Mana Design Rules
- 카드만 반복하여 무한 마나를 만드는 구조를 금지한다.
- 카드는 전투 준비와 자원 운용의 중심이며, 룬/스펠 책임을 대체하지 않는다.

## 4. 플레이 흐름

- 카드가 Card Deck으로 복귀하기까지 남은 턴 수.
- 카드 구매, 제거, 강화 등을 수행하는 노드.
- 무한 마나 루프
- [ ] TurnManager
- 준비 단계 카드 드로우 -> 카드 사용 -> 버림/재생 흐름을 기본 카드 루프로 둔다.

## 5. 데이터 구조

| 항목 | 설명 | 비고 |
|---|---|---|
| Card Deck | Card Deck | 기존 용어 문서 기준 |
| Hand | Hand | 기존 용어 문서 기준 |
| Discard Pile | Discard Pile | 기존 용어 문서 기준 |
| Regeneration | Regeneration | 기존 용어 문서 기준 |
| Regen Count | Regen Count | 기존 용어 문서 기준 |
| Exhaust | Exhaust | 기존 용어 문서 기준 |
| Mana | Mana | 기존 용어 문서 기준 |
| TODO | 룬은 별도의 덱 구조로 관리된다. | 원문 확인 필요 |
| TODO | 카드만 반복하여 무한 마나를 만드는 구조를 금지한다. | 원문 확인 필요 |
| TODO | 카드만으로 승리하는 구조 | 원문 확인 필요 |
| TODO | [ ] CardData | 원문 확인 필요 |
| CardQueue | 카드 효과는 큐에 쌓아 순차 처리한다. | 원문 초안 분리 |
| TODO | [ ] CardDeckRuntime | 원문 확인 필요 |
| TODO | [ ] RuneDeckRuntime | 원문 확인 필요 |

## 6. 예시

- TODO: 기존 문서에서 예시를 확인해야 한다.

## 7. 현재 구현 상태

- TODO: 07_Package_Rebuild_Checklist.md에서 현재 구현 상태를 확인해야 한다.

## 8. TODO

- [ ] 04_Card_System.md의 부족한 세부 기획을 기존 문서 기준으로 보강한다.

## Change Log

### 2026-07-15
- 05_Rune_System.md에 섞여 있던 카드 드로우, 사용, 재생 흐름을 Card System으로 분리
