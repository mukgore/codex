# 분할 사전검사와 영상 풀 인수 증거 대조

기준 작업 브랜치는 두 저장소의 `work/todo-consolidation-20261103`이다. 시작점은 [codex 80a9c9e][research]와 [handcaptcha e21a974][hand]다.

## V02 평가 전 자료 검사

`python -m validation_v03.source_preflight --root PRIVATE_MEDIA_DIR --manifest PRIVATE_MANIFEST.json`을 자료 분할·임계값을 잠그기 전에 실행한다. JSON은 자료별 객체의 배열이다. 각 객체에 `asset_id`, `source_family_id`, `capture_id`, `performer_id`, `split`, `parent_asset_ids`, `path`를 둔다. `path`는 루트에 상대적이며 `split`은 development, validation, test 중 하나다. 원본은 부모 배열이 비어 있고 단일 원본 계열 파생본은 부모가 한 개다. 여러 원본을 결합한 시행은 이 자산 명세 밖이며 기존 [점수 비교기](../../validation_v03/compare_scores.py)의 모든 구성 계열 검사 대상이다.

세 분할이 모두 있어야 한다. 동일 촬영·수행자·계열·파일 바이트가 분할을 건너가거나, 부모가 누락되거나, 파생 관계에 순환·식별 불일치가 있으면 차단한다. 표준 출력에는 항목별 건수만 기록하며 종료 코드는 통과 0, 발견된 문제 1, 입력 오류 2다. 기존 점수 분석은 별도로 참가자와 시행의 분할을 검사한다. 가짜 ID를 부여한 동일 바이트 복사와 교차 파생 관계를 합성 자료로 재현했다. 재인코딩한 뒤 부모를 누락한 자료나 사람의 실제 신원은 자동으로 확인할 수 없다. 새 평가 자료는 촬영 대장 대조와 유사 동작의 사람 검토가 필요하다.

## V05 로컬 발급 예산

격리 실험 서버 CLI는 세션 수명 중 발급을 기본 64회로 제한하며 `--max-issues-per-session`으로 조정한다. 이미 발급한 문제의 만료는 해당 세션의 예산을 복원하지 않는다. 동시 발급에서도 제한을 유지했고 별도 세션에는 독립 예산을 적용한다. 실험 라이브러리를 호출하는 기존 배치에는 예산을 선택적으로 적용한다. 이 범위는 서버가 발급한 세션이다. 브라우저 실험 페이지는 새 문제를 누를 때 새 세션을 만드는 기존 구조이므로 사용자별·계정별 한도에는 별도 세션 지속 정책과 gateway가 필요하다.

## N01 자료 노출 범위

두 checkout에서 로컬 refs의 도달 가능한 Git blob과 ZIP을 기존 검사기로 확인했다. 시작점에서 codex는 334 blob, handcaptcha는 283 blob과 ZIP 내부 7개를 읽었다. 두 검사 모두 지정된 자격증명 패턴 후보 0건이었다. handcaptcha 현재 트리의 기존 문제 manifest와 좌표 자료는 공개되어 있고, 추적 ZIP에는 영상 4개·JSON 2개·이미지 1개가 있다. 기존 자료를 미노출 평가군으로 사용할 수 없다. 파일의 상세 검사 결과와 해시는 로컬에 두었다. 도달 불가능한 이력·중첩 자료·영상 속 식별정보·동의 범위는 이 결과로 확정할 수 없다.

## T01–T24 증거 대응

아래 번호는 [v0.4의 인수 시험](../video_pool_occlusion_delivery_requirements_v0.4.md#15-필수-인수-시험)이다. 범위가 다른 국소 시험을 운영 합격으로 합산하지 않는다.

| ID | 확인한 증거 | 남은 인수 조건 |
|---|---|---|
| T01 | [registry 회귀][registry]에서 UNKNOWN·DENIED·연구전용 승격 거부 | 실제 신규 운영 자산의 권리 검토 |
| T02 | [로컬 응답 회귀][integration]에서 실험 페이지·미디어 경로 검사 | prod 응답 및 실제 배포 bundle 검사 |
| T03 | [렌더 회귀][mask]에서 누락·짧은 마스크로 출력 실패 | 최종 적용 경로 전체와 위치별 시험 |
| T04 | [렌더 회귀][mask]에서 미판정 프레임을 전체 분모에 포함 | 새 촬영 자료의 실제 결측 |
| T05 | [렌더 회귀][mask]에서 이미지 깊이가 래스터 좌표에 영향 없음 | 채택할 마스크·게이트 버전별 통합 검산 |
| T06 | [타임라인 회귀][timeline]에서 필터·역재생의 원본 프레임 대응 | 지원하는 변형 전부와 실제 자료의 PTS |
| T07 | [타임라인 회귀][timeline]에서 실패 후보 격리·manifest 제외 | 운영 인코더와 게시 경로에서 부분 실패 |
| T08 | [container와 rendition 검사][container] 및 FFmpeg 6개 재검사 | 각 최종 배포본의 전 프레임 마스크·PTS |
| T09 | [container 검사][container]에서 추가 track·poster 계열 제한 | 실제 페이지의 별도 poster·thumbnail·대체 rendition |
| T10 | [legacy 재편입 회귀][legacy] | 운영 후보 전체의 동일 기준 이행 |
| T11 | [비공개 전달 회귀][delivery] | 외부 origin 직접 접근과 실제 목록 차단 |
| T12 | [비공개 전달 회귀][delivery]에서 세션·만료 검사 | 운영 tenant와 실제 인증 연동 |
| T13 | [비공개 전달 회귀][delivery]에서 로컬 no-store | 실제 cache가 이미 채워졌을 때 권한 검사 |
| T14 | [Range/HEAD 회귀][delivery] 및 [브라우저 seek 기록][container] | 승인 세션에서 gateway까지 포함한 재생·재시도 |
| T15 | [비공개 전달 회귀][delivery]에서 원자적 1회 소비 | 운영 다중 worker·저장소에서 같은 조건 검증 |
| T16 | [로컬 회귀][integration]에서 client 판정 필드 거부 | 실제 보호 동작과 운영 verifier 연동 |
| T17 | [기존 알려진 풀 탐색](../g4_actual/g4_attack_matrix.md) | 신규 평가군과 사전등록 상한에 따른 판정 |
| T18 | 요구사항과 미실행 상태 확인 | 실제 대응 자료와 분석 결과 |
| T19 | [촬영·선별안](2026-11-10_rights_capture_screening_protocol.md) | 사전 잠금, 동의, 주석, 실제 사람 비교 |
| T20 | 이번 분할 사전검사에서 계보 충돌·바이트 중복 차단 | 실제 평가 자료와 재인코딩·유사 촬영 검토 |
| T21 | 서버 판정 경계 설계 | 정답을 제공하지 않는 화면에서 실제 사람 완료 검증 |
| T22 | [registry][registry]·[전달 회귀][delivery]에서 철회 후 접근 차단 | 실제 origin·cache와 철회 처리 연동 |
| T23 | [타임라인 회귀][timeline]에서 실패 후보 제외 | 운영 자산 고갈·장애에서 실제 대체 흐름 |
| T24 | [registry][registry] 및 [실행 계보](2026-11-10_session_artifacts_and_run_manifest.md) | 실제 release의 전체 증거 연결 및 독립 검토 |

[research]: https://github.com/mukgore/codex/commit/80a9c9e75f716c39ed14893d4cf5755b696c67fa
[hand]: https://github.com/mukgore/handcaptcha/commit/e21a974cd223236bccf2a647cba45f5c559f6430
[registry]: https://github.com/mukgore/handcaptcha/blob/e21a974cd223236bccf2a647cba45f5c559f6430/dataset_pipeline/tests/test_release_registry.py
[mask]: https://github.com/mukgore/handcaptcha/blob/e21a974cd223236bccf2a647cba45f5c559f6430/dataset_pipeline/tests/test_mask_delivery.py
[timeline]: https://github.com/mukgore/handcaptcha/blob/e21a974cd223236bccf2a647cba45f5c559f6430/dataset_pipeline/tests/test_timeline_candidate.py
[container]: https://github.com/mukgore/handcaptcha/blob/e21a974cd223236bccf2a647cba45f5c559f6430/dataset_pipeline/CONTAINER_RENDITION.md
[legacy]: https://github.com/mukgore/handcaptcha/blob/e21a974cd223236bccf2a647cba45f5c559f6430/dataset_pipeline/tests/test_legacy_bake.py
[delivery]: https://github.com/mukgore/handcaptcha/blob/e21a974cd223236bccf2a647cba45f5c559f6430/dataset_pipeline/tests/test_private_delivery.py
[integration]: ../../g4_lab/test_integration.py
