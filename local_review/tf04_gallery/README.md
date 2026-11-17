# TF-04 실제 결과 로컬 갤러리

모델·렌더·실험을 재실행하지 않고 보존된48영상과 기록을 본다. UI는 기존 prod 기반 비교본을 사용한다. 외부 배포·업로드·패키지 설치는 없다.

2026-11-18 준비본:

- 갤러리: http://127.0.0.1:49677/
- 기준/전체켬 나란히: http://127.0.0.1:52999/experiments/local_review_20261118/
- 기존 스위치 화면: http://127.0.0.1:52999/experiments/prod_ui_factorial/
- 원영상: `../../../private_artifacts/tf4d_20261116_v1` (저장소 기준으로는 `../private_artifacts/tf4d_20261116_v1`).
- 보기용 metadata/사본: `../private_artifacts/tf04_viewer_20261118_v2/`, MP4는 그 안 `viewing_mp4/`.
- 원래 기록: `../private_artifacts/tf04_display_record_20261116_v1/`.

서버는 현재 사용자 열람을 위해 유지한다. 닫혔다면 저장소 루트에서 각 명령을 별도 터미널로 실행한다. 지정 포트가 이미 사용 중이면 다른 서버를 종료하지 말고 `--port 0`으로 새 주소를 받는다. 포트가 바뀌면 private manifest의 `ui_url`도 해당 실제 UI 주소에 맞춰 사용해야 한다.

```powershell
# handcaptcha-ui-20261113 루트에서 기존 서버
& '..\..\hand-captcha-research\.venv\Scripts\python.exe' -m experiments.preview_server --port 52999

# codex-research-20261110 루트에서 갤러리
& '..\..\hand-captcha-research\.venv\Scripts\python.exe' -m local_review.tf04_gallery.server --viewer ../private_artifacts/tf04_viewer_20261118_v2 --port 49677
```

`prepare.py`는 새 별도 private 폴더만 허용한다. 재사용할 보기용 사본이 이미 있으므로 열람 때 다시 실행할 필요가 없다. v1은 Python3.10에 없는 hash API 때문에 변환 전에 중단됐고 빈 준비 폴더를 보존했다. v2에서 Python3.10 호환 hashing으로 정정했다. 실험 기록이 아닌 열람 준비의 실패이며 원본은 그대로다.

## 읽는 방법

갤러리 첫 줄은 같은 손·seed·시점의 A/B/C 무가림 비교다. B는 정적 자세이므로 움직이지 않는 것이 정상이다. U는 수정 전 정적 대조로 전체48개 목록에 있다. 다음 줄은 같은 A의 무가림/후보/최종 비교다. B/C/U의 후보·최종은 만들지 않았으므로 목록에서도 없는 것으로 표시한다.

무가림32개는 FFV1 AVI, 후보8개는 MPEG-4 Part2 mp4v라 일반 브라우저 호환용 H.264/yuv420p MP4 사본을 만들었다. 이미 H.264인 최종8개는 원본 직접 재생이다. 사본은 손실 압축이며25프레임/8FPS/512×420/3.125초를 유지한다. 새 연구 입력·재계산 결과로 취급하지 않는다. 원경로·원본hash·사본hash·변환 명령은 private manifest/log에 남겼다.

UI 나란히 비교는 기존 `prod_ui_factorial/run.html?preview=1&condition=0`과`63`을 직접 iframe으로 사용한다. 예시 그림만 나타나고 카메라/모델은 시작하지 않는다. 오른쪽의6스위치는 기존 조건 bit를 그대로 쓴다. 시간 버튼은 예시의 초기 힌트/페이드를 같은 시점으로 정지한다. 실제 카메라 진입 링크는 별도 파일 선택 화면이며 사용자가 자료를 넣고 시작해야 한다. 원래 실제 실행은 unpkg MediaPipe 웹 자산을 읽으므로 완전 오프라인 실행과 구분한다. 이번 열람에서 외부 라이브러리를 내려받거나 카메라를 시작하지 않았다.

## 확인 범위

원래 실행 receipt의361산출물과 원영상48개를 전후 검산했다. 48개 미디어의 HEAD/byte-range(206)/poster, metadata·기록 링크, 경로/Host 제한, 기존 UI/새 비교 페이지 HTTP 응답과 두 JS 구문 검사를 통과했다. 서버는127.0.0.1에만 bind하고 갤러리는 manifest에 등록된48개 파일·poster와 지정 기록만 제공한다. 임의 private 폴더 조회는 없다. prod hash는 기존`0d82dd439fe7976f8b860eb82e654e6f5637b2d7a3fcce2d02f2f99e5f5bea11`과 같다.

기본 브라우저로 세 URL을 여는 OS 요청은 성공했다. 브라우저 host와 native pipe가 이용 불가하여 실제 화면 렌더/재생을 자동 조작으로 확인하지는 못했다. 대표 A/B/C의 기존 source preview 이미지는 직접 확인했다. 카메라·사람/운영·인증 실험 결과나 최종 채택 주장을 추가하지 않는다.
