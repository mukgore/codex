# G03 — 미확정4구간의 제한 이분할 결과

등록된 새 촬영21행의 원본 경로0·선별 관측0·HaMeR3개/Text2HOI10개 지정 핵심 항목 미확보를 재확인한 뒤, 실제 입력 없이 가능한 조건부 경계 후속을 진행했다. [사전등록](../sdk_residual_bisection_preregistration_2026-11-17.md)에 따라 기존 v2의 미확정4구간만 더 작은 전체 시간구간으로 계산했다. 완료한764유한leaf·SDK forward·원영상 생성은 재실행하지 않았다.

[이분할](../../analysis/runtime_benchmark/bounded_interval_refinement.py) · [실행기](../../analysis/runtime_benchmark/sdk_residual_bisection.py) · [저장 결과 검산/집계](../../analysis/export_sdk_residual_bisection.py) · [검사](../../tests/test_bounded_interval_refinement.py) · [공개 집계](../../reports/tf03_sdk_residual_20261117.json).

## 실제 결과

| 잔여 parent | 구간 평가 시도 | terminal | 유한 조건부 terminal | 미확정 terminal | 부모 전체 후보 |
|---|---:|---:|---:|---:|---|
| right seed7 | 13 | 7 | 6 | 1 | 미완료 |
| right seed19, 첫 잔여 | 13 | 7 | 7 | 0 | 조건부 완성 |
| right seed19, 둘째 잔여 | 13 | 7 | 6 | 1 | 미완료 |
| left seed19 | 3 | 2 | 2 | 0 | 조건부 완성 |
| 합계 | 42 | 23 | 21 | 2 | 2/4 parent 조건부 완성 |

시도42개에는 나중에 분할된 부모의 평가도 들어 있다. 최종23terminal의 폭은 서로 다르므로 기존 동일폭768leaf와 단순 성공률 비교를 하지 않는다. 2개 미확정 terminal은 정한 최대 깊이6에서 같은 `SDK_SHIFTED_NORM_INCLUDES_ZERO` 사유로 남았다. 성공할 때까지 더 분할하거나 오차 pad를 바꾸지 않았다.

완성한 부모2개의 유한 remainder 최댓값은 각각 약0.0487187/0.000499826 native 단위다. 미완료 부모의 유한 조각 최댓값은 부모 전체 경계로 사용할 수 없다. mm·물리적 충돌 여유로 읽지 않는다. 기존 좌표를 새 시점에서 SDK로 계산하거나 새 관측을 추가하지 않았으며, 이번에는 샘플 포함 검사를 하지 않았다.

## 실행 기록과 검산

- 실행 생산 커밋: `17ae890`. 새 output `../private_artifacts/tf03_sdk_residual_20261117_v2`, record `tf03_sdk_residual_record_20261117_v2`, config `tf03_sdk_residual_config_20261117_v2.json`.
- `EXITED_ZERO`, 사후 전체 worktree/input/environment 일치와11출력의 `RECORDED_FILES_MATCH`를 확인했다. snapshot928입력(설정 포함)·17pin. 정상0바이트 과거 로그1개는 직접 snapshot 대신 원래 receipt 검산에 연결했다.
- core wall10.6985초·자체CPU10.34375초. 기존 receipt의 최초 검증은 제외하고, 입력 준비·평가·기록/저장·최종 원본 재검증은 포함한다. 로컬 CPU 계산 경과시간이며 모델 추론 속도·인증 지연이 아니다.
- source와 prior 성공 receipt를 전후 검산했다. 각 부모의 이분 트리·최대깊이·빈틈 없는 terminal 분할·bound 배열의 shape/순서/유한성·42평가의84개 start/finish 원log와 공개 분모를 별도 exporter에서 대조했다.
- 새7검사는 분할 없는 유한 부모·전체 시간구간 분할·깊이 예산·다른 미확정 사유·예기치 않은 오류·인접 float·잘못된 입력을 다룬다. 기존 SDK box10검사도 통과했다. 과거 전체384검사와 이번17검사의 실행 범위는 구분한다.

최초v1은 snapshot 준비 중0바이트 로그를 직접 입력으로 등록해 거부됐다. 계산 subprocess는 시작되지 않았다. v1 설정과 부분 기록 폴더를 보존했고 결과/생성시간을 만들지 않았다. v2에서 이 기록 연결만 정정했으며 조건/깊이/예산/수식은 유지했다.

## 의미와 다음 조건

이번 결과는 4개 큰 미확정 구간 중2개에 대해 더 작은 **조건부** 경계가 연결됐다는 뜻이다. backend 수치 오차 가정1e-12/1e-14/1e-6은 여전히 검증되지 않았다. 실제 경로 특이점 발생을 관측한 것도, 남은2조각의 충돌을 검출한 것도 아니다.

`backend_error_bounds_validated=false`, `continuous_collision_free_proven=false`, `CCD_clearance=false`, `release_allowed=false`, 풀 채택0을 유지한다. 남은2조각의 상관/0분모 배제, 실제 backend 오차 보증, 시간 전체 vertex–face/edge–edge 및 공유 simplex 검사는 계속 필요하다. 생체/물리/사람·운영 검증도 별도다.

앞 단계 실제 촬영/선별/3A/3B/독립평가 입력 우선, 전체62ID·3D44표행·GEN3D-05·R0–R9와 원본/비공개/Cloud보류를 유지한다. 대시보드는 사용자 지시대로 수정/재생성하지 않았고 고정된 연구 snapshot을 그대로 둔다. 새 결과는 로컬에만 보존하며 추가 push는 하지 않았다.
