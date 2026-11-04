# 감사 후 순차 구현 기록

사용자는 손바닥을 카메라에 보이도록 돕는 UI 아이디어 추가와 남은 항목의 순차 실행을 요청했다. 아래는 190행 감사 스냅샷 이후의 실제 진행 기록이다. 기존 G1~G4의 수용 범위는 유지한다. 기존 코드를 수정해도 새 사람/독립 공격 성능은 실제 입력이 확보되기 전 완료로 표시하지 않는다.

## 진행 순서

| 순서 | 묶음 | 진행 상태 | 선행 조건·완료 근거 |
|---|---|---|---|
| 1 | 손바닥 안내 UI 후보 | 평가·3종 구현 | [12종 평가와 선정 근거](2026-11-04_palm_ui_evaluation.md). 01 문구/02 비교 그림/03 준비 단계 |
| 2 | 가림·타임라인·배치 산출물 | 연구 후보 경로 구현·검사 | 필터/역재생 map→비공개 FFV1→변경 없는 Stage6→MP4/시간검사→후보 manifest. 독립 PTS/운영 release는 별도 |
| 3 | 선택 손·손바닥 안내·이벤트 기록 | 독립 시연 구현·검사 | 준비/선택/자가 확인/재생 분리, trial별 로컬 허용 이벤트. 실제 prod/카메라·사람 효과 검증은 남음 |
| 4 | 표준 좌표/시간 adapter와 후보 비교 | 코드·합성 검사 완료, 실자료 평가 대기 | [명시 단위/미러·gap·분모·후보 특징](2026-11-04_standard_adapter.md). 보정 점수·B0 변경 없음 |
| 5 | 자체 P1 생성 파일럿 | 연결 시험용 3D fixture 구현, 실측 P1 대기 | 사용자: 원본 동작/대응 자료 없음. 자체 골격 3종→렌더→가림 MP4. 인체·접촉·사람 검증 없음 |
| 6 | R1 원형 재현·사람/공격·운영 | 입력 조건별 진행 | 허용 데이터·모델·checkpoint/자원·대응 정상/독립 source 필요 |

별도 새 참가자 모집·기업 연락·유료 결제·운영 배포가 필요한 항목은 현재 사용자 요청에서 자동 실행하지 않는다. 필요한 자료를 확인하고 독립 가능한 코드·합성 검증을 계속한다. 추가 패키지 설치를 기본 선행 조건으로 삼지 않는다.

## 표준 adapter와 자체 작성 3D fixture 후속 실행

[표준 adapter](2026-11-04_standard_adapter.md)는 입력 영상 크기·좌표 공간·ms/s·미러·최대 gap을 명시해야 한다. 손목 중심/중지 MCP scale, 15개 각도와 실제 초 단위 시각을 보존하며 누락·잘못된 기하·큰 공백을 연속 block으로 나눈다. 실패/짧은 block도 분모에 남긴다. 기존 DTW와 실제 시각 미분을 연결해 raw 후보 특징을 만들지만 score=None이며 B0 산식·임계값은 변경하지 않는다. 새 11개와 기존 수학12/점수 비교7의 30개 검사를 통과했다. 실자료 대응·학습/calibration·군집 CI·JS 이식은 남아 있다.

사용자에게 가림 없는 원본 동작 2~3종 및 대응 자세·시간 자료를 물었고, 답변은 **없음**이었다. 이를 임의의 가려진 관절 추정치로 대체하지 않았다. handcaptcha의 [자체 작성 골격 fixture](https://github.com/mukgore/handcaptcha/tree/work/todo-consolidation-20261103/experiments/motion_fixture)는 정해진 index_flex/middle_flex/alternating 동작과 seed 진폭으로 3D 뼈 좌표를 만들고, 정사영 렌더·decoder 시각·Stage7 v2·기존 Stage6·출력 검사까지 연결한다.

실제 실행은 세 동작 각각 seed=7, 24frame, 12fps, w3=2.5다. 각각 24/24 frame의 기하 gate를 통과했고 masked MP4와 manifest를 생성했다. source/가림 preview를 눈으로 확인했다. 이 수치와 관절 범위는 연결 시험 조건이며 인체의 안전 범위나 연구 기준이 아니다. 결과는 `RESEARCH_FIXTURE_ONLY`, release_allowed=false이며, 자체 좌표·영상은 Git 제외 폴더에만 남긴다. surface collision/물체 접촉/잡기 물리/사람 수행 가능성/보안 효과는 시험하지 않았다. seed나 동작 이름을 독립 family 수로 세지 않는다. Text2HOI 원형 재현 또는 완성된 실측 P1로 표시하지 않는다.

fixture 5개 검사까지 포함한 관련 검사는 **106개**다: handcaptcha unittest39 + 기존 함수17 + Node20, codex adapter11 + 수학12 + 점수 비교7. 기존 test_calculations 4개는 openpyxl 부재로 앞서 실행 불가였으며 이 숫자에 포함하지 않는다. 추가 설치는 하지 않았다. 아래 71개는 adapter/fixture 추가 전 단계의 기록이다.

## 다음에 필요한 입력과 남은 작업

- UI: 실제 카메라와 모델·좌우손/미러/소실·재시도 사용성, 손바닥 방향 효과 비교, prod의 문제/gate/timer 연결. 현재는 독립 시연이다.
- 표준 특징: metadata가 확인된 같은 trial의 legacy 결과와 후보 특징, 사전 고정한 개발/validation/test 분할, score 변환·학습·calibration 및 독립 사람/공격 평가.
- 생성: 허용된 가림 없는 원본 동작과 대응 자세·시간, 물체·접촉 모델/검사, 사람 수행 가능성과 공격·비용 평가. 원본 부재 상태에서는 실측 P1을 완료할 수 없다. R1은 별도의 허용 데이터/모델/checkpoint/자원이 필요하다.
- 가림/운영: 별도 legacy/bake 경로의 동일 검증 적용, 독립 container PTS/VFR·track 검사, 권리/상태 전이/release validator·운영 media/server 검증. 현재 후보 MP4가 있어도 운영 출하는 완료되지 않았다.

190행 스냅샷의 과거 미구현 판정은 위 후속 변경과 함께 읽는다. 남은 요구를 통째로 완료로 승격하거나 완료율로 환산하지 않았다.

## 손바닥 방향 요구의 코드상 공백

현재 prod에는 “손바닥이 카메라를 향하도록” 문구가 있지만 독립 시연은 방향을 구체적으로 안내하지 않았다. dataset_pipeline의 frame_theta는 normal 각을 0~90도로 접어 손바닥/손등 양쪽을 정면으로 취급한다고 코드에 명시한다. 따라서 기존 frontality 통과를 손바닥 방향 통과로 표시할 수 없다. 우선 손금이 보이는 쪽을 렌즈로 향하게 하는 명시적 문구·그림·준비 단계를 구현하고, 자동 판정은 좌우손·미러·측면/굽힘 불확실성을 검증한 뒤 별도 연결한다.

## Stage6 유지·Stage7 수정 결정과 실행

사용자가 충돌 설명을 검토한 뒤 “stage6을 유지하고, stage7을 그에 맞게 수정”하도록 지시했다. Stage6 파일과 가림 수식은 변경하지 않았다.

Stage7 정책 `midpoint_middle_pip_visible_fingertips_v2`는 중지 PIP와 두 중간점의 안쪽 가림 조건을 유지한다. 손목/손바닥 5지점 전체 노출 조건을 폐기하고 엄지·검지·약지·소지 끝점 중 설정한 수 이상이 여유를 둔 원 밖에 남도록 검사한다. 기본 최소 2개는 공학 초기값이며 `condition2_min_visible_fingers` 1~4 설정으로 드러낸다. 손바닥 방향 판정이나 사람의 인지 가능성으로 해석하지 않는다.

변경: common/config/Stage7, batch 보고서의 정책 버전, 기존 함수 회귀 수정, 새 `test_stage7_v2.py`, `dataset_pipeline/GATE_POLICY.md`. 반환값에는 정책 버전·가시 손가락·실패 이유·프레임별 기하 진단이 포함된다. 기존 결과는 재계산하거나 덮어쓰지 않았다.

검사: unittest 발견 20개(기존 가림 9+새 Stage7 11)와 기존 무인자 함수 17개가 통과했다. 새 검사는 Stage6의 실제 합성 MP4 출력에서 중지 PIP·손목이 검게 가려지고 비대상 손끝이 남는 것을 재디코딩하여 확인했다. Stage6의 Git diff가 비어 있음을 확인했다. 새 사람/독립 공격 성능·운영 출하는 별도다.

## 프레임 대응·배치 출력과 손바닥 안내 실행

Stage1의 decoder 시간(ms)을 원본 index와 함께 기록하고, 필터/역재생 뒤 출력 index·CFR 시각·원본 index/시각·reference index를 명시적으로 연결했다. 원본을 다시 decode해 추출 정보와 대조한 뒤 손 좌표와 같은 순서로 비공개 lossless 중간 영상을 만들고 기존 Stage6을 호출한다. 최종 MP4의 개수/크기/가림 내부 및 CFR 시각을 검사한다. 누락 시간·모순 좌표·frame count/FPS 불일치·가림/인코딩 실패·예산 초과는 후보 게시를 거부한다. 기존 후보는 덮어쓰지 않는다.

batch는 실제 후보 MP4와 artifact manifest를 연결하고, 생성 실패를 `quarantined_render`로 기록해 artifact 목록에서 제외한다. CLI 기본은 후보 생성, `--report-only`는 기하 보고서만 만든다. Python API는 호환성을 위해 렌더를 명시적으로 켜야 한다. 출력은 `RESEARCH_CANDIDATE`, `release_allowed=false`, `rights_status=UNREVIEWED`다. decoder 시간 왕복 일치는 독립 container PTS·VFR 원 duration 보존·다른 track·권리·사람/공격 승인 완료를 뜻하지 않는다.

손바닥 UI는 12종을 네 기준으로 사전 평가해 짧은 손금 문구·손바닥/손등 비교 그림·문제 재생 전 카메라 준비의 세 개를 구현했다. 안정적인 손 선택과 명시적 자가 확인 뒤에만 문제를 재생한다. 원본 카메라 검출과 화면 중첩은 분리한다. 준비/시작/소실/재시작/완료/오류를 최대 1,000개 로컬 이벤트로 기록하고, 사용자가 버튼을 눌러야 내보낸다. 영상·좌표·파일명·참가자 ID를 거부하며 재시작은 새 trial 번호다.

최종 관련 검사 **71개 통과**: Python unittest 발견 34(기존20+timeline/candidate11+추출 resource3), 기존 무인자 함수17, Node20. 별도로 1280px/390px headless Chrome에서 가로 넘침 없음·준비 화면/두 그림·기본 시작 잠금·좌우손 그림 전환을 확인했다. Computer Use 커널 경로 오류로 실제 창 제어 대신 별도 Chrome 프로필에서 정적 화면을 검토했다. 실제 카메라·사람 사용성 시험은 수행하지 않았다. Stage6 해시/파일은 유지했다. 기존 G1~G4 연구 재실행·추가 패키지 설치·운영 배포는 없었다.
