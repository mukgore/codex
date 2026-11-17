# R7 도착 대기열 계약과 현재 검산 — 2026-11-17

R4의 실제 HaMeR/새 모델 계측과 R6의 같은 정보 공격 비교는 입력/자산 대기다. 그 선행 조건을 완료 처리하지 않고, 독립적으로 준비할 수 있는 R7 대기열 API를 추가했다. [구현](../analysis/runtime_benchmark/arrival_queue.py) · [합성 회귀 검사](../tests/test_arrival_queue.py). 실제 영상/모델/사람/서버를 실행한 결과가 아니다.

## 정보와 시계 경계

신뢰하는 producer가 **현재 전달된 pixel bytes만** `arrive(sequence, source_pts_ns, pixels)`에 넣는다. 도착 시각은 queue가 자기 monotonic clock에서 읽는다. source PTS는 메타데이터이며 latency 계산에 사용하지 않는다. worker에는 `consumer()`를 전달한다. 소비자 API는 `take()`와 `finish(batch, outcome=...)`뿐이며 원파일 경로·전체 프레임 배열·미래 ID 조회를 제공하지 않는다. 아직 도착한 프레임이 없으면 `None`이다. 순번은 음수가 아닌 증가 정수이며 재사용을 거부한다.

이는 협력하는 로컬 adapter의 API 계약이다. Python 객체 introspection·별도 filesystem 접근·producer의 선행 decode/잘못된 pixel/정답 주입을 격리하는 sandbox가 아니다. 실제 재생기는 producer와 worker의 데이터 전달 경계를 추가로 검산해야 하며, 전체 영상을 가진 reference/oracle와 온라인 모델을 구별해야 한다. bytes만 받는다는 이유로 픽셀 추론이나 보안 경계가 입증되지는 않는다.

하나의 ingress event loop에서 순차 호출한다. thread-safe queue나 background scheduler가 아니다. 블로킹 모델을 ingress loop에서 직접 실행하면 도착 전달이 멈춘다. 실제 연결에서는 별도 worker process에 현재 batch만 전달하고, producer loop는 그동안 새 도착을 계속 기록해야 한다. 이 process/재생 scheduling 연결은 아직 구현하지 않았다. GPU 완료를 기다리지 않은 호출 반환을 `response_ready`로 보고해서는 안 된다.

## 고정 정책

| 계약 | 동작 |
|---|---|
| FIFO | 대기 용량이 차면 새 도착을 `incoming_overflow`로 기록하고 버린다. 처리 중 batch는 대기 용량과 별도다. |
| latest | capacity=1만 허용한다. 새 도착이 대기 중 이전 프레임을 교체하며 처리 중 프레임은 교체하지 않는다. |
| batch | min_batch에 도달하거나, 가장 오래 기다린 프레임의 max_wait가 지나거나, EOS가 오면 max_batch까지 전달한다. 실제 take 시각까지의 추가 scheduling 지연도 대기에 포함한다. |
| 기한 | 같은 queue clock의 절대 deadline을 사용한다. `now >= deadline`이면 기한을 넘긴 것으로 처리한다. 대기 중 프레임과 이후 새 도착은 deadline drop이며, 이미 처리 중인 batch는 완료 시 늦음을 기록한다. |
| 완료 | `response_ready`, `no_detection`, `error`, `aborted`를 별도로 기록한다. response_ready는 채점/hold/인증 성공이 아니다. |
| 중단 | pending은 이유와 함께 drop한다. active batch는 unfinished token만 남기며 가짜 finish/0초를 만들지 않는다. |

arrival/start/finish/drop/end_input/close event에는 증가 event ID와 같은 단조 시각을 남긴다. pixel bytes는 event에 쓰지 않는다. 각 프레임의 queue wait와 arrival→finish 지연을 개별 기록하며, service time을 batch 크기로 나누지 않는다. frame 나이는 현재 구현에서 **실제 ingress 도착 이후 나이**다. source capture clock과 ingress clock을 정렬하지 않았으므로 촬영 이후 나이로 부르지 않는다. batch의 deadline_met는 응답 시각 조건이며 전체 관문 결과가 아니다.

sink는 기존 durable JSONL writer에 연결할 수 있다. 쓰기 실패가 나면 이후 처리를 거부하고 미완료 기록을 보존해야 한다. 현재 API의 event list 자체는 영구 저장이 아니며, raw queue event에서 summary 재생성·변조/부분 로그 복구·manifest 결합은 다음 구현 과제다. 성공한 unit test를 별도 실행 record/재생기 실험으로 주장하지 않는다.

## 수행한 검사와 미완료

8개 새 합성 검사는 미도착 조회 부재와 PTS/시계 분리, batch 대기/EOS, 처리 중 FIFO 과부하, latest 교체, queue/compute를 포함한 기한, 중단의 미완료 보존, ID/path/시계 회귀 거부, sink 실패 후 중단을 검사했다. 기존 stage/journal과 합해 `Ran 26, OK`다. 주입 시계이므로 실제 처리 성능값은 없다.

다음은 queue 원event의 독립 재구성/보존, 고정된 도착 일정의 producer와 worker process 연결 및 미래 프레임 차단 검사다. 실제 모델·같은 정보 공격 비교·원래 관문/기한·localhost 전체 흐름·독립 세션 재실행이 확보되기 전에는 R7/R8/R9 전체 완료로 닫지 않는다. 새 실제 재생 실험은 별도 사전등록과 immutable output/record 및 입력·코드·환경 snapshot을 갖춘다. 완료48영상 추론은 반복하지 않는다.

전체62개 ID·3D44표행·R0–R9, 앞 단계 실제 촬영/선별/대응 입력 우선, 비공개 영구 보관·Cloud보류·기존 prod 불변을 유지한다.
