# 3A 대응 비교와 3B 점수 진단 — 2026-11-10

기준 사용자 화면과 설계는 `handcaptcha/hand_captcha_prod.html`이다. 아래 도구는 비공개 수집 자료를 오프라인으로 분석하며 prod UI·채점식·0.25 기준을 수정하지 않는다. 구현 검사에 쓴 입력은 합성 fixture이며 실제 사람 성능 결과가 아니다.

## 3A: 같은 시행 조건의 모방·정지·오답 비교

`python -m validation_v03.paired_controls --input ../private_artifacts/controls.json --output ../private_artifacts/controls_report_NEW.json`

입력 JSON의 최상위는 `data_scope`와 `trials`다. `data_scope`는 `observed`, `synthetic`, `unspecified` 중 하나이며 호출자의 선언이다. 코드가 실제 촬영·동의·출처를 증명하지 않는다.

| 필드 | 필요한 값 |
|---|---|
| trial_id, capture_id | 실제 시행·촬영 식별자. 같은 촬영을 다른 조건으로 재라벨하지 않음 |
| protocol_id, participant_id | 잠근 실험 버전과 비공개 참가자 ID |
| target_id, source_family_id | 목표 영상 버전과 원동작 계열. 목표 하나에 계열 하나 |
| camera_id, recording_seconds, repeat | 동일 카메라, 사전 정한 기록 길이, 대응 반복 번호 |
| score_origin | `offline_fixed_duration` 또는 `issued_live`. 두 결과를 합치지 않음 |
| condition | 아래 명시된 조건 코드 |
| outcome | `recorded`, `tracking_failure`, `timeout`, `technical_error`, `aborted` |
| legacy_score | [0,1]의 실제 기존 점수 또는 null. 기술 오류·중단에는 null |
| gate_pass, motion_completed | 서로 독립인 Boolean 또는 미관측 null. 문자열 `"False"`는 거부 |

조건 코드는 `normal_imitation`, `slow_imitation`, `small_imitation`, `hold_first`, `hold_middle`, `hold_last`, `wrong_order`, `partial`, `wrist_only`, `static_photo`다. 실제 정지 손과 사진 입력은 합치지 않는다. 동작 완료 판정은 점수와 별도 관찰/주석에서 가져온다.

정상 모방과 대조 입력은 **protocol·참가자·목표·family·카메라·기록 길이·반복·점수 출처가 모두 같을 때만** 대응된다. 가까운 점수를 골라 짝짓거나 다른 카메라를 조용히 합치지 않는다. 정상 짝 없음과 양쪽 중 미채점으로 차이를 못 낸 경우를 별도 센다. 양쪽 점수가 있을 때 `normal−control` 평균·중앙값, 역전·동점 수, 참가자별/목표별 평균의 집계를 낸다. 원 ID나 개인별 값의 배열을 출력하지 않는다.

각 조건에 전체 시도·채점/미채점·점수 수용/거부·관문 관측/통과·점수와 관문 동시 통과·동작 완료/미완료/미판정·추적 실패/시간 초과/기술 오류/중단을 따로 낸다. 누락·기술 오류를 0점 또는 공격 거부 성공으로 채우지 않는다. timeout/추적 실패에서도 고정 길이의 별도 오프라인 점수가 실제로 있으면 그 출처로 남길 수 있으며, 현장 발급 결과와 분리된다.

현재 실제 3A 입력은 없다. 이 도구에 기존 좌표 반복을 넣어 실제 카메라 시행으로 바꾸지 않는다. 시행을 수집하는 UI/카메라 코드는 추가하지 않았다.

## 3B: ROC/DET, AUC/EER, 공격 유형별 결과

기존 CSV의 필수 열과 source/참가자/capture 분할 검사는 유지한다. 옵션 `--curves`가 development/validation/test의 모든 경험적 ROC/DET 점과 AUC·EER 참고값을 추가한다. `--curve-plot`은 Matplotlib이 설치된 환경에서 PNG/SVG/PDF를 만든다. 모델·새 런타임 패키지는 자동 설치하지 않는다.

```powershell
python -m validation_v03.compare_scores --input ../private_artifacts/paired_scores.csv --output ../private_artifacts/score_report_NEW.json --min-human-accept <사전값> --max-attack-accept <사전값> --curves --curve-plot ../private_artifacts/curves_NEW.png --data-scope observed --cluster-repetitions 2000 --cluster-seed 7 --cluster-confidence .95
```

자리표시자 두 개는 관측 전에 정한 값으로 바꾼다. 예시 명령은 실제 값이나 승인된 연구 기준이 아니다. CSV·원본 fingerprint가 든 JSON·실험 그림은 검토 없이 공개하지 않는다. 합성 예시는 `--data-scope synthetic`으로 표시하며 그림 상단에도 합성 자료임을 명시한다.

- ROC x/y는 공격 수용률/정상 사람 수용률, DET x/y는 공격 수용률/정상 사람 거부율이다. DET는 확률 그대로의 선형 축이며 0/1을 임의 probit 값으로 치환하지 않는다.
- 모든 동점은 함께 처리한다. reject-all의 무한 threshold는 JSON에서 `threshold=null, accept_rule=reject_all`로 명시한다. 나머지는 `score>=threshold`다. 전체 표 계산을 매 threshold 전수 재검색에서 정렬/누적으로 바꿨고, 직접 Boolean 비교와 독립 순위 검산으로 확인했다.
- AUC는 사람 점수가 공격보다 높은 쌍에 1, 동점에 0.5를 주는 순위 해석과 일치한다. 낮은 공격 허용 영역의 성능을 대신하지 않는다. EER은 경험적 점 사이 확률 선형 보간 참고값이며 그에 따른 운영 임계값을 선택하지 않는다.
- 임계값 선택은 기존대로 **validation만** 사용한다. test 곡선과 최악 유형 결과는 잠근 임계값에서의 기술통계다. test 결과로 다시 고르면 새 버전·새 미사용 test가 필요하다.
- 곡선 분모는 채점된 시행이며, 전체 배정 시도·기술 오류·중단 수를 함께 기록한다. 기술 오류·중단은 성공 거부가 아니다. 고정 threshold 전체 시도 지표는 기존 endpoint를 함께 본다.

### 선택 열 `attack_family`

공격 유형별 결과가 필요하면 모든 CSV 행에 이 열을 넣는다. human 행은 비우고, attack 행에는 아래 코드 하나를 쓴다. 일부 공격만 코드가 있거나 임의 식별자가 들어오면 거부한다.

`replay`, `static_image`, `stationary_hand`, `wrong_motion`, `partial_motion`, `interpolation`, `reverse`, `shuffle`, `random`, `invalid_geometry`, `coordinate_injection`, `other_specified`

이는 평가한 공격 조건 코드다. 정상 사람이 잘못 따라 한 입력을 자동으로 ‘AI/공격자 신원’으로 라벨하는 변환은 하지 않는다. `other_specified`의 세부 정의는 비공개 사전 프로토콜에 남긴다. 새 유형은 코드/프로토콜 버전 변경으로 추가한다.

열이 없으면 유형별 결과는 `unavailable_no_attack_family_column`이다. 있으면 validation/test에서 각 유형의 시도·채점·오류·중단·점수 수용을 보고하고, 채점된 자료에서의 최악 수용률과 동률 유형을 명시한다. 미채점만 있는 유형은 최악률 0으로 만들지 않고 `families_without_scored_trials`로 남긴다. 기존 threshold 선택의 공격 제약은 **전체 공격을 합친 제약**이며 유형별 위험 상한을 보장하지 않는다.

군집 옵션을 함께 쓰면 test의 기존 전체 human/attack 구간에 더해 유형별 별도 bootstrap 구간도 낸다. source·참가자·capture 연결 성분은 **전체 test에서 먼저 만든 뒤** 유형을 고른다. 다른 유형을 매개로 연결된 자료도 독립으로 쪼개지 않는다. 한 군집은 `INSUFFICIENT_CLUSTERS`, 퇴화 재표본화는 `DEGENERATE_RESAMPLING`과 구간 없음으로 남긴다. 유형별 구간들은 개별 주변 구간이며, 모든 유형 또는 최악 유형을 동시에 덮는 신뢰구간이 아니다.

## 이번 검증 범위

신규 3A 8개, 점수 진단 7개, 기존 CSV 비교 7개·수학 12개·군집(확장 후) 8개 검사를 통과했다. 군집 연결 검사에는 다른 공격 유형을 통해 같은 family 자료가 연결되는 반례가 포함된다. 실제 CLI로 합성 CSV→JSON→그림→군집 연결과 기존 출력 덮어쓰기 거부를 확인했다. 그림을 열어 제목·범례·축·validation marker·합성 표시를 확인했다. 이 결과를 사람/공격 성능 향상이나 S05의 독립 평가 완료로 표시하지 않는다.
