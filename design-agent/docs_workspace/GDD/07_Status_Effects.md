# Status Effects

## 1. 목적

이 문서는 `07_Status_Effects.md`에 해당하는 `Status Effects` 영역을 정리한다. 기존 문서에서 확인된 기준: 카드가 현재 전투 중 다시 사용할 수 없도록 완전히 제거되는 상태.

## 2. 현재 확정된 내용

- 카드가 현재 전투 중 다시 사용할 수 없도록 완전히 제거되는 상태.
- Buff
- 대상에게 유리한 상태 효과.
- Debuff
- 대상에게 불리한 상태 효과.
- Injury
- 누적된 손상 상태.
- 상태 효과는 중첩 가능하다.
- 각 상태 효과는 개별 규칙을 가진다.
- 상태 효과끼리 상호작용할 수 있다.
- Injury System
- Injury는 일반 HP와 별도로 추적되는 누적 손상 상태다.
- 일부 스킬이나 효과는 Injury를 참조하거나 소비할 수 있다.
- Buff / Debuff Design Rules
- 상태 효과는 짧고 명확한 역할을 가져야 한다.
- 중첩이 가능하더라도 무한 제어 상태를 만들면 안 된다.
- Injury Design Rules
- Injury는 보조 리스크/리소스여야 한다.
- Injury 중심 빌드가 가능하더라도 필수 메타가 되면 안 된다.
- 턴 종료 시 발동하는 버프/디버프가 있다면 턴 종료 단계에서 처리한다.
- 제한 시간이 있는 상태 효과는 턴 종료 시 지속 시간을 감소시키고 0이 되면 종료한다.
- 전투 시작 시 최대 체력은 누적 부상만큼 감소한 값으로 시작할 수 있다.

## 용어

- Buff: Buff
- Debuff: Debuff
- Injury: Injury


## 3. 핵심 규칙

- 각 상태 효과는 개별 규칙을 가진다.
- Buff / Debuff Design Rules
- Injury Design Rules
- 상태 효과 지속 시간 감소와 종료 판정은 상태 효과 시스템에서 관리한다.

## 4. 플레이 흐름

- 턴 종료 시 버프/디버프 효과 적용 -> 지속 시간 감소 -> 만료 상태 제거 순서로 처리한다.

## 5. 데이터 구조

| 항목 | 설명 | 비고 |
|---|---|---|
| Buff | Buff | 기존 용어 문서 기준 |
| Debuff | Debuff | 기존 용어 문서 기준 |
| Injury | Injury | 기존 용어 문서 기준 |
| Duration | 상태 효과의 남은 지속 시간 | 원문 초안 분리 |

## 6. 예시

- TODO: 기존 문서에서 예시를 확인해야 한다.

## 7. 현재 구현 상태

- TODO: 07_Package_Rebuild_Checklist.md에서 현재 구현 상태를 확인해야 한다.

## 8. TODO

- [ ] 07_Status_Effects.md의 부족한 세부 기획을 기존 문서 기준으로 보강한다.

## Change Log

### 2026-07-15
- 05_Rune_System.md에 섞여 있던 버프/디버프 턴 종료 처리와 부상 규칙을 Status Effects로 분리
