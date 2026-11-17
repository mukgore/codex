# 실행시간 검증 보고서 색인

기존 집계의 위치를 보존하면서 runtime R0–R9 연결을 모은다. 개별 행/파일 수를 전체 완료율로 사용하지 않는다. 원자료·모델/좌표·세부 로그·원clock/receipt는 비공개다.

| 근거 | 공개 집계/방법 | 현재 범위 |
|---|---|---|
| 실제 MediaPipe 오프라인48영상 | [JSON](../mediapipe_matched_20261117.json), [영상별48시간행](../mediapipe_matched_timings_20261117.csv), [방법](../../docs/deliveries/2026-11-17_mediapipe_matched_video.md) | 1,200저장 입력/769검출. browser parity·cold/warm·실시간 인증은 미검증 |
| R4 단계 hook 준비 | [JSON](../r4_stage_profile_fixture_20261117.json), [방법](../../docs/deliveries/2026-11-17_stage_profile_fixture.md) | 합성5경로. 실제 새 모델 단계 시간을 측정한 값 아님 |
| R7 도착 queue/process 준비 | [JSON](../r7_process_replay_20261117.json), [방법](../../docs/deliveries/2026-11-17_process_replay_fixture.md) | 합성7경로. 실제 모델의 온라인 응답/관문은 미완료 |
| R8 known-source localhost | [JSON](../r8_local_timing_20261117.json), [요청11행](../r8_local_requests_20261117.csv), [방법](../../docs/deliveries/2026-11-17_local_http_timing.md) | reference/정지/schema3사례. 실제 UI first pixel/카메라/과거·운영 인증은 미검증 |
| R9 별도 process 재구성 | [JSON](../r9_reconstruction_20261117.json), [방법](../../docs/deliveries/2026-11-17_runtime_reconstruction.md) | 원출력812·공개 JSON4/CSV59행 일치. 새 실측/독립 구현/제3자 검증 아님 |

[전체 runtime 완료 기준](../../docs/runtime_validation_todo_2026-11-04.md)과 [62ID/3D44표행/R0–R9 통합표](../../docs/remaining_work_master_2026-11-15.md)를 유지한다. R0 실제 자산·R1 기록기/GPU/보존·R2 새 고정 입력·R3 실제 파일럿/별도 보관·R4 HaMeR/새 모델 계측·R5 조건별 반복·R6 같은 정보의 실제 공격·R7 실제 인과적 응답·R8 UI/신뢰 입력/전체 흐름·R9 독립 실제 세션은 각 선행 조건과 미완료를 별도로 추적한다. Cloud/Colab/GPU 이전은 보류다.
