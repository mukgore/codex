# CAPTCHA 재현 검증 및 A/B 분석

판정 기준: **확인됨**은 읽은 원자료에서 직접 확인, **조건부 재현**은 후보 구현/기준 데이터를 적용하면 저장값이 재생됨, **미확인/자료 부족**은 실제 수집 출처를 입증할 기록이 없음.

## 요약

- **DR4 — 조건부 재현 완료:** 독립 Python 구현으로 A/B 20 trial과 `prod_v2_pool` 18 세션의 JSON 점수를 다시 계산했다. 38/38 비교 행에서 원시 지표, 추정 지표, 최종 점수, 탐지율 및 프레임 수가 저장값과 허용오차 내 일치했다. 이는 현재 확인한 후보 HTML/랜드마크·pool 자료에 조건부이며, 세션별 실행 빌드를 확증하지 않는다.
- **A/B — 분석 완료:** 고유 참가자 10명, 각 A/B 한 trial(총 20 trial)이다. A 점수 평균 0.6451, B 0.5094. 참가자별 B−A 평균 −0.13567 (95% paired-t CI −0.17704…−0.09430, paired dz −2.346, 정확 양측 sign-flip p=.001953; 10/10에서 B가 낮음).
- **실제 판정/통과율:** A/B JSON에는 `passed` 결과가 저장되지 않았다. HTML의 `.25` 상수도 A/B 결과 기록에서 통과 판정으로 사용되지 않는다. 따라서 threshold 통과율은 **자료 부족**이며 사후 점수로 관측된 것처럼 만들지 않았다.
- **DR6 — 부분 완료:** 후보 코드와 JSON 스키마·상수·산출값의 호환은 확인했으나 실제 실행 HTML 빌드, 브라우저 설정, 세션별 baseline/pool manifest 연결은 미확인이다.
- A/B와 prod18은 별도 코호트로 유지했다. 새 실험, 공격, CAPTCHA 기능 개발은 수행하지 않았다.

## A/B 설계 및 측정 정의

- 후보 수집기: `<local approved input path>` (`ab_v2_3actions`). A는 reference video 재생 모드, B는 정적/keyframe/fade 제시 모드로 코드에 정의돼 있다. A/B JSON의 `version`, `keyframeSpec`, 두 trial 객체는 이 구조와 호환된다. 호환은 실제 실행 증명과 다르다.
- A/B 원자료: `<local approved input path>` (10개). 기준 랜드마크: `<local approved input path>`.
- prod 후보: `<local approved input path>`; 비교 대상 JSON 18개: `<local approved input path>`. 사용된 pool 설정: `<local approved input path>`; 선택된 기준 landmark 실제 파일은 the local-only input hash inventory (excluded from this repository)에 각각 나열했다.
- 고유 `participantId` 10개가 있고 중복은 확인되지 않았다. JSON의 `abOrder`는 AB 4명, BA 6명이다. 후보 HTML은 `Math.random()<0.5`로 순서를 배정하지만 난수 seed나 배정 로그는 저장되지 않아 무작위 배정의 실제 실행을 독립 증명할 수 없다.
- 각 조건에서 같은 참가자가 같은 keyframe/action 사양을 수행해 대응 비교는 자료 구조상 타당하다. 그러나 순서·연습·피로 효과 및 제시 방식 효과를 분리하지 못한다.
- 시간은 JSON `duration`을 밀리초로 저장하며 코드의 `performance.now()-trialStartTime`로 계산된다. 시작은 trial 진입/초기 포즈 매칭 구간 이전, 종료는 마지막 매칭 이후 지연된 완료 콜백으로 추적된다. 따라서 순수 재생 시간이나 순수 응답 시간으로 해석하지 않았다. inter-trial 대기 구간은 다음 trial 시간에 포함되지 않는다.
- `rA/rDA/rAc`는 원시 지표, `sA/sDA/sAc`는 탐지율과 최대 오차 상수를 적용한 추정 지표, `captcha`는 가중 최종 점수다. `tF/dC/dR`은 총 프레임/검출 프레임/검출률로 저장된다. 모든 trial에 11개 segment가 기록됐다. 단, 완료되지 않은 세션 분모는 없으므로 완주율은 산출할 수 없다.
- 조건 요약의 95% CI는 조건별 평균의 t 구간이고, 추론은 참가자 내 B−A 차이에 대한 95% paired-t CI와 2^10 전체 부호반전 exact 검정을 사용했다. 효과크기는 paired Cohen dz다. 구성 지표 검정은 다중비교 보정 전 탐색 결과다.

## A/B 주요 결과

| 지표 | A 평균 (중앙값) | B 평균 (중앙값) | B−A 평균 [95% CI] | exact sign-flip p |
|---|---:|---:|---:|---:|
| 최종 captcha 점수 | 0.64510 (0.64551) | 0.50943 (0.51355) | −0.13567 [−0.17704, −0.09430] | .00195 |
| angle (도) | 18.3857 (17.4103) | 34.5958 (33.5800) | +16.2101 [+11.1228, +21.2974] | .00195 |
| dtw_angle (도) | 23.7870 (23.3245) | 27.7934 (27.3625) | +4.0064 [+1.1135, +6.8994] | .01563 |
| accel | .02285 (.02301) | .02898 (.02605) | +.00613 [+.00016, +.01210] | .02734 |
| sA | .60079 (.61851) | .26069 (.28464) | −.34010 [−.44606, −.23414] | .00195 |
| sDA | .45416 (.45541) | .35993 (.37740) | −.09423 [−.15889, −.02957] | .01172 |
| sAc | .87113 (.87462) | .83103 (.86322) | −.04010 [−.08512, +.00491] | .06641 |
| duration (초) | 29.7479 (29.2068) | 31.3872 (29.9065) | +1.6393 [−2.3023, +5.5809] | .36133 |
| landmark 검출률 | .98827 (.99811) | .97769 (1.00000) | −.01058 [−.05038, +.02922] | .59375 |

점수의 방향은 B에서 일관되게 낮았지만, 표본은 10명이고 단일 조건 차이는 코드의 점수 정의 및 제시 방식에 종속된다. 수행 시간 및 검출률 차이는 불확실하며, `dtw_angle`/`accel` p값은 여러 구성 지표를 탐색한 결과라 확증적 결론으로 취급하지 않는다. AB/BA 순서별 점수 차이는 각각 −.12233(n=4), −.14456(n=6), 순서 상호작용 exact permutation p=.595이다. 시간 차이는 −2.075초 대 +4.115초(p=.095, 탐색적)로 보이지만 낮은 표본과 순서 교락 때문에 효과를 분리해 주장할 수 없다.

## DR4 계산 및 오류

`reproduce_scores.py`는 후보 HTML 함수를 호출하지 않고 JSON 랜드마크와 기준 랜드마크부터 별도 계산한다. 사용한 후보 계산은 XY 좌표를 프레임 크기로 정규화하고, 손목 기준으로 이동·중지점 거리로 스케일 정규화(하한 1e−6), A/B 기준 포즈를 생성한다. prod에서는 clip 손잡이/선택 손 차이에 따라 기준 x를 미러링한다. 관측과 기준은 같은 프레임 수로 선형 보간한다. 15개 AT triplet의 평균 각도 오차, 길이 round(1.2×기준)의 재표본화 후 sliding-window 최소 각도 오차(`dtw_angle` 명칭), 프레임 인덱스상 XY 2차 차분 크기 차이(`accel`)를 계산한다. 검출 없는 프레임은 제외되지만 총 프레임 분모에는 남고, 3개 미만 검출 segment는 유효 지표 표본에서 제외된다. 원시값은 MX `{angle:46.9413, dtw_angle:44.0014, accel:.1926}`과 가중치 `{.25,.38,.37}`로 제한 구간 추정치와 최종 점수로 변환된다.

38행 모두 저장값과 일치했다. 최대 절대 오차: angle 4.80e−14°, dtw_angle 4.62e−14°, accel 6.94e−18, 추정 angle/dtw 각각 9.99e−16, 추정 accel 0, 최종 점수 5.56e−16, 검출률 0. 모든 A/B keyframeSpec은 현재 baseline에서 재생성한 12개 keyframe과 일치했다. 이 숫자는 현재 구현 가정 아래의 산술 재현 일치이지 수집 당시 빌드의 확정 증거가 아니다.

## 산출물 및 재현 방법

로컬 분석 출력은 입력 해시와 가명화된 참가자별 표를 생성한다. 이 두 파일과 세션별 오차표는 개인별 연구 기록의 연결 가능성을 줄이기 위해 Git 저장소에 포함하지 않았다.

```powershell
python analysis\reproducibility\reproduce_scores.py --out data\derived\reproducibility
python analysis\reproducibility\analyze_ab.py --out data\derived\reproducibility
```

| 파일 | 용도 |
|---|---|
| `reproduce_scores.py` | 독립 좌표→원시/추정/최종 점수 재계산 및 저장값 검증 |
| `replay_errors.csv` | A/B 20 trial + prod18 세션별 저장값/재계산값/오차 |
| `replay_validation.json`, `replay_manifest.json` | 판정, 가정, 환경 및 재현 설정 |
| `analyze_ab.py` | 원본 A/B JSON을 직접 읽는 대응 통계 및 그림 생성 |
| `ab_participant_results.csv` | 참가자별 A, B, B−A 표(P01–P10) |
| `ab_condition_summary.csv`, `ab_paired_summary.csv`, `ab_stats_summary.json` | 조건·대응 통계 상세값 |
| `ab_paired_plot.png` | 점수, 시간, 검출률 paired plot |
| the local-only input hash inventory (excluded from this repository) | 원본 JSON, 기준 데이터, 후보 HTML, pool manifest 및 사용한 기준 clip 해시 |
| `artifact_sha256.csv` | 생성한 보고서·코드·결과 파일 해시 |
| `independent_verification.md` | 별도 구현으로 원본 JSON을 다시 집계한 교차검증 |

## 해결되지 않은 자료 공백

세션별 실행 HTML/build 해시, 브라우저·카메라 설정, 세션이 사용한 baseline 및 pool manifest 해시/매핑이 없다. 현재 후보 `hand_captcha_prod.html` 해시는 2026-07-29 수정 기록을 가진 파일 자체만 식별하며 실제 18건의 실행파일이라고 증명하지 않는다. 실행 당시 세션 manifest가 없어 실행 버전 확정은 불가능하고, SHA-256 및 수정일은 파일 동일성/시점 기록이지 실행 provenance가 아니다. DR3 프레임 1개 차이는 기존 G2/G3 집계상 8,782 segment frames 대 8,764 recording log frames(18 차이)이며, 세션별 공통 frame ID가 없어 일대일 대조는 미확인이다. 이 작업은 기존 G2/G3 프레임 결과를 다시 산출하거나 바꾸지 않았다.

다음 검증에 필요한 자료는 실행 당시 세션별 build/source hash와 설정 기록, reference/pool manifest digest, 프레임 공통 ID 또는 고정밀 단조 타임스탬프, 실제 참가자 배정 seed/log, 통과 판정 기록이다. 이 자료가 보존되지 않았다면 실제 실행 버전 및 통과율은 과거 기록만으로 복구할 수 없다.
