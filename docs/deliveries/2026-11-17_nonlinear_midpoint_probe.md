# G03 실제 비선형 경로의 새96시점 진단 — 2026-11-17

원래 TF-03의 네 경로에서 이전25샘플 사이24개 중간 시점을 새로 SDK계산했다. **96개 구간 모두 실제 중간 정점이 양 끝 정점의 직선 보간과 상대1e-7보다 크게 달랐다.** 새96시점에서 모델 prior/샘플 표면 지표는0이었다. 선형 정점용 CCD를 그대로 원래 경로에 적용할 수 있다는 뜻도, 연속 무충돌이 증명됐다는 뜻도 아니다.

[사전등록과 후속 연속 검사 계약](../tf03_midpoint_preregistration_2026-11-17.md) · [실행 코드](../../analysis/runtime_benchmark/template_free_midpoint_probe.py) · [집계](../../reports/tf03_midpoint_20261117.json) · [프레임별 표면검사 시간/차이96행](../../reports/tf03_midpoint_frame_timings_20261117.csv).

## 원래 경로와 직선 대체의 차이

원래 경로는0/1.5/3초의 세 anatomical Euler 상태를 quintic으로 잇고 `B Rx Ry Rz Bᵀ`→SciPy axis-angle→float32→SDK Rodrigues·pose blend/LBS를 통과한다. Euler 성분이나 끝 mesh만 직선으로 잇는 경로와 같지 않다. 저장 waypoint/원제안각 대응을 먼저 확인하고 새 시점은 `0.0625+0.125*i`(i0..23)로 고정했다. 기존100프레임 SDK추론은 반복하지 않았고 양손 neutral2회는 입력 대응 확인용 새 호출이다.

| 경로 | 새 시점 | 최대 중간 정점 이탈(native 단위) | 최대 이탈/endpoint mesh 대각선 | 상대1e-7 초과 구간 |
|---|---:|---:|---:|---:|
| right seed7 | 24 | 0.000196583 | 0.000762339 | 24/24 |
| right seed19 | 24 | 0.000132095 | 0.000517757 | 24/24 |
| left seed7 | 24 | 0.000188398 | 0.000751756 | 24/24 |
| left seed19 | 24 | 0.000146414 | 0.000561744 | 24/24 |

이 native 단위를 mm로 해석하지 않는다. 해상도와 비교한 관측값이며 오차의 전체 시간 상한이 아니다. midpoint가 작은 이탈을 보여도 구간의 최대 이탈이 더 클 수 있다.

## 새 표면 샘플과 분모

SDK24자세 배치4회+neutral단일2회=6호출,98자세 평가다. 새96시점의 모델 prior 벌점/비공유 면 표면 비clear는0이다. 비공유 면 narrow phase32,334쌍, 공유 면894,720쌍(정상894,712·float 미확정8·겹침/퇴화0)을 검사했다. 새 미확정8건은 실행 안의 기존 유리수 fallback으로 모두 공유 연결부만 교차함을 확인했다. 이전 실행의 미확정8건을 재계산한 것이 아니다. 모든시도/원float판정/정확후속은 비공개 raw에 보존한다.

원샘플100과 새중간96은 같은 네 경로의196시점이며 독립 family/사람 표본이 아니다. 새 영상·사람 시행·풀 채택0개, 기존 격리는 유지한다. 샘플 표면 판정으로 폐곡면 부피 포함·물체 역학·임상/사람 편안함을 승인하지 않는다.

## 실행·시간·검사

생산 commit `06f3edb`, private 출력 `../private_artifacts/tf03_midpoint_20261117_v1`, 기록 `tf03_midpoint_record_20261117_v1`, 설정 `tf03_midpoint_config_20261117_v1.json`이다. 입력844개(설정 포함), 기존17pin CPU환경·Torch1thread를 snapshot했다. `EXITED_ZERO`·사후 snapshot 일치·20개 출력의 `RECORDED_FILES_MATCH`를 확인했다. 원자료/모델/좌표/개별 hash/record는 영구 비공개다.

core wall205.057초/자체CPU203.172초다. 모델 import/setup·neutral/midpoint SDK·샘플표면/이탈·저장/journal·원receipt 재검산을 포함하고 최초 receipt 확인/recorder는 제외한다. 경로별 wall은52.173/51.172/47.624/50.022초이고 프레임별 CSV는 표면 검사 구간이다. 이 CSV 시간을 SDK프레임별 추론 latency로 부르지 않는다. 새6개+기존 공유/정확19개, 실행 CPU환경에서25검사 통과다.

## 다음 연속 검사에 필요한 것

[IPC Toolkit 공식 NonlinearTrajectory 계약](https://github.com/ipc-sim/ipc-toolkit/blob/main/src/ipc/ccd/nonlinear_ccd.hpp)은 구간의 선형 근사에서 최대 이탈 상한을 요구한다. 이 계약을 참고해 실제 SDK경로와 수치 오차까지 포함하는 vertex enclosure/remainder가 확보되기 전에는 선형 primitive CCD 결과를 원래 경로의 보증으로 승격하지 않는다. 라이브러리 설치·실행은 하지 않았다.

현재 `continuous_collision_free_proven=false`, `chord_remainder_supremum_bound_available=false`다. endpoint/midpoint 모두 무교차인데 quarter-time에 면이 겹치는 분석적 반례도 검사했다. 후속은 실제 회전/pose blend/LBS와 float32/SDK 수치 동작을 포함하는 보수적 시간구간 enclosure, 공유 연결부 예외·vertex–face/edge–edge 연속 처리의 연결이다. 유한 샘플 추가만 계속해 이를 완료로 바꾸지 않는다. 전체62ID·3D44표행·R0–R9와 실제 촬영/사람 입력 우선은 유지한다.
