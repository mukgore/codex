# R4 단계 계측 준비와 합성 경로 검산 — 2026-11-17

앞 단계4의 실행시간 공백을 다시 대조하고, 다음 입력부터 쓸 선택적 stage 계측을 추가했다. **실제 모델을 새로 실행하거나 완료한 추론을 반복하지 않았다.** 기존 MediaPipe48영상의 import/resource·batch 시간은 보존하며, 과거의 프레임별 decode/RGB/graph 시간을 소급하지 않는다.

[사전등록](../r4_stage_profile_preregistration_2026-11-17.md) · [계측 코드](../../analysis/runtime_benchmark/stage_profile.py) · [합성 실행](../../analysis/runtime_benchmark/stage_profile_fixture.py) · [worker 연결](../../analysis/runtime_benchmark/mediapipe_video_worker.py) · [검사](../../tests/test_stage_profile.py) · [비성능 집계](../../reports/r4_stage_profile_fixture_20261117.json).

## 추가한 동작

worker의 선택적 `--stage-profile-output NEW_PRIVATE_DIRECTORY`는 다음 새 predictions와 같은 parent의 새 디렉터리에 원event/summary를 저장한다. 기본값은 계측 없음이다. source extractor의 본문·confidence/model profile을 교체하지 않고, 지정 module의 cv2/mp 이름만 한 worker에서 임시로 감싼다. 실제 패키지 module 자체는 변경하지 않으며 종료/예외/중단 때 참조를 복원한다. nested/concurrent 사용은 거부한다.

decoder open/read/release·RGB 변환·Hands setup/process/close의 실제 operation 시작/종료와 wall/자체CPU를 기록한다. operation 시간은 intent/finish 기록 I/O를 제외한다. 나머지 gap에는 Python loop/metadata/PTS/결과 변환·trace fsync가 함께 포함된다. 이 gap을 순수 좌표 변환 시간으로 부르지 않는다. 단계와 gap의 배타적 합이 전체 profile window와 일치하고, raw JSONL에서 같은 집계가 재생성돼야 한다.

시작 의도만 남은 call은 실행/완료 여부와 기간 미확정이며0으로 채우지 않는다. 유실/부분 마지막 줄·미완료·phase/outcome 불일치·종료 뒤 event·시간 경계 불일치를 구분/거부한다. 이 trace는 독립 인증이 아니며 명령 실행 receipt가 최종 파일 bytes를 별도로 묶는다.

## 실제로 실행한 검산의 범위

owned stage1의 native function 정의를 AST로 불러오고 **합성 decoder/Hands**를 연결했다. baseline/profiled 함수의 반환값·예외 class·상태·정리·참조 복원을 비교했다. Python monotonic clock은 이 합성 interface를 잰 것이며 실제 MediaPipe/HaMeR 성능값이 아니다. 혼동을 피하려고 공개 집계에는 fixture 시간을 내보내지 않았다.

| 합성 경로 | 원함수/계측 의미 일치 | raw 복구 상태 | 특징 |
|---|---|---|---|
| 정상2프레임 | 일치 | COMPLETED | read3회(EOF포함), process2회, release/close각1 |
| process 오류 | 일치 | ERROR | 두 번째 process 오류·부분 분모와 정리 유지 |
| open 실패 | 일치 | ERROR | FileNotFoundError, graph 미생성·원래 정리 동작 유지 |
| RGB 오류 | 일치 | ERROR | decoded1/process0과 정리 유지 |
| close 오류 | 일치 | ERROR | frame 처리가 끝나도 전체 함수 성공이 아님 |

5/5 경로에서 원trace→summary가 동일했다. 모델 kernel·검출 품질·새 source family·사람/공격/인증 성공을 측정한 것이 아니다.

## 검사와 실행 기록

새10검사는 I/O를 제외한 call 시간·배타적 wall/CPU·원함수 결과/예외/cleanup·EOF 분모·namespace 복원/중첩 거부·incomplete/truncated/변조 상태·CPU>wall·clock regression·KeyboardInterrupt를 검사했다. 기존 MediaPipe 지표/resource4검사와 합해14검사 통과다. CLI 선택옵션 전달/기본값과 기존·다른 parent의 profile 경로를 runtime import 전에 거부하는 검사도 포함한다. GPU 완료/실제 decoder 및 graph timing parity는 미검증이다.

생산 commit `1a9e7ba`, private output `../private_artifacts/r4_stage_profile_fixture_20261117_v1`, record `r4_stage_profile_fixture_record_20261117_v1`, config `r4_stage_profile_fixture_config_20261117_v1.json`이다.4입력(설정 포함)·기존 연구6pin환경, `EXITED_ZERO`·사후snapshot 일치·11출력의 `RECORDED_FILES_MATCH`를 확인했다. 모든 raw trace·상세 clock/record/hash는 영구 비공개로 보존했다. source/old prediction/원영상·prod UI는 변경하지 않았다.

## 남은 일과 전체 목표

R4의 설치된 MediaPipe 경로에 새 계측을 연결할 준비와 V00/R1/R9의 일부 기록 검산을 보완했다. **HaMeR 자산/허용 runtime·실제 cold/warm·GPU 완료·같은 입력 품질/성능·streaming·서버/보호 동작·독립 재실행은 미완료**다. 이전 HaMeR core3개 미확보 preflight를 실제 계측 완료로 바꾸지 않는다. 실제 자산/새 입력이 확보되면 별도 사전등록·fresh execution record로 실행한다. 완료한48영상 추론의 누락 시간을 채우려고 다시 실행하지 않았다.

3D 조건부 경계의4미확정leaf/미검증 backend 가정과 연속 narrow phase도 그대로 남는다. 전체62개 ID·3D44표행·R0–R9, 실제 촬영/선별/대응·독립평가/운영 입력 우선과 비공개/Cloud보류/격리를 유지한다. 이 세션에서 마지막으로 push/원격 일치를 확인한 commit은 `68417fc`이며 새 변경은 로컬에 보존한다.

기본 연구 환경의 전체 검사는 `Ran 340, OK (skipped=1)`이었다. mpmath가 없는 기본 환경에서 SDK box 모듈을 명시적으로 제외하며, 기존 SDK 환경의 box/temporal16검사는 모두 통과했다. sibling source가 없는 CI에서는 원함수 AST parity4검사만 별도 이유로 건너뛰고 독립 clock/log 검사는 유지한다. 현재 로컬에는 sibling source가 있어 해당4검사도 실행했다. CI에 새 runtime/모델/원자료를 자동 설치·복제하지 않는다.
