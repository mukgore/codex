# 완료 영상의 실제 MediaPipe 픽셀 추정 진단 — 사전등록 v1

등록 촬영 21행의 원본 경로와 선별 관측은 여전히 0이다. 실제 사람 평가와 1/2/3A·독립 보정은 필요한 입력으로 남긴다. 전체 목표의 가능한 4단계 진단으로, [TF-04 완료 영상](deliveries/2026-11-16_matched_display.md)에 기존 로컬 MediaPipe를 적용한다. 가림에 대한 사람·모델 우열, 실제 공격·인증 성능을 입증하는 실험은 아니다.

## 고정 입력과 모델

실제 FFV1 source32개, 가림후보8개, H.2648개를 모두 처리한다. 총48영상×25프레임=1200개 이미지 입력이다. 이를1200회 CNN forward나 독립1200시행으로 부르지 않는다. B/C/U에는 최종영상이 없으며 합성해서 채우지 않는다. 같은 A의 source/후보/final을 대응시키고, 나머지24 source는 자체 진단으로 구분한다.

설치된 MediaPipe0.10.14·기존26pin CPU 환경·full hand/palm/graph/handedness 자산과 기존 ASCII 리소스 cache를 사용한다. 이미 자산 존재·fingerprint·ASCII 상대경로를 확인했으며 새 다운로드/설치·Cloud 전송은 없다. 각 영상은 새 worker/Hands graph로 시작하고 기존 offline stage1의 `static_image_mode=False`, `max_num_hands=1`, `model_complexity=1`, detection/tracking confidence 각.5를 고정한다. Python profile은 브라우저 prod의.35/.4와 다르며 브라우저 검출기와의 동등성을 주장하지 않는다. prod UI/채점 기준은 바꾸지 않는다.

Python graph는 호출마다33333μs를 부여한다. 입력 영상의8FPS PTS는 분석에 보존되지만 graph에 전달되지 않는다. 따라서 실제8FPS 시간축 추적이나 UI/실시간 시스템과 같다고 주장하지 않는다. worker는 영상 픽셀과 confidence/고정 자산 fingerprint만 받는다. 원모델/정답 좌표는 worker가 종료한 뒤 부모의 오차/채점 분석에서만 읽는다. 모델에 생성기 좌표나 보이지 않는 정보를 주지 않는다.

## 원출력·결측·오차·점수

기존 stage1의25프레임 실제 출력, image/world 좌표와 raw handedness 분류/score를 private에 보존한다. predicted image/world landmark가 함께 있어야 stage1의 detected=True이며, 미검출 프레임을 삭제하거나 좌표0으로 채우지 않는다. 프레임ID/실제decode PTS·길이/해상도/유한값을 검증한다. world/depth의 metric 정확도와 handedness 정답은 평가하지 않는다.

known 생성모델의21점 투영과 2D pixel오차, target middle PIP오차, 참조 wrist–middle MCP길이로 나눈 오차를 계산한다. 이는 독립 사람 주석이 아니고 모델 관절/표면tip의 의미 차이·self-occlusion도 남는다. 오차는 검출된 프레임에 조건부이며 검출/미검출 분모와 함께 보고한다. 검출0의 오차는 null이고0으로 쓰지 않는다. 참조길이 퇴화는 normalized오차 결측으로 별도 센다.

원좌표와 실제 검출열을 고정 prod JS 함수로48×2구간=96개 진단한다. `.25` 점수와38도 keyframe 조건, 누락/segment효과를 따로 보고200ms hold·UI·최종 인증으로 승격하지 않는다. source_info→video_info와 x/width,y/height 변환은 명시하고 mirror=false로 유지한다. 현재 자료에 맞춰 가중치/기준을 보정하지 않는다.

## 시간·기록·실패

예산은 전체600초·영상 worker별90초다. worker 실제 command/request/stdout/stderr·원출력, runtime/resource 준비와 batch decode/모델 setup/process/close의 wall·자체CPU를 영상별로 보존한다. 부모 subprocess wall은 Python 시작·JSON저장/종료를 포함하며 worker 자체CPU는 worker에서 직접 측정한다. frame journal은 batch 반환 후 분모를 계수하므로 per-frame latency 이벤트로 해석하지 않는다. Node 자식 CPU는 미측정이다.

고정 실행 순서와 새 worker/graph, warm resource/통제되지 않은 OS·import cache를 명시하고 일반 cold/warm 또는 온라인 지연으로 부르지 않는다. 기존 영상 생성 시간48행과 새 추론 시간표를 분리한다. 오류/timeout/미검출도 기록하고 성공 수를 채우는 재시도·confidence 변경은 하지 않는다.

코드·명세·전체 worktree·모델/리소스/환경·모든 영상/reference와 완료 receipt를 사전 snapshot에 연결하고 새 immutable 출력/기록 root를 쓴다. 실행 중 코드/문서/커밋을 변경하지 않는다. 비공개 영구보관·모델/좌표/원자료/개별hash의 비공개와 연구 격리를 유지한다. TF-05 실제 사람·독립평가·운영/보안·생체/물리 검증과 다른 모델의 미확보 자산은 별도로 남는다.
