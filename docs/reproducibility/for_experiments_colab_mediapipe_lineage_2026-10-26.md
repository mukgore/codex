# FOR_EXPERIMENTS의 Colab·MediaPipe 계보 확인 — 2026-10-26

## 연구자 기억과 대조한 내용

연구자는 이 자료를 사람 대상 실험에 사용하지 않고 후속 실험용으로 남겼을 가능성이 높으며, 공격 관련 MediaPipe 실행은 Colab에서 했을 수 있다고 설명했다. 승인된 로컬 코드와 산출물 스키마를 읽기 전용으로 대조했다.

## 확인된 코드·산출물 관계

- 다운로드 자료의 Colab 자동 생성 `handtest1.py`는 MediaPipe 0.10.14 설치를 지정하고, 업로드된 MP4를 입력으로 받는다.
- 코드는 기준 영상과 가림 단계별 영상을 MediaPipe로 추적한 뒤 landmark 오차·검출/정확도·jitter 및 pause-point 값을 계산한다.
- `FOR_EXPERIMENTS`의 4개 그룹에는 그룹별 MP4 4개와 JSON 2개가 있다. tracking JSON의 `frames`, `segmentation`, `video_info` 구조와 다른 JSON의 `baseline_jitter`, `levels` 구조는 Colab 코드가 저장하는 결과 형식과 부합한다.
- 각 그룹의 tracking JSON은 landmark 좌표가 있는 합계 434 frame records를 보유한다. 이는 이미 처리된 MediaPipe 결과 자료가 있음을 보여준다.
- 별도 `ingest_experiment_folders.py`는 Colab 형식의 실험 폴더를 pool manifest로 가져오는 기능을 설명한다. 그러나 이 스크립트가 실제로 실행됐다는 기록이나 `FOR_EXPERIMENTS` 영상이 현재 pool에 들어갔다는 직접 연결은 발견하지 못했다.

## 판정

- **강하게 지지됨:** 이 자료 묶음은 Colab 기반 MediaPipe 가림/추적 품질 실험의 입력·산출물 형식과 부합한다. 사람 대상 CAPTCHA 세션 JSON은 아니며, 연구자의 기억과도 일치한다.
- **확인됨:** `model_test_results.json`은 세 가림 단계별 static/dynamic accuracy, pause-point accuracy, jitter 계열 결과를 저장한다.
- **미확인:** 이 결과가 실제 CAPTCHA 공격의 성공 여부, production gate 통과, production score 통과 또는 end-to-end 인증을 평가한 것인지는 확인되지 않았다. 산출물의 지표는 landmark 추적 품질을 기술하며 CAPTCHA 인증 결과와 다르다.
- **미확인:** Colab에서 실제 실행된 노트북 revision, 실행 날짜, 업로드한 원본 파일과 각 저장 결과의 세션별 연결은 남아 있지 않다.
- **미확인:** 이 자료가 현재 G4 attack reference library 또는 점수·threshold 조정에 쓰였는지. 파일이 독립적으로 남아 있거나 기존 공격 MP4와 byte-identical하지 않다는 사실만으로 미사용을 증명할 수 없다.

## 다음 데이터 활용 원칙

연구자 설명에 따라 이 자료는 사람 실험 자료로 세지 않는다. MediaPipe occlusion robustness의 기존 산출물로는 코드·지표 정의를 대조할 수 있다. CAPTCHA 공격의 독립 holdout으로 쓰려면 원본 gesture/source family가 공격 reference·개발에 포함되지 않았다는 계보와, 별도 CAPTCHA challenge·gate/score endpoint 연결이 필요하다. 그 증거 전에는 holdout 또는 공격 성공 자료로 보고하지 않는다.

원자료, 참가자 정보, 영상명, 로컬 경로 및 해시는 공개하지 않았다.
