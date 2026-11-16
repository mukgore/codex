# TF-01 원문·모델 제약 적용표 — 2026-11-16

인계 후 고정 prod 좌표 진단을 마치고 작성한 B/C 경로의 적용 명세다. **TF-01 문서 완료이며 TF-02 구현/실행 완료가 아니다.** 기존 A와 여섯 미확정 한계는 보존한다. 현재 적용 가능한 모델 prior만 쓰는 후보의 상태는 `MODEL_CONSTRAINED_RESEARCH_ONLY`, `release_allowed=false`다.

## 원문에서 실행 규칙까지

| ID·절/식/표 | 관절·축·중립·단위 | 연동·대상/과제 | 현재 적용과 남은 조건 |
|---|---|---|---|
| BIO-01 MANO; 기존 SDK/point contract | native16관절과 표면손끝5점 분리. root와 비root45축각 분리; radians. 길이는 model_native_units | 학습된 자세 표현의 PCA기저; 임의 계수의 분포는 새 공학 선택 | B 자세 제안 표현으로 가능. 모델/라이선스·사용 범위 검증 유지. 샘플링 계수의 정상분포를 학습된 확률밀도/사람 분포로 부르지 않음 |
| BIO-02 §3.1 뼈 길이 구간, 식(1)–(3), 식(7); BIO-03 §1/식(2) | BMC21점의 길이·손바닥 구조와 국소 굽힘/벌림. 현재 MANO점 대응의 각도 중심/표면tip 구분 필요 | 굽힘–벌림의 결합 허용 영역; pose추정용 제약 | feature계산만 가능. 실제 길이구간/곡률/벌림/hull 수치·엄지·단위·모집단 대응 미확정; 생성 승인 관문으로 대체 불가 |
| BIO-06 §3.1 식(1), 표6 | DIP/PIP/MCP 굽힘의 비엄격 근사; MDH와 현재 모델의 축/부호/중립 대응 미완료; 표 단위degree | DIP≈(2/3)PIP, PIP≈(3/4)MCP; 개인/과제 의존 | 경성 등식이나 보편 허용구간으로 적용하지 않음. residual 허용치 없음. A의 .85/.55는 이 식을 구현한 값이 아님 |
| BIO-07 §II 표I–II, §III 표III | 일반DH와 finger기저; BIO-06은 수정DH. 보고 excursion이며 signed허용구간 아님 | 잡기 과제의 단순화와 기존 문헌 재인용 | 원문/재인용의 엄지MCP/IP 벌림2칸 불일치 유지. 원측정·neutral/sign 대응 전 수치 적용 보류 |
| BIO-09 CPF §3/보충A.1; 후속 고정 manotorch AxisLayerFK·AnatomyConstraintLossEE | flat 모델 template기준축, twist/spread/bend, intrinsic XYZ. 비root회전은 `B·Rx·Ry·Rz·Bᵀ`, 내부rad/표degree. root별도 | 현재 저자 코드의 모델용 각도 prior; 원2021 posed축 방법과 구분 | 검산된 compose/extract와 고정 defaults 재사용 가능. 임상축/실측안전·연동/동역학의 근거는 아님 |
| GEO-01 §9; 기존 mesh검사 | actual778정점/1538면, 샘플별 비공통꼭짓점 후보쌍 | 기하교차/퇴화 지표 | 현 검사 재사용. 인접면·부피/포함·연속충돌·물체힘/접촉은 미검증 |
| BIO-06 §6/표9; 프로젝트 시간 확장 | 20명의10초 최대속도 주먹쥐기, 가정한 파형에서 유도된rad/s; 주기해석 미확정 | 특정 무부하 빠른 개폐 과제 | 안전/편안함 상한으로 전용 금지. 가속도상한 없음. TF-02 정적자세에는 시간규칙N/A, TF-03은 별도 사전등록 필요 |

수치/출처 상세는 [기존 추출](../references/chen2013_constraint_extraction.json), [Cobos 원표 대조](../references/cobos2008_constraint_extraction.json), [모델 defaults](../references/manotorch_default_constraint_extraction.json)에 연결한다. 이 표는 기존 로컬 검토/코드의 적용 범위를 정리한 것이며 전체 원논문 재현이 아니다. 11월16일 [고정 저자 코드](https://github.com/lixiny/manotorch/blob/a2a70c591f91551078b7bb2af9b5d9f275b626e0/manotorch/anatomy_loss.py), [같은 revision 안내](https://github.com/lixiny/manotorch/tree/a2a70c591f91551078b7bb2af9b5d9f275b626e0), [BMC 본문](https://jankautz.com/publications/WeaklySupervised3DHand_ECCV20.pdf)을 다시 열어 관련 정의/방법 구분을 확인했다. 새 모델/가중치를 받지 않았다.

## 고정 모델 prior의 수치와 배정

출처는 위 JSON의 고정 revision `a2a70c5…`, 원본 blob `0e13cdb…`, `setup`/`forward`다. 아래는 저자 모델 defaults이며 측정된 사람 한계가 아니다. thumb_pip라는 저자 이름은 native15 엄지 말단/IP를 뜻한다. 좌우손에 author_exact를 그대로 적용하고 이상적 반사 comparator와 섞지 않는다.

| 모델 관절 그룹 | native 인덱스 | twist, 도 | spread, 도 | bend, 도 |
|---|---|---:|---:|---:|
| 검지/중지/약지/소지 MCP |1,4,10,7 |[0,0] |[-5,5] |[0,90] |
| 같은 손가락 PIP |2,5,11,8 |[0,0] |[0,0] |[0,90] |
| 같은 손가락 DIP |3,6,12,9 |[0,0] |[0,0] |[0,90] |
| 엄지 CMC |13 |[-45,45] |[-15,45] |[0,45] |
| 엄지 MCP |14 |[0,0] |[-10,10] |[0,90] |
| 엄지 말단/IP |15 |[0,0] |[0,0] |[0,90] |

구현은 기존 `template_basis`/`compose_anatomical`/`extract_anatomical`과 `assess`를 재사용한다. strict초과와 저자1e-6rad zero-mask 후 벌점을 각각 기록한다. 모델이 반환한 실제 full_pose로 재추출해 검산한다. shape/root를 바꿔 차이를 숨기지 않고 Euler singularity 부근은 진단 계약 밖으로 거부한다.

## 계속 미확정인 여섯 규칙

| 규칙 | 계산 단위/의미 | 실행 허용값 상태 |
|---|---|---|
| bone_lengths | 관절/표면tip 종류를 구분한 길이, 물리SI미확인 | 미확정 |
| palm_curvatures | 현재 BMC feature의 곡률 표현; 표면 곡률과 구분 | 미확정 |
| palm_spread_radians | 손바닥 인접뼈 벌림rad | 미확정 |
| joint_angle_hulls | 각 관절 국소 굽힘/벌림rad의 결합영역 | 미확정 |
| angular_speed_rad_s | 실제초 시간축의 각속도; BMC의 정적한계와 별도 | 미확정; TF-02 정적자세에서는 N/A |
| angular_acceleration_rad_s2 | 실제초 시간축의 각가속도 | 미확정; TF-02 정적자세에서는 N/A |

`UNRESOLVED_LIMITS`는 계속 유지한다. 정적자세에 가짜 timestamp를 붙여 속도0의 통과를 만들지 않는다. 원형 없는 **동작**은 정적자세 후보 확보 뒤 TF-03에서 따로 다루며 물리/사람/최종가림/보안 승인은 각각 별도다.
