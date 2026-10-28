# G4 공격 결과 및 정보 가정

실제 소스의 채점 함수를 호출한 탐색 결과다. 원래 페이지는 두 clip의 재생·전환을 포함한다. 여기서는 한 clip의 실제 keyframe 구간을 공유 경계 프레임으로 나누어 computeScores를 호출했다. 관문은 실제 onRes에 replay 시계를 주입하고 영상/페이드 스케줄을 생략했다. 원래 전체 UI·실시간 카메라 결과로 해석하지 않는다.

threshold .25, angle 38°, hold 200ms, W2/MX는 실제 HTML 값을 그대로 사용했다. Source 8개는 이미 공개 reference에 포함됐으며 모두 개발 자료다. 방향·변형·56개 오답 pair는 독립 표본이 아니다. 성공률 모집단 추정이나 확증 CI를 계산하지 않았다.

## 실제 계산 및 신규 loopback 서버

| 응답 | 건수 | score 통과 | offline gate 통과 | guarded local L3 허용 | stationary 후보 L3 허용 |
|---|---:|---:|---:|---:|---:|
| 기준 궤적 exact replay (oracle control) | 8 | 8 | 8 | 8 | 8 |
| 첫 자세 고정 | 8 | 8 | 5 | 5 | 0 |
| 중간 자세 고정 | 8 | 8 | 6 | 6 | 0 |
| 마지막 자세 고정 | 8 | 8 | 5 | 5 | 0 |
| 시작/끝 자세 선형 보간 | 8 | 8 | 8 | 8 | 8 |
| 역순 재생 | 8 | 8 | 6 | 6 | 6 |
| 프레임 순서 섞기 | 8 | 7 | 6 | 6 | 6 |
| 모든 좌표 0 | 8 | 8 | 0 | 0 | 0 |
| source별 관절 bounding box 내 무작위 | 8 | 5 | 5 | 5 | 5 |
| 첫 자세 + 표준편차 1e-8 잡음 | 8 | 8 | 5 | 5 | 5 |
| 다른 source의 저장 궤적 | 56 | 56 | 37 | 37 | 37 |
| 사전 pose 없는 uniform [0,1] 좌표 (별도 run) | 8 | 0 | 0 | 0 | 미실행 |

위 표의 고정/보간/bounded random은 알려진 목표 reference를 사용하는 강한 사전지식 조건이다. Blind uniform은 길이·fps만 사용한다. 모두 관절 좌표 입력이며 실제 손 영상 추론/가상 카메라 실행은 아니다. 모든 좌표 0은 점수를 넘었지만 관문이 막았고 새 validator도 거부했다. 이를 전체 인증 성공으로 세지 않았다.

Local L3는 새 서버가 실제 함수를 재계산하고 gate+score를 만족한 grant를 받아 protected action counter를 한 번 증가시킨 결과다. 과거 시스템 L3는 NOT_TESTED다.

## 실제 MP4 채널

| 채널 | 관측/사전지식 | 결과 | 제한 |
|---|---|---|---|
| 파일명 | 공개 manifest | 파일명이 보이면 8/8 직접 연결 | 새 서버는 원래 이름·reference 경로를 반환하지 않음 |
| 전체 프레임 수 | 실제 decode count + 알려진 8개 manifest | 6/8 singleton, 나머지 2개는 같은 길이 | 알려진 작은 풀 안의 식별성 |
| 원 후보 cx/cy/r 궤적 | 실제 MP4 최대 30프레임/clip; 공개 landmark에서 q=1.95 예상 원 library | 8/8 top-1, 동점 0; 선택한 전체 library replay score/gate 8/8 | 실제 원 위치·반경 GT 정확도는 미측정. Skin-bit/손 좌표는 query에 사용하지 않음. Reference 지식은 강함 |
| 영상 바이트 캐시 | 불투명 URL의 실제 로컬 MP4 + 과거 공개 영상/답안 사본 | 순서 비공개 무작위 배정에서도 8/8 식별, score/gate/신규 local L3 8/8 | 동일 공개 자산 재사용·좌표 제출 조건. 실제 카메라 또는 미관찰 source 결과 아님 |

원의 궤적 lookup 성공은 이 8개 known-source 자료에서 관측됐다. 프레임별 원 추정 정확도, 새로운 촬영, 가림의 상대 난도 증가는 별도 검증이 필요하다. Metadata와 원 궤적을 제거한 무가림/가림 대응 통제 실험은 수행하지 않았다.

## 현재 pool 밖 legacy 보충 검사

공개 landmarks_base의 6개 이전 기록에도 현재 함수를 직접 호출했다. 이 자료는 현재 challenge manifest에 없고 과거 개발/calibration 사용 계보가 불명확하므로 독립 holdout이 아니다. 좌우·같은 동작의 연결을 포함할 수 있어 독립 표본 6개로 취급하지 않는다. L3는 미실행이다.

| 응답 | 건수 | score 통과 | offline gate 통과 |
|---|---:|---:|---:|
| 해당 legacy 기준 replay | 6 | 6 | 6 |
| 해당 첫 자세 고정 | 6 | 6 | 0 |
| 시작/끝 보간 | 6 | 6 | 2 |
| 현재 8개 pool 중 고정한 한 다른 기준 궤적 | 6 | 6 | 2 |

Legacy 고정 자세에서는 gate가 모두 막았다. 현재 8개 결과를 모든 동작에 일반화하면 안 된다는 반례이며, 두 자료 집합의 점수·관문 패턴을 합치지 않았다. [보충 집계](../../reports/g4_actual/legacy_supplement_summary.json).

근거: [계산 집계](../../reports/g4_actual/summary.json), [blind](../../reports/g4_actual/blind_summary.json), [metadata](../../reports/g4_actual/pixel_summary.json), [circle](../../reports/g4_actual/circle_summary.json), [무작위 배정 cache](../../reports/g4_actual/media_lookup_randomized_summary.json).
