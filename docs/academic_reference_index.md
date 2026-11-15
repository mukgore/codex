# 학술 자료 색인과 코드·주장 연결

최초 정리: 2026-11-15. 앞으로 참고한 논문을 이 문서에 계속 추가한다. **생물학적 타당성은 학술 근거와 실제 모델의 관절·좌표계·단위·적용 조건을 대응해 판단한다.** 기하 검사, 자연스러워 보이는 모양, 논문 인용, 코드 검사 통과만으로 생체 유효성을 승인하지 않는다.

현재 연구에서 확인하거나 기존 문서에 참고로 기록한 자료를 안정 ID로 모았다. 아래 `기존 기록`은 해당 프로젝트 문서의 열람 상태를 옮긴 것이며 이번에 전부 다시 읽었다는 뜻이 아니다. `원문 대기`·`초록`·`프로젝트 안내`·`관련 절 검토`·`구현 대응`을 구분한다. 구현 대응도 원 논문 모델/학습/성능 전체 재현을 뜻하지 않는다. 원문/PDF를 이 저장소에 복제하지 않았다.

## 생체 제약과 생성 — 우선 읽을 자료

### BIO-01 — MANO

Romero, Javier; Tzionas, Dimitrios; Black, Michael J. (2017). **Embodied Hands: Modeling and Capturing Hands and Bodies Together.** ACM Transactions on Graphics / SIGGRAPH Asia, 36(6), Article245.

- **찾기:** [공식 프로젝트·논문/PDF·BibTeX](https://mano.is.tue.mpg.de/index.html). 공식 BibTeX를 옮긴 [인용 파일](../references/hand_research_core.bib)의 `Romero2017MANO`.
- **확인:** 2026-11-15 공식 프로젝트의 서지·모델 설명을 재확인. 관련 모델/실행 기록은 [48프레임 생산자](deliveries/2026-11-14_mano_controlled_producer.md), [192프레임 랜덤 진단](deliveries/2026-11-15_mano_random_diagnostic.md).
- **적용:** 학습된 손 형상/자세 표현. 연구 코드 `analysis/runtime_benchmark/mano_recorded_producer.py`, `mano_random_diagnostic.py`; handcaptcha의 `mano_reference_audit.py`, `biomechanical_profile.py`.
- **한계/남은 확인:** 실제 SDK16관절과 표면 손끝5점·전체 자세 출처는 기록했다. 모든 PCA 입력의 생체 유효성·SI단위·엄지 의미·사람 편안함 보장은 아니다. 실제 모델 파일 사용권과 논문의 인용은 별도다.

### BIO-02 — Biomechanical Constraints 본문

Spurr, Adrian; Iqbal, Umar; Molchanov, Pavlo; Hilliges, Otmar; Kautz, Jan (2020). **Weakly Supervised 3D Hand Pose Estimation via Biomechanical Constraints.** ECCV.

- **원문:** [저자 공개 PDF](https://jankautz.com/publications/WeaklySupervised3DHand_ECCV20.pdf). 인용 key `Spurr2020BMC`.
- **읽을 위치:** 본문 §3.1, 식(1)–(6)의 손바닥/국소 관절 특징과 식(7)의 허용 각도 영역. 식 위치와 구현 설명은 [feature/profile 전달 기록](deliveries/2026-11-14_biomechanical_features_and_profile.md).
- **적용 코드:** handcaptcha `experiments/motion_fixture/biomechanical_features.py`의 `extract`, `biomechanical_profile.py`의 `validate`/`assess`. 작성된 골격과 MANO native 점을 구분한 회귀 검사가 있다.
- **확인:** 관련 절/식은 11월14일 구현 시 검토한 기록이 있고 11월15일 본문 링크·서지를 재확인했다. 추정 학습용 soft constraint를 생성기의 규칙 검사로 독립 구현한 것이다.
- **한계:** 수식을 구현한 것과 실제 허용 수치를 확보한 것은 다르다. 현재 내장 여섯 한계는 미확인이다. 모든 사람/과제의 수행 가능성이나 안전한 속도를 이 논문 하나로 확정하지 않는다.

### BIO-03 — BMC 보충 자료

BIO-02와 같은 저자/연도. **Supplementary: Weakly Supervised 3D Hand Pose Estimation via Biomechanical Constraints.**

- **원문:** [ECVA 보충 PDF](https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123620205-supp.pdf).
- **읽을 위치:** §1, octant 부호 처리와 식(2), convex hull 근사·영역 밖 각도 거리. 본문과 보충 자료는 한 연구의 두 자료이며 독립 근거 두 개로 세지 않는다.
- **적용:** `signed_angles`, `polygon`/`hull_distance`; 각도 부호/경계·회전 재구성 검사. 11월14일 관련 절 검토 기록, 11월15일 링크/관련 절 재확인.
- **한계:** 부호 표현 범위와 생물학적 허용 범위는 다르다. 허용 hull의 실제 값·대상/추정/주석 조건과 엄지 대응은 별도 추출해야 한다.

### BIO-04 — GRAB

Taheri, Omid; Ghorbani, Nima; Black, Michael J.; Tzionas, Dimitrios (2020). **GRAB: A Dataset of Whole-Body Human Grasping of Objects.** ECCV.

- **찾기:** [공식 프로젝트·논문·보충·코드·BibTeX](https://grab.is.tuebingen.mpg.de/index.html), 인용 key `Taheri2020GRAB`.
- **확인/용도:** 11월15일 공식 안내/서지 재확인. 실제 손·물체·몸 움직임과 접촉 자료를 참고할 후보이며 현재 랜덤 MANO 진단은 GRAB 실제 동작을 재현한 결과가 아니다.
- **읽을 다음 부분:** 데이터 획득/모델 fitting·접촉 정의·대상과 object 구성·오차/subject별 제한. 특정 모션/참가자의 분포를 보편적 생체 한계로 자동 전용하지 않는다.
- **상태:** 자료 사용/다운로드·단위/관절 대응·우리 과제 적용은 별도 입력/검토가 필요하다.

### BIO-05 — D-Grasp

Christen, Sammy; Kocabas, Muhammed; Aksan, Emre; Hwangbo, Jemin; Song, Jie; Hilliges, Otmar (2022). **D-Grasp: Physically Plausible Dynamic Grasp Synthesis for Hand-Object Interactions.** CVPR.

- **찾기:** [저자 프로젝트·Paper·Code·BibTeX](https://eth-ait.github.io/d-grasp/), [CVF 논문 페이지](https://openaccess.thecvf.com/content/CVPR2022/html/Christen_D-Grasp_Physically_Plausible_Dynamic_Grasp_Synthesis_for_Hand-Object_Interactions_CVPR_2022_paper.html), 인용 key `Christen2022DGrasp`.
- **확인:** 11월15일 저자 페이지의 서지/방법 개요 재확인. 같은 날 CVF 링크는403이어서 그 경로의 원문 재열람 성공으로 기록하지 않는다. 대체 원문 링크는 저자 페이지의 Paper를 따른다.
- **적용/미적용:** 물리 기반 접근/잡기/이동의 설계 참고다. 현재 prescribed trajectory·capsule 거리 또는 PCA 곡선이 D-Grasp의 강화학습/물리 모델 재현은 아니다.
- **남은 확인:** 원문 방법·제약/보상·접촉/지지·평가 조건·자산 사용권을 실제 도입 범위와 대응해야 한다.

### BIO-06 — Chen Chen et al.2013의 수치와 연동 참고

Fai Chen Chen et al. (2013). **Constraint Study for a Hand Exoskeleton: Human Hand Kinematics and Dynamics.** Journal of Robotics, Article910961. [출판 DOI](https://doi.org/10.1155/2013/910961), [동일 논문 PDF 사본](https://pdfs.semanticscholar.org/5a84/3ade1ba00d075c4a9ae93c331dc7ee2c4b70.pdf), BibTeX `ChenChen2013Constraints`.

2026-11-15 원PDF2·6·11·12쪽을 렌더/시각 대조했다. §3.1 식(1)·표6 선택4행·§6/표9 집계속도를 [비승인 참고JSON](../references/chen2013_constraint_extraction.json)에 추출했다. [수식/표 산술 대조](deliveries/2026-11-15_biomechanical_numeric_sources.md)에서는6개 속도가 반주기 해석에서 반올림 수준으로 맞음을 확인했지만 저자 의도는 미확정이다. 관절 정의·MDH부호·BMC/MANO·과제/대상 대응 전 실행 한계로 쓰지 않는다. 표6은 BIO-07을 재인용한 것이다.

### BIO-07 — Cobos et al.2008 원출처 추적

Cobos, Ferre, Sánchez-Urán, Ortego & Peña (2008). **Efficient Human Hand Kinematics for Manipulation Tasks.** IROS. [저자기관 UPM 서지/원문 연결](https://oa.upm.es/4040/).

BIO-06 표6의 참고문헌[13], BMC의 참고문헌[10]이다. 11월15일 기관 서지/초록 확인 후 [기관PDF](https://oa.upm.es/4040/1/INVE_MEM_2008_58022.pdf)를 기본 인증서 검증을 유지한 Windows curl 재시도로 확보했다.6쪽을 렌더/검토하고 §II/표I–II의 일반D-H, §III/표III의 가동 범위·원출처, 과제별 모델 평가를 읽었다. [원표 대조](deliveries/2026-11-15_original_constraint_comparison.md)에서 선택18칸 중 엄지2칸이2013년 재인용과 다름을 확인했다. 임의로 합의/오류를 확정하지 않았다. [추출JSON](../references/cobos2008_constraint_extraction.json)·BibTeX `Cobos2008Kinematics`. 이전 접근 실패는 당시 기록이며 원도서·neutral/axis·task/개인차는 계속 추적해야 한다.

### BIO-08 — Neutral-zero 관절 기능 측정

Ryf, C.; Weymann, A. (1995). **The neutral zero method — A principle of measuring joint function.** Injury26. [DOI10.1016/0020-1383(95)90116-7](https://doi.org/10.1016/0020-1383(95)90116-7).

BMC 본문의 한계 출처 예시인 참고문헌[33]에서 서지를 확인했다. 11월15일 DOI 접근은 실패했으며 **원문 미열람**이다. 중립자세와 측정 원칙 확인을 위한 후속이며, 구체적 관절 값이나 우리 모델 대응을 이 자료에서 확보했다고 표시하지 않는다.

## 각 생체 판단에 무엇이 아직 필요한가

**국소 좌표 대조:** [BIO-06 표7–8과BIO-07 표I–II의 일반/수정D-H 참고 계산](deliveries/2026-11-15_kinematic_conventions.md)을264조건에서 맞췄다. 별도 작성 단일 기준축에서 BMC 방향 복원25조건도 확인했다. 실제 MANO/임상 축 fitting·안전 범위 검증이 아니며 복합 각도 수치쌍을 그대로 동일시하지 않는다. 코드: handcaptcha `kinematic_conventions.py`.

**2026-11-15 이름표 대조:** [각도 중심점/나가는 뼈 끝점의15개 기록과 선택 문헌4행](deliveries/2026-11-15_angle_center_mapping.md)을 연결했다. 192프레임의 기존960개 수치 배열이 그대로임을 확인했다. 이름 대응은 임상/MDH 축·중립/부호 검증이 아니다. BIO-02의 자식점에 따른 뼈 이름과 실제 각도 중심을 구분한다.

| 판단 항목 | 현재 연결된 학술 근거/코드 | 아직 비어 있는 근거 |
|---|---|---|
| 뼈 길이/비율 | BIO-01 모델·BIO-02 길이 구간 표현·profile `bone_lengths` | 실제 SI단위, 관절 중심/표면 손끝 구분 이후 대상별 수치와 근거 |
| 손바닥 곡률/벌림 | BIO-02 §3.1 식(1)–(3)·`palm_curvatures`/`palm_spread_radians` | 실제 허용값·population/과제·모델 대응 |
| 굽힘/벌림 결합·엄지·좌우손 | BIO-02 local frame/각도·BIO-03 §1·`joint_angle_hulls` | 관절별 hull·엄지 정의·좌우 대응·문헌/관측 대상과 일반화 범위 |
| 속도/가속도·연속 움직임 | 실제 초 미분은 프로젝트 확장. BIO-06 §6/표9의 과제별 속도 참고 수치를 추출 | **실행용 생체 한계는 미확정.** 주기 해석·대상/과제/부호 대응과 가속도 기준을 더 확인. 빠른 수행의 집계값을 안전/편안함 한계로 쓰지 않음 |
| 자기/물체 충돌·접촉·지지 | BIO-04/05는 관련 데이터/방법 후보, GEO는 기하 검사 참고 | 실제 표면/물리 모델·오차·자기 접촉/관통 정의와 검증 사례 |
| 편안함·피로·따라 하기 | 문헌 검토와 별개로 실제 사람 관측 필요 | 대상 참가자·동의·사전 정의 과제·중단/부담/수행 결과. 컴퓨터 검사만으로 승인 불가 |

새 수치마다 source ID, 본문 절/식/표·페이지, 값 원문/단위, 좌표계/관절 이름, 대상/측정 조건, 모델 대응, 허용 오차·보간·개인차 범위, 코드/검사와 확인일을 남긴다. 없는 값을 임의 안전 기준으로 채우지 않는다. `pending_profile()`의 수식 URL은 수치 승인 기록이 아니다.

## 추정·데이터·생성 모델 자료

아래는 기존 [3D 명세 §8](3d_hand_object_challenge_requirements_v0.1.md#8-외부-연구와-사용권), [모델 입력 확인](deliveries/2026-11-04_model_readiness.md), [선행 주장 대조](deliveries/2026-11-10_level_cost_and_visibility.md)의 참고를 모았다. 별도 표기가 없으면 이번에 원문을 새로 재검토하지 않은 **기존 기록**이다. 일부는 서지 전체 전사와 원문 절 기록을 더 해야 한다.

| 안정 ID | 찾을 자료/원문·공식 링크 | 실제 참고 범위와 남은 확인 |
|---|---|---|
| DATA-01 | Moon et al., ECCV2020, [InterHand2.6M](https://www.ecva.net/papers/eccv_2020/papers_ECCV/html/3540_ECCV_2020_paper.php) | 상호작용 손 데이터/단안 추정 참고. 가림 영상 이해·모방·인증 성능으로 이전하지 않음 |
| DATA-02 | Pavlakos et al., CVPR2024, [Reconstructing Hands in 3D with Transformers (HaMeR)](https://openaccess.thecvf.com/content/CVPR2024/html/Pavlakos_Reconstructing_Hands_in_3D_with_Transformers_CVPR_2024_paper.html) | 단안3D 복원/HInt 평가 참고. 사용자 실제 깊이 실측이나 우리 과제 공격 성공은 별도 |
| DATA-03 | [Text2HOI: Text-guided 3D Motion Generation for Hand-Object Interaction, 공식 repo](https://github.com/JunukCha/Text2HOI) | 11월15일 공식 repo 링크 재확인. 실행 자산/환경·원 논문 절/서지 대응은 추가. 생성 자연스러움/사용권을 코드 공개로 승인하지 않음 |
| DATA-04 | NeurIPS2023, [DeepSimHO](https://papers.nips.cc/paper/2023/hash/fbdaea4878318e214c0577dae4b8bc43-Abstract-Conference.html) | grasp 안정성 기반 손·물체 추정의 선행 후보. 원문 구체적 수치/구현 재검토 필요 |
| DATA-05 | [OakInk 공식 프로젝트](https://oakink.net/) | 손·물체 데이터/형상 후보. 자산별 권리·주석/단위/과제 조건 확인 필요 |
| DATA-06 | [DexYCB 공식 프로젝트](https://dex-ycb.github.io/) | 손·물체 자세 평가용 데이터 후보. 모델·영상·인물/상용 범위는 별도 확인 |

## 채점·시간 정렬·통계 자료

아래 적용 범위와 제외한 알고리즘은 [11월9일 문헌 적용 기록](deliveries/2026-11-09_literature_similarity.md)에 있다. 소수 공개 좌표의 합성 비교는 실제 사람 실험/독립 평가가 아니다. 아래는 기존 문서에서 확인한 서지/링크를 이어받았으며 최신 본문 재검토와 완전한 서지 전사가 필요한 항목도 있다.

| 안정 ID | 자료와 찾는 링크 | 적용 지점/한계 |
|---|---|---|
| SCORE-01 | Akamine, Dingemanse & Özyürek2026, [DOI](https://doi.org/10.3758/s13428-026-02975-5), [고정 코드 revision](https://github.com/ShoAkamine/dtw_validation/blob/0b439f47e47b8b807fd219ecac477e0868cc2cf3/kinematics/study2/scripts/dtw_functions.py) | 손끝 DTW step pattern·끝점/정규화 설정 참고. 참가자 유사도 평가 재현 아님 |
| SCORE-02 | De Smedt et al., CVPRW2016, [Skeleton-Based Dynamic Hand Gesture Recognition](https://openaccess.thecvf.com/content_cvpr_2016_workshops/w21/papers/De_Smedt_Skeleton-Based_Dynamic_Hand_CVPR_2016_paper.pdf) | 연결 관절 차이/뼈 표현 참고. 원3D feature·SVM 전체 구현 아님 |
| SCORE-03 | Shi et al., CVPR2019, [Two-Stream Adaptive Graph Convolutional Networks for Skeleton-Based Action Recognition](https://openaccess.thecvf.com/content_CVPR_2019/papers/Shi_Two-Stream_Adaptive_Graph_Convolutional_Networks_for_Skeleton-Based_Action_Recognition_CVPR_2019_paper.pdf) | 뼈 stream 아이디어 참고. GCN 학습/정확도를 이전하지 않음 |
| SCORE-04 | Vemulapalli et al., CVPR2014, [Human Action Recognition by Representing 3D Skeletons as Points in a Lie Group](https://openaccess.thecvf.com/content_cvpr_2014/papers/Vemulapalli_Human_Action_Recognition_2014_CVPR_paper.pdf) | 골격 표현/시간 정렬 분리 참고. SE(3)/리만 거리 전체 재현 아님 |
| SCORE-05 | Devanne et al., IEEE TCYB2015, [DOI](https://doi.org/10.1109/TCYB.2014.2350774) | 궤적/시간 정렬 설계 참고. 완전한 제목/서지·방법 재검토는 원 DOI로 확인 |
| SCORE-06 | Keogh & Pazzani2001, [Derivative Dynamic Time Warping](https://ics.uci.edu/~pazzani/Publications/keogh-kdd.pdf) | 식(6) 국소 기울기·경계 처리. 진행률32샘플 DDTW와 실제 초당 속도를 구분 |
| SCORE-07 | Tang et al., Pattern Recognition2018, [DOI](https://doi.org/10.1016/j.patcog.2018.02.011) | 전환점/부분 동작 설계 참고. 논문 가중 알고리즘을 적용한 결과 아님 |
| SCORE-08 | Sakoe & Chiba1978, [DOI](https://doi.org/10.1109/TASSP.1978.1163055) | 제한 DTW의 시간 정렬 참고. prod의 기존 sliding-window를 진짜DTW로 부르지 않음 |
| SCORE-09 | Fawcett2006, [An introduction to ROC analysis](https://doi.org/10.1016/j.patrec.2005.10.010) | ROC 운영점·tradeoff 해석. 독립 test에서 재보정하지 않음 |
| SCORE-10 | NIST, [Measures, uncertainties, and significance test in operational ROC analysis](https://www.nist.gov/publications/measures-uncertainties-and-significance-test-operational-roc-analysis) | 운영점/불확실성 참고. 현재 CAPTCHA의 독립 성능 근거 아님 |
| SCORE-11 | NIST, [Comparison of confidence intervals for large operational biometric data: parametric and non-parametric](https://www.nist.gov/publications/comparison-confidence-intervals-large-operational-biometric-data-parametric-and-non) | 군집/독립성·분모 구분의 후속 참고. 완전한 서지/정확한 적용 조건 전사 필요 |

주요 코드: `analysis/literature_similarity.py`, `validation_v03/standard_metrics.py`, `validation_v03/compare_scores.py`; [채점 명세](scoring_standardization_v0.3.md). 각도/뼈 DTW·원시 feature·미분·점수/관문/인증을 구분한다.

## CAPTCHA·가림·사용성 선행 자료

[주장 근거표](claim_evidence_matrix.md)와 [3D 명세 §8](3d_hand_object_challenge_requirements_v0.1.md#8-외부-연구와-사용권)의 기존 확인 범위를 유지한다. 아래 자료는 생체 관절 한계의 근거가 아니다.

| 안정 ID | 자료/찾는 링크 | 기록된 확인 범위·후속 |
|---|---|---|
| PRIOR-01 | Shumilov & Philippovich2014, [Using 3D Animated Hand Gestures to Create a New Type of CAPTCHA](https://ceur-ws.org/Vol-1197/paper22.pdf) | 프로그램3D손/충돌/CAPTCHA 선행. 문자/숫자 읽기와 camera 모방을 구분한 기존 기록 |
| PRIOR-02 | Shumilov & Philippovich2016, [Gesture-based animated CAPTCHA](https://doi.org/10.1108/ICS-12-2014-0082) | **공개 초록만 확인한 기존 기록**, 본문 대비 대기 |
| PRIOR-03 | Shim et al.2026, [Designing cognitive 3D immersive CAPTCHA for human verification in virtual reality systems](https://doi.org/10.1007/s10055-026-01487-z) | 3D 공간 상호작용 선행. 물체 선택과 가려진 손·접촉 모사는 동일 과제 아님 |
| PRIOR-04 | Usuzaki et al., IEICE ComEX2025, [J-STAGE DOI10.23919/comex.2025COL0018](https://www.jstage.jst.go.jp/article/comex/14/12/14_2025COL0018/_article/-char/en) | 가려진 한자 CAPTCHA. 기존 보고서의 연도/철자 차이 유지, 손동작 방어로 확대하지 않음 |
| PRIOR-05 | Pothiraj et al., ICCV2025, [CAPTURE](https://openaccess.thecvf.com/content/ICCV2025/papers/Pothiraj_CAPTURE_Evaluating_Spatial_Reasoning_in_Vision_Language_Models_via_Occluded_ICCV_2025_paper.pdf) | 가려진 객체 수 추론 benchmark. 손 관절/모방/인증 과제와 구분 |
| PRIOR-06 | Searles et al., USEC2025, [reCAPTCHA v2 연구 PDF](https://dev.ndss-symposium.org/wp-content/uploads/usec25-21.pdf) | 다른 표본 SUS 점수는 우리UI의 무작위 직접 비교가 아님 |
| PRIOR-07 | Panwar et al., CICT2018, [DOI10.1109/INFOCOMTECH.2018.8722409](https://doi.org/10.1109/INFOCOMTECH.2018.8722409) | 기존 기록상 서지/초록 확인·**본문 미열람**. 보고서의 prototype/오분류 수치 원문 대조 대기 |

## 기하·표면 교차 검사 — 생체 근거와 분리

| 안정 ID | 자료 | 검토한 위치와 상태 |
|---|---|---|
| GEO-01 | David Eberly, [Intersection of Convex Objects: The Method of Separating Axes](https://www.geometrictools.com/Documentation/MethodOfSeparatingAxes.pdf), 문서 수정2022-06-20 | 11월15일 §9/PDF18쪽의 두 삼각형 축 후보·공면 처리 관련 절을 확인. handcaptcha `mesh_intersections.py`에 독립 구현, [192프레임·후보66,568쌍 진단](deliveries/2026-11-15_mano_surface_intersections.md). 인접 면 제외·샘플 시간·수치 허용값은 프로젝트 선택이며 부피/연속/생체 검증 아님 |
| GEO-02 | Tomas Möller1997, [A Fast Triangle-Triangle Intersection Test](https://web.stanford.edu/class/cs277/resources/papers/Moller1997b.pdf), [출판 DOI](https://www.tandfonline.com/doi/abs/10.1080/10867651.1997.10487472) | 11월15일 원 논문 검색 결과에서 평면 거리/교차 방법을 확인한 대안 참고. 알고리즘 구현/전체 원문 검토 완료로 표시하지 않음 |

기하 검사에서는 접함·공면·교차 의심, 인접 면 제외와 수치 오차, 샘플 사이 충돌 누락을 구분해야 한다. 이 문헌은 관절의 생체 허용 각도·속도·사람 편안함의 근거가 아니다.

## 권리·표준·특허는 별도 근거

- [MANO 라이선스](https://mano.is.tue.mpg.de/license.html), [GRAB 라이선스](https://github.com/otaheri/GRAB/blob/master/LICENSE): 논문 인용과 자산 사용/재배포 허용은 별개다. 동봉 버전을 보존하며 현재 페이지로 교체하지 않는다.
- [US11409855B2 claims](https://patents.google.com/patent/US11409855B2/en): 학술 생체 근거가 아닌 선행기술 검토 항목이다. 특허성/법적 결론으로 확정하지 않는다.
- [Cloud 이전 조사](codex_cloud_migration_preparation_2026-11-14.md): 모델의 외부 전송·호스팅은 별도 확인/승인 항목이다. 현재 로컬 연구를 계속한다.

## 앞으로 자료를 찾고 기록하는 규칙

1. 새 논문을 쓰기 전에 안정ID·정확한 제목/저자/연도/학회·DOI/저자/학회 원문·보충/공식 코드와 revision을 추가한다. 서지 미확인은 표시하고 추정으로 채우지 않는다.
2. 원문 열람 수준과 날짜, 적용 절·식·표/페이지를 적는다. 초록 확인을 원문 검토로, 검색 결과를 코드 재현으로 바꾸지 않는다. 링크 오류/403·대체 원문도 기록한다.
3. 주장/규칙→출처→대상/단위/좌표 대응→코드→실제 검사/실행 근거를 연결한다. **논문의 근거·프로젝트의 구현 선택·실험 관측**을 나눠 쓴다.
4. 실제 생체 수치·허용 hull·시간 한계·불확실성을 추출하면 출처 ID와 적용 범위를 profile의 evidence에 넣고 이 색인의 미확인 칸도 갱신한다.
5. [앞으로 할 일 통합표](remaining_work_master_2026-11-15.md)를 함께 갱신한다. 공식 링크/서지 중심으로 보관하며 논문/자산의 공개 여부를 파일 재배포 권리로 해석하지 않는다.
