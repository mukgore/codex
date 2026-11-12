# V02 계보 사전검사와 점수 CSV 연결 — 2026-11-12

## 완료한 개발 작업

기존 단일 부모 자산 검사 `source_preflight`를 유지하면서, 여러 부모와 여러 계열을 가진 자극의 계보를 점수 시행에 연결하는 `lineage_manifest`를 추가했다. 파일 이름이나 새 ID를 부여해도 실제 동일 바이트를 같은 그룹으로 묶는다. 할당하지 않은 복사본의 노출 이력과 부모의 개발·공개 노출도 자식에게 전달한다. 부모 DAG의 순환, 미등록 부모, 가족 계열 누락, 미해결 계보, 사람·촬영·동작 계열·원본·바이트의 split 간 겹침을 검사한다. 파일은 검사 전후 다시 해시하며 입력 크기·노드·계보 및 배정 멤버십에 상한을 둔다.

점수 비교기의 `--lineage-manifest` 옵션을 제공하면 CSV 시행 ID, split, 모든 원동작 계열, 참가자, 응답 촬영이 실제 검사한 배정과 일치해야 한다. 일치하지 않거나 계보 문제를 발견하면 임계값을 선택하기 전에 중단한다. 옵션이 없는 기존 사용은 유지하되 계보 검사를 수행하지 않았다고 결과에 명시한다. 선언과 파일 일치를 확인해도 실제 독립성·촬영 출처·사용권을 증명했다고 표시하지 않는다.

## 실제 파일로 확인한 반례

신규 계보 테스트 15개를 포함해 원격 통합 후 전체 Python 테스트 145개가 통과했다. 복수 부모·동일 바이트·미할당 공개 복사본·파일 변경·배정 변경·기존 출력 보존과 CLI의 임계값 선택 전 차단을 확인했다. handcaptcha prod 파일의 바이트는 기존 기준과 일치했다.

보존 무가림 원본과 무가림·검정·손가락색 FFV1 파생본 4개를 읽었다. 네 파일의 바이트는 서로 다르다. 세 파생본을 development/validation/test에 하나씩 배정한 **합성 분할**에서 공통 조상·원본 바이트·동작 계열·촬영의 split 간 겹침을 각각 세 쌍에서 탐지했다. test의 개발 노출도 한 건 탐지했다. 파일 바이트는 종료 시 재확인했다. 이는 실제 파일의 누출 반례이며 새로운 사람 응답이나 독립 평가가 아니다. 집계는 [보고서](../../reports/lineage_preflight_20261112.json), 경로·ID·해시는 Git 밖 비공개 산출물에 남긴다.

## 사용 방법

```text
python -m validation_v03.lineage_manifest --input PRIVATE_MANIFEST.json --output PRIVATE_ARTIFACTS/NEW_RUN
python -m validation_v03.compare_scores --input PRIVATE_SCORES.csv --output NEW_PRIVATE_REPORT.json --min-human-accept 0.95 --max-attack-accept 0.05 --lineage-manifest PRIVATE_MANIFEST.json
```

위 수용률 값은 명령 형식의 예시이며 채택된 연구 기준이 아니다. 감사 CLI는 발견 사항을 기록하며 0으로 종료하므로 `declared_constraints_satisfied`를 확인해야 한다. 점수 CLI는 이 필드가 false이면 차단한다. 입력 오류는 감사 CLI에서 2로 종료하며 경로·ID를 오류에 노출하지 않는다. 기존 출력은 덮어쓰지 않는다.

JSON은 `schema_version: 1`, `data_scope`, `require_unexposed_test`, `sources`, `allocations`를 가진다. source에는 `source_id`, 실제 `path`, `parent_ids`, 모든 `family_ids`, 원본 촬영의 `capture_ids`, `lineage_status`, `exposure`를 쓴다. root 상태는 공급된 자료 안의 최상위라는 뜻이며 독창성 증명이 아니다. lineage 상태는 `root_of_supplied_material`, `derived`, `unresolved`; exposure는 `declared_unused`, `used_in_development`, `known_public`, `unknown`이다. allocation은 `allocation_id`(CSV trial_id), `split`, `source_ids`, `participant_ids`, 응답 `capture_ids`를 가진다. synthetic 선언도 실제 파일을 요구한다. 여러 부모가 있으면 부모의 모든 계열을 자식에 선언한다.

## 필요한 입력과 다음 선행 조건

V02 자동 검사 개발은 진전됐지만 미사용 실제 촬영·사람·원동작 계열은 확보되지 않았다. 재인코딩·좌우 반전·유사 동작인데 부모를 숨긴 자료는 바이트 검사만으로 탐지하지 못하므로 촬영 대장과 영상 검토가 필요하다. 과거 공개 pool과 현재 개발 원본을 독립 test로 승격하지 않는다. 실제 점수 보정은 2단계 명확성 확인과 분리된 대응 시행이 들어온 뒤 수행한다.

원격의 `53ef1b8`, `b916291`에 있던 V02 단일 부모 검사, V05 세션 발급 예산, 노출·인수·비용 감사도 fast-forward로 통합했다. 이 작업을 다시 미실행으로 열지 않는다. 이후 가능한 엔지니어링 검토는 V05 실행/연결 예산과 운영 경계부터 진행하며, 실제 운영·사람 실험의 선행 조건은 유지한다. UI 수정 단계 전까지 handcaptcha prod 화면을 기준으로 한다.
