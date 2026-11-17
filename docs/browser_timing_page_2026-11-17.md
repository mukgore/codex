# R8 선택적 브라우저 시간 기록 페이지 — 2026-11-17

기존 G4 페이지의 fetch 본문 수신 이후에 남았던 **브라우저 내 이벤트/영상 callback/시험 동작 응답**의 기록 경로를 준비했다. root prod는 변경하지 않았다. 기본 G4 페이지도 그대로이며 `create_server(..., timing_page=True)` 또는 서버 CLI의 `--timing-page`를 선택해야 새 페이지가 나온다.

[페이지](../g4_lab/timing_page.html) · [페이지 동작](../g4_lab/timing_app.js) · [clock/callback 라이브러리](../g4_lab/browser_timing.js) · [Node 계약 검사](../tests/browser_timing.test.cjs) · [Python/HTTP 연결 검사](../tests/test_browser_timing.py).

## 기록하는 것

새 문제·submit·consume의 request/JSON response 시각을 같은 document의 `performance.now()`로 남기고 각 요청에 opaque correlation ID를 넣는다. document ID/attempt index/event ID로 구분하며 다른 timeline에서 가져온 event로 elapsed를 계산하지 않는다. clock regression·잘못된 이름/metadata를 거부한다. server raw와의 연결은 ID로 해야 하며 browser/server 원시 clock을 서로 빼지 않는다.

새 media source를 넣기 전에 `requestVideoFrameCallback`을 등록한다. callback now·관측 시각·presentationTime/expectedDisplayTime·mediaTime·크기/presentedFrames와 선택적 processingDuration을 기록한다. [WICG 원명세](https://wicg.github.io/video-rvfc/)에서 presentationTime은 합성 제출 시각이고 expectedDisplayTime은 예상 표시 시각이다. callback이 늦을 수 있어 expectedDisplayTime이 callback now보다 작다는 이유만으로 버리지 않는다. processingDuration이 없으면 null이다. 이 명세는 Community Group draft이며 W3C 표준으로 부르지 않는다.

callback 상태는 PENDING/OBSERVED/UNAVAILABLE/TIMEOUT/ABORTED/ERROR를 구분한다. 미지원·timeout을 loadeddata나 임의 timer 시각으로 대체하지 않는다. timeout/취소 때 callback 취소를 요청하고 늦은 callback은 이미 정한 결과를 바꾸지 않는다. 새 문제를 받으면 이전 media/observer를 정리하고 이전 grant도 비운다. 잘못된 JSON을 다시 넣어도 이전 grant가 남지 않는다.

단위는 native API 그대로다. callback/observation/presentationTime/expectedDisplayTime과 event `at_ms`는 browser performance 기준 ms, mediaTime은 media PTS 초, processingDuration은 decoder pipeline의 초다. width/height는 CSS pixel이 아닌 media pixel이며 presentedFrames는 frame count다. 서로 다른 단위의 metadata를 합산하지 않는다.

첫 action JSON response까지의 elapsed와 실제 `protected_action_allowed`를 따로 저장하고, 반복 consume도 남긴다. 요청별 HTTP 상태와 반복 평가 이력을 보존한다. 원문 replay 배열·cookie·challenge/grant ID는 내려받는 시간 JSON에 넣지 않는다. 원clock·correlation과 세부 점수는 private 기록이므로 결과 파일은 `browser_timing.private.json`으로 로컬 다운로드한다. 외부 업로드/카메라 코드는 없다. browser가 보고한 telemetry 자체는 조작할 수 있어 입력 출처/사람 존재의 인증으로 쓰지 않는다.

## 사용 범위와 검산

```powershell
python -m g4_lab.server --source-root ../handcaptcha-ui-20261113 --timing-page
```

이는 새 연구 서버를 수동으로 시작하는 명령이며 이번에 실행한 브라우저 실험의 명령이 아니다. CLI flag는 client 기록 페이지를 고르는 기능이다. server `ServerTiming` 파일과 결합한 측정은 별도 실행기에서 `create_server(service, timing=recorder, timing_page=True)`로 연결하고 사전등록/새 output·record/config를 갖춰야 한다.

Node의 fake video/clock/DOM/fetch를 이용한9개 계약 검사는 cross-document/clock regression, 늦은 callback, API 미지원, timeout/late callback, abort, invalid metadata/오류, 이전 grant 정리, 거부 결과와 private export의 요청 상태/평가 이력 보존을 다룬다. Python은 그 Node 검사를1개 entry로 실행하고 별도1검사에서 실제 loopback HTTP의 기본/선택 자산과 cache policy를 확인한다. 기존 계측/서버24검사와 합해26개 Python 검사를 통과했다. 합성 입력이며 실제 browser engine이나 video 표시의 검증이 아니다.

실제 브라우저 표시는 아직 측정하지 않았다. 설치된 Chrome/Edge의 존재와 Playwright 미설치만 확인했고 설치/실행/사용자 앱 조작은 하지 않았다. 실제 browser callback이 관측되더라도 물리 화면/사용자 인지·카메라/실제 hold/인증을 증명하지 않으므로 `physical_display_proven=false`를 유지한다. 향후 headless 측정은 화면을 표시하지 않는 별도 조건으로 기록하고 headed/physical display와 합치지 않는다. 기존 R8 localhost 측정이나 R9 재구성은 반복하지 않았다.

## 앞 단계 입력 재확인

[지정 입력 metadata 확인](../reports/priority_input_gates_20261117.json): 등록 촬영21행의 source_path0, 응답 관측 필드0, 독립 주석2양식의 좌표 scalar 기입0이다. 지정 model_inputs layout의 HaMeR3개/Text2HOI10개가 미확보이며, 별도 MANO intake 좌우 파일은 보존돼 있다. layout 부족을 PC 전체/모든 model 자산의 부재로 확대하지 않는다. 이번 확인은 읽기 전용 경로/양식 점검이며 모델 import/역직렬화/새 추론은 하지 않았다.

전체62ID·3D44표행·R0–R9·실제 촬영/선별/대응/독립평가 우선과 root prod/기존 실행·원자료 불변/영구 비공개/Cloud보류를 유지한다. R8/R9 전체 인수와 실제 사람/강한 모델/운영 검증은 계속 미완료다.

최종 전체 검사는 `Ran 384, OK (skipped=1)`로 종료했다. skip1은 기본 환경에 mpmath가 없는 optional SDK box 모듈이며 기존 SDK 환경의 별도16검사 통과 기록을 유지한다. 이번에 SDK/모델/브라우저 환경을 설치·변경하지 않았다.
