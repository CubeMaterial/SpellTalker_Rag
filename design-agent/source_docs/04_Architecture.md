# Architecture
전체 흐름 제어 중심.

### GameManager
- 게임 전체 진입점
- 씬 전환 및 전역 상태 관리

### BattleManager
- 전투 시작 / 종료
- 턴 흐름 제어
- 승패 판정

### TurnManager
- Turn Start / Preparation / Initiation / End 흐름 제어
- 단계 전환 관리

### EnemyManager
- 적 생성
- 적 행동 실행
- 적 Intent 갱신

### UIManager
- 화면 갱신 요청
- 전투 UI, 맵 UI, 보상 UI 라우팅

---

## UI Layer
UI는 입력과 출력만 담당한다.

### Rules
- UI는 PlayerRuntime를 직접 수정하지 않는다.
- UI는 Manager 또는 Controller를 호출한다.
- 실제 값 변경은 System / Manager 계층에서 수행한다.

### Example UI Modules
- HandUI
- RuneHandUI
- ManaUI
- BattleHUD
- IntentUI
- RewardUI
- MapUI
- ShopUI

---

## Recommended Data Flow
1. UI 입력
2. Manager가 요청 수신
3. System이 규칙 처리
4. Runtime 상태 갱신
5. UI 반영

예시:
카드 클릭
→ BattleManager 또는 CardController 호출
→ CardSystem.UseCard()
→ PlayerRuntime.currentMana 갱신
→ CardDeckRuntime.discardPile 이동
→ UI 갱신

---

## Key Separation Rules
- CardData와 CardRuntime 상태를 섞지 않는다.
- RuneData와 RuneDeckRuntime 상태를 섞지 않는다.
- SpellData는 정의만 가지며, 발동 결과는 SpellSystem이 처리한다.
- Enemy Intent 표시와 실제 행동 실행은 분리한다.

---

## Prototype Priority Order
1. Battle core loop
2. Card system
3. Rune system
4. Spell system
5. Reward system
6. Map system
7. Shop / Rest / Boss flow

---

## Technical Constraints
- 새 의존성 추가 최소화
- 큰 MonoBehaviour 클래스 금지
- 가능한 한 테스트 가능한 순수 로직 클래스 우선
- Unity 씬 의존 로직은 최소화