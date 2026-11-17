# G03 실제 SDK 경로의 조건부 구간 경계 후보 — 사전등록 v1

이전 midpoint 관측 최대값을 all-time bound로 바꾸지 않는다. 별도 연산으로 Euler→SciPy quaternion/matrix/native rotvec→float32→SDK shifted-norm Rodrigues→pose blend/LBS의 시간구간 경계 **후보**를 구현한다. 백엔드 오차 한계가 검증되지 않았으므로 이 실행은 인증된 enclosure/CCD 성공 실험이 아니다.

## 입력·분모·새 계산

완료 TF-03 원본 `tf03_path_20261116_v1`/기록과 새96중간시점 `tf03_midpoint_20261117_v1`/기록, 기존 허용 MANO intake/계속 연구 범위를 고정한다. 네 경로의 원래24구간을 각2등분해 총192개 .0625초 leaf를 순서대로 계산한다. beta/root/transl0·flat_hand_mean0이며 같은 model buffers와 source basis/waypoint를 쓴다. SDK forward0, model buffer load2, 새 영상/사람 시행/독립 family/풀 채택0이다.

leaf의 양 끝에 이미 저장된 mesh를 검사한다.192×2=384 checkpoint 비교는 고유196관측값의 중복 사용이며 독립 표본/새 SDK평가가 아니다. 원SDK 출력·모델·기존float/정확/중간시점 결과는 변경하지 않는다. 구간 박스·정점별 remainder 후보·valid mask·미확정 이유·관측 이탈 수·wall/CPU를 비공개에 남긴다. 미확정 leaf의0-filled 배열은 valid=false이며 경계로 사용할 수 없다.

## 실제 연산과 명시적 가정

기존 mpmath1.3.0 `iv`(40decimal digits)로 실수 sin/cos/atan2와 quintic endpoint를 감싸고 binary64 endpoint를 바깥쪽으로 변환한다. 기본 산술/float32 cast·reduction/FMA/underflow의 명시적 모델과 누적 roundoff 여유를 적용한다. `iv` 자체도 공식 문서상 실험적 기능이며 설치된 backend와의 동등성을 증명하지 않는다.

SciPy1.10.1의 `from_euler/as_matrix/from_matrix/as_rotvec` 선택된 계산 구조를 따른다. matrix→quaternion 가능한 dominant 분기는 모두 감싸고 canonical sign/분모가 해소되지 않으면 미확정이다. SDK는 실제 `norm(rotvec+1e-8)`와 원래 K/행렬 다항식을 사용하며 단순한 이상적 Euler 회전으로 건너뛰지 않는다. source axis-angle/float32, actual template/J_regressor/posedirs/weights·부모tree와 LBS4×4 연쇄를 포함한다.

다음 값은 **아직 검증되지 않은 공학 가정**으로 고정한다. 생산 quintic scalar/각 성분 계산 절대오차1e-12, binary64 초월함수 절대오차1e-14, Torch float32 sin/cos 절대오차1e-6; 기본 산술은 finite IEEE binary32/binary64 round-to-nearest·통상적 reduction/FMA와 bounded underflow를 가정한다. 이 값들은 문헌에서 확인한 backend 보증이나 생체 한계가 아니다. 관측을 포함하도록 값을 튜닝하지 않는다. 헤더에 SLEEF 호출이 있어도 설치 binary의 실제 dispatch/오차 bound를 증명한 것으로 쓰지 않는다.

`backend_error_bounds_validated=false`, `CCD_clearance=false`, `continuous_collision_free_proven=false`, `release_allowed=false`를 유지한다. 관측이 하나라도 박스 밖이면 이탈 수를 남기고, singular/branch 범위가 해소되지 않으면 해당 leaf를 미확정으로 남긴다. command 종료0/모든 관측 포함은 이 가정의 검증이나 all-time 보증이 아니다.

정점별 chord remainder 후보는 각 leaf의 공간 박스와 원래 endpoint chord의 같은 시간 범위 사이의 최대 축별 거리에서 계산한다. 상관을 잃는 보수적 계산이라 느슨할 수 있다. midpoint 최대값을 복사하지 않으며 유한 candidate 전체가 나와도 현재는 조건부 값이다. vertex–face/edge–edge CCD·공유 연결부 연속 예외·부피 포함·물체 물리·생체/사람 검증은 수행하지 않는다.

## 확인한 원자료와 검증

2026-11-17 [SciPy v1.10.1 고정 source](https://raw.githubusercontent.com/scipy/scipy/v1.10.1/scipy/spatial/transform/_rotation.pyx)의 선택된 회전 변환을 확인했다. [mpmath interval 문서](https://mpmath.org/doc/1.3.0/contexts.html#arbitrary-precision-interval-arithmetic-iv)의 포함 성질과 experimental 제한을 함께 적용한다. 기존 installed smplx0.1.28 `lbs.py` 및 Torch vec256/vec512 float headers를 읽었다. source 확인을 binary dispatch/전체 수치 오차 인증으로 바꾸지 않는다. 새 설치·cloud 전송은 없다.

새9검사: 유리수 기준의 산술 외향 포함·0분모/제곱근/비유한 거부·float32/실제 reduction 포함·trig 내부극값·선택된 SciPy 변환·SDK shifted norm/singularity·native basis·synthetic LBS·chord box를 검사한다. 기존 temporal6검사와 합해15통과다. 최초 0거리 제곱합이 바깥쪽 반올림으로 음의 극소 하한을 가진 반례는 수학적 비음수 교집합으로 처리했다. backend 계약의 전체 증명이 아니다.

900초·기존17pin CPU1thread·새 immutable output/record/config, 전체 worktree·입력/SDK source/binary/환경·실제 command/시간/stdout/stderr/종료/출력hash를 기록한다. 실행 중 편집/커밋 금지다. 실패/미확정도 보존하고 기준을 바꿔 성공을 채우지 않는다. 전체62ID/3D44표행/R0–R9·실제 입력 우선·영구 비공개/연구 격리를 유지한다.
