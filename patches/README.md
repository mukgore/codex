# handcaptcha 전달 패치 보관본

`handcaptcha_todo_2026-11-03.patch`는 **mukgore/handcaptcha main b4d96d1e84324edd5376f9258f9863a0b6282a5a** 기준이다. 최초 전달 세션에서 해당 저장소 브랜치 생성이 403으로 거절되어 보존한 패치다. 이후 별도 작업본 적용·검사와 작업 브랜치 커밋은 [반영 기록](../docs/deliveries/2026-11-03_review.md)을 따른다. 작업 브랜치 커밋은 main 적용·운영 배포를 뜻하지 않는다. 이미 적용한 작업 브랜치에 이 패치를 중복 적용하지 않는다.

최초 전달 세션에서는 codex 파일 쓰기도 도구의 승인 정책으로 차단되어 로컬 전달본에만 있었다. 원격 브랜치 생성은 성공했지만 코드 업로드·PR 생성은 미완이다.

## 포함 내용

- Stage6: 미검출 mask와 잘못된 시간축·frame 수·FPS·치수 거부, 2D 원 계산, 임시 출력, 재디코딩 개수/크기/가림 내부 검사, atomic no-clobber 게시.
- Stage7: 2D 래스터와 기하 판정 일치, 미검출을 전체 분모에 포함.
- `experiments/hand_selection/`: 큰 유효 손 선택·안정화·유지, 모호/소실 시 중단, 분리/중첩 화면·투명도·반전 제어. 검출 입력은 원본 카메라다. 자동 저장/업로드·채점·인증 없음.
- 테스트·시연 안내·ROADMAP/README 연결.

기존 `hand_captcha_prod.html`과 `hand_captcha_prod_modified.html`은 수정하지 않는다. 기존 PR #1의 2026-10-26 mask 패치와 겹치므로 두 패치를 연이어 적용하지 않는다. 그 패치가 이미 적용된 브랜치는 최신 main과 비교해 이식해야 한다.

## 적용

원본 작업을 보존하고, 권한이 있는 handcaptcha checkout의 깨끗한 별도 브랜치에서 실행한다. 최신 main이 위 기준과 달라졌다면 먼저 차이를 확인한다.

```powershell
git switch -c work/hand-selection-mask-review b4d96d1e84324edd5376f9258f9863a0b6282a5a
git apply --check <codex경로>/patches/handcaptcha_todo_2026-11-03.patch
git apply <codex경로>/patches/handcaptcha_todo_2026-11-03.patch
python -m pytest dataset_pipeline/tests -q
node --test experiments/hand_selection/selection.test.cjs experiments/hand_selection/demo.test.cjs
```

경로 자리표시자는 실제 위치로 바꾼다. 테스트 환경에는 기존 MediaPipe/OpenCV/NumPy와 pytest가 필요하다. 이번 실행 환경에 Git/pytest 의존성이 완비되지 않아 `git apply --check` 자체는 실행하지 못했다. 대신 기준 파일의 Git blob SHA를 확인하고, 전체 diff context·hunk 길이·round-trip 결과를 독립 파서로 비교했다. Python 테스트는 unittest 및 기존 17개 무인자 test 함수를 `FunctionTestCase`로 실행했다. 자세한 수와 제한은 [검증 기록](../docs/implementation_progress_2026-11-03.md)에 있다.

## 로컬 시연과 남은 검증

handcaptcha 루트에서 `python -m http.server 8765 --bind 127.0.0.1`을 실행하고 `http://127.0.0.1:8765/experiments/hand_selection/`를 연다. 기존에 가림이 완료된 로컬 MP4/WebM을 선택한 후 화면 조건을 정하고 카메라 시작을 누른다. 브라우저 카메라 허용은 사용자가 수행한다. 시연 후 서버를 종료한다.

브라우저/네이티브 접근 호스트가 이번 세션에서 연결되지 않아 스크린샷·실제 카메라 검증을 수행하지 못했다. Node의 DOM/canvas 대역으로 원본 카메라 검출·중첩 표시 분리, 소실 중단·카메라 정리를 확인했다. 실제 기기·레이아웃·추적 품질·사람 사용성과 prod gate/score 연결은 남은 작업이다.

가림 내부 검사 허용값(30/255)과 경계 2px 제외는 codec 진단용 초기값이다. 해부학적 가림·피부/손끝 단서 누설·PTS/VFR·다른 트랙·poster·권리·공격 저항·release 승인 검사를 대신하지 않는다. 파일시스템이 hard link를 지원하지 않으면 게시를 실패시킨다. 원본과 결과가 1:1 대응하지 않는 변형은 거부한다.
