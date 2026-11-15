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
