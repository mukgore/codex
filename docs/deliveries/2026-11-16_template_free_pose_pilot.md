# TF-02 원형 없는 자세 제안 실행 — 2026-11-16

## 실행 전 상태와 계약

전체 목표를 재개해 [원래 실행 순서](../research_goal_followups_2026-11-10.md)와 [통합 백로그](../remaining_work_master_2026-11-15.md)를 유지한다. 등록 촬영/선별 입력이 없는 단계는 대기로 두고 [TF-01 적용표](../tf01_constraint_application_2026-11-16.md)에 따라 [TF-02 사전등록v1](../tf02_pose_pilot_preregistration_2026-11-16.md)을 구현했다. 앞선 prod 좌표 진단과 원자료·완료 실행은 보존한다.

실제 구현은 [template_free_pose_pilot.py](../../analysis/runtime_benchmark/template_free_pose_pilot.py)다. A32/B32/U32의 논리적96자세, 실제70개 SDK forward를 계획한다. B는6PC 정상계수scale.5의 단일 정적 자세 제안이며 원형ID/고정시간곡선/보간을 입력으로 받지 않는다. U는 B의 실제출력을 공유한다. A는 기존 recipe의8개 사전선택 자세를 beta/root0으로 비교한다.

실행 전18개 검사(신규4·기존 모델 prior8·해부학축6)가 통과했다. 기존 CPU17pin·Torch1thread를 사용한다. 양손 각각 neutral과2개 PCA/native 대조에서 full_pose/관절/mesh가1e-6이내인지 검사하고 그 손의 본시도로 넘어간다. 이 공학허용치는 임상한계가 아니다. 해부학축 왕복도1e-6을 확인한다.

저자 코드 defaults의 strict초과와1e-6rad zero-mask후 벌점, 샘플표면교차·퇴화, 정적BMC feature계산을 별도로 남긴다. 정적자세에는 가짜시각/속도0을 붙이지 않고 시간규칙N/A, 여섯 생체한계는 미확정으로 유지한다. 모델/표면 지표0도 연구격리이며 사람/물리/완성 동작이나 풀채택 통과가 아니다.

사전명세/코드·사용범위·모델/기저·고정저자원문·SDK/worker/환경을 새 config와 전체worktree snapshot에 연결한다. 새 private출력 `tfp_20261116_v1`, 실행기록 `template_free_pose_record_20261116_v1`만 사용한다. 예산600초와 모든제안/거부·오류·실제시각/wall/자체CPU·원래SDK출력을 보존한다. 실행 중 편집/커밋은 하지 않는다. 결과에 따라 같은 실행 안의 분포/관문을 바꾸지 않는다.

## 거부 실행과 현재 명세의 분리

위 최초 구현 실행은 SDK70개/종료0까지 수행했으나, 실행 중 다른 작성자가 작업트리와 사전등록을 변경해 `POSTFLIGHT_REJECTED`가 됐다. 출력334개와 전체 실패 기록을 보존하며 성공 실험으로 세지 않는다. 당시 제안 entropy는 현재 확정 명세와도 다르므로 성공 실행의 재현 결과로 합산하지 않는다. `template_free_pose_concurrent_drift_audit_20261116_v1.private.json`에 변경된 명세와 작업트리 차이를 연결했다.

현재 사전등록은 entropy `[seed,hand_index,attempt,62026]`와 모든 표현 대조를 본시도 전에 수행하는 구현을 명시한다. [현재 생산자](../../analysis/runtime_benchmark/mano_template_free_pose_pilot.py), [제안/검사](../../analysis/runtime_benchmark/template_free_pose.py)를 읽고4개 신규 검사를 통과한 뒤 별도 ID `TF02-STATIC-POSE-ENTROPY62026-20261116-V1`로 실제 실행했다. 최초 구현 파일과 실패 기록을 삭제/덮어쓰기하지 않았다.

## 검산된 실제 결과

현재 실행은70개 SDK forward,64개 고유 실험 제안(A32/B32), 논리적96행(U는 B공유)을 완료했다. `EXITED_ZERO`, 전체 worktree/입력/17pin 환경 전후 일치,329개 산출물 `RECORDED_FILES_MATCH`, journal `COMPLETED70/70`이다. 입력은 설정 포함309개다. 비공개 출력/기록/설정은 각각 `tf02_entropy62026_20261116_v1`, `tf02_entropy62026_record_20261116_v1`, `tf02_entropy62026_config_20261116_v1.json`이다.

| 조건 | 제안 | 모델 prior 벌점0 | 샘플 표면 지표0 | 두 조건 모두 만족 |
|---|---:|---:|---:|---:|
| A, 기존 원형의 선택 정적 자세 |32 |32 |32 |32 |
| B, 원형 없는6PC 제안 |32 |0 |32 |0 |
| U, B의 공유 무관문 대조 |32 |0 |32 |0 |

양손 PCA/native 표현 대조의 full_pose 최대절대차는 각각2.98e-8, 정점은1.49e-8/7.45e-9였다. 등록한1e-6 이내다. 핵심 준비/제안/SDK/QA/저장 wall12.094초, 자체CPU11.703초이며 외부 실행기의 snapshot/receipt 봉인은 제외한다. [공개 집계](../../reports/template_free_pose_pilot_20261116_entropy62026.json)에 손별/조건별 수치와 자세별 시간 요약을 남겼다.

B는 원형/시간 파형 없이 실제 모델 자세32개를 제안했지만 현재 모델 prior 후보0개였다. 이 결과를 성공한 자연 동작 생성으로 부르거나 분포/기준을 사후 조정하지 않는다. 모든 결과는 연구 격리, BMC 여섯 한계 미확정, 움직임/영상/사람/독립family/풀 채택0이다. 원형 없는 **움직임** TF-03은 아직 수행하지 않았다.

다음 제안은 [별도 고정 모델 제약 투영 사전등록](../tf02_projected_pose_preregistration_2026-11-16.md)이다. 무수정 B 실패를 보존한 채 수정 전후·허용 구간/수치 출처·왜곡/중복·실제 SDK/표면 결과를 비교한다. 이는 새 실행 조건이며 기존 실험을 통과로 바꾸는 보정이 아니다.
