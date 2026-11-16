# G03 원래 비선형 경로의 새 중간 시점 진단 — 사전등록 v1

기존 TF-03의100 SDK프레임과 공유 면 보완/정확 후속은 보존한다. 이번은 원래 샘플 사이에 실제 생성식으로 새 mesh를 계산하고, 정점 직선 보간으로 대체 가능한지와 새 샘플의 모델 prior/표면 상태를 확인하는 별도 진단이다. **연속 무충돌 판정 실험으로 대체하지 않는다.**

## 원래 경로와 고정 새 분모

`tf03_path_20261116_v1`/`tf03_path_record_20261116_v1`의 양손×seed7/19 네 경로를 입력으로 고정한다. 저장 `proposed_angles`의0/12/24번이0/1.5/3초 waypoint다. 기존25시점의 제안각과 동일한 quintic 정의가1e-12 이내로 일치해야 한다. 각 .125초 구간의 midpoint .0625,.1875,...,2.9375초에 새24자세씩 총96자세를 계산한다. 기존100 SDK자세를 다시 계산하지 않는다.

원래 정의 `q0+(q1-q0)*(6u^5-15u^4+10u^3)` → intrinsic XYZ → template basis conjugation → SciPy axis-angle → float32 → 고정 SDK Rodrigues/LBS를 그대로 쓴다. 정점 위치를 직접 잇는 선형 경로로 바꾸지 않는다. 부모25프레임은 midpoint와 대응한 chord를 계산할 때만 읽는다. beta/root/transl0, flat_hand_mean=true, 기존 CPU17pin·Torch2.5.1+cpu/smplx0.1.28·1thread를 유지한다. 양손 neutral2회로 원래 neutral_points와≤1e-7/topology 동일성을 확인한 뒤24자세 배치4회다. 총98자세 평가/SDK6호출이다.

## 측정·기준·실패

새96프레임의 actual pose/16관절/표면tip·778정점과 actual anatomical angles·저자 prior strict/mask후 excess를 저장한다. 기존 비공유 면 SAT와 새 공유 simplex 보완을 모두 실행하며, float 미확정 쌍은 저장 binary64의 기존 정확 유리수 후속으로 검사한다. 전체 fallback1,024쌍 상한을 넘거나 입력/원receipt/모델neutral이 달라지면 실패로 남긴다. 이전 미확정8건을 다시 계산하는 실험이 아니다. 새 프레임에서 생긴 미확정/지표/퇴화/오류와 모든 시도를 보존한다.

midpoint 정점과 양 끝 정점 평균의 거리, 각 구간의 최대 native 거리와 endpoint mesh 대각선으로 나눈 값을 기록한다. 상대1e-7 초과 구간 수는 기존 수치 해상도와 비교한 기술통계이며 임상/물리 기준이 아니다. 모델 단위를 mm라고 가정하지 않는다. 관측된 midpoint 오차를 전체 구간의 오차 상한으로 쓰지 않는다. endpoint·midpoint가 모두 무교차여도 사이에 충돌할 수 있다는 분석적 반례를 검사한다.

core/경로/프레임 표면검사 wall·자체CPU와 SDK98/새96/neutral2·원프레임 재추론0의 분모를 구분한다. 전체900초·새 immutable root/record/config·전체 worktree/입력/환경·명령/시간/stdout/stderr/실패/출력 hash를 기록하며 실행 중 편집/commit 금지다. 새 영상/사람 시행·독립 family·풀 채택은0이다. threshold·sampling·seed를 결과에 맞춰 조정하지 않는다.

## 실제 연속 검사가 요구하는 후속 계약

2026-11-17 [IPC Toolkit의 NonlinearTrajectory 공식 선언](https://github.com/ipc-sim/ipc-toolkit/blob/main/src/ipc/ccd/nonlinear_ccd.hpp)을 확인했다. 시간별 정점뿐 아니라 구간의 직선 근사에서 최대 이탈의 보수적 상한이 필요하다. [Tight-Inclusion 공식 저장소](https://github.com/Continuous-Collision-Detection/Tight-Inclusion)는 선형 primitive CCD와 수치 오차/최소 간격을 다룬다. 이번에 해당 라이브러리를 설치/실행하거나 논문 알고리즘을 재현하지 않는다.

후속 CCD 진입에는 **실제 Euler→axis-angle/float32→SDK Rodrigues/LBS 경로를 포함하는 정점별 all-time enclosure 또는 chord remainder 상한**, 그 수치 오차·시간/단위·face/vertex 매핑, 연속 vertex–face/edge–edge 처리·공유 연결부 예외의 근거가 필요하다. 샘플 최대값이나 이상적 회전만의 bound를 SDK 전체 경로의 보증으로 대체하지 않는다. 현재 이 상한은 미확보이며 연속 무충돌·부피 포함·물체 역학·생체/사람/운영 승인은 false다. 이번 진단의 역할은 실제 모델 경로와 선형 대체의 차이를 측정하고 다음 envelope 구현을 올바른 경로에 연결하는 것이다.

새6검사와 기존 공유/정확19검사, 총25개가 실제 실행 CPU환경에서 통과했다. 실제 입력이 들어오면 원래1→2→3A→3B→4→5→6 순서부터 우선하며62ID/3D44표행/R0–R9·영구 비공개/Cloud보류/연구격리를 유지한다.
