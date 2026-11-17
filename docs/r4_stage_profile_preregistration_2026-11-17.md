# R4 단계별 계측 준비와 합성 경로 검산 — 사전등록 v1

기존 완료 MediaPipe48영상의 기록에는 import/resource와 batch 추출 시간은 있지만 프레임별 decode/RGB/Hands 호출 시간이 없다. 그 시간을 소급하지 않고 완료 추론도 반복하지 않는다. 다음 **새 입력/별도 사전등록 실행**부터 쓸 선택적 계측과 오류·정리 의미를 먼저 검산한다. 실제 MediaPipe/HaMeR 성능·R4 전체 완료를 주장하는 실험이 아니다.

## 선택적 계측의 범위

[기존 worker](../analysis/runtime_benchmark/mediapipe_video_worker.py)에 `--stage-profile-output NEW_PRIVATE_DIRECTORY`를 추가한다. 기본값은 계측 없음이고 기존 request/confidence/model profile을 바꾸지 않는다. 디렉터리는 새 predictions와 같은 parent 안의 새 경로여야 한다. 실제 자산/코드/입력은 종전 preflight와 새 실행 snapshot을 통과해야 한다.

[stage_profile](../analysis/runtime_benchmark/stage_profile.py)은 지정 stage1 module의 cv2/mp 이름만 임시 proxy로 바꾸며 원래 `_extract_landmarks_native`의 본문을 실행한다. 실제 cv2/MediaPipe module 자체를 수정하지 않고 중첩/동시 사용은 거부한다. 정상·예외·KeyboardInterrupt에서 참조를 복원한다. decoder open/read/release, RGB 변환, Hands 생성/process/close를 같은 worker의 perf_counter_ns/process_time_ns로 계측한다. 추가 모델 호출·read·전처리나 파라미터 변경은 없다.

호출 의도를 JSONL에 flush/fsync한 뒤 operation 시작 시각을 잡고, 반환/예외 직후 종료 시각을 잡는다. operation 시간은 trace write를 제외한다. 그 밖의 gap은 실제 Python/metadata/loop/PTS/결과 변환과 trace I/O를 함께 포함한다. `result_conversion_loop_and_trace_io`를 순수 좌표 변환 시간으로 바꾸지 않는다. 전체 측정 window는 gap+call의 배타적 합과 일치해야 한다. 마지막 summary 기록/namespace 복원은 window 밖이다. CPU는 자기 process이며 native thread 합 때문에 wall보다 클 수 있다. GPU 완료·native graph 내부 palm/landmark별 forward·온라인 응답은 측정하지 않는다.

원trace에서 complete summary를 재생성한다. 끝나지 않은 call intent는 outcome/duration 미확정이며0으로 채우지 않는다. truncated/lost trace는 complete summary가 될 수 없다. phase/outcome/중복·종료 뒤 event·시간 경계 불일치를 거부한다. 이 JSONL은 독립 서명/인증이 아니며 실행 receipt가 실제 파일 bytes를 별도로 연결한다.

## 고정 검산 5경로

owned stage1 source에서 native function 정의 하나만 AST로 불러오고 실제 모듈 import 대신 **합성 decoder/Hands**를 제공한다. 실제 모델/영상/카메라/가중치를 실행하지 않는다. 각 case를 baseline과 profiled 함수로 비교한다.

1. 정상: 합성2프레임(검출1/미검출1), decoder read3회(EOF포함)/process2회.
2. 두 번째 process 오류: 원래 예외·release/close·부분 분모 유지.
3. open 실패: 원래 FileNotFoundError·모델 미생성/원래 정리 동작 유지.
4. RGB 변환 오류: graph process 전에 중단하고 원래 정리 동작 유지.
5. close 오류: 프레임 처리 완료와 전체 함수 성공을 구분.

5경로 모두 함수 결과/예외 class·read/process/release/close state·namespace 복원과 raw JSONL→summary 동일성을 확인한다. 실제 monotonic clock은 합성 interface를 잰 것이며 이 값은 MediaPipe/HaMeR 처리시간이 아니다. 기록11출력(5trace+5summary+전체summary), 전체120초·새 immutable output/record/config·전체 worktree/source/environment·명령/시각/stdout/stderr/종료/hash를 남긴다. 실행 중 편집/commit 금지다.

새8검사+기존MediaPipe4검사, 총12통과다. trace I/O 제외·배타적 wall/CPU 합·원함수 결과/오류/정리·EOF분모·중첩/잘못된namespace·중단/부분로그·CPU>wall·clock역행·KeyboardInterrupt를 다룬다. 이는 실제 모델 계측 검증이 아니다.

## 남은 원래 요구

R4 HaMeR는 마지막 지정 preflight에서 core3자산이 없었다. 이번에 자산을 내려받거나 환경을 설치하지 않는다. 실제 모델의 cold/warm·GPU 완료·검출/전처리/추론/변환/채점/저장 전체 연결은 해당 자산과 새로운 입력/실행이 필요하다. MediaPipe의 새 profile도 실제 모델 호출 전까지 준비 상태다. 기존 batch 시간을 세부 시간으로 나누어 채우지 않는다. full62ID·3D44표행·R0–R9/원래 우선순위·prod/영구 비공개/기존 실행/원자료/Cloud보류를 유지한다.
