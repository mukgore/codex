# 표준 좌표·시간 adapter와 후보 특징 연결

`validation_v03/adapters.py`는 `segments[].frames[].t/lm` 형태의 비공개 session 입력을 받는다. 영상 폭/높이, 좌표 공간(normalized_xy/pixel_xy), 시간 단위(ms/s), x 미러 적용 여부, 최대 gap을 호출자가 명시한다. 누락 영상 크기를 720×720 등으로 채우지 않는다. 해당 metadata가 없는 기존 기록은 추가 근거 없이 이 경로로 자동 재분석하지 않는다.

normalized x/y를 실제 픽셀 축으로 바꾼 뒤 미러를 한 번만 적용하고 손목 중심·손목–중지 MCP 길이로 정규화한다. 15개 관절 각도와 실제 초 단위 시각을 보존한다. z는 이 후보에서 사용하지 않는다. 퇴화 뼈/scale·비유한 좌표·Boolean/문자 좌표는 invalid로 분류한다. 화면 밖 좌표 자체를 오류라고 단정하거나 clip하지 않는다.

null·잘못된 기하·큰 시간 공백은 연속 block의 경계다. frame을 임의로 보간하지 않는다. 3개 미만의 짧은 block은 분석에서 사용하지 않되 attempted/detected/missing/invalid/짧은 block 분모에 남긴다. 구간별 시간 초기화는 별도 segment로 보존하고 같은 segment 안의 중복/역전 시각은 오류로 처리한다.

`compare_contiguous_blocks`는 완전한 두 block에 기존 실제 DTW·실제 시각 미분 함수를 연결한다. 실제 각도열의 DTW와 명시적 phase grid의 각도 MAE, 실제 초 단위에서 계산한 가속도를 phase에 맞춘 차이를 반환한다. 가속도 단위는 정규화 손 길이/s²다. phase 미분이나 미터 단위 가속도가 아니다. radius/grid는 호출자가 정하고 DTW 예산을 자동 늘리지 않는다.

출력은 **후보 raw 특징**이며 score=None이다. 기존 B0 산식·MX·가중치·threshold를 바꾸지 않는다. 이 오차를 곧바로 compare_scores의 candidate_score에 넣으면 수용 방향/척도가 맞는다고 보장할 수 없다. 같은 trial의 legacy 결과와 후보 특징을 연결한 뒤 개발/validation 자료에서 변환·후보 기준을 고정하는 단계가 남아 있다. 분류기 학습·calibration·공격군별 결과·군집 CI·prod JS는 아직 완료되지 않았다.

```powershell
python -m validation_v03.adapters --input data/work/session.json --output data/work/private_features.json --width 640 --height 480 --coordinate-space normalized_xy --time-unit ms --mirror-x no --max-gap-seconds 0.2
```

위 크기와 gap은 명령 형식 예시다. 실제 입력 근거와 사전 고정한 정책으로 바꾼다. 출력은 좌표 유래 특징과 시각이 들어 있는 **비공개 파일**이다. Git/공개 저장소에 올리지 않는다. CLI는 기존 출력 덮어쓰기를 거부한다. 참가자 식별자 등 session의 불필요한 metadata는 출력에 복사하지 않는다.

합성 검사 11개는 종횡비 복원·미러 한 번·ms/s 동등성·null/gap 분할과 분모·손상/짧은 block·구간 시간 초기화·명시 metadata·identity/실제 시간 특징·잘못된 좌표·CLI 저장/덮어쓰기 거부를 확인한다. 실제 사람/공격 입력의 성능이나 기존 G1~G4 연구를 다시 계산한 결과가 아니다.
