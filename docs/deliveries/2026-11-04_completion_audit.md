# 전달본 이후 작업 완료 여부와 자동 생성 현황 감사

**감사 이후 진행:** 아래 190행과 코드 표는 전달 커밋 기준의 감사 스냅샷이다. 이후 Stage6 유지/Stage7 v2, 프레임 대응/배치 MP4, 손바닥 UI 12종 평가/3종 구현, 표준 좌표·시간 adapter 및 자체 작성 3D 골격 fixture를 추가했다. 최신 상태·106개 관련 검사·남은 요구는 [순차 구현 기록](2026-11-04_execution_progress.md)을 따른다. 사용자 답변상 가림 없는 원본 동작 자료는 없다. fixture는 실측 P1·Text2HOI 재현·사람/공격 성능의 완료가 아니다. 스냅샷의 “손목 충돌 미해결”, “batch/adapter/시연 logger 없음”을 현재 코드 상태로 읽지 않는다.

검토 기준: 2026-11-04. 결론: **deliverables가 두 저장소의 앞으로 할 일을 전부 실행한 것은 아니다.** 계획 통합·실험 카드·설명 초안과 세 묶음의 코드(점수 쌍 비교, Stage6/7 가림 보강, 독립 손 선택/중첩 시연)가 추가됐다. 생성기·실제 사람/독립 공격 평가·prod 통합·운영 출하는 완료되지 않았다.

**손동작 자동 생성은 원래 GitHub 요구사항에 있었다.** main의 [3D 손·물체 명세][THREED]는 2026-10-26 작성된 PROPOSED / NOT_TESTED 문서다. [초안 PR #2](https://github.com/mukgore/codex/pull/2)의 [촬영 대 생성 명세][GEN]는 Text2HOI+GRAB/MANO 원형 재현 R1과 자체 skeleton/primitive 저비용 파일럿 P1을 구분한다. 원격 확인 시 PR #2는 open/draft·미병합이며 head는 b8c39d5다. 전달 백로그 G01~G08에도 보존돼 있으나, 해당 생성 코드·실행 로그·생성 자산은 이번 전달에 없다.

## 검토 범위와 판정 기준

- 기존 G1~G4의 수용된 연구·재검산 범위를 유지했다. G3의 종료 결정과 G4 로컬 탐색/국소 방어/검산 완료를 후속 미완료로 되돌리지 않는다. 이 감사의 남은 일은 그 뒤의 기능·실험·운영 확장이다.
- main: codex 6cfe1b1, handcaptcha b4d96d1. 전달 커밋: [codex 916cc6f](https://github.com/mukgore/codex/commit/916cc6fd0febe7f94115c94ff16b8abc10c46e4a), [handcaptcha 6d92012](https://github.com/mukgore/handcaptcha/commit/6d9201296b3c4341b555845868ae15fd5f5ada8b). 원격 작업 브랜치 head와 기존 브랜치 목록을 다시 확인했다. 전달 변경은 작업 브랜치에 있으며 main 병합·배포 결과가 아니다.
- 전달 폴더 전체, 원문 색인의 문서, 관련 현재 코드와 테스트, 기존 G3/G4 기록, PR #1/#2 및 기존 원격 브랜치의 현재 tree를 대조했다. Git 전체 과거 이력·비공개 로컬 원자료·외부 대화 전체의 부재를 증명하는 감사는 아니다.
- 표의 “문서 완료”는 해당 계획/설명 작성 완료다. “코드·합성 검사”는 코드와 합성 회귀 수준이다. “부분”은 요구의 일부만 충족한다. “미실행/입력 필요/설계 후보”는 실행 성과가 아니다. “기존 완료 유지”는 전달본 이전에 수용된 결과다.
- 62개 상위 행과 여러 하위 계약은 서로 겹치고 크기도 다르다. 아래 **190개 추적 행**은 대조의 누락 점검 수이며 190개의 독립 작업이나 완료율 분모가 아니다.
- 이전 전달 적용에서 통과한 58개(수학12+CSV7+기존 함수17+가림9+Node13)는 [실행 기록][REVIEW]을 따른다. 이번 상태 감사에서 연구 실험이나 그 검사를 다시 실행하지 않았다. 추가 패키지도 설치하지 않았다.

## 실제 구현과 연결의 경계

| 묶음 | 확인한 성과 | 끝나지 않은 연결 |
|---|---|---|
| 점수 비교 | 두 점수가 이미 있는 CSV의 분할 검증·validation 선택·오류/중단 분모·집계 | 원좌표→특징/점수 adapter, 실제 대응 자료, B2/B3·군집 CI·JS 이식 |
| 손 선택/중첩 | 독립 시연의 큰 유효 손 선택·유지·소실 중단·분리/중첩 | prod의 handedness/문제/gate/timer/로그, 실제 카메라·사람 비교 |
| 가림 | Stage6/7의 2D 판정·누락 거부·전체 분모·재decode 내부 검사 | run_batch 연결·PTS/시간변형·다른 bake/legacy·최종 release |
| 자동 생성 | 요구·문헌·R1/P1 실행 계약이 있음 | 동작 generator, 손/물체/접촉, 렌더·정답·평가·생성 자산 |
| 서버/평가 | 기존 G4 loopback·반례·일회 소비 검산을 유지 | 실제 입력 출처·운영 경계·새 사람/미사용 source·비용 |

## 자동 생성으로 혼동하기 쉬운 기존 코드

1. [Stage6 generate_occluded_video][H6]는 기존 촬영 영상에 가림을 굽는다. [별도 bake][BAKE]는 역재생 변형도 처리한다. 새로운 행동 family를 합성하는 생성기가 아니다.
2. [lab 서버 issue][SERVER]는 저장된 source 목록에서 선택한다. 새 손동작을 만드는 함수가 아니다.
3. g4_lab/attacks.py의 generate_attacks는 알려진 기준 궤적을 정지/역전/보간/셔플/난수 대조 응답으로 변형한다. 기존 G4 진단 코드이며 정상 challenge 생성기로 세지 않는다.
4. 테스트의 합성 좌표/3-frame MP4와 Canvas render는 회귀 fixture/화면 합성이다. 3D 손·물체 generator의 구현/성능 결과로 세지 않는다.
5. 현재 tree들의 코드·노트북·모델 자산 파일 목록을 검색했다. 아래 scope JSON은 검색한 ref/SHA와 결과를 보존한다. 모든 비공개/과거 위치에 생성기가 없다는 주장은 하지 않는다.

## 세부 점검에서 발견한 중요한 공백

1. [pipeline.run_batch][PIPE]는 여전히 Stage6 renderer를 호출하지 않고 Stage7의 후보 manifest만 쓴다. accepted와 완성된 가림 MP4/release는 다르다.
2. [Stage2][QUALITY]는 frame을 제거하고 [Stage4][STAGE4]는 forward+reverse를 만든다. 새 [Stage6][H6]은 그 대응을 구현하지 않고 consecutive source index만 허용한다. 출력 FPS는 제공 info를 사용하며 실제 PTS/VFR 동등성은 검증하지 않는다.
3. w3>1이면 중점 원 안에 P0 손목이 들어가지만 [Stage7][H7]은 손목이 밖에 있을 것을 요구한다. [충돌 회귀][HGATETEST]는 보존됐고 해소되지는 않았다.
4. [dataset_expansion_bake_v1.py][BAKE]는 별도 경로로 남아 있고 last mask 재사용·최초 mask 없음의 위험한 구조와 Colab !pip 문법이 유지된다. Stage6 수정이 이 파일까지 고친 것은 아니다.
5. [legacy ingest][INGEST]는 현재 tree에 없는 export_pool을 import하며 동일 출하 관문을 실행하지 않는 구조가 남아 있다.
6. [prod][PROD]는 maxNumHands:1과 배열 첫 손, 공개 정답 fetch, client 채점 구조를 유지한다. 독립 시연의 두 손 검출·중첩 구현이 현재 prod에 반영됐다고 표시하면 안 된다.
7. [시연][DEMO]에는 상태 문구가 있으나 카드 B의 trial/event logger는 없다. 8 callback 안정화는 검증된 시간 기준이 아니며 좌우손/과제/관문 초기화도 prod와 연결되지 않았다.
8. [CSV CLI][COMPARE]는 caller가 제공한 계보 ID와 완성된 두 점수를 검사한다. attack-family/object/contact family 분할, 실제 근접 중복, 미사용 source의 독립성을 스스로 증명하지 않는다. 모든 split에 scored human/attack을 요구하므로 특정 split/집단이 전부 실패한 자료를 그대로 처리하는 범용 전체시스템 집계기도 아니다.
9. 백로그 V03의 “2×2”는 [원문 V3][VALIDATION]의 2×3(보호 유무×과제 없음/무가림/가림)을 축약했다. P0/P1은 보호 도구만으로 판정 가능한 때 포함한다. 모방 2×2만 시험하면 그 축소 범위를 밝혀야 한다.
10. POOL-03의 원문 상태는 INGESTED→RIGHTS_CLEARED→QUALITY_CHECKED→MASKED→ARTIFACT_VERIFIED→HUMAN_REVIEWED→SECURITY_EVALUATED→RELEASED이며 실패 QUARANTINED/폐기 RETIRED다. 백로그의 짧은 요약과 실제 구현된 상태 머신을 혼동하지 않는다.
11. T03의 첫/중간/끝, T05의 raster와 gate, T07/08의 RELEASED·PTS·모든 트랙 인수는 현재 일부 합성 검사보다 넓다. 같은 ID 전체 통과로 승격하지 않았다.
12. [원래 수학 명세][SCORE]의 “NumPy 2.2.6 재실행 전”과 일부 이전 문서의 업로드 실패는 과거 시점 기록이다. 후속 [전달 검사][REVIEW]의 2.2.6 통과·원격 커밋을 함께 읽어야 한다.

## 통합 백로그 62개 항목

| ID | 현재 판정 | 확인한 것 / 전달본의 기여 | 남은 정확한 작업·한계 | 근거 |
|---|---|---|---|---|
| NOW-01 | 문서 완료 | 통합 목록·원문 색인이 전달되고 커밋됨 | 목록에 있는 모든 작업의 실행 완료를 뜻하지 않음 | [BACKLOG][BACKLOG], [INDEX][INDEX] |
| NOW-02 | 코드·합성 검사 | Stage6/7 패치 적용 및 가림 9개·기존 함수 17개 검사 | PTS·release·다른 굽기 경로·수식 충돌은 별도 | [H6][H6], [H7][H7], [HTEST][HTEST], [REVIEW][REVIEW], [HINTEGRITY][HINTEGRITY] |
| NOW-03 | 코드·합성 검사 | 독립 시연과 선택 모듈, Node 13개 검사 | prod 연결·실제 카메라·사용성 측정 | [SEL][SEL], [DEMO][DEMO], [NTEST][NTEST], [DEMOTEST][DEMOTEST] |
| NOW-04 | 코드·합성 검사 | 점수 쌍 CSV 비교 CLI와 7개 검사 | 원자료 특징/점수 추출과 실제 평가 자료 | [COMPARE][COMPARE], [CTEST][CTEST] |
| NOW-05 | 문서 완료 | 카드 A/B/C의 조건·분모·기록 계약 작성 | 실험 선택·수치 잠금·수집·실행·판정 | [CARDS][CARDS] |
| NOW-06 | 문서 완료 | 기존 연구 설명·발표 검토 초안 작성 | 발표 시간·최종 주장 선택과 실제 발표 | [EXPLAIN][EXPLAIN] |
| R01 | 부분 | 설명 초안을 작성함 | 최종 발표 원고·분량·연구자 검토 | [EXPLAIN][EXPLAIN], [ROADMAP][ROADMAP] |
| R02 | 기존 완료 유지 | G3·A/B·FR1~4·DR3 수용 상태를 연결 | 기존 분석을 재실행할 새 미완료로 취급하지 않음 | [G3][G3] |
| R03 | 기존 완료 유지 | 조건부 재현 수용과 과거 build 계보 한계를 보존 | 미래 실행에서 build/pool manifest 기록; 과거 추가 복구는 현 범위 불요 | [G3][G3], [LINEAGE][LINEAGE] |
| R04 | 기존 완료 유지 | 이전 인간 단계 전체로 기준 선정, 사후 13시나리오 제외 설명 보존 | 새 독립 평가를 기존 연구로 소급하지 않음 | [G3][G3] |
| R05 | 입력 필요 | 초기 n=4·표10·grid25·시간·옛 p값 계보를 목록화 | 특정 원자료/실행 이력 확보 시 한정 대조; 완료된 A/B를 다시 열지 않음 | [RECOVERY][RECOVERY], [G3][G3] |
| R06 | 부분 | 과거 null의 해석 한계와 새 로그 계약 작성 | 새 관찰로 실제 수행/추적 오류 및 전체 UI 시간 구분 | [CARDS][CARDS], [DICT][DICT] |
| R07 | 기존 완료 유지 | 기존 G4 로컬 탐색·국소 방어·검산 기록을 연결 | 독립 source/사람/신뢰 입력은 별도 후속 질문 | [G4STATE][G4STATE], [G4REPORT][G4REPORT] |
| R08 | 문서 완료 | 모호성·허용 답 집합 카드 A 작성 | 복수 답 주석·채점 규칙 결정 및 관찰 | [CARDS][CARDS] |
| R09 | 문서 완료 | 지각/운동/추적 오류 분해와 수행 가능성 계획 | 관찰 절차·동의·자료 및 실제 평가 | [CARDS][CARDS], [FOLLOWUP][FOLLOWUP] |
| U01 | 코드·합성 검사 | 유효 21점·bbox·동률·안정화 선택 구현 | 실제 검출 반환 수·잘림/자세/FPS 영향 확인 | [SEL][SEL], [NTEST][NTEST] |
| U02 | 부분 | 위치·크기·형태 연속 추적, 소실/모호성 후 전체 재시작 | 짧은 재연결·handedness/문제/gate/로그 통합; 오연결 실기 검증 | [SEL][SEL], [DEMO][DEMO], [UI][UI] |
| U03 | 코드·합성 검사 | 분리/중첩·투명도·독립 반전·원본 카메라 검출 | 실제 좌우손·레이아웃·카메라·사용성 | [DEMO][DEMO], [HTML][HTML], [NTEST][NTEST], [DEMOTEST][DEMOTEST] |
| U04 | 미실행 | prod와 독립된 시연까지만 존재 | 선택 손·좌우손·관문·타이머·기록 연결 및 shadow 비교 | [PROD][PROD], [DEMO][DEMO] |
| U05 | 부분 | 후보 목록과 한 문장 상태 안내·손 테두리 일부 구현 | 연습/시범/작은 보조화면/도움말 선택·구현·비교 | [UI][UI], [DEMO][DEMO], [CARDS][CARDS] |
| U06 | 문서 완료 | 손 선택과 UI 효과를 나누는 카드 B 작성 | 행동 정답 정의·이벤트 수집기·참가자 비교·채택 결정 | [CARDS][CARDS], [UI][UI] |
| S01 | 미실행 | 좌표·시간·누락 표준 adapter는 명세로 남음 | 종횡비·미러·구간 시간·null/gap·참조 계보 adapter 구현 | [SCORE][SCORE], [COMPARE][COMPARE] |
| S02 | 부분 | 기존 constrained_dtw와 합성 검사 재사용 | 실제 15각도 특징·band/grid 선택·오답 비교·JS 이식 | [METRICS][METRICS], [SCORE][SCORE] |
| S03 | 부분 | 기존 비균일 timestamp 미분 함수 재사용 | 단위·gap·평활화·FPS/노이즈 검증과 실제 trial 적용 | [METRICS][METRICS], [SCORE][SCORE] |
| S04 | 부분 | 이미 계산한 legacy/candidate 점수 비교 도구 추가 | B0/B1 특징/점수 추출, B2 학습·B3 ablation·calibration | [COMPARE][COMPARE], [SCORE][SCORE] |
| S05 | 부분 | 기존 threshold 함수와 새 validation/test 집계 | ROC/DET 그림·공격군별 최악률·군집 CI·독립 평가 | [COMPARE][COMPARE], [METRICS][METRICS] |
| S06 | 미실행 | legacy gate를 유지하고 새 로그 항목만 설계 | gap/hold/coverage 규칙, 구간 집계, 버전 로그·저장 재로드 | [SCORE][SCORE], [PROD][PROD], [CARDS][CARDS] |
| S07 | 부분 | 합성 수학/CSV 검사는 있음 | adapter 검산→실제 대응 trial→독립 평가→JS parity→shadow | [SCORE][SCORE], [REVIEW][REVIEW] |
| V00 | 부분 | 기존 lab의 L1/L2/L3 구분과 새 score-only 분모 처리 | 새 실행 metadata validator·전체 attempts 로그·사전 잠금 | [SERVER][SERVER], [COMPARE][COMPARE], [VALIDATION][VALIDATION] |
| V01 | 기존 완료 유지 | known-pool의 정상/오답/정지/보간 탐색은 기존 G4에서 수행 | 새 기준·새 자료의 확증 평가가 필요하면 별도 실행 | [G4REPORT][G4REPORT], [G4STATE][G4STATE] |
| V02 | 부분 | CSV의 source/participant/capture ID 교집합 검사 | 실제 계보·근접 중복·attack-family holdout과 미사용 자료 | [COMPARE][COMPARE], [CARDS][CARDS], [VALIDATION][VALIDATION] |
| V03 | 미실행 | 입력 보호 추가 효과의 설계만 존재 | 원문 2×3 조건(가능한 경우), 보호 도구 적합성 및 대응 시험 | [VALIDATION][VALIDATION], [CARDS][CARDS] |
| V04 | 기존 완료 유지 | 기존 loopback 세션/만료/일회 소비·회귀 완료 | 실제 capture trust·과거 운영 인증·배포는 별도 범위 | [SERVER][SERVER], [G4STATE][G4STATE] |
| V05 | 미실행 | lab에 in-process RLock과 세션 상태는 존재 | rate/query·만료 정리·evaluator 공유 잠금·다중 worker/영속 원자성 | [SERVER][SERVER], [G4REVIEW][G4REVIEW] |
| V06 | 입력 필요 | 과거 human18/공개 pool/legacy의 차이를 유지 | 공통 challenge의 새 정상 자료·실제 카메라·source 계보 | [OVERLAP][OVERLAP], [G4STATE][G4STATE] |
| N01 | 부분 | 이번 전달 파일의 공개 범위·키 패턴을 검사 | 저장소 전체 Git 이력·비공개 자료의 별도 감사 | [REVIEW][REVIEW], [BACKLOG][BACKLOG] |
| N02 | 부분 | 실행 명령·관측 환경과 전달본 해시 기록 | 완전한 의존성 잠금·새 run manifest; 과거 계보는 범위 결정 유지 | [REVIEW][REVIEW], [REPRO][REPRO] |
| N03 | 부분 | 기존 주장 근거·선행 문헌·신규성 한계 보존 | 채택할 주장의 정밀 대조와 필요시 최신 1차 문헌 조사 | [CLAIM][CLAIM], [THREED][THREED] |
| P01 | 입력 필요 | 권리 대장 스키마와 금지 조건은 설계됨 | source별 허가·동의·파생/송출 권리 대장 및 validator | [POOL][POOL] |
| P02 | 입력 필요 | 촬영·source/capture/performer·중복 계획 존재 | 새 촬영/사용권 자료·실질 family 수량·분할·주석 | [POOL][POOL], [CARDS][CARDS] |
| P03 | 미실행 | private source/artifact와 public 응답·상태 전이 명세 | 기계 검증 schema와 승격/격리/폐기 상태 머신 | [POOL][POOL], [PIPE][PIPE] |
| M01 | 부분 | Stage6/7은 x/y 기준, 비연속 인덱스 거부 | 원본↔출력 frame/PTS mapping·시간변형·VFR 처리 | [H6][H6], [H7][H7], [STAGE4][STAGE4] |
| M02 | 설계 후보 | M0~M4·다중/순간/시간변화 후보를 보존 | 수식-손목 충돌 해결과 사람/단서/합성 공격 대응 비교 | [POOL][POOL], [HGATETEST][HGATETEST], [G4REPORT][G4REPORT] |
| M03 | 부분 | Stage6의 누락 거부·최종 decode·크기/개수/내부 픽셀 검사 | 해부학 ROI·PTS·모든 rendition/track·권리·release gate | [H6][H6], [HTEST][HTEST], [POOL][POOL] |
| P04 | 부분 | 기존 closed-set lookup·원/피부/미디어 단서 반례는 있음 | 독립 source·반복 예산·변형 제거·다중 마스크 합성 공격 | [G4REPORT][G4REPORT], [POOL][POOL] |
| D01 | 설계 후보 | 사전생성/요청생성/캐시/실시간 비교 계약 | 같은 source에서 수율·CPU·p95·저장/전송·공격/사람 비교 | [POOL][POOL] |
| D02 | 부분 | 기존 loopback의 media session/expiry 검사 | 운영 private origin·tenant·warm cache·Range/seek·폐기 정책 | [SERVER][SERVER], [POOL][POOL] |
| D03 | 부분 | 새 lab 서버 계산은 기존 구현, prod는 공개 정답 fetch 유지 | 비공개 정답 기반 실시간 UX·입력 경계·oracle/query 정책 | [PROD][PROD], [SERVER][SERVER], [POOL][POOL] |
| T01 | 부분 | 인수 24종의 일부 기계 검사와 기존 lab 회귀만 존재 | 아래 T01~24 각각의 운영/실자료 조건을 확인 | [POOL][POOL], [HTEST][HTEST] |
| W01 | 부분 | WP0 감사 기록과 WP2 가림 정비 일부 | WP1 확보/schema·WP2 연결/PTS·WP3~5 평가/운영 의존 작업 | [POOL][POOL] |
| G01 | 문서 완료 | 촬영 대 생성 비교 PR #2와 G01~08 연결 | R1/P1 생성 코드·자료·실행 결과 | [GEN][GEN], [THREED][THREED] |
| G02 | 미실행 | seed/모델/물체/카메라/접촉 manifest 명세 | 3D generator·기본 손/물체·접촉 계획·버전 manifest | [GEN][GEN], [THREED][THREED] |
| G03 | 미실행 | 관절·접촉·비관통·안전 가동·편안함 계약 | 기하/물리 validator와 실제 수행 가능성 검사 | [THREED][THREED], [GEN][GEN] |
| G04 | 미실행 | 비슷한 손 움직임에 물체 단서로 답이 다른 대응쌍 설계 | 대응 scene 생성·정답 집합·사람/공격 구분 평가 | [THREED][THREED] |
| G05 | 미실행 | 원본 pass/mesh/seed 비공개·최종 가림 렌더 계약 | 렌더러·그림자/반사/실루엣·buffer/codec 누출 검사 | [THREED][THREED], [GEN][GEN] |
| G06 | 설계 후보 | G0/G1/G2 과제 의미와 SCORE3D 구분 | G0 선택·투영 특징·복수 답·웹캠 불확실성 평가 | [THREED][THREED] |
| G07 | 미실행 | B0~B3×A1~A4 공정 비교 명세 | source/object/contact family 분할·같은 예산의 실제 실행 | [THREED][THREED], [GEN][GEN] |
| G08 | 입력 필요 | 외부 코드/모델/데이터 권리·자원 전제 목록 | 허용 자산·checkpoint·환경/자원 확보 및 원형 재현 | [GEN][GEN], [THREED][THREED] |
| B01 | 문서 완료 | 사람 성공·시간·중단·접근성 계획과 카드 A/B | 새 사람 자료·동의·순서·행동/수치 기준·관찰 | [CARDS][CARDS], [VALIDATION][VALIDATION] |
| B02 | 미실행 | 공격/방어·구매자 비용 공식은 명세 | 실측 setup/attempt/CPU/전송·p50/p95·경제성 입력 | [VALIDATION][VALIDATION], [POOL][POOL] |
| B03 | 설계 후보 | 고객군·질문·거래 증거 기준의 기존 명세 | 승인된 고객 조사·견적·계약/지급 근거 | [VALIDATION][VALIDATION] |
| B04 | 미실행 | CONTINUE/MODIFY/STOP/INCONCLUSIVE 기준 존재 | 사람·강한 공격·비용·권리 증거를 모은 새 의사결정 | [VALIDATION][VALIDATION], [ROADMAP][ROADMAP] |

## 기존 코드 감사 AUD-01~20의 조치 여부

| ID | 현재 판정 | 확인한 것 / 전달본의 기여 | 남은 정확한 작업·한계 | 근거 |
|---|---|---|---|---|
| AUD-01 | 미해결 | 공개 8 clip manifest 구조 보존 | 공개 응답과 비공개 정답 manifest 분리 | [MANIFEST][MANIFEST], [PROD][PROD] |
| AUD-02 | 미해결 | prod의 landmark fetch 그대로 | 서버 reference와 정답 없는 UX | [PROD][PROD], [SERVER][SERVER] |
| AUD-03 | 부분 | prod Math.random sort 유지; lab은 secrets.choice | 실제 발급에 안전한 배정·pool 부족 실패 연결 | [PROD][PROD], [SERVER][SERVER] |
| AUD-04 | 보존 | 기존 5-MCP 평균 baseline 수식 유지 | M0 버전/계보를 명시해 비교 | [LEGACYMASK][LEGACYMASK], [POOL][POOL] |
| AUD-05 | 부분 | Stage6 중점 원 수식·2D 계산 | M0/M1 manifest 버전·새 파라미터 검증 | [H6][H6], [POOL][POOL] |
| AUD-06 | 미해결 | w3>1 손목 충돌 회귀를 보존 | 목표 ROI/수식/외부 단서 조건 합의 | [H7][H7], [HGATETEST][HGATETEST] |
| AUD-07 | 개선됨 | Stage6/7 가림 수식은 x/y만 사용 | 전체 adapter·모든 경로로 일반화하지 않음 | [H6][H6], [H7][H7] |
| AUD-08 | 개선됨 | 미검출을 Stage7 전체 분모에 포함 | 운영 출하 gate 및 다른 경로 통합 | [H7][H7], [HTEST][HTEST] |
| AUD-09 | 개선됨 | Stage6 모든 mask 사전 확인·실패시 결과 미게시 | 별도 bake/legacy 경로도 같은 정책 적용 | [H6][H6], [HTEST][HTEST], [BAKE][BAKE] |
| AUD-10 | 부분 | Stage6은 비연속/역재생 인덱스를 거부 | 실제 filter/reverse 영상·mask·정답·PTS 재매핑 | [H6][H6], [STAGE4][STAGE4], [QUALITY][QUALITY] |
| AUD-11 | 미해결 | run_batch는 Stage6 호출 없음 | 최종 renderer·검증·immutable manifest 연결 | [PIPE][PIPE] |
| AUD-12 | 미해결 | forward+reverse 및 len/fps 계산 | 실제 PTS 길이 gate·목표 범위 판정 | [STAGE4][STAGE4], [CONFIG][CONFIG] |
| AUD-13 | 미해결 | 전체 배치의 open-hand median 추정 유지 | train-only 추정·원본/촬영자 균형·중복 제거 | [WEIGHTS][WEIGHTS], [PIPE][PIPE] |
| AUD-14 | 미해결 | handedness 분류 score를 confidence로 사용 | 방향 분류 확신과 landmark 품질 분리 | [EXTRACT][EXTRACT], [QUALITY][QUALITY] |
| AUD-15 | 미해결 | legacy 복사 편입 구조 유지 | Stage2/3/7·최종 byte·권리 관문 동일 적용 | [INGEST][INGEST] |
| AUD-16 | 미해결 | 없는 export_pool의 import 유지 | 모듈/계약 복구·실행 전 의존성 확인 | [INGEST][INGEST] |
| AUD-17 | 미해결 | 별도 bake는 !pip Colab 셀 형식 | CLI 패키징·adopted_clips/filter 계약 | [BAKE][BAKE] |
| AUD-18 | 미해결 | 별도 bake의 last mask 재사용 경로 유지 | 모든 frame mask·임시/원자 게시·누락 격리 | [BAKE][BAKE] |
| AUD-19 | 미해결 | 별도 H264 후 1:1 프레임 가정 유지 | 최종 H264 재decode·PTS/개수/가림 검사 | [BAKE][BAKE] |
| AUD-20 | 미해결 | config에 미검증 placeholder 표시 유지 | 실제 dev 자료의 실행값/근거/잠금 기록 | [CONFIG][CONFIG] |

## 출하 인수 T01~24의 실제 검증 범위

| ID | 현재 판정 | 확인한 것 / 전달본의 기여 | 남은 정확한 작업·한계 | 근거 |
|---|---|---|---|---|
| T01 | 미실행 | 권리 UNKNOWN 거부는 명세 | 권리 대장·release validator·실패 fixture | [POOL][POOL] |
| T02 | 미실행 | prod는 전체 manifest와 정답을 fetch | 정답 없는 client bundle·응답 allowlist 검사 | [PROD][PROD], [POOL][POOL] |
| T03 | 부분 | Stage6 누락 공통 거부 및 중간 누락 명시적 검사 | 첫/끝 누락 별도 실행·모든 경로의 격리/송출 검사 | [H6][H6], [HTEST][HTEST], [BAKE][BAKE] |
| T04 | 부분 | 미검출을 분모에 포함하고 renderer가 거부 | 실제 출하 승격 경계까지 연결 | [H7][H7], [HTEST][HTEST], [PIPE][PIPE] |
| T05 | 부분 | 2D 수식 코드와 큰 z circle 회귀 존재 | x/y 동일 z변경의 raster·gate 양쪽 명시적 동등성 검사 | [H6][H6], [H7][H7], [HTEST][HTEST] |
| T06 | 부분 | 비연속 원본 인덱스 거부 검사 | 삭제/역재생/시간변형을 실제 동기화하는 mapping | [H6][H6], [STAGE4][STAGE4] |
| T07 | 부분 | 임시 출력·재decode·실패시 미게시 및 기존파일 보존 | encoder 실패 주입 전 범위와 RELEASED 승격 금지 연결 | [H6][H6], [HTEST][HTEST], [PIPE][PIPE] |
| T08 | 부분 | 합성 MP4 전체 count/dimension/내부 픽셀 검사 | PTS 단조성·duration·모든 최종 rendition/실자료 기대값 | [H6][H6], [HTEST][HTEST] |
| T09 | 미실행 | Stage6 하나의 MP4만 생성 | poster/thumbnail/다중 track/오디오/metadata 전수 검사 | [POOL][POOL], [H6][H6] |
| T10 | 미실행 | legacy 재편입 자동 우회 구조 유지 | 동일 관문 실행·예외 제거 | [INGEST][INGEST] |
| T11 | 부분 | lab의 안전한 경로·media session 검사 | 운영 private origin/목록·기존 공개 답 회수 불가 고려 | [SERVER][SERVER], [PROD][PROD] |
| T12 | 부분 | 기존 lab에 만료/다른 session 검사 | tenant·REVOKED/release 정책 포함 실제 서비스 시험 | [SERVER][SERVER], [G4REVIEW][G4REVIEW] |
| T13 | 미실행 | 운영 CDN/warm cache 경계 없음 | 캐시 적중 상태에서도 무권한 반환 차단 시험 | [POOL][POOL], [SERVER][SERVER] |
| T14 | 미실행 | lab media 응답은 완전한 운영 Range 인수 아님 | 승인 세션 Range/seek/retry와 제한 우회 시험 | [SERVER][SERVER], [POOL][POOL] |
| T15 | 기존 로컬 완료 | in-process 세션·일회 소비/동시 회귀 근거 존재 | 다중 worker·DB·영속 소비까지 확대하려면 별도 시험 | [SERVER][SERVER], [G4STATE][G4STATE], [G4TEST][G4TEST] |
| T16 | 기존 로컬 완료 | lab은 client passed를 신뢰하지 않고 실제 함수 재계산 | prod 연동·capture trust와 혼동하지 않음 | [SERVER][SERVER], [G4TEST][G4TEST], [PROD][PROD] |
| T17 | 기존 반례 확인 | 공개 lookup의 성공/취약 신호 기록 | 새 source/사전 상한에 대한 새 후보 판정; 방어 통과로 표기 불가 | [G4REPORT][G4REPORT], [G4REVIEW][G4REVIEW] |
| T18 | 미실행 | 여러 마스크의 누적 복원은 설계 | 같은 source mask 정렬·합성 공격과 한계 기록 | [POOL][POOL] |
| T19 | 미실행 | 카드만 작성 | 동일 조건 사람/공격 대응·가림 추가효과·UX 측정 | [CARDS][CARDS], [VALIDATION][VALIDATION] |
| T20 | 부분 | 제공된 source/participant/capture ID 중복 검사 | 실제 계보·perceptual/trajectory 중복·촬영자 파생본 검증 | [COMPARE][COMPARE], [POOL][POOL] |
| T21 | 미실행 | 독립 시연은 채점이 없어 대체 증거 아님 | 정답 fetch 제거 후 generic guide·서버 gate로 완료 | [PROD][PROD], [DEMO][DEMO], [POOL][POOL] |
| T22 | 미실행 | retired/revoked artifact 관리 명세 | 신규 발급 금지·활성 challenge/캐시 무효화 | [POOL][POOL], [SERVER][SERVER] |
| T23 | 미실행 | 발급 부족/장애의 운영 대체 흐름 미완 | 승인 자산 부족·서버 실패 시 원본 없는 fallback 시험 | [POOL][POOL], [SERVER][SERVER] |
| T24 | 부분 | 코드 커밋·전달 manifest·검사 기록 있음 | 각 release의 입력/권리/검사·자산 버전 추적 완성 | [REVIEW][REVIEW], [PIPE][PIPE], [POOL][POOL] |

## 작업 패키지 WP0~5

| ID | 현재 판정 | 확인한 것 / 전달본의 기여 | 남은 정확한 작업·한계 | 근거 |
|---|---|---|---|---|
| WP0 | 문서 완료 | 기존 정적 감사·수식/정답 노출/연결 공백 기록 | 후속 변경의 상태를 이 감사로 보충 | [POOL][POOL], [ARCH][ARCH] |
| WP1 | 계획·입력 필요 | 권리/촬영/schema 요구와 카드 존재 | 실제 권리 대장·capture_protocol·split_manifest·schema 구현 | [POOL][POOL], [CARDS][CARDS] |
| WP2 | 부분 | Stage6/7 실패 중단·2D·최종 내부 검사는 구현 | frame/PTS mapping·recipe·run_batch 연결·immutable manifest·T03~10 | [H6][H6], [H7][H7], [PIPE][PIPE], [POOL][POOL] |
| WP3 | 기존 탐색+후속 미실행 | known-pool G4 결과를 재사용 | 권리/기하 통과 새 자료의 사람·공격·비용 비교와 release 후보 | [G4REPORT][G4REPORT], [POOL][POOL] |
| WP4 | 기존 로컬+후속 미실행 | loopback 서버·세션·보호 counter 존재 | 운영 private store·API·실제 client UX·T11~16/T21~24 | [SERVER][SERVER], [POOL][POOL] |
| WP5 | 미실행 | 운영 결정 규칙은 명세 | 제한 시험·반복 노출·고갈·대체 UX·운영/폐기 결정 | [POOL][POOL], [VALIDATION][VALIDATION] |

## 실용성 V0~V6의 26개 하위 항목

| ID | 현재 판정 | 확인한 것 / 전달본의 기여 | 남은 정확한 작업·한계 | 근거 |
|---|---|---|---|---|
| V0-01 | 부분 | 코드/전달 manifest 및 기존 lab run 기록 있음 | 새 필수 metadata validator·사전 code/config/split 잠금 | [REVIEW][REVIEW], [G4STATE][G4STATE], [VALIDATION][VALIDATION] |
| V0-02 | 기존 완료 유지 | 기존 lab은 L1/L2/로컬 L3 분리; CLI도 score_only 표시 | 실제 입력 보호 조건의 L3는 별도 확인 | [SERVER][SERVER], [G4REPORT][G4REPORT], [COMPARE][COMPARE] |
| V0-03 | 부분 | 카드 B 이벤트 계약·lab events 존재 | 완전한 attempts/global_frame/시간/실패/비용 수집기 | [CARDS][CARDS], [SERVER][SERVER], [VALIDATION][VALIDATION] |
| V0-04 | 부분 | CLI 오류/중단을 attempted 분모에 보존 | 전체 세션·재시도·timeout·missing 결과 경계값 집계 | [COMPARE][COMPARE], [VALIDATION][VALIDATION] |
| V1-01 | 기존 완료 유지 | 기존 G4에서 오답 판별 취약 질문을 탐색 | 새 정상 허용오차 검증은 새 자료로 별도 진행 | [G4REPORT][G4REPORT] |
| V1-02 | 기존 완료 유지 | oracle/정지/역전/다른 동작/invalid 회귀 근거 | 같은 목표의 새 정상 사람 자료 | [G4STATE][G4STATE], [G4TEST][G4TEST] |
| V1-03 | 부분 | 기존 산식 보존, 새 CLI validation threshold 선택 | 동일 trial 후보 특징·잠근 test·source별 confusion | [COMPARE][COMPARE], [G4REPORT][G4REPORT] |
| V1-04 | 기존 탐색 완료 | 기존 오답 유형·관문/점수·반례 보고 | 새 정상/오답 사전 하한·상한의 확증 판정 | [G4REPORT][G4REPORT], [VALIDATION][VALIDATION] |
| V2-01 | 부분 | source 구성요소·참가자·capture ID 검사 구현 | 미사용 원본 분할 manifest와 실제 독립성 증거 | [COMPARE][COMPARE], [CARDS][CARDS] |
| V2-02 | 기존 탐색+후속 미실행 | 공개/known-pool 공격군 기록 있음 | K0/K1 새 source와 공격군/예산별 실행 | [G4REPORT][G4REPORT], [VALIDATION][VALIDATION] |
| V2-03 | 문서 완료 | 동일 source·예산·노출 통제 명세 | 해상도/크기/코덱 등 대응 조건 실제 제작·시험 | [CARDS][CARDS], [VALIDATION][VALIDATION] |
| V2-04 | 기존 탐색 완료 | known-pool 반례·한계 판정 존재 | held-out·adaptive 새 평가를 별도 보고 | [G4REPORT][G4REPORT], [VALIDATION][VALIDATION] |
| V3-01 | 문서 완료 | 원문은 보호유무×과제없음/무가림/가림 2×3 | P조건 가능성 확인; 모방 2×2만 실행하면 축소 범위 명시 | [VALIDATION][VALIDATION] |
| V3-02 | 미실행 | 입력 보호 적합성의 조사 항목 정의 | 손 입력·세션 연결·지원환경·증명/위험신호·조건 비교 | [VALIDATION][VALIDATION] |
| V3-03 | 부분 | 로컬 좌표 제출·client 변조·만료/재사용 검사 | 실제 정상 카메라/가상 카메라/보호 도구 대응 시험 | [SERVER][SERVER], [G4STATE][G4STATE], [VALIDATION][VALIDATION] |
| V3-04 | 미실행 | 로컬 protected counter는 이미 검산됨 | O1-U1/P1 추가효과·정상 비열등성의 새 판정 | [G4REPORT][G4REPORT], [VALIDATION][VALIDATION] |
| V4-01 | 문서 완료 | 조건/순서/학습·동의 계획 카드 | 새 참가자·source 대응·접근성 절차와 수행 | [CARDS][CARDS], [VALIDATION][VALIDATION] |
| V4-02 | 문서 완료 | 첫 시도·완료·중단·전체 시간·도움 지표 정의 | 실제 이벤트 수집·실패 포함 시간/결과 집계 | [CARDS][CARDS], [VALIDATION][VALIDATION] |
| V4-03 | 미실행 | 완료율·부담 판정 규칙 존재 | 사전 수치 고정과 새 사람 결과 판정 | [VALIDATION][VALIDATION] |
| V5-01 | 미실행 | setup/attempt 상각·p=0 주의 공식 명세 | cold/warm·CPU/메모리/전송·반복 비용 실측 | [VALIDATION][VALIDATION] |
| V5-02 | 미실행 | 가림/검출/채점/서버/SDK 분리 계측 명세 | 장치별 비용·지연·실패 재시도 측정 | [VALIDATION][VALIDATION], [POOL][POOL] |
| V5-03 | 미실행 | 고객 순가치 공식 정의 | 측정/고객 제공 입력·민감도 분석 | [VALIDATION][VALIDATION] |
| V6-01 | 문서 완료 | 고객군·증거 필드·연락 단계 기준 존재 | 승인된 조사와 유효 고객 대화 기록 | [VALIDATION][VALIDATION] |
| V6-02 | 문서 완료 | 기존 인터뷰 질문지 있음 | 실제 인터뷰 실행·발언/해석 구분 | [VALIDATION][VALIDATION] |
| V6-03 | 미실행 | 계약/견적/사용권 범위 명세 | 평가 범위·예산·계약·지급의 실제 근거 | [VALIDATION][VALIDATION] |
| V6-04 | 미실행 | 관심/의사/지급·계속/중단 기준 존재 | 고객 증거 기반 의사결정 | [VALIDATION][VALIDATION] |

## 표준 채점 S1~S8 세부 항목

| ID | 현재 판정 | 확인한 것 / 전달본의 기여 | 남은 정확한 작업·한계 | 근거 |
|---|---|---|---|---|
| S1 | 미구현 | 표준 좌표/time/missing adapter 명세 | S1-01/02의 실제 입력 파서·fixture | [SCORE][SCORE], [COMPARE][COMPARE] |
| S1-01 | 미구현 | 폭/높이·한번만 mirror·퇴화 scale 계약 | 종횡비 보정·관절/미러 기하 adapter와 검산 | [SCORE][SCORE] |
| S1-02 | 부분 | 미분 primitive는 비유한/중복/gap 거부 | segment 시간→초·참조 frame/PTS·null 구간·resample adapter | [METRICS][METRICS], [SCORE][SCORE] |
| S2 | 기존 primitive | 실제 DP DTW·band·경로/cell budget 구현 | 실제 각도열·사전 grid/radius·오답/시간정렬 평가 | [METRICS][METRICS], [SCORE][SCORE] |
| S3 | 기존 primitive | 비균일 시각 gradient·단위 계약 구현 | 실자료 noise/FPS·평활화·gap 선택 및 ablation | [METRICS][METRICS], [SCORE][SCORE] |
| S4 | 부분 | 이미 산출된 두 점수를 비교 | 특징 추출·B0/B1/B2/B3 학습/평가 전 과정 | [COMPARE][COMPARE], [SCORE][SCORE] |
| S4-01 | 부분 | CSV human/attack label 요구 | wrong-human/attack-family/knowledge budget와 대응 계보 | [COMPARE][COMPARE], [SCORE][SCORE] |
| S4-02 | 미구현 | B0/B1/B2/B3 후보 명세 | B1 특징 산출·StandardScaler/LogisticRegression·ablation | [SCORE][SCORE] |
| S4-03 | 미구현 | ID 교집합 검사와 validation-only 선택은 있음 | 그룹 학습·fit 누출 방지·calibration·최종 test | [COMPARE][COMPARE], [SCORE][SCORE] |
| S5 | 부분 | threshold_table·운영점·validation 선택/집계 | 곡선·군집 CI·공격군별 최악값·실자료 평가 | [METRICS][METRICS], [COMPARE][COMPARE] |
| S6 | 미구현 | prod legacy gate와 카드 로그 계약 존재 | 시간 gap/coverage·구간 집계·저장 round-trip | [PROD][PROD], [CARDS][CARDS], [SCORE][SCORE] |
| S7 | 부분 | 기존 legacy와 새 합성 수학 검사 보존 | adapter→대응 trial→독립 평가→JS parity→shadow | [SCORE][SCORE], [REVIEW][REVIEW] |
| S8 | 부분 | 수학12·CSV7 검사와 재현 명령 있음 | 실자료 인수·JS/운영 전체 통과 조건 | [REVIEW][REVIEW], [SCORE][SCORE] |

## 손 선택·중첩 UI의 구현 계약

| ID | 현재 판정 | 확인한 것 / 전달본의 기여 | 남은 정확한 작업·한계 | 근거 |
|---|---|---|---|---|
| A-01 | 코드·합성 검사 | 여러 손의 유효 bbox·가장 큰 후보·동률 처리 | 실제 detector/부분 잘림·손 크기 기준 실증 | [SEL][SEL], [NTEST][NTEST] |
| A-02 | 부분 | 안정화·선택유지·소실 latch·명시적 전체 재시작 | 짧은 재연결·handedness/문제/gate/timer/log 통합 | [SEL][SEL], [DEMO][DEMO], [UI][UI] |
| A-03 | 코드·합성 검사 | 시작/안정화/선택/소실 안내와 다시선택 버튼 | 실제 사용자 이해도·문구 선택 | [DEMO][DEMO], [HTML][HTML] |
| A-04 | 부분 | 순서·크기·교차·소실·배열재사용 합성 검사 | 수용 사례6의 좌우손·문제·gate·기록 초기화 및 실기7종 | [NTEST][NTEST], [PROD][PROD] |
| B-01 | 코드·합성 검사 | 카메라 위 가림 문제를 겹치는 시연 | 시선/대응 부담 감소의 실제 검증 | [DEMO][DEMO], [HTML][HTML], [UI][UI] |
| B-02 | 부분 | 분리/중첩·투명도·반전·종횡비·원본 검출 | 실제 좌우손/장치·기존 채점/time 조건 통합 | [DEMO][DEMO], [HTML][HTML], [PROD][PROD] |
| B-03 | 문서·부분 구현 | 손 테두리·투명도·안내로 일부 혼동 대응 | 배경·가림·정렬 혼동과 실제 수행 관찰 | [UI][UI], [DEMO][DEMO] |
| B2 | 계획·부분 구현 | AI 안내 후보6종과 상태안내 일부 | 연구자 소수 후보 선택 기록·추가 UI·비교 | [UI][UI], [CARDS][CARDS] |
| E1 | 문서 완료 | 조건/행동/이벤트 수집 계약 카드 B | 의도한 손 정답·first-correct 기준 잠금·실제 logger | [CARDS][CARDS] |
| E2 | 미실행 | 채택/수정/보류 기준 설계 | 비식별 비교 결과·선택 이유 | [CARDS][CARDS], [UI][UI] |

## 손 선택 수용 사례 7종

| ID | 현재 판정 | 확인한 것 / 전달본의 기여 | 남은 정확한 작업·한계 | 근거 |
|---|---|---|---|---|
| CASE-1 | 합성 검사 | 작은 손 선검출과 무관하게 큰 유효 손 선택 | 실제 카메라의 여러 손 반환 검증 | [NTEST][NTEST] |
| CASE-2 | 합성 검사 | 검출 배열 재정렬에도 선택 유지 | 실제 손 움직임/추적 품질 | [NTEST][NTEST] |
| CASE-3 | 합성 검사 | 더 큰 먼 distractor 등장에도 유지 | 가까운 유사 손의 오연결 평가 | [NTEST][NTEST], [SEL][SEL] |
| CASE-4 | 합성 검사 | 비슷한 크기/교차 모호성에서 임의 연결 거부 | 실제 교차·가림 자료의 민감도 | [NTEST][NTEST] |
| CASE-5 | 합성 검사 | 선택 손 소실시 남은 손으로 진행 안 함 | 실제 timeout·gate·점수 처리 연결 | [NTEST][NTEST], [PROD][PROD] |
| CASE-6 | 부분 | 페이지 reload로 시연 전체 초기화 | 선택 손 handedness·문제 방향·관문·기록 일관성 | [DEMO][DEMO], [PROD][PROD] |
| CASE-7 | 부분 | 단일 손의 작은 이동 선택 유지 합성 검사 | 기존 prod 수행 흐름에 통합 후 회귀 | [NTEST][NTEST], [PROD][PROD] |

## AI 안내 후보 6종

| ID | 현재 판정 | 확인한 것 / 전달본의 기여 | 남은 정확한 작업·한계 | 근거 |
|---|---|---|---|---|
| OPT-1 | 후보 | 짧은 시작 시범 목록 | 연습용 다른 동작의 시범 구현·학습효과 통제 | [UI][UI] |
| OPT-2 | 부분 구현 | 상태별 한 문장 안내 있음 | 과제/관문 단계 안내 통합과 비교 | [DEMO][DEMO], [UI][UI] |
| OPT-3 | 후보 | 큰 주화면+작은 보조화면 명세 | 작은 보조창 UI·중첩과 대응 비교 | [UI][UI] |
| OPT-4 | 부분 구현 | 선택 손 테두리 있음 | 문제 재생/관문 순간 강조와 실제 이해 검증 | [DEMO][DEMO], [UI][UI] |
| OPT-5 | 후보 | 별도 연습 모드 목록 | 채점 설명 연습 구현·전체 부담 측정 | [UI][UI] |
| OPT-6 | 후보 | 선택형 도움말 목록 | 요청형 도움/시범 구현·선택 편향 고려 | [UI][UI] |

## 손동작 자동 생성 세부 실행 항목

| ID | 현재 판정 | 확인한 것 / 전달본의 기여 | 남은 정확한 작업·한계 | 근거 |
|---|---|---|---|---|
| GEN3D-01 | 설계만 | 장면 변수·seed·generator_version·정답 비공개 명세 | 손/물체/카메라/trajectory/contact 생성과 manifest | [THREED][THREED], [GEN][GEN] |
| GEN3D-02 | 설계만 | 관절/속도·접촉·비관통·사람 편안함 계약 | 기하/물리 자동 검사와 사람 수행 검사 | [THREED][THREED], [GEN][GEN] |
| GEN3D-03 | 설계만 | 물체 단서가 답을 바꾸는 대응쌍 명세 | scene 생성·허용 답·사람/공격 인과 비교 | [THREED][THREED] |
| GEN3D-04 | 설계만 | 가림 렌더만 송출·buffer/seed 누출 금지 | renderer·가림·그림자/반사/코덱 검사·송출 | [THREED][THREED] |
| SCORE3D | 설계만 | G0는 2D 모사, 가상 접촉을 실측으로 채점하지 않음 | 투영 참조·웹캠 불확실성·복수 답 집합·서버 평가 | [THREED][THREED] |
| EVAL3D | 설계만 | B0~B3와 A1~A4·family holdout 비교 | 실제 scene/사람/강한 공격·비용 실행 | [THREED][THREED] |
| R1-1 | 미실행 | Text2HOI 원형 재현 전제 목록 | 공식 code/checkpoint/data/model 권리·환경 manifest | [GEN][GEN] |
| R1-2 | 미실행 | 원형 전처리 절차 명세 | 허용 GRAB/H2O/ARCTIC 등 실제 준비·전처리 로그 | [GEN][GEN] |
| R1-3 | 미실행 | VAE contact→diffusion→refiner 구조 명세 | 공식 demo/checkpoint 실행·원 출력 보존 | [GEN][GEN] |
| R1-4 | 미실행 | 원 논문 과제/분할 평가 계약 | 다양성·자연성·접촉·관통 원형 평가 | [GEN][GEN] |
| R1-5 | 미실행 | 원형 성공 후 CAPTCHA 전용 단계 명세 | G0 필터·렌더/가림·byte검사·발급 adaptation | [GEN][GEN] |
| P1-1 | 미실행 | 촬영 2~3 family 기반 자체 파일럿 제안 | 원본 대응 자세·시간·접촉 범위 자료 | [GEN][GEN] |
| P1-2 | 미실행 | 자체 skeleton+primitive·제한 변형 설계 | 기본 손·물체·grasp/contact 계획·trajectory 구현 | [GEN][GEN] |
| P1-3 | 미실행 | 수율/지연/가림 유효성 측정 목표 | 후보 생성→기하검사→렌더/가림→탈락사유/CPU 측정 | [GEN][GEN] |
| P1-4 | 미실행 | 촬영 V0·제한변형 V1·자체 V2·원형 V3 비교 | 대응 source/family·사람/공격·비용의 실제 비교 | [GEN][GEN] |
| GEN-RELEASE | 미실행 | 품질·권리·사람·강한 공격·비용 도입 관문 | 생성된 최종 자산과 전체 증거/비공개 서버 경계 | [GEN][GEN], [THREED][THREED], [POOL][POOL] |

## 손등 대신 손바닥을 카메라로 향하게 돕는 UI 설계

사용자 추가 요구: 설계대로 손바닥 쪽을 카메라에 보이게 한다. 이 절은 기존 190행 감사 이후 추가한 UI 후보이며, 사용자 효과가 검증됐다는 뜻은 아니다. [순차 구현 기록](2026-11-04_execution_progress.md)에서 실제 구현 상태를 이어서 관리한다.

현재 prod의 angle_mismatch 문구는 손바닥을 카메라로 향하도록 안내한다. 반면 dataset_pipeline/stage3_frontality.py의 frame_theta는 normal 각도를 접어 손바닥과 손등을 모두 정면으로 취급한다. 손 윤곽·2D 점 배열이 비슷할 수 있으므로 “정면 손 검출”과 “손바닥 확인”을 구분해야 한다. 문구·그림·자가 확인은 안내이며 자동 검증/인증이 아니다.

| ID | UI 아이디어 | 구체적인 동작 | 확인할 효과와 주의점 |
|---|---|---|---|
| PALM-UI-01 | 손금 기준의 한 문장 안내 | “손금이 보이는 쪽을 카메라 렌즈로 향해 주세요.”를 시작 전·선택 손 화면에 표시 | 사용자가 화면 속 문제 손을 어느 쪽으로 복제할지보다 자신의 손 면을 먼저 이해하는지 |
| PALM-UI-02 | 손바닥 그림과 작은 손등 예시 | 손금이 있는 열린 손바닥을 크게, 손톱이 보이는 손등을 작은 비교 그림으로 표시 | 손 실루엣만으로 앞뒤를 혼동하지 않는지; 좌우손 그림을 모두 제공 |
| PALM-UI-03 | 준비용 카메라 미리보기 | 문제 영상 재생 전에 카메라만 보면서 손 면을 맞추는 단계 | 준비/권한 시간을 과제 제한시간과 분리; 점수 결과로 손 면을 추정하지 않음 |
| PALM-UI-04 | 짧은 손목 회전 시범 | 별도의 연습 손으로 손등→옆면→손바닥이 되는 과정을 짧게 보여 줌 | 본 문제의 가려진 정답이나 자세를 시범으로 노출하지 않음 |
| PALM-UI-05 | 손바닥 방향의 명시적 자가 확인 | “카메라에 손금이 보이는 쪽을 보였습니다” 확인 후 시작 가능 | 사용자의 확인이며 자동 판정이 아니라는 기록 유지; 확인을 보안 증거로 사용하지 않음 |
| PALM-UI-06 | 방향 전용 피드백 | 검증된 판정기가 생기면 손바닥/손등/측면/불확실을 구분 | 불확실을 손등으로 단정하지 않고 재배치 안내; 임의 left/right 부호 규칙 금지 |
| PALM-UI-07 | 손바닥 내부의 기준 표시 | 정답과 무관한 손바닥 중심 원·손금 표식이 있는 가이드를 카메라 옆에 표시 | 현재 손의 위치/크기와 방향을 따로 설명; 손 윤곽 맞추기를 채점 과제로 오해하지 않게 함 |
| PALM-UI-08 | 좌우손·미러 일관성 | 왼손/오른손 선택에 맞는 그림과 “손금 쪽은 그대로” 문구 | 화면 반전과 손 앞뒤 뒤집기를 혼동하지 않도록 실제 좌우손 조건 검증 |
| PALM-UI-09 | 손등을 보였을 때 회복 도움 | “손목을 편하게 돌려 손금 쪽을 렌즈에 보여 주세요”와 다시 준비 버튼 | 불편한 과회전 강요 금지; 통증/가동 제한 시 쉬기·대체 경로 제공 |
| PALM-UI-10 | 선택형 음성·큰 글씨 | 같은 짧은 안내를 사용자가 요청하면 읽거나 큰 글씨로 표시 | 소리 자동 재생에 의존하지 않음. 자막·그림·색 이외 표식 유지 |
| PALM-UI-11 | 짧은 연습 후 본 시도 | 손바닥 보이기→선택 손 표시→문제 따라 하기 순서를 정답 없는 연습으로 경험 | 본 시도에 연습 로그/좌표를 이어 붙이지 않고 새 trial로 시작 |
| PALM-UI-12 | 도움 요청·방향 오류 기록 | 안내 조건·도움·자가확인·시작·소실·재시작·중단을 상대시간으로 기록 | 원영상/개인 좌표 기본 저장 없이, 별도 관찰로 정한 손 면을 정답으로 사용 |

후속 [12종 평가와 선정 기록](2026-11-04_palm_ui_evaluation.md)에 따라 PALM-UI-01 한 문장·02 앞뒤 비교 그림·03 카메라 준비 단계를 세 주 기능으로 구현했다. 05 자가 확인과 08 좌우손 그림은 이들의 보조 조작이다. 안내 자체와 자동 손바닥 판정은 별개 작업이다. 자동 판정은 정면·좌우손·미러·측면·주먹·부분 가림에서 별도 정답 주석/불확실 처리 검증이 필요하다.

평가는 기존 분리/중첩 비교와 한꺼번에 바꾸지 않는다. 같은 손 선택·동작·채점 아래 안내 조건만 바꾸고, 첫 손 면 오류, 올바른 손바닥 제시까지 시간, 도움/재시도·포기, 전체 완료시간과 불편감을 기록한다. 손바닥을 보였는지는 관찰 기준으로 별도 정의한다. 높은 점수나 bbox 크기를 올바른 손 면의 정답으로 쓰지 않는다. 새 사람 자료가 없으면 구현·합성 확인까지만 완료로 표시한다.

## 이후 진행 순서

현재 결과를 기준으로 구현할 때에는 다음 의존성을 따른다. 이 감사는 아래 작업의 실행 결과를 새로 만든 것이 아니다.

1. 기존 G1~G4 근거와 역사적 baseline을 보존한다. 이미 수용된 재현/분석을 다시 완료 조건으로 만들지 않는다.
2. 가림 경로는 수식/ROI 충돌 결정→원본/출력 PTS mapping→별도 bake/legacy 정비→run_batch/immutable artifact 연결 순으로 묶는다.
3. 손 선택은 시연의 실제 카메라 확인→handedness/문제/gate/timer/로그 통합→동일 UI에서 선택 정책 비교→같은 선택 정책의 UI 비교 순으로 구분한다.
4. 점수 비교는 표준 adapter→동일 trial의 B0/B1 점수→계보가 잠긴 validation/test→군집 불확실성/공격군별 결과→필요한 B2/B3→Python/JS parity/shadow 순으로 진행한다.
5. 자동 생성은 G0 과제/동작 family와 원본/허용 자산을 정한 후 P1 자체 skeleton/primitive 파일럿과 R1 원형 재현을 각각 진행한다. 둘의 성과를 섞지 않고 촬영 기준선과 비교한다. 권리/자료/자원이 필요한 항목은 필요한 입력을 명시한다.
6. 새 사람·미사용 source·강한 공격·입력 보호·비용의 대응 자료가 확보된 뒤 운영/계속 여부를 결정한다. 생성 seed 수나 영상 변형 수만으로 독립 문제 수/보안 향상을 계산하지 않는다.

## 추적 행과 검토 범위 파일

같은 폴더의 `2026-11-04_completion_matrix.json`에 위 190개 행과 현재 tree 검색 범위·ref/SHA·근거 URL을 보관한다. 누락 검사는 통합 백로그 62개, AUD20개, 인수24개, V하위26개를 원문 ID 순서와 대조했다. 다른 묶음도 개수와 ID 중복을 확인했다. 이 무결성 점검은 요구사항의 구현 완료 검사가 아니다.

[BACKLOG]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/backlog_2026-11-03.md
[INDEX]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/backlog_source_index_2026-11-03.md
[REVIEW]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/deliveries/2026-11-03_review.md
[CARDS]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/experiment_cards_2026-11-03.md
[EXPLAIN]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/research_explanation_2026-11-03.md
[G3]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/reproducibility/g3_dr3_fr5_researcher_update_2026-10-28.md
[LINEAGE]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/reproducibility/prod_v2_source_lineage_correction_2026-10-26.md
[RECOVERY]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/RECOVERY_TARGETS.md
[DICT]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/data_dictionary.md
[G4STATE]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/g4_actual/g4_progress_state.md
[G4REPORT]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/g4_actual/g4_final_report.md
[G4REVIEW]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/g4_actual/g4_independent_review.md
[G4TEST]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/g4_actual/g4_test_results.md
[ROADMAP]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/research_roadmap_2026-11-02.md
[UI]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/hand_selection_and_overlay_ui_proposal_v0.1_2026-11-02.md
[FOLLOWUP]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/followup_experiments.md
[SCORE]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/scoring_standardization_v0.3.md
[VALIDATION]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/practical_validation_requirements_v0.3.md
[POOL]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/video_pool_occlusion_delivery_requirements_v0.4.md
[THREED]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/3d_hand_object_challenge_requirements_v0.1.md
[CLAIM]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/claim_evidence_matrix.md
[REPRO]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/reproduction.md
[OVERLAP]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/docs/reproducibility/g4_human_attack_pool_overlap_2026-10-26.md
[COMPARE]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/validation_v03/compare_scores.py
[METRICS]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/validation_v03/standard_metrics.py
[CTEST]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/tests/test_compare_scores.py
[SERVER]: https://github.com/mukgore/codex/blob/916cc6fd0febe7f94115c94ff16b8abc10c46e4a/g4_lab/server.py
[SEL]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/experiments/hand_selection/selection.js
[DEMO]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/experiments/hand_selection/demo.js
[HTML]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/experiments/hand_selection/index.html
[NTEST]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/experiments/hand_selection/selection.test.cjs
[DEMOTEST]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/experiments/hand_selection/demo.test.cjs
[H6]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/stage6_occlusion.py
[H7]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/stage7_gate.py
[HTEST]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/tests/test_mask_delivery.py
[HINTEGRITY]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/tests/test_mask_integrity.py
[HGATETEST]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/tests/test_stage7_gate.py
[PIPE]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/pipeline.py
[PROD]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/hand_captcha_prod.html
[MANIFEST]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/pool_manifest.json
[LEGACYMASK]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/handtest1.py
[CONFIG]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/config.py
[WEIGHTS]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/stage5_weights.py
[EXTRACT]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/stage1_extract.py
[QUALITY]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/stage2_quality.py
[STAGE4]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/stage4_length_norm.py
[INGEST]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_pipeline/ingest_experiment_folders.py
[BAKE]: https://github.com/mukgore/handcaptcha/blob/6d9201296b3c4341b555845868ae15fd5f5ada8b/dataset_expansion_bake_v1.py
[GEN]: https://github.com/mukgore/codex/blob/b8c39d5b4453865e1eca1106976406447b588a3a/docs/hand_motion_source_and_generation_research_v0.1.md
[ARCH]: https://github.com/mukgore/codex/blob/e4e918b606f3b0626a54cae96c78743924062ab7/docs/captcha_architecture_and_repo_audit_2026-10-26.md
