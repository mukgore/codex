# R8 새 localhost의 reference·정지·schema 계측 — 2026-11-17

고정 root prod의 원문 JS 평가기와 기존 좌표/영상을 새 localhost에서 연결해 **점수·offline 관문·grant·일회 보호 시험 동작**을 구분했다. 알려진 reference는 보호 동작을1회 허용했지만, 정지 재생은 점수 기준을 넘어도 관문에서 거부됐다. client/server11요청과8출력 검산을 통과했다. 실제 카메라·모델·화면 표시·과거/운영 인증 시험은 아니다.

[사전등록](../r8_local_probe_preregistration_2026-11-17.md) · [실행기](../../analysis/runtime_benchmark/local_http_probe.py) · [계측 계약](../r8_http_timing_contract_2026-11-17.md) · [공개 집계](../../reports/r8_local_timing_20261117.json) · [요청별11행](../../reports/r8_local_requests_20261117.csv).

## 입력과 관측 결과

지정 UI pool8source를 기존 Node로 준비하고 정렬상 첫 source 하나를 고정했다. provider는 issue 이전부터 해당 영상과 전체 저장 좌표를 아는 reference 진단이다. opaque media를 실제 HTTP로 받아 고정 source의 bytes와 대조했지만, 영상을 보고 새 좌표를 추론하지 않았다. 모델 forward/검출/새 렌더·영상/사람 시행은0이다. 브라우저에서 영상을 재생하거나 first pixel을 관측하지 않았다.

두 replay는 동일한119 timestamp/119검출을 사용한다. 정지 후보는 결측 mask를 보존하면서 검출된 좌표만 처음 검출 자세로 고정한다. 원본/임계값을 바꾸거나 데이터를 필터링하지 않았다. G4 JS의 공유 경계가 있는3구간 채점은 payload119프레임과 별도의 내부 분모를 가지므로 새로운121관측처럼 세지 않는다.

| 사례 | HTTP submit | score(.25기준) | offline gate | grant | 새 보호 시험 동작 | 재사용 |
|---|---:|---:|---|---|---|---|
| known reference | 200 | 0.986929 / 통과 | 통과 | 발급 | 1회 허용 | 거부 |
| 처음 자세 정지 | 200 | 0.608384 / 통과 | 거부 | 없음 | 미실행 | 미실행 |
| client passed/score 주장 추가 | 400 | 미평가 | 미평가 | 없음 | 미실행 | 미실행 |

schema control은 정상 reference에 허용하지 않은 client 주장 필드를 추가한 제출이다. 평가기를 호출하지 않았고, 미평가를 점수0/관문 false로 채우지 않았다. 보호 동작은 localhost의 메모리 counter이며 최종1회와 client의 허용 관측1회가 일치했다. 두 번째 consume은 거부됐다.

## 실제 시간의 경계

다음 값은 각 사례1회/source1개에서 관측한 ms다. request trace의 시작과 body_received를 같은 client clock에서 빼서 재구성했다. 실제 화면 표시/문제 인지/카메라 입력의 시작이 아니다.

| 사례 | issue trace→media 본문 | client submit | server evaluator inclusive | issue trace→첫 보호 동작 본문 |
|---|---:|---:|---:|---:|
| known reference | 40.027 | 539.787 | 485.944 | 616.022 |
| 처음 자세 정지 | 64.688 | 512.071 | 430.143 | null(미실행) |

schema control의 issue trace→submit 본문은67.857ms였으며 media/평가기/보호 동작 종점과 비교하지 않는다. producer가 요청 함수 진입 전에 잡은 더 이른 procedure 시작 기준 값도 private/JSON에 별도 이름으로 남겼다(reference616.052ms). request trace 시작 기준의616.022ms와 같은 값으로 덮어쓰지 않는다.

server evaluator 시간에는 bridge queue·JSON 전달·JS 실행·기록 overhead 등이 포함된다. 서버의 구조 validation은 바깥 submit 구간에 포함된다. submit 안에 nested이므로 더해서 전체시간으로 만들지 않는다. tracing/fsync/IPC overhead를 포함했고 계측을 끈 비교 실행은 하지 않았다. client/server 원시 clock을 서로 빼지 않았다. Python core wall2006.860ms/setup654.050ms/자체CPU609.375ms는 실행기 함수 진입 이후 준비·3사례·정리/재결합까지이며 마지막 summary write는 밖이다. Node 자식 CPU는 미관측/null로 남겼다. 모델 cold/warm이나 GPU 속도로 해석하지 않는다.

G4 onRes/hold는 제출 timestamp로 fake-clock 재생한 **offline 관문**이다. HTTP elapsed가 실제여도 실제200ms 카메라 hold·입력 freshness/사람 존재가 검증된 것은 아니다. 한 known-source의 두 replay와 schema control을 독립 성공률/FAR 표본이나 강한 영상 모델 공격으로 세지 않는다. source별/장비별 latency 분포와 일반화는 미검증이다.

## 실행 증거와 남은 일

생산 commit `b8481bc`, private output `../private_artifacts/r8_local_timing_20261117_v1`, record `r8_local_timing_record_20261117_v1`, config `r8_local_timing_config_20261117_v1.json`이다. 입력22개(설정 포함)·기존 연구6pin·Node v24.18.0, `EXITED_ZERO`·사후snapshot 일치·8출력의 `RECORDED_FILES_MATCH`를 확인했다. 기록 실행 동안 편집/commit하지 않았다. source IDs/좌표/개별 hash·원clock·correlation·세부 이벤트/receipt는 영구 비공개다.

원JSONL→client/server 복구→ID/route 결합→저장 joined/attempt·service event의 점수/관문·consume 대응을 확인했고 누락0이다. 보고서/CSV는 source ID·절대 원clock·입력 hash 없이 범위가 정해진 결과와 elapsed만 내보냈다. 모델/원영상 추론·완료 실험을 다시 실행한 것이 아니라 새 HTTP 계측 종점의 진단이다.

관련29검사가 통과했다. 초기 exporter 검산을 합성 unit 임시폴더에 연결할 때 production private-root guard가 거부한 경우를 확인했고, production guard는 유지한 채 unit fixture에만 기존 temp guard를 주입했다. 실제 지정 private 실행 폴더의 집계는 그 guard와 추가 service-event 검산을 통과했다. 실제 기록/출력은 수정하거나 재실행하지 않았다.

R8의 기존 evaluator/새 localhost 연결 일부 근거다. R7 실제 모델의 인과적 응답·고정된 실제 관문/기한·UI/카메라·신뢰 입력과 보호 동작, R9 독립 세션 재실행/원로그 재검산은 남는다. 앞 단계 실제 촬영/선별·독립평가 입력 우선과 전체62ID·3D44표행·R0–R9, root prod/원자료 불변·비공개 영구 보관·Cloud보류를 유지한다.

최종 전체 검사는 `Ran 376, OK (skipped=1)`로 종료했다. skip1은 기본 환경에 mpmath가 없는 optional SDK box 모듈이며 기존 SDK 환경의 별도16검사 통과 기록을 유지한다. SDK/모델 환경은 이번에 변경하지 않았다.
