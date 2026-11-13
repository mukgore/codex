# 실행 순서에 따른 62개 백로그 추적표 — 2026-11-10

목표는 [기존 백로그](backlog_2026-11-03.md)의 전체 62개 ID다. [연구 목표의 실행 순서](research_goal_followups_2026-11-10.md#실행-순서와-기존-백로그-연결)를 우선하며, 현재 할 수 없는 실제 실험은 대기로 두고 다른 항목의 독립 작업을 진행한다. 기존에 수용된 연구를 다시 미완료로 열지 않는다. UI 수정 단계 전까지 설계와 화면은 handcaptcha prod 기준이다.

‘기존 수용’은 그 당시 지정 범위에 한정된다. ‘코드 검증’도 실제 사람·독립 평가·운영 완료가 아니다. ‘추가 작업 가능’은 아직 실행할 수 있는 엔지니어링/검토 작업이 있다는 뜻이며 다음 작업 큐다. 이 표의 항목/근거 파일 존재 검사는 연구 전체 완료 감사가 아니다. 상세 구현·원자료·실제 관찰이 더 필요한 항목을 완료로 표시하지 않는다.

| ID | 우선 단계 | 현재 근거/범위 | 남은 일 또는 필요한 입력 |
|---|---|---|---|
| NOW-01 | 전체 | 통합 목록·원문 연결·이 62개 추적표 | 변경 때 전체 ID와 우선순위 유지 |
| NOW-02 | 1/5 | 가림 누락 중단·timeline/후보·최종 픽셀 검사 코드, 보존 원본 3조건 [실행][EXEC] | 실제 승인·다양한 원본·운영 송출은 대기 |
| NOW-03 | 6 | 선택/중첩·prod 기반 변형과 회귀 [실행][EXEC] | 현재 prod 기준 유지. 실기·사용성 비교 입력 필요 |
| NOW-04 | 3B | paired score CLI·ROC/DET·유형별 결과·군집 구간 [진단][DIAG] | 독립 split의 실제 대응 점수 필요 |
| NOW-05 | 1–6 | 카드 A–E·촬영/선별 실행안 [촬영][CAPTURE] | 실제 참가자·목표·판정 기준 잠금과 수집 |
| NOW-06 | 전체 | 연구 설명 초안과 실제 수치 walkthrough [실행][EXEC] | 발표 분량·최종 주장·연구자 검토 필요 |
| R01 | 전체 | 설명 초안 있음 | 최종 발표/원고는 연구자 선택·발표 일정 입력 필요 |
| R02 | 기존 연구 | 기존 G3·A/B·FR1–FR4·DR3 수용 유지 [결정][ACCEPT] | 현 목적에서 재실행 불요 |
| R03 | 기존 연구 | 과거 build 조건부 재현 수용 유지 [결정][ACCEPT] | 새 실행 manifest만 엄격히 남김. 과거 복구 재개 안 함 |
| R04 | 기존 연구 | FR5 기준·holdout 부재·사후 제외 범위 유지 [결정][ACCEPT] | 새 검증을 과거 독립 검증으로 소급하지 않음 |
| R05 | 과거 자료 | 기존 복구 감사와 미회수 이력 유지 [이전 감사][AUDIT] | 특정 원출력/실행 이력 없으면 대기. 무차별 재검색 안 함 |
| R06 | 2/3B | 18세션·126구간 좌표/로그 대응 검증 [실행][EXEC] | 재생/정지 관문 대기는 미기록. 새 관찰·이벤트 필요 |
| R07 | 기존 연구/3A | 알려진 8문제 136건 회귀·독립 검산 [실행][EXEC] | 기존 국소 수용 유지. 새 source/사람/신뢰 입력은 별도 |
| R08 | 2 | 모호성 판정 단위·선별 초안 [촬영][CAPTURE] | 독립 주석·처음 보는 사람 응답·사전 기준 잠금 |
| R09 | 2/3A | 지각/운동/추적 분리 절차 [촬영][CAPTURE] | 실제 관찰·모방·추적 실패 기록 필요 |
| U01 | 6 | 손 선택 코드·회귀, 종전 사용자 PC 기능 확인 [실행][EXEC] | 기기/FPS/자세별 실기 입력 필요 |
| U02 | 6 | 선택 유지·소실 중단·전체 재시작 회귀 [실행][EXEC] | 교차/유사 손의 실제 오연결·재선택 부담 입력 |
| U03 | 6 | prod 기반 중첩·원본 카메라 분리 및 [64조합 화면/합성 경로 검사][UI64] | 실제 참가자·기기 비교 필요 |
| U04 | 6 | 별도 prod 기반 선택 손 연결·관문/시간/중단 회귀 [실행][EXEC] | 실제 shadow/다기기 평가 후 채택. root prod 교체 안 함 |
| U05 | 6 | A/B/C·초기 500ms 무가림→500ms 가림 페이드·전체 [64조건][UI64] | 실제 효과·최적 조합·기본 화면 채택은 미확정 |
| U06 | 6 | 카드 B·[64조건표와 조건/시간/중단 기록][UI64] | 정답 행동 주석·동의한 사람 비교·효과/채택 판단 필요 |
| S01 | 3B | 좌표/시간/종횡비/미러/결측 adapter·검사 [실행][EXEC] | 실제 대응 자료의 기하·계보 확인 필요 |
| S02 | 3B | 실제 DTW·각도/JS parity·원본 예 [실행][EXEC] | 독립 source/사람 자료에서 band·grid 선택/평가 |
| S03 | 3B | 실제 초 미분·gap 분리·[72개 sampling/합성 노이즈/평활화 계산](deliveries/2026-11-10_derivative_sensitivity.md) | 필터가 원래 미분도 바꾸는 민감도 확인. 실제 기기·정상/오답 이득 평가는 입력 대기 |
| S04 | 3B | 원시 특징·고정 점수 비교 도구 [진단][DIAG] | B1 독립 보정·B2/B3 학습은 대응 자료/군집·표본 필요 |
| S05 | 3B | ROC/DET·AUC/EER 진단·유형별 최악률·유형별 군집 구간 [진단][DIAG] | 독립 실제 평가 대기. 최악 유형 동시 위험 상한은 미구현/미주장 |
| S06 | 3B | [저장/재로드][PERSIST]·[18세션/126구간 집계와 계산 불가 기준 분리][SEGMENTS] | 영상 간 전환 기준·실제 camera coverage·새 이벤트·정책 채택은 실제 수집/연결 입력 필요 |
| S07 | 3B | legacy 회귀·adapter/원시 JS 수치 검사 | 독립 보정/평가와 동일 trial shadow 입력 필요 |
| V00 | 4/공통 | [사전 metadata/파일/코드/lock 검사·후검사·runtime journal 연결 실제 실행][PERSIST] | 새 실험은 이 경로로 scope별 기록. 신규 사람/모델/운영 사건 계측은 별도 입력 필요 |
| V01 | 3A | 기존 known-pool 수용 유지, 카메라 대응 분석기 [진단][DIAG] | 실제 같은 사람/문제/카메라 입력 필요 |
| V02 | 3B/4 | source/사람/capture 분할·바이트 중복 탐색 [실행][EXEC] | [계보·바이트 중복 사전검사][PREFLIGHT] 및 [복수 부모·노출 전파·점수 CSV 연결][LINEAGE] 검증. 실제 미사용 source 및 유사 촬영 확인 필요 |
| V03 | 5 | 가림×입력 보호 설계와 과거 국소 진단 | 신뢰 입력 방식·실제 대응 2×2 자료·동일 예산 필요 |
| V04 | 5 | 기존 국소 endpoint 수용·단일 소비/세션 회귀 [실행][EXEC] | 운영 인증·실제 capture trust는 대기 |
| V05 | 5 | TTL/상한/정리/429·소비·영속 core 회귀 [실행][EXEC] | [세션 발급 예산][PREFLIGHT]·[연결 수/전체 수명 상한][CONNECTION]·[채점 대기/입출력 예산][DEADLINE] 검증. 실제 사용자별 제한·운영 다중 worker·gateway는 별도 |
| V06 | 3A/4 | 기존 human18/공개 pool 차이 유지 | 공통 challenge·실제 카메라·새 정상 자료 필요 |
| N01 | 1/5 | 전달 파일·Git 패턴/ZIP 감사·비공개 분리 기록 | [두 저장소 이력과 현재 자료 형태 대조][PREFLIGHT]. 비도달 이력·영상 의미·권리 범위는 별도 |
| N02 | 공통 | 해시 잠금 환경·오프라인 재설치·[26 pin metadata 검사와 실행 manifest 연결][PERSIST] | 과거 build 미확인·다른 OS/브라우저/모델 runtime은 미검증 유지 |
| N03 | 공통 | 주장 근거표·기존 선행 한계 기록 | [InterHand·HaMeR 원 논문과 주장 범위 대조][LEVEL]. 과제 동일성·특허성 확정은 별도 |
| P01 | 1/5 | 기존 본인 촬영·본인 손·연구 사용/영구 비공개 확인 [촬영][CAPTURE] | 외부/다른 참가자 자산의 동의·운영 송출 권한은 별도 입력 |
| P02 | 1 | 원본 1개·21개 촬영 접수 계획 [촬영][CAPTURE] | 새 촬영·수행자/family 계보·주석 필요 |
| P03 | 5 | private 경로·SQLite 승격/철회 검증 [실행][EXEC] | 실제 운영 reviewer·배포/접근 통제 환경 필요 |
| P04 | 5 | 알려진 pool 재생/lookup 반례·노출 구분 | 미사용 pool·반복 노출 예산·새 대응 공격 필요 |
| M01 | 1/5 | frame map·후보 렌더·독립 container 점검 [실행][EXEC] | [실제 합성 container 경계 재검사][PREFLIGHT]. 신규 원본의 실제 타임라인은 대기 |
| M02 | 1/4 | 원본 1개 3색×3회 실제 추적 [실행][EXEC] | [보존 원본과 3개 가림 수준의 실제 추적][LEVEL]. 새 source/사람 이해도 대기 |
| M03 | 1/5 | 최종 프레임·영역·track 검사와 후보 gate [실행][EXEC] | [container·부가 자산 증거 대조][PREFLIGHT]. 실제 페이지 poster와 최종 배포 rendition 검사 대기 |
| D01 | 6 | 실제 FFV1 크기·배치 경과 기준선 [실행][EXEC] | [합성 영상 인코딩·컨테이너 검사·크기 분리 계측][LEVEL]. 전송·운영 요금/품질은 별도 |
| D02 | 5 | local Range/HEAD/no-store·만료/철회 core 회귀 [실행][EXEC] | 실제 origin/cache/gateway·운영 환경 필요 |
| D03 | 5 | 정답 공개 fetch 한계·신뢰 evaluator 경계 기록 [실행][EXEC] | 인증된 gateway·trusted evaluator·prod 단계별 연결 입력 필요 |
| T01 | 5 | 일부 T01–T24 인수 코드·문서 연결 [이전 감사][AUDIT] | [24개 전체 증거와 공백 대조][PREFLIGHT]. 실제 운영 인수는 대기 |
| W01 | 1–6 | 입력 없는 실험과 독립 개발을 나눠 진행, 이 전체 추적표 | 각 WP 선행 조건을 유지한 실행 계속. 현재 목표 active |
| G01 | 6 | 촬영 풀/3D 비교 설계와 기존 fixture | 실제 권리·수행 가능성·품질·동일 범위 비용 입력 필요 |
| G02 | 6 | 자체 골격/MANO fixture·[기존 재검사][MANO]·[두 접촉 proxy/깊이 대안쌍][CONTACT] | 실제 grasp 안정성·다양성·동작/물체/카메라 계보 필요 |
| G03 | 6 | capsule/sphere·[전 프레임 반경 교집합/실제 래스터 재검사][MANO] | 생체 범위·접촉/관통 주석·실제 편안함 검증 필요 |
| G04 | 6 | 대안쌍 질문 정의·A06/A07 촬영 계획 [촬영][CAPTURE]·[깊이 반전 대조][CONTACT] | [외부 단서 반례][LEVEL]. oracle 깊이와 영상 정보를 구분. 실제 장면/사람 해석 대기 |
| G05 | 6 | 최종 masked-only·비공개 pass 경계·[정사영 대안쌍][CONTACT] | [가림 바깥 단서 대조][LEVEL]. depth buffer/표면 가림·그림자·반사의 최종 렌더 검사 대기 |
| G06 | 6 | G0 손 모양 따라 하기 후보와 별도 접촉 범위 | 연구 과제 선택·복수 정답 기준·사람 입력 필요 |
| G07 | 6 | B0–B3×A1–A4 비교 요구 유지 | [16개 비교 셀과 예산·분모의 증거 구분][LEVEL]. 독립 평가 자극과 실제 대응 자료 대기 |
| G08 | 4/6 | MANO private intake·HaMeR preflight [실행][EXEC] | HaMeR/Text2HOI checkpoint·나머지 자산·허용 실행 환경 필요 |
| B01 | 2/6 | 사용성/이해·접근성 절차·중단 기준 [촬영][CAPTURE] | 동의한 참가자·경험/기기 기록·실제 관찰 필요 |
| B02 | 5/6 | batch 시간·실측 저장 bytes 기준선 [실행][EXEC] | [로컬 인코딩·검사 기준선][LEVEL]. 요청·전송·운영·사람 검수 비용은 별도 계측 |
| B03 | 6 | 고객 문제/인터뷰 후보 보존 | 용도·고객·연락 범위·거래 조건 입력 필요. 외부 연락/판매 안 함 |
| B04 | 6 | CONTINUE/MODIFY/STOP/INCONCLUSIVE 기준 유지 | 사람·강한 공격·비용·권리의 실제 결과와 연구자 최종 결정 필요 |

## 다음 구현 우선순위

2026-11-13 현재 V05 한 단위를 완료·push한 뒤 [prod 기반 UI 64조합][UI64]을 별도 단위로 구현·검사했다. 이후에는 원래 연구 실행 순서의 선행 조건과 전체 요구를 다시 대조한다. UI 수정 결과를 실제 사람 효과로, 합성 3D fixture를 실제 생성 모델 평가로 승격하지 않는다.

새 촬영/사람 자료가 없는 현재는 3A 대응 분석·S05 엔지니어링·S03 sampling/합성 잡음 민감도·S06 저장/재로드·V00/N02 공통 snapshot과 실제 journal 연결을 수행했다. 이후 [V02·V05·N01·M01/M03·T01의 코드와 근거를 보강했다][PREFLIGHT]. [M02 보존 가림 수준·6단계 비용과 모호성 반례도 개발 범위에서 검산했다][LEVEL]. 원문에 요구된 실제 평가를 문서/fixture로 대체해 완료시키지 않는다. 현재 전체 목표를 완료나 차단으로 판정할 근거는 없다.

[EXEC]: deliveries/2026-11-10_all_stage_execution.md
[DIAG]: ../validation_v03/SCORE_DIAGNOSTICS.md
[CAPTURE]: deliveries/2026-11-10_rights_capture_screening_protocol.md
[ACCEPT]: reproducibility/g3_dr3_fr5_researcher_update_2026-10-28.md
[AUDIT]: deliveries/2026-11-04_completion_audit.md
[PERSIST]: deliveries/2026-11-10_session_artifacts_and_run_manifest.md

[PREFLIGHT]: deliveries/2026-11-10_preflight_and_acceptance_audit.md

[LEVEL]: deliveries/2026-11-10_level_cost_and_visibility.md

[LINEAGE]: deliveries/2026-11-12_lineage_score_preflight.md

[CONNECTION]: deliveries/2026-11-12_lab_connection_budget.md

[DEADLINE]: deliveries/2026-11-13_evaluator_deadline.md

[UI64]: deliveries/2026-11-13_ui_factorial.md

[SEGMENTS]: deliveries/2026-11-13_segment_aggregation_and_priority_gates.md

[MANO]: deliveries/2026-11-13_mano_artifact_review.md

[CONTACT]: deliveries/2026-11-13_grasp_contact_counterexamples.md
