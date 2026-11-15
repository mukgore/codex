# 논문의 D-H·수정 D-H와 BMC 각도 표현 대조

## 참고 모델에서 확인한 관계

BIO-07 Cobos2008 표I–II(2247–2248쪽)의 일반 D-H와 BIO-06 Chen Chen2013 표7–8(7–8쪽)의 수정 D-H를 독립적인 forward-kinematics 참고 코드로 구현했다. [Cobos 기관 원문](https://oa.upm.es/4040/1/INVE_MEM_2008_58022.pdf), [Chen Chen DOI](https://doi.org/10.1155/2013/910961). 표의 회전축·관절 순서·길이 위치·마지막 손끝 이동을 원문 화면에서 대조했다.

일반 D-H는 `Rz(theta) Tx(a) Rx(alpha)`, 수정 D-H는 `Rx(alpha) Tx(a) Rz(theta)`를 사용했다. 해당 표의 d는0이다. 손가락 기저 좌표계를 기준으로 한 국소 모델이며 wrist와 각 손가락의 실제 배치·인체 치수를 맞춘 것은 아니다.

- **엄지 제외 모델:** `S(c,a,f,p,d)`가 일반 D-H라면, 수정 D-H에서 벌림 입력을 `-a`로 바꾸고 계산 출력에 `Rx(-pi/2)`를 적용하면 같은 관절 위치와 손끝 transform을 얻는다. 표에 쓰인 두 국소 기준을 맞추는 관계다.
- **엄지 모델:** 같은 관절 입력을 쓰되 수정 D-H에 마지막 손끝 link 이동을 명시하면 일반 D-H와 일치한다.

264개 작성 조건(엄지 제외216개·엄지48개, 임의 길이 비율과 두 scale)을 계산했다. 대응 후 최대 위치/transform 차이는 모두 약8.88e-16 이하였다. 대응 없이 같은 입력·같은 좌표라고 비교하면214조건의 위치가 달랐다. **수식 표기가 다르다는 것 자체가 다른 손이나 틀린 모델을 의미하지 않는다.** 이 국소 관계를 실제 MANO의 검증된 해부학적 좌표 변환으로 확대하지 않는다.

## BMC와 단일 관절의 방향 비교

BMC의 `Ry(f) Rx(-a)` 순서와 위 D-H의 MCP 회전 순서는 두 축을 함께 움직일 때 같은 수치쌍이 아니다. 단일 관절을 대상으로, BMC의 중립 x/y/z를 참고 모델의 y/z/x에 놓는 **작성 기준축**을 정해 비교했다. 이 축은 참가자나 MANO에서 측정한 축이 아니다.

25조건에서 D-H로 얻은 outgoing bone 방향을 이 기준축의 BMC 각도로 나타낸 뒤 복원하면 최대1.11e-16 차이로 같았다. 다만 두 각도 숫자를 각각 동일하다고 놓는 단순 대응과의 최대 차이는 약0.1555rad(8.9도)였다. 한 축만 움직이는 대조와 두 축이 동시에 움직이는 대조를 나눠 검사했다. 이 수치는 **작성 참고 조건의 표현 차이**로, 실제 추적 오차나 사람의 관절 이상/불편을 측정한 값이 아니다.

같은 뼈 방향은 축방향 twist를 유일하게 정하지 않는다. 첫 관절의 방향 복원만으로 아래 관절의 임상 frame이나 전체 손 좌표 대응까지 검증하지 않았다. thumb·손바닥 곡률·실제 손가락 기저/wrist offset과 neutral/sign 적용은 별도다.

## 코드·실행 근거

handcaptcha `9f29ac4`의 `kinematic_conventions.py`, 연구 `6f45fbe`의 `kinematic_convention_audit.py`. 알려진 중립/CMC90도 끝점, 전체 국소 chain과 끝점 orientation, 엄지 terminal link, BMC 단일 방향 복원·복합각 차이·입력 계약의5개 검사를 추가했다. handcaptcha 전체157개 통과. [집계 JSON](../../reports/kinematic_convention_20261115.json).

실제 외부 기록은 코드·두 원논문/대조 이미지·실제 수학 구현9입력과 기존 offline26pin 환경을 묶었다. `EXITED_ZERO`, 전후 snapshot 일치, 출력3개 검산 통과. `private_artifacts/kinematic_convention_20261115/`, `kinematic_convention_record_20261115/`, `kinematic_convention_config_20261115.json`에 작성 조건/원문/상세 기록을 비공개 보존한다. 원문 렌더는 계산 실행 이전에 별도 수행했으며 소급 실행 정보는 만들지 않았다.

## 완료한 것과 다음 조건

완료한 것은 **두 출판 국소 모델 사이의 선언한 수학적 변환과 작성 단일 기준축에서의 BMC 방향 대응**이다. 길이/각도 grid는 공학 단위이고 생체 허용 범위가 아니다. 실제 MANO fitting·임상 중립축·생체/편안함·물리·모델 새 추론은 없다. 기존 수치 프로필·엄지 표의 불일치·랜덤 격리 상태도 유지했다.

다음은 이 참고 코드를 실제 모델의 알려진 중립/축 perturbation과 대조하고, wrist/finger 기저·엄지·twist·coupled 영역·단위의 학술/측정 근거를 확인하는 일이다. 그 결과 없이 논문의 가동 범위를 BMC/MANO의 안전 한계로 넣지 않는다. [학술 색인](../academic_reference_index.md)과 [전체 다음 일](../remaining_work_master_2026-11-15.md)을 갱신하며 앞 단계 실제 촬영/사람 입력 우선은 유지한다.
