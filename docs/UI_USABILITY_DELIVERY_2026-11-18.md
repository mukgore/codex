# 2026-11-18 prod 사용성 첫 실행본

최우선 범위는 `UI_USABILITY_HANDOFF_2026-11-18.md`와 사용자의 이번 명시 지시다. 다른 연구 백로그를 진행하지 않았다. 다음 작업은 사용자가 이 실행본을 확인한 뒤 제공하는 피드백의 수정이다.

## 작업 공간과 기준

원격 `work/todo-consolidation-20261103`을 fetch해 확인했다. 기존 `deliverables-review/codex`, `deliverables-review/handcaptcha`는 미커밋 변경이 없었지만 원격 브랜치와 이력이 갈라져 있어 reset/rebase/merge 없이 보존했다. 별도 worktree:

- `C:\Users\조영준!\Documents\CLI\usability\codex`: 기준 `ddab37f`, 작업 브랜치 `work/ui-usability-20261118`.
- `C:\Users\조영준!\Documents\CLI\usability\handcaptcha`: 기준 `e03bcfa602500ce7346169181a2344999a07c3d5`, 같은 이름 작업 브랜치.

각 checkout에 적용할 AGENTS.md는 없었다. 기존 저장소/운영 prod를 덮어쓰지 않았으며 원격 push·배포·모집은 하지 않았다.

## 전달물

단일 실행본 `handcaptcha/experiments/prod_usability/index.html`, 상세 명령·설정·5분 점검표는 같은 폴더 `README.md`, 기준 commit·파일 SHA-256은 `baseline.json`, 검증 기록은 `VALIDATION.md`다.

```powershell
Set-Location -LiteralPath 'C:\Users\조영준!\Documents\CLI\usability\handcaptcha'
node .\experiments\prod_usability\server.cjs 8770
```

http://127.0.0.1:8770/experiments/prod_usability/

목표 가림 영상과 카메라를 단일 화면에 contain 합성한다. 목표 기본 투명도 42%, 조절 20–65%. 원본 카메라만 추론기에 전송한다. 기존 점수 함수·가중치·관문 기준·문제 내용은 고정했다. 결과 화면에 JSON 저장 버튼을 추가하고 3초 자동 재시작은 제거해 결과를 읽고 보관할 수 있게 했다. 기존 업로드 URL은 빈 값이다.

다중 검출은 최대 4손이며, 유효 landmark와 정규화 bbox 면적 3.5% 이상 중 큰 손을 350ms 안정화해 선택한다. 선택 후 위치·면적·형태 연속성을 사용하고 반환 인덱스나 좌우손 라벨로 추적하지 않는다. 유지 면적은 2.4%, 유사 크기는 1.12배 이내 대기, 누락 유예는 1500ms다. 기준은 임시 개발값이다. 실거리·신원 확인이 아니며 자세에 따라 면적이 변한다.

선택 손만 기존 관문·수행 기록·채점·저장 경로에 전달한다. 짧은 누락은 null이고 hold를 초기화한다. 1.5초 손 이탈 또는 교차 모호성에는 현재 시도를 폐기하고 기록/관문/좌우손 버퍼를 초기화한 뒤 카메라·모델을 유지하며 자동으로 손 선택 대기로 돌아간다. 재시작 안내를 표시하고 손이 다시 안정 선택되면 새 문제를 시작한다. 비동기 문제 로딩/재생/결과 콜백도 이전 시도를 재개하지 않게 가드했다. 오류 발생 시 수동 재시작 버튼도 유지한다.

## 사용자 점검과 이후

혼자 손을 넣어 따라 하기 → 다른 손을 함께 넣어 선택 확인 → 선택 손을 빼고 다시 넣어 재시작 확인. 실제 사람의 카메라 손 선택과 중첩 가독성은 사용자 확인 대기다. 합성 좌표 검사는 사람 테스트가 아니다. 다음 수정은 사용자가 가장 불편했던 장면 한 가지에 맞춰 이 같은 폴더에서 진행한다.

## 사용자 피드백 v2 및 버전 저장

다음 영상이 디코딩/seek 완료될 때까지 이전 가림 프레임을 유지한다. 손 이탈은 1.5초 후 안내와 함께 자동 재시작한다. 첫 전달 버전은 handcaptcha 로컬 Git 태그 `usability-v1-20261118` 및 `usability/backups/prod_usability_v1_20261118.zip`에 보존했다. 이번 반영본은 `usability-v2-20261118` 태그로 저장한다. 원격 push/배포는 하지 않는다.
