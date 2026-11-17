# 실제 SDK 경로의 조건부 시간구간 경계 — 2026-11-17

Euler→SciPy quaternion/matrix/axis-angle→float32→실제 SDK의 shifted-norm Rodrigues→pose blend/4×4 LBS를 감싸는 **조건부** 구간 경계를 구현했다. 단순한 이상적 회전이나 midpoint 최대값으로 건너뛰지 않았다. 개선 버전은768leaf 중764개에서 유한 후보를 만들고 저장196관측값을 모두 포함했다. **백엔드 오차 가정이 미검증이고4leaf가 미확정이므로 연속 무충돌/CCD 승인은 하지 않는다.**

[v1 사전등록](../sdk_path_boxes_preregistration_2026-11-17.md) · [v2 사전등록](../sdk_path_boxes_refinement_preregistration_2026-11-17.md) · [산술](../../analysis/runtime_benchmark/interval_boxes.py) · [경로/LBS](../../analysis/runtime_benchmark/sdk_path_boxes.py) · [실행](../../analysis/runtime_benchmark/sdk_path_box_probe.py) · [집계/비교](../../reports/tf03_sdk_boxes_20261117.json) · [leaf별 시간960행](../../reports/tf03_sdk_box_leaf_timings_20261117.csv).

## 계산 범위와 실제 결과

원TF-03의100시점과 이미 계산한96midpoint를 읽었다. 각 실행은 모델buffer2개를 읽었으며 SDK forward·새 영상/사람/독립 family·풀 채택은 모두0이다. 매번 원본/모델/기존 output을 보존했다.

| 항목 | v1 | v2 |
|---|---:|---:|
| 원래 .125초 구간당 고정 분할 | 2 | 8 |
| 시간leaf 시도 | 192 | 768 |
| 유한 조건부 후보 | 176 | 764 |
| 미확정 | 16 | 4 |
| 양쪽/전체leaf가 유한한 원래 구간 | 80/96 | 92/96 |
| 저장 checkpoint 비교(중복 포함) | 352 | 381 |
| 실제 비교된 고유 저장 시점 | 187/196 | 196/196 |
| 후보 밖 관측 좌표 | 0 | 0 |
| 검증된 backend 경계/CCD 승인 | false/false | false/false |

미확정 이유는 모두 `SDK_SHIFTED_NORM_INCLUDES_ZERO`다. 입력 범위가 `norm(rotvec+1e-8)`의0을 배제하지 못하면 나누지 않고 중단했다. 실제 경로에서 특이점이 발생했다는 관측이 아니다. v2 미확정은 right7에서1개, right19에서2개, left7에서0개, left19에서1개다. 해당 leaf의 valid=false를 보존하며0-filled 배열을 경계로 쓰지 않는다.

v2는 같은 angle의 `a/sin(a/2)` 상관을 monotonicity 조건 아래 유지하고 시간 분할을 고정8개로 바꿨다. v1/v2의 backend 오차 가정·모델buffer는 동일하며 buffer의 bitwise 대응도 내보내기에서 확인했다. 두 버전 모두 완성한80원구간의 정점별62,240항목에서 v2 remainder 후보가 모두 작았다. 경로별 new/old 비율의 중앙값은0.0771/0.0951/0.0819/0.0920이며, 비교한 모든 항목의 비율은1보다 작았다. 이는 조건부 후보의 계산 개선이며 검증된 물리 여유나 모델 품질 개선이 아니다.

v2 경로별 최대 유한leaf remainder 후보는 right7=0.1082494, right19=0.00743635, left7=0.0833788, left19=0.0127085 native 단위다. 이 최대값은 유한leaf만의 값이며 전체 경로 경계로 사용할 수 없다. 단위를 mm로 간주하지 않는다. 일부 후보는 여전히 느슨하다.

## 아직 보증할 수 없는 부분

실수 함수의 interval 포함과 목표 binary의 오차 보증은 별개다. 고정한 생산 polynomial 절대오차1e-12, binary64 초월함수1e-14, Torch float32 sin/cos1e-6과 IEEE/reduction/underflow 모델은 **명시했으나 검증하지 않은 공학 가정**이다. 관측을 포함시키려고 값을 바꾸지 않았다. source의 SLEEF 호출 확인이나 저장 샘플 포함만으로 실제 dispatch/libm/BLAS의 모든 입력 오차를 증명하지 않는다. mpmath `iv`의 실험적 제한도 유지한다.

[SciPy 고정 v1.10.1 source](https://raw.githubusercontent.com/scipy/scipy/v1.10.1/scipy/spatial/transform/_rotation.pyx)와 installed smplx0.1.28 LBS/실제 Torch headers·binary를 추적했다. [mpmath 공식 interval 문서](https://mpmath.org/doc/1.3.0/contexts.html#arbitrary-precision-interval-arithmetic-iv)의 수학적 포함과 experimental 경고를 함께 적용한다. 검증된 backend 경계가 없으므로 current candidate를 [IPC NonlinearTrajectory](https://github.com/ipc-sim/ipc-toolkit/blob/main/src/ipc/ccd/nonlinear_ccd.hpp)의 보증된 remainder로 등록하지 않았다. 이 라이브러리들은 새로 설치/실행하지 않았다.

768leaf 중 관측이 없는leaf도 있고, 저장된196시점을 모두 포함해도 그 사이 시간 전체가 실제 backend 후보에 포함된다는 증명은 아니다. 연속 vertex–face/edge–edge CCD와 공유 simplex 예외·부피 포함·손/물체 물리·생체/사람 승인은 미완료다. `continuous_collision_free_proven=false`, `CCD_clearance=false`, `release_allowed=false`와 기존 격리를 유지한다.

## 실행/검사/보존

v1 생산 `7cb821a`, output/record/config는 `../private_artifacts/tf03_sdk_boxes_20261117_v1`, `tf03_sdk_boxes_record_20261117_v1`, `tf03_sdk_boxes_config_20261117_v1.json`이다.879입력(설정 포함)·17pin·16출력·`EXITED_ZERO`/사후snapshot 일치/`RECORDED_FILES_MATCH`다. core wall48.219초/자체CPU47.625초다.

v2 생산 `346725b`, 대응 output/record/config의 suffix는 `_v2`다.904입력·17pin·16출력이며 동일 검산을 통과했다. core wall199.759초/자체CPU197.734초다. buffer load·interval·저장 관측 검사·저장/journal·원receipt 재검산을 포함하고 최초 receipt 확인/recorder는 제외한다. 분할 수/식이 달라진 비통제 실행이므로 일반 runtime 우열로 해석하지 않는다. v1원출력/판정도 그대로 보존했다.

현재 box10+temporal6=16검사가 CPU환경에서 통과했다. 유리수 기준 산술·영분모/비유한 거부·float32 reduction·trig 극값·고정 SciPy 경로·SDK shifted norm·synthetic LBS/chord·상관 유지 quotient의 점검이며 전체 backend 검증이 아니다. 새 결과의 raw box/모델buffer·개별hash/record는 영구 비공개이며 공개 파일은 집계·leaf시간뿐이다.

## 다음 요구와 전체 큐

G03/GEN3D-02의 보수적 시간구간 계산 경로를 구현했으나 실제 all-time 보증은 완료하지 않았다. 남은4leaf의 상관/특이점 배제와 backend/error envelope의 근거를 확보한 뒤에만 보증된 CCD narrow phase에 연결한다. 샘플 추가나 미검증 pad 확대를 성공으로 세지 않는다. 전체62ID·3D44표행·R0–R9와 실제 촬영/선별/3A/3B/사람·모델/운영 입력 우선은 그대로다. GitHub에는 승인된 `68417fc`까지만 반영됐고 이후 변경은 로컬에 보존한다.
