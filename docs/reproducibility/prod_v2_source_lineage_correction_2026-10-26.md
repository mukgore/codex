# prod_v2_pool 자료 계보 정정 — 2026-10-26

이 문서는 [로컬 자료 계보 후보](local_source_map_candidate_2026-10-26.md)와 [G4 pool 교차 확인](g4_human_attack_pool_overlap_2026-10-26.md)의 코호트 해석을 정정한다. 앞 문서들은 조사 당시 확인한 경로별 묶음을 별도 코호트처럼 표현했으나, 이후 내부 식별자를 숨긴 채 파일을 직접 대조해 동일 자료 복사본임을 확인했다.

## 수정된 확인 결과

- 현재 작업공간에서 `experimentInfo.version == prod_v2_pool`인 JSON 18건을 확인했다. 이들의 participant ID는 18개 모두 고유했다.
- 승인된 수신 자료 폴더의 `sessionLog` JSON 17건은 위 18건 중 17건과 각각 **바이트 단위로 동일**했다. SHA-256 비교는 로컬에서만 수행했고 다이제스트는 공개하지 않았다.
- 따라서 17건은 별도 코호트가 아니라 `prod_v2_pool` 18건의 복사본이다. 나머지 1건은 수신 자료 폴더에서 확인되지 않았다.
- 두 위치의 17개 대응쌍 외에 participant ID가 겹치는 기록은 없었다. A/B 10건은 별도 구조와 version을 가진 자료이며 `prod_v2_pool` 자료로 합치지 않는다.
- `prod_v2_pool` 18건의 keyframe 참조는 현재 pool manifest와 연결되지만, 이 매니페스트와 `version` 문자열만으로 과거 각 세션의 실제 실행 HTML/build/browser를 증명하지는 않는다.

## G4 공격 자료와의 재대조

저장된 G4 공격 결과의 8개 gesture label은 현재 pool manifest의 clip ID 8개와 직접 일치한다. `prod_v2_pool` 18세션의 keyframe 참조에서는 그중 7개만 관찰됐다. 나머지 1개는 이 인간 코호트에 기록이 없다. label별 인간 세션 수는 0, 1, 3, 4, 5, 6, 8, 9건이었다.

이는 기존 사용자 자료 안에서 같은 pool ID를 매개로 한 제한적 비교 가능성을 보여주지만, 공격 reference library가 source gestures를 포함하므로 held-out 검증은 아니다. 세션마다 challenge 구성도 같지 않고, challenge ID 일치만으로 동일 프레임 전환·방향·판정 환경 또는 paired trial을 입증할 수 없다. 저장된 공격 결과의 gate/score 정의와 인간 JSON의 `scores` 정의도 코드 수준에서 별도로 맞춰야 한다.

## 상태 및 다음 처리

- 이전 문서의 “별도 17-session 인간 코호트” 표현은 **철회**한다. 올바른 표현은 “prod_v2_pool 18건 중 17건의 byte-identical 사본”이다.
- A/B 10건은 계속 별도 코호트로 유지한다.
- 이 정정으로 독립 holdout이나 end-to-end 인증 증거가 생긴 것은 아니다.
- 다음으로 기존 코드에서 `prod_v2_pool` 인간의 `scores`와 G4 공격의 gate/score 계산 정의를 비교할 수 있다. 의미·분모가 일치하지 않으면 값들을 직접 대응시키지 않고 각 결과를 별도로 보고해야 한다.
