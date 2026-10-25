# G4 평가 사전등록 템플릿 — v0.2

상태: 설계용 양식. 작성·검토·연구자 승인 전에는 실행 승인서가 아니다. 빈칸을 예시값으로 채우지 않는다. 원본 gesture/clip 목록, 개인별 자료, 입력 해시는 별도 비공개 저장소에 보관한다.

관련 문서: docs/human_data_analysis_requirements_v0.2.md의 FR6/NFR6, docs/threat_model.md, docs/followup_experiments.md, docs/reproducibility/v0_2_status_and_g4_next_steps_2026-10-26.md.

## A. 연구 질문 및 고정할 주장

- 연구 ID / 버전:
- 연구 질문:
- 공격자 유형 및 이유:
- 사전등록 일시와 holdout 개봉 조건:
- 이 결과로 허용할 주장:
- 이 결과로 허용하지 않을 주장:
- 책임 연구자 / 독립 검증자:

## B. 공격자별 정보와 자원

각 공격자 조건을 별도 행으로 작성한다. 서로 다른 입력 정보가 합쳐지면 별도 ablation 조건으로 등록한다.

| 조건 ID | challenge 전 보유 자료 | challenge 중 관측 가능 정보 | 제외된 정보 | CPU/GPU·모델·메모리 | 준비·추론 시간 | query·재시도 한도 |
|---|---|---|---|---|---|---|
| 미정 | 미정 | 미정 | 미정 | 미정 | 미정 | 미정 |

최소 구분 검토: 공개 화면/프레임, 파일·전환 metadata, 원 중심·반경, edge/visibility bit, 저장 reference/library, 모델 추론, 이들의 결합. 공격자에게 제공되지 않은 내부 landmark/score/answer를 입력으로 사용하지 않았는지 검증한다. 브라우저 상태·클라이언트 점수 변조 또는 API 직접 호출을 포함할지는 연구자가 별도로 정한다.

## C. 공통 challenge 및 판정 환경

- 인간 및 공격자에게 같은 challenge_id·원본 gesture/clip·방향·시도 한도를 적용하는 방법:
- 같은 화면·해상도·프레임 순서·전환·timeout·브라우저/runtime를 유지하는 방법:
- 동일 환경을 만들 수 없는 경우 독립 변수로 분리할 차이:
- 카메라·검출기·전처리·landmark 버전 및 좌우 미러링:
- challenge 무작위 배정 방법·seed·배정표 보관 위치:
- 재시도·취소·timeout·권한 실패·기술 오류 분류:
- 등록된 전체 시도와 각 분석 분모의 정의:

동일 challenge를 보장하지 못하는 결과는 paired 비교라고 부르지 않는다. 프레임·방향 파생물·조합 수를 독립 표본 수로 취급하지 않는다.

## D. 세 결과 endpoint 및 분모

각 endpoint에 판정 이벤트, 분자, 분모, 미판정 처리, 로그 근거를 실행 전에 채운다.

| Endpoint | 정의 | 분자 | 분모 | 입력/기술 실패 처리 | 확인 로그 |
|---|---|---|---|---|---|
| Gate 성공 | 등록한 gate 조건을 만족 | 미정 | 미정 | 별도 분류 후 사전 규칙 적용 | 미정 |
| Score 통과 | 잠긴 최종 score가 잠긴 threshold를 통과 | 미정 | 미정 | 별도 분류 후 사전 규칙 적용 | 미정 |
| End-to-end 인증 성공 | 실제 보호 동작/승인 상태까지 도달 | 미정 | 미정 | 등록된 모든 시도를 보고 | 미정 |

stop_on_fail=false에서 후속 score를 계산한 것은 gate 성공이나 end-to-end 성공으로 바꾸어 세지 않는다.

## E. 개발/검증 분리 및 누출 점검

- 개발 split의 source family 기준:
- holdout split의 독립 원본 gesture/clip 기준:
- 반복 세션, mirror, 방향 역전, fade/warp, 조합, 재인코딩의 source family 연결 규칙:
- 중복 및 near-duplicate 검사 방법:
- split manifest의 비공개 보관 위치 및 접근 통제:
- 독립 검증자의 split 검사 일시/결론:
- 누출 발견 시 평가 무효화·재분할·재승인 규칙:

같은 원본에서 파생된 자료는 전부 같은 split에 둔다. holdout 결과를 본 뒤 조건·threshold·가중치를 바꾸면 변경된 결과를 탐색 결과로 분리한다.

## F. 사전 잠금 설정

| 설정 | 고정값 또는 revision | 출처/정당화 | 잠금 시각 | 변경 시 처리 |
|---|---|---|---|---|
| challenge/pool | 미정 | 미정 | 미정 | 미정 |
| scoring/gate 구현 | 미정 | 미정 | 미정 | 미정 |
| weights / Emax / threshold | 미정 | 미정 | 미정 | 미정 |
| detector / preprocessing | 미정 | 미정 | 미정 | 미정 |
| timeout / retries | 미정 | 미정 | 미정 | 미정 |
| analysis code / environment | 미정 | 미정 | 미정 | 미정 |

설정은 holdout 접근 전에 버전·fingerprint를 남겨 잠근다. 수치의 과학적 타당성은 연구자가 정당화하고 독립 검증자가 평가 전 잠금을 확인한다.

## G. 표본·통계·성공/실패 기준

- 독립 분석 단위 및 cluster:
- 주 outcome, 방향, 비교 조건:
- 표본 수 또는 목표 정밀도와 근거:
- paired 또는 unpaired 분석 선택 근거:
- 효과크기 및 신뢰구간 방법:
- 다중 비교 처리:
- 성공 경계와 그 근거:
- 실패 경계와 그 근거:
- 불확정 판정 조건:
- 중단/기술실패 조건:

현재 자료만으로 임의의 최소 성공률, 허용 실패율, 효과크기, 신뢰구간 폭 또는 표본 수를 확정하지 않는다. 연구자 결정과 독립 사전등록 확인이 끝나기 전에는 holdout 결과를 열지 않는다.

## H. 자원·기록·개인정보

- 하드웨어 및 CPU/GPU 제한:
- 모델 revision, weights, 준비시간, 추론시간, peak memory:
- 네트워크/API 사용 여부 및 승인:
- 시도·프레임·예외의 기록 schema:
- 원자료/식별 정보/해시 보관 위치와 접근 제한:
- 공개할 집계와 공개하지 않을 자료:
- 원자료 불변 확인과 출력물 개인정보 검사:

기본 계획은 기존 승인 자료와 로컬 CPU 분석이다. GPU, 유료 서비스, 외부 API, 신규 촬영·모집, 서비스 배포는 별도 승인이 필요하다.

## I. 실행 전 독립 검토 및 승인

- [ ] 공격자 관측 가능 정보가 명확하고 내부 정답 누출이 없다.
- [ ] 동일 challenge 여부와 환경 차이를 설명했다.
- [ ] gate / score / end-to-end 정의와 분모가 서로 구분된다.
- [ ] source-family split과 near-duplicate 누출 검사를 독립 검증자가 확인했다.
- [ ] weights / Emax / threshold / gate / timeout이 holdout 전에 잠겼다.
- [ ] 표본·효과·CI·성공/실패/불확정 기준의 근거가 기록됐다.
- [ ] 원자료 보호·공개 산출물 검사를 완료했다.
- [ ] 연구자가 이 특정 프로토콜·자료·실행을 승인했다.
- [ ] 독립 검증자가 실행 전 manifest를 승인했다.

연구자 승인자 / 날짜:
독립 검증자 / 날짜:
실행 허가 상태: 미승인 / 승인 (해당하는 하나를 선택하고 근거 기록)

## 요구사항 대응 확인

| 명세 | 템플릿 위치 |
|---|---|
| FR6 공격자 지식·관측·계산자원 | B, H |
| FR6 동일 challenge와 판정 환경 | C |
| FR6 gate, score, 전체 인증 분리 | D |
| FR6 원본 source 단위 분할·누출 방지 | E |
| FR6 weights/threshold 사전 고정 | F |
| FR6 사전 성공/실패 기준 및 한계 | G |
| NFR1/NFR4 원본 보존·개인정보 | H |
| NFR5/NFR6 자원·단계 승인 | H, I |

이 템플릿은 계획을 빠짐없이 기록하도록 돕는 양식이며, 연구자 선택·자료 확보·독립 검토·실행 승인을 대신하지 않는다.
