# 재개 후 실제 처리 기록

**최신 안전 종료:** 사용자가 하던 작업까지만 저장·정리 후 종료를 요청했다. 아래 코드/검사 기록까지 보관하고 서버8766/8767을 종료했다. 인계 전체나 실제 모델·운영 연구가 완료됐다는 뜻은 아니다.

## 종료 전 추가 완료

- MediaPipe 한글 설치 경로 우회를 일반 extract API의 격리 worker로 구현했다. 설치 asset만 복사하고 부모/설치 파일은 변경하지 않는다. 실제 기존 원본113frame/113검출 확인. legacy 진단은 기존 Stage3에 거부되어 격리됐고 기준을 변경하지 않았다. 실패/timeout을 batch 분모에 남기며 출력 소유권/새 보고서 전용 쓰기로 기존 결과를 보존한다.
- runtime journal의 상태/순서/hash chain/프레임 분모·중단/손상·bundle 재검산을 구현했다. 검사8개 및 실제 모델 없는5상태 smoke(COMPLETED/ERROR/TIMED_OUT/UNAVAILABLE/INTERRUPTED)를 실행했고 별도 프로세스가 모든 bundle 복구 결과를 동일하게 읽었다. GPU/HaMeR 측정·Colab VM 재설정 검증은 아니다.
- 독립 ffprobe container 검사와 masked-only H.264 파생본을 구현했다. 실제 자체 fixture24frame의 primary와 H.264에서 track/packet/CFR2초를 검사하고 모든 mask 내부/보이는 영역 codec 차이를 대조했다. Chrome 재생/seek도 확인했다. state는 연구용이며 실제 권리/인체/공격 승인 자료를 등록하지 않았다.
- 기존 간이 서버의 seekable0 문제를 확인해 byte Range를 지원하는 public preview 서버를 추가했다. hidden/private/traversal 경로를 거부하며 실제 HTTP의 Range/HEAD/416을 검사했다. 운영 registry/tenant/만료 송출 구현과 구분한다.
- 기존 연구용 .venv를 발견해 codex 전체 unittest45개가 통과했다. 이전 global interpreter에서 openpyxl 부재로 실행하지 못했던4개도 포함한다. 추가 Python package 설치는 없었다. 다만 이 .venv에서도 MediaPipe/protobuf 충돌은 남는다.
- 새 실행 파일은 사용자의 도구 승인 후 프로젝트 private_tools에 FFmpeg9.0.2를 다운로드하고 공개SHA256 대조/버전 확인했다. 시스템 PATH/Python package는 변경하지 않았으며 binary는 Git에 넣지 않는다.
- 마지막 handcaptcha Python 검사94개(discovery77+기존 함수17) 통과. JS 연결9개와 기존 JS20개 기록도 유지한다. 실제 연구·새 사람·운영 성능의 수치로 합산하지 않는다.

모델 보유 질문에 사용자가 없음이라고 답했다. [준비 상태](2026-11-04_model_readiness.md)와 공식 접근 조건을 기록했다. 실제 R1/HaMeR 실행·새 독립 사람/공격·권리 승인·운영 송출 등은 아직 미완료다. 다음 입력/환경 없이 완료로 승격하지 않는다.

사용자는 인계 작업을 계속 진행하도록 요청했다. 원격 갱신 timeout 이후 작업을 끝낸 응답은 미완료 작업의 종료가 아니었다. 아래는 실제 후속 실행 기록이며 인계 전체가 완료됐다는 뜻이 아니다.

## 완료한 후속 코드

- 대기하던 prod UI 문서 commit 9f8a447을 원격 작업 브랜치에 정상 fast-forward 반영했다. GitHub 연결 도구의 반복 timeout 후 기존 Git 인증을 사용했다. 로컬 codex 이력을 강제 push하지 않았다.
- handcaptcha 0c6a6aa: notebook 원본 편입의 누락 export_pool import와 무검사 legacy 복사를 제거했다. 원본 영상을 현재 Stage1~7/후보 renderer로 재처리하고 새 비공개 intake에만 저장한다. 기존 운영 pool을 덮어쓰지 않는다. 관련 5개 검사 통과.
- handcaptcha a9390f7: 별도 bake의 이전 mask 재사용/FPS=12 fallback/자동 설치·실행을 제거하고 공통 파이프라인으로 전환했다. 입력 FPS를 실제 영상과 대조한다. 시각 근거 없는 JPEG 폴더는 거부한다. 관련 4개 검사 통과.
- handcaptcha 78d192d: SQLite의 순차 review 승격/동시 revision/파일·보고서 해시/권리 만료/종료 상태/연구 전용 release 금지를 구현했다. 검토 사실 자체는 신뢰하는 검토자의 실제 보고서가 필요하다. 관련 8개 검사 통과. 실제 승인 또는 운영 서버 연결 결과는 아니다.
- 같은 commit: candidate/batch/intake/bake/fixture 출력과 등록부를 저장소 웹 루트 밖으로 제한했다. Git ignore를 HTTP 접근 제어로 오인하지 않도록 보완했다. 관련 3개 검사 통과. 기존 자체 생성/원본 점검 파일은 저장소 밖 private_artifacts/handcaptcha로 옮겼다.

최신 Python unittest discovery 59개가 통과했다. 기존 무인자 함수17/Node20/codex30의 변경 없는 검사 기록과 합하면 관련 항목은 126개다. 모든 126개를 이번 한 명령으로 실행했다는 뜻은 아니다. Stage6 blob 37c7ccfe068ed64b97750c6bcc59bd068e96183b는 유지했다.

## 기존 저장소에서 발견한 관찰 원본 한 개

사용자가 별도로 제공할 원본은 없다고 답한 뒤, 이미 저장소에 있던 left_1_experiment ZIP 안에서 baseline_original.mp4와 experiment_data.json을 확인했다. 영상은 720×720/24fps/113frame이며 보관된 추정 좌표의 frame 번호가 decoder frame 번호와 일치한다. 독립 촬영 계보·정밀 3D 정답을 이 사실로 증명하지 않는다.

기존 설치 MediaPipe가 한글 경로에서 graph 초기화를 실패했다. 별도 점검 프로세스에서 이미 설치된 resource를 비공개 ASCII 상대 경로로 복사하고 해당 프로세스의 resource 경로만 조정해 실행했다. 설치 파일 변경/추가 다운로드·설치가 없다. 113frame 모두 검출했고 decoder 시각은 단조 증가했다. 새 world 좌표는 MediaPipe 추정값이며 측정된 3D 정답이 아니다. 이 우회는 일반 CLI에 자동 적용된 기능이 아니다.

원본/추정 좌표/상세 해시는 공개 commit에 넣지 않았다. 로컬 private_artifacts/handcaptcha/existing_archive_inspection_v1에 보관한다. source는 하나이며 독립 test·새 사람 성능·동작 수행 가능성·운영 권리 검증 자료로 승격하지 않는다. 자체 작성 fixture가 완성된 실측 P1 또는 Text2HOI 재현이 된 것도 아니다.

## 계속 남은 것

[이력 패턴·환경 진단 및 새 main 근거 연결](2026-11-04_history_environment_audit.md)을 추가했다. 패턴 검사430blob/ZIP7, 후보0건이나 의미상 개인정보 감사 완료는 아니다. 실제 환경은 MediaPipe0.10.9/protobuf5.29.6 충돌 상태다.

### prod 선택 연결 후속 구현

handcaptcha `experiments/prod_selected_hand`에 기존 B 화면을 기반으로 두 손 검출/선택 손과 해당 handedness 전달, 소실·모호성·긴 공백·timeout의 전체 시도 중단, 늦은 sequence/result callback 차단, 카메라 late stream/완료 loop 정리, 전체 reload 재시작과 로컬 이벤트 저장을 연결했다. 기존 prod 원본·B UI 비교 원본은 보존한다. 기존 metric 코드와 38도/200ms 상수 동등성을 확인했다.

새 정책의 gate gap 200ms/tracking gap 500ms/trial 60초는 검증되지 않은 공학 초기값이다. 실제 사용자를 차단하지 않는 별도 실험 경로다. Node 연결6개 통과, PC/모바일 실제 DOM에서 합성 검출 packet으로 선택 index와 라벨 대응/소실 중단/늦은 시작 차단을 확인했고 JS 예외0건, 두 패널/가로 넘침 없음이었다. 실제 카메라/모델/사람 수행을 검증한 결과는 아니다. 기존 검사126에 이 연결6개를 합한 관련 항목은132개이며 browser2화면은 별도다.

실제 생성 HTML의 initCam/bootstrap/loop를 읽는 async 검사3개도 추가해 통과했다. 중단 후 늦게 들어온 stream 정지, 늦은 모델 초기화 뒤 카메라 획득 금지, 완료 후 in-flight inference의 loop 재예약 금지를 확인한다. 사용자는 지금 직접 카메라 확인이 가능하다고 답했고 로컬 링크/확인 순서를 안내했다. 실제 사용자 시험 결과 회신은 아직 대기 중이다.

후속 사용자 보고: 카메라/목표 영상 표시, 선택 손 유지, 소실 후 중단의 1·2·3항목이 정상이라고 답했다. 해당 세 항목은 사용자 PC 실기 확인으로 기록한다. 4번 전체 다시 시작은 별도 확인 질문에 회신 대기 중이다. 기기/브라우저/반복/원시 이벤트 로그는 미수집이며 1회 기능 확인을 새 참가자 비교·면 오류율 개선·보안 검증으로 확대하지 않는다.

4번도 후속 회신에서 “정상적으로 다시 진행됨”으로 확인했다. 네 기능의 사용자 PC 실기 확인은 완료했다. 위 대기 표현은 회신 전의 기록이다. 정량 효과/다른 기기·사람 검증은 남는다.

아래 “선택 연결”의 코드 공백 일부는 위 버전으로 보완했지만 실제 카메라/모델·기기·사람 비교는 계속 남는다.

- 원래 prod UI 안에서 선택 손/handedness/문제/gate/timer 초기화를 연결하는 별도 실험 버전과 실제 카메라 확인.
- 등록부와 비공개 송출 서버/검토자 인증 연결, 독립 container PTS·모든 track/rendition 검사, 운영 접근 경계.
- 실제 대응 trial·분할에 근거한 후보 score/calibration/독립 사람·공격·군집 CI·JS shadow/parity.
- 실측 P1의 실제 관절/접촉/사람 타당성, R1의 허용 데이터/checkpoint/환경, 비용·새 사람/시장 관찰.
- 전체 이력의 원자료/비밀값 감사, 재현환경 잠금 등 원래 감사의 후속 항목.

입력이 없는 항목을 완료로 표시하지 않는다. 190행은 전달 당시 스냅샷이며 이 문서와 후속 구현 기록으로 변경을 추적한다.
