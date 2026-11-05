# 가려진 손동작 CAPTCHA 연구 검증

**현재 실행 현황(2026-11-05):** [단일 작업 계획·수행 결과·남은 입력](docs/deliveries/2026-11-05_work_plan.md). 실행 감독기/실제 MediaPipe 계측, 물체 접촉 fixture, 비공개 송출 core, 군집 구간/원시 JS parity, 격리·오프라인 재현환경을 보완했습니다. 실제 모델·사람/공격·운영 승인은 미완료입니다. 아래 문서는 각 시점의 기록입니다.

**재개 후속:** [legacy/bake 재처리·승격 등록부·비공개 저장 분리·기존 원본 한 개 점검](docs/deliveries/2026-11-04_resume_followup.md). 과거 상태와 최신 구현 범위를 구분해 기록합니다.

**기존 prod 기반 UI 수정안:** [A 문구 / B 비교 그림 / C 기존 가이드 손금 및 12종 재평가](docs/deliveries/2026-11-04_prod_palm_variants.md). 사용자가 원한 기존 화면 기반으로 다시 구현했습니다. 목표·카메라 패널과 원래 동작을 사용하며 앞선 독립 시연의 별도 준비 단계는 제외했습니다.

**순차 구현:** [실행 기록](docs/deliveries/2026-11-04_execution_progress.md)에 프레임 대응·연구 후보 MP4, [손바닥 안내 12종 평가·3종 구현](docs/deliveries/2026-11-04_palm_ui_evaluation.md), [표준 좌표/시간 adapter](docs/deliveries/2026-11-04_standard_adapter.md), 자체 작성 3D 골격 fixture를 기록했습니다. 관련 합성/회귀 106개와 준비 화면 배치를 확인했습니다. 원본 동작 자료는 없으며 실측 기반 생성·사람 효과·운영 release는 미완료입니다.

**전달본 후속 점검:** [작업 완료 여부·손동작 자동 생성 감사](docs/deliveries/2026-11-04_completion_audit.md)는 통합 목록 62개와 하위 요구를 대조합니다. 전달 당시 자동 생성은 설계 단계였고, 이후 자체 작성 골격으로 연결 시험을 추가했습니다. 실측 P1·Text2HOI 재현과는 구분하며, 남은 작업은 위 실행 기록을 따릅니다.

**최신 작업 현황(2026-11-03 전달본):** [두 저장소 통합 할 일](docs/backlog_2026-11-03.md), [실험 카드](docs/experiment_cards_2026-11-03.md), [설명·발표 초안](docs/research_explanation_2026-11-03.md), [handcaptcha 수정 패치와 적용 안내](patches/README.md). 큰 손 선택·중첩 화면과 가림 보강은 [handcaptcha 작업 브랜치](https://github.com/mukgore/handcaptcha/tree/work/todo-consolidation-20261103)에 커밋했고 기존/후보 점수 비교 CLI를 추가했습니다. 이번 적용·검사 내역은 [전달본 반영 기록](docs/deliveries/2026-11-03_review.md)에 있습니다.

이 저장소는 기존 연구의 결과를 재현하고 한계를 검토하는 공개 분석 저장소입니다. 원본 보고서·참여자 응답·개인별 좌표·영상·모델 산출물은 공개 저장소에 포함하지 않습니다. 공개 가능한 집계 결과와 분석 코드만 제공합니다.

G3는 [연구자 종료 결정과 남은 증거 한계](docs/reproducibility/g3_dr3_fr5_researcher_update_2026-10-28.md)를 기록한 단계입니다. 이후 승인된 로컬 G4 공격·방어 탐색을 수행했습니다. 최신 결과는 [G4 실제 코드 보고서](docs/g4_actual/g4_final_report.md), 과거 1차 상태와 결과는 [PROJECT_STATUS.md](PROJECT_STATUS.md) 및 [phase1_review.md](docs/phase1_review.md)에서 확인할 수 있습니다. 운영 배포·신규 참여자 수집·독립 holdout 검증은 수행하지 않았습니다.

## 재현 가능한 분석

Windows PowerShell에서 저장소 루트로 이동하고, Python 3.10 이상으로 로컬 가상환경을 만든 다음:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe analysis\audit.py
```

`analysis/audit.py`는 로컬 `data/raw/`에 원자료 스냅샷이 있을 때 개인 자료를 읽어 집계합니다. `data/`는 Git에서 제외되어 있으므로, 명세에 따라 확보한 원본 파일을 사용자가 로컬에 배치해야 합니다. 입력 데이터는 수정하지 않습니다. 집계 보고서는 `reports/phase1_aggregates.json`에 씁니다. 원문 값, 결측 분모, 공개용 집계 해시 및 실행 환경 정보는 별도 로컬 `data/derived/`에 기록됩니다.

기존 원 움직임 기반 공격은 `analysis/replay_existing.py`로 저장된 관측 결과부터 재생할 수 있습니다. 이 재생은 원본 동영상을 다시 처리하지 않으며, 픽셀 추출·카메라 입력·서버 인증 경로를 검증하지 않습니다. 필요한 코드와 원자료 스냅샷은 비공개 로컬 보관본에 있습니다.

## 자료 처리

- 보고서 원문은 수정하지 않습니다.
- 참여자 단위 자료, 설문 원응답, 좌표, 동영상, 로컬 파일 목록과 해시, 임시 작업 산출물은 공개하지 않습니다.
- 결과를 재현할 수 없는 과거 실험은 수행된 것처럼 표현하지 않습니다.
- 핵심 검증 결과와 남은 자료 공백은 [docs/phase1_review.md](docs/phase1_review.md)에 있습니다.


## Reproducibility follow-up (2026-10)

Independent, conditional replay of the archived A/B and prod_v2_pool records and the paired A/B summary are organized under [analysis/reproducibility](analysis/reproducibility), [docs/reproducibility](docs/reproducibility), and [reports/reproducibility](reports/reproducibility). See the [artifact map](docs/reproducibility/README.md). Raw records, participant-level rows, per-session errors, and input hashes remain local and are excluded from Git. Historical executed-build provenance remains unresolved.

## 실용성 검증 및 표준 채점 전환 v0.3

- [실용성·사업성 검증 요구사항](docs/practical_validation_requirements_v0.3.md): 오답 거부, 미관찰 문제, 입력 보호와 가림의 추가 효과, 사용자 부담, 비용, 구매 증거를 분리합니다.
- [prod 분석 및 표준 수학 기반 채점 전환](docs/scoring_standardization_v0.3.md): handcaptcha prod의 고정 버전을 분석하고 DTW·시간 미분·오류율 곡선·임계값 선택의 이행 요구사항을 정의합니다.
- [실험용 수학 모듈](validation_v03/standard_metrics.py)과 [합성 테스트](tests/test_standard_metrics.py)를 추가했습니다. 실제 사람/공격 성능 개선이나 prod 교체·배포를 의미하지 않습니다.

```bash
python -m unittest discover -s tests -p test_standard_metrics.py -v
```

## 영상 풀·가림 생성·송출 설계 v0.4

[동작 영상 풀 확보·가림 생성·보안 송출 요구사항](docs/video_pool_occlusion_delivery_requirements_v0.4.md)은 기존 handcaptcha 구현의 정적 감사, 영상 확보·사용권·중복 관리, 전 프레임 가림 및 재디코딩 검사, 정답 비공개·세션 기반 송출, 반복노출 공격과 운영 인수 시험을 정의합니다. 설계 문서이며 신규 영상 생성·보안 실험·배포를 수행했다는 의미가 아닙니다.

## G4 실제 코드 탐색 및 국소 방어 (2026-10-28)

[실험 코드와 재현 안내](g4_lab/README.md)는 실제 HTML 채점·관문 함수, 공개 MP4 및 새 localhost 서버를 연결합니다. [공격 결과](docs/g4_actual/g4_attack_matrix.md), [방어 비교](docs/g4_actual/g4_defense_matrix.md), [회귀·교차검산](docs/g4_actual/g4_test_results.md), [독립 검토](docs/g4_actual/g4_independent_review.md), [비식별 집계](reports/g4_actual)를 보존했습니다. 실제 카메라·인간 성능·미사용 source 일반화·과거 시스템 L3를 입증한 결과는 아닙니다. 원자료와 개별 replay 입력은 공개하지 않습니다.

## 후속 연구·개발 계획 (2026-11-02)

[후속 로드맵](docs/research_roadmap_2026-11-02.md)에 기존 연구·발표 마무리, 가림 모호성과 사람 수행 가능성, 채점·입력 보호 검증, 영상 풀 및 3D 손·물체 생성 후보의 우선순위와 단계 전환 조건을 정리했습니다. 계획 기록이며 신규 실험·배포 완료를 의미하지 않습니다.

## 공격 실행시간 다조건 검증 계획 (2026-11-04)

[HaMeR·공격 실행시간 검증 TODO](docs/runtime_validation_todo_2026-11-04.md)는 과거 Colab 실행시간 회고의 한계를 출발점으로, CPU/GPU·최초/반복 실행·프레임 처리 설정·저비용 공격의 비교, 중단에도 보존 가능한 로그, 오프라인/온라인/서버 종점의 구분을 R0–R9 할 일과 완료 기준으로 정리합니다. 벤치마크 구현이나 새 성능 측정을 완료한 기록은 아닙니다.
