# 다음 로컬 세션을 위한 인계 — 2026-11-16 최종 정리

**최신 TF-04 인계:** [실제결과](deliveries/2026-11-16_matched_display.md): native `tf4n_20261116_v1`/`tf04_native_record_20261116_v1`(74출력), display `tf4d_20261116_v1`/`tf04_display_record_20261116_v1`(361출력), 분석재개 `tf4a_20261116_v2`/`tf04_analysis_record_20261116_v2`(9출력)는모두검산통과다. 분석v1 `tf4a_20261116_v1`/기록의 `PROCESS_ERROR`와5부분출력은그대로보존했다. 완료SDK/48영상/256점수/36raster를다시실행하지않는다. 다음가능한앞단계진단은기존로컬MediaPipe의완료영상추정이며full/palm/graph/handedness자산과기존ASCII리소스cache를확인했다(새추론은아직0). TF-05/실제입력은대기,전체목표active. GitHub push는자동승인거부후명시승인대기다. 로컬연구와비공개/격리/전체큐를유지한다.

**최신 목표 진행 갱신:** 전체 실행순서/백로그 목표는 active다. [TF-02 실제실행](deliveries/2026-11-16_template_free_pose_pilot.md), [TF-02P 실패생산자 원출력의 별도감사](deliveries/2026-11-16_projected_pose_audit.md), [TF-03 실제4경로·100프레임](deliveries/2026-11-16_template_free_paths.md)까지 진행했다. 다음은 **TF-04 동일조건 카메라/author_region_union/최종영상·계보/채점 비교 명세와 실행**이다. TF-03 출력/기록/설정은 `tf03_path_20261116_v1`, `tf03_path_record_20261116_v1`, `tf03_path_config_20261116_v1.json`이며 `EXITED_ZERO`,102 SDK자세/28출력 검산 통과다. TF-02P 원생산자의 `PROCESS_ERROR`는 보존하고 이를 별도 성공감사와 혼동하지 않는다. 실제입력 우선·기존전체큐·격리/비공개/Cloud보류는 유지한다. 아래 이전 인계/‘다음’은 이력이며 완료한 SDK/영상은 다시 실행하지 않는다.

**같은 날짜의 후속 재개 갱신:** 사용자의 명시적 재개 후 이 문서를 끝까지 읽고 상태/등록 입력/세 receipt1104산출물을 확인했다. 예정했던 [고정 prod JS 수치 진단1024건](deliveries/2026-11-16_frozen_prod_coordinate_scores.md)은 이제 완료다. 기록은 `..\private_artifacts\frozen_prod_score_record_20261116_v2`, 출력은 `fpsd_20261116_v2`, 설정은 `frozen_prod_score_config_20261116_v2.json`이다. v1 준비 실패도 별도 private기록/설정으로 보존했다. [TF-01 적용표](tf01_constraint_application_2026-11-16.md)와 [TF-02 사전등록](tf02_pose_pilot_preregistration_2026-11-16.md)을 작성했으며 **다음 독립 단위는 TF-02 표현 검산·구현·기록 실행**이다. 기존 촬영21행 원본0/선별관측0, 원래 앞단계 우선과 전체 백로그는 유지한다. 아래는 이전 중단 시점의 원문이며 ‘채점 미착수/TF-01 계획만’은 후속 갱신 전 이력이다. 완료한 좌표 진단/이전 생성·렌더는 재실행하지 않는다.

사용자가 이번 단위까지 정리·커밋한 뒤 안전 중단을 요청했다. **전체 연구 완료가 아니라 일시중지다.** 새 세션이 사용자의 재개 요청을 받으면 이 문서와 실제 파일 상태를 먼저 확인한다. 이전 대화가 모두 전달된다고 가정하지 않는다. 별도의 전역 설정·자동 실행·권한 변경 없이, 저장한 문서와 명시적인 시작 프롬프트를 인계 기준으로 쓴다. 다른 컴퓨터/Cloud에는 비공개 로컬 자료가 자동 이전되지 않는다.

## 1. 저장소와 먼저 읽을 문서

- 작업 위치: `C:\Users\조영준!\Documents\CLI\deliverables-review\codex-research-20261110`.
- GitHub: `mukgore/codex`, 원격 작업 브랜치 `work/todo-consolidation-20261103`.
- 현재 로컬 브랜치: `work/research-input-audit-20261110`. 이름이 원격과 다르지만 의도된 작업트리다. 임의 checkout/reset/clean/새 복제로 바꾸지 않는다.
- 이번 문서 추가 전 완료 기준: `d6e361f` (120개 실제 파일 계보 점검). 인계 문서 자체를 담는 최종 커밋은 `git log -1` 및 원격 ref로 확인한다. 자기 커밋 hash를 문서에 미리 꾸며 쓰지 않는다.
- handcaptcha 작업트리: `..\handcaptcha-ui-20261113`, HEAD `9f29ac44adb42509ca7a6c475b82031c9d30f198`. 이번 정리에서 변경 없음. 원래 `..\codex`, `..\handcaptcha` 작업트리도 건드리지 않는다.

읽는 순서:

1. 저장소와 상위의 적용 가능한 `AGENTS.md`, `git status --short`, `git branch --show-current`, `git log -5 --oneline`.
2. [연구 순서 문서](research_goal_followups_2026-11-10.md)의 **「실행 순서와 기존 백로그 연결」**. 1→2→3A→3B→4→5→6이 우선이다.
3. [앞으로 할 일 통합표](remaining_work_master_2026-11-15.md): 기존62개 백로그 ID, 3D 상세 요구44개, 실행시간 R0–R9를 보존한다. 연구 전체를 3D만의 목표로 축소하지 않는다.
4. [이번 신규 방향](template_free_constrained_generation_2026-11-16.md), [학술 색인](academic_reference_index.md), [생체/랜덤 생성의 기존 상태](3d_biomechanics_and_random_generation_2026-11-14.md).
5. [마지막 계보 결과](deliveries/2026-11-16_counterfactual_lineage.md), [실제 다른 모델 움직임/동일 최종 영상 대조](deliveries/2026-11-15_relative_middle_display_counterfactual.md), [실험 증거 규칙](experiment_evidence_protocol_2026-11-14.md).

README/PROJECT_STATUS와 우선순위 문서의 오래된 ‘다음’ 문장은 당시 단위의 이력이다. 최신 입력 상태와 이 인계 문서/전체 큐를 함께 판단한다.

## 2. 완료한 일과 과장하면 안 되는 부분

- 기존 원형 조건부 생성과 고정 모델 prior/표면/최종 영상 관문은 구현되어 있다. 동시/순차 굽힘 및 선택 손가락 원형의 수치 변형이며 임의의 모든 자연 동작 생성기가 아니다. 등록 seed는7·19, 원형 연동/시간값 일부는 공학 선택이다.
- 실제 중지 대안32조건을 SDK802회 계산하고64시점·192영상으로 비교했다. 변경48시점 중46개의 최종 H.264는 부모와 픽셀과 파일 바이트가 같았다. 무가림48개는 모두 달랐다. 모델 조건에서의 정밀 궤적 비유일성이며, 사람에게 다른 정답인지·공격 성공인지·CAPTCHA 불가능인지의 입증은 아니다.
- 최신 계보 점검: 120개 실제 파일 항목, native32조건의 정확한 좌표/시간 payload24종, 최종 H.26464개의 파일 바이트14종. 그중12종에 다른 모델 궤적이 연결된다. 잘못된 가상 split의 byte/family/source 중복과 노출을 검출했다. 독립 평가 partition은 없다. 새 추론·영상·사람 시행을 수행한 점검이 아니다.
- 마지막 전체 연구 검사263개 통과 기록, 최신 계보 관련15개 검사 통과 기록을 보존한다. 이번 문서 정리만으로 모델/전체 검사를 재실행하지 않았다.
- 모든 3D 결과는 연구 격리이며 풀/브라우저 채택0개. BMC 여섯 허용 한계 미확인, 임상 축/범위·편안함·실제 사람 해석/모방·물리/연속 충돌은 미완료다.
- 신규 B/C 원형 없는 생성 방향은 **계획만 추가**했다. TF-01 적용표/TF-02 자세 샘플러/TF-03 경로 생성은 아직 구현·실행하지 않았다. 기존 A 경로도 유지한다.

## 3. 다음 세션의 작업 순서

1. **상태 점검과 새 입력 확인.** dirty 파일을 보존하고 실행 receipt/출력 검산을 읽는다. 완료한 생성/렌더를 다시 시작하지 않는다. 마지막 등록 촬영21행의 원본 경로0개, 선별 관측값0개는 등록 범위의 상태일 뿐 PC 전체 영상이 없다는 뜻은 아니다. 새 원본/응답이 생겼으면 원래1/2/3A부터 우선한다.
2. **기존에 예정한 다음 작은 단위:** 원본·숨은 대안·정지·부분 동작·결측 좌표를 고정 prod 원문 JS 채점/자세 각도 함수로 진단한다. 코드/실행은 아직 시작하지 않았다. Node는 확인됐으므로 순수 수치 진단은 실제 카메라 없이 준비 가능하다. 가중치·기준을 재보정하지 않는다. UI의 시간/200ms hold/실제 검출·인증을 시뮬레이션 통과로 주장하지 않는다.
3. **추가 요청의 후속:** 위 단위를 다른 신규 실험으로 확장하기 전에 새 생성 방향 TF-01의 원문→관절/축/단위/연동/수치 적용표를 준비하고 작은 TF-02 제안 실험을 등록한다. 실제 입력이 앞서면 그것을 우선한다. A 비교 경로를 유지하고 B/C 구현과 미확정 생체 제약을 구분한다. 자세 prior만 통과한 결과는 연구 격리, 사람 유효 승인 금지다.
4. 이후 TF-03/04/05 및 전체 백로그를 선행 조건에 따라 진행한다. UI64조합의 실제 효과, 같은 정보의 사람/모델 비교, 실제 운영/공격 검증과 비용은 계속 미완료다. 불가 단계는 필요한 입력을 적고 독립적으로 가능한 작업을 진행한다.

### 다음 채점 수치 진단에 필요한 고정 정보

prod: `..\handcaptcha-ui-20261113\hand_captcha_prod.html`.
SHA256: `0d82dd439fe7976f8b860eb82e654e6f5637b2d7a3fcce2d02f2f99e5f5bea11`.

`MATCH_ANGLE_THRESH=38`, `MATCH_HOLD_MS=200`, `THRESHOLD=.25`, `W2={da:.38,ac:.37,a:.25}`, `MX={angle:46.9413,dtw_angle:44.0014,accel:.1926}`.
확인할 실제 함수 이름: `ppSingle`, `angleErr`, `findKeyframes`, `pp`, `rs`, `mA`, `mDA`, `mAc`, `es`, `computeScores`. 원문은 `POSE MATCHING`/`METRICS` 주석 주변이다.

※ 위 함수 이름은 prod 원문 확인용이다. `mDA`는 현재 sliding window이며 진짜 DTW로 부르지 않는다. `mAc`는 index 기준 이차 차분이라 초 단위 가속도가 아니다. 자체 비교 점수를1이라고 미리 가정하지 않는다. `computeScores`는 `segments`/`keyframes` 상태와 결측 비율의 영향을 받고 각도 수치만으로200ms hold나 최종 인증을 보장하지 않는다. 이후 구현 시 원문 hash와 추출 범위를 검증하고 독립 Python 복제로 미묘한 반올림 차이를 숨기지 않는다.

## 4. 비공개 로컬 자료와 실행 환경

아래 모든 `private_artifacts`/`private_tools`는 연구 저장소 기준 **`..\private_artifacts\` / `..\private_tools\`**다. 실제 모델·mesh/좌표·영상·가림 원본/개별 hash/원문 사본은 공개 커밋하지 않는다.

| 용도 | 보존 위치 |
|---|---|
| 최신 계보 결과/기록 | `mcl_20261116/`, `counterfactual_lineage_record_20261116/`, `counterfactual_lineage_config_20261116.json`, `mcl_prerequisites_20261116.private.json` |
| 숨은 중지 native/최종 영상 | `mcn_20261115/`, `mcd_20261115/`, `mano_hidden_native_record_20261115/`, `mano_hidden_display_record_20261115/`; config는 `mano_hidden_native_config_20261115.json`, `mano_hidden_display_config_20261115.json` |
| 부모/가림 관문 | `mano_preflex_cues_20261115/`, `mpc_20261115/`, `mug_20261115/`, 각각의 기존 기록과 config. 저자 합집합 record는 `mano_union_guard_record_20261115/` |
| 모델/사용 범위 | `model_inputs/mano_intake_v1/`, `mano_continuing_research_scope_20261114.private.json`; 모델 intake의 원래 manifest/동의 기록도 보존 |
| 학술 원문/고정 코드 | `cpf_literature_20261115_v1/`, `manotorch_loss_source_20261115/`, `manotorch_region_source_20261115/`, `cpf_region_review_20261115/`, `manotorch_source_review_20261115/` |
| 촬영/선별 등록 | `screening_packet_20261110_v1/capture_jobs.private.json` 및 기존 응답 양식. 실제 입력 여부를 재확인 |

실행 환경은 새 설치 없이 기존 것을 확인한다.

- 연구 검사 Python: `..\..\hand-captcha-research\.venv\Scripts\python.exe`.
- SDK CPU: `..\private_artifacts\mano_cpu_runtime_20261105\venv\Scripts\python.exe`, Torch2.5.1+cpu/smplx0.1.28/numpy1.23.5/scipy1.10.1, 해당 폴더 `requirements-wheels.lock`17pin.
- 영상/검산: `..\private_artifacts\offline_runtime_rebuild_20261105\venv\Scripts\python.exe`, numpy1.26.4/scipy1.14.1/opencv4.10.0/mediapipe0.10.14, lock26pin.
- Node: `C:\Program Files\nodejs\node.exe`, 확인 버전v24.18.0.
- FFmpeg/ffprobe: `..\private_tools\ffmpeg-9.0.2\ffmpeg.exe`, `ffprobe.exe` (bin 하위 아님).
- PDF 검토 도구: `..\private_tools\pdf_review_20261115\`의 pypdfium2 4.30.0. 모델 환경에 설치하지 않는다.

### 완료 receipt와 실행 중 상태의 구분

- 최신 계보: 생산자 `97964ee61bff69004bfdeab6fe4a00364cba9848`, 입력1763/26pin/출력5, `EXITED_ZERO` / `RECORDED_FILES_MATCH`, 기존 exec76817 종료0.
- native 중지 대안: 생산자 `8a68c0fdf547c3b2ef3ff5e45e7dcf72a7ee0a1d`, 입력777/17pin/출력198, `EXITED_ZERO` / 출력 검산 통과, 기존 exec16563 종료0.
- 최종 표시 대안: 같은 생산자, 입력683/26pin/출력901, `EXITED_ZERO` / 출력 검산 통과, 기존 exec98939 종료0.
- 위 번호는 이전 도구 핸들의 이력이다. 새 세션에서 살아 있는 세션 ID로 가정하거나 wait/kill을 보내지 않는다. 이번 정리에서 새 연구 프로세스를 시작하지 않았다. Windows CIM 전역 프로세스 조회는 이전 접근 거부였으므로 모든 OS 프로세스의 종료를 보장하지 않는다.

이번 최종 인계 준비에서는 위 세 receipt의 등록 출력1104개를 다시 읽어 파일 존재·크기·SHA256이 모두 일치함을 확인했다. 새 실험이나 현재 worktree에 대한 과거 입력 snapshot의 재승인은 아니다. 새 문서의 로컬 링크 누락0, 기존 통합 큐 ID 삭제0, prod 원본 hash 일치도 확인했다.

영상별 생성시간은 public reports의 native32행/영상192행과 private 원기록에 있다. ready/검증 완료·wall/자체CPU·cache를 구분하고 자체CPU에 ffmpeg 자식 CPU가 포함된다고 가정하지 않는다. 과거 시간을 새로 채우지 않는다.

## 5. 반드시 지킬 사용자 지시

- 본인 촬영·본인 손인 기존 영상은 연구/가림 파생본 범위의 사용자 진술을 기록했다. **비공개 영구 유지**이며90일 삭제로 되돌리지 않는다. 외부 업로드/공개/상업 사용 동의로 확장하지 않는다.
- 모델 라이선스와 원문/코드 라이선스는 별도다. 제한 모델·가중치·원자료를 공개 저장소에 넣지 않는다. Cloud/Colab/GPU 이전은 보류이며 별도 지시 없이 실행/환경 변경하지 않는다.
- CAPTCHA/UI는 항상 handcaptcha root prod를 기반으로 한다. prod 교체/배포를 하지 않는다. 중첩과 최초500ms 같은 첫 정지 프레임 노출+500ms fade 등6요인64조합의 실험 코드/합성 검사는 기존 범위로 유지하며 실제 사용자 효과를 검증했다고 쓰지 않는다.
- 표면 가림은 현재 `author_region_union` 기본 관문과 고정 profile/assignment/source-review가 필요하다. 누락/불일치 시 거부한다. legacy proxy로 조용히 후퇴하거나 보호 영역/기준을 줄이지 않는다.
- 학술 수치마다 출처·관절/축/단위·대상/과제를 기록한다. 저자 코드 기본값/공학 연동을 임상 한계로 부르지 않는다.
- 새 실제 실행은 명령·UTC/실시간·자체CPU·생산 코드와 전체 worktree·입력/환경 snapshot·종료/stdout/stderr·출력 hash와 실패 기록을 새 immutable root에 남긴다. 기록 실행 중에는 문서/코드를 편집하거나 커밋하지 않는다. postflight가 전체 작업트리를 확인하므로 예전에도 도중 편집으로 정당하게 거부된 실행을 보존했다.
- 임의 프로세스 종료/재시작·원본 덮어쓰기·force push·main 반영 금지. 도구/권한이 바뀌거나 파일이 없으면 실제 확인 못 한 부분을 보고한다. 이번에는 추가 승인 질문 없이 지정 브랜치 커밋/인계 후 중단한다.

## 6. 복사해서 쓸 다음 세션 시작 프롬프트

```text
로컬 손동작 CAPTCHA 연구를 재개해 줘. 작업 폴더는
C:\Users\조영준!\Documents\CLI\deliverables-review\codex-research-20261110
이고 GitHub mukgore/codex의 work/todo-consolidation-20261103 브랜치 작업이야.
로컬 브랜치는 work/research-input-audit-20261110일 수 있으니 이름이 다르다고 바꾸지 마.

먼저 적용 AGENTS.md와 git 상태를 확인하고 docs/SESSION_HANDOFF_2026-11-16.md를
끝까지 읽어. docs/research_goal_followups_2026-11-10.md의
「실행 순서와 기존 백로그 연결」을 우선하고 remaining_work_master_2026-11-15.md,
template_free_constrained_generation_2026-11-16.md, academic_reference_index.md와
마지막 계보/중지 대안 delivery를 읽고 실제 private 기록과 대조해.

완료한 실행/렌더를 다시 하지 말고 변경 파일·기존 프로세스·원자료를 보존해.
새 촬영/선별 입력을 먼저 확인하고, 없으면 예정한 고정 prod JS 채점 수치 진단을
다음 작은 단위로 진행한 뒤 원형 없는 제약 생성 TF-01/02로 이어가.
기존 원형 변형 생성은 유지하고, 원형 없이 자세/경로를 만드는 별도 경로도
학술 원문·관절/축/단위/연동의 근거에 따라 실제로 시도해.
미확인 생체 한계는 꾸며 넣지 말고 모델 제약/사람 타당성/물리/보안을 구분해.
새 실제 실험은 사전 명세와 실행/입출력/시간/실패 기록을 남기고,
기록 실행 중에는 worktree 편집/커밋을 하지 마.

prod UI 기준·기존 임계값·비공개 영구 보관·Cloud 보류와 전체 백로그를 유지해.
현재 실제 상태와 다음 단위를 짧게 알려준 뒤 작업을 계속해.
```

이 프롬프트와 같은 로컬 작업 폴더를 사용한다. GitHub 문서만으로 비공개 모델/자료까지 복원할 수는 없다. 새 세션에서 이전 도구·권한·목표 상태를 그대로 가정하지 말고 확인한다. 자동 재개 설정은 추가하지 않았으며, 이 세션은 최종 push/상태 검산 후 사용자 요청대로 일시중지한다.
