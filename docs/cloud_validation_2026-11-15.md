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
3. MANO 재실행 전: 사용자가 보유한 동봉 LICENSE/info와 현행 약관에서 Cloud 호스팅/제3자 접근 허용 범위를 확인한다. 대상 호스트·접근자·보관/삭제·전송 경로를 정하고 별도 전송 승인이 필요하다. 필요한 파일은 `MANO_LEFT.pkl`, `MANO_RIGHT.pkl`, `LICENSE.txt`, `info.txt`, `asset_manifest.json`/intake, 연구 사용범위 기록, 기존 좌우 PC1 비교 출력과 설정·증거다. 비공개 경로로 승인된 파일만 전송하고 새 배치/hash를 대조한다. Git/LFS/공유 환경에 넣지 않는다. 이 작업은 전송을 수행하지 않았다.

## 최종 결과·보존 — 2026-11-15

- 최종 연구196개, pipeline147개, Node24개 모두 종료0. 코드 상태: codex 실행기 수정 `ace0d84`+회귀 `e7219d1`; handcaptcha 의미 계약 `3680240`+샘플러 `5b7b3cf`. 최종 재검사는 문서/lock 추가만 있는 상태에서 수행했다. 상세 명령·실제 UTC·경과·종료 상태는 [비식별 실행표](../reports/cloud_model_free_20261115.json), 설치 metadata pins는 [환경별 lock](../requirements/cloud-20261115/README.md)에 있다.
- `assess`의 기본 point semantics는 `unspecified`로 미통과다. 생산자가 `articulated_joint21`을 선언하면20구간, `mano16_surface5`면 표면손끝5구간을 제외한15구간만 길이 불변 수치 검사한다. 이 불변성의 허용오차는 구현의 수치 회귀 tolerance이며 생체 허용값이 아니다. MANO 혼합점의 나머지 BMC feature는 계산 진단용으로 유지하되 기존21관절 프로필로 evidence-backed anatomy pass를 만들지 않는다. 실제 MANO 대응 재검사는 자산이 없어 하지 않았다. 로컬 미검증 코드를 가져오거나 재구성한 것이 아니다.
- 제한 sampler는 기존 공학 QA 동작3종과 기존 seed 진폭 범위만 재사용했다. 별도 PCG64 흐름·시도6회·144프레임, 모든 시작/끝/recipe/거부 사유를 남겼다. 여섯 제한 미확인+물리단위/역학/사람 미검증으로 **6/6 거부**, 검증된 풀 후보0. 생물학적으로 타당한 랜덤 생성 완료가 아니다. 실행 ID `CLOUD-AUTHORED-SAMPLER-20261115-02`: `EXITED_ZERO`, worker 종료0, 사후 snapshot 일치, 출력9개 재검사 `RECORDED_FILES_MATCH`. 첫 `-01`은 worker import root 누락으로 `PROCESS_ERROR`, 종료1·출력0을 보존했다. 시간 예산은 sampler가 시도 전/후 점검하고 execution_record가 전체120초 상한을 적용한다.
- 실행 당시 worker의 import root는 `PYTHONPATH=/workspace/work/handcaptcha:/workspace/work/codex`였다. recorder는 research venv, worker는 video venv를 사용했다. recorder config에 worker root/버전/lock과 worker source들을 입력으로 snapshot했다. 상세 recipe/좌표/receipt/log는 공개하지 않는다.
- `pip check`: research/video/UI 모두 종료0. matplotlib/Fontconfig의 기본 home cache 쓰기 경고는 최종 pipeline에서 `MPLCONFIGDIR`·`XDG_CACHE_HOME`을 workspace 안으로 지정해 해소했다. uv의 home 실행기 링크 생성 경고는 실제 설치 경로의 Python3.10을 직접 사용해 우회했다. 원래 home/보호 디렉터리는 변경하지 않았다.
- Chromium은 nobody 소유 SUID helper와 `NoNewPrivs=1`·namespace 제약을 확인했다. sandbox를 끄지 않았다. Cloud 화면128/합성시작64는 여전히 미실행이다. 향후 적절한 sandbox가 있는 browser 환경이 선행 조건이다.

### GitHub와 복구

codex 작업은 [PR #3](https://github.com/mukgore/codex/pull/3)에 순차 커밋했다. 지정 브랜치로의 자동 병합/강제 push는 하지 않았다.
handcaptcha는 read/clone 가능하지만 shell push403; 연결 GitHub 앱의 repo metadata는 push=true여도 실제 create-tree는403(Resource not accessible by integration)이었다. 따라서 원격 반영 성공으로 보고하지 않는다. 계정 일반 권한과 토큰/앱의 실제 접근 범위는 다르다. 사용자의 해당 연결에 저장소 Contents write 권한이 필요하다. 코드를 계속 진행하고 로컬 커밋 두 개와 [복구 패치](patches/handcaptcha_cloud_20261115.patch)를 codex PR에 보존했다. 기존 원격은 그대로다.

패치는 handcaptcha 기준 `ebdfcb8`의 별도 checkout에서 `git apply --check` 종료0, 현재 변경본에서 reverse check 종료0을 확인했다. 권한이 갖춰지면 **최신 지정 브랜치를 다시 확인/변경 검토한 뒤** 별도 작업 브랜치에서 패치를 적용·검사·push하고 지정 브랜치 대상 PR을 만든다. 재구성된 커밋 SHA는 현재 Cloud 로컬 SHA와 달라도 파일 diff를 대조할 수 있다. 다른 작업자의 변경을 덮어쓰지 않는다.

### 다음 Cloud 실행 지시

1. 두 지정 원격 HEAD와 PR/작업트리를 다시 확인한다. codex PR3 변경과 handcaptcha 복구 패치의 적용 여부를 먼저 구분한다. 원래 네 문서 읽기 순서·백로그62개·prod/2D채점/64조합은 유지한다.
2. 실제 촬영21개 접수·사용권/동의·사람 선별·모방/정지 대응·독립 주석이 들어오면 해당 앞 단계 선행 조건부터 확인한다. 없으면 독립 코드 작업만 계속한다.
3. 모델 없는 후속: sourced constraint profile에 관절/표면 의미·엄지/좌우손·단위/인용 위치·적용 범위 계약을 더 명확히 한다. **현재 실제 허용 수치는 하나도 새로 승인하지 않았다.** 물리단위가 확인되지 않은 MANO native units를 m/mm로 바꾸지 않는다. 기존 혼합21점의 tip proxy에 기존 해부학 관절 hull을 그대로 승인하지 않는다.
4. MANO 실제 제한 랜덤 생산자로 이어가려면 승인된 자산/비공개 범위 기록, 원래16관절/5표면점/전체자세 계약, 고정 좌우48프레임과 기존 비교 자료가 필요하다. Linux 모델 환경을 별도로 설치·wheel hash/사용범위·새 실행 증거를 검증하고 **고정 입력 재현부터** 수행한다. 수치 tolerance는 결과를 보기 전에 정한다. 조건 미확인 시 생성 통과/후보풀 승격 금지.
5. 적절한 sandbox browser가 준비되면 기존 browser_check로 화면128·합성 runtime64를 새 출력 폴더에 재실행한다. 실제 카메라/MediaPipe·사람 효과는 별도다.
6. 상세 Cloud 기록의 별도 비공개 영구 보관처는 아직 지정되지 않았다. 기록은 현재 VM의 Git 밖에만 있고 장기 보존을 보장하지 않는다. 모델/실자료 자동 전송이나 공개 Git 업로드로 이를 해결하지 않는다. 승인된 목적지·접근자·전송/보관 정책이 먼저다.

전체 연구 상태는 **진행 중**이다. 이번 단위 완료는 모델 없는 환경/회귀/거부 기록 진단까지이며 실제 사람 실험·모델 생체 생성·운영 채택의 완료가 아니다.


### 모델 없는 환경 재구성 예시

아래는 다음 Cloud 실행용 명령이다. 현재 검증 환경은 위 실제 실행표의 명령으로 설치했으며 이 블록 전체를 과거 실행했다고 주장하지 않는다. 저장소는 이 작업의 `/workspace/work/{codex,handcaptcha}` 배치를 전제로 한다.

```bash
python3 -m venv /workspace/work/venvs/research
/workspace/work/venvs/research/bin/python -m pip install --no-cache-dir -r /workspace/work/codex/requirements/cloud-20261115/research.lock
python3 -m venv /workspace/work/venvs/ui
/workspace/work/venvs/ui/bin/python -m pip install --no-cache-dir -r /workspace/work/codex/requirements/cloud-20261115/ui.lock
UV_CACHE_DIR=/workspace/work/uv-cache UV_PYTHON_INSTALL_DIR=/workspace/work/python UV_PYTHON_BIN_DIR=/workspace/work/bin uv python install 3.10.22
/workspace/work/python/cpython-3.10-linux-x86_64-gnu/bin/python3.10 -m venv /workspace/work/venvs/video
/workspace/work/venvs/video/bin/python -m pip install --no-cache-dir -r /workspace/work/codex/requirements/cloud-20261115/video.lock
```

환경마다 pip check와 위 최종 검사 명령을 새 기록으로 실행한다. 특정 환경이 실패해도 다른 분리 환경의 검사는 계속한다. 모델 환경은 포함하지 않는다.

이번 커맨드 로그 디렉터리는 `CLOUD-COMMAND-LOGS-20261115` 사후 inventory로83개 파일을 봉인했다. 이는 실제 per-command logger 기록을 나중에 묶은 것이며 inventory 자체를 과거 실험 실행으로 주장하지 않는다. 상세 파일 집합과 hash는 비공개다. 실패 sampler `-01`도 기록 재검사에 일치하며 `PROCESS_ERROR` 상태를 유지한다.
