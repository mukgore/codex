# 가려진 손동작 CAPTCHA 연구 검증

**Cloud 이전 준비:** [현재 작업 보존·이전 가능 범위·실행 초안](docs/codex_cloud_migration_preparation_2026-11-14.md), [새 작업 인계문](docs/codex_cloud_handoff_2026-11-14.md). Cloud 실행과 비공개 자료 전송은 아직 하지 않았습니다.

**새 손 생성 실행(2026-11-14):** [양손 48프레임을 다시 만들고 원래 관절·손끝·전체 자세를 보관](docs/deliveries/2026-11-14_mano_controlled_producer.md)했습니다. 이전 결과와 값이 일치하고 실행 증거를 확인했습니다. 랜덤 생성과 생물학적 타당성 검증은 남아 있습니다.

**보관 손 모델 대응(2026-11-14):** [MANO 12개의 저장 손끝·화면 좌표 연결과 288프레임 계산](docs/deliveries/2026-11-14_mano_reference_mapping.md)을 확인했습니다. 생체 허용 범위·물리 단위 승인은 남아 있습니다. [3D 문제 생성과 사용자 채점의 차이](docs/3d_scoring_baseline_explanation_2026-11-14.md)도 기록했습니다.

**생체 검사 개발(2026-11-14):** [논문 수식을 코드로 옮겨 480프레임에 적용](docs/deliveries/2026-11-14_biomechanical_features_and_profile.md)했습니다. 현재 접촉 모형의 손바닥 기준 공백과 허용 수치 미확인을 찾아 통과시키지 않았습니다. 실제 생물학적 타당성·제약 있는 랜덤 생성은 아직 미완료입니다.

**3D 계보·생체/랜덤 계획(2026-11-14):** [기존 112개 영상의 가족관계/분할 검사](docs/deliveries/2026-11-14_generated_scene_lineage.md)를 마쳤습니다. seed만 바꾼 자료의 독립 평가 주장을 막습니다. [학술 근거를 둔 제약 프로필과 랜덤 생성 계획](docs/3d_biomechanics_and_random_generation_2026-11-14.md)도 명시했습니다. 현재 생물학적으로 타당한 동작만 생성하는 완성된 모델은 아닙니다.

**3D 표면 단서(2026-11-14):** [앞뒤 가림·물체/조명 네 조건을 실제 영상으로 비교](docs/deliveries/2026-11-14_surface_depth_cues.md)했습니다. 32개·768프레임과 실행 기록을 확인했습니다. 같은 최종 영상의 다른 깊이 정답과 조명 단서를 구분했으며 사람/AI 성능 검증은 남아 있습니다.

**실험 기록(2026-11-14):** [명령·시각·종료 상태·결과 파일을 연결해 보존](docs/deliveries/2026-11-14_execution_evidence_and_priority_resume.md)합니다. 실제 재실행 파일 69개를 검증했고, 과거 자료의 사후 보존과 구분했습니다. 전체 Python 177개 통과. [새 실험 기록 기준](docs/experiment_evidence_protocol_2026-11-14.md)을 따릅니다.

**접촉 모형 후속:** [두 접촉 모형·깊이 대안쌍](docs/deliveries/2026-11-13_grasp_contact_counterexamples.md), 12개 대조/8개 출력·192프레임·검사 111개 통과. 선 그림의 개발 검사이며 실제 손/사람·AI 효과는 미검증입니다. 원래 순서의 촬영·선별·실제 대응 자료가 우선입니다.

**3D 코드 후속:** [기존 가상 손 12개·가림 4개/96프레임 재검사](docs/deliveries/2026-11-13_mano_artifact_review.md). 미공유 로컬 코드를 검토·보완했으며, 새 모델 추론이나 실제 사람/공격 성능 결과는 아닙니다.

**명세 순서 후속:** [현재 입력과 18세션 구간 집계 확인](docs/deliveries/2026-11-13_segment_aggregation_and_priority_gates.md). 서로 다른 영상 사이의 구간은 기준 좌표가 짧아 계산 불가로 0점이 생길 수 있음을 확인했습니다. 실제 사람의 실패로 판단하지 않았으며, 촬영·동의한 응답·모델 입력은 대기입니다.

**UI 단위 완료(2026-11-13):** [초기 0.5초 노출·0.5초 가림 페이드와 모든 64조합](docs/deliveries/2026-11-13_ui_factorial.md). 관련 Node 24개, 화면 128건, 합성 카메라 경로 64건을 검증했습니다. 실제 사람 효과와 최종 화면 채택은 별도 입력 대기입니다. 다음 작업은 원래 명세 우선순위와 선행 조건을 따릅니다.

**2026-11-13:** [채점 프로그램의 대기·전송·응답 시간 제한과 실패 처리](docs/deliveries/2026-11-13_evaluator_deadline.md)를 검증했습니다. 다음은 사용자 요청의 prod 기반 초기 무가림→가림 페이드와 UI 모든 조합입니다. 전체 촬영·사람/AI 비교·3D 생성 목표를 유지합니다.

**V05 후속(2026-11-12):** [로컬 연결 수·전체 연결 시간 제한](docs/deliveries/2026-11-12_lab_connection_budget.md)을 검증했습니다. 전체 Python 148개와 실제 prod bridge 통합 9개가 통과했습니다. 운영 환경 검증과 evaluator 전체 실행 예산은 남아 있습니다.

**V02 후속(2026-11-12):** [복수 부모·바이트 복사·노출 이력 검사와 점수 CSV 사전검사](docs/deliveries/2026-11-12_lineage_score_preflight.md)를 구현했습니다. 보존 원본과 세 파생본의 잘못된 분할을 실제 파일로 탐지했습니다. 신규 촬영·독립 평가 자료는 대기이며, 다음 검토는 V05 실행·연결 예산입니다.

**S06·V00/N02 후속:** [18세션 저장/재로드·실제 JS export·실행 전 snapshot과 runtime journal 연결](docs/deliveries/2026-11-10_session_artifacts_and_run_manifest.md)을 검증했습니다. 새로운 사람/모델 성능 결과나 과거 build 복원이 아닙니다. 이후 V02 작업은 위 후속 기록을 따릅니다.

**3A/3B 후속:** [62개 항목 전체 추적과 다음 작업](docs/backlog_execution_audit_2026-11-10.md), [실제 카메라 대응 분석·ROC/DET·공격 유형별 결과 도구](validation_v03/SCORE_DIAGNOSTICS.md). 대응 키가 맞을 때만 정상/정지/사진을 비교하고, validation에서 잠근 기준으로 유형별 결과·군집 구간을 낸다. Python 103개가 통과했다. 구현 검사는 합성 자료이며 새 사람 실험 결과가 아니다. 전체 목표는 진행 중이다.

**최신 실행(2026-11-10):** [현재 자료로 실행한 전 단계 작업과 필요한 입력](docs/deliveries/2026-11-10_all_stage_execution.md). 기존 18세션 경계 대응, 세 가림색의 실제 MediaPipe 비교, prod 점수 검산, 로컬 상태 상한/만료 정리와 회귀를 완료했습니다. 새 촬영·사람 응답·HaMeR·운영 인증은 별도 입력 대기입니다. **UI 수정 단계 전까지 설계와 화면은 handcaptcha prod를 기준으로 유지합니다.** 아래는 과거 시점의 기록입니다.

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

[연구 목표와 후속 실험 추가 기록 (2026-11-10)](docs/research_goal_followups_2026-11-10.md)에 측정 방향, 복수 해석, 기존 데이터의 한계, 접근성, 가림색 비교를 정리했습니다.

## 후속 연구·개발 계획 (2026-11-02)

[후속 로드맵](docs/research_roadmap_2026-11-02.md)에 기존 연구·발표 마무리, 가림 모호성과 사람 수행 가능성, 채점·입력 보호 검증, 영상 풀 및 3D 손·물체 생성 후보의 우선순위와 단계 전환 조건을 정리했습니다. 계획 기록이며 신규 실험·배포 완료를 의미하지 않습니다.

## 공격 실행시간 다조건 검증 계획 (2026-11-04)

[HaMeR·공격 실행시간 검증 TODO](docs/runtime_validation_todo_2026-11-04.md)는 과거 Colab 실행시간 회고의 한계를 출발점으로, CPU/GPU·최초/반복 실행·프레임 처리 설정·저비용 공격의 비교, 중단에도 보존 가능한 로그, 오프라인/온라인/서버 종점의 구분을 R0–R9 할 일과 완료 기준으로 정리합니다. 벤치마크 구현이나 새 성능 측정을 완료한 기록은 아닙니다.
