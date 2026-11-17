# R7 별도 process timed-release 합성 검산 — 사전등록 v1

기존 queue/log 준비를 실제 부모/worker process 전달 경로와 연결한다. 실제 모델/영상/사람/게이트/서버의 지연이나 인증 결과를 측정하지 않는다. 완료한 모델 추론을 반복하거나 자산을 다운로드/설치하지 않는다. 원래 전체 단계/백로그와 실제 입력 우선은 유지한다.

## 실행 경계

[arrival_replay](../analysis/runtime_benchmark/arrival_replay.py)는 부모가 미리 가진 합성 bytes의 일정만 가지고 있다가 정해진 offset 이후 실제 도착 시각을 queue에 기록한다. worker command에는 importable handler entry만 전달한다. [worker](../analysis/runtime_benchmark/replay_worker.py)는 containment 설치 후 gate를 받아 handler를 import하고, 현재 batch의 sequence/PTS/pixels만 받는다. 전체 일정·파일 경로·참조 답은 전달하지 않는다. Python/filesystem 악성 코드 sandbox가 아니며 handler/producer는 신뢰하는 로컬 코드다.

worker 처리 중 부모가 계속 도착/drop을 기록한다. 부모의 start→finish는 IPC/관측·logging을 포함한 service 구간이고 모델 kernel 시간이 아니다. worker handler 자체의 wall/자체CPU 차이는 별도 clock 구간이며 더해서 전체시간을 만들지 않는다. GPU 동기화/실제 모델 handler는 이번 범위에 없다. setup(import/ready)·timed-release·cleanup을 분리한다. preloaded bytes 준비/디코딩 비용은 제외되며 원본 촬영 이후 나이도 측정하지 않는다.

부모 delivery에 scheduled/actual ingress/lateness를 기록한다. OS 지연·fsync·IPC 때문에 실제 도착이 늦을 수 있으며0으로 보정하지 않는다. polling은1ms sleep 요청이지만 실제 scheduling 보장이 아니다. 단일 idle worker에만 최대8MiB batch를 보내며 parent의 pipe write 자체는 선점형 deadline이 아니다. 실제 명령은 외부 execution recorder의120초 process-tree budget으로 추가 감싼다. child의 hang/종료는 소유 Windows Job/POSIX process group으로 회수한다. 다른 기존 프로세스는 건드리지 않는다.

## 고정7사례

[replay_fixture](../analysis/runtime_benchmark/replay_fixture.py)의 고정 사례다. FIFO/latest 첫 합성 handler만150ms sleep하며 이것은 모델 시간이 아니다. 입력4개는 offset0/10/20/30ms, 첫 source PTS는900ms이며 clock과 구분한다.

| 사례 | 고정 기대: 도착/finish/drop/처리 중 미완료/미도착 | 종점 |
|---|---|---|
| FIFO capacity1 | 4/2/2/0/0 | transport COMPLETED |
| latest capacity1 | 4/2/2/0/0 | transport COMPLETED |
| partial no_detection | 1/1/0/0/0 | min/max batch2이나 EOS로1개 flush, no_detection |
| timeout | 1/0/0/1/1 | 60초 sleep handler를0.2초 release deadline에서 회수. 두 번째 예정 도착1초는 미도착 |
| handler error | 1/1/0/0/0 | 오류 outcome, queue ERROR |
| worker crash | 1/0/0/1/0 | exit7, finish는 미확정 |
| setup error | queue 없음 | 의도한 missing synthetic module import 실패, setup ERROR |

처리 중 도착/overload, EOS batch, deadline, 오류와 process exit/미도착, 현재 batch의 실제 bytes hash/keys/sequence와 dispatch 대응, 저장 원로그→recovery 일치를 검사한다. 실제 scheduling이 기대 분모와 다르면 실패/원기록을 그대로 보존하며 기준 조정이나 같은 root 재실행을 하지 않는다. handler 준비 budget10초, 기본 release budget5초이며 timeout 사례만0.2초다. 전체120초, CPU 연구6pin 기존 환경만 사용한다.

예상41출력: queue가 있는6사례는 각 plan/transport/stderr/result와 queue event/recovery6개, setup error는4개, 전체 summary1개다. 실제 명령/UTC/wall/자체CPU/stdout/stderr·producer commit/전체 worktree·입력/환경 snapshot·postflight·모든 출력 크기/hash를 새 비공개 output/record/config에 남긴다. 실행 중 편집/commit 금지다.

공개 집계는 사례 상태/분모/검산 여부와 모델·영상·사람0만 허용한다. 합성 sleep/IPC 시간은 비공개 원로그에 남기고 모델 성능표로 내보내지 않는다. full62ID·3D44표행·R0–R9와 prod/원자료/비공개 영구 보관/Cloud보류를 유지한다. 실제 모델·관문/기한·localhost 전체 흐름·독립 세션은 계속 미완료다.
