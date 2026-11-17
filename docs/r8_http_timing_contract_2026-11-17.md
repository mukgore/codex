# R8 선택적 HTTP/클라이언트 계측 계약 — 2026-11-17

**후속 완료:** [전용 실행기·사전등록과 새 known-source localhost 기록](deliveries/2026-11-17_local_http_timing.md)을 추가했다.3사례·11요청/8출력 검산이며 실제 모델/카메라/운영 인수는 미완료다. 아래 실행기/새JS기록이 없다는 문장은 이 후속 전 상태다.

기존 [G4 서버](../g4_lab/server.py)는 세션·문제 발급·입력 validation·서버 재채점·grant·일회 보호 시험 동작을 이미 구현한다. 이번 변경은 그 서버에 선택적 계측을 연결한다. 기본 `create_server(service)`는 계측 없이 동작하고, `create_server(service, timing=...)`일 때만 기록한다. root prod/원자료/기존 완료 결과는 변경하지 않는다.

[서버 계측/복구](../analysis/runtime_benchmark/http_timing.py) · [클라이언트/시도 구간/결합](../analysis/runtime_benchmark/http_client_timing.py) · [8개 새 검사](../tests/test_http_timing.py).

## 서로 다른 종점과 시계

`ServerTiming(new_private_jsonl)`은 단조 시계로 요청/phase 시작과 종료를 fsync 기록한다. 요청 duration의 시작은 HTTP handler dispatch이며 TCP accept/HTTP header 읽기는 포함하지 않는다. body read/JSON parse, session/issue/submit/protected action, media authorize/read, response encode/write를 구분한다. `TimedEvaluator(original, timing)`는 원래 evaluate를 그대로 호출하고 submit 안에 nested evaluator phase만 추가한다.

phase는 **inclusive**이며 intent 기록 I/O·기록 lock 대기/trace overhead가 포함된다. submit/evaluator를 더해 전체시간으로 만들지 않는다. 평가기 구간도 G4 JS 호출·입력 검산·bridge 대기 등을 포함하며 모델 추론 시간이 아니다. 요청 종료 event의 마지막 write는 그 요청 elapsed 밖이다. response_write 완료는 서버 write 반환이며 클라이언트 수신/화면 표시 완료가 아니다.

`TimedLocalClient`는 IPv4 loopback에만 연결하고 proxy/redirect를 사용하지 않는다. 각 요청에 opaque correlation ID를 보내고 서버는 별도 request ID와 연결한다. 클라이언트 구간에는 JSON 준비·연결/요청·본문 수신·JSON parse·connection close와 trace overhead가 포함된다. 별도의 body_received 시각을 남긴다. `reconcile(client_raw, server_raw)`는 ID/route로 연결하되 **서로 다른 clock의 원시 시각을 빼지 않는다.** 완료한 서버 로그에 대응 request가 관측되지 않으면 null이며0초로 채우지 않는다. 모호한 중복 correlation은 거부한다.

`measure_attempt`는 기존 session에서 issue 요청 시작→media 본문 수신→제공된 replay 작성→submit→첫 보호 동작 본문 수신을 측정한다. grant가 없으면 보호 동작 완료시간/성공은 null이다. 두 번째 consume은 별도 요청이며 첫 응답 종점에 합치지 않는다. `first_pixel_presented_ns`는 항상 null이다. 브라우저 render/문제 인지/카메라·실제 사용자의 전체 시간을 측정했다고 하지 않는다.

score_pass·gate_pass·validation_pass·server_grant_issued·protected_action_allowed·repeat_action_allowed를 구분한다. HTTP200이나 trace outcome OK가 인증 성공은 아니다. G4 evaluator의 onRes/hold는 제출된 timestamp 기반 offline callback 재생이므로, 실제 HTTP 경과시간과 실제200ms 카메라 hold를 혼합하지 않는다. 현재 server 보호 동작은 새 localhost의 메모리 counter이며 과거/운영 인증 endpoint가 아니다.

## 정보·오류·보존

request trace에는 allowlist route만 남기고 `/media/:challenge`로 token을 지운다. cookie/session/challenge/grant ID·request/response body·좌표·평가기 예외 message를 기록하지 않는다. 원log와 clock/상세 결과는 비공개다. correlation은 로컬 기록 연결자이며 신원/입력 인증 수단이 아니다. handler/평가기·frame provider는 신뢰하는 코드다.

server/client raw 복구는 event 순서·단조 시각·phase parent/짝·duration·응답 write/수신 marker와 종료를 대조한다. partial prefix는 INTERRUPTED, 빈 log는 LOG_LOST, 모순/완료 뒤 추가/손상은 LOG_CORRUPT다. 미완료 phase/request의 종료시간은 null이다. server trace의 여러 request는 context별로 구분하고 recorder close는 live request가 있으면 거부한다. 기록이 실패하면 이후 계측 실행을 거부하며, 보호 동작 이후 기록 실패를 side effect rollback으로 주장하지 않는다. 실제 실행 파일 bytes/입력/코드/환경 결합은 외부 execution_record가 별도로 맡는다.

## 현재 검산과 실제 입력 preflight

합성 평가기/합성 media bytes를 사용한 **실제 loopback HTTP** 검사와 clock/log 단위 검사8개를 추가했다. nested inclusive 시간·모든 raw prefix·중단/close/context 복원·변조·concurrent context·저장 실패 후 네트워크 전 중단, 점수/관문/grant/보호 동작과 이중 consume, 점수/관문 거부, 평가 오류503을 검사했다. 기존 connection/capacity/evaluation-error16개와 합해24검사를 통과했다. 합성 media는 재생/디코딩한 영상이 아니며 실제 JS 평가기나 모델을 실행한 검사는 아니다.

기존 default G4 source 경로 `../g4-handcaptcha-source`는 없지만 지정 UI 작업트리 `../handcaptcha-ui-20261113`에는 pool_manifest의8clip·영상8/8·좌표8/8과 기존 Node 실행기가 있다. root prod hash는 인계의 고정값과 일치한다. 이는 지정 asset의 존재 preflight이며 새로운 촬영/독립 family가 확보됐다는 뜻은 아니다. 이 시점에서는 해당 입력으로 새 계측 실험을 실행하지 않았다.

## 다음 실제 기록 실행의 고정 범위

다음 단위에서 전용 실행기를 구현/검산한 뒤 별도 사전등록을 커밋하고 실행한다. 계획은 지정 UI manifest의 정렬상 첫 source 하나를 고정한 새 localhost·기존 Node/원문 JS 평가기에서 (1) 알려진 저장 reference 재생, (2) 처음 검출 자세의 정지 재생, (3) client passed/score 주장 추가 schema 거부를 비교하는 것이다. 같은 source/timestamp를 재사용하는 개발 진단이며 독립 사람/강한 영상 모델 공격이 아니다.

accept를 기대값으로 강제하지 않고 실제 score·offline gate·grant·보호 동작/이중 consume·HTTP 상태와 각 미완료를 보고한다. 모든 source/manifest/prod/landmark/video·Python/Node·설정·코드/환경 snapshot과 전체 새 명령/시간/stdout/stderr/출력 hash를 fresh private output/record에 남긴다. 실행 중 편집/commit을 하지 않는다. 새 다운로드/렌더/모델 추론/외부 전송·Cloud 이전은 필요 없다. 실행기가 아직 없으므로 이 문서는 실험 완료나 실행 가능한 명령의 기록이 아니다.

R8 전체에는 실제 모델의 관측/응답과 고정 관문/기한 연결, UI/동일 클라이언트 전체 종점, R9 독립 세션 검증이 계속 필요하다. 전체62ID·3D44표행·R0–R9와 앞 단계 실제 촬영/선별/대응 입력 우선, 원본/임계값 불변·비공개 영구 보관·Cloud보류를 유지한다.

최종 전체 회귀 검사는 `Ran 371, OK (skipped=1)`로 종료했다. skip1은 기본 환경에 mpmath가 없는 optional SDK box 모듈이며 기존 SDK 환경의 별도16검사 통과 기록을 유지한다. 이번에 SDK/모델 환경을 변경하지 않았다.
