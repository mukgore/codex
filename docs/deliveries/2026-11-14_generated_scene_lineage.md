# 3D 영상 가족관계와 분할 사전검사 — 2026-11-14

같은 문제의 변형을 연습과 시험 양쪽에 섞으면 처음 보는 문제에서의 성능으로 해석할 수 없다. [GEN3D-01·EVAL3D·POOL-01/02의 공백](../3d_execution_requirement_audit_2026-11-14.md)에 따라 [장면 계보 계약/검사](../../validation_v03/GENERATED_SCENE_MANIFEST.md)를 구현했다. 원래 앞 단계의 촬영·사람·독립 평가 입력은 계속 필요하다.

## 구현한 것

- hand/object geometry, contact plan, trajectory, camera, renderer 여섯 family를 명시한다. seed·generation run·source/recipe identity와 구분한다.
- 실제 파일/모든 부모·재인코딩/동일 bytes를 연결한다. byte alias를 먼저 확장해 자식에게 부모 관계를 빠짐없이 상속한다. generated source에 실제 카메라 capture ID를 꾸며 넣지 않는다.
- `compare_scores --generated-scene-manifest`가 CSV allocation과 연결된다. 겹침/미확인 계보가 있으면 threshold 선택 전 거부한다. 일반 lineage 경로와 기존 촬영 자료의 capture 요구는 유지한다.
- 일부 축만 분리하는 평가도 정책에 명시할 수 있지만 전체 독립 평가로 주장하지 않는다. 모든 family/자산 상태의 의미는 작성자 선언이며 파일 검사만으로 권리나 의미적 독립성을 증명하지 않는다.

## 기존 파일로 실제 확인

앞 [표면 렌더 실행](2026-11-14_surface_depth_cues.md)의 기록을 실행 전후 재검사하고, 그때 snapshot한 handcaptcha 구현 파일이 현재 사용하는 코드와 같은지 확인했다. 저장 참조 288프레임을 같은 생성 recipe로 다시 계산해 정확히 대조했다. 새 동작/참가자/독립 source를 생성하지 않았다.

| 확인한 자료 | 결과 |
|---|---:|
| 실제 영상 파일 | 112개 = 무가림 48 + 가림 후보 32 + H.264 32 |
| 코드/seed recipe의 기본 scene | 4개 |
| seed 종류 | 2개 |
| 실제 서로 다른 파일 bytes | 66종 |
| 동일 bytes 중복 그룹 | 30개 |
| 서로 다른 scene까지 연결된 동일 bytes 그룹 | 10개 |
| hand / object / contact / trajectory / camera / renderer family | 1 / 1 / 2 / 1 / 1 / 1 |
| 새 사람 시행 / 모델 추론 | 0 / 없음 |

66종 bytes도 고유 동작 66종이 아니다. 컨테이너/인코딩 차이는 동작의 차이가 아니며 동일 bytes의 영상이 다른 3D 설명을 가질 수도 있다. 현재 좁은 family 자료만으로 여섯 축이 분리된 독립 평가 풀을 만들었다고 할 수 없다.

세 가지 배정을 검사했다. 실제 사람/공격 점수 분할이 아니라, 자료를 잘못 나누었을 때 검사가 잡는지 보는 **합성 배정**이다.

| 배정 | 실제 검사 결과 |
|---|---|
| 전체 diagnostic | 현재 자료를 개발 진단으로 유지. 독립 development/validation/test partition은 없음 |
| seed 7→development, 19→test | 여섯 축의 family가 모두 공유되고, 동일 bytes/원본 관계와 기존 개발 노출도 연결됨. validation도 없음. 거부 |
| 원본→development, 동시 반전→validation, 손만 반전→test | 부모·동일 bytes·모든 family 축·노출 이력을 통해 누출 발견. 손만 반전한 거부용 제어를 실제 test로 채택하지 않음. 거부 |

독립성을 확인했다는 결과가 아니라 **이 자료로 독립 평가를 주장하면 안 된다는 근거**다. 분석/코드 진단에는 계속 쓸 수 있다. 새 seed 수를 늘리는 것만으로 손/물체/동작/카메라 family의 공유 문제가 해결되지 않는다.

## 실행 증거와 검사

최종 코드는 codex `b129989`, 실행 ID는 `G01-G02-V02-SCENE-LINEAGE-20261114-v3`다. 비공개 401개 입력 파일·코드·26-pin 환경을 실행 전 snapshot했고, 실제 명령 종료 0·후검사 일치·출력 8개 연결/재검사까지 확인했다. 이전 실행의 빈 stderr log 1개는 직접 nonempty input snapshot 대상에서 제외하되 이전 receipt의 checksum과 전후 검사를 통해 계속 연결했다.

초기 준비는 이 빈 log 때문에 프로세스 실행 전에 거부됐다. 그 설정/사후 메모를 보존했다. 중간 v2 실행에서는 동일 bytes의 부모를 자동 family에 상속할 때 생긴 불필요한 metadata finding을 발견해 보완했다. v2 산출물/실행 기록은 덮어쓰지 않고 최종 v3 집계를 사용한다. 없는 과거 시작 시각을 만들지 않았다.

Python 전체 189개와 장면 계보 신규 12개 검사가 통과했다. 서로 다른 seed의 공유 family, 같은 recipe의 이름 변경, 미배정 alias/노출 전파, 부모/자식, 미검토 자산·검사 중 자산 변경, source/응답 capture 분리, CSV binding과 CLI의 threshold 전 거부를 확인했다.

```powershell
python -m validation_v03.execution_record verify --record ../private_artifacts/generated_scene_lineage_record_20261114_v3
```

[공개 집계](../../reports/generated_scene_lineage_20261114.json) 외의 영상·좌표·개별 파일 해시·장면/family/자산 manifest·상세 로그는 비공개 영구 보관한다. prod UI·점수식·운영 발급은 변경하지 않았다. 현재 scene manifest는 이번 분석 때 만들었으며 과거 렌더 실행의 사전 manifest로 소급하지 않는다.

## 다음 순서

사용자가 확인한 [학술 근거와 제약 있는 랜덤 생성](../3d_biomechanics_and_random_generation_2026-11-14.md)을 다음 독립 단위로 둔다. 관절/손바닥/연동·시간·충돌의 근거를 코드 좌표계에 대응하는 프로필과 거부 관문부터 준비한다. 현재의 임의 공학 fixture를 생물학적으로 타당하다고 바꾸거나, seed만 늘려 다양한 자연 동작 공급을 완료하지 않는다. 앞 단계 실제 촬영·사람 응답/주석·동일 조건 모방/정지·독립 평가 자료가 오면 그 우선순위를 먼저 따른다.
