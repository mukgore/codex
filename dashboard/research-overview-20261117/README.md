# 손동작 CAPTCHA 연구 지도

`dist/index.html`을 브라우저로 열면 된다. 인터넷 연결이나 설치 없이 화면 전환·검색·필터·차트 선택이 동작한다. GitHub 링크를 열 때만 인터넷이 필요하다. 근거 문서 링크도 함께 쓰려면 현재 저장소 폴더 구조를 유지한다.

## 읽는 순서

1. **전체 흐름**: 촬영부터 사용성까지 7단계를 눌러 이미 준비된 것과 필요한 입력을 확인한다.
2. **활동 타임라인**: 19개 전환점으로 흐름을 읽고, 전체 커밋 보기에서 월·저장소·분야·GitHub/로컬을 검색한다.
3. **결과 이해**: 점수→관문→서버 허용→실제 인증을 구분하고 대표 모델/표시 결과의 범위를 확인한다.
4. **남은 일**: 기존 62개 ID를 단계·상태로 찾고 남은 입력과 이전 근거를 함께 읽는다.
5. **GitHub·근거**: 이력 범위·확인 시점·문서 출처를 확인한다.

## 자료 범위

- 기준일: 2026-11-17. 연구 기준 커밋은 codex `9f1a68e`, handcaptcha `9f29ac4`로 고정했다.
- GitHub `main` 이력과 지정 작업 브랜치, 해당 로컬 연구 이력을 저장소+SHA로 중복 제거한 329개 기록이다. 모든 브랜치·PR·사용자 활동 전체를 수집한 통계는 아니다.
- codex 173개 중 로컬 전용 21개, handcaptcha 156개 중 로컬 전용 0개다. GitHub 확인 당시 작업 브랜치 tip은 각각 `68417fc`, `9f29ac4`다.
- 커밋 수는 활동량이며 연구 성과·인증 성공률·전체 완료율이 아니다. 제목 기반 분야 분류는 탐색용이다. 날짜는 한국 시간의 커밋 날짜이며 실험 수집일을 뜻하지 않는다.
- 기존 GitHub 개발과 최근 로컬 연구를 시간·출처로 연결했다. 이력만으로 각 기여자를 판정하지 않는다.
- 공개 집계·문서·정제한 GitHub metadata만 사용한다. 원영상·모델·개인별 좌표·비공개 실행 기록은 읽거나 포함하지 않는다. 외부 서비스 배포나 새 push는 하지 않았다.

자세한 서술은 [활동 정리](../../docs/WORK_SUMMARY_2026-11-17.md), GitHub 근거는 [정제 snapshot](../../reports/dashboard_github_snapshot_20261117.json)을 참조한다.

## 재생성·검사

저장소 루트에서 기존 연구 Python으로 실행한다. 추가 설치는 없다.

```powershell
& '..\..\hand-captcha-research\.venv\Scripts\python.exe' -m analysis.build_research_dashboard
& 'C:\Program Files\nodejs\node.exe' dashboard/research-overview-20261117/check.cjs
```

`template.html`은 화면 소스, `data.json`은 확인 가능한 자료, `dist/index.html`은 자료와 코드를 모두 포함한 최종 파일이다. 재생성에는 원래 두 Git checkout과 현재 공개 집계/문서가 필요하다. 이미 생성된 HTML을 여는 데는 필요하지 않다.

선택적으로 아래 명령으로 로컬 미리보기를 실행할 수 있다. 출력된 `127.0.0.1` 주소를 열고 종료 시 Ctrl+C를 누른다.

```powershell
& '..\..\hand-captcha-research\.venv\Scripts\python.exe' dashboard/research-overview-20261117/serve.py --port 0
```

검증: 5개 화면, 7단계, 10개월 구간, 검색·필터·빈 결과·62개 ID·판정 단계·근거 링크의 Node 실행 검사가 통과했다. HTML 자료와 원본 JSON의 일치 및 로컬 HTTP 응답도 확인했다. 제공된 브라우저 연결 host가 이용 불가하여 실제 브라우저 렌더·모바일 화면은 확인하지 못했다. 이 검사는 새 연구 실험이 아니다.
