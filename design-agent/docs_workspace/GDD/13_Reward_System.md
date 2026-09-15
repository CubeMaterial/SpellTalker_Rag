# Reward System

## 1. 목적

이 문서는 `13_Reward_System.md`에 해당하는 `Reward System` 영역을 정리한다. 기존 문서에서 확인된 기준: Reward

## 2. 현재 확정된 내용

- Reward
- 카드 보상 선택
- 추가 보상 처리 가능
- 전투 보상 획득
- Milestone 5 - Reward / Map Loop
- 전투 후 보상 선택 가능
- [ ] RewardSystem
- 전투 승리 후 적 종류를 기록하고 보상 흐름으로 넘긴다.
- 적 종류에 따라 골드와 카드 보상을 지급한다.


## 3. 핵심 규칙

- 보상은 전투 승리 이후 처리한다.
- 적 종류는 보상 산정에 영향을 줄 수 있다.

## 4. 플레이 흐름

- Milestone 5 - Reward / Map Loop
- 전투 승리 -> 적 종류 확인 -> 골드/카드 보상 지급 -> 맵 복귀 순서로 처리한다.

## 5. 데이터 구조

| 항목 | 설명 | 비고 |
|---|---|---|
| RewardTable | 적 종류별 골드/카드 보상 규칙 | 원문 초안 분리 |

## 6. 예시

- TODO: 기존 문서에서 예시를 확인해야 한다.

## 7. 현재 구현 상태

- TODO: 07_Package_Rebuild_Checklist.md에서 현재 구현 상태를 확인해야 한다.

## 8. TODO

- [ ] 13_Reward_System.md의 부족한 세부 기획을 기존 문서 기준으로 보강한다.

## Change Log

### 2026-07-15
- 05_Rune_System.md에 섞여 있던 전투 보상, 골드, 카드 보상 내용을 Reward System으로 분리
