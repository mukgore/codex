# R8 새 localhost/reference·정지·schema 계측 — 사전등록 v1

[계측 계약](r8_http_timing_contract_2026-11-17.md)의 다음 실행을 고정한다. [전용 실행기](../analysis/runtime_benchmark/local_http_probe.py)와 [검사](../tests/test_local_http_probe.py)를 구현했다. 합성 source/평가기 기반의 실제 HTTP 및 기존 계측/서버 검사29개를 통과했다. 여기까지 실제 source의 JS 평가기는 아직 실행하지 않았다.

## 입력·사전 지식·종점

지정 `../handcaptcha-ui-20261113`의8clip pool manifest를 사용한다. 정렬상 첫 source 하나로 issue 순서를 고정하며 provider는 그 source의 기존 전체 좌표/영상 bytes를 issue 이전부터 안다. source를 처음 보는 영상 모델이나 독립 평가가 아니다. media 수신 bytes와 고정 source hash를 비교하고 기존 reference를 전달한다. 원본8영상/8좌표와 manifest/prod를 snapshot 입력으로 묶는다. Node 초기 준비는8source의 기존 좌표를 읽지만 submit 평가 family는1개다.

root prod SHA256은 인계의 `0d82dd439fe7976f8b860eb82e654e6f5637b2d7a3fcce2d02f2f99e5f5bea11`로 고정한다. 다르면 실행 전에 거부한다. 모델/renderer/검출기/카메라/외부 서비스·새 영상은 실행하지 않는다. 실제 G4 Node bridge는 원문 JS 함수만 추출하며 page startup/카메라/외부 fetch를 실행하지 않는다.

## 고정3사례

| 순서 | 입력 | 판정/계측 |
|---|---|---|
| 1 known_reference | 기존 raw frame index 시간과 결측을 보존한 reference | issue→media body→replay→submit, grant가 있으면 첫 consume과 두 번째 consume |
| 2 static_first_detected | 동일 timestamp/결측 mask, 검출 행은 처음 검출한21점 자세의 복사 | 위와 같은 흐름. 실제 score/gate/grant/보호 동작을 보고하며 기대 수락/거부를 고정하지 않음 |
| 3 invalid_schema_claims | 새 challenge에 정상 reference와 client `passed=True, score=1` 필드를 추가 | HTTP400·grant 없음. media/보호 동작을 실행하지 않는 schema control이며 전체 시도 시간과 섞지 않음 |

reference 검출이 없거나 구조/시간이 잘못되면 데이터를 고치거나 필터링하지 않고 실패로 보존한다. 점수/관문 수락은 통과 조건이 아니다. grant가 발급되면 새 localhost 메모리 counter의 첫 consume과 두 번째 consume 결과를 구분하고, 관측한 true 첫 consume 수와 최종 counter가 같아야 한다. 두 번째 consume true는 허용하지 않는다. grant가 없으면 보호 동작/완료시간은 null이다.

## 실제 시계와 한계

client/server는 별도 단조 clock domain을 사용한다. 같은 client의 issue 요청 시작→media 본문 수신과 첫 action 본문 수신 구간을 남긴다. first pixel/render/사람 인지 시각은 관측하지 않는다. schema control은 issue→submit body만 기록한다. server 요청은 dispatch→return, evaluator phase는 submit 내부 inclusive 구간이다. nested 시간을 더해 전체시간을 만들지 않는다. tracing/fsync/lock/IPC의 overhead를 포함하며 계측을 끈 값과 동일하다고 가정하지 않는다.

G4 gate는 제출된 timestamp로 실제 JS onRes를 fake-clock 재생한 **offline 관문**이다. HTTP elapsed는 실제지만200ms 카메라 hold/입력 freshness/인증을 측정한 결과가 아니다. 새 보호 시험 동작은 localhost 메모리 counter이며 과거/운영 서비스의 인증 성공이나 보안 우회로 해석하지 않는다. 같은 known source의 개발 시도3개를 독립 문제/사람/보안 성공률 표본으로 세지 않는다.

## 고정 실행/출력

기존 Python 연구6pin·Node v24.18.0만 사용한다. 원본/source/model 환경을 변경하지 않는다. evaluator call15초, client/server request20초, state wait1초, challenge TTL60초/session TTL300초, session issue budget3개, stationary filter off를 유지한다. CPU Python wall/자체CPU와 setup을 기록하고 Node 자식 CPU는 미관측/null이다. client/socket timeout은 CPU 선점이 아니므로 전체 명령을120초 execution_record process-tree 예산으로 감싼다.

성공 명령의 예상8출력은 plan·server/client JSONL·attempts·joined·server events·Node stderr tail·summary다. 요청 수는 grant에 따른 consume 유무 때문에9–13개다. 전체 raw→recovery/ID-route 결합, 대응 누락0, schema evaluator 호출 없음과 HTTP400, 일회 counter 일치를 검산한다. 오류/부분 기록은 보존하고 같은 output/record/config를 덮어쓰거나 재실행하지 않는다. 새 실행은 별도 사전등록/ID가 필요하다.

새 private output/record/config에 명령·UTC/wall/자체CPU·stdout/stderr·producer commit/전체 worktree·설정/모든 입력/실행기/Node·환경 lock snapshot·postflight·출력 크기/hash를 보존한다. 실행 중 코드/문서 편집·commit 금지다. 공개에는 source ID·입력 hash/좌표·원clock/상세log 없이 사례별 실제 상태·성공/거부/null·경계가 명시된 소수의 elapsed 값을 허용한다. n=1/source1의 기술적 관측이며 반복 latency 분포나 모델 속도/인증 우위를 추정하지 않는다.

full62ID·3D44표행·R0–R9·앞 단계 실제 입력 우선/원본·임계값 불변/영구 비공개/Cloud보류를 유지한다. 실제 모델/강한 같은 정보 공격·실시간 UI/카메라/신뢰 입력·운영/독립 세션은 계속 미완료다.
