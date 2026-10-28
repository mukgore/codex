# G4 actual-code 결과 독립 해석 검토 — 2026-10-28

## 검토 범위

`media_lookup.py`, `circle_lookup.py`, 비식별 aggregate summary, `server.py`, `validation.py`, `test_integration.py`를 정적으로 검토했다. 이전 독립 Python 검산 결과도 포함한다. 개인별 자료나 raw 입력 행은 열람·복사·출력하지 않았다. 136회 전체 실험을 반복하지 않았다. 별도로 stationary-filter 반례만 8개 알려진 source에 대해 로컬 `LabService`에서 시험했다. 브라우저, 카메라, 외부 endpoint는 사용하지 않았다.

**판정:** 보존 자료의 여덟 알려진 source에 대해 오프라인·loopback 구현 안에서 재현 가능한 취약 신호가 있다. 독립 holdout, 인간 허용도, 원본 CAPTCHA의 과거/운영 L3 인증은 검증되지 않았다.

## 결과와 공격자 지식 가정

### 기존 136회 실제 코드 호출 평가

136회는 8개 알려진 source의 9개 응답 생성 조건과 서로 다른 reference source를 사용한 56개 조합으로 구성된다. 한 source가 여러 조건과 조합에 반복 등장하므로 136을 독립 표본 수로 해석하지 않는다.

- 모든 8개 exact replay가 점수와 합성 offline gate를 통과했다. 이는 oracle 상한 조건이다.
- 56개 wrong-library 조합은 score threshold를 56/56 통과했고 offline gate는 37/56 통과했다. 선택한 자료와 gate 모사 범위에서 점수만으로 잘못된 reference를 충분히 가르지 못한 신호다. 37/56을 새 동작에 대한 공격 성공률로 일반화할 수 없다.
- 별도 Python 구현이 136개 `score.captcha`, `score_pass`, `gate_pass`를 모두 일치시켰다. 불일치 0건, 최대 절대 점수 오차 `2.220446049250313e-16` (허용오차 `1e-10`). 이는 같은 입력·keyframe 분할·공식에 대한 구현 교차검산이지 독립 자료 검증이 아니다.

### 기존 공개 영상 cache lookup

`media_lookup.py`는 도전 전에 알고 있는 공개 영상 8개와 landmark reference를 cache로 구성한다. 도전 중 내려받은 MP4 bytes의 SHA-256을 cache에서 찾아 reference 응답을 고른다. `service.challenges[challenge_id]['key']`의 target 값은 답을 고른 뒤 결과 표시에만 사용된다. 코드상 target label이 predictor의 분류 입력으로 들어가지는 않는다.

보존 summary는 8/8 영상 식별, 8/8 score pass, 8/8 합성 offline gate pass, 8/8 **새 loopback 서비스의 test protected action 허용**을 기록한다. 이는 이전에 공개된 동일 파일을 닫힌 집합에서 재식별해 replay한 결과다. 서비스의 challenge 할당은 이번 실행에서 정렬된 고정 순환 순서였으므로, 임의·무작위 할당에서 같은 결과가 난다는 증거는 없다. 다만 구현된 predictor 자체는 순번 대신 받은 bytes의 exact cache match를 사용한다.

### Pixel metadata 및 circle lookup

- pixel summary: filename이 관측 가능하다는 조건에서 manifest의 정확한 파일명은 8/8 source를 직접 구별한다. decoded frame count만 쓸 때는 알려진 여덟 source 중 6/8이 고유하며 나머지 2개는 각각 둘의 후보가 남는다. 이는 이 고정 pool의 메타데이터 구별 결과다.
- circle summary: predictor는 contour probe에서 얻은 정규화 center/radius의 4개 값만 reference distance 계산에 사용한다. target ID는 nearest candidate 선택 이후 정답 여부 계산 및 후속 offline evaluator challenge 선택에 쓰이고, 거리 계산/정렬 입력에는 전달되지 않는다. 따라서 코드 흐름상 target label이 predictor에 직접 누출된 흔적은 찾지 못했다.
- 알려진 여덟 source를 모두 reference로 사용한 closed-set top-1 결과는 8/8이다. 이후 score/gate 재생은 circle 특징으로 새 landmark를 복원한 것이 아니라, 예측된 library source의 **전체 공개 landmark 궤적**을 target의 offline scorer/gate에 넣은 lookup replay다.
- contour 추출 결과와 독립 per-frame circle center/radius 정답을 대조할 자료가 없어, 관측 특징이 실제 원 정보를 정확히 재고 있는지 검증되지 않았다. 그러므로 이 결과는 제한된 알려진 library 식별 신호이며 독립적인 circle-only 공격 성능이나 새 source 성능으로 해석하지 않는다.

## Gate, score, local L3의 의미

실제 HTML에서 `computeScores`와 `onRes` 함수 본문을 격리 Node context에서 호출하지만 페이지 startup, browser, camera, CDN, 업로드 경로는 실행하지 않는다. `onRes` gate는 제출된 landmark와 timestamp를 fake clock에 넣고, matched callback은 keyframe을 즉시 진행시킨다. video playback/fade scheduling은 stub 처리된다. 따라서 gate 결과는 이 오프라인 조건에서 실제 함수의 pose threshold/hold 계산을 호출한 결과이지, 실시간 카메라의 브라우저 gate 재현은 아니다.

loopback test server는 미디어 제공부터 제출 검증, 서버 측 점수/gate 판정, 일회 grant, test protected action까지의 **새 로컬 offline-landmark 프로토콜**을 보인다. 그 서버는 프레임 좌표가 실제 카메라에서 왔는지 증명하지 않는다. 원본 CAPTCHA에는 검증된 역사적 보호 동작 endpoint가 없으므로 원본/운영 L3는 계속 **미확인/NOT_TESTED**다. `local_l3_allowed`는 이 새 모델 안에서만 유효하다.

## Stationary-filter 반례

서비스의 선택적 stationary filter는 검출된 모든 landmark 배열이 첫 배열과 정확히 같은지 `np.all(arr == arr[0])`로 검사한다. 동일 pose를 반복하는 baseline은 이 조건에 걸리지만, 실수 좌표에서 아주 작은 변동이 있으면 stationary로 분류되지 않는다.

확인용으로 각 알려진 source의 첫 검출 pose를 그 source의 전체 raw-frame timestamp에 반복하고, 매 두 번째 프레임의 단일 landmark 좌표에 `1e-9` normalized-unit 변화를 주어 filter가 활성화된 local `LabService`에 제출했다. 8/8 입력은 exact-equality filter를 통과했고, score pass 8/8, offline gate pass 5/8, test protected action 허용 5/8이었다. 이 특정 합성 counterexample는 exact-equality 필터가 미세 입력 변화를 견고하게 차단하지 못함을 보인다. 사람 입력이나 실제 카메라, holdout 성능에 대한 결과는 아니다.

기존 summary에도 almost-stationary 조건에서 5/8의 stationary-candidate local action 허용이 기록돼 있다. 따라서 이 간단 필터를 방어 성공으로 보지 않는다. 서버가 임의 좌표를 받는 구조에서 진짜 방어를 하려면 입력 provenance를 제공하는 신뢰 경계가 별도로 필요하다. 이 테스트 server는 그 경계를 구현하지 않는다.

## 서버 및 통합 시험의 정적 검토

확인된 유용한 범위 제한은 IPv4 loopback bind, Host/Origin 검사, JSON/body/frame 크기 제한, 정확한 submission schema, 유한 좌표·엄격 증가 timestamp·21×2 frame shape 검사, session/challenge/grant binding, 만료 및 one-time 소비다. 통합 시험은 client `passed`/`score` 삽입, 교차 session, replay, expiry, malformed frames 및 동시 요청을 포함한다. 별도 Blue Team 실행에서 9개 HTTP integration test가 통과했다고 전달받았으며, 이번 검토에서는 재실행하지 않았다.

남은 제한과 위험:

- `validate_frames`는 값의 모양과 finite 여부는 검사하지만 좌표를 화면 범위 `[0,1]`로 제한하지 않고, timestamp가 진짜 캡처 시각인지, landmark가 카메라에서 생성됐는지도 확인하지 않는다. API가 허용하는 알려진 landmark replay는 중앙 위협으로 남는다.
- session/challenge/grant 상태는 단일 프로세스 메모리에 있고 lock도 프로세스 내부 범위다. 재시작, 여러 worker/서버, durable atomicity는 검증되지 않았다.
- rate/query 제한은 없다. 제출 처리 중 service lock 아래 evaluator 계산이 수행되므로 동시 요청이 늘면 대기/서비스 거부 위험이 있다. body/frame 상한은 자원 가드이며 성능·운영 보증이 아니다.
- 이미 제출된 challenge의 media도 세션과 TTL이 유효하면 다시 읽을 수 있다. 반복 재생·수집 제한은 구현되지 않았다.
- challenge source 순서는 이번 media/pixel 실험에서 고정 순환으로 지정됐다. 이 설정으로 임의 배정의 비밀성이나 source exhaustion 공격 저항을 평가하지 않았다.
- HTTP-only loopback cookie/Origin 규칙은 로컬 시험 경계에 맞춘 것이다. 실제 서비스 보안 설계나 외부 노출 설정으로 확대할 수 없다.

## 연구 해석과 다음 검증

**확인된 범위:** 여덟 공개 source/reference의 닫힌 집합에서 MP4 cache matching과 circle-feature nearest lookup이 해당 집합의 label을 식별했다. 새 local offline-input server는 프레임을 다시 채점하고 합성 gate와 test action 결정을 내린다. 제한된 입력 오류·session binding·one-time 상태 동작도 통합 시험 범위에서 다뤄졌다.

**탐색적/조건부:** circle query 특징으로 알려진 library에서 source를 찾고 해당 library trajectory를 replay한 결과. Independent Python은 같은 136 attempts의 수치 구현을 별도로 일치시켰다. Stationary filter 반례는 알려진 pose에 대한 합성 입력이다.

**미검증:** independent source-family holdout, 신규 gesture 일반화, 실제 인간 통과율/사용성, camera provenance, 실시간 browser challenge, 원본 CAPTCHA의 end-to-end L3, contour center/radius의 독립 정확도, 운영 속도/부하/다중 worker 보안.

다음 확증 평가에는 미사용 source-family manifest와 독립 검토자 잠금, challenge 할당 무작위화, 실제 circle-feature ground truth, 사람과 동일한 challenge 비교(인간 결과를 주장할 경우), 승인된 capture trust/evaluator 설계가 필요하다. 현재 결과만으로 가림이 일반 공격 난도를 높인다거나 제품 방어가 검증됐다고 결론 내리지 않는다.

## 후속 보완: 비밀 순서 lookup, blind baseline, mask fault injection

### 무작위 순서 media lookup

`G4-MEDIA-CACHE-002`는 8개 공개 source/media를 닫힌 후보 집합으로 사용하며, 균형 잡힌 비밀 무작위 할당 순서를 predictor에 전달하지 않는 구성이다. Aggregate 결과는 8/8 식별, score pass, offline gate pass 및 새 loopback 서버의 local protected action 허용이다. 이는 앞선 고정 순서 구현의 순서 누출을 제거한 재실행 결과로 볼 수 있지만, 후보 source와 reference는 계속 알려진 기존 자료이며 표본은 8개뿐이다. 따라서 미사용 holdout, 신규 source 일반화, 독립 gesture 추정 성능 또는 원본 서비스 L3의 증거가 아니다. 기존 001 기록은 보존한다.

### 무정보 좌표 기준선

`G4-BLIND-001`은 영상 길이와 FPS만 아는 조건에서 [0,1] 좌표를 독립 균일 추출한 8회 탐색 기준선이다. summary에는 score pass 0/8, offline gate pass 0/8, guarded local L3 0/8이 기록되어 있다. Orchestrator는 별도 Python 검산 8건에서 불일치 0건을 보고했으나, 이 감사에서는 그 검산 산출물을 별도로 확인하거나 재실행하지 않았다. 이 결과는 무정보·비해부학적 입력이 이 조건에서 통과하지 못했다는 뜻에 한정되며, 방어 효과, 공격 난도 증가, 통계적 실패율 또는 유효한 사람 동작 공격과의 비교를 입증하지 않는다.

### Stage 6 mask fault-injection 검토

새 실험 코드는 기존 Stage 6 함수의 AST 추출본과 기존 영상의 처음 3개 decoded frame을 사용한다. Video capture/writer는 메모리 spy로 대체했고, 실제 decode와 circle rasterizer는 사용했다. 집계 기록상 legacy 경로에서는 첫 프레임 landmarks 누락 시 원본 frame 출력, 중간 누락 시 이전 mask 재사용, 짧은 landmark map의 tail 재사용, z-only 변경에 따른 radius 변경이 재현됐다. strict wrapper는 완전한 3-frame fixture를 받아들이고 첫/중간 누락 또는 frame-count 불일치를 출력 전에 거부했으며, z-only 변경에서 2D mask/output이 불변이고 입력 decoded images가 바뀌지 않았다. 요약에 기재된 7개 국소 테스트 통과는 작성팀 보고이며 이 감사에서 재실행하지 않았다.

이 결과는 제한된 기계적 fault-injection 검증이다. 실제 전체 영상 decode/encode pipeline, 배포 산출물, 실제 challenge에서의 정보 누출, 공격 성공률 또는 보안 효과를 검증하지 않았다. 처음 3개 frame과 테스트용 비보정 W3 값에 국한되고, AST 추출 함수와 메모리 writer 경로를 썼다. 따라서 누락 데이터에서 stale mask나 원본 frame이 나올 수 있는 코드 경로를 보여주는 근거로만 해석해야 한다. 배포 자산의 실제 누출이나 방어 완료 주장으로 확대할 수 없다.

## Legacy reference 보완 평가

`G4-LEGACY-SUPPLEMENT-001`은 현재 manifest 밖에 있는 기존 공개 legacy reference 6건을 대상으로 각 reference에 exact replay, 첫 pose 유지, 양 끝점 보간, 현재 pool의 고정 reference 재생성 등 4조건을 적용한 탐색적 평가다. 결과 집계는 네 조건 모두 score pass 6/6이며 offline gate pass는 각각 6/6, 0/6, 2/6, 2/6이다. 이 run은 L3를 시험하지 않았다. 별도 Python 재구성은 24건의 score, score 판정, gate 판정을 모두 일치시켰고, 최대 score 절대 오차는 `7.216449660063518e-16`으로 허용오차 `1e-10` 이하였다. 검산 요약은 개인/원자료 없이 private validation 파일에 보존했다.

이 6건은 현 manifest 밖이라는 사실만으로 미사용 holdout이 되지 않는다. 과거 개발·보정 lineage가 확인되지 않았고, 좌우 및 동작 관계가 있어 여섯 개의 독립 표본으로 간주할 수 없다. 독립 Python 검산도 동일 자료와 공식의 교차 계산이며 holdout 검증이 아니다. 이 결과는 score pass가 다른 reference 집합에서도 나타난 한편 gate pass는 입력 조건에 따라 달랐음을 보여주는 제한된 관측이다. 다른 source family에서 gate가 더 강하거나 약하다는 일반 결론, 신규 동작 일반화, 인간 성능 또는 실제 CAPTCHA 우회 성공을 뜻하지 않는다.
