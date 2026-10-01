# 진행 상태

- 범위: 1차 결과 재현·검증·보완 실험 계획. 후속 구현 승인 없음.
- 원본: ../CAPTCHA. 직접 수정하지 않음. data/raw 스냅샷과 data/inventory.json 생성 완료. 안전 종료 직전 원본과 스냅샷 전체 해시 재검증 통과.
- 지정 원격: https://github.com/mukgore/codex.git. 기존 main 이력 보존. 공개 저장소임을 확인했고 사용자가 공개 사용으로 변경 승인함. 선별한 코드·문서·집계만 푸시한다.
- 조사: 원자료 164개(숨김 desktop.ini 포함), 157382505바이트. 상위 및 자료 하위 AGENTS.md 없음. Python 3.10 설치 확인, 기본 PATH에는 없음. gh 없음. 로컬 스냅샷 전체 해시 검증 완료.
- 완료: 보고서 로컬 텍스트 추출, 사람 18명·HaMeR 28조합 저장 오차→점수 재계산, SUS 10명/21명 및 α 재현, 결측·시간 기초 감사, 기존 공격 저장 관측→매칭→좌표 채점 재실행.
- 검증: 계산 회귀 검사 4개 통과. reports/phase1_aggregates.json과 analysis/audit.py 일치. 공격 재실행 기존 결과와 일치.
- 상태: 사용자 요청에 따라 안전 종료. 1차 검토 문서·주장 근거표·보완 실험 카드는 미완료. HANDOFF.md 참고.
- Git: 초기 설정 커밋 26c792b는 푸시 완료. 이번 안전 종료 WIP는 로컬 커밋만 하며 푸시하지 않는다.
- 다음 명령(저장소 루트 PowerShell): `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
