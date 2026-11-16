# S05: 사전 지정 유형의 군집 사건 동시 상한

[simultaneous_risk.py](simultaneous_risk.py)는 test 점수 CSV와 별도 사전 계획 JSON을 받는다. 기존 [군집 bootstrap](cluster_intervals.py)의 주변 구간과 다른 종점이다. **고정된 유형별 시도 예산 안에서 한 군집이 한 번이라도 점수 수용되는 사건**을 센다. 시행별 FAR·사람 수용률·자세/hold·전체 인증 성공의 상한으로 읽지 않는다.

## 방법과 조건

각 유형에서 군집이 iid Bernoulli 단위이고 평가 이전에 기준·유형·시도 예산/명단이 고정돼 있다는 조건이 필요하다. 같은 참가자/capture/구성 source를 공유하는 test 행 전체를 먼저 연결하고 유형별로 거른다. 연결 성분이 실제 독립임을 코드가 증명하지는 않는다. 유형 간·두 채점 방식 간 독립성은 Bonferroni에 필요하지 않다.

유형 수 K, 두 방식의 총2K개 상한에 각각 `delta=(1-confidence)/(2K)`를 배정한다. n군집 중 x사건이면 일측 Clopper–Pearson 상한은 `BetaInverseSurvival(delta; x+1,n-x)`이며 x=n이면1이다. x=0이면 `1-delta**(1/n)`로 계산해0위험 오류를 피한다. 최악 사전지정 유형의 상한은 유형별 상한의 최대다. 미관측 유형은1이며 이후 마음대로 유형을 제거해 값을 낮출 수 없다.

근거는 NIST의 [정확 이항 상한](https://www.itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbici.htm)의 이항 CDF 역산과 [Bonferroni 일반 부등식](https://www.itl.nist.gov/div898/handbook/prc/section4/prc473.htm)이다(확인2026-11-17). NIST의 일반 부등식을 우리 사전지정 종점2K개에 적용했다. 수치 역산에는 기존 SciPy1.15.3의 `scipy.special.betainccinv`를 사용하며 환경을 새로 설치하지 않았다.

기술 오류·중단·군집 내부의 예산 미달은 수용 가능 사건으로 처리한 보수적 상한을 계산한다. 관측 수용 군집 수와 미확정 군집 수는 별도다. 군집 자체가 계획 수보다 빠졌으면 전체 유형 상한은1이다. 계획보다 많은 군집/시도·사전계획 밖의 유형·split 누출은 거부한다. 기록되지 않은 군집이나 출처를 자동 발견할 수는 없다. 소실과 실제 거부를 구별하려면 원로그·완전한 시행 명단 검증이 별도로 필요하다.

## 입력과 사용

CSV는 기존 [점수 비교 계약](SCORE_DIAGNOSTICS.md)을 따르며 모든 행에 `attack_family`가 필요하다. development/validation/test마다 scored human/attack이 있는 기존 계약도 유지한다. 아래 계획은 **설명용**이며 실제 평가 사전등록이 아니다.

```json
{
  "schema_version": 1,
  "confidence": 0.95,
  "thresholds": {"legacy_score": 0.25, "candidate_score": 0.6},
  "families": {
    "replay": {"clusters_n": 100, "attempts_per_cluster": 3},
    "stationary_hand": {"clusters_n": 100, "attempts_per_cluster": 3}
  },
  "thresholds_locked_before_test": true,
  "iid_clusters_within_family": true,
  "fixed_attempt_budget_before_test": true,
  "complete_test_roster": true
}
```

```powershell
python -m validation_v03.simultaneous_risk --input PRIVATE_TRIALS.csv --plan PRIVATE_PLAN.json --output NEW_PRIVATE_REPORT.json --data-scope observed
```

네 선언은 실제 프로토콜/명단 검토 후 입력한다. 하나라도 false면 상한은 null이다. 도구는 선언의 진실이나 계획 고정 시각을 인증하지 않는다. threshold 탐색 기능은 없으며 test를 본 뒤 기준·모델·유형·예산을 고르면 이 조건부 해석은 무효다. 출력은 재사용하지 않은 새 경로에만 쓴다. 입력/계획의 무결성 hash는 비공개 보고서에 남긴다.

## 검증과 남은 평가

새11검사는 정확한 이항 꼬리방정식·유한표본 비포함 확률·0/전체 사건·2K 보정·빠진 유형·오류/중단/부분 예산·반복 군집·다른 유형을 통한 연결·가정 누락·과다 예산/누출·CLI 덮어쓰기 거부를 검사했다. 기존 군집8검사와 MediaPipe4검사를 합해23검사 통과다. 합성 fixture의 수학/엔지니어링 검산이며 사람/공격 실험 실행은 아니다.

S05의 이 종점 구현 공백을 해소했으나 독립 실제 평가, 희귀 위험을 제한할 표본수, 사람 수용성과의 공동 기준, 기기/운영 범위와 인증 위험은 미완료다. 공급 family가 하나인 최신 TF-04/MediaPipe 자료를 독립 군집 자료로 바꿔 이 도구에 넣지 않는다.
