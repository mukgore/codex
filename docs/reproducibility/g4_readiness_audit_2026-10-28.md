# G4 준비 감사 및 다음 실행 계약 초안 — 2026-10-28

상태: 준비 감사. G3 재검증이나 G4 신규 평가가 아니며, 실행 승인서가 아니다. 이 비식별 기록에는 참가자별 원자료, 식별자, 로컬 경로·파일명, 입력 해시를 포함하지 않는다.

후속 기록: 이 문서는 A·B 준비 시점의 상태를 보존한다. 이후 별도 승인으로 수행한 실제 코드 탐색·국소 방어는 [G4 실제 코드 보고서](../g4_actual/g4_final_report.md)에 있다. 해당 후속 실행과 이번 공개 발행 승인으로 아래 준비 시점의 실행 제한을 소급 변경하지 않는다.

기준 문서와 코드: GitHub `mukgore/codex` main `76bd22d406f1e1d8efba54207dcb27094522755a` (2026-10-28). 로컬 작업 사본은 `ca00cf7fc9deb57f105ad592343d18483ccd7d6c`이며 원격보다 28개 커밋 뒤에 있다. 원격 main은 읽기 전용으로 `FETCH_HEAD`까지 조회했다. checkout, merge, pull, commit, push는 하지 않았다. 문서 작성 시점 로컬 변경은 이 새 문서뿐이다.

## G3 종료 상태와 잔존 한계

연구자는 G3를 종료하기로 결정했다. 이 종료는 DR4·DR6·FR5 등 과거 증거 한계를 소급 제거하지 않는다.

- DR3: 관찰된 18개 세션의 segment/frame 분모 차이는 콜백 순서와 first-segment 로그 경계로 설명된다. null 이벤트의 고유 대응 및 정확한 이벤트 시각 재구성은 여전히 불가능하다.
- DR4·DR6: 채택된 지표의 재생은 당시 확인한 후보 코드와 자료에 조건부로 일치했지만, 각 과거 세션의 실제 build/runtime/pool 연결은 입증되지 않았다. 미검증 후보 지표를 검증된 값으로 취급하지 않는다.
- FR5: 과거 인간 자료로 기준을 만들고 뒤 단계에 변경 없이 적용했다는 것은 연구자 설명이다. 선행 자료에 독립 holdout이 없고 동시대의 기준 잠금 기록도 확인되지 않았다. 이후 단계 적용이 독립 표본 검증임을 단정하지 않는다. 제외된 13개 민감도 시나리오는 연구 근거나 preregistration으로 재해석하지 않는다.
- G3 기존 해석: 사람 18세션과 HaMeR 28조합의 점수 통과 차이는 cohort 및 독립성 한계 안에서만 해석한다. 28조합은 8개 원동작을 공유하며, 실제 전체 인증 성공을 측정한 결과가 아니다.

## 저장소 및 실행 환경

- 로컬 HEAD와 `origin/main`: 위와 같이 28개 커밋 차이. 조사 전 작업 트리는 clean이었다. fetch 후에도 추적 파일 변경은 없었다.
- 쓰기 경계: 현재 CLI 작업공간 안에서만 파일을 만들 수 있다. CAPTCHA 자료 폴더는 조사 중 읽기만 했다. 원본 자료, CAPTCHA HTML, 기존 출력은 수정하지 않았다.
- Computer Use: `cua_repl` 연결 자체는 사용 가능했다. 런타임의 browser inventory는 빈 목록, app inventory에는 열린 NAVER Whale 창이 있었다. 해당 창 선택은 `window id ... no longer belongs to Naver_Whale; current owner is Naver_Whale` 오류로 실패했고, 화면/AX 읽기 성공 여부를 확인할 수 없었다. 재열거에서도 동일한 창 ID/제목을 반환했다. 따라서 원인은 확정하지 않는다. 브라우저 provider 미노출과 창 바인딩/소유권 불일치까지가 관찰된 실패 단계다. 실제 페이지 상호작용은 없었다.
- 사용 도구 식별: Computer Use skill 번들은 `26.1021.31345` 경로에 설치되어 있다. 이 값은 번들 버전이며, 실행 중인 cua/sky 런타임의 정확한 버전은 응답에 노출되지 않았다. 최초 실패 응답은 위 창 선택 오류다. 앱/browser inventory 호출은 성공했다.
- 다른 방법: 로컬 venv에 Python 3.10 계열과 OpenCV, NumPy, MediaPipe가 있으며 오프라인 재생 산출물도 있다. Playwright·Selenium·Pyppeteer Python 패키지는 탐색되지 않았다. 이는 브라우저 바이너리나 Node 도구의 부재를 뜻하지 않는다. 정적 코드 검사 및 기존 로컬 replay 검증기는 확인된 대체 경로지만 gate나 L3를 측정하지 않는다. CUA 브라우저 연결이나 승인된 staging/evaluator endpoint는 이번 환경에서 확인되지 않았다.
- 환경 진단 중 CAPTCHA를 풀거나 제출하지 않았고, 카메라 허용·결과 POST·외부 전송을 하지 않았다.

## 기존 G4 자료의 재사용 범위

| 자료 | 재사용할 수 있는 증거 | 새 평가로 셀 수 없는 것 |
|---|---|---|
| 2026-10-24 랜드마크 재구성 재생 (8개 source, 조건별 8행) | 보존된 입력/코드에 대한 오프라인 재현성, 저장된 안정 지표의 재계산 | 새 source 평가, gate 성공률, 독립 일반화, 원 크기만의 인과효과, L3 인증 |
| 2026-10-24 피부-bit/reference lookup (8개 source에서 forward 관측 및 파생 reverse, 16 평가) | 같은 8개 source를 공유하는 closed-set 식별·점수 재생 결과; 독립 재계산은 top-1 14/16, 점수 threshold 통과 16/16으로 저장 결과와 허용 오차 내 일치 | held-out 성능 또는 공격 성공률 추정. reference와 평가 challenge가 같은 원동작을 공유하고 reverse는 독립 source가 아님 |
| 인간 기록 및 pool 연결 조사 | 일부 인간 기록과 공격 자료가 같은 pool clip ID 집합을 참조한다는 계보 단서; 지표 수식 호환성 검토 | 동일 challenge/build/방향 조건의 paired 비교. 일부 sessionLog cohort는 7개 공격 label과 겹치지만 균형/완전 대응이 아니며 reference도 같은 pool을 포함 |
| 기존 구현·정적 페이지 분석 | 현재 후보의 클라이언트 채점/업로드 경로와 정답 노출 가능성 점검 | 서버가 보호 동작을 허용하는 L3 endpoint. 실제 endpoint 로그가 보존되지 않음 |

기존 오프라인 결과는 기존 결과로만 인용하고 분모를 합산하지 않는다. 같은 오프라인 재생을 다시 실행해도 신규 G4 평가가 되지 않는다.

## G4 연결 가능성 및 준비 판정

| 요소 | 현재 확인 | 준비 상태 |
|---|---|---|
| Source family | 공격/참조 자료는 8개 원동작에서 유래하며 reference에도 이 source가 포함된다. 인간 기록과 pool clip ID의 일부 겹침은 확인됐으나 자료 전반의 family/파생본 manifest는 미완성이다. 다른 후보 영상은 기존 source와 직접 연결되지 않았지만 독립 holdout임을 증명하지 못했다. | 기존 same-pool 분석에는 조건부 연결 가능. 독립 평가 split은 미준비 |
| Challenge | 과거 기록 일부가 pool ID로 연결된다. 동일 challenge, 화면·전환·방향·시도 한도와 당시 build/runtime를 보장하는 대응표는 없다. | 기존 자료의 탐색 비교에 한정 |
| Reference library | 평가 대상 8개 원동작을 포함하는 저장 reference가 있다. | closed-set 재현에는 가능. holdout reference 분리는 불가 |
| Human/attack data | 인간 18세션, 별도 sessionLog cohort, 공격 재생 자료가 보존돼 있다. 코호트·단위·challenge lineage는 동일하지 않다. | 비식별 스키마/분모 감사와 탐색 요약은 가능. 신규 paired 비교로 합치지 않음 |
| Gate | 생산 후보 코드에는 자세/지속시간 gate가 있으나 기존 offline replay 산출물은 실시간 gate endpoint 기록이 아니다. | 저장 산식의 정적 검토 가능. 실제 gate endpoint 평가 불가 |
| Score | 기존 클라이언트 점수와 공격 재생용 호환 산식이 확인됐다. 저장 threshold·weight는 역사적 baseline이며 v0.3은 새 임계값을 별도 validation split에서 선택하도록 요구한다. | 기존 score replay 검증 가능. 새 기준 선택/held-out 판정은 미준비 |
| L3 end-to-end | 실제 보호 동작을 허용·거부하는 격리 endpoint 또는 로그가 확인되지 않았다. | 기술적으로 미준비; staging 또는 소유자 승인 시험 endpoint 필요 |

## FR6 및 v0.3 V0–V3 최소 실행 프로토콜 초안

이 초안은 데이터·도구와 연구자 선택이 채워진 후 별도 승인받아야 한다. 성공률, 표본 수, 자원 상한, threshold를 임의로 정하지 않는다.

1. **V0 공통 기반:** 자료/코드/설정 버전과 source-family lineage를 비공개 manifest로 고정한다. 원본, crop, mirror, 방향 반전, 변형, 재인코딩, 동일 촬영자/세션 파생물을 family 수준에서 연결하고 near-duplicate 누출을 검사한다. gate, score, L3 endpoint를 각각 별도 시도 행·분모로 기록한다. 모든 시도, timeout, 검출 실패, 취소, 기술 오류를 보존한다.
2. **V1 기존자료 채점 반례 회귀:** 기존 자료에서 의도한 답/틀린 답 및 저장 가능한 기존 오류 사례를 지정한다. 역사적 점수/gate 계산과 v0.3 표준화 후보를 버전별로 비교하고, 방향·단위·누락·구간·임계값 적용을 검증한다. 이 단계는 채점기의 회귀·closed-set 진단이지 held-out 공격 평가가 아니다.
3. **V2 새 source 일반화:** 독립 원본 source family를 개발/validation/test로 분리하고, split manifest를 결과 산출 전에 독립 검토자가 잠근다. 공격 유형과 challenge 전/중 관측 지식, 준비·추론 자원 및 재시도 상한을 연구자가 정한다. 학습·가중치·정규화·threshold는 개발/validation에서만 정하고 test 공개 후 변경하지 않는다. 인간과 공격자는 가능한 한 동일 challenge/판정 조건을 사용하며 차이가 있으면 별도 조건으로 기록한다. 현재 8개 reference source는 이 독립 test를 제공하지 않는다.
4. **V3 입력 보호의 추가 효과:** 격리된 staging에서 보호 없는/보호 있는 입력 조건을 명시하고, 가림 조건의 추가 효과와 사람 완료 가능성을 같은 버전·challenge 분모로 비교한다. 이 단계는 승인된 입력 보호 기술, 격리된 전체 경로 및 결과를 관찰할 안전한 test action이 준비된 뒤에만 가능하다. 준비되지 않으면 feasibility/설계 항목으로 남기며 실험 성공으로 보고하지 않는다.
5. **Endpoint 및 판정:** (a) gate 진입/완료와 시간 유지, (b) score 값 및 사전 고정 기준 통과, (c) 서버의 단일 보호 동작 허용/거부(L3)를 독립 기록한다. 어떤 endpoint가 primary인지, 성공 방향, 분모, 기술 실패·불확정 처리를 연구자와 독립 검증자가 사전에 합의한다. score pass를 gate 통과나 L3 성공으로 치환하지 않는다.
6. **보고:** 표본·정밀도 근거, paired 여부, cluster 단위, 효과크기/CI, 다중 비교, 중단 기준은 자료 구조와 주장에 근거해 확정한다. 근거가 없으면 값은 미정으로 두며, 결과는 승인된 threat model/source 범위 밖으로 일반화하지 않는다.

## 다음 세션의 G4 실행 계약 초안

실행 계약을 승인할 때 아래 항목을 특정 버전과 값으로 채운다. 공란이 있는 동안 평가 실행을 시작하지 않는다.

- 연구 질문 / 허용·금지 주장 / FR6·V0–V3 포함 범위:
- 공격자 유형, challenge 전·중 지식, 허용 도구 및 자원·시간·query·재시도 상한:
- source-family 개발/validation/holdout manifest, reference-library 분리, 누출 검사 책임자와 잠금 시각:
- 동일 challenge·화면·전환·방향·장치 조건 또는 차이를 분리할 설계:
- 채점기 버전, 전처리/좌표/시간 규칙, 가중치·정규화·threshold·gate 유지 조건의 고정 위치:
- primary endpoint와 gate/score/L3 각각의 성공·실패·불확정 정의 및 분모:
- 표본 수 또는 목표 정밀도와 근거, 통계 분석·중단 규칙:
- 승인된 격리 환경, endpoint 관찰 방법, 원자료 접근 권한과 보관 위치:
- 독립 사전 검토자, 재현 절차, 비식별 공개 산출물 검사:
- 연구자 승인 일시 및 이번 실행에 포함되는 정확한 자료·절차:

계약은 신규 공격 실행, CAPTCHA 통과/제출, 방어 변경, 실제 서비스 배포 또는 외부 전송을 이 문서만으로 승인하지 않는다. CAPTCHA 통과 동작이 포함될 경우 실행 시점의 별도 확인이 필요하다. 현재의 허용 범위는 문서·코드 정적 점검과 환경 진단이며, 실제 page submission·camera input·외부 endpoint 호출·원본 변경은 포함되지 않는다.

## 남은 준비 항목

- 비공개 source-family/파생본 계보 manifest와 기존 pool/reference의 중복 판정.
- 기존 인간 기록과 공격 시도의 challenge/build/방향/분모 대응을 주장할 수 있는지 확인; 근거가 없으면 paired 분석 포기.
- 연구자가 선택할 공격자 모델, 자원 상한, primary endpoint, 성공·실패·불확정 경계, 표본/정밀도 목표.
- 독립 source holdout 및 잠금 절차. 현 보존 8개 source만으로는 만들 수 없다.
- gate와 L3를 각각 기록할 수 있는 소유자 승인 격리 evaluator/staging 및 protected test action.
- Computer Use 브라우저 provider 또는 창 바인딩 원인을 특정할 재현 가능한 runtime/app/window trace. 대체 경로는 승인된 harness/staging에서만 평가하고, offline replay를 웹 endpoint의 대용으로 부르지 않는다.

공개 저장소에는 요약 집계와 방법만 둔다. 개인별 원자료, 원본/식별 가능한 영상, ID 대응표, 로컬 식별 경로, 입력 해시는 비공개 위치에 유지한다.
