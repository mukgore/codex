# prod 채점 감사 및 표준 수학 기반 전환 명세 v0.3

## 1. 범위와 실제 변경 상태

- 분석 대상: [mukgore/handcaptcha hand_captcha_prod.html](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/hand_captcha_prod.html)
- 기준 commit: 037873299a9e45435250aa158857b35e07668259
- prod blob: 7cdc3294ef95c74fa7f1a8ced3787dad4443e554. 같은 commit의 prod_modified와 blob이 같다.
- 위 버전은 현재 공개 prod이며, 과거 18명 수집 빌드라고 확정하지 않는다.
- 사용자 추가 지시로 prod 분석 및 개선을 시작한다. 기존 prod는 수정·배포하지 않고 codex에 비교용 수학 모듈을 추가한다.
- 이번에 구현한 것: 실제 DP DTW, 비균일 시간 간격 미분, 임계값별 사람/공격 수용률, validation 임계값 선택, 그룹 중복 검사.
- 이번에 수행한 것: 합성 수학 사례와 경계조건 단위 검사. 사람/AI 성능 재평가·분류기 학습은 아직 수행하지 않음.
- 후속 세션 파서·기하 보정·실제 데이터 평가·JS 통합은 아래 요구사항에 따라 이어서 구현한다.
- 원칙: 표준 방법 사용은 정의·비교·검증을 쉽게 한다. 보안 성능 향상을 자동 보장하지 않는다.

## 2. 쉬운 설명

지금 시험에는 두 문제가 섞여 있다.

- “손동작을 얼마나 비슷하게 따라 했나?”는 동작 채점 문제다.
- “이 답을 낸 쪽이 사람인가, 공격 프로그램인가?”는 구분 문제다.

동작을 아주 잘 따라 하는 공격도 있으므로 높은 동작 점수가 사람의 증명은 아니다.
먼저 자와 시계를 제대로 만들고, 그 자로 사람과 공격의 결과를 따로 재어 본다.
두 무리가 겹치면 숫자 하나를 바꾼다고 마법처럼 갈라지지 않는다.

## 3. 코드에서 확인한 내용과 조치

줄 번호는 위 고정 commit 기준이다.

| 위치 | 현재 구현 | 분석 및 요구 |
|---|---|---|
| 129–136 | gate 38도, 유지 200ms, threshold .25, weights .38/.37/.25, MX 고정 | 역사적 baseline 보존. 새 값은 train/validation에서만 선택 |
| getBaseFromLandmarkData 252–271 | x/width, y/height로 변환, 미검출 frame 제거, origIdx 별도 | 화면 종횡비와 원본 시간축을 유지하는 adapter 필요 |
| findKeyframes 276–290 | 프레임 차분, 11프레임 창, .005·15프레임 규칙 | 속도 단위와 간격을 초 단위로 정의하는 후보와 비교 |
| ang / ppSingle 294–308 | 2D 각도, 손목 원점, 손목-9번 크기 정규화 | 합리적 baseline이지만 퇴화 뼈·손 크기·종횡비 검사 필요 |
| onRes 726–836 | 미검출 null 기록, gate 연속 유지 200ms | 새 gate는 시간 연속성·검출 중단 재설정까지 별도 평가 |
| rs 844 | 검출된 배열 인덱스 선형 보간 | 실제 t를 무시. 결측 구간을 삭제한 시간 압축과 구분 필요 |
| mA 845 | 리샘플 후 15각도 평균 절대오차 | MAE 자체는 표준적. 모두 교체할 이유는 없음 |
| mDA 846 | 1.2배 늘린 뒤 슬라이딩 최솟값 | 실제 DTW 아님. legacy 명칭은 유지하고 새 진짜 DTW 후보 추가 |
| mAc 847 | XY 이차 차분 크기 오차, 시간 미사용 | m/s² 아님. 시간 미분과 위상 변화량을 구분 |
| es 848 | max 기준 선형 정규화·클리핑 후 detection rate 곱함 | 손 검출 품질과 동작 유사성이 한 점수에 섞임 |
| computeScores 850–868 | 검출 3개 미만 구간 제외 후 전체 연결 | 구간 경계·null 삭제·누락 구간의 영향을 별도로 검사 |
| result 904–906 | final score >= .25를 passed로 저장 | 동작 유사도 점수를 사람 확률/서버 인증으로 해석 금지 |
| 설정 및 결과 141–145, 913 이후 | SAVE_LOCAL_JSON=false, UPLOAD_URL 빈 문자열, 결과 뒤 reload | 이 설정 그대로 신규 실험하면 영구 로그가 안 남을 수 있음. 수집 전 저장·수신 확인 필요 |

추가 구조 한계: 정답 landmark가 브라우저에서 공개 fetch되고 최종 score도 클라이언트 계산이다.
점수식을 개선해도 정답 노출/클라이언트 통과 신호 신뢰 문제는 해결되지 않는다. V3 전체 경로에서 별도 다룬다.

## 4. S1 — 좌표·누락·시간축 표준화

### S1-01 좌표 공간

- 기준영상과 카메라 각각 width/height를 기록한다.
- 기하 계산 전 정규화 x,y를 동일 축 단위로 바꾼다: 예를 들어 (x*width, y*height) 픽셀 좌표.
- 그 뒤 손목 중심 이동과 손목-9번 길이로 나눈다. 각 프레임의 scale이 너무 작거나 뼈 길이가 퇴화하면 invalid로 표시한다.
- mirror는 센서 좌표/표시 좌표/기준 좌표를 구분하고 한 번만 적용한다.
- 회전 정렬/Procrustes는 선택적 ablation이다. 손 방향 차이가 정답을 구분한다면 회전 불변화가 보안을 떨어뜨릴 수 있다.
- 현재 기록에 영상 크기가 없다면 임의 720×720로 채우지 않는다. legacy normalized-XY 분석과 기하 보정 분석을 구분한다.
- z를 추가하면 정확해진다고 가정하지 않는다. 좌표계·스케일·추정 품질을 검증한 별도 후보로 둔다.

수용 검사: 같은 실제 손 기하를 다른 종횡비로 표현해도 보정 후 각도가 일치한다.
반전 적용 횟수, 퇴화 관절, 비유한 입력의 처리도 fixture로 검증한다.

### S1-02 시간과 결측

- 사람은 segment.frames[].t 밀리초를 초로 바꾼다. 구간 경계에서 시간이 리셋되면 구간별 처리한다.
- 기준은 원본 frame_idx/fps 또는 실제 타임스탬프를 사용한다. 검출된 배열 인덱스/fps로 대신하지 않는다.
- 단조 증가·중복·큰 공백을 검사한다. null을 제거한 뒤 남은 샘플을 연속 시간으로 취급하지 않는다.
- 짧은 결측의 보간 허용 길이, 최소 coverage, 최대 연속 결측, 분석 제외 경계를 dev 단계에서 고정한다.
- 불연속/다른 clip 경계를 미분하지 않는다. 첫 구현은 완전한 연속 구간만 받아들이고 나머지는 ValueError로 명시한다.
- 실제 시간 비교와 0–1 수행 위상 비교를 다른 특징으로 기록한다. 위상 미분을 물리 가속도로 부르지 않는다.
- 재표본화는 초 단위 grid 또는 명시적 phase grid를 선택하고 grid 간격/길이를 manifest에 기록한다.

## 5. S2 — 실제 DTW를 비교 후보로 도입

기존 sliding_angle_mae_legacy와 새 dtw_angle_distance를 별도 열로 보존한다.
새 후보는 각 프레임의 15개 관절 각도 벡터를 입력으로 받는다.

D(i,j) = ||a_i - b_j||² + min(D(i-1,j), D(i,j-1), D(i-1,j-1))

- 시작과 끝을 모두 연결한다. 허용 이동은 (1,1), (1,0), (0,1)이다.
- 이번 구현의 band는 명시적 |i-j| <= radius이다. 불가능하면 band를 자동 확장하지 않고 오류를 반환한다.
- 길이가 다른 자료는 명세된 시간/phase grid로 먼저 맞추거나 충분한 radius를 미리 고정한다.
- radius와 grid를 test 결과에 맞춰 바꾸지 않는다.
- 표준 거리 sqrt(최적 누적 제곱오차)를 저장한다.
- 별도 파생 특징 path_rmse=sqrt(최적 누적 제곱오차/(경로 길이×각도 수))를 저장한다. 평균 비용 자체를 최소화한 경로라고 주장하지 않는다.
- DTW가 시간 차이를 과하게 허용해 오답도 맞춰 주는지 정지/역전/틀린 순서 대조군으로 검사한다.
- 경로 길이, 대각선 이탈, 긴 반복 정렬 구간도 기록한다.
- 계산·메모리 예산을 둔다. 현재 참고 구현은 n*m 1,000,000 cell 초과를 거부한다.

구현 상태: validation_v03/standard_metrics.py의 constrained_dtw.
수용 검사: 작은 모든 경로를 열거하는 독립 계산과 최적 비용 일치, identity, 시간 늘임, 다른 순서, band 불가능, 비유한 값 검사.
보안 채택 조건: 새 test에서 오답/공격 감소와 인간 허용폭을 함께 만족. DTW라는 이름만으로 채택하지 않는다.

## 6. S3 — 시간에 맞는 속도·가속도

- 현재 index_second_difference_legacy를 보존한다.
- 새 후보는 실제 t_seconds를 넣은 numpy.gradient로 속도와 가속도를 계산한다.
- 정규화 손 길이 좌표면 단위는 hand_length/s, hand_length/s²다. 실제 미터 단위가 아니다.
- 각도 특징이면 deg/s, deg/s²로 명시한다.
- 샘플 간격이 불규칙하면 t 배열을 직접 제공한다.
- 미분은 잡음을 증폭한다. 평활화가 필요하면 균일 grid에서 Savitzky–Golay 등의 창·차수·경계 규칙을 dev에서 정하고 무평활 baseline과 비교한다.
- Savitzky–Golay의 delta는 균일 샘플 간격이다. 불규칙 데이터를 그대로 넣어 해결됐다고 하지 않는다.
- 구간의 처음/끝 미분값과 추적 지터 민감도를 보고하고, 동일 근육 움직임을 다른 FPS로 측정한 안정성을 검사한다.
- 가속도 특징이 판별에 기여하지 않으면 제외 후보도 비교한다. 기존 .37 가중치를 자동 승계하지 않는다.

구현 상태: time_derivatives. 기본 평활화나 결측 보간은 없으며 호출자가 gap 한도를 명시해야 한다.
검사: 불균일 시각에서 x=t²의 v=2t, a=2; 시간축 2배의 속도 1/2·가속도 1/4; 중복 시각·큰 공백·null 거부.

## 7. S4 — 점수 결합을 표준 분류 문제로 검토

### S4-01 레이블

- legitimate_human=1, evaluated_attack=0으로 방향을 고정한다.
- “모든 AI”를 대표한다고 하지 않는다. attack_family와 knowledge budget을 기록한다.
- 틀린 동작을 하는 사람은 V1 wrong-answer 데이터다. 단순히 AI=0으로 바꾸어 신원 분류 학습에 넣지 않는다.
- 인간/공격 자료가 서로 다른 challenge·빌드·환경이면 분류기가 그 차이를 학습할 수 있다. 같은 프로토콜 대응 자료가 확보되기 전 학습 결과는 탐색 한정이다.

### S4-02 비교 후보

- B0: 기존 MX/가중치/.25 전체 보존.
- B1: 각도 MAE 또는 constrained DTW 한 특징 + validation 임계값. 단순 기준.
- B2: StandardScaler + L2 정규화 LogisticRegression의 작은 특징 집합.
- B3: B2에서 시간 특징/품질 특징을 하나씩 빼는 ablation.

품질 후보: coverage, 최대 연속 결측, 구간 완료 여부.
동작 후보: 각도 MAE, constrained DTW, 시간/위상 변화 오차.
특징 수를 표본 수보다 과도하게 늘리지 않는다.
장치·촬영자·파일 길이 등 우연한 출처 차이를 “사람다움”으로 배우지 않는지 조사한다.

### S4-03 학습·검증

- StandardScaler·결측 처리·특징 선택·정규화 강도는 train 내부에서만 fit한다.
- 참여자와 source 중 하나만 묶은 단순 GroupKFold로 모든 누출이 해결된다고 가정하지 않는다.
- 동일 참여자 또는 동일 source/capture로 연결된 표본을 그룹으로 묶거나, 목적에 맞는 별도 cohort로 분리한다.
- 연결 성분이 하나로 합쳐져 독립 test가 없어지면 추가 수집 필요를 보고한다.
- 미관찰 source, 미관찰 참여자, 미관찰 attack_family를 별도 일반화 질문으로 평가한다.
- 후보 선택은 그룹을 보존한 내부 검증, 최종 평가는 잠근 test 한 번이다.
- 로지스틱 출력도 자동으로 운영의 “사람일 확률”이 아니다. 클래스 비율·선정 공격·분포가 바뀌면 해석이 달라진다.
- 확률을 표시하려면 독립 calibration, reliability plot/Brier score와 운영 분포 가정을 추가한다.
- 작은 기존 표본에서는 복잡한 분류기보다 B0/B1 오류율 곡선부터 평가한다.

구현 상태: 설계만 완료. 실제 레이블 데이터 adapter와 B2 학습기는 미구현이며 결과를 만들지 않는다.

## 8. S5 — ROC/DET와 운영 임계값

점수가 클수록 사람으로 수용한다는 방향을 고정한다.

- Human accept rate = 수용된 정상 사람 / 정상 사람 수.
- Human reject rate = 거부된 정상 사람 / 정상 사람 수.
- Attack accept rate = 수용된 평가 공격 / 평가 공격 수.
- ROC: x=attack accept rate, y=human accept rate.
- DET: x=attack accept rate, y=human reject rate. probit 축을 쓸 경우 0/1 시각화 처리만 별도로 한다.
- 동점 점수는 같은 threshold에서 함께 처리한다.
- ROC-AUC는 전체 순위 분리의 보조 지표다. 실제 낮은 공격 허용 구간의 성능을 대신하지 않는다.
- EER은 두 오류율이 같은 지점의 참고값이며 보안 제품의 자동 운영 기준으로 쓰지 않는다.
- PR/precision을 보고하면 평가 데이터의 클래스 비율과 운영 prevalence 가정을 함께 쓴다.
- confusion matrix와 공격군별 최악의 오류율, 군집 단위 불확실성을 함께 보고한다.

운영 threshold 선택:
1. validation에서 최소 인간 수용률과 최대 공격 수용률을 사전 정의.
2. 두 경험적 제약을 만족하는 threshold 중 인간 수용률 최대, 공격 수용률 최소, 높은 threshold 순으로 선택.
3. 만족하는 값이 없으면 None/“실현 가능한 threshold 없음”. 임의 .25나 EER로 fallback하지 않음.
4. 잠근 threshold를 test에 적용해 같은 지표와 불확실성을 보고.
5. 경험적 validation 제약 충족은 모집단 위험 상한 보증이 아님.
6. score-only 곡선과 전체 gate+input protection+server 흐름의 오류율을 구분.

구현 상태: operating_point, threshold_table, select_validation_threshold.
split_name 검사만으로 실제 데이터 독립성이 입증되지 않는다. source/participant/capture manifest를 별도 검증해야 한다.
현재 함수는 complete score 배열만 받는다. null 실패 사례는 세션 adapter에서 별도 분모로 보고해야 하며 삭제해서 성능을 올리면 안 된다.

## 9. S6 — 자세 관문·구간 집계·데이터 수집

- 최신 prod의 38도/200ms 유지 규칙을 legacy 기준으로 기록한다.
- gate 진입/이탈, 유지 시간, 검출 끊김, 프레임 공백을 로그에 남긴다.
- 프레임 사이 미관측 시간을 무조건 연속 자세 유지로 인정하지 않는 gap 규칙을 검토한다.
- keyframe 탐색의 프레임 간격을 초 단위 속도·최소 간격 후보로 전환한다.
- 전체 연결 점수와 구간별 점수 집계를 비교한다. 짧은 실패 구간이 긴 정상 구간 평균에 묻히는지 본다.
- 구간마다 필수 최소 coverage와 누락 사유를 유지한다. 다른 clip 사이 전환은 별도 범주다.
- 신규 수집 전에 저장 성공 및 재로드 round-trip을 검사한다. source hash/manifest/scoring_version/실제 영상 크기를 기록한다.
- 저품질 입력은 무조건 공격이라고 단정하지 않는다. quality reject/retry와 attack reject를 구분한다.

## 10. S7 — 이행·검증·중단 순서

1. legacy 동작은 기존 분석 코드로 재현 유지.
2. 실제 prod 출처 고정 및 수학 primitive 합성 테스트: 이번 시작 범위.
3. 구간/time/missing/source adapter 구현과 원자료 일부 독립 검산.
4. 동일 trial에서 legacy와 B1 특징을 나란히 산출. 실자료 부족이면 BLOCKED.
5. source/참여자 대응 자료와 분할 확보 후 ROC/DET와 validation threshold 평가.
6. 충분한 독립 자료가 있을 때 B2와 ablation 비교.
7. 개선을 확인한 후보만 JS shadow mode로 이식하고 Python/JS parity 검증.
8. 실제 사람을 차단하지 않는 비교 운영 뒤 별도 배포 결정.

수학 함수가 맞아도 자료가 두 집단을 나누지 못하면 채점 조정만으로 해결하려 하지 않는다.
B1/B2가 B0보다 안 좋으면 기존 방법 유지 또는 문제 설계 수정으로 결론 낼 수 있다.

## 11. S8 — 실행 및 인수 조건

파일:
- validation_v03/standard_metrics.py
- tests/test_standard_metrics.py

실행:
```bash
python -m unittest discover -s tests -p test_standard_metrics.py -v
```

현재 실행 환경: Python 런타임의 NumPy 2.3.5에서 12개 테스트 통과.
기존 requirements.txt는 NumPy 2.2.6이며 이번 변경은 그 파일을 수정하지 않는다.
2.2.6 환경에서의 재실행은 아직 하지 않았다.
추가 sklearn 비교 검산은 설치된 1.8.0의 roc_curve(drop_intermediate=False)와 100개 합성 사례에서 임계값·FPR·TPR 일치를 확인했다. 제품 의존성으로 추가하지 않는다.

12개 테스트는 192개 작은 DTW 사례의 모든 허용 경로 열거 비교,
시간 미분의 해석적 정답, 점수 동점/방향, 불가능한 threshold,
test에서 threshold 조정 거부, source 누출 검사를 포함한다.
이것은 구현 정확도 검사이며 실제 사람/공격 구분 성능 결과가 아니다.

## 12. 공식 방법 자료

아래 자료는 방법 정의의 근거이며 이 CAPTCHA의 효과를 입증하지 않는다.
조회일은 이번 작업 기준, 설치 버전과 웹의 최신 문서 버전은 다를 수 있다.

- [tslearn DTW 정의와 DP·경로 제약](https://tslearn.readthedocs.io/en/stable/user_guide/dtw.html)
- [NumPy gradient: 비균일 spacing 및 미분](https://numpy.org/doc/stable/reference/generated/numpy.gradient.html)
- [SciPy Savitzky–Golay와 delta](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.savgol_filter.html)
- [scikit-learn ROC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_curve.html)
- [scikit-learn DET](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.det_curve.html)
- [scikit-learn threshold tuning 및 학습 자료 재사용 경고](https://scikit-learn.org/stable/modules/classification_threshold.html)

전체 실용성 검증과 결합: [practical_validation_requirements_v0.3.md](practical_validation_requirements_v0.3.md).
