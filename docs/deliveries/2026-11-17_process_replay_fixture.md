# R7 별도 worker 도착 재생 검산 — 2026-11-17

부모가 고정 일정으로 합성 pixel bytes를 전달하고 별도 process가 현재 batch만 처리하는 경로를 연결했다. **실제 모델·원영상·사람·게이트·서버 실행은0**이다. [사전등록](../r7_process_replay_preregistration_2026-11-17.md) · [재생기](../../analysis/runtime_benchmark/arrival_replay.py) · [worker](../../analysis/runtime_benchmark/replay_worker.py) · [고정 fixture](../../analysis/runtime_benchmark/replay_fixture.py) · [검사](../../tests/test_arrival_replay.py) · [비성능 공개 집계](../../reports/r7_process_replay_20261117.json).

## 실제로 확인한 경계

부모가 전체 일정을 가지고 있지만 worker에는 handler entry와 현재 sequence/PTS/pixels만 전달한다. 실제 파일 경로·전체 일정/미래 프레임·참조 답을 넘기지 않는다. 현재 batch의 keys/sequence/pixel hash와 dispatch 대응을 확인했다. source PTS와 실제 도착 clock은 별개이며, scheduled/actual/lateness를 기록했다. 처리 중 부모는 새 도착/drop을 계속 기록한다.

이것은 신뢰하는 코드 사이의 process/API 경계다. worker의 별도 filesystem/전역 지식이나 악성 Python introspection을 격리하는 sandbox는 아니다. 미리 읽은 입력 준비/디코딩은 release 시간에서 제외한다. 실제 카메라/미래 정보 전체 차단·온라인 공격 성능을 입증한 결과가 아니다.

부모의 service는 IPC·응답 관측/logging을 포함한다. worker의 handler wall/자체CPU는 별도 duration이다. 합성 sleep을 모델 시간으로 내보내지 않으며 공개 집계에는 clock/duration을 제외했다. setup/ready와 release, cleanup을 분리하고 실제 arrival 지연을0으로 보정하지 않았다. 부모 pipe write는 선점형 timer가 아니므로 새 명령은 외부120초 execution record로도 감쌌다.

## 고정7사례 결과

| 사례 | 상태 | 도착 | finish | drop | 처리 중 미완료 | 미도착 |
|---|---|---:|---:|---:|---:|---:|
| FIFO | COMPLETED | 4 | 2 | 2 | 0 | 0 |
| latest | COMPLETED | 4 | 2 | 2 | 0 | 0 |
| EOS partial/no_detection | COMPLETED | 1 | 1 | 0 | 0 | 0 |
| release timeout | TIMEOUT | 1 | 0 | 0 | 1 | 1 |
| handler 오류 | ERROR | 1 | 1 | 0 | 0 | 0 |
| worker exit7 | ERROR | 1 | 0 | 0 | 1 | 0 |
| setup 오류 | ERROR | — | — | — | — | — |

COMPLETED는 transport의 도착/정착 완료다. no_detection/handler 오류는 별도 outcome이며 인증 성공이 아니다. timeout과 worker exit에는 가짜 finish를 쓰지 않았다. setup 오류에는 queue 자체를 만들지 않았다. 오류4종은 사전등록한 합성 경로이며 실제 모델 실패율이나 보안 성공률의 분모가 아니다.

## 실행 기록과 보존

생산 commit `3d00b92`, output `../private_artifacts/r7_process_replay_20261117_v1`, record `r7_process_replay_record_20261117_v1`, config `r7_process_replay_config_20261117_v1.json`이다. 입력3개(설정 포함)·기존 연구6pin 환경, `EXITED_ZERO`·사후snapshot 일치·41출력의 `RECORDED_FILES_MATCH`를 확인했다. queue가 있는6사례의 원bytes→recovery와 공개 집계 결합을 다시 확인했다. 기록 실행 동안 코드/문서를 편집하지 않았다. 원clock·transport·hash·stderr·receipt는 영구 비공개다.

초기 관련46검사(queue22·stage/journal18·기존 supervisor6)를 통과했다. 이후 전체362검사에서는 latest 첫 dispatch가 항상 sequence0이라는 timing 가정1개가 실패했다. 실제 fsync/OS 지연으로 다음 프레임이 먼저 도착해0을 교체하는 것은 정책상 허용된다. 테스트를 실제 arrival 순서의 FIFO/latest 선택과 현재 pixels/dispatch 대응을 확인하도록 수정했고, 의도한 ingress 로그 지연으로 첫 프레임이 교체되는 회귀 검사를 추가했다. 이미 성공한7사례 원기록/생산 코드는 다시 실행하거나 바꾸지 않았다.

수정 후 전체 검사는 `Ran 363, OK (skipped=1)`로 종료했다. 현재 새process6검사는 실제 도착 순서/현재 pixels, FIFO/latest/EOS batch, 강제 ingress 지연, timeout 미완료/회수, handler error/exit/setup 구분, invalid config/fresh root를 다룬다. skip1은 기본 환경에 mpmath가 없는 SDK box 모듈이며 기존 SDK 환경의 별도16검사 통과 기록을 유지한다. SDK 코드는 이번에 변경하지 않았다. 실제 모델/GPU 완료와 같은 입력의 모델 품질/관문 성공은 검증하지 않았다.

등록 촬영 jobs21행의 `source_path`는 이번 확인에서도0개였다. PC 전체 영상이 없다는 뜻은 아니다. 전체62개 ID·3D44표행·R0–R9와 실제 촬영/선별·대응/독립평가 우선, prod 불변·비공개 영구 보관·Cloud보류를 유지한다. R7 전체 인수에는 실제 모델/같은 정보 공격·고정 관문/기한 연결이 필요하다. 다음 독립 작업은 R8 기존 localhost 흐름의 실제 타이밍/판정 계약을 점검해 연결 준비를 하는 일이다. 새 local service 실행 역시 별도 사전등록/기록을 갖춘다.
