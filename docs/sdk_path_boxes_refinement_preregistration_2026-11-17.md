# SDK 조건부 구간 경계 v2 — 상관 유지와 고정 세분화 사전등록

v1 `tf03_sdk_boxes_20261117_v1`/`tf03_sdk_boxes_record_20261117_v1`의192leaf는176유한 후보/16미확정·352저장 checkpoint 비교의 이탈0이었다. v1 최대 remainder 후보는 경로별 약1.896/1.180/0.658/20.185 native 단위로 지나치게 느슨했다. 원16출력·코드commit `7cb821a`·미확정 판정을 보존한다. 새 버전은 성공을 채우기 위한 오차 pad/기준 변경이 아니라 식의 상관과 시간 분해를 보완하는 별도 계산이다.

## 고정 변경과 수학적 근거

SciPy `as_rotvec`의 같은 angle에서 계산되는 `a/sin(a/2)`를 분자/분모 독립 interval로 처리하면 상관을 잃는다. a∈[.001,4]에서 `sin(x)-x*cos(x)`(x=a/2)는 증가한다. 왼쪽 값이 고정 sine-error δ보다 크면 `a/(sin(a/2)±δ)`도 증가하므로 각각 endpoint로 감쌀 수 있다. 이 조건을 mpmath interval로 검사하고, 성립하지 않으면 미확정이다. small-angle 분기는 기존대로 별도 감싼다. 새로운 검사는 pointwise quotient/perturbed sine 전체 범위와 경계/거부를 포함한다.

원래24시간 구간을 각각8등분해 네 경로768leaf(.015625초)를 고정 순서로 계산한다. 선택적으로 성공할 때까지 계속 나누지 않는다. .125초 구간의 parent endpoints와 이미 저장된 midpoint만 현재leaf 시간에 속할 때 비교한다. 최대384 checkpoint 비교는 같은196개 관측값의 반복 사용이다. 관측이 없는leaf도 있으며 이탈0만으로 그 leaf를 검증했다고 쓰지 않는다. 실제 비교 수와 unique checked frame 수를 별도로 기록한다.

기존 SDK경로·모델 buffer/zero beta/root·실제 Rodrigues epsilon·LBS mapping·17pin 환경·IV40자리·기본 산술/reduction/underflow와 **미검증 pad1e-12/1e-14/1e-6은 전부 그대로**다. source/target code version과 producer를 새 snapshot에 남긴다. SDK forward0·새 영상/사람 시행·독립 family·풀0이며 모든candidate는 조건부다. backend 오차 검증/CCD clearance/연속 무충돌/생체 승인은 계속false다.

900초·fresh immutable output/record/config, 전체 worktree/입력·실제 command/time/stdout/stderr/종료/출력 hash를 남긴다. 누락/미확정/너무 느슨한 경계도 결과로 보존한다. v1과의 비교는 모든공통 유한구간의 정점별 remainder와 전체 구간 완성 수, 저장 관측 포함·미확정 수를 보고한다. 기존 원자료/완료 실행을 덮어쓰거나 rerun하지 않는다. 이번에는 새로운 식/768leaf를 계산한다.

새 scale 검사1개를 추가해 box10+temporal6=16검사가 CPU환경에서 통과했다. 실제 백엔드 초월함수/누적 산술 보증과 연속 narrow phase/공유 simplex 예외는 별도 미완료다. 전체62ID·3D44표행·R0–R9와 앞 단계 실제 입력 우선·영구 비공개/격리는 유지한다.
