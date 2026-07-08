# UI UX

## 1. 목적

이 문서는 `16_UI_UX.md`에 해당하는 `UI UX` 영역을 정리한다. 기존 문서에서 확인된 기준: GameManager

## 2. 현재 확정된 내용

- GameManager
- BattleManager
- TurnManager
- EnemyManager
- UIManager
- 전투 UI, 맵 UI, 보상 UI 라우팅
- UI Layer
- UI는 입력과 출력만 담당한다.
- UI는 PlayerRuntime를 직접 수정하지 않는다.
- UI는 Manager 또는 Controller를 호출한다.
- 실제 값 변경은 System / Manager 계층에서 수행한다.
- Example UI Modules
- HandUI
- RuneHandUI
- ManaUI
- IntentUI
- RewardUI
- MapUI
- ShopUI
- UI 입력
- Manager가 요청 수신
- Runtime 상태 갱신
- UI 반영
- → BattleManager 또는 CardController 호출
- → PlayerRuntime.currentMana 갱신
- → CardDeckRuntime.discardPile 이동
- → UI 갱신
- CardData와 CardRuntime 상태를 섞지 않는다.


## 3. 핵심 규칙

- TODO: 기존 문서에서 핵심 규칙을 확인해야 한다.

## 4. 플레이 흐름

- TurnManager

## 5. 데이터 구조

| 항목 | 설명 | 비고 |
|---|---|---|
| TODO | UI는 PlayerRuntime를 직접 수정하지 않는다. | 원문 확인 필요 |
| TODO | Runtime 상태 갱신 | 원문 확인 필요 |
| TODO | → PlayerRuntime.currentMana 갱신 | 원문 확인 필요 |
| TODO | → CardDeckRuntime.discardPile 이동 | 원문 확인 필요 |
| TODO | CardData와 CardRuntime 상태를 섞지 않는다. | 원문 확인 필요 |

## 6. 예시

- Example UI Modules

## 7. 현재 구현 상태

- TODO: 07_Package_Rebuild_Checklist.md에서 현재 구현 상태를 확인해야 한다.

## 8. TODO

- [ ] 16_UI_UX.md의 부족한 세부 기획을 기존 문서 기준으로 보강한다.
