# TF-04 공통 화면 조건의 A/B/C/U 대조 — 사전등록 v1

TF-03의 검산된4경로를 입력으로 등록한다. 실제 촬영/선별 입력이 없는 동안 가능한 공급/표시 진단이며 기존1→2→3A→3B→4→5→6·전체62개ID/3D44요구/R0–R9를 대체하지 않는다. prod/UI·원임계값·비공개 영구보관·Cloud보류를 유지한다. GitHub push는 기존 자동승인 거부 후 명시적 승인 대기 상태이며 이번 로컬 실행과 구분한다.

## 비교 조건과 실제 계산 분모

양손×seed7/19의4조건마다 다음4arm을 만든다. 총16조건×기존2시점=32source영상/800렌더프레임이다. 새로운 독립family가 아니다.

| arm | 원자료와 길이 | 관문에서의 취급 |
|---|---|---|
| A | 기존 middle_only_cues_open/preflex20의25단계 원형. beta/root0으로 새 SDK계산. 기존phase는 유지하고 PTS만0–3초로 공통화 | 실제 반환값의 모델 prior/샘플표면 지표를 새로 검사 |
| B | TF-03 시작 waypoint인 수정된 정적자세를25회 반복 | 성공한 원출력 감사의 모델/샘플표면 판정과 actual파일을 대조 |
| C | TF-03의 실제25프레임 경로를 그대로 재사용 | 완료 receipt/100프레임 실제 모델·표면 판정 재검증 |
| U | B와 같은 원래 PCA 부모 자세를25회 반복 | 기존 모델 prior 위반을 보존하는 무수정 대조. 위반하면 가림/최종 채택 거부 |

B/C/U의 actual좌표와 surfaceQA는 보존된 입력을 재사용한다. A100프레임+양손neutral2=102새 SDK자세(25프레임배치4+단일neutral2의6호출)만 계산한다. 입력 bundle의400좌표프레임 중300은 재사용이며400새추론으로 세지 않는다. 기존 동작/영상/실패생산자를 재실행하지 않는다. 수정생산자의 `PROCESS_ERROR`와 별도 원출력감사 `EXITED_ZERO`를 둘 다 명시적으로 검증한다.

모든arm은 beta/root0, 동일BGR[170,205,225],25프레임·8FPS·512×420이다. 첫–마지막PTS는3.0초,25/8의 명목 영상길이는3.125초이며 둘을 혼동하지 않는다. A의 원래시간분포를 일반 성능기준으로 재현한 실험이 아니라 같은 표시격자의 조건부 비교다. B의 정적반복은 실제 정지손/카메라가 아니다.

## 카메라·가림·최종 관문

기존 완료 `mug_20261115`의 shared camera를 바이트 그대로 복사해 새입력 bundle에 포함한다. 현재조건에 맞춰 재calibration·시점최적화·개별clip fit을 하지 않는다. 각손은 beta0 neutral의 고정proper등록, 각clip은 첫wrist평행이동만 제거한다. 원래 두시점/화면크기/기준을 유지한다.

고정 profile/assignment/source-review blob과 현재neutral/topology를 검증해 **author_region_union**만 사용한다. 기존 rest보호면과 저자부위의 합집합을 줄이지 않고 legacy대체를 허용하지 않는다. 기존source별 radius구간/Stage7,2픽셀 codec core, 원밖 비목표손끝patch 최소2개, 채널30/외부MAE2.0 등 기존관문을 유지한다. radius구간 선택은 기존원형생성의 같은함수이며 이 실험에서 기준을 보정하는 것이 아니다.

모든32source를 FFV1로 만들고 저장pixel hash/프레임수/PTS를 실제decode로 검증한다. 모델·샘플표면/legacy·union radius구간/Stage7/정확한 raster·codec core/patch조건이 모두 충족될 때만 가림후보와H.264를 제작한다. U같은 upstream모델위반은 interval이 가능해도 채택하지 않는다. 관문거부도 결과이며 보호영역·공개단서기준을 줄여 성공 수를 채우지 않는다.

허용된 후보/최종은 실제decode로 union영역 채널/외부화질을 재검사한다. 조건별 모델/표면·가림/영상 생성 분모와 재사용QA를 분리한다. 최종파일이 있으면 바이트/픽셀중복·부모/계열/노출·점수를 후속기록으로 비교하고, 최종이 없는조건은 소스투영 점수와 ‘최종 미생성’을 구분한다. 현재 고정 prod 수치진단은 실제카메라/hold/인증 성능이 아니다.

## 사전 기록과 실패 처리

native bundle은 기존17pin CPU·600초, display는 기존26pin OpenCV/FFmpeg·900초를 별도 config/immutable root/receipt로 기록한다. production변경/새설치/외부업로드는 없다. 각영상의 ready(인코더종료 또는 library반환)/추가검산완료·UTC/wall/자체CPU·단계·bytes/FPS/길이·캐시·공통준비·실패를 보존한다. 자체CPU에 FFmpeg자식CPU를 합산했다고 가정하지 않는다. 새SDK·source제작·가림·H.264의 시간 범위를 구분한다.

실행 중 전체worktree를 편집/커밋하지 않는다. 오류/중단/부분출력을 보존하며 동일root를 덮어쓰지 않는다. 출처/환경/명세·코드/전체worktree와 모든부모입력/기록을 사전 snapshot, 종료/stdout/stderr/출력hash를receipt에 연결한다. 전 결과는 연구격리·여섯한계미확정·사람/임상연동/연속충돌/물리·운영/보안미승인·풀0개다.
