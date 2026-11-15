# 각도 중심 관절과 뼈 끝점의 이름 구분

학술 가동 범위를 코드에 대응하기 전에 각도 이름표를 정리했다. [BMC 본문 §3의 notation/그림3](https://jankautz.com/publications/WeaklySupervised3DHand_ECCV20.pdf)은 뼈를 자식 끝점으로 이름 붙인다. 코드의 기존 `JOINT_LABELS`도 이 뼈 끝점을 나열했지만 관절 제한을 연결할 때는 **각도가 놓인 점**과 구분해야 한다.

예를 들어 검지의 첫 각도는 `INDEX_MCP`에서 `INDEX_PIP`로 향하는 뼈의 방향을 local frame으로 나타낸 값이다. 이 각도에 뼈 끝점 이름인 PIP만 붙이면 앞으로 MCP용 값 대신 PIP용 값을 연결할 위험이 있다. 이전에 임상 한계를 실제로 잘못 적용한 결과가 있었다는 뜻은 아니다. 현재 허용 프로필은 미확인 상태였고 그대로 유지했다.

## 바꾼 것

- `JOINT_LABELS`는 각도가 놓인 canonical 중심점 이름으로 바로잡았다. 기존 뼈 끝점 이름은 `ANGLE_CHILD_LABELS`로 명시했다.
- 15개 각도마다 순번·중심점·들어오는 뼈의 부모점·나가는 뼈의 끝점·임상 관절 이름 후보를 기록한다. `ANGLE_RECORD_VERSION`을 따로 두었다.
- feature 추출과 profile 평가가 이 기록을 함께 내보낸다. 임상 축·중립자세·부호 검증은 모두 false다. 수치 계산식·순서/단위·허용 한계·채점/화면은 바꾸지 않았다.

## 학술 선택 행의 이름 수준 대응

| BIO-06 표6 선택 행 | 코드 각도 순번(0부터) | 중심점 | 나가는 뼈 끝점 |
|---|---|---|---|
| Thumb TMC | 0 | THUMB_CMC | THUMB_MCP |
| Index MCP | 3 | INDEX_MCP | INDEX_PIP |
| Index PIP | 4 | INDEX_PIP | INDEX_DIP |
| Index DIP | 5 | INDEX_DIP | INDEX_TIP |

이는 canonical 골격의 **이름 후보 대응**이다. BMC local frame·MANO axis-angle/PCA·논문 MDH/임상 중립자세의 각도가 같다는 검증은 아니다. 엄지의 TMC와 코드의 CMC 라벨, root→MCP 방향과 실제 중수골 기준, 표면 손끝과 관절 중심을 각각 더 확인해야 한다. 수치 변환·부호 선택·허용 hull을 자동 적용하지 않는다.

## 실제 검증

handcaptcha `5c13624`, 연구 audit `dfc4c39`. 중심점/끝점·엄지/검지 후보 대응과 알려진 새끼손가락MCP 굽힘, metadata 복사·비승인 상태를 검사했다. 신규2개를 포함해 handcaptcha 전체152개 검사가 통과했다.

저장된 랜덤8동작·192프레임에서 bone lengths·palm curvature/spread·15개 각도·local frames를 다시 계산했다. 기존 비공개 평가에 저장된 **960개 배열 모두 값이 정확히 일치**했다. 새 metadata는15각도를 명시하고 선택 문헌4행을 이름 후보로 연결했지만 검증된 임상 축 대응은0개다. [공개 요약](../../reports/angle_center_mapping_20261115.json).

실제 execution_record는51입력과 코드/기존 offline26pin 환경을 묶어 실행했다. `EXITED_ZERO`, 전후 snapshot 일치, 산출물3개 검산 통과다. source 실행 기록도 전후 대조했다. 로컬 `private_artifacts/angle_center_mapping_20261115/`, `angle_center_mapping_record_20261115/`, `angle_center_mapping_config_20261115.json`에 상세 기록을 보관한다. 원좌표/개별 입력 hash를 공개하지 않는다.

## 남은 일

Cobos2008 기관 PDF는 웹 timeout에 이어 로컬 Python의 certificate chain 검증과 Windows curl의 자격 획득 단계에서 접근 실패했다. 인증서 검증 해제·시스템 설정 변경은 하지 않았다. 기관의 서지/초록은 재확인했고 원문 읽기는 대기로 유지한다. 접근 실패가 해소되면 원측정/모델 정의를 추적한다. [학술 색인](../academic_reference_index.md).

다음은 임상/MDH 축·중립자세·부호·엄지·root 기준의 대응과 시간 한계 해석을 확인하는 일이다. 현재 여섯 허용 한계·생체/물리/사람 검증·랜덤 결과 격리는 변하지 않았다. 원래 촬영·선별·실제 모방/정지 비교 입력이 들어오면 그 단계부터 우선 처리한다.
