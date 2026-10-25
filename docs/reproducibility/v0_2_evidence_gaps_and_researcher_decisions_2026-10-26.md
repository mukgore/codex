# v0.2 증거 공백 및 연구자 판단 추적 — 2026-10-26

이 문서는 기존 수용 상태 보고서를 대체하지 않고, 부분 완료·증거 제한·연구자 판단 항목의 현재 근거와 최소 후속 조치를 한곳에 연결한다. 개인 자료, 참가자별 값, 원자료 해시와 로컬 절대경로는 포함하지 않는다.

기준: [v0.2 현황](v0_2_status_and_g4_next_steps_2026-10-26.md), [DR4/G4 보충](v0_2_status_addendum_2026-10-26.md), [prod_v2 계보 정정](prod_v2_source_lineage_correction_2026-10-26.md), [G4 점수·자료 후보 대조](g4_score_compatibility_and_source_candidates_2026-10-26.md), [FR6 사전등록 양식](g4_preregistration_template_v0.2.md).

## 항목별 잔여 사항

| 항목 | 현재 판정 | 확인된 근거 | 정확한 공백 | 공백 성격 | 최소 다음 조치 |
|---|---|---|---|---|---|
| DR3 프레임 경계 | PARTIAL | 코드의 callback/phase 전환 순서와 인간 기록의 첫 segment 경계가 세션별 +1 frame 현상을 설명한다. | 개별 recording frame과 callback/event를 공통 식별자·충분한 타임스탬프 정밀도로 일대일 연결하지 못한다. 따라서 원인 설명은 코드 수준에서 강하지만 모든 프레임의 실증 매칭은 아니다. | 기존 로그에 식별자가 없다면 과거 실행에 대해서는 증거 제한. | 당시 고정밀 이벤트 로그가 남아 있으면 대조한다. 없으면 코드상 설명과 직접 관측을 분리해 종료 기록하고, 프레임별 확정 주장은 하지 않는다. |
| DR4 후보 지표 | PARTIAL | prod_v2_pool 18세션의 세 채택 지표 재계산은 저장값과 18/18 일치했다. 네 후보 지표는 과거 별도 4세션·36 trial에서 산식이 확인되고 독립 재생 오차가 작았다. | 네 후보 지표가 prod_v2_pool에서 실행·저장된 산식이라는 증거가 없다. 별도 4세션 결과를 prod18에 전이할 수 없다. | 과거 수집 파일에 지표 계산·설정이 기록되지 않았다면 그 빌드 사용 여부는 미확정. | prod18 session manifest 또는 실행 당시 코드 revision/설정이 발견되면 대조한다. 없으면 네 지표는 “과거 코드에서 정의·검증된 후보”로만 기술한다. |
| DR6 실행 계보 | EVIDENCE_LIMITED | 현재 재현은 코드 revision·환경·입력 참조·설정 기록을 갖는다. JSON version 문자열과 pool ID는 후보 구현 호환성을 지지한다. | version 문자열은 실제 실행 코드의 fingerprint가 아니다. 세션별 HTML/build/browser/pool revision manifest가 없다. | 과거 실행 기록이 생성되지 않았거나 보존되지 않았다면 복구 불가. | 당시 export/archive, browser cache, 배포 commit 또는 세션별 run manifest가 있는지 승인된 자료에서 한 차례 확인한다. 없으면 증거 제한으로 종료하고 추정 확정하지 않는다. |
| FR5 민감도·사전 고정 | PARTIAL | 13개 가중치/정규화 시나리오와 순위 변화가 분석돼 있다. | 과거 최종 평가 전에 가중치·Emax·threshold가 잠금됐다는 provenance가 없다. 사후 민감도는 사전등록 증거를 대신하지 않는다. | 과거 평가 시 잠금 기록이 없으면 현재 복구 불가. | 기존 설정 commit/실험 계획/타임스탬프가 있는지 대조한다. 없으면 과거 결과의 선택 편향 한계로 남기고, 후속 평가에서는 holdout 전에 잠근다. |
| NFR4 개인정보·저장소 이력 | PARTIAL | 알려진 개인 절대경로·원자료 세션 파일명에 대한 현재 GitHub main 검색에서 일치 항목이 없었고 원자료는 무시 규칙 대상이다. | 현재 branch의 제한 검색은 전체 Git history, 모든 secret 패턴, 대용량/숨은 파일을 포괄하는 보안 감사가 아니다. | 검사 범위가 불완전함. 전체 이력 감사는 기술적으로 수행 가능하지만 아직 완료 근거가 없다. | 저장소 전체 commit history에 대해 개인정보·secret·원자료 포함 여부를 로컬에서 검사하고, 발견 항목은 내용 공개 없이 상태만 보고한다. 필요 시 정정은 기존 공개 범위와 사용자 승인에 따라 처리한다. |
| LR3 해석 승인 | REQUIRES_RESEARCHER_DECISION | 기술 결과와 반론·일반화 한계가 문서화되어 있다. | 어떤 주장으로 결과를 최종 서술할지, 관측된 오프라인 공격 성공을 연구 결론에서 어느 강도로 표현할지 연구자 승인이 없다. | 연구자 권한에 속하는 해석 결정. | 연구자가 최종 주장 문구와 허용/금지 해석을 승인하거나 수정한다. 판단 전에는 기술 검증 완료와 연구 결론 승인을 분리한다. |
| G4 신규 자료 일반화 | PARTIAL / EVIDENCE_LIMITED | 기존 공격 산출은 재생됐고, 사람·공격 자료는 일부 같은 pool ID를 공유한다. FOR_EXPERIMENTS는 Colab MediaPipe 가림/추적 품질 산출물 형식과 부합한다. | 기존 attack reference와 source가 분리된 holdout, 같은 challenge의 사람·공격 대응, 실제 gate 이벤트와 보호 동작의 server log가 없다. FOR_EXPERIMENTS가 공격 개발·조정에 쓰이지 않았다는 provenance도 없다. | 기존 closed-set 자료만으로는 독립 일반화 및 end-to-end 인증을 확정할 수 없다. | 별도 source-family manifest와 미사용 holdout을 확인하고, 외부 전송이 없는 staging에서 gate/score/end-to-end를 각각 기록한다. 실행 조건은 사전등록·독립 검토 후 진행한다. |

## 연구자 판단과 기술 조치의 분리

### 연구자가 결정해야 하는 것

1. G3 결과에서 허용할 최종 주장과 금지할 주장의 강도(LR3).
2. G4에서 primary outcome을 하나만 고르는 대신 gate 성공, score 통과, end-to-end 인증을 각각 별도 endpoint로 보고할 것인지 확인. 세 결과는 서로 대체하지 않는다.
3. FOR_EXPERIMENTS가 공격 reference 구성 또는 score/threshold 조정에 사용됐는지, 알고 있는 provenance가 있는지. 모르면 미확인으로 유지한다.

### 기술적으로 가능한 최소 후속 조치

1. DR3 당시 고정밀 이벤트 로그 또는 추가 코드 기록이 있는지 확인한다. 없으면 프레임별 일대일 원인 확정은 불가하다고 보존한다.
2. DR6 세션별 빌드 기록과 FR5 평가 전 설정 잠금 근거를 승인된 자료에서 검색한다. 없으면 evidence-limited로 종결한다.
3. NFR4 전체 Git 이력 검사를 수행해 현재 branch 검색과 구분한 감사 범위를 기록한다.
4. G4에 쓸 독립 source-family 자료와 격리된 server-side test endpoint가 생기기 전에는 held-out 또는 전체 인증 성공 결론을 내리지 않는다.

## 종료 판단

G3 분석·재현 산출물은 기술적으로 대부분 완결되었다. DR3/DR4/DR6/FR5/NFR4는 위 증거 공백에 따라 PARTIAL 또는 EVIDENCE_LIMITED로 남고, LR3는 연구자 승인이 남는다. 이 항목들은 상태 문서에 이미 표시됐지만, 위 표가 현재 확인된 공백과 최소 후속 조치를 상세화한다. G4 독립 실험과 end-to-end 평가는 현재 자료만으로 완료되지 않았다.
