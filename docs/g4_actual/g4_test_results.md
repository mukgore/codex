# G4 검사 결과 및 재현 범위

## 새로 실행한 검사

| 검사 | 결과 | 범위 |
|---|---|---|
| 실제 함수 탐색 136개 | 행별 결과/입력/서버 사건 보존 | 현재 8개 source, 개발 입력 |
| 별도 Python 산식/관문 교차검산 | 136/136, score/score-pass/gate 불일치 0; 최대 score 차이 2.22e-16 | JS bridge를 import하지 않는 별도 구현, 허용오차 1e-10 |
| Blind uniform 별도 검산 | 8/8 불일치 0, score 오차 0 | 같은 평가자 코드의 추가 입력, holdout 아님 |
| HTTP 통합 | 9개 통과 | 실제 evaluator + loopback, 세션·변조·만료·일회성·동시성·민감 경로 차단 |
| Mask 회귀 | 7개 통과 | 정상/누락/길이/finite/2D/원본 보존 |
| 최종 통합 회귀 | 16개 통과, 실패·오류·skip 0 | 위 9+7을 하나의 회귀 명령으로 기록, 약 6.39초 |
| 실제 Stage6 fault-injection | 첫 3 actual decoded frames에서 결함/사전 거부 확인 | Capture/Writer는 memory spy, circle rasterizer와 기존 함수 본문은 실제 코드 |
| 신규 서버 cache 경로 | 001 및 randomized 002에서 각각 8/8 식별/score/gate/local action | 두 run을 독립 표본 16개로 합치지 않음 |
| Legacy 기준 보충 | 6개 이전 기준 × 4종 응답 = 24행 | 현재 pool 밖의 공개 개발 자료, local L3 없음 |
| Legacy 별도 Python 검산 | 24/24 불일치 0, 최대 score 오차 7.22e-16 | 독립 구현으로 입력 재구성, holdout 독립성은 아님 |

이전 14개 합성 protocol 테스트는 존재/개수를 확인했으나 다시 실행하거나 위 16개에 더하지 않았다. G3/A·B 원자료도 재계산하지 않았다.

실행 환경: Python 3.10.3, Node v24.18.0, NumPy 2.2.6, 로컬 OpenCV, CPU. 전체 주 비교 136행은 두 서버 조건과 직접 계산을 포함해 약 100.38초였다. 실제 계산 median은 공격군별 약 138–167ms이며 새 VM 생성 비용을 포함한다. Randomized cache run의 median 약 207ms는 이미 기록된 영상을 좌표로 제출한 시간으로, 실제 카메라 수행 시간을 포함하지 않는다. Peak memory와 개발 인건비는 계측하지 않았고, 금전비·배포 처리량으로 환산하지 않았다.

## 저장 및 실행

공개 가능한 집계는 reports/g4_actual, 입력·개별 시도·manifest·검산·회귀 로그는 Git 제외 data/work에 보존했다. Source code fingerprint는 실행 후 기록으로 사전등록 잠금을 대신하지 않는다.

아래 명령은 worktree 루트에서 기존 로컬 venv 또는 동일 의존성의 Python으로 실행한다. 같은 출력 경로를 재사용하지 않는다.

```powershell
python -m g4_lab.run --source-root ../g4-handcaptcha-source --run-id G4-REPRO-NEW --run-dir data/work/g4_repro_new --summary reports/g4_repro_new/summary.json
python -m g4_lab.independent_check --source-root ../g4-handcaptcha-source --run-dir data/work/g4_repro_new
python -m g4_lab.checks --output reports/g4_repro_new/regression.json --log data/work/g4_repro_new/regression.log
python -m g4_lab.media_lookup --source-root ../g4-handcaptcha-source --output reports/g4_repro_new/cache.json --run-id G4-CACHE-REPRO-NEW
```

브라우저/실제 카메라/2-clip UI scheduler/인간 사용성/미사용 source/운영 L3/전체 MP4 출하 검사는 NOT_TESTED다. 이전 CUA 선택 오류를 현재 재현했다고 주장하지 않는다. 이번 최종 inventory에는 browser provider가 0개였고, Node의 Playwright/Playwright-core/Puppeteer도 설치돼 있지 않았다.

근거: [회귀 집계](../../reports/g4_actual/regression_summary.json), [별도 검산 코드](../../g4_lab/independent_check.py), [HTTP 검사](../../g4_lab/test_integration.py), [mask 검사](../../g4_lab/test_masking.py).
