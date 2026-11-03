# 할 일 원문·요구사항 색인 — 2026-11-03

이 색인은 확인한 문서의 목차와 요구 ID를 보존한다. 목차 자체를 미완료 목록으로 취급하지 않는다. 현재 판정은 [통합 목록](backlog_2026-11-03.md), 최신 수용 범위는 G3/G4 결정 기록을 따른다.

## codex main과 열린 PR의 계획·근거 문서

### [3d_hand_object_challenge_requirements_v0.1.md](3d_hand_object_challenge_requirements_v0.1.md)

1. 10살에게 설명 · 2. 기존 설계에서 바뀌는 부분 · 3. 반드시 먼저 결정할 과제 의미 · 4. 생성 계약 GEN3D · GEN3D-01 장면 변수와 재현성 · GEN3D-02 사람이 실제로 할 수 있는 동작 · GEN3D-03 물체 추론이 진짜 필요한가 · GEN3D-04 가림과 출력 보안 · 5. 입력과 채점 SCORE3D · 6. 공격 및 비교 실험 EVAL3D · 7. 도입 관문과 비용 · 8. 외부 연구와 사용권 · 8.1 신규성·선행기술 경계 (2026-10-26 추가) · 8.2 자산과 연구용 자료 · 9. 기존 문서와 연결할 실행 입력

### [claim_evidence_matrix.md](claim_evidence_matrix.md)

참고문헌 확인 상태

### [codex_v0.2_adoption.md](codex_v0.2_adoption.md)

적용 전 확인 · 단기 권장 업무 — G0/G1 문서·계획 · 에이전트 역할 연결 · Codex에 전달할 첫 프롬프트 · 이후 단계

### [data_dictionary.md](data_dictionary.md)

사람 세션 JSON (18개) · HaMeR 28조합 JSON · SUS 원응답 · 결측·시간 품질 결과

### [decisions.md](decisions.md)

결정 기록

### [followup_experiments.md](followup_experiments.md)

F0 — 누락된 기존 증거 회수·재현성 복구 (우선 1) · F1 — 같은 challenge에서 사람/공격자 전체 흐름 비교 (우선 2) · F2 — challenge 정보 누설 ablation (우선 3) · F3 — 고정 평가식/일반화 검사 (우선 4) · F4 — 인지/사용성 기제 분리 (우선 5; 인적 승인·지도교사 절차 선행) · 승인 이후에만 고려할 사항

### [g4_actual/g4_attack_matrix.md](g4_actual/g4_attack_matrix.md)

실제 계산 및 신규 loopback 서버 · 실제 MP4 채널 · 현재 pool 밖 legacy 보충 검사

### [g4_actual/g4_defense_matrix.md](g4_actual/g4_defense_matrix.md)

G4 방어 후보와 전후 비교

### [g4_actual/g4_final_report.md](g4_actual/g4_final_report.md)

무엇이 실제로 성공했는가 · 가림이 난도를 높였는가 · 방어는 무엇을 바꾸었는가 · 정상 입력과 새로운 자료에서는 유지되는가 · 가장 중요한 남은 위험과 다음 연구 · 판정

### [g4_actual/g4_independent_review.md](g4_actual/g4_independent_review.md)

검토 범위 · 결과와 공격자 지식 가정 · 기존 136회 실제 코드 호출 평가 · 기존 공개 영상 cache lookup · Pixel metadata 및 circle lookup · Gate, score, local L3의 의미 · Stationary-filter 반례 · 서버 및 통합 시험의 정적 검토 · 연구 해석과 다음 검증 · 후속 보완: 비밀 순서 lookup, blind baseline, mask fault injection · 무작위 순서 media lookup · 무정보 좌표 기준선 · Stage 6 mask fault-injection 검토 · Legacy reference 보완 평가

### [g4_actual/g4_progress_state.md](g4_actual/g4_progress_state.md)

실행 기준 및 보존 · 완료 및 제약

### [g4_actual/g4_test_results.md](g4_actual/g4_test_results.md)

새로 실행한 검사 · 저장 및 실행

### [hand_selection_and_overlay_ui_proposal_v0.1_2026-11-02.md](hand_selection_and_overlay_ui_proposal_v0.1_2026-11-02.md)

1. 출발점과 목표 · 사용자가 설명한 현재 동작 · 사용자가 직접 관찰한 문제 · 이번에 원하는 변화 · 2. 기능 A — 가장 큰 손으로 시작하기 · A-01. '가장 큰 손'의 초기 정의 · A-02. 시작할 때 선택하고 수행 중에는 유지하기 · A-03. 사용자에게 보일 안내 초안 · A-04. 구현 수용 사례 · 3. 기능 B — 문제 영상과 카메라의 중첩 화면 · B-01. 사용자의 원안 · B-02. 첫 프로토타입 구성 제안 · B-03. 중첩 때문에 생길 수 있는 혼동과 대응 · 4. AI로 추가 생성·탐색할 안내 후보 · 5. 비교·평가 계획 초안 · A와 B의 영향을 나누어 보기 · 기록할 지표 · 6. 구현 작업으로 넘길 묶음 · 7. 이번 결정과 남은 선택

### [handcaptcha_implementation_roadmap_2026-11-02.md](handcaptcha_implementation_roadmap_2026-11-02.md)

지금 먼저 할 일 · 구현 후보와 검증 조건 · 연구·개발 순서 · 관련 문서

### [human_data_analysis_requirements_v0.2.md](human_data_analysis_requirements_v0.2.md)

1. 목적과 검증 질문 · 1.1 A단계: 기존 인간 n=18 데이터의 심층 분석 · 1.2 B단계: 후속 인간–공격 비교의 분석 준비 · 1.3 연구 질문 · 2. 현재 증거와 범위 경계 · 3. 데이터 요구사항 (DR) · 4. 기능 요구사항 (FR) / 수용 기준 · FR1 결측 심층 분석 — 기존 감사 위에 추가 · FR2 이상치·품질 분석 · FR3 지표 분포·상관·중복성 분석 · FR4 추정 불확실성 · FR5 가중치·정규화·판정 민감도와 일반화 한계 · FR6 공격 판별력 비교 — 설계 선행 / 실행 승인 별도 · 5. 비기능 요구사항 (NFR) · 6. 학습과 연구자 판단 (LR) · 7. 요구사항 추적표 — 2026-10-19 문서 검토 기준 · 8. 산출물 및 단계 게이트 · 9. Codex 에이전트 연결 정책

### [implementation_audit_2026-10-17.md](implementation_audit_2026-10-17.md)

조사 범위와 근거 구분 · 1. 버전과 실행 경로 · 2. 자세 관문과 기록 흐름 · 3. A/B 제시 방식 · 4. 가림 생성 · 5. 정규화·리샘플링·점수 · 6. 좌우 손 처리 · 7. 추가 확인이 필요한 자료와 범위 · 8. 추가 허가 범위에서 확인한 버전 연결

### [inventory.md](inventory.md)

실험 계보(확인도 포함) · 명시적 누락/외부 의존성

### [phase1_review.md](phase1_review.md)

사용자 검토가 필요한 요점 · 무엇을 실제로 다시 계산했나 · 핵심 불일치와 판정 · 다음 결정을 위한 우선 계획 · 현재 판정 · 사용자 검토 질문

### [practical_validation_requirements_v0.3.md](practical_validation_requirements_v0.3.md)

1. 쉬운 설명 · 2. 목표, 비목표 및 현재 출발점 · 2.1 목표 · 2.2 비목표 · 2.3 기존 증거를 다시 실험하라고 오인하지 말 것 · 3. 요구사항 상태 및 판정 규칙 · 4. 공통 기반 요구사항 (V0) · V0-01 자료 계보 및 재현성 · V0-02 평가 층 분리 · V0-03 최소 실행 로그 · V0-04 분석 분모 · 5. V1 — 채점기가 틀린 답을 거부하는가? (최우선) · V1-01 가설 · V1-02 입력과 대조군 · V1-03 절차 · V1-04 산출 및 판단 · 6. V2 — 새 문제에서도 저비용 공격을 막는가? · V2-01 데이터 분할 · V2-02 공격군 및 지식 수준 · V2-03 공정한 비교와 누출 분리 · V2-04 산출 및 판단 · 7. V3 — 입력 보호와 결합할 때 가림의 추가 효과가 있는가? · V3-01 조건 설계 · V3-02 입력 보호 적합성 조사 · V3-03 통제된 전체 경로 시험 · V3-04 판정 · 8. V4 — 정상 사용자가 실제로 완료할 수 있는가? · V4-01 설계 · V4-02 지표와 시간 · V4-03 판정 · 9. V5 — 비용 비대칭과 구매자 경제성이 실제로 성립하는가? · V5-01 공격 비용 · V5-02 방어 비용 · V5-03 고객 관점 · 10. V6 — 필요한 고객이 실제로 지불할 것인가? · V6-01 조사 대상과 기록 · V6-02 인터뷰 질문 · V6-03 거래 검증 · V6-04 판정 · 11. 통계·표본·해석 요구사항 · 12. 산출물 및 디렉터리 계약 · 13. 실행 순서, 역할 및 자율 진행 · 14. 자동 점검과 인수 기준 · 15. 최종 의사결정표 · 16. 기존 문서와의 추적 관계 · 17. 표준 수학·채점 전환 추가 요구사항 (S1–S8)

### [reproducibility/captcha_replay_ab_2026-10.md](reproducibility/captcha_replay_ab_2026-10.md)

요약 · A/B 설계 및 측정 정의 · A/B 주요 결과 · DR4 계산 및 오류 · 산출물 및 재현 방법 · 해결되지 않은 자료 공백

### [reproducibility/computer_use_local_g4_attempt_log_2026-10-28.md](reproducibility/computer_use_local_g4_attempt_log_2026-10-28.md)

Why Computer-use was considered · Attempt history reported in the session · Outcome and limits · Evidence to retain if a separate authorized attempt is made

### [reproducibility/for_experiments_colab_mediapipe_lineage_2026-10-26.md](reproducibility/for_experiments_colab_mediapipe_lineage_2026-10-26.md)

연구자 기억과 대조한 내용 · 확인된 코드·산출물 관계 · 판정 · 다음 데이터 활용 원칙

### [reproducibility/g3_dr3_fr5_researcher_update_2026-10-28.md](reproducibility/g3_dr3_fr5_researcher_update_2026-10-28.md)

DR3 — frame-count boundary reconciliation · DR4 and DR6 — researcher scope decisions · FR1–FR4 — current acceptance basis · FR5 — researcher clarification · 13 sensitivity-scenario artifacts · A/B, LR3, and phase boundary

### [reproducibility/g3_interpretation_g4_existing_runs_2026-10-24.md](reproducibility/g3_interpretation_g4_existing_runs_2026-10-24.md)

공개 범위 · G3 해석 · G4 실행 1 — 랜드마크 재구성 조건 비교 · G4 실행 2 — 피부-bit closed-set 식별 · 결론과 남은 증거

### [reproducibility/g4_human_attack_pool_overlap_2026-10-26.md](reproducibility/g4_human_attack_pool_overlap_2026-10-26.md)

확인 결과 · 판정 · 적절한 다음 분석

### [reproducibility/g4_local_page_scope_2026-10-26.md](reproducibility/g4_local_page_scope_2026-10-26.md)

확인한 항목 · 수행하지 않은 것 · G4 판정에 미치는 영향

### [reproducibility/g4_pixel_extraction_replay_2026-10-26.md](reproducibility/g4_pixel_extraction_replay_2026-10-26.md)

범위와 방법 · 해석 · 보존 및 개인정보 · 다음 검증에 필요한 것

### [reproducibility/g4_preregistration_template_v0.2.md](reproducibility/g4_preregistration_template_v0.2.md)

A. 연구 질문 및 고정할 주장 · B. 공격자별 정보와 자원 · C. 공통 challenge 및 판정 환경 · D. 세 결과 endpoint 및 분모 · E. 개발/검증 분리 및 누출 점검 · F. 사전 잠금 설정 · G. 표본·통계·성공/실패 기준 · H. 자원·기록·개인정보 · I. 실행 전 독립 검토 및 승인 · 요구사항 대응 확인

### [reproducibility/g4_readiness_audit_2026-10-28.md](reproducibility/g4_readiness_audit_2026-10-28.md)

G3 종료 상태와 잔존 한계 · 저장소 및 실행 환경 · 기존 G4 자료의 재사용 범위 · G4 연결 가능성 및 준비 판정 · FR6 및 v0.3 V0–V3 최소 실행 프로토콜 초안 · 다음 세션의 G4 실행 계약 초안 · 남은 준비 항목

### [reproducibility/independent_verification.md](reproducibility/independent_verification.md)

수행 방법 · 교차 확인 결과 · 별도 좌표 재계산 확인 · 해석 한계

### [reproducibility/local_source_map_candidate_2026-10-26.md](reproducibility/local_source_map_candidate_2026-10-26.md)

확인된 비공개 로컬 자료 구조 · 증거 상태 · 다음에 조사할 연결

### [reproducibility/prod_v2_source_lineage_correction_2026-10-26.md](reproducibility/prod_v2_source_lineage_correction_2026-10-26.md)

수정된 확인 결과 · G4 공격 자료와의 재대조 · 상태 및 다음 처리

### [reproducibility/README.md](reproducibility/README.md)

Local input layout

### [reproducibility/v0_2_evidence_gaps_and_researcher_decisions_2026-10-26.md](reproducibility/v0_2_evidence_gaps_and_researcher_decisions_2026-10-26.md)

항목별 잔여 사항 · 연구자 판단과 기술 조치의 분리 · 연구자가 결정해야 하는 것 · 기술적으로 가능한 최소 후속 조치 · 종료 판단

### [reproducibility/v0_2_status_addendum_2026-10-26.md](reproducibility/v0_2_status_addendum_2026-10-26.md)

정정 1: DR4 후보 지표 · 정정 2: G4 기존 추출 결과의 소스 재생 · 상태 변경 요약 · 재현 범위와 기록 한계

### [reproducibility/v0_2_status_and_g4_next_steps_2026-10-26.md](reproducibility/v0_2_status_and_g4_next_steps_2026-10-26.md)

기준과 범위 · 검증한 기존 결과 · 요구사항 수용 상태 · G4를 이어가기 위한 필수 준비 · 다음 실행 위치

### [reproduction.md](reproduction.md)

실행 정보 · 점수·통계 재현 · 공격 재현 · 재현되지 않은 단계 · 지표 이름 및 의미 차이

### [research_roadmap_2026-11-02.md](research_roadmap_2026-11-02.md)

1. 먼저 일차 연구와 발표를 마무리한다 · 2. 현재 근거와 출발점 · 3. 다음에 연구자가 선택할 질문 · 4. 우선순위와 완료 조건 · P0 — 기존 검증 정리와 후속 실험 설계 · P1 — 유망 후보와 실제 인증 흐름의 분리 검증 · P2 — 문제 생성·고급 후보와 실용성 · 5. 실험 실행 전에 채울 항목 · 6. 저장소 역할과 작업 경계 · 7. 기존 상세 문서

### [scoring_standardization_v0.3.md](scoring_standardization_v0.3.md)

1. 범위와 실제 변경 상태 · 2. 쉬운 설명 · 3. 코드에서 확인한 내용과 조치 · 4. S1 — 좌표·누락·시간축 표준화 · S1-01 좌표 공간 · S1-02 시간과 결측 · 5. S2 — 실제 DTW를 비교 후보로 도입 · 6. S3 — 시간에 맞는 속도·가속도 · 7. S4 — 점수 결합을 표준 분류 문제로 검토 · S4-01 레이블 · S4-02 비교 후보 · S4-03 학습·검증 · 8. S5 — ROC/DET와 운영 임계값 · 9. S6 — 자세 관문·구간 집계·데이터 수집 · 10. S7 — 이행·검증·중단 순서 · 11. S8 — 실행 및 인수 조건 · 12. 공식 방법 자료

### [threat_model.md](threat_model.md)

자산·판정 지점 · 공격자 가정별 현재 평가 · 해석 시 경계 · 아직 시험하지 않은 저비용 baseline

### [video_pool_occlusion_delivery_requirements_v0.4.md](video_pool_occlusion_delivery_requirements_v0.4.md)

0. 문서 계약 · 1. 쉬운 설명과 핵심 결정 · 2. 기존 방식 검토 · 3. 요구사항 우선순위와 상태 · 4. POOL-01 — 자료 확보 경로와 권리 · 4.1 확보 우선순위 · 4.2 권리 대장 · 4.3 직접 촬영 계약 · 5. POOL-02 — 촬영 계획과 실질적인 다양성 · 5.1 작은 확보 실험부터 · 5.2 데이터 계보와 분할 · 5.3 수량 보고 · 6. POOL-03 — 데이터 구조와 상태 전이 · 6.1 서로 다른 네 저장 영역 · 6.2 상태 전이 · 6.3 비공개 source manifest · 6.4 비공개 artifact manifest · 6.5 브라우저 반환 스키마 · 7. MASK-01 — 수학·타임라인 계약 · 7.1 수식 버전 · 7.2 2D 판정 · 7.3 원본-출력 정렬 · 8. MASK-02 — 가림 후보 및 선택 방법 · 9. MASK-03 — 가림 적용과 출하 검사 · 9.1 굽기 · 9.2 기하 gate와 보안 gate의 구분 · 9.3 최종 MP4 재디코딩 · 10. SERVE-01 — 구조 선택 · 10.0 원본 확보·변형·가림의 대안 비교 · 10.1 MP4 생성 주기와 재사용 경계 · 10.2 세션마다 달라 보이게 할 필요가 생기면 · 11. SERVE-02 — challenge 발급·수명·재생 · 11.1 발급 · 11.2 상태 · 11.3 media endpoint · 11.4 짧은 수명 링크와 캐시 · 12. SERVE-03 — 기존 prod를 바꾸어야 하는 지점 · 13. POOL-04 — 재사용·수집·답안집 공격 · 14. 비용·성능·운영 기록 · 15. 필수 인수 시험 · 16. 작업 패키지와 완료 순서 · WP0 기존 방안 감사 — 이번 문서의 범위 · WP1 확보·스키마 · WP2 오프라인 생성기 정비 · WP3 가림·풀 공격 평가 · WP4 격리 송출·서버 판정 설계/구현 · WP5 제한 시험·운영 결정 · 17. 산출 경로 및 판정 · 18. 출처 및 추적 · 저장소 고정 버전 · 공식 외부 자료

## 루트의 과거 작업·회수·진행 기록

- [HANDOFF](../HANDOFF.md), [PROJECT_STATUS](../PROJECT_STATUS.md), [RECOVERY_TARGETS](../RECOVERY_TARGETS.md), [RECOVERY_INSTRUCTIONS](../RECOVERY_INSTRUCTIONS.md), [README](../README.md). 과거 정지·문서 전용 범위를 이번 사용자 요청과 혼동하지 않는다. 자료 공개 경계는 유지한다.

## main 밖의 독자 문서·변경

- [PR #1 아키텍처 감사](https://github.com/mukgore/codex/blob/audit/captcha-architecture-20261026/docs/captcha_architecture_and_repo_audit_2026-10-26.md): 서버 검증 계약·두 저장소 감사·사용권·가림·backend·held-out 증거·이전 mask 패치.

- [PR #2 영상 확보 대 3D 생성](https://github.com/mukgore/codex/blob/research/hand-motion-generation-20261026/docs/hand_motion_source_and_generation_research_v0.1.md): source/contact 다양성, Text2HOI 연구 재현과 파일럿, GRAB/MANO 자원/권리, 품질·사용성·공격·배포 관문.

- [이전 재현성 감사 브랜치 보고](https://github.com/mukgore/codex/blob/captcha-reproducibility-audit/reports/captcha-reproducibility-audit.md): 조건부 DR4 재생, 과거 DR3/DR6/후보지표/A/B/HaMeR 계보. 이후 10-26/28 보충 기록이 우선한다.

- handcaptcha의 [분기 비교](https://github.com/mukgore/handcaptcha/compare/main...claude/kind-bardeen-vnotu9): prod/modified 변경을 검토 대상으로 보존하며 자동 병합하지 않는다.

## handcaptcha 코드의 남은 구현 계약

- Stage1–5 추출·품질·정면·길이 정규화·가중치 추정; Stage6/7 수식과 손목 가시성 충돌; filtered/reversed 타임라인과 원본 대응; `pipeline.run_batch`의 후보 판정과 최종 영상 release 구분.

- `dataset_expansion_bake_v1.py`의 Colab/CLI 정비, 프레임 유지·재인코딩 가정, 권리·split·source lineage, 최종 바이트 검사.

- prod의 `maxNumHands:1`, `multiHandLandmarks[0]` 및 동일 인덱스 handedness 연결: 새 선택 모듈의 실제 prod 연결은 남음. 기존 공개 landmark/영상·client scoring은 서버 비밀 정답/신뢰 입력 경계와 다름.

## v0.4 인수 시험 T01–T24 전 목록

권리 UNKNOWN, 공개/비공개 manifest, 첫/중간/끝 mask 누락, 검출불능 frame, z 독립 2D, 시간변형 정렬, encoder/부분 파일, 최종 MP4/PTS/mask, poster/thumbnail/트랙, legacy 재편입, origin/목록, 세션/tenant/만료, warm cache, Range/seek/retry, 동시 submit/재사용, client passed/score, 공개 lookup, 다중 마스크 합성, 사람 대응 조건, source/capture split, landmark 차단 후 UX, retired/revoked, 풀 부족/장애 fallback, 전체 release 증거 연결. [판정 조건 원문](video_pool_occlusion_delivery_requirements_v0.4.md).
