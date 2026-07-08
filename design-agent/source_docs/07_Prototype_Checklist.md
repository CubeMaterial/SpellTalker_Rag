# Prototype Checklist (Docs ↔ Implementation)

이 문서는 `Assets/Docs/02_Game Spec.md`의 **Prototype Completion Condition**을 기준으로,
현재 코드 구현 상태를 빠르게 점검하고 다음 작업 TODO를 정리한다.

---

## 기준 문서
- Game Spec: `Assets/Docs/02_Game Spec.md`
- Architecture: `Assets/Docs/04_Architecture.md`
- Plans: `Assets/Docs/06_Plans.md`

---

## 완료 조건 체크리스트

표기:
- ✅ 구현됨(프로토타입 레벨로 동작 가능)
- 🟡 부분 구현(동작은 하나 끊기거나 규칙/루프가 불완전)
- ❌ 미구현

### 1) 맵 진입
- 🟡 현재: `MasterManager.Start()`에서 `MapManager.Initialize(FloorType.Tutorial)` 호출로 맵 생성/표시 루트는 존재.
  - 근거: `Assets/SpellTalker/Scripts/Manager/Common/MasterManager.cs`
  - 근거: `Assets/SpellTalker/Scripts/Manager/Map/MapManager.cs`
- TODO:
  - (선택) “게임 시작 → 맵 진입”을 `GameManager` 진입점으로 정리.
    - 후보: `Assets/SpellTalker/Scripts/Manager/Common/GameManager.cs`
  - (프로토타입) 맵 컨텐츠 랜덤 배치가 ScriptableObject 설정으로 동작하도록 `MapContentConfigData` 에셋을 생성/연결.
    - 관련: `Assets/SpellTalker/Scripts/Data/Map/MapContentConfigData.cs`
    - 관련: `Assets/SpellTalker/Scripts/Data/Map/MapFloorContentData.cs`
    - 관련: `Assets/SpellTalker/Scripts/Data/Map/MapEncounterPoolData.cs`

### 2) 전투 진입
- ✅ 현재: 맵 셀 진입 시 `EncounterType`이 Combat/Elite/Boss면 `BattleManager.StartBattle()` 호출.
  - 근거: `Assets/SpellTalker/Scripts/Manager/Common/MasterManager.cs`
  - 근거: `Assets/SpellTalker/Scripts/Manager/Battle/BattleManager.cs`

### 2.5) 카드 재생(Reshuffle/Regeneration)
- 🟡 현재: `CardData.isReusable` + `regenCount` 기반 “재생(턴 경과 후 덱 복귀)”이 전투 턴 종료 시점에 틱되도록 연결됨.
  - 근거: `Assets/SpellTalker/Scripts/Manager/Battle/BattleManager.cs`
  - 근거: `Assets/SpellTalker/Scripts/Manager/Battle/CardManager.cs`
  - 근거: `Assets/SpellTalker/Scripts/Runtime/CardInstance.cs`
- TODO:
  - “재생 카드가 덱으로 돌아올 때 시각 피드백/로그” 등은 필요 시 추가.

### 3) 카드 사용
- ✅ 현재: 카드 사용 플로우를 `CardManager.UseCard(...)` 단일 경로로 통일해서 런타임 상태(손패/덱/버림)와 UI 이벤트가 일관되게 동작.
  - 호출 경로: `HandUI.PlayCard()` → `CardManager.UseCard(...)`
    - 근거: `Assets/SpellTalker/Scripts/UI/Battle/HandUI.cs`
    - 근거: `Assets/SpellTalker/Scripts/Manager/Battle/CardManager.cs`
  - 처리 순서: 손패 제거 → 효과 실행 → 마나 반영 → 버림/재생 처리 → UI 이벤트(배치 emit)
    - 근거: `Assets/SpellTalker/Scripts/Manager/Battle/CardManager.cs`

### 4) 마나 획득
- ✅ 현재: 카드 사용 시 `BattleManager.GainMana(...)`로 마나가 반영되고, UI는 `BattleUIManager.UpdateManaUI` 경유로 갱신.
  - 근거: `Assets/SpellTalker/Scripts/Manager/Battle/CardManager.cs`
  - 근거: `Assets/SpellTalker/Scripts/Manager/Battle/BattleManager.cs`
  - 근거: `Assets/SpellTalker/Scripts/Manager/Battle/BattleUIManager.cs`

### 5) 룬 드로우 및 조합
- ✅ 현재: `RuneManager`가 `RuneDeckRuntime` 기반으로 손패 유지(최대 5), 배치(최대 3), 실패 시 버림 처리 루프 포함.
  - 근거: `Assets/SpellTalker/Scripts/Manager/Battle/RuneManager.cs`
  - 근거: `Assets/SpellTalker/Scripts/Runtime/RuneDeckRuntime.cs` (존재 전제: 코드상 사용 중)

### 6) 스펠 발동
- ✅ 현재: 배치 룬 키 조합으로 스펠 검색 → 마나 소모 → 캐스팅 → 결과 적용(피해/자해/실패)까지 구현.
  - 근거: `Assets/SpellTalker/Scripts/Manager/Battle/SpellManager.cs`
  - 비고: 현재 대상 선택은 기본 “살아있는 적 1체”에 고정.
    - 근거: `Assets/SpellTalker/Scripts/Manager/Battle/BattleManager.cs`

### 7) 전투 승패 판정
- ✅ 현재: 플레이어 사망/적 전멸 시 승패 판정 후 `EndBattle()` 호출.
  - 근거: `Assets/SpellTalker/Scripts/Manager/Battle/BattleManager.cs`

### 8) 전투 보상 획득
- ❌ 현재: Reward 선택/골드/카드 선택 등 “보상 시스템”이 구현/연결되어 있지 않음(승리 시 맵 복귀만).
  - 근거: `Assets/SpellTalker/Scripts/Manager/Battle/BattleManager.cs`
- TODO:
  - 최소 보상 구현(프로토타입):
    - 승리 시: 카드 1장 선택(또는 3택1) + 골드 획득
  - Reward UI는 입력/표시만 담당하고, 덱 추가/골드 증가 로직은 Manager/System에서 처리.

### 9) 휴식 / 상점 / 보스 노드 이동
- 🟡 현재: 맵에서 `EncounterType`은 존재하나, Combat 외 타입(Event/Shop/Rest)의 진입 처리/루프가 미구현.
  - 근거: `Assets/SpellTalker/Scripts/Manager/Common/MasterManager.cs`
  - 근거: `Assets/SpellTalker/Scripts/Manager/Map/MapManager.cs`
- TODO:
  - `HandleEncounter`에서 `Rest/Shop/Event`를 최소 구현으로 연결.
  - “보스 노드 클리어 → 던전 종료” 조건을 명시적으로 처리.

### 10) 던전 1회 완주
- ❌ 현재: 완주(런 종료) 상태/씬/요약 화면/리셋 루프 부재.
- TODO:
  - 최소 정의:
    - Boss 승리 시 “완주” 처리 → 메인/결과 화면 → 새 런 시작 가능

---

## 현재 가장 큰 리스크(정리 우선순위)
1) 카드 사용 플로우가 `HandUI → Player.PlayCard()`와 `CardManager`가 분리되어 있어 런타임 상태가 쉽게 어긋날 수 있음.
2) 마나 수급(카드 ↔ 전투 마나) 연결이 문서 요구조건의 핵심인데 현재 단일 경로로 보장되지 않음.
3) 승리 후 보상/맵 루프가 빠져서 “1회 완주”까지 연결이 끊김.

---

## 추천 작업 순서(다음 3개만 하면 프로토타입이 ‘루프’가 된다)
1) Card Use 단일화 + 마나 연결(카드 사용이 루프의 시작)
2) Victory → Reward 선택 → 덱/골드 반영
3) Shop/Rest 최소 구현 + Boss 완주 처리
