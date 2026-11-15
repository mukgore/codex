# Cloud 시작·호환성 검사 — 2026-11-15 (진행 중)

실제 provider=cloud 호스트에서 실행했다. 로컬 PC/파일 연결은 사용하지 않았다. 기준 원격은 codex `5546f813968c21ded96622ff1305f8ae73ef78a5`, handcaptcha `ebdfcb85d551328bd9e5f1788f921ad630991302`로 인계값과 일치했다. 지정 문서를 순서대로 읽었다. 별도 `work/cloud-validation-20261115`에서 개발하며 PR 대상은 두 저장소의 `work/todo-consolidation-20261103`이다.

## 완료

- Debian 13.6 x86_64, Python 3.12.14, Node 24.22.1, ffmpeg/ffprobe 7.1.5, Chromium 156.0.8078.79 확인. CPU 노출 3이나 cgroup quota는 2 CPU분, RAM 호스트 9.7GiB이나 cgroup 8GiB. 초기 디스크 7.4GiB 여유.
- 분리 research(Python3.12), video(Python3.10.22), ui(Python3.12/websockets16.0) venv 구성. Windows venv/lock은 복사하지 않았다. video는 기존 Windows 입력 pins를 Linux에서 설치한 새 환경이며 검증된 Linux lock으로 간주하지 않는다. 연구·영상 `pip check` 종료0.
- 연구 최초 193검사: 종료1(실패1/오류22). Cloud의 `/workspace/.git`, `/tmp/.git` 빈 read-only 보호 디렉터리 오판; 이후 venv 실행기 심볼릭 링크 거부8개를 구분했다. 호환성 수정 후 195검사 종료0. POSIX timeout/descendant 종료 회귀도 포함한다.
- Node UI 24검사 종료0. pipeline 기준139검사 종료0. 실제 사람/MediaPipe 성능은 측정하지 않았다.
- prod Linux LF sha256 `44c88ec2ede1205684923e4b43cc4a6024e48a364a70518201262cba258be2c8`; CRLF로 계산하면 이전 `0d82dd439fe7976f8b860eb82e654e6f5637b2d7a3fcce2d02f2f99e5f5bea11`과 일치. prod 내용은 수정하지 않았다.

호환성은 정확히 `/workspace`·`/tmp`의 비링크·빈·write bit 없는 `.git` 보호 디렉터리만 예외다. 그 밖의 `.git`(빈 디렉터리/파일/링크 포함), 출력 폴더 자체가 저장소인 경우도 차단한다. 실행기만 원 경로와 해석한 실제 파일을 함께 기록·사후 비교한다. 출력/증거 링크 거부는 유지한다.

## 실패·필요 입력

브라우저 검사: 최초 출력 경로 거부 종료1(두 경로), 보호 디렉터리 수정 후 browser exited 종료1. 직접 Chromium 진단은 SIGABRT(-6): SUID sandbox helper 설정 오류. `--no-sandbox`는 추가하지 않았다. 화면128/합성 runtime64의 Cloud 실행은 미완료다. UI 조건64개는 Node 코드 검사로만 확인했다.

연구 설치 첫 명령은 도구 호출 stdout/종료0만 남았고 자체 사전 receipt는 없었다. 이후 설치·명령은 별도 logger로 실제 argv/cwd/UTC/elapsed/종료와 stdout/stderr sha256를 보존했다. 상세 로그는 Cloud의 Git 밖 `work/private_artifacts/cloud_20261115/`에만 있다. 호스트 시각은 독립 인증 시각이 아니며 과거 실행 정보는 소급하지 않는다. VM 복구/수명에 영구 보관을 의존하지 않는다.

MANO/개인 영상·좌표·로컬 수정은 가져오지 않았다. 원래 1단계 통제 촬영21행 → 2단계 사람 선별 → 3A 대응 모방/정지 → 3B 보정 → 4 공통 정보 비교 → 5 운영 → 6 공급 확대 순서를 유지한다. 필요한 실입력은 여전히 대기다. 이 실행은 전체 연구 완료가 아니다.

## 다음 선행 조건

1. 모델 없는 point 의미 계약 회귀: SDK관절16/표면손끝5를 분리하고 표면 tip에 고정 길이 강제를 적용하지 않는다. 모델 실제 실행으로 주장하지 않는다.
2. 근거·단위가 없는 프로필은 미통과. 제한 샘플러와 모든 시도/거부 기록은 이 계약과 별개로 개발·검사한다. 임의 생체 범위는 넣지 않는다.
3. MANO 재실행 전: 사용자가 보유한 동봉 LICENSE/info와 현행 약관에서 Cloud 호스팅/제3자 접근 허용 범위를 확인한다. 대상 호스트·접근자·보관/삭제·전송 경로를 정하고 별도 전송 승인이 필요하다. 필요한 파일은 양손 PKL, LICENSE/info, asset manifest/intake, 연구 사용범위 기록, 기존 좌우 PC1 비교 출력과 설정·증거다. 비공개 경로로 승인된 파일만 전송하고 새 배치/hash를 대조한다. Git/LFS/공유 환경에 넣지 않는다. 이 작업은 전송을 수행하지 않았다.
