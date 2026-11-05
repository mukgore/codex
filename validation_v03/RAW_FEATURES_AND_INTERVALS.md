# 원시 특징 일치와 군집 구간 (2026-11-05)

`raw_features.cjs`는 Python adapters.py의 명시적 좌표/시간/미러/분리 block, 15각도, band DTW, 실제 초 기반 2차 gradient/가속도와 위상 재표본화의 독립 JavaScript 구현이다. CommonJS module이며 stdin JSON CLI로도 검사할 수 있다. prod UI/점수/임계값에 연결하지 않았고 score는 null이다. 실제 adoption 이후의 JS shadow 검증을 대신하지 않는다.

검사에는 단위/미러/누락/잘못된 기하/큰 gap, 불규칙 시간의 원시 특징, seeded DTW와 tie path, 잘못된 timestamp/spec 거부를 포함한다. 정상 위치 오차1e-12, 각도2e-6도, 비교 특징2e-9의 허용을 검사에 명시한다. 수치 범위가 다른 실제 후보/긴 sequence/다른 브라우저 engine의 검증은 별도다.

`compare_scores`의 기존 CSV 명령에 다음 세 인수를 함께 추가하면 검증 split에서 고정한 두 threshold로 test의 paired percentile cluster bootstrap을 계산한다:

```text
--cluster-repetitions 2000 --cluster-seed 7 --cluster-confidence 0.95
```

같은 참가자·촬영·구성 원본 family 중 하나라도 공유한 행을 연결 성분으로 묶어 resample한다. human/attack별 score accept / 모든 attempt를 계산하며 기술 실패/중단을 분모에서 제거하지 않는다. 동일 resample로 candidate-legacy 차이도 계산한다. raw ID는 결과에 내보내지 않는다. 입력의 전체 split 계보 중복 검사를 먼저 통과해야 하며 test로 threshold를 재선택하지 않는다.

독립 cluster가 하나면 INSUFFICIENT_CLUSTERS/구간없음으로 남긴다. 모든 resample 값이 같으면 DEGENERATE_RESAMPLING/구간없음으로 남겨 0건 관찰을 0 위험의 확증처럼 표시하지 않는다. resampling 독립성/계보 진실성·연구 프로토콜은 사용자가 검토해야 한다. 사람/공격 joint 신뢰구간, 전체 세션/보호행위 위험 보장, 실제 데이터 기반의 성능 개선 결과는 아니다.
