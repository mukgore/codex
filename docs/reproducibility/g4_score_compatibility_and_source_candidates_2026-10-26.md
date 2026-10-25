# 기존 human·G4 점수 호환성과 독립 자료 후보 — 2026-10-26

## 점수식 대조

다음 보존 자료를 읽기 전용으로 대조했다.

- `hand_captcha_prod.html`, `hand_captcha_prod_new.html`
- `circle_edge_attack/scoring.py`, `circle_edge_attack/common.py`, `circle_edge_attack/phase3_evaluate.py`
- 기존 `prod_v2_pool` human JSON의 `scores` 구조와 보존된 G4 결과

**확인됨:** 두 HTML과 Python scoring port는 좌표 정규화, 선형 재표본화, angle / sliding-window DTW-angle / accel 계산, 세 estimated 점수, 가중 결합에서 같은 수식을 사용한다. 세 max 상수, 세 가중치, 최종 threshold도 일치한다. 공격 코드 주석은 Python 구현을 프로덕션 함수의 port라고 명시한다.

**확인됨:** human JSON에는 detection rate, raw, estimated, final captcha score, threshold, passed, weights가 저장된다. G4의 circle-edge stage 4는 같은 채점 port와 threshold로 오프라인 재생 점수를 계산한다.

**직접 비교 제한:** human 값은 한 세션의 모든 segment frame을 연결해 계산한 session-level 점수다. 공격 stage 4 값은 gesture × direction별 replay의 clip-level 점수다. 공격 채널의 입력 검출률도 채널 A는 기본 1.0, 채널 B는 측정 detector rate를 사용할 수 있다. 따라서 현재 저장된 aggregate human score와 clip-level attacker score는 동일 표본 단위·동일 분모의 대응값이 아니다. 동일 수식 사용은 수식 호환을 보이지만, 집계 점수를 바로 대조할 근거는 아니다.

**게이트 의미 차이:** G4의 pixel/reference lookup top-1 판단은 브라우저의 landmark angle gate와 같지 않다. 생산 HTML의 live gate는 각도 한계와 유지 시간을 포함한다. 오프라인 공격 요약은 해당 실시간 gate 이벤트를 재현하지 않는다.

**전체 인증:** 보존된 코드는 클라이언트 계산·결과 전송 흐름을 보여주지만, 현재 자료에는 서버가 보호된 동작을 허용했다는 endpoint/log가 없다. 그러므로 어떤 score 통과 비율도 end-to-end 인증 성공률로 바꿔 부를 수 없다.

## 별도 영상 후보

승인된 `FOR_EXPERIMENTS` 자료 아래에서 MP4 16개와 JSON 8개를 확인했다. 4개 하위 그룹마다 MP4 4개와 JSON 2개가 있고, JSON 4개는 tracking 형식으로 총 434 frame records와 pixel landmark 필드를 가진다. 다른 JSON 4개는 세 단계 변형 설정 구조다.

이 MP4들은 기존 CAPTCHA 공격 source MP4들과 byte-identical duplicate가 아니었다. 그러나 tracking JSON의 source field는 이 폴더의 영상 basename 또는 현재 pool manifest 경로와 직접 일치하지 않았다. sidecar 안에서 pool ID 문자열이 관찰된 사실만으로 영상·challenge·gesture family가 동일하다고 판정할 수 없다. 따라서 이 자료는 **독립 holdout 확정 자료가 아니라 연결 조사가 필요한 후보**다.

별도로 수신 자료 폴더의 MP4 18개는 A/B 또는 sessionLog JSON과 동일 basename이 없고 participant ID / internal timestamp도 파일명에서 연결되지 않았다. 이 영상들도 메타데이터 기반의 명시적 source manifest 없이 세션에 붙이지 않았다.

## 다음 데이터 요청의 최소 형태

사용자가 파일을 직접 찾아 공개 저장소에 올릴 필요는 없다. 현재 후보는 승인된 로컬 폴더에 있다. 기존 자료만으로 이어갈 때 필요한 것은:

1. 16개 별도 영상의 4개 그룹이 어떤 원본 gesture/source family에 해당하는지 설명하는 비공개 매핑(모르면 ‘미상’으로 남김).
2. 이 자료가 현재 attack reference library 또는 threshold/weight 선택에 쓰였는지에 대한 provenance.
3. 동일 challenge human/attacker 비교에 사용하려면 각 시도에 적용된 clip ID, 방향, keyframe, 전환/화면 조건 연결.
4. 독립 holdout 주장에는 attack/reference 개발에 쓰이지 않은 source family라는 확인. 이를 입증할 수 없으면 descriptive sensitivity material로만 사용.

이 문서에서는 raw scores, challenge IDs, 개인 식별자, 파일명, 로컬 경로, 해시를 공개하지 않았다.
