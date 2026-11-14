# 생성 장면 계보와 점수 보정 사전검사

`generated_scene_manifest.py`는 실제 파일의 부모/동일 bytes와 3D 장면의 family 기준을 함께 확인한다. 서로 다른 seed는 미사용 물체·접촉 계획·움직임의 증거가 아니다. ID와 family/자산 상태는 작성자의 선언이며 검사 통과도 의미적 독립성·권리·실제 사람/카메라를 인증하지 않는다.

## 비공개 JSON 계약

최상위 필드는 `schema_version=1`, `data_scope`(기존 lineage scope), `require_unexposed_test`, `separate_axes`, `scenes`, `sources`, `allocations`다. 기존 [실행 기록 기준](../docs/experiment_evidence_protocol_2026-11-14.md)과 함께 사용한다.

- 각 scene: `scene_id`, `origin_type=generated_3d`, `generator_version`, `generation_run_id`, 정수 `seed`, 비어 있지 않은 `parameters`, `family_axes`, `asset_record`.
- `family_axes`는 `hand_geometry`, `object_geometry`, `contact_plan`, `trajectory`, `camera`, `renderer` 여섯 키다. 각 값은 family ID 또는 명시적 미확인 `null`이다. null은 사전검사 finding이며 통과시키지 않는다.
- `asset_record`는 실제 local `path`와 `status`다. 상태는 `self_authored_fixture`, `external_terms_recorded`, `unreviewed`. 파일 존재/bytes를 확인하지만 내용의 진실성과 허용 범위를 자동 인증하지 않는다. 미검토 자산은 거부 finding이다.
- 각 source: `source_id`, 실제 `path`, `scene_id`, `parent_ids`, 기존 `lineage_status`/`exposure`, 비어 있지 않은 `variant_parameters`, 선택적 `sha256`. variant에는 깊이 제어·렌더 모드·media stage 같은 실제 변형을 기록한다.
- `allocations`는 기존 `allocation_id`, `split`, `source_ids`, `participant_ids`, `capture_ids` 계약이다. **생성 자극 원본에 카메라 capture ID를 만들지 않는다.** 사람 응답 영상의 실제 capture/participant ID는 allocation에서 별도로 기록하고 검사한다.

`separate_axes`에는 이번 평가에서 분리하겠다고 미리 정한 축을 명시한다. 모두 분리할 때 여섯 축을 모두 적는다. 일부만 선택하면 나머지 축의 겹침도 집계하되 그 축의 독립성을 주장하지 않는다. 생성 batch/run ID가 같다는 이유만으로 분할을 거부하지 않는다. 같은 batch에서도 실제로 분리된 family를 생성할 수 있으나 그 의미는 별도 검토 대상이다.

scene ID·실제 generator/version/seed/parameters의 동일 recipe, 부모/파생본·byte alias는 선택한 축과 무관하게 함께 추적한다. alias와 모든 부모 관계를 먼저 확장한 뒤 family를 자동 상속한다. 서로 다른 장면의 영상 bytes가 같아도 ‘family 선언 오류’로 단정하지 않고 실제 중복 그룹과 분할 누출로 검사한다. 보이는 영상만 같고 3D 정답이 다른 모호성도 별도 검토해야 한다.

## 실행과 점수 연결

```powershell
python -m validation_v03.generated_scene_manifest --input ../private_artifacts/scene_manifest.private.json --output ../private_artifacts/NEW_SCENE_AUDIT
python -m validation_v03.compare_scores --input ../private_artifacts/scores.csv --output ../private_artifacts/NEW_SCORE_REPORT.json --generated-scene-manifest ../private_artifacts/scene_manifest.private.json --min-human-accept PREDECLARED_VALUE --max-attack-accept PREDECLARED_VALUE
```

실험 실행은 명령 기록 도구로 감싸 별도 새 기록 폴더를 사용한다. 예시의 두 판단 값은 실제 수집 전에 정한 값으로 바꾼다. `--generated-scene-manifest`와 일반 `--lineage-manifest`는 함께 지정할 수 없다. 생성 장면 평가에서는 이 전용 사전검사를 명시적으로 사용한다. CSV 자체로 자극이 생성물인지 자동 인증하지 않는다.

모든 CSV trial ID·split·participant/response capture·source family 집합이 검사된 allocation과 같아야 한다. 불명확한 계보·선택 축 겹침·알려진/노출 미확인 test·없는 독립 partition 등이 있으면 **threshold를 고르기 전에** 거부한다. `source_family_ids`는 자동 상속된 typed family ID 집합과 일치해야 한다. seed-only 이름으로 바꿔 통과시키지 않는다.

summary는 개수/발견 종류만 공개 가능하도록 구성한다. 상세 manifest/findings/asset·입력 해시·source family ID/seed·경로는 private output에 둔다. `declared_constraints_satisfied=true`도 현재 선언과 파일 제약을 만족한다는 뜻이며 독립 연구 완료가 아니다.
