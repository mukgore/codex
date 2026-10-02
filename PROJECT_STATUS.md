# 프로젝트 진행 상태 — 2026-10-03

## 목표와 단계

- 현재 목표: 1차 연구 현황·재현·데이터/결측/채점/통계 검증, 주장 근거 상태 및 보완 실험 계획 작성.
- 사용자 재개 지시 후 검토 문서를 작성했고 **1차 결과·실험 계획 제출, 사용자 검토 대기** 상태다.
- 1차 검토·명시 승인 전에는 새 CAPTCHA 후보·입력 방식·서비스·참여자 실험을 시작하지 않는다. 보고서 원본은 직접 편집하지 않았다.

## 완료

- 원자료 164개, 157382505 bytes를 `data/raw/`에 스냅샷하고 `data/inventory.json`의 SHA-256으로 원본과 전부 대조했다. `data/` 전부 Git 제외.
- PDF 원문을 텍스트로 추출하고 파일/실험 계보를 조사했다. 노트북 3개는 모두 output cell이 없음.
- 사람 n=18, HaMeR 28조합의 저장 raw score와 detection rate에서 최종 score 재계산; 저장점수와 부동소수점 수준 일치.
- 두 SUS 응답표 n=10/21 score 및 Cronbach alpha 재현. 점수 58.75/73.333, alpha .819/.823. 누락 응답 없음.
- 사람 명시 null 141/8782 segment frame, phase·timestamp·좌표 shape·결측 민감도 기초 분석.
- HaMeR score 28/28 통과와 별개로 38도 gate 189/224 통과, 모든 gate 통과 조합 10/28 및 `stop_on_fail=false` 확인.
- 원 visibility-bit 공격은 저장 관측 이후 매칭/좌표 scoring 재실행 결과 일치. top-1 14/16, 좌표점수 16/16. 원영상 픽셀 단계는 입력 영상 부재로 재실행하지 않음.
- 저장된 citation 일부를 J-STAGE/ICCV/Google Patents/Google Cloud/Meta 공식 자료에서 대조. 신규성/전체 문헌 전수검증은 완료 아님.
- `docs/inventory.md`, `data_dictionary.md`, `reproduction.md`, `claim_evidence_matrix.md`, `threat_model.md`, `followup_experiments.md`, `phase1_review.md` 초안 작성. README/요구 패키지/결정기록 갱신.

## 잠정 결과 및 제한

- 사람 score mean .6631, 17/18 ≥.25. HaMeR score mean .7218, 28/28 ≥.25. 28조합은 8개 동작을 공유하므로 독립 모집단 표본 28개가 아님.
- 표 10 지표 가중합은 .55677→.557. 본문 초기 레벨3 n=4 .493과 표본/코드 관계 불명. 동일값으로 합치지 않음.
- p≈.012 n=10 A/B는 원점수·조건순서 자료가 없어 재현 불가. 10명 SUS는 A/B 점수가 아님.
- n=21 SUS 응답과 n=18 인증 세션의 개인 연결은 불가.
- 공개된 visibility-bit attack과 사용자가 별도로 보고한 원 위치/크기-only 공격은 구분. latter는 원자료·산식·시도 기록이 특정되지 않아 미재현.
- 12.70초는 keyframe 일치 이후 recording segment duration 합이며 전체 인증 경과시간이 아님. HaMeR 실행시간은 보고서 내부 10시간/21분 불일치, timed log 미제공.
- 사람 원영상, 원 level-3 영상 및 HaMeR 실행환경이 없어서 좌표 검출에서 전체 재추론·일반화·end-to-end 인증은 검증하지 않음.

## 산출물

- 핵심 검토: `docs/phase1_review.md`
- 재현·공격 경계: `docs/reproduction.md`, `docs/threat_model.md`
- 데이터/실험 계보: `docs/inventory.md`, `docs/data_dictionary.md`
- 주장표/후속 카드: `docs/claim_evidence_matrix.md`, `docs/followup_experiments.md`
- 공개 집계: `reports/phase1_aggregates.json`, `reports/attack_replay.json`
- 원본/중단 기록: `HANDOFF.md` (안전 종료 시점의 역사적 기록), `docs/decisions.md`

## 저장소 상태와 다음 단계

- 원격 `https://github.com/mukgore/codex.git`는 공개 저장소이며 사용자 동의로 사용 중. 개인정보, 개별 응답·좌표, 비밀값, 로컬 절대 경로, 대형 원자료는 공개하지 않는다.
- 검토 산출물 커밋 `aa82fdc`를 원격 `main`에 푸시 완료. 원격과 로컬 `main`은 동기화되어 있다.
- 이번 재개 범위에서 자동화 검사/테스트를 추가하거나 실행하지 않았다. 분석 출력 재현은 이전 세션의 `reports/phase1_aggregates.json` 및 `attack_replay.json`에 기록되어 있다.
- 다음 명령(PowerShell, 저장소 루트): `$env:PYTHONIOENCODING='utf-8'; .\.venv\Scripts\python.exe analysis\audit.py`
- 사용자가 `docs/phase1_review.md`와 `docs/followup_experiments.md`를 검토하고 다음 작업을 승인하면, 승인 범위를 `docs/decisions.md`에 기록하고 해당 단계만 시작한다. 승인 전 후속 구현은 하지 않는다.
