# R9 별도 프로세스의 기존 실행 재구성 — 2026-11-17

네 종류의 runtime 자료를 각각 새 Python process에서 읽고 공개 JSON4개/CSV59행이 동일하게 재생성됨을 확인했다. 다섯 기존 execution record의 원출력812개와 새 감사24출력의 검산을 통과했다. **완료한 모델·Node scoring·HTTP/worker 측정은 반복하지 않았다.** R9의 독립 실측 세션/전체 조건 재현을 완료했다는 뜻은 아니다.

[사전등록](../r9_reconstruction_preregistration_2026-11-17.md) · [부모 실행기](../../analysis/runtime_benchmark/reconstruction_audit.py) · [재구성기](../../analysis/runtime_benchmark/reconstruction_worker.py) · [공개 집계](../../reports/r9_reconstruction_20261117.json) · [runtime 보고서 색인](../../reports/runtime_benchmark/README.md).

| 자료 | 원출력 | 새 프로세스에서 확인한 내용 | 공개 집계 일치 |
|---|---:|---|---|
| 실제 MediaPipe 저장 예측 | 391 | 48×25=1,200프레임/769검출, 좌표 오차·분모, 저장96점수 집계, journal/bundle | JSON / CSV48행 |
| R4 합성 stage profile | 11 | 5경로 원trace→summary | JSON |
| R7 합성 process replay | 41 | 7경로 raw queue→summary·실패/미완료 분모 | JSON |
| R8 known-source localhost | 8 | 3사례·11 HTTP요청의 raw→joined→case/요청 집계 | JSON / CSV11행 |
| 기존 TF-04 reference display | 361 | MediaPipe 비교 reference의 원실행 receipt 결합 | 원출력 검산 |

MediaPipe 오차는 기존 generated-model projection reference와 저장 예측으로 다시 계산했다. 같은 순수 수학 함수를 사용하므로 독립 알고리즘 검증이 아니다. float metric만 abs/rel1e-12를 허용하고 count/null/identity는 정확히 일치해야 했다. 재생성 공개 JSON은 값·타입·목록 순서가 정확히 같았으며 CSV도 header/cell/row가 일치했다. 줄바꿈/JSON key 형식 차이는 결과 차이로 세지 않았다. 저장96 score는 재집계했으며 JS 점수 자체를 다시 실행하지 않았다.

새 worker process와 parent를 구분해 실행/종료를 기록했다. 같은 구현/환경의 별도 process이므로 다른 컴퓨터·연구자·독립 구현·제3자 실행으로 부르지 않는다. 모델 추론/새 영상/사람/측정 세션은0이다. 과거 latency·누락 시간을 다시 채우거나 원파일/기존 공개 보고서를 덮어쓰지 않았다.

## 기록과 빈 로그의 취급

생산 commit `3f65d17`, output `../private_artifacts/r9_reconstruction_20261117_v1`, record `r9_reconstruction_record_20261117_v1`, plan/config는 같은 prefix의 `r9_reconstruction_plan_20261117_v1.json`/`r9_reconstruction_config_20261117_v1.json`이다. 입력807개·기존 연구6pin, `EXITED_ZERO`·사후snapshot 일치·새24출력의 `RECORDED_FILES_MATCH`를 확인했다. 실행 중 코드/문서 편집·commit을 하지 않았다.

지정 원출력/기록857파일 중60개는 정상적인 빈 stdout/stderr log다(원출력55/기록5). 공통 snapshot의 빈 placeholder 입력 거부를 바꾸지 않았다. 비어 있지 않은797파일은 직접 snapshot했고, 빈60파일은 새 plan의 경로/0bytes/empty hash와 parent 전후 검사 및 기존 receipt로 결합했다. 빈 로그를 누락/삭제하거나0초 성능값으로 해석하지 않았다. 공개 기대6파일과 plan/실행기/사전등록/config도 snapshot에 들어 있다.

원log/예측·reference 좌표/개별 hash·원시 clock/경로/PID·receipt는 영구 비공개다. 공개 감사 집계에는 작업 종류·사례/분모·JSON/CSV 일치·모델0/새 측정0만 남겼다. parent가 어떤 worker 오류/timeout을 만나도 다음 작업을 확인하고 partial/nonzero를 보존하는 경로도 unit test로 검사했다.

새6검사와 관련 기존21검사, 총27검사를 통과했다. JSON 타입/순서, float 허용 오차와 count/null, CSV header/빈 cell, 고정 roster/path/root guard, 실패/timeout 뒤 다음 작업 확인, 빈 로그 변경/유실을 검사했다. CSV fixture의 Windows newline 중복 변환은 원bytes로 작성하도록 바로잡았고 실제 원본/보고서는 변경하지 않았다.

## 남은 전체 요구

R9 raw 재구성/보존 부분의 근거이며 R9 전체 인수는 미완료다. 실제 모델 조건의 별도 세션 재실행·장비/cold-warm/품질 대응·실제 streaming/관문·브라우저/카메라/운영 전체 흐름과 실제 독립 평가 자료는 계속 필요하다. 이 검사로 새로운 독립 source/family나 사람 표본이 생기지 않는다. 전체62ID·3D44표행·R0–R9/앞 단계 실제 입력 우선·root prod/원자료 불변·비공개/Cloud보류를 유지한다.

최종 전체 검사는 `Ran 382, OK (skipped=1)`로 종료했다. skip1은 기본 환경에 mpmath가 없는 optional SDK box 모듈이며 기존 SDK 환경의 별도16검사 통과 기록은 유지한다. 이번에 SDK/모델 환경을 변경하지 않았다. 등록 촬영21행의 source_path0도 재확인했다.
