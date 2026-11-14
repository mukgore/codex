# 학술 수식의 코드 대응과 생체 제약 프로필 진단 — 2026-11-14

## 현재 단위와 근거

사용자 요청의 [생물학적 타당성·제약 있는 랜덤 생성](../3d_biomechanics_and_random_generation_2026-11-14.md)에 따라 수식 계산과 허용 범위 판정을 분리했다. 앞 단계의 실제 촬영·사람 응답/주석·독립 비교 자료는 여전히 우선이며, 이번 작업은 입력 없이 가능한 G02/G03의 개발 진단이다.

1차 자료인 [Spurr et al., ECCV 2020 본문 §3.1](https://jankautz.com/publications/WeaklySupervised3DHand_ECCV20.pdf)의 뼈 길이, 손바닥 curvature/각도, local joint frame과 [보충 자료 §1](https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123620205-supp.pdf)의 각도 부호·허용 영역 판정을 확인했다. 실제 수치 범위는 이 논문의 수식만으로 정해지지 않는다. 이번 구현은 해당 식을 독립 작성한 feature/검사 코드이며 논문 network·학습·성능의 재현은 아니다.

## 구현 범위

handcaptcha `841925a`의 수식/프로필 구현을 `5b43e86`에서 논문의 정적 근거와 프로젝트의 시간 확장 출처까지 구분했다. 해당 `biomechanical_features.py`와 `biomechanical_profile.py`의 범위:

| 계산/판정 | 대응과 범위 |
|---|---|
| 20개 뼈 길이 | 이름으로 대응. 5개 root 다음 각 손가락의 3개 연결 순서 |
| 4개 손바닥 curvature·4개 root 간 각도 | 본문 Eq.1–3. 무차원/라디안 값을 계산 |
| 15개 굽힘·벌림 각도쌍 | 본문 Eq.4–6·보충 Eq.2. `atan2`로 부호를 보존하고 local frame을 전달 |
| 각도쌍 허용 영역 | 보충 §1의 convex hull 내부/경계 및 projected-edge residual. 두 각도의 독립 min/max 상자만으로 통과시키지 않음 |
| 속도/가속도 | 이 프로젝트의 시간 확장. 실제 초·불균등 간격, flexion branch unwrap을 사용. 논문에 동적 안전 한계가 주어졌다고 주장하지 않음 |
| 같은 생성 rig의 뼈 길이 | 프레임 간 고정 길이를 수치 오차 범위에서 확인. 개인별 생체 가동 한계와 다른 생성 계약 |

좌표는 column basis로 저장하고 local 회전은 `Ry(flexion) Rx(-abduction)`을 기존 basis 오른쪽에 곱한다. 재구성한 z축이 실제 child bone과 같은지 검사한다. left 입력은 반사해 right convention으로 대응하지만 handedness 자체를 관측/인증하지 않는다. 회전·이동·미러·scale의 수치 성질도 검사했다.

MediaPipe 이름의 엄지 CMC/MCP/IP/TIP와 논문의 일반화된 finger layer를 혼동해 같은 숫자 한계를 넣지 않는다. 엄지 전용 해부학적 대응은 미확정이다. 길이는 `m`/`mm`/`authored_units`를 구분하며 미보정 authored unit에 물리적 뼈 한계를 승인해 붙일 수 없다.

0길이·취소되는 손바닥 normal·정의되지 않는 각도는 값을 채우지 않고 거부한다. 이 hard rejection은 잘못된 생성 후보를 통과시키지 않기 위한 프로젝트 결정이며 differentiable training의 수치 처리를 복제한 것이 아니다.

## 허용 범위의 기록과 미확인 처리

`pending_profile()`는 버전·feature convention·길이 단위·엄지/좌표 대응 상태와 여섯 규칙을 모두 기록한다. 각 규칙은 상태·수치·출처/위치·값의 기원·적용 집단/범위를 연결한다. 규칙은 뼈 길이, 손바닥 curvature, root 각도, 15개 각도 hull, angular speed, angular acceleration이다.

내장 프로필은 **여섯 수치 범위 모두 unresolved/null**이다. 수식의 출처가 있다는 사실을 생물학적 허용 수치의 근거로 바꾸지 않는다. 합성 수치로 코드가 통과해도 `evidence_backed_rule_checks_pass=false`이며, 수치 통과만으로 생체/물리/사람 수행을 보장하지 않는다. 현재 전체 생성 준비·운영 공개는 항상 미승인 상태다.

이 코드는 별도 feature/profile 평가 경로다. 기존 software fixture의 render 출력, root prod UI·채점식·Stage7을 생체 검사 통과 경로로 바꾸지 않았다. 생체 검증된 랜덤 생성기에 연결한 상태도 아니다. 자기 충돌·실제 해부학 표면·물체 역학·샘플 사이의 연속 궤적·사람 편안함은 추가로 필요하다.

## 실제 20개 시퀀스·480프레임 진단

기존 surface 실행 기록을 전후 검증하고 당시 코드와 같은 `generate`/`grasp_contacts`/`contact` source로 참조 288프레임을 재계산해 대조했다. 기존 네 template의 두 seed도 좌표로 다시 계산했다. 새 사람 촬영·모델 추론·독립 동작 family를 만들지 않았다.

| 자료 | 시퀀스/프레임 | 계산 결과 | 생체 제약 통과 |
|---|---:|---|---:|
| 기존 두 접촉 모형 × 두 seed × 세 깊이 제어 | 12 / 288 | 모두 `CANCELLING_PALM_EDGE_NORMALS`, local 관절 기준을 구성할 수 없음 | 0 |
| 기존 index/middle/alternating/touch template 재계산 | 8 / 192 | feature 계산 가능. 수치 범위 미확인으로 `UNRESOLVED_LIMITS` | 0 |

첫 결과는 **현재 작성한 손바닥 배치가 이 BMC 좌표계 검사에 부적합**하다는 근거다. 실제 사람의 의학적 이상을 진단하거나 모든 해당 동작이 불가능하다고 판정한 결과가 아니다. 두 번째도 feature가 계산됐다는 뜻이지 자연스러운 손/편안한 동작의 입증이 아니다. 이전의 capsule 접촉/가림/codec 검사가 성공했다는 사실은 그 좁은 범위로 유지한다.

## 실행 증거와 코드 검사

최종 실행 ID `G02-G03-BMC-PROFILE-20261114-v2`, handcaptcha 코드 `5b43e86`, 분석 코드 codex `daa3185`. 비공개 404개 입력/코드와 26-pin 환경을 실행 전 snapshot하고 실제 명령 종료 0·후검사 일치·출력 23개 연결/재검사를 마쳤다. 초기 실행도 별도 폴더에 보존하며, 시간 확장이 논문 수치로 보이지 않도록 source locator를 구분한 최종 프로필의 v2 실행을 집계한다. 숫자 한계를 새로 넣거나 표본을 늘리지 않았다. 각 case의 feature/오류·적용 프로필·재계산한 좌표와 상세 기록은 비공개 영구 보관한다. [공개 집계](../../reports/biomechanical_profile_audit_20261114.json)에는 개수·상태만 있다.

```powershell
python -m validation_v03.execution_record verify --record ../private_artifacts/biomechanical_profile_record_20261114_v2
```

pipeline 전체 131개가 통과했다. 신규 13개는 수작업 기하/부호·local 회전, rigid transform/미러/scale, 퇴화 기준, hull의 상자 모서리/경계, 실제 시간 미분/unwrap, 미확인/합성 프로필, 속도·가속도·고정 길이 위반과 잘못된 단위/근거를 검사한다. 테스트용 숫자는 사람의 안전 범위로 사용하지 않는다.

## 다음 단위

랜덤 범위를 넓히기 전에 **손 골격/엄지·좌우손·물리 길이 단위의 근거 있는 대응과 허용 수치/영역**을 준비한다. 현재 접촉 proxy의 퇴화 배치를 숫자로 덮어 고치지 않는다. 기존 MANO/실측 참고 자료는 출처·단위·관절 대응부터 확인한 뒤 활용 여부를 판단한다. 이 선행 조건이 확인돼야 제한 샘플러와 시도별 거부 기록으로 이어진다. 실제 사람의 이해/편안함·강한 공격 비교는 별도다.
