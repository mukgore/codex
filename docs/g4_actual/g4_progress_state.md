# G4 실제 코드 실행 상태 — 2026-10-28

상태: 승인된 로컬 탐색·구현·검산을 완료했다. G4의 확증적 일반화·사람 사용성·운영 인증 보안은 미완료다. G3는 종료 상태를 유지한다.

## 실행 기준 및 보존

- codex 최신 원격 main: `76bd22d406f1e1d8efba54207dcb27094522755a`.
- 원래 checkout: `ca00cf7fc9deb57f105ad592343d18483ccd7d6c`, 원격보다 28개 뒤, 분기 없음(0 ahead / 28 behind). 기존 준비 감사 문서 1개 미추적 상태를 보존했다.
- 신규 격리 worktree: 위 최신 main의 detached HEAD. 기존 브랜치에 pull/merge/reset/checkout을 수행하지 않았다.
- handcaptcha 별도 소스 사본: `b4d96d1e84324edd5376f9258f9863a0b6282a5a`, 작업 트리 변경 없음. 기존 로컬 후보 HTML과 전체 내용은 다르지만 `pp`부터 `computeScores`까지 metrics 구간은 동일하다. 과거 수집 빌드라는 주장은 하지 않는다.
- 이전 합성 protocol_guard.py/test_protocol_guard.py가 실제 존재하고 test 메서드 14개임을 확인했다. 이전 테스트와 G3 분석은 다시 실행하지 않았다.
- 새 코드와 비식별 집계만 이 worktree에 추가했다. 입력/행별 결과/코드 지문은 Git 제외 data/에 있다. 실험 실행 중에는 commit/push, 유료 API, GPU, 외부 인증 접속, 원본 수정을 하지 않았다. 실험 종료 후 사용자가 GitHub commit/push를 별도로 승인했으며, 공개 범위는 코드·문서·비식별 집계다.

## 완료 및 제약

| 작업 | 상태 | 근거 |
|---|---|---|
| 최신 원격 및 안전한 실행 기준 확보 | 완료 | 별도 worktree/소스 사본, 원본 상태 보존 |
| 실제 HTML 점수·관문 함수 연결 | 완료 — 오프라인 범위 | 실제 함수 본문 brace 추출 + Node VM 호출. 페이지 시작/카메라/업로드 미실행 |
| A1 및 라이브러리 오답 실험 | 완료 — 탐색 | 136개 개발 응답 + 별도 blind uniform 8개 + pool 밖 legacy 24개 보충 검사 |
| A2 실제 영상 채널 조사 | 완료 — closed-set | 8개 MP4 전체 decode, frame-count, 240개 circle 후보, circle lookup |
| A3 저장 reference 재구성 | 완료 — 알려진 풀 | 공개 기준 궤적/예측 library를 실제 채점 함수로 평가. 기존 HaMeR/MediaPipe 결과는 신규 결과로 재집계하지 않음 |
| A4 실제 계산과 로컬 서버 연결 | 완료 — 신규 시험 서버 | localhost HTTP, 세션/만료/일회성 grant 및 보호 counter |
| 방어 통합 및 반례 | 완료 — 제한된 구현 | 서버 재계산/입력 검증/엄격 mask wrapper. stationary 후보는 반례로 폐기 |
| 별도 계산 및 코드 검토 | 완료 | Python 검산 136+8+24개, 별도 검토자 반례, 16개 최종 회귀 통과 |
| 새 source/사람/실제 카메라 일반화 | 자료·도구 부족 | 미사용 source-family holdout 및 대응 인간 자료 없음. 현재 CUA browser inventory 0, Node Playwright/Playwright-core/Puppeteer 없음 |
| 과거 시스템 L3/제품화 보안 | 미확인 | 기존 보호 endpoint 근거 없음. 신규 loopback 결과로 소급 주장하지 않음 |

실행 ID: `G4-ACTUAL-001`, `G4-BLIND-001`, `G4-MEDIA-CACHE-001/002`, `G4-REGRESSION-001`. Circle/metadata 및 Stage6 fault-injection은 별도 집계 파일로 보존했다. 주 실험의 Git 소유권 오류는 모든 결과 저장 후 manifest 작성에서만 발생했다. 저장된 결과를 재실행하지 않고 command-scoped safe.directory로 누락 manifest만 완성했다. 코드 지문은 실행 후 snapshot이며 사전 잠금 증거가 아니다.

추가 자료 점검에서 공개 legacy landmark 기준 6건과 대응 이전 영상 18개를 확인했다. 현재 manifest의 8개에는 포함되지 않는다. 독립성/과거 calibration 사용 계보가 확인되지 않아 holdout으로 승격하지 않고, `G4-LEGACY-SUPPLEMENT-001`에서 24개 입력의 현재 산식 동작만 보충 검사했다.

현재 풀에 대한 정해진 공격 목록, 반례 및 기계적 방어 검사는 마쳤다. 같은 8개 결과를 보고 임계값을 조정하는 작업은 확증 효과를 만들지 못한다. 다음 성능 판단에는 미사용 source와 입력 출처를 검증할 환경, 대응 정상 자료 및 연구자 정의의 성공 기준이 필요하다. 전체 G4 완료로 처리하지 않는다.
