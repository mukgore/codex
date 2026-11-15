# 저자 부위 합집합을 제작 관문에 연결 — 2026-11-15

[실행 순서](../research_goal_followups_2026-11-10.md#실행-순서와-기존-백로그-연결)를 유지한다. 실제 촬영/사람 입력은 등록 접수 여부를 재확인하며 앞 단계 입력이 들어오면 우선한다. [기존 영상의 추가 보호 검사](2026-11-15_author_surface_region_union_audit.md)를 사후 확인으로만 두지 않고 이후 진단 영상 제작에도 적용하는 단위다.

## 실행 전 변경과 계획

- `mano_common_camera_rerender`의 기본 보호는 `author_region_union`이다. 고정 profile/assignment/저자 source-review 입력이 모두 있어야 하며 누락·source blob 불일치·현재 모델 부위 대응 실패는 거부한다. 기존 proxy로 자동 대체하지 않는다.
- 저자 중지 proximal/intermediate 정점에 닿는 면 전체를 기존 보호 면에 더한다. 양손 각15개 centroid/뼈 대응과 index 연결을 확인하고 실제 union을 source raster·반경 조건·ROI/codec core·가림 후보/H.264 재생 픽셀 검사에 사용한다.
- 예전 방식은 명시적 `--protection-mode legacy_rest_proxy`로만 재현한다. 그 결과는 `legacy_reproduction_only=true`로 표시하고 저자 합집합 통과로 집계하지 않는다. legacy 조건에서 author 입력을 주고 무시하는 것도 거부한다.
- 원래 Stage6/7 내부15%·외부10%·손끝 최소2개·전 프레임100%, codec2픽셀·채널30·외부MAE2.0은 그대로다. 비어 있지 않은 distal patch는 사람이 알아볼 수 있다는 검증이 아니다.

실제 계획은 [기존 paired-preflex16개 저장 동작](2026-11-15_visible_cue_conditioned_generation.md)의 양손·두시점32개/800프레임 재렌더다. 새 모델 추론이나 새 난수 동작은 없다. 관문이 허용할 때만 새 가림 후보와 H.264를 만들고 영상별 실제 시간/실패를 기록한다. source와 이전 결과/receipt는 보존한다. 같은 동작을 다시 그려 독립 family가 늘어난 것으로 세지 않는다.

기본 입력 누락 시 source I/O 이전 거부, legacy 명시/입력 혼용 거부, 기존 보호 면 보존·잘못된 모델 부위 거부 등을 포함해 관련17개 검사를 통과했다. 실제 결과는 실행 이후 추가한다. 모든 자료는 연구용 격리이며 생체·사람·운영 승인이나 prod UI 변경은 아니다.

## 실행 명령의 형태

기존26pin 로컬 오프라인 환경에서 저장소 루트를 작업 디렉터리로 사용한다. 아래 대괄호 경로는 실제 비공개 자산/새 출력 경로로 지정해야 하며 원본 모델/영상은 공개 저장소에 넣지 않는다.

```text
python -m analysis.runtime_benchmark.mano_common_camera_rerender
  --source [완료한-비공개-SDK-출력]
  --source-record [그-실행-record]
  --worker-root [기존-handcaptcha-작업트리]
  --ffmpeg [기존-ffmpeg.exe] --ffprobe [기존-ffprobe.exe]
  --camera-mode hand_neutral_registered
  --region-profile references/cpf_model_surface_region_review.json
  --region-assignment [고정-저자-merged_vertex_assignment.txt]
  --region-review [고정-palette-loader-source-review-폴더]
  --output [새-비공개-출력]
```

실제 실험은 이 명령을 `validation_v03.execution_record run`으로 감싸 코드/입력/환경·명령·시각·종료/산출물을 먼저/나중에 기록한다. 원문 그림/색 기반 프로젝트 부위 대응과 임상/독립 해부학 경계의 차이는 [학술 색인](../academic_reference_index.md)에 유지한다.

## 실제 완료 결과

등록 접수21행의 원본 경로0개·선별 응답 관측값0개를 실행 전에 다시 확인하고 config 입력에 묶었다. 범위는 등록 접수이며 전체 컴퓨터의 파일 조사나 사람 관찰이 아니다. 원래 단계 입력을 기다리는 동안 독립 진단 제작 검사를 진행했다.

| 실제 실행 항목 | 결과 |
| --- | --- |
| 명령에서 보호 방식 옵션을 생략 | 기본 `author_region_union` 적용, legacy fallback 없음 |
| 현재 양손의 모델 부위 대응 | 각15/15 centroid/예상 뼈 확인 |
| 저장16동작 × 두시점 source 재렌더 |32영상·800프레임 |
| 합집합 반경/ROI/patch를 통과한 경우 |16/32, 최소2개 비어 있지 않은 distal patch |
| 새로 인코딩한 가림 후보/H.264 |각16영상·400프레임, 재생 후 합집합 픽셀 검사 통과 |
| 실제 영상 시간 |source32 + 가림16 + H.26416 =64행 |
| 새 모델 추론/독립 family/풀·브라우저 채택 |모두0 |

양손의 실제 저장 보호 face 목록을 [사후 독립 audit](2026-11-15_author_surface_region_union_audit.md)의 합집합 목록과 대조했고,800개 amodal raster도 모두 정확히 일치했다. 메타데이터에 mode 이름만 붙인 것이 아니라 제작 단계에서 같은 추가 영역을 쓴 것을 확인했다.

현재 저장 동작에서는 source32·가림16·H.26416 파일이 각각 이전 제작물과 **전체 바이트까지 동일**했다. 영상은 실제 다시 인코딩했고 시간도 새 실행에서 측정했지만, 새 문제/다양성/독립 표본이 늘어난 결과는 아니다. 기존 fixture에서는 화면을 유지하면서 필수 보호 관문이 추가된 회귀 확인이다.

오른손 두시점과 왼손 한시점의 시작/중간 H.264 프레임을6장 추출했고 이 중3장을 직접 시각 확인했다. 여전히 검은 원 밖 작은 손끝 일부만 남는다. 가림 통과를 사람이 정확한 동작을 읽을 수 있는 증거로 쓰지 않고 연구용 격리를 유지한다. 모델의 전반적인 생체/경계·사람 모방·복수 답·강한 공격/운영 인수도 별도다.

[집계 JSON](../../reports/mano_union_guard_20261115.json)과 [영상별 시간64행 CSV](../../reports/mano_union_guard_video_timings_20261115.csv)에 단계별 실제 wall/자체CPU·UTC·FPS/길이/bytes와 준비 완료 경계를 남겼다.

| 실제 구간, 초 | 준비 완료 최소/중앙/최대 | 추가 검산까지 최소/중앙/최대 |
| --- | --- | --- |
| 저장 source→공통 카메라 FFV1 인코더 종료 |3.265 / 3.371 / 3.739 |3.440 / 3.627 / 3.981 |
| source→가림 library 반환(내부QC 포함) |0.269 / 0.284 / 0.325 |0.309 / 0.329 / 0.384 |
| 가림 후보→H.264 library 반환(내부QC 포함) |0.480 / 0.523 / 0.637 |0.522 / 0.568 / 0.687 |

공통 source/보호 정의/카메라 준비약0.100초와 recorder 봉인은 별도다. cached SDK 결과를 재사용한 재렌더 시간이며 원 모델 생성 시간을 이번64행에 다시 넣지 않았다. library 내부 인코더 종료 순간과 내부QC를 나누어 관측하지 않았고 FFmpeg 자식CPU도 측정하지 않았다. 순서 고정·OS/codec cache와 배경 부하 미통제인 로컬 진단으로 이전 방식보다 빠르다는 성능 비교가 아니다.

실행은 `EXITED_ZERO`, journal `COMPLETED800/800`, 생산자 `36d46d6`·입력274개·dependency26pin·산출물425개 검산 통과다. 비공개 위치는 `private_artifacts/mug_20261115/`, `mano_union_guard_record_20261115/`, `mano_union_guard_config_20261115.json`, `mug_prerequisites_20261115.private.json`과 선택 프레임 `mug_review_20261115/`다. raw mesh/좌표·실제 face/ROI·영상·개별 hash는 Git에 추가하지 않았다. 기존 source/모델/이전 결과·receipt와 prod UI는 변경하지 않았다.

연구258개와 실제 오프라인 region/camera17개 검사 통과. 새2개는 기본 누락 입력의 사전 거부·legacy 혼용 거부·기존 보호 목록 불변과 잘못된 부위 거부를 확인한다. 전체 생체/사람/인증 인수는 아니다.

## 완료한 일과 다음 관문

완료는 사후 추가 검사였던 합집합 보호를 진단 가림 제작의 기본 필수 관문으로 연결하고, 실제 제작/재생과 원본 보존·영상별 시간을 검산한 것이다. 현재16개는 모두 연구용 격리이며 사용자용 문제로 채택하지 않았다.

다음 독립 개발은 **같은 표시 단서에서 서로 다른 숨은 중지 동작이 가능해지는지** 실제 모델·최종 가림 영상으로 검사하는 일이다. 전체 손의 단순 깊이 평행이동만을 다른 정답으로 세지 않고, 고정된 형상/카메라/가림/표시 조건에서 상대 관절 동작의 대안을 검토한다. 이것도 생성기 측 모델 제약 진단이며 사람의 유효 정답이나 실제 공격 성공으로 표시하지 않는다. 사람 선별/모방·복수 허용 답의 최종 확정은 실제 입력이 필요하다.

원래1→2→3A→3B→4→5→6과 UI64조합 실제 효과 관문, 비공개 영구 보관·Cloud 보류는 유지한다. 실제 촬영·독립 주석·사람 응답·모델/운영 입력이 들어오면 앞 단계부터 우선한다.
