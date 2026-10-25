# v0.2 요구사항 현황 및 G4 다음 단계 — 2026-10-26

## 기준과 범위

기준은 docs/human_data_analysis_requirements_v0.2.md와 docs/codex_v0.2_adoption.md다. 기존 결과는 새로 실행한 것과 구분했다. 이번 확인은 명세 수용 기준, 이미 보존된 G2/G3 산출물, 공개된 G4 요약, 읽기 전용 검증 결과를 연결한다. 새 참가자 자료·원영상은 만들지 않았다.

GitHub main은 728525c4d3e81142f1d916a8a58205c7fb36d977까지 갱신되어 있다. 로컬 작업 사본은 ca00cf7에 있어 GitHub보다 5개 문서 커밋 뒤처져 있었다. 두 버전 사이 변경은 G4 결과 보고서와 집계 보고서 정리였으며 분석 소스는 바뀌지 않았다. 이후 GitHub 연결을 기준으로 이 상태 문서를 기록했다.

## 검증한 기존 결과

- 인간 18세션의 독립 Node 좌표 재생 기록은 저장 raw/estimated/final score와 18/18 일치한다. 최종 점수 최대 절대 오차는 1.23e-15다. 같은 기준 랜드마크와 후보 산식을 공유하므로 과거 수집 빌드의 증명은 아니다.
- 로컬 G4 독립 검증기는 기존 재구성 16행과 원 주변 bit 평가 16개를 대조해 PASS했다. 재구성 행의 최대 차이는 0, bit 평가 재계산 점수 최대 차이는 8.89e-16, top-1은 14/16, threshold 통과는 16/16이었다. 기존 요약과 상세 한계는 [G4 기존 실행 보고서](g3_interpretation_g4_existing_runs_2026-10-24.md)에 있다.
- 이 16개 평가는 원본 동작 8개를 공유하고 reverse 사례도 forward 관측에서 파생됐다. reference library도 같은 원본 동작을 포함한다. 따라서 결과는 closed-set 오프라인 재생에 한정된다. 독립 held-out, 사람과 동일 challenge의 대응 평가, 실시간 gate, 실제 전체 인증 흐름 결과로 해석하지 않는다.
- 저장소 계산 단위시험은 로컬 venv의 Python 3.10에서 4/4 통과했다. G4 독립 검증기는 별도 로컬 입력을 읽어 위 결과를 재계산했다. 개인별 입력과 로컬 전용 verifier는 공개하지 않았다.

## 요구사항 수용 상태

| 항목 | 상태 | 수용 근거와 남은 제한 |
|---|---|---|
| DR1 | ACCEPTED | 18개 JSON 스키마·pool 연결 및 독립 검증 기록이 있다. |
| DR2 | ACCEPTED | 명시적 null, phase 로그, 분모를 구분했다. 원영상이 없어 기록되지 않은 시간 누락은 판정할 수 없다. |
| DR3 | PARTIAL | 코드 콜백 순서와 18개 첫 segment의 matching-phase payload가 +18 경계를 설명한다. null 프레임의 고유 이벤트 대응은 불가능하다. |
| DR4 | PARTIAL | 세 채택 지표의 좌표 재생은 조건부로 18/18 일치한다. 실제 수집 빌드는 미확정이고, 나머지 네 후보 지표는 검증 가능한 산식이 없어 값으로 계산하지 않았다. |
| DR5 | ACCEPTED | dtw_angle의 sliding-window 의미와 accel의 구현 정의를 대조했다. |
| DR6 | EVIDENCE_LIMITED | 현재 재생의 revision·환경·입력 참조·설정 기록은 있다. 과거 18세션별 HTML/build/browser/pool 연결 증거는 없다. |
| FR1 | ACCEPTED | 18세션 결측·시간·phase 집계와 분모 설명이 기존 G2/G3 패키지에 있다. 누락 메커니즘은 확정하지 않았다. |
| FR2 | ACCEPTED | IQR 후보와 전체 포함/후보 민감도 분석이 보존되어 있다. 자동 제외는 하지 않았다. |
| FR3 | ACCEPTED | 세 채택 지표 raw/estimated 요약·상관과 불확실성 한계가 보존되어 있다. |
| FR4 | ACCEPTED | 참가자/세션 단위 bootstrap·Wilson 결과와 독립 확인 기록이 있다. |
| FR5 | PARTIAL | 13개 민감도 시나리오와 순위 변화가 확인됐다. 과거에 가중치·threshold가 평가 전에 고정됐다는 provenance는 없다. |
| FR6 (현재 설계 수용 기준) | ACCEPTED — 설계만 | 위협 지식, 자원, 동일 challenge 원칙, gate/score/end-to-end 분리, source-level split, 평가 전 잠금, 성공·실패·불확정 초안이 기존 위협 모델·후속 실험 설계에 있다. 실행용 수치와 preregistration은 별도 연구자 결정 전까지 미정이다. |
| G4 실험 증거 | PARTIAL | 기존 오프라인 결과는 독립 재계산됐다. held-out 일반화와 실제 웹 인증 흐름을 측정하지 않아 공격 성공률이나 운영 보안성을 결론낼 수 없다. |
| NFR1–NFR3 | ACCEPTED | 원자료와 공개 집계를 분리했고, 계산·해석·자료 한계를 구분했다. |
| NFR4 | PARTIAL | data/는 gitignore 대상이고 현재 GitHub main의 알려진 개인 절대경로·원자료 세션 파일명 검색은 일치 항목이 없었다. 다만 code search는 전체 Git history 비밀값 감사를 대신하지 않는다. |
| NFR5–NFR6 | ACCEPTED | 기존 검증은 로컬 CPU/기존 자료 범위였고, 새 데이터 생성·서비스 배포·가중치 변경은 하지 않았다. |
| LR1–LR2 | ACCEPTED | 데이터 품질·통계·일반화의 한계를 설명하고 독립 검증 반론을 연결했다. |
| LR3 | REQUIRES_RESEARCHER_DECISION | 취약 신호를 연구 결론으로 어떻게 표현할지, G3 해석을 최종 승인할지는 연구자 판단이다. |

상태는 기술 검증과 연구자 판단을 분리한다. ACCEPTED는 해당 명세 단계의 수용 기준만 충족한다는 뜻이다. FR6 설계가 수용되어도 G4의 독립적인 공격 성능 검증이나 CAPTCHA의 실사용 안전성이 입증되는 것은 아니다.

## G4를 이어가기 위한 필수 준비

1. 연구자가 공격 유형별 primary outcome과 성공 방향, 실패 경계, 불확정 규칙을 선택한다.
2. 허용할 공격자 지식 및 CPU·시간·query 예산을 고정한다.
3. 같은 challenge·판정 환경을 인간/공격자에게 제공할 수 있는 자료를 확보하거나, 차이를 별도 요인으로 선언한다.
4. 원본 clip family 기준 개발/held-out manifest와 threshold·가중치·정규화 상수의 잠금을 확정한다.
5. 독립 검증자가 누출·분모·endpoint 정의를 확인한 뒤 해당 실행에 대한 사전등록을 마친다.

현재 8개 clip으로는 독립 held-out 평가를 구성할 수 없고, 인간 18세션은 같은 challenge/build로 연결되지 않았다. 이 증거를 보충하려면 새 자료 또는 독립 source가 필요하다. 사람 모집·촬영이나 다른 경로의 추가 원자료 접근은 이 결과로 승인된 것으로 보지 않는다.

컴퓨터 화면 조작이 필요한 웹 확인은 Computer Use URL 판독이 막혔다. 로컬 자동화 하네스는 별도 방법으로 검토할 수 있지만, 이 보고서는 해당 웹 시험을 실행했다고 주장하지 않는다. CAPTCHA 통과 동작은 실행 직전 사용자 확인을 받아야 한다.

## 다음 실행 위치

G4 사전등록·누출 점검 양식은 [G4 사전등록 템플릿](g4_preregistration_template_v0.2.md)에 추가했다. 템플릿의 대응표를 FR6 항목과 대조했고, 근거가 없는 수치는 임의로 채우지 않았다. 연구자가 primary outcome, 성공·실패 경계, 표본/정밀도, 공격자 자원과 확보 가능한 동일 challenge/held-out 자료를 지정하면 이 양식을 채워 독립 검증할 수 있다. 자료나 결정이 준비되기 전에는 실행 가능한 preregistration으로 간주하지 않는다.
