# v0.2 상태 보충 및 정정 — 2026-10-26

기준 현황은 [v0.2 요구사항 현황](v0_2_status_and_g4_next_steps_2026-10-26.md)이다. 이 문서는 그 후 추가로 확인한 사실에 한해 해당 보고서를 보충하며, 이전 보고서를 덮어쓰지 않는다.

## 정정 1: DR4 후보 지표

이전 현황의 “나머지 네 후보 지표는 검증 가능한 산식이 없어 값으로 계산하지 않았다”는 문장은 정정이 필요하다.

승인된 로컬 자료에서 과거 구현 `verified_final.py` 및 그 구현을 대상으로 한 별도 재생·검증 산출물을 확인했다. 그 산출물의 범위는 과거 인간 4세션 × 9 trial = 36 trial이며, `prod_v2_pool` 인간 18세션이나 A/B 코호트가 아니다. 원본 함수는 다음을 정의한다.

- `distance`: baseline frame 수에 맞춰 좌표를 선형 재표본화한 뒤, 손목을 제외한 20개 landmark의 평균 유클리드 거리를 계산한다. 전처리는 손목 원점 이동 및 wrist–MCP9 길이 정규화다.
- `dtw_distance`: 손목 제외 landmark 좌표 평균으로 각 프레임의 scalar 신호를 만들고 절대차 비용의 unconstrained DTW 경로를 구한 다음, 경로상 20개 landmark의 평균 유클리드 거리를 반환한다.
- `tendency`: 15개 landmark 쌍 거리 시계열의 Pearson 상관을 각각 구해 평균한다. 상수/비유한 상관은 0으로 둔다.
- `trajectory`: 10프레임 이상인 사용자 track의 손목 제외 각 landmark 좌표에 cubic Savitzky–Golay smoothing을 적용한다. 창 길이는 약 25%로 홀수·최소 5 조건을 적용하며, 각 landmark의 잔차 크기 변동계수(CV)를 평균한다.

기존 별도 검증 산출물은 이 과거 코호트에서 4개 raw metric의 독립 재계산 오차가 모두 (1.53\times10^{-14}) 이하, estimated 값 오차가 (1.05\times10^{-14}) 이하라고 기록하고 있다. 이것은 후보 정의 및 과거 코호트 재생을 뒷받침하지만, 해당 지표가 prod18 실제 수집 빌드에서 실행됐다는 증거는 아니다. 따라서 DR4는 계속 **PARTIAL**이다. prod18에 이 네 지표를 사후 적용하거나 임의로 산식을 옮겨 계산하지 않는다.

## 정정 2: G4 기존 추출 결과의 소스 재생

추가 보고서 [G4 pixel extraction replay](g4_pixel_extraction_replay_2026-10-26.md)는 보존된 8개 소스 클립에서 기존 추출 경로를 재실행해 저장된 프레임 수, bit sequence, Hamming/majority 판정이 8/8 일치했음을 기록한다. 이는 저장된 오프라인 결과의 픽셀 추출 계보를 보강한다. 독립 holdout, 동일 challenge human-vs-attacker 비교, 라이브 gate 또는 end-to-end 결과는 아니다. G4 실험 증거 상태는 여전히 **PARTIAL**이다.

추가 영상 일부는 기존 CAPTCHA 영상의 바이트 단위 중복본이어서 별도 표본이 아니다. 별도 비중복 영상은 challenge/reference pool/원본 gesture와 연결되는 manifest가 없어 holdout 근거로 채택하지 않았다.

## 상태 변경 요약

| 요구사항 | 현재 상태 | 이번 확인의 영향 |
|---|---|---|
| DR4 | PARTIAL | 네 후보 지표는 과거 별도 4-session 코호트에서 함수 정의와 독립 재생 근거가 있다. prod18 실제 실행 및 과거 빌드 연결은 미확인이다. |
| DR6 | EVIDENCE_LIMITED | 현재 재생 코드·환경 메타데이터와 과거 수집 빌드 증거의 공백을 해소하지 않는다. |
| G4 실험 증거 | PARTIAL | 기존 8개 source clip에 대한 추출 재생 근거가 추가됐다. 독립 평가 및 end-to-end 증거는 없다. |
| FR6 설계 | ACCEPTED — 설계만 | 기존 설계 템플릿의 범위와 한계는 그대로다. 실제 프로토콜 수치/연구자 승인 전 실행 가능한 등록은 아니다. |

## 재현 범위와 기록 한계

새 공개 보고서에는 원자료, 개인 식별자, 로컬 경로, raw input hash, trial-level 값이 없다. 후보 지표 검증 상세와 개인별 오차표는 승인된 로컬 출력물에 남아 있으며, 공개 저장소에 업로드하지 않았다. 위의 수치와 집계는 해당 로컬 산출물에서 확인한 집계이며 새 실행으로 가장하지 않는다.
