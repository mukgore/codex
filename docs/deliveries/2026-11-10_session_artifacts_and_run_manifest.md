# S06 저장·재로드와 V00/N02 사전 실행 기록 검증

[실행 순서](../research_goal_followups_2026-11-10.md#실행-순서와-기존-백로그-연결)와 [62개 추적표](../backlog_execution_audit_2026-11-10.md)의 다음 작업으로 수행했다. handcaptcha prod UI·HTML·채점식은 수정하지 않았다. 기존 내보내기/저장 자료를 분석하는 도구이며 새로운 사람 촬영·동의·응답은 생성하지 않았다.

## S06: 실제 보존 자료의 저장·재로드

[session_artifacts.py](../../validation_v03/session_artifacts.py)는 다음 세 형식을 명시적으로 검사한다.

| 형식 | 검사하는 것 | 검사로 확보하지 못하는 것 |
|---|---|---|
| `prod_v2_pool` 보존 세션 | segment/frame 구조, XYZ 21점 또는 null, 시각 순서, 저장 total/detected/detectionRate와 실제 프레임 일치 | 수집 build, 실제 카메라 FPS/영상 크기, 재생·자세 대기 분리, 점수식 재실행 |
| `selected_hand_gate_v1` 이벤트 내보내기 | 실제 고정 정책 값, 허용 event/reason/phase, 시각·중단 flag·잘림 | 카메라 진위, 원래 점수·정답, 프레임 coverage, 최종 인증 |
| `palm_guidance_v1` 로컬 시연 로그 | 허용 필드, 상대 시각, trial index·설정 값, 잘림 | 실제 모방 점수·인간 성공, 빠진 terminal 이벤트 |

좌표가 들어오면 안 되는 두 이벤트 형식에서는 `lm` 등 알 수 없는 필드를 거부한다. `"False"` 문자열을 Boolean으로 간주하지 않는다. 중복 JSON key·NaN/무한 수·역전 시각·지원하지 않는 정책을 거부한다. 저장 이벤트의 동일 시각은 JS 시계 반올림/클램핑과 양립하므로 허용하며, 이것을 실제 원시 시계의 단조성 증명으로 사용하지 않는다.

선택 손 bridge는 완료를 기록한 callback 뒤에 `phase_changed` 같은 후처리 이벤트를 덧붙일 수 있다. 실제 형식대로 이를 허용하되 완료/중단이 충돌하는 terminal flag는 거부한다. bridge의 오래된 이벤트 삭제와 demo의 새 이벤트 저장 중단은 각각 잘림으로 남긴다. 잘린 로그에서 전체 시도 결과를 확정하거나 없는 사건을 복구하지 않는다. terminal 이벤트가 보인다는 사실도 인증 성공이 아니다.

새 private artifact 폴더에 **원래 JSON bytes**, canonical JSON, 원본/canonical checksum과 재계산한 검사 결과를 담은 receipt를 저장한다. 각 쓰기에 flush/fsync를 적용하고 receipt를 마지막에 쓴다. 즉시 별도 load 경로로 원본→canonical→원데이터를 다시 대조한다. 부분 저장·세 파일 중 어느 하나의 변경·기존 출력 재사용을 거부한다. receipt도 canonical bytes로 대조해 공백 변경이나 Python에서 같게 취급할 수 있는 `1`/`true`, `3`/`3.0` 형식 변경을 놓치지 않는다. checksum은 우발적 손상을 검사할 뿐, 세 파일을 함께 재작성할 수 있는 작성자를 인증하지 않는다.

[실행 코드](../../analysis/roundtrip_existing_sessions.py)로 기존 18세션을 실제 처리했다. 입력 원본 bytes를 바꾸지 않았고 모든 좌표/null을 보존했다.

| 실제 처리 범위 | 결과 |
|---|---:|
| 보존 세션 시도 / 저장·재로드 검증 | 18 / 18 |
| 구간 / segment 프레임 | 126 / 8,782 |
| 명시적 미검출 | 141 |
| 원본 bytes 변경 | 0 |
| 실제 JS 내보내기 코드로 만든 별도 합성 사례 | 완료 / 중단 / 잘림 3종 검증 |
| 신규 사람 관측 | 0 |

[JS harness](../../analysis/export_event_fixtures.cjs)는 실제 소유 source의 selector/logger/bridge를 synthetic hand·mock clock으로 실행했다. 카메라·브라우저·MediaPipe·외부 네트워크는 사용하지 않았다. 이 세 사례는 18세션이나 사람 표본에 합치지 않는다. 원본/좌표/개별 결과/입력 fingerprint는 private storage에만 보관했다. [공개 집계](../../reports/session_roundtrip_20261110.json)에는 합계와 합성 사례 상태만 있다.

```powershell
python -m validation_v03.session_artifacts --input <기존_JSON> --output ../private_artifacts/session_artifact_NEW
python -m validation_v03.session_artifacts --verify ../private_artifacts/session_artifact_NEW
python -m analysis.roundtrip_existing_sessions --raw-root ../../hand-captcha-research/data/raw --source-root ../handcaptcha --output ../private_artifacts/session_roundtrip_NEW
```

이것은 S06의 저장/재로드 계약을 실제 자료로 검사한 결과다. 새로운 gate gap/coverage 정책의 사용자 수용·새 기록 UI 연결·실제 미관측 시간의 실패 분류를 완료한 것은 아니다. 특히 `camera_frame_coverage=null`과 과거 build 미확인 상태를 유지한다.

## V00/N02: 실행 전에 고정하고 실행 뒤 대조

[run_manifest.py](../../validation_v03/run_manifest.py)는 아래 입력을 빠뜨린 실행을 사전 준비 단계에서 거부한다.

- run/protocol/scoring/challenge manifest/input protection 버전, endpoint·정보 노출·진단/개발/검증/test 분할·실행 종류
- seed 또는 적용하지 않는 구체적 이유, 실제 OS·hardware·browser 기술, 명시적 시간 예산·실험 parameters
- 실제 code 파일·입력/참조 파일·정확한 dependency lock 경로

live camera/human screening에서 browser를 `not_applicable_offline`으로 채우는 경우를 거부한다. hardware/browser/사용권 등은 호출자의 기술이며 독립 인증으로 바뀌지 않는다. 승인·동의가 있다고 자동 생성하지 않는다.

자동 snapshot에는 현재 Git commit·tracked diff와 untracked 내용을 반영한 dirty fingerprint, 선택한 코드/입력/설정 파일 bytes·SHA256, Python 실행기/버전, lock SHA256·pin·실제 설치 metadata 버전을 담는다. code 파일의 저장소 이탈·중복 input ID·없는 파일·byte budget 초과를 거부한다. lock은 정확한 버전 고정 형식이어야 하며, 설치 metadata 버전이 다르면 거부한다. 추가 설치 package도 숨기지 않고 private manifest에 남긴다. **설치 metadata 일치는 wheel 내용 재검증이나 깨끗한 환경·dependency consistency 검증의 대체가 아니다.**

실행 뒤 code/input bytes·Git 상태·Python·설치 package/lock을 다시 대조한다. config와 관련 파일이 바뀌거나 manifest bytes 자체가 바뀌면 거부한다. 사전 준비 성공은 `PREPARED_NOT_EXECUTED`, 후검사 성공은 `CURRENT_SNAPSHOT_MATCHES`다. 그 자체로 실험이 완료됐다고 출력하지 않는다.

```powershell
python -m validation_v03.run_manifest --config ../private_artifacts/run_config.json --repo . --output ../private_artifacts/run_provenance_NEW
python -m validation_v03.run_manifest --verify ../private_artifacts/run_provenance_NEW
```

### 실제 runtime journal 연결

[실행 wrapper](../../analysis/provenance_guard_smoke.py)에서 위 snapshot을 **실행 전** 만들고, 그 SHA256을 기존 runtime journal의 manifest에 연결했다. 실제 JS 내보내기 3종 생성→artifact 저장/재로드→후검사→journal 완료→bundle 재검산을 수행했다. 기존 해시 고정 offline 환경의 **26개 pin이 설치 metadata와 일치**했다.

| 실제 기술 실행 | 결과 |
|---|---|
| 실행 전 snapshot | 생성 |
| 실행 후 코드/입력/환경 | snapshot과 일치 |
| 계획 JS 내보내기 / 검사 완료 | 3 / 3 |
| runtime journal과 provenance 연결 | 일치 |
| bundle 복구 | COMPLETED |
| 계획 영상 프레임 / 실제 사람 관측 | 0 / 0 |
| 카메라·모델 추론 | 실행하지 않음 |

[공개 집계](../../reports/provenance_guard_20261110.json)에는 fingerprint·경로·환경별 상세 식별자를 복사하지 않았다. 최종 코드의 private 상세는 `provenance_guard_final_20261110`에 있다. 초기/중간 실행은 별도 폴더에 보존했고, 공개 기술 결과 집계는 최종 실행과 일치했다. 실제 wall clock은 기록했지만 mock clock 이벤트의 33ms와 모델/사람 처리시간을 혼동하지 않는다. 이 실행은 JS export/storage 계약의 기술 실행이다.

후검사 이후 문서·보고서를 게시하거나 commit이 바뀌면 `--verify`는 현재 상태의 drift를 보고할 수 있다. 이것을 감추려고 과거 snapshot을 덮어쓰지 않는다. 실행 당시 후검사·journal·bundle은 immutable 근거로 보존하고 새 실행은 새 폴더/새 snapshot을 쓴다. 현재 구현을 과거 사람/HaMeR 실행의 사전 기록으로 소급하지 않는다.

## 검증과 다음 입력

artifact 신규 검사 11개와 manifest 신규 검사 7개가 통과했다. 실제 18세션/3종 export와 사전 snapshot을 연결한 기술 실행도 완료했다. 검사에는 부정확한 pin·seed/필수 metadata 누락·코드/입력/lock/untracked 변경·manifest 변조·기존 출력·path 이탈이 포함된다. 실제 JS 검사에는 소유 handcaptcha checkout과 Node가 필요하며, checkout이 없는 환경의 해당 integration skip은 실행 근거로 세지 않는다. 이번 환경에서는 실제 소스를 사용해 통과했다.

S06의 기존 자료 보존과 V00/N02의 공통 snapshot 경로는 구현·기술 검증 상태다. 실제 신규 수집에서 permission/phase-before/after/global-frame-ID, 실제 display/capture 해상도·전체 UI 시간·입력 출처를 계측하려면 해당 실험과 prod 기반 연결이 필요하다. 현재 goal은 계속 진행하며 다음은 **V02 계보·파생본·중복의 사전 검사**, 그 뒤 5단계의 남은 보안/최종 출력 검사다.
