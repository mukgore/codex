# 구현 진행·검증 기록 — 2026-11-03

> 이 문서는 최초 전달 세션의 구현·제약 기록이다. 이후 별도 작업본의 Git 적용 검사와 커밋 준비 결과는 [전달본 반영 기록](deliveries/2026-11-03_review.md)에 있다. 이전 세션의 업로드 실패를 현재 반영 상태와 혼동하지 않는다.

## 결과

`codex/main 6cfe1b1`을 기준으로 별도 작업 브랜치를 만들었다. 통합 할 일, 41개 원문 문서의 목차 색인, 실험 카드 3개, 설명·발표 초안, 기존/후보 score 비교 CLI와 테스트, handcaptcha 적용 대기 패치를 추가했다. 과거 G3·A/B 현재 범위 수용 상태는 유지했다. 기존 PR #1/#2와 추가 브랜치의 독자 내용을 작업 목록에 연결했다.

handcaptcha 브랜치 생성은 연결 권한 제한(403 `Resource not accessible by integration`)으로 실패했다. 따라서 handcaptcha main 반영·PR 생성·배포는 하지 못했다. 수정안은 codex `patches/`에 보존했다. 기존 prod HTML/수집·채점 흐름은 수정하지 않았다.

**최종 원격 상태:** codex의 `work/todo-consolidation-20261103` 브랜치 생성만 성공했다. 뒤이은 GitHub 파일 쓰기(create_tree)는 도구의 승인 필요/승인 정책 never 제한으로 실행이 차단됐다. 따라서 이 변경은 GitHub에 업로드되지 않았고 PR도 생성하지 못했다. 파일 쓰기 요청을 다른 경로로 우회하지 않고, 두 저장소 패치·변경 파일·검증 기록을 로컬 전달 ZIP에 보존했다.

## 실제 검증한 항목

| 묶음 | 실행/검사 | 결과 |
|---|---|---|
| codex 기존 수학 primitive | `python -m unittest discover -s tests -p test_standard_metrics.py -v` | 12/12 통과 |
| 새 score 비교 도구 | `python -m unittest discover -s tests -p test_compare_scores.py -v` | 7/7 통과. 모든 source 구성요소/participant/capture 누출, test 튜닝 방지, 오류·중단 분모, 집계 비식별, CLI 출력·덮어쓰기 거부 |
| handcaptcha 기존 함수형 검사 | 기존 geometry/Stage3/Stage5/Stage7의 무인자 test 함수를 `unittest.FunctionTestCase`로 실행 | 17/17 통과 |
| handcaptcha mask 검사 | `python -m unittest dataset_pipeline.tests.test_mask_delivery dataset_pipeline.tests.test_mask_integrity -v` | 9/9 통과. 합성 3-frame MP4, 누락·배열 불일치·출력 보존·재디코딩 내부 오류·동시 게시 반례 |
| 손 선택·시연 | `node --test experiments/hand_selection/selection.test.cjs experiments/hand_selection/demo.test.cjs` | 13/13 통과. 순서/크기/교차/소실/재선택/배열 재사용, 원본 검출 입력, 중첩 표시, stop/cleanup |
| 기준 소스 | 다운로드한 관련 handcaptcha 소스 25개를 Git blob SHA-1과 대조 | 전부 b4d96d1 기준과 일치 |
| 패치 round-trip | 기준→14개 변경 파일의 diff 생성, 독립 exact-context 파서로 hunk 길이·문맥·삭제행 검증 및 전체 재구성 비교 | 14/14 작업본과 일치. Git 실행 검사는 아님 |

실행 합계 **58개 검사 통과**. 동일 테스트 반복 호출은 합계에 더하지 않았다. 환경은 Python 3.10.3, NumPy 2.2.6, OpenCV 5.0.0, Node v24.18.0이다. 합성 좌표/합성 비디오를 사용했으며 신규 참여자 영상·개인 좌표·비밀 답은 Git에 포함하지 않았다.

## 도구·환경 제한과 실패 처리

- 작업 폴더의 OS 접근 거부로 기존 로컬 checkout은 열거나 수정하지 못했다. 허용된 임시 폴더에서 GitHub 기준 소스를 읽어 별도 작업본을 만들었다. 기존 사용자 변경과 충돌하지 않았다.
- 기본 환경에 SciPy와 완비된 pytest 의존성이 없어 전체 `unittest discover -s tests`에서 기존 `test_calculations`의 import가 실패했다. 의존성 설치 시도는 다운로드 진행이 멈춰 종료했다. 관련 없는 audit 코드를 고치거나 이 4개 검사를 통과했다고 보고하지 않는다. 이번 변경과 관련된 수학 12개·새 CLI 7개를 별도로 실행했다.
- handcaptcha의 기존 17개 함수형 검사는 pytest를 가장하거나 테스트를 생략하지 않고 각 함수를 `FunctionTestCase`로 실제 실행했다. 새 mask 검사는 unittest다. 보통의 완비된 개발 환경에서는 `python -m pytest dataset_pipeline/tests -q`로 재확인할 수 있다.
- Git 실행 파일이 제공되지 않아 `git apply --check`/`git diff --check`를 실행하지 못했다. diff round-trip과 선별 파일의 링크·공개범위·추가행 공백을 검사했다. 권한 있는 checkout에서는 적용 전에 Git의 정식 검사도 수행해야 한다.
- Computer Use inventory가 브라우저 접근 호스트 및 native pipe 연결 실패, 사용 가능 브라우저 0개를 반환했다. 화면 캡처·실제 카메라·기기 레이아웃 검증은 미실행이다. Node DOM/canvas 대역 검사를 실제 브라우저 사용성 시험으로 표현하지 않는다.

## 보존한 한계

가림 내부의 검은 픽셀 확인은 정해진 raster 원 내부 검사다. 손 해부학적 부위 전체를 가렸다는 근거, codec 경계 누출 부재, PTS/VFR 일치, 운영 release gate나 공격 저항은 아니다. mask 누락 시 이전 좌표를 재사용하지 않지만 필터/역재생을 지원하는 타임라인 재매핑도 구현하지 않았다.

손 선택은 위치·크기·형태 연속성 휴리스틱이며 소유자 식별이 아니다. 빠른 움직임/미검출·교차·화면 밖 손에서 중단될 수 있다. 기본값은 검증되지 않은 공학 설정이다. 별도 시연은 기존 prod의 관문·제한시간·채점·기록과 연결하지 않았다.

비교 CLI는 두 점수를 이미 가진 private trial 표를 받는다. 실제 raw coordinate→후보 feature/score adapter, 공격군별 결과, 군집 CI, 독립 source 검증, 사람·공격 성능 결과는 만들지 않았다. source/participant/capture ID가 제공됐다는 것만으로 계보가 입증되지는 않는다.

다음 작업과 필요한 입력은 [통합 목록](backlog_2026-11-03.md), 실행 준비는 [실험 카드](experiment_cards_2026-11-03.md), 패치 사용은 [적용 안내](../patches/README.md)에 있다.
