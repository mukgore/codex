# G4 공격 결과와 인간 sessionLog의 ID 교차 확인 — 2026-10-26

이 보충은 [로컬 자료 계보 후보](local_source_map_candidate_2026-10-26.md)의 추가 비교다. 실제 동작 ID, 개인 ID, 영상명, 원자료, 입력 해시는 공개하지 않는다.

## 확인 결과

- 보존된 G4 공격 원시 결과에는 8개의 고유 gesture label이 있다.
- 이 8개 label은 현재 pool manifest의 clip ID 8개와 모두 직접 일치한다.
- 별도 17-session 인간 `sessionLog` cohort는 그 공격 label 중 7개를 keyframe/segment 참조로 포함한다. 1개 공격 label은 이 인간 cohort에 대응 레코드가 없다.
- 인간 cohort에서 label별 세션 수는 0~8개로 달랐다. 같은 challenge ID가 모든 세션에 동일하게 제시된 완전 대응 설계라고 볼 수는 없다.
- 기존 G4 reference library의 gesture 이름과 sessionLog action 이름은 직접 일치하지 않았다. 현재 연결은 pool manifest의 clip ID를 매개로 한 간접 연결이다.

## 판정

**조건부로 확인됨:** 공격 결과와 인간 sessionLog가 일부 같은 pool clip ID를 참조하므로, 이 ID 집합에서 탐색적 same-pool 비교를 설계할 연결 단서가 있다.

**미확인:** 실제 수집 당시 pool/build revision, 화면·방향·전환의 동일성, 개별 공격 시도와 사람 세션의 paired 대응, 공격 결과와 인간 기록의 동일 scoring/gate semantics.

**독립 평가로 사용 불가:** 공격 reference library에 해당 source gestures가 이미 포함되어 있으므로, 이 교차 집합은 held-out 일반화 검증이 아니다. 공격 label 하나는 인간 기록이 없고, 모든 label의 인간 세션 수도 같지 않다. 이 집계만으로 통계적 공격 성공률 또는 전체 인증 성공을 계산하지 않았다.

## 적절한 다음 분석

기존 결과를 덮어쓰지 않고, 별도 기술 분석으로 7개 겹치는 clip ID에 한정해 다음을 확인할 수 있다.

1. sessionLog의 저장 raw/estimated/final 점수가 동일 pool clip에 대해 계산됐는지 코드·스키마로 대조한다.
2. G4 공격의 gate·score 결과가 같은 분모와 의미인지 확인한다. 이름이 비슷하다는 이유로 score를 합치지 않는다.
3. challenge 조건이 다르거나 저장된 endpoint가 없으면 각각 descriptive result로 남기고, end-to-end 인증으로 해석하지 않는다.

독립 held-out G4 주장을 위해서는 기존 attack reference와 source family가 겹치지 않는 새 evaluation source가 별도로 필요하다.
