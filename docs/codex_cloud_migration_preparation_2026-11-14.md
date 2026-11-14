# Codex Cloud 이전 조사와 실행 준비 — 2026-11-14

현재 한 단위 연구를 마친 뒤 작성한 **계획**이다. Cloud VM 생성·설치·시험 실행·모델/영상 업로드는 하지 않았다. 기존 연구 코드나 로컬 환경을 이전 목적으로 바꾸지 않았다. 아래 명령은 승인 후 Cloud에서 검증할 초안이며 Linux 실행 성공 기록이 아니다.

## 먼저 마친 연구와 인계 시점

[MANO 새 생산 경로](deliveries/2026-11-14_mano_controlled_producer.md): 연구 commit `425f1dd`(생산 코드 `5b4cf85` 포함), handcaptcha commit `ebdfcb8`. 두 저장소 모두 `work/todo-consolidation-20261103` 원격 브랜치에 push했다. 이 시점 두 작업 트리는 깨끗했다. 양손 48프레임 생성·재decode, 이전 표면/관절/PCA 값 일치, journal 48/48 완료와 출력 17개 재검사가 통과했다. 첫 실패도 보존했다. 프로세스는 실제 호출의 종료 코드와 실행 receipt로 종료를 확인했으며 임의로 중단/재시작하지 않았다. 이후 `Get-Process python,ffmpeg,ffprobe`에도 해당 이름의 실행 프로세스가 나오지 않았다. 이 조회는 모든 컴퓨터 작업의 종료를 증명하지 않는다.

따라서 **이번 단위의 출력 검증·커밋·push가 끝난 지금이 인계 준비 시점**이다. 전체 연구 완료 시점은 아니다. [원래 순서](research_goal_followups_2026-11-10.md)의 통제 촬영·사람 선별·실제 모방/정지 대응 자료가 우선이며 아직 입력 대기다. 다음 독립 개발은 관절 출처 계약을 유지한 제약 프로필·제한 랜덤 생성/거부 기록이다. SI 단위·생체 허용 범위를 추정으로 승인하지 않는다. UI는 handcaptcha root prod를 기준으로 유지한다.

## 공식 기능과 아직 확인하지 않은 것

현재 공식 안내는 `Work in > Cloud`에서 환경을 만들고 저장소·의존성을 준비한 뒤 Publish하고 새 작업을 시작하는 흐름이다. 작업은 PC가 잠든 동안에도 진행한다. 같은 Cloud 작업을 다시 열면 그 작업의 파일을 이어 쓰며, 새 작업은 준비된 환경에서 별도 시작한다. 중요 결과는 별도 보존해야 한다. 기본 복구 기간은 마지막 시작/재개 후 최대 7일이다. 기본 VM은 Plus/Edu Plus 2 vCPU·8 GiB RAM·8 GiB disk, Pro/Business/Enterprise/Edu/Edu Pro 4 vCPU·16 GiB·32 GiB다. Computer use는 현재 미지원이다. Only me 설정과 필요한 패키지/도메인만 허용하는 설정을 사용할 수 있다. [공식 Cloud 환경 안내](https://learn.chatgpt.com/docs/environments/cloud-environments)

위는 제품 문서 확인이다. **사용자 요금제·Cloud 권한·두 GitHub 저장소 연결·선택 가능한 VM·Linux 배포판/아키텍처·네트워크 정책·실제 자원 한도는 이 세션에서 확인하지 못했다.** 여기 제공된 도구에는 Cloud 환경 생성/게시·VM 상태 조회 도구가 없다. 현재 로컬 대화·실행 프로세스·파일·개인 스킬이 자동 이전됐다고 보지 않는다. 기존 remote-PC 연결은 PC 전원이 필요하므로 전원 종료 후 독립 실행의 대안으로 쓰지 않는다.

## 작업별 이전 판단

| 작업 | 판단 | 필요 요소·로컬 전용 입력 | 기능 차이·최소 준비 |
|---|---|---|---|
| 연구 코드·좌표/통계 단위 검사 | 우선 이전 후보 | codex 저장소, Python과 `requirements.txt` | Linux에서 전체 193개 재실행. Windows Job Object 대신 POSIX process group 경로도 검증 |
| MANO CPU 손 생성 | 기술적으로 이전 후보, 권리/입력 준비 전 실행 대기 | Python3.10, torch2.5.1+cpu, smplx0.1.28, chumpy0.70, 아래 모델 환경; 양손 PKL·동봉 LICENSE/info·intake·범위 기록 | Windows venv 복사 불가. Linux wheel/lock 새 검증. 모델의 제3자 호스팅 범위 확인과 별도 업로드 승인 필요 |
| 영상 렌더·좌표/채점 검증 | 파일 기반 부분 이전 후보 | OpenCV, NumPy/SciPy, ffmpeg/ffprobe, 비공개 비교 자료, 두 저장소 | FFV1/H264 지원과 timestamp/픽셀·수치 차이 검증. 새 Cloud 실행 기록 생성. 실제 관측을 합성 결과로 대체하지 않음 |
| 실행 기록·Git 커밋/PR | 이전 후보 | GitHub 연결·권한, execution_record/run_manifest, 비공개 결과 보존처 | 코드/요약만 Git. 상세 산출물은 승인된 저장처에 별도 저장 후 hash 대조. 계정별 push/PR 가능 여부 실제 확인 |
| 중첩·초기 노출 UI의 Node 검사 | 우선 이전 후보 | handcaptcha, Node24.18.0 | 기존 24개 Node 검사 실행. prod 원본 hash 유지 |
| UI 64조합 브라우저 검사 | 조건부 이전 후보 | Chromium/Chrome, Python `websockets==16.0`, ffmpeg, CDP localhost | 현재 스크립트는 headless subprocess를 직접 쓰므로 Computer use와 별개. `--chrome`에 Linux 경로 전달 가능. VM sandbox/포트/codec 실제 확인 전 성공 주장 불가 |
| 실제 MediaPipe 손 인식 | 녹화 영상 추론은 조건부, 실제 웹캠은 로컬 | legacy Hands0.10.14 및 실제 사용 모델/CDN·녹화 파일 | CPU/브라우저 backend와 검출 차이 확인. UI 합성 검출기는 실제 MediaPipe 성능 검증이 아님 |
| 실제 카메라·사람의 모방/선별·편안함 | 로컬 유지 | 사용자 카메라·조명·사람·동의와 실제 촬영 | PC가 꺼진 Cloud에서 사용자 손을 직접 촬영할 수 없음. 별도 촬영 후 허용 범위의 자료 분석만 가능 |

## 로컬 자료와 저장 위치

기준 폴더는 `C:\Users\조영준!\Documents\CLI\deliverables-review\`다. 상세 개인 입력 경로/해시는 로컬 비공개 기록에서만 읽는다.

- 연구 작업 트리 `codex-research-20261110/`, hand 구현 `handcaptcha-ui-20261113/`. GitHub repo는 각각 `mukgore/codex`, `mukgore/handcaptcha`다. 기본 브랜치로 전환하지 않는다.
- `private_artifacts/model_inputs/mano_intake_v1/`: 양손 모델과 동봉 LICENSE/info·asset manifest. 총 5파일 **7,648,352 bytes** 실측. 원본 intake의 `UNREVIEWED` 등 초기 상태는 변경하지 않았다.
- `private_artifacts/mano_cpu_runtime_20261105/venv/`: Windows Python3.10 CPU 실행 환경. 파일 크기 합 **1,596,064,647 bytes** 실측. Linux 설치 크기나 RAM 사용량을 뜻하지 않는다. 같은 폴더의 wheel lock은 Windows 산출물용이다.
- `private_artifacts/mano_controlled_producer_20261114_v2/`: 이번 결과 17파일 **2,386,722 bytes**. 원래 16관절/전체 자세·표면·참조·영상·미리보기·journal/bundle. 실행 증거 `mano_controlled_producer_record_20261114_v2/`: 9파일 **74,059 bytes**. 둘 다 Git 밖이다.
- 이번 config는 `mano_controlled_producer_config_20261114_v2.json`, 사용 범위 연결은 `mano_continuing_research_scope_20261114.private.json`. 78개 실제 입력 snapshot·CPU 17개 package lock·producer code와 묶여 있다.
- 현재 producer의 **이전 값 비교**까지 실행하려면 `mano_pca_flat_sweep_20261105/{left,right}_pc1/`의 기존 자료도 필요하다. 범위 기록은 `codex/docs/deliveries/2026-11-05_{mano_cpu_pilot,model_access_steps}.md`를 참조한다. 새 두 repo checkout만으로는 이 자료들이 생기지 않는다.
- 실제 원본 영상·사람 입력·기존 세션과 비교 기준은 별도 로컬 비공개 자료다. 이번 조사에서 전체 개인 디스크를 수집하지 않았다. 실제 촬영 입력은 현재 등록 기록상 대기다.

## 의존성과 설치 명령 초안

**공통 도구:** Git, Python3.10(모델·MediaPipe 기준), venv/pip, Linux용 ffmpeg/ffprobe(로컬 비교 기준 9.0.2), Node24.18.0, Chromium/Chrome, UI용 websockets16.0. OpenCV Linux 실행에는 이미지에 따라 `libgl1`·`libglib2.0-0` 등이 필요하다. 패키지 권한/배포판을 확인한 뒤 설치한다. 원래 Windows exe/venv/wheel의 hash를 Linux 패키지 hash처럼 재사용하지 않는다.

**연구 환경:** 저장소 `requirements.txt`의 NumPy2.2.6/SciPy1.15.3/openpyxl3.1.5/pypdf6.19.0/OpenCV-python4.12.0.88/matplotlib3.10.8. 모델 환경과 섞지 않는다.

**모델 환경의 실제 17 pins:** chumpy0.70, filelock4.1.0, fsspec2026.9.0, Jinja2 3.1.6, MarkupSafe3.0.4, mpmath1.3.0, networkx3.4.2, NumPy1.23.5, OpenCV-contrib-python4.10.0.84, SciPy1.10.1, setuptools75.8.0, six1.17.0, smplx0.1.28, sympy1.13.1, torch2.5.1+cpu, typing_extensions4.16.0, wheel0.45.1. `pip freeze` 일치만으로 배포 파일이 같아지지는 않는다. Linux wheel의 출처·hash·간접 의존성을 새로 기록한다. Chumpy는 보존한 공개 소스 hash를 대조하고 별도 환경에서 wheel을 build해야 한다. Windows wheel을 Linux에 쓰지 않는다.

**영상/MediaPipe 환경:** handcaptcha의 `dataset_pipeline/requirements-win-py310.txt` 버전 선택을 참고하되 Linux lock으로 간주하지 않는다. 주요 pin은 mediapipe0.10.14 / NumPy1.26.4 / protobuf4.25.3 / OpenCV-contrib4.10.0.84 / jax·jaxlib0.4.30 / SciPy1.14.1 / matplotlib3.9.4다. 일반 `dataset_pipeline/requirements.txt`는 다른 cv2 배포물도 설치할 수 있어 Linux lock을 따로 검증한다. 같은 환경에 cv2 배포물을 중복 설치하지 않는다. UI용 websockets는 이번 offline 영상 환경에는 없고 연구 환경에16.0이 있음을 확인했다.

아래는 **승인 후 Cloud에서만 실행할 예시**다. 현재 환경에는 실행하지 않았다. 처음에는 모델·개인 영상을 사용하지 않는다.

```bash
# Example layout: connected repos in /workspace/codex and /workspace/handcaptcha
cd /workspace/codex
git switch work/todo-consolidation-20261103
git rev-parse HEAD
python3.10 -m venv /workspace/venvs/research
/workspace/venvs/research/bin/python -m pip install -r requirements.txt
/workspace/venvs/research/bin/python -m pip check
/workspace/venvs/research/bin/python -m unittest discover -s tests

cd /workspace/handcaptcha
git switch work/todo-consolidation-20261103
node --version
node --test experiments/prod_ui_factorial/conditions.test.cjs experiments/hand_selection/selection.test.cjs experiments/prod_selected_hand/bridge.test.cjs experiments/prod_selected_hand/async.test.cjs
```

Python/Node가 이 경로와 버전으로 존재하는지 먼저 확인한다. OS별 설치 명령을 확인 없이 적용하지 않는다.

Linux 영상 환경을 검증한 뒤 실행할 예시:

```bash
cd /workspace/handcaptcha
FFMPEG=$(command -v ffmpeg)
CHROME=$(command -v chromium || command -v google-chrome)
test -n "$FFMPEG" && test -n "$CHROME"
/workspace/venvs/video/bin/python -m unittest discover -s dataset_pipeline/tests
/workspace/venvs/ui/bin/python -m experiments.prod_ui_factorial.browser_check \
  --chrome "$CHROME" --ffmpeg "$FFMPEG" \
  --output /workspace/private_artifacts/cloud_ui_NEW_RUN
```

root 권한에서는 Chromium sandbox 시작이 실패할 수 있다. `--no-sandbox`를 임의로 추가하지 않고 VM의 실행 사용자·브라우저 구성을 확인한 뒤 필요한 변경을 별도 승인받는다.

모델 실행은 권리/업로드 승인·Linux17pin 검증·비교 자료 전송·경로 대응을 마친 뒤에만 진행한다.

```bash
cd /workspace/codex
/workspace/venvs/mano/bin/python -m validation_v03.execution_record run \
  --config /workspace/private_artifacts/cloud_mano_config.NEW.json \
  --repo /workspace/codex \
  --record /workspace/private_artifacts/cloud_mano_record_NEW \
  --artifact-root /workspace/private_artifacts/cloud_mano_NEW -- \
  /workspace/venvs/mano/bin/python -m analysis.runtime_benchmark.mano_recorded_producer \
  --intake /workspace/private_artifacts/model_inputs/mano_intake_v1 \
  --research-record /workspace/private_artifacts/cloud_research_scope.NEW.json \
  --worker-root /workspace/handcaptcha \
  --legacy-root /workspace/private_artifacts/mano_pca_flat_sweep_20261105 \
  --output /workspace/private_artifacts/cloud_mano_NEW
```

새 config의 78개 입력 참조·SDK source·Linux lock·code commit을 Cloud 실체로 snapshot한다. Windows의 기존 증거는 덮어쓰지 않는다. 범위 기록의 절대 경로만 고쳐 옛 기록처럼 쓰지 않고 원기록과의 관계·전송 hash·Cloud 배치를 새로 기록한다. 이전 로컬 postflight의 환경 일치는 Cloud에 적용되지 않는다. 입력이 부족하면 이 명령부터 실행하지 않는다.

## 자원과 결과 차이 검증

이번 두 사례의 외부 실행 receipt상 경과 시간은 약7.86초, 모델/영상은48프레임이다. CPU 시간·최대 RAM은 측정하지 않아 Cloud 실행 시간을 예측할 수 없다. 초기 계획은 한 작업·torch 한 thread, 4vCPU/8–16GiB RAM·빈 disk8GiB 이상을 후보로 삼되 필요 최소값은 아니다. 8GiB disk에는 여러 Python 환경·torch와 다운로드 cache·Chromium·영상이 함께 들어가면 부족할 수 있다. 처음 `df -h`, `free -h`, `nproc`와 실제 최대 RSS·생성 크기·경과 시간을 기록한다. 32GiB disk에서도 여유를 확인한다. 큰 실험은 나누고 GPU가 있다고 가정하지 않는다. 이 CPU 환경으로 HaMeR/Text2HOI의 부족 자산까지 해결했다고 보지 않는다.

결과 일치 확인 순서:

1. 두 repo commit과 root prod SHA256 `0d82dd439fe7976f8b860eb82e654e6f5637b2d7a3fcce2d02f2f99e5f5bea11`, 승인된 전송 파일 bytes/hash를 대조한다. 모델 hash는 비공개로 유지한다.
2. Python/모든 package·wheel·ffmpeg build/codec·Node/Chrome·OS/CPU/thread/seed를 기록하고 단위 검사·시간 초과/process-group 회귀를 실행한다.
3. 고정 좌우 PC1 각24프레임부터 시작해 raw16/canonical21·fullpose48·parent16·faces·finite·순서·시각·journal48분모를 대조한다. Windows 배열과 bitwise 일치 여부부터 보고한다. 다르면 최대 절대 오차/RMS/변화 위치를 저장하며 통과시키려고 기준을 사후 확대하지 않는다. 수치 허용값은 결과 판정 전에 정한다.
4. FFV1 전체 decoded 프레임·투영·특징/점수 차이를 확인한다. OS/codec간 H264 bytes나 PNG metadata 일치는 보장하지 않는다. decoded 화소·마스크 내부/외부·PTS/크기/프레임 수를 나눠 비교한다.
5. UI24개 Node 검사·128개 화면/화소·64개 합성 시작/준비/중단을 재검사한다. 실제 camera/MediaPipe/사람 효과는 별도 결과다. 채점 불가·추적 결측·시간 초과를 점수 차이와 구분한다.
6. 새 Cloud 실행을 execution_record로 종료·snapshot·출력과 연결하고 승인한 비공개 저장처에 보관한 뒤 재검증한다. 로컬 hash는 독립적인 실험 인증이 아니다.

## MANO와 비공개 자료의 이동 조건

동봉 LICENSE를 로컬에서 읽고 현행 [공식 MANO 라이선스](https://mano.is.tue.mpg.de/license.html)도 확인했다. 비상업 과학 연구·관리하는 컴퓨터에서의 사용 범위와 제3자 제공/재배포 제한이 있다. 동봉판과 현행 페이지의 표현 차이를 유지한다. **비공개 Cloud라는 이유만으로 허용되는지는 확인하지 못했다.** Codex 호스트에 배치하고 호스트 측에서 접근하는 범위가 허용되는지, 필요하면 권리자에게 확인할 항목으로 남긴다. 연락하거나 새 계약을 맺지 않았다.

모델·라이선스 원문·좌표/파생 mesh/영상·개인 영상을 공개 repo/LFS나 공유 준비 환경, 대화 첨부에 넣지 않는다. 본인 촬영·연구 사용 확인을 외부 서비스 전송 동의로 바꾸지 않는다. 이번 조사 요청은 실데이터 전송 승인이 아니다. 대상·장소·접근자·보관/삭제·전송 경로를 구체화해 별도 승인받는다. Publish도 준비 파일을 담으므로 처음 환경에는 모델을 넣지 않는다. 장기 보관은 VM의 7일 복구 가능성에 의존하지 않는다.

## PC를 종료하기까지의 구체적 순서

1. **완료한 준비:** 현재 단위 종료·기록 검증·코드와 요약 push. 로컬 결과와 실패 기록은 유지한다. 이 자료와 [인계 지시](codex_cloud_handoff_2026-11-14.md)를 Cloud 작업에 전달한다.
2. **사용자 Cloud 설정:** `Work in > Cloud > Create environment`에서 두 repo를 선택한다. Only me·지정 branch·필요한 package domains를 설정하고 계정 권한/이용 한도를 확인한다. 처음에는 모델·개인 자료 없이 준비한다.
3. **승인 후 환경 구성:** 분리 환경과 Linux lock을 준비하고 작은 검사를 실제 실행한 뒤 setup 보고를 확인해 Publish한다. 별도 승인 전에는 이전을 위해 연구 코드나 환경을 바꾸지 않는다.
4. **Cloud 새 작업 시작:** 게시한 환경에서 새 작업을 시작하고 인계 지시·branch를 전달한다. Cloud 로그와 호스트의 두 repo·입력을 확인한다. 로컬 디스크/localhost/PC의 VPN 서비스에 의존하지 않아야 한다. 이 로컬 대화를 이어가는 것만으로 이전되지는 않는다.
5. **모델까지 이어갈 경우:** 권리/전송 확인·승인, 독립적인 비공개 저장 경로, Linux 모델 smoke와 차이 검증을 마친 뒤 생성을 시작한다. 해결 전에도 모델 없는 코드·UI·채점 구현은 가능하다.
6. **그 뒤 PC 종료:** 로컬 결과 저장과 Cloud 실행을 확인한 뒤 사용자가 PC를 종료한다. Cloud 실행은 PC 전원에 의존하지 않는다. 휴대폰/다른 기기에서 같은 Cloud 작업을 확인한다. 무기한 실행·무제한 이용을 보장하지 않는다.

현재 Cloud 실행은 시작하지 않았다. 지금 PC를 끄면 로컬 작업이 자동으로 Cloud에서 이어지는 상태가 아니다. 코드부터 이전하는 경로가 최소이며 같은 MANO 생성까지 이어가려면 권리/입력·Linux 검증을 추가해야 한다.
