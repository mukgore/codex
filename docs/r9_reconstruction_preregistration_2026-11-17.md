# R9 별도 프로세스의 읽기 전용 재구성 — 사전등록 v1

R9의 원로그 재계산/집계 부분을 검산한다. 완료한 모델/SDK/영상/HTTP 문제 실행을 다시 시작하지 않는다. **새 measurement session, 독립 구현/연구자/제3자 검증은 아니다.** 같은 버전의 공개 exporter와 일부 순수 수학 함수를 별도 Python process에서 재실행해, 저장 입력/출력과 집계가 일관되는지 확인한다. R9의 전체 재현/실제 모델 조건 비교는 계속 미완료다.

[부모 실행기](../analysis/runtime_benchmark/reconstruction_audit.py) · [자식 재구성기](../analysis/runtime_benchmark/reconstruction_worker.py) · [검사](../tests/test_reconstruction_audit.py).

## 고정4작업과 원본

| 작업 | 기존 private output/record | 재구성 |
|---|---|---|
| mediapipe | `mp4p_20261117_v1` / `mediapipe_tf04_record_20261117_v1` | 저장48×25예측/reference의 오차·분모,96저장 점수의 집계, journal/bundle, 공개 JSON/48행CSV |
| stage_profile | `r4_stage_profile_fixture_20261117_v1` / `r4_stage_profile_fixture_record_20261117_v1` | 합성5경로의 raw→summary, 공개 JSON |
| process_replay | `r7_process_replay_20261117_v1` / `r7_process_replay_record_20261117_v1` | 합성7경로의 raw queue→summary, 공개 JSON |
| local_http | `r8_local_timing_20261117_v1` / `r8_local_timing_record_20261117_v1` | 3사례·11요청의 client/server raw→joined→case/요청 집계, 공개 JSON/11행CSV |

경로는 연구 repo 기준 `../private_artifacts/` 아래다. MediaPipe reference는 기존 `tf4d_20261116_v1` / `tf04_display_record_20261116_v1`에 결합한다. 네 실행451출력과 reference display361출력, 총812원출력의 bytes·크기·hash를 기존 receipt로 확인한다. 현재 worktree를 과거 snapshot과 일치한다고 주장하지 않는다.

MediaPipe의 저장 예측을 기존 generated-model projection reference와 비교해 순수 수학 metric을 다시 계산한다. 같은 metric 함수를 재사용하며 독립 해부학/수치 구현 검증으로 부르지 않는다. count/null/bool/identity는 정확히 일치해야 한다. 재계산한 float metric에만 abs/rel1e-12를 허용한다. 저장된96 score를 새 JS로 다시 채점하지 않고 각 영상의 원score와 전역 row/집계를 대조한다. 원점수 자체의 정확도/인증 타당성을 독립 입증하지 않는다.

## 비교·오류·보존

네 작업을 각각 새로운 Python process로 시작한다. parent/worker PID와 명령/실제 종료·stdout/stderr·경과시간은 private에 기록한다. 실제 모델·Node scoring·HTTP server/worker replay·영상 decoder/renderer는 시작하지 않는다. 과거 성능/latency를 새 값으로 덮어쓰지 않는다.

새 private 재구성 파일을 기존 공개 JSON/CSV와 대조한다. JSON은 정규화한 값/타입/목록 순서가 같아야 하며 key/whitespace 형식 차이는 무관하다. CSV는 header와 각 cell/row가 같아야 하며 newline encoding만 무관하다. 누락/null을0으로 바꾸거나 실패/미확정 사례를 제거하지 않는다. 원본/기존 공개 보고서에는 쓰지 않는다.

각 worker60초, 전체300초 budget이다. worker 오류/timeout은 보존하고 다음 작업을 계속 확인한다. 하나라도 실패하면 parent가 partial summary를 저장하고 nonzero로 종료한다. 같은 root를 덮어쓰거나 실패 작업을 자동 반복하지 않는다. 모든 원본 root와 새 output의 ancestor overlap을 거부한다.

성공 시 예상24출력: 재생성 JSON4/CSV2/worker result4, 작업별 stdout/stderr8/process result4, 전체 plan/summary2다. 새 계획·공개 기대파일6개·원본812파일·다섯 execution record의 파일·Python/사전등록을 입력 snapshot에 포함한다. 기존 연구6pin만 사용한다. 별도 config/record/output에 새 명령/UTC/wall/자체CPU·producer/worktree·코드/입력/환경 snapshot·postflight·파일 hash를 남긴다. 기록 실행 중 편집/commit 금지다.

**실행 전 입력 표현 보완:** 지정 원본/기록 파일857개 중60개는 정상적인 빈 stdout/stderr log다(원출력55/기록5). 공통 snapshot의 빈 placeholder 입력 거부는 바꾸지 않는다. 비어 있지 않은797파일은 직접 snapshot하고, 빈60파일은 새 plan에 path/0bytes/empty SHA256을 명시해 parent 시작/종료 때 존재·0bytes를 검사하며 기존 receipt의 bytes/hash 검산에도 포함한다. 공개 기대6파일·새 plan/Python/사전등록과 config를 합친 snapshot 입력은807개가 예상된다. 이는 빈 log를 누락/삭제하거나0초 성능값으로 바꾸는 처리가 아니다. 아직 새 기록 명령은 실행하지 않았다.

원log/좌표/모델 예측·개별 hash·절대 clock/경로/PID·receipt는 영구 비공개다. 공개에는 네 종류의 재구성 상태/사례·분모/JSON/CSV 일치와 실제 모델0/새 measurement0만 낸다. 새 모델/카메라·실제 운영/독립 평가·R9 전체 완료를 주장하지 않는다. 전체62ID·3D44표행·R0–R9/실제 입력 우선·root prod/원자료 불변·비공개/Cloud보류를 유지한다.
