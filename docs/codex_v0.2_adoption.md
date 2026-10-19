# Codex에 데이터 분석 v0.2 명세 적용하기

> 이 문서는 실행 지침을 위한 안내서다. 문서 커밋 자체는 분석·실험·방어 구현 승인이 아니다.

## 적용 전 확인
1. 로컬 Codex 작업 폴더의 `git remote -v`로 **`mukgore/codex`**인지 확인하고, 변경 중인 파일을 `git status --short`로 확인한다.
2. `git fetch origin` 후 로컬 미커밋 변경 사항을 보존한 상태에서 최신 `main`을 반영한다. 병합 충돌은 자동 덮어쓰지 않는다.
3. `PROJECT_STATUS.md`, `HANDOFF.md`, `docs/phase1_review.md`, `docs/data_dictionary.md`, `docs/reproduction.md`, `docs/followup_experiments.md`, `docs/human_data_analysis_requirements_v0.2.md`를 읽는다.
4. 현재 `AGENTS.md`와 `.codex/agents/` 존재 여부를 확인한다. 없다고 해서 기존 사용자 PC 상위 디렉터리·하네스 전역 규칙을 지워서는 안 된다. 본 저장소에 Codex 규칙이 아직 commit되어 있지 않으면 **명세서 참조 규칙을 별도로 제안하고 승인 후 병합**한다.

## 단기 권장 업무 — G0/G1 문서·계획
- 현재 구현/문서와 v0.2 DR1–DR6, FR1–FR6 요구사항을 1:1 대응한다.
- 각 요구사항의 상태를 `완료 증거 있음 / 부분 구현 / 미구현 / 원자료 부족 / 승인 필요`로 분류한다.
- 이미 있는 `analysis/audit.py` 계산과 1차 보고서를 덮어쓰지 않는다.
- 우선순위: DR3 프레임 경계 원인 → FR2 IQR → FR3 3지표 상관 → FR4 지표별 신뢰구간 → FR5 가중치 민감도 → FR6 프로토콜.
- 분석을 실제로 **실행**하기 전에는 사용자에게 단계·코드변경 범위·산출물 위치·개인정보 검사·검증 계획을 보고하고 승인을 구한다.

## 에이전트 역할 연결
| 역할 | 맡는 작업 | 금지/경계 |
|---|---|---|
| data-auditor | DR1–DR6, FR1, 자료 계보 | 비공개 원자료 업로드 금지 |
| data-analyst | FR2–FR5 계산 설계 및 승인된 계산 | 분모·seed·데이터 분할 변경 은폐 금지 |
| analysis-verifier | 재계산·통계적 반증·누출 검토 | 구현자 자체 검토만으로 승인 금지 |
| research-reporter | 추적표·불확실성·연구자 해석 분리 | 결과나 참가자 데이터 임의 생성 금지 |
| developer/tester | 승인된 G4 이후 보안 방식 작업 | G0–G3에서 신규 공격·방어 실행 금지 |

에이전트의 실제 이름은 로컬 설치 내용에 맞게 적용한다. 이름이 없으면 해당 역할을 기존 에이전트에 매핑하고, 임의의 agent 호출로 동작한다고 가정하지 않는다.

## Codex에 전달할 첫 프롬프트

```text
현재 저장소는 mukgore/codex다. 새로운 v0.2 요구사항 명세인
docs/human_data_analysis_requirements_v0.2.md 와
docs/codex_v0.2_adoption.md 를 읽고, AGENTS.md 및 로컬
.codex/agents/*.toml의 기존 규칙과 충돌을 조사해라.

이번 작업은 G0/G1: 명세 적용 상태 조사와 분석 계획 수립까지만 허용한다.
PROJECT_STATUS.md, docs/phase1_review.md, docs/data_dictionary.md,
docs/reproduction.md, analysis/audit.py를 근거로 DR1–DR6,
FR1–FR6의 완료/부분/미완/자료부족/승인필요 추적표를 작성해라.

기존 원자료·보고서·과거 집계는 수정하지 말고, 개인정보나
개인별 로그는 공개 Git에 올리지 마라. 실행 계획에는 표본 단위,
분모, 코드 변경 대상, 출력 위치, 검증자, 예외 처리와 실패 기준을 명시해라.
현재 승인되지 않은 FR1–FR6 새 계산·새 실험·가중치 변경·배포를 시작하지 마라.
기존 에이전트 규칙을 자동으로 덮어쓰지 말고, 병합 제안만 제출한 후
나의 승인 요청을 해라.
```

## 이후 단계
- 사용자 승인 후 **G2** 인간 n=18 심층 분석을 실시한다. 개인별 자료와 로그는 로컬 gitignored 영역에만 둔다.
- **G3**에서 다른 검증자가 값과 해석을 반박 관점으로 검토한다.
- **G4**는 데이터 분석이 아니라 새 공격·CAPTCHA 설계 검증이므로 별도 승인한다.
