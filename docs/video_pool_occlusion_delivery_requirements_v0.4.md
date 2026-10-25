# 동작 영상 풀 확보·가림 생성·보안 송출 요구사항 v0.4

## 0. 문서 계약

- 목적: 충분한 동작 자료 확보부터 가림 생성, 품질·누출 검사, 세션 발급, 송출, 정답 검증 및 폐기까지의 설계.
- 분석 기준: handcaptcha 037873299a9e45435250aa158857b35e07668259, codex a4b18aa60873522f16f7be5ba5b463502b9a8365 및 작성 중 추가된 c0983ae0fddd8ba761ad73a459e7de836f318443까지의 자료 계보 기록.
- 이번 작업은 기존 코드 정적 검토와 요구사항 작성이다. 데이터 다운로드·신규 촬영·영상 생성·보안 시험·운영 배포는 수행하지 않았다.
- 이전 [실용성 검증 v0.3](practical_validation_requirements_v0.3.md) 및 [표준 채점 전환 v0.3](scoring_standardization_v0.3.md)에 추가한다.
- 코드 정적 결함 가능성, 직접 확인한 구조, 앞으로 검증할 가설을 구분한다. 현재 배포 영상이 실제 무가림 프레임을 포함한다고 단정하지 않는다.
- “안전한 송출”은 비밀 원본·정답의 불필요한 전달 차단, 전 프레임 가림 무결성, 세션 접근 통제, 검증된 공격 범위 내 저항을 뜻한다. 시청한 영상의 복제·추론을 완전히 방지한다는 뜻이 아니다.
- 기존 공개 자료 삭제나 이력 변경은 이번 범위에 포함하지 않는다.

## 1. 쉬운 설명과 핵심 결정

시험 문제를 많이 준비하되 답안지는 선생님만 갖는다.
검은 종이를 화면 위에 얹는 대신, 가릴 부분을 실제로 검게 바꾼 영상만 학생에게 보낸다.
한 장이라도 가리지 못했다면 그 문제를 내보내지 않는다.
문제의 번호·파일 이름·검은 원 움직임만 보고 답을 알아낼 수 있는지도 시험한다.
똑같은 문제를 계속 내면 답을 외울 수 있으므로, 몇 번 노출됐고 얼마나 쉽게 외워지는지 관리한다.

추천 출발 구조:
1. 권리가 명확한 직접 촬영의 작은 풀로 전체 파이프라인을 검증.
2. 원본·정답은 비공개 보관, 가림은 오프라인에서 미리 굽고 최종 MP4를 재검사.
3. 서버가 검증된 자산에서 문제를 선택하고 세션별 접근 권한을 발급.
4. 브라우저에는 가려진 영상과 재생 안내만 전달.
5. 입력의 진위와 정답 판정은 별도 서버/입력 보호 계층에서 확인.
6. 규모·반복노출 실험 후에만 사전 생성 변형 또는 요청 시 생성으로 확장.

영상 풀의 크기 자체를 보안성으로 대신하지 않는다.

## 2. 기존 방식 검토

아래 파일은 모두 분석 기준 handcaptcha commit에 존재한다. 링크는 18절에 있다.

| ID | 파일/함수 | 확인 결과 | 요구 조치 |
|---|---|---|---|
| AUD-01 | pool_manifest.json | custom01–08의 8개 clip, label·video_file·landmarks_file 공개, w3_new=null | 공개 manifest와 비공개 정답 manifest 분리 |
| AUD-02 | prod loadClipLandmarks / genSequence | 브라우저가 정답 landmark 파일을 fetch해 관문·채점에 사용 | 정답을 보내지 않는 서버 판정 구조 필요 |
| AUD-03 | prod genSequence | sort(() => Math.random()-0.5)로 선택, 2개 로드 실패 시 console 오류 중심 처리 | 서버의 안전한 무작위 배정, 부족하면 명시적 발급 실패 |
| AUD-04 | handtest1.py occlusion_params | 5개 지점 평균 M, C=W+q(M-W)/2, r=q||M-W||/2 | 기존 수식 baseline 보존 |
| AUD-05 | stage6 project_occlusion_circle | C=(P0+P9)/2, r=w3||P0-P9||/2 | 기존 방식과 다른 수식. 동일 이름으로 혼용 금지 |
| AUD-06 | stage7 + common | P0 등 다섯 단서 지점을 원 밖에 요구 | w3>1이면 중심-손목 거리보다 반경이 커 손목 조건과 충돌. 기존 test도 이 충돌을 기록 |
| AUD-07 | stage1 + geometry + stage6/7 | px의 x,y는 픽셀, z는 정규화 값인데 dist가 3차원 전부 사용 | 래스터 마스크 판정은 2D 픽셀로 통일 |
| AUD-08 | stage7 gate_clip | 미검출 프레임을 failing 목록에 넣지만 total에는 넣지 않음 | 전체 출력 프레임 분모, 미판정은 출하 차단 |
| AUD-09 | stage6 generate_occluded_video | 첫 유효 마스크 전에는 그대로 write, 이후에는 마지막 마스크 재사용 | 누락 프레임 fail-closed, 과거 마스크 자동 재사용 금지 |
| AUD-10 | stage2/4/6 | quality에서 frame 삭제, length_norm은 forward+reverse, renderer는 원본을 순서대로 읽음 | source_frame/PTS→output_frame 대응표 강제 |
| AUD-11 | pipeline.run_batch | stage7과 manifest는 생성하지만 실제 stage6 영상 renderer를 호출하지 않음 | manifest accepted와 배포 MP4 생성 완료를 구분 |
| AUD-12 | stage4/config | 5–6초 목표가 config에 있으나 초과 길이를 거부/보정하는 gate 없음 | 실제 PTS 길이 검증, 역재생은 신규 원본으로 세지 않음 |
| AUD-13 | stage5_weights | 배치 전체 open-hand 프레임의 median; 역재생 중복 포함 가능 | train source에서만 추정, 원본·촬영자 가중 균형, test 참조 금지 |
| AUD-14 | stage1 confidence / stage2 | multi_handedness의 score를 confidence로 quality에 사용 | 손 방향 분류 확신과 landmark 정확도를 분리 |
| AUD-15 | ingest_experiment_folders | legacy는 stage2/3/7 재검사 생략, 원본 landmark와 가림 MP4를 복사 | legacy 예외 폐지, 동일 출하 관문 적용 |
| AUD-16 | ingest import | dataset_pipeline.export_pool을 import하나 기준 tree에는 해당 파일 없음 | 실행 전 의존성 검사, 없으면 BLOCKED |
| AUD-17 | dataset_expansion_bake_v1.py | adopted_clips 입력, 동일 mask 활용, 역재생·H264 변환. !pip 포함 Colab 셀 형식 | CLI 패키징 별도, filter 생성기와 입력 계약 확인 필요 |
| AUD-18 | bake_occluded_video | missing mask의 last mask 재사용, 최초 누락 때 원본 write 가능 | 모든 출력 프레임 mask 확인, 누락 시 자산 전체 격리 |
| AUD-19 | bake reencode_h264 | 변환 뒤 프레임 1:1 유지한다고 주석으로 가정 | 재디코딩한 실제 프레임·PTS 검사 필요 |
| AUD-20 | config.py | 여러 기본값을 실제 자료 미검증 placeholder로 명시 | 실행값/근거/잠금 시점 기록. 확정 보안 기준으로 사용 금지 |

두 가림 수식은 실제로 다르다. 기존 방식은 연속 좌표상 손목이 원의 경계에 놓이고, 확장 방식은 w3>1일 때 손목이 안쪽에 놓인다.
정수 반올림·안전 margin까지 고려해야 하므로 “손목을 모두 원 밖에 둔다”는 gate를 어느 수식에나 그대로 붙이지 않는다.

현재 manifest가 확장 pipeline으로 만들어졌다는 실행 계보는 이 정적 검토에서 확인하지 않았다.
공개 저장소의 baseline/좌표/과거 파일은 공격자가 얻을 수 있다고 가정한다.
나중에 경로를 숨겨도 이미 노출된 자료의 비밀성이 회복됐다고 하지 않는다.

## 3. 요구사항 우선순위와 상태

- MUST: 출하/검증에 필요한 필수 조건.
- SHOULD: 비용과 위험에 따라 근거를 남기고 조정 가능.
- MAY: 후속 탐색 후보.
- 상태: NOT_STARTED / READY / COMPLETE / BLOCKED.
- 성능 결론: SUPPORTED / REFUTED / INCONCLUSIVE / NOT_TESTED.
- 설계 문서 COMPLETE와 보안 성능 SUPPORTED는 다르다.
- 각 요구사항에 owner_role, evidence_path, limitation, next_action을 연결한다.

## 4. POOL-01 — 자료 확보 경로와 권리

### 4.1 확보 우선순위

| 경로 | 장점 | 제약 | 채택 위치 |
|---|---|---|---|
| 직접 촬영 | 동작·카메라·원본 시간축·사용권 통제 가능 | 촬영·동의·검수 작업 필요 | 초기 운영 후보 우선 |
| Jester 공개 gesture 자료 | 큰 규모의 동작 후보를 빠르게 탐색 | 공식 제공 형태가 100px·12fps JPG 프레임이며 연구용 계약상 외부 송출·상업 운영 경로 아님 | 내부 연구 후보만 |
| IPN Hand / IPN HandS | 원본 RGB 영상과 일부 영상의 수동 보정 2D 손 좌표·구간 주석을 함께 검토 가능 | 공개 원본/좌표의 lookup 위험, 주석 시간축 차이, CC BY 표시·추가 권리 확인 | 공개 데이터 활용 파이프라인과 공격 비교 우선 후보 |
| InterHand2.6M | 3D GT·다중 카메라 등 기하 검증에 유용 | 상업 활용권 별도 확인, 동작 모방 문제와 과제 차이 | 좌표·가림 기하 검증 후보 |
| 상업 라이선스 영상/위탁 촬영 | 용도에 맞춘 권리와 규모 확보 가능 | 비용·계약·원본 좌표 필요 | 수요 확인 후 |
| 절차적 3D 손 생성 | 정답·다양성 생성 제어 가능 | 모델/자산 권리, 사람 수행성, 합성 특징, 렌더 비용 | 후속 실험 전용 |

권리 원문 조사:
- Qualcomm 공식 Jester 소개는 148,092개·27종·12 FPS·100px 품질을 안내한다.
- 확인한 Qualcomm 2022 연구용 계약은 내부 비영리 연구 범위를 정하며 외부 제공/상업 이용을 제한한다. 다운로드 가능함을 CAPTCHA 영상 송출 허가로 해석하지 않는다. 별도 계약이 있다면 그 적용 범위를 확인한다.
- InterHand 공식 저장소 LICENSE는 CC BY-NC 4.0을 표시한다. 데이터·코드·MANO 등 파생 자산 각각의 적용 약관을 확인해야 하며 상업 운영 풀로 자동 채택하지 않는다.
- 무료 서비스도 자동으로 연구용 허용 범위가 되는 것은 아니다.
- 현재 작업에서는 해당 데이터셋을 다운로드하거나 약관에 동의하지 않았다.

### 4.2 권리 대장

각 source는 owner/source URL, license/version, acquisition date, original checksum,
commercial_use, modification, public_delivery, redistribution, derived_artifact_conditions,
attribution, consent_record_id, withdrawal/retention 조건을 비공개 대장에 기록한다.
각 permission은 ALLOWED / DENIED / UNKNOWN이다.
운영 목적에 필요한 항목이 UNKNOWN/DENIED면 운영 풀 승격 차단.
코드 라이선스를 영상·사람 초상/촬영 동의에 대신 적용하지 않는다.
마스크를 씌우거나 좌표만 추출했다고 사용 제한이 사라진다고 가정하지 않는다.

### 4.3 직접 촬영 계약

- research-only와 service-delivery 동의를 구분한다.
- 얼굴·음성·불필요한 배경 식별정보를 기본 촬영 범위에서 제외한다.
- 공개 제공본과 원본 보관기간, 철회 요청 시 앞으로의 사용 중단 절차를 명시한다.
- 참여자 식별정보는 영상 manifest와 분리한다.
- 미성년 참여자의 촬영·동의 절차는 학교/연구자 절차를 확정한 뒤 모집한다.
- 공개 영상이 이미 복제됐을 수 있으므로 철회 시 모든 외부 사본 회수를 보장하지 않는다.

인수 기준: 운영 후보 100%의 권리 대장이 있고, UNKNOWN 항목이 release에 포함되지 않는다.

## 5. POOL-02 — 촬영 계획과 실질적인 다양성

### 5.1 작은 확보 실험부터

탐색 수집안: 촬영자 3명 × 동작군 10개 × 다른 take 2개 = 최대 60개 원본 후보.
이 수는 보안상 충분한 풀 크기가 아니라 확보·검수 비용을 재는 pilot 제안이다.
촬영자·동작군·독립 test 분할은 촬영 전에 고정하며, 같은 take의 반복은 독립 원본으로 세지 않는다.
v0.3의 30-source 탐색안과 동시에 독립적인 표본처럼 합치지 말고 하나의 split manifest로 조정한다.
3명으로 인구 집단 일반화를 주장하지 않는다.

촬영 조건 기본안:
- 하나의 손, 카메라 고정, 손끝/손목이 화면 경계 밖으로 사라지지 않는 구도.
- 720p/30fps는 시작 후보이며 실제 기기·저장 비용에 맞춰 결정. 실제 PTS를 보존한다.
- 손가락 접기·펴기·선택 손가락 움직임·순차 전환을 동작군으로 분류한다.
- 손목 통증·과도한 관절 가동을 요구하는 동작 제외.
- 좌우손·손 크기·조명·배경을 기록하되 실명/민감 속성 수집을 늘리지 않는다.
- 각 clip의 2–4개 의미 있는 자세와 전환 구간을 주석화하는 것은 탐색 시작안이다.
- 5–6초 길이는 강제 보안 기준이 아니다. 자연 수행시간과 전체 UX 목표를 보고 고정한다.

### 5.2 데이터 계보와 분할

source_id, source_family_id, capture_id, subject_code, gesture_family_id, take_id를 분리한다.
reverse/mirror/speed/crop/mask 변형은 parent source와 같은 split이다.
다중 시점의 같은 움직임도 같은 capture group에 묶는다.
sha256 중복, perceptual fingerprint, 정규화 동작 궤적 근접성으로 중복 후보를 찾고 사람이 확인한다.
공개 hash는 만들지 않고 내부 manifest에 보관한다.
비슷한 동작이 안전한 오답 구분을 무너뜨리는지 v0.3 V1 검사에 연결한다.

### 5.3 수량 보고

매 배치에서 다음을 구분한다.
입수 파일 수 / 고유 촬영 수 / 고유 source family / 동작군 수 /
기하 통과 수 / 사람이 수행 가능한 수 / 공격 시험 통과 수 / 운영 승인 수.
색상·배속·역재생 변형 100개를 고유 동작 100개라고 보고하지 않는다.
임의의 대형 목표를 먼저 정하지 않고 채택률과 clip당 검수·생성 비용을 측정한다.

## 6. POOL-03 — 데이터 구조와 상태 전이

### 6.1 서로 다른 네 저장 영역

1. raw: 원본 영상·동의·권리 기록. 비공개.
2. reference: 기준 좌표·관문·타임라인·정답·변환 계보. 비공개.
3. candidate: 가림 중간 산출물·마스크·검사 자료. 비공개.
4. release: 검사 완료한 가림 영상만. 저장소는 비공개, API를 통해 선택 자산만 송출.

Git 공개 영역은 코드·명세·합성 fixture·검토된 집계에 한정한다.
raw/reference를 프런트 정적 디렉터리 아래에 놓지 않는다.
파일명 난수화만으로 이 분리를 대신하지 않는다.

### 6.2 상태 전이

INGESTED → RIGHTS_CLEARED → QUALITY_CHECKED → MASKED →
ARTIFACT_VERIFIED → HUMAN_REVIEWED → SECURITY_EVALUATED → RELEASED.

실패/불확실: QUARANTINED, 더 이상 사용하지 않는 자료: RETIRED.
RELEASED로 건너뛰는 legacy/trusted 예외를 금지한다.
SECURITY_EVALUATED는 테스트 범위를 기록한 상태이지 안전 인증명이 아니다.
연구 전용 풀은 RESEARCH_ONLY로 구분하고 운영 release와 섞지 않는다.

### 6.3 비공개 source manifest

필수:
schema_version, source_id, source_family_id, capture_id, subject_code,
gesture_family_id, split, rights_record_id, origin_exposure(public/private/unknown),
input_hash, width, height, time_base, frame_count, duration, handedness,
extractor_version, coordinate_space, timeline_map_ref, source_status.

### 6.4 비공개 artifact manifest

artifact_id, source_ids, family_ids, transform_recipe_version, mask_policy_version,
recipe_seed_ref, frame_mapping_ref, frame_mask_ref, reference_version, scoring_version,
encoder_version/config, output_hash, decoded_frame_count, duration, codecs,
quality_report_ref, leakage_report_ref, rights_status, exposure_count, state, release_version.

### 6.5 브라우저 반환 스키마

challenge_id, media_url, expires_at, protocol_version, allowed_hand,
playback_segments(start_ms,end_ms), submission_url, max_attempts.

MUST NOT:
source_id, 원본 파일명, label/동작명, 정답 landmark, 관문 목표각,
원 중심·반경 배열, 원본/정답 hash, 생성 seed, 전체 pool 목록, 내부 storage key.
재생 구간 자체의 누출도 평가한다. 필요한 UI 안내 외 메타데이터는 보내지 않는다.
스키마 allowlist로 응답을 만들고 내부 manifest를 직렬화해 일부 필드만 지우는 방식을 피한다.

## 7. MASK-01 — 수학·타임라인 계약

### 7.1 수식 버전

M0_LEGACY: W와 [1,5,9,13,17] 평균 M으로 C=W+q(M-W)/2, r=q||M-W||/2.
M1_MIDPOINT: C=(P0+P9)/2, r=w3||P0-P9||/2.
두 수식을 버전으로 분리하고 정답/마스크 manifest에 기록한다.
새 q/w3는 개발 source에서만 선택하며 좌우·손 크기·투영에 대한 적용 범위를 기록한다.

### 7.2 2D 판정

가림 중심·반경·거리·pixel raster는 동일한 2D 픽셀 좌표계에서 계산한다.
world 3D를 사용한 비율 추정이 image 2D 투영에 그대로 맞는다고 가정하지 않는다.
정수 중심/반경 변환 및 border clipping 후의 실제 래스터 mask를 대상으로 검사한다.
유한하지 않은 좌표, 음수/0 반경, 화면 밖 마스크, 퇴화 손 크기는 실패다.
얼굴 자세 임계값 등 다른 과제의 숫자를 손 가림 검증값으로 전용하지 않는다.

### 7.3 원본-출력 정렬

모든 출력 frame에 output_frame_idx, output_pts, source_frame_idx, source_pts,
transform_id, reference_index, mask_status를 연결한다.
quality filter가 프레임을 버리더라도 배열 압축 인덱스로 원본 영상을 읽지 않는다.
reverse/시간변형은 영상·마스크·정답·관문 시각에 동일하게 적용한다.
재인코딩 뒤 실제 PTS로 다시 검사하며 FPS 메타데이터만 믿지 않는다.
mask/source/frame count 불일치 시 출력을 격리한다.
개발용 기본 FPS fallback은 표시 가능하지만 운영 자산 승격에서는 시간 근거가 필요하다.

## 8. MASK-02 — 가림 후보 및 선택 방법

| 후보 | 의도 | 필수 반증 검사 |
|---|---|---|
| M0 기존 동적 원 | 연구 baseline | 원 궤적·피부-bit·lookup |
| M1 중점 원 | 확장 코드 비교 | 손목 외부 gate 충돌 및 실제 가림 범위 |
| M2 정규화된 손 배치 + 고정 마스크 | 동작에 따라 변하는 원 정보 감소 | 손 이동/배경 변환의 새 단서, 사람 난도 |
| M3 제한된 파라미터 변형 | 정적 영상 직접 매칭 저감 후보 | 변형 제거 후 매칭, 반복 노출 복원 |
| M4 사전 검증된 복수 마스크 | 다양성 후보 | 서로 다른 노출 영역을 합쳐 정답 복원하는 공격 |

어느 후보도 채택 완료로 취급하지 않는다. 기존 고정 원 비교에서 효과가 입증되지 않았음을 명시한다.
M2 실험에서 원뿐 아니라 손 크기·좌표까지 바뀌면 분리된 변수로 보고한다.
무작위로 가린다는 사실은 보안 근거가 아니다.
마스크 파라미터가 목표 관절 위치를 너무 직접적으로 나타내는지 평가한다.
같은 원본의 여러 마스크를 제공하면 여러 영상의 합성으로 숨긴 손이 드러날 수 있으므로, 변형 수 증가를 무조건 보안 강화로 세지 않는다.

선택은 가림 정확도 + 정상 사람 완료율 + 가장 강한 허용 공격의 전체 성공률 +
반복노출 성능 + 생성/송출 비용의 공동 비교로 한다.
MediaPipe 단일 검출 실패는 보조 지표일 뿐 출시 합격 기준이 아니다.

## 9. MASK-03 — 가림 적용과 출하 검사

### 9.1 굽기

- 원본 decode → 복사 프레임 → 2D mask 픽셀 치환 → 새 영상 encode.
- CSS overlay, canvas 표시 덧씌우기, 원본+mask 동시 다운로드는 운영 경로에서 금지.
- 원본 트랙, 별도 무가림 썸네일/poster, 첨부 이미지, 미사용 비디오 트랙, 오디오, 자막, 원본 파일명 metadata를 포함하지 않는다.
- 모든 출력 프레임에 검증된 마스크가 있어야 한다.
- 최초/중간/마지막 mask 누락 시 clip 전체 격리. 기본 정책은 원본 write나 last mask 유지가 아니다.
- 복구 후보는 원본에서 다시 추정하고 전 프레임 검사를 통과한 새 artifact로 만든다.
- 인코더 미설치·코덱 실패·출력 0바이트·열기 실패는 실패다. 경고만 출력하고 배포하지 않는다.
- 변경 중 파일은 release에 노출하지 않는다. 임시 파일 검사 후 immutable artifact로 원자적 등록.

### 9.2 기하 gate와 보안 gate의 구분

기하 gate:
- 가릴 ROI와 보일 ROI를 문서화한다. 세 landmark 지점은 관절 면적 전체의 검증을 대신하지 못한다.
- 기존 P0 포함 외부 조건과 수식 충돌을 먼저 해결한다. “통과 영상이 나오게” gate만 약화시키지 않는다.
- 실제 이미지에서 목표 부위를 가리는지 검수 표본과 주석을 통해 확인한다.
- 분모는 전체 출력 프레임. failed/unknown=0이어야 출하 가능.
- 판정 불가능 프레임을 제외한 100%를 전체 100%라고 쓰지 않는다.

보안 gate:
- 공개 가능한 가림 영상만으로 원본/정답을 찾는 공격, 생성 규칙의 누출, 반복노출을 V2에 따라 평가.
- 기하를 통과했어도 공격 통과 상한을 넘으면 운영 후보에서 제외.
- 보안 상한은 사전등록된 프로토콜 값이며 이 명세가 임의 숫자를 만들지 않는다.

### 9.3 최종 MP4 재디코딩

MP4를 처음부터 끝까지 decode하여 frame count, PTS 단조성, 해상도, duration, mask ROI를 검사.
인코딩 전 원본이 아닌 마스킹된 프레임만 인코더에 들어가는지 확인.
codec 때문에 mask 경계 색이 달라질 수 있어 “순수 검정 픽셀만 허용” 대신 기대한 마스킹 래스터와 보수적 내부 ROI를 비교한다.
허용 오차·경계 margin은 codec 검증 fixture로 정하고 실제 영상을 보고 임의 확대하지 않는다.
첫/끝 프레임·seek·역재생 경계·전환 구간을 반드시 확인한다.
모든 렌디션/포스터/썸네일/재인코딩본은 별도 검사 대상이며, 검증 전 사본을 CDN이 자동 생성하지 않게 한다.

## 10. SERVE-01 — 구조 선택

| 방식 | 비용/구현 | 평가 |
|---|---|---|
| 기존 정적 GitHub Pages + 정답 JSON | 구현 간단 | 공개 연구 데모만. 운영 보안 경계 아님 |
| 오프라인 굽기 + 비공개 저장 + 서버 발급 | 요청 시 계산 적음 | 초기 권장 |
| 사전 생성한 변형 여러 개 | 저장·검수 증가 | 반복노출/복원 시험 후 도입 |
| 요청 시 동적 마스킹/인코딩 | 요청당 연산·대기·DoS 부담 | 파일럿에서 비교, 운영 채택은 효과·비용 검증 후 |
| 브라우저가 원본을 받아 가림 | 전송 후 원본 회수 불가 | 운영 경로 부적합 |

처음에는 CPU 기반 로컬 준비 + 격리된 테스트 서버로 검증한다.
무료 호스팅을 확정하거나 구매하지 않는다.
서명 URL·CDN은 공급자 선택 전의 인터페이스 요구사항이다. 무료 계층이 비공개 저장·서버 실행을 지원하는지 별도 확인한다.

권장 데이터 흐름:
원본 비공개 보관 → 좌표 추출/검수 → 가림 굽기 → 최종 파일 검사 →
비공개 가림 자산 → challenge 발급 서버 → 브라우저.
기준 좌표는 reference 저장소 → 검증 서버로만 이동한다.

### 10.0 원본 확보·변형·가림의 대안 비교

아래의 '그대로'는 **원본 동작·구도·시간축을 유지하고 필수 가림은 적용**한다는 뜻이다.
무가림 원본 영상을 브라우저에 그대로 보내는 운영안은 아니다.
원본이 이미지 연속 프레임인 경우에도 반드시 MP4 한 개로 저장해야 하는 것은 아니다.
최종적으로 브라우저가 받는 것은 검증된 가림 픽셀로부터 만든 재생 가능한 바이트여야 한다.

| 후보 | 준비 단계 | 사용자 요청 시 | 장점 | 핵심 검증 |
|---|---|---|---|---|
| A. 원본 그대로 선택 → 미리 가림·인코딩 | 권리 확보, 좌표·구간 추출, 가림본 1회 생성·검사 | 검증 자산 선택·송출 | 구현·전체 출력 검사 단순 | 반복 관측과 공개 원본 매칭 |
| B. 원본에 소폭 변형 → 미리 가림·인코딩 | crop/scale/밝기 등 허용 변형의 한정된 산출물을 사전 검사 | 변형 중 승인된 것 선택 | 재생 지연 작음 | 좌표 동기화·변형 제거 매칭·여러 가림본 합성 |
| C. 비공개 원본에서 요청 시 선택·변형·가림 → 인코딩 송출 | 원본·기준 좌표와 안전한 변형 범위 준비 | 서버 decode, 변형, 좌표 변환, 가림, 인코딩, 검사 후 출력 | 자산별 MP4 사전 생성·저장 감소 | 시작 지연·동시성·완료 전 누출·인코더 비용 |
| D. 구간/프레임 단위 가림 결과 캐시 | 권리·좌표·세그먼트 검증 및 캐시 키 설계 | 없는 부분만 서버 생성, 검증된 부분만 재사용 | 수요가 몰리는 원본만 계산·저장 | 캐시 누출·시간축·구간 경계·미검사 바이트 |
| E. 가림된 프레임을 서버에서 인코딩·분할 송출 | 프레임별 마스크/상태·포맷/플레이어 구현 | 작은 묶음씩 가림→검사→인코딩→전송 | 완성 MP4 파일을 남길 필요 없음 | 묶음별 재디코딩·재생 호환·지연·전송비 |

D/E도 영상 인코딩·전송 비용이 사라지는 방식은 아니다. 브라우저에 raw video,
원본 프레임, 좌표·마스크를 넘겨 브라우저에서만 덮는 방법은 비밀 원본 보호 요건을 충족하지 못한다.
A/B와 C/D/E는 배타적이지 않다. 첫 접근에 C로 생성·검사하고 합격 결과를
사설 캐시에 저장해 다음 접근에는 A처럼 제공하는 정책도 비교한다.
다만 한 번 검사한 MP4와 다르게 C/D/E는 매 요청의 **최종 송출 바이트**까지
가림이 유지되는지를 출하 전 검사해야 한다. 검사가 끝나지 않은 출력 chunk를 먼저 flush하지 않는다.

원본을 선택·변형할 때의 계약:
- 공개 데이터셋 여부, 받은 판본/해시, 원본의 촬영자·동작군·공개 노출을 기록한다.
- dataset class label만으로 프레임별 손 관절 정답을 갖췄다고 가정하지 않는다.
  필요한 좌표·관문은 추출/검수하여 원본 frame/PTS에 결합한다.
- crop/scale/flip/속도/구간 선택 시 영상·좌표·가림·정답·재생 시각에 같은 변환을 적용한다.
  좌우 반전으로 지시 손/동작 의미가 바뀌면 별도 문제로 재검증한다.
- 밝기·압축·색 변화는 배경 단서 제거에 도움이 되는지 시험하되
  동작을 새로 만들거나 정답 entropy를 늘렸다고 세지 않는다.
- 사용권은 원본 취득, 가림·변형, 외부 사용자에게 파생 영상 송출,
  상업 사용, 표시·출처 조건을 각각 확인한다.
- 공개 원본/손 좌표를 공격자가 확보한 closed-set nearest-neighbor 매칭을 기본 공격으로 포함한다.
  변형본을 얼마나 쉽게 원본과 다시 연결하는지와 사람 수행률을 함께 측정한다.

우선 파일럿: 같은 권리 확인 영상 표본으로 A, B(소폭 변형), C(요청 시)를
동일한 좌표·마스크 정책으로 구현해 비교한다. 요청 수·동시성 구간별
원본당 준비시간, 첫 프레임 p95, CPU/메모리, 저장·송출량, 실패·미가림 프레임 수,
정상 사람 완료율, 공개 원본 매칭 성공률을 기록한다.
미가림 출력은 0건이어야 하며, 그 외 수치의 합격선은 실험 전에 정한다.
C가 실질적 보안 이득 없이 비용과 지연만 늘리면 A 또는 선택적 캐시를 채택한다.
A의 반복노출이 목표를 깨고 C도 공개 원본 매칭을 막지 못하면 원본 확보 전략을 바꾼다.

데이터셋 조사 우선 후보:
- Jester: 148,092개 동작 클립이라는 탐색 장점이 있으나 공식 배포는
  100px/12fps JPG 연속 프레임이며 공식 연구용 계약은 내부 연구만 허용한다.
  이를 MP4 원본 라이브러리나 상업 송출 권한으로 가정하지 않는다.
- IPN Hand: 공식 설명은 640×480/30fps RGB 연속 동작 영상이다.
  공식 저장소는 영상·주석을 CC BY 4.0으로 표시한다.
  IPN HandS는 200개 영상의 손 좌표와 구간 주석을 제공하며,
  배포 프레임 인덱스와 원본 영상 타임라인 차이를 명시한다.
  저작자 표시 방식, 인물·촬영 동의, 운영 목적과 계약 적용은 별도 권리 검토 대상이다.
  공개 원본·좌표를 전제한 공격을 통과했다는 뜻은 아니다.

### 10.1 MP4 생성 주기와 재사용 경계

기본 운영 경로에서는 세션마다 MP4를 생성하지 않는다. 영상 source를 처음 편입하거나
마스크 정책·인코더·원본을 변경할 때 오프라인으로 가림 영상을 한 번 생성하고,
전체 프레임 검사에 합격한 불변 MP4를 여러 세션에 제공한다.
매 세션에는 서버의 자산 선택, challenge 발급, 짧은 수명 접근권과 검증 기록만 새로 생성한다.
동일 byte가 반복 제공될 수 있다는 점을 공격 모델에 명시한다.

| 사건 | MP4 생성 | 요청 시 수행 |
|---|---|---|
| 새로운 source 촬영·편입 | 1회 굽기·검사 | 없음 |
| 마스크/인코딩 버전 변경 | 해당 자산 새 버전 굽기·검사 | 이전 버전 발급 종료 |
| 일반 사용자의 challenge 요청 | 생성 없음 | 승인된 자산 선택·접근권 발급 |
| 같은 session의 seek/range/retry | 생성 없음 | 같은 승인 자산의 일부 바이트 재송출 |
| source를 폐기하고 새 영상 충원 | 새 source만 굽기 | 폐기 자산 발급·접근 종료 |

비용 모델을 분리한다:
C_offline = source당 추출 + 마스킹 + 인코딩 + 재디코딩 검수.
C_request = 발급 + 인증 + 미디어 전송 + 검증.
한 자산이 실제 N회 쓰이면 준비비 평균은 C_offline/N이지만,
같은 N이 커질수록 답안집 구성/매칭 공격 비용은 낮아질 수 있다.
운영 적정 N을 임의로 정하지 않고 V2 공격 성공률과 인간 완료율, 갱신비를 함께 측정한다.

### 10.2 세션마다 달라 보이게 할 필요가 생기면

1. 먼저 여러 **서로 다른 원본 source**를 확보하고 발급 분포와 노출 상한을 설계한다.
2. 다수 변형이 도움이 되는지 검증되면 제한된 변형만 미리 굽고 각각 검사한다.
   원본 하나에서 나온 모든 변형은 동일 family로 계산하며, 영상별 저장비와
   서로 다른 mask의 노출 부분을 합칠 수 있는 위험을 함께 기록한다.
3. 검증된 가림 구간 파일을 순서대로 제공하는 방식은 파일별 검수를 줄일 수 있지만,
   각 구간의 독립 식별, 재생 간격, 구간 조합을 통한 답 복원, 서버 판정 동기화를
   새 공격면으로 평가한 뒤에만 채택한다. 완성 조합마다 MP4를 굽는 것은 기본값이 아니다.
4. 요청 시 동적 인코딩의 **운영 채택**은 동일 준비 자산의 반복 노출이 실제로 문제가 되고,
   사전 생성·회전만으로 목표를 맞추지 못했을 때만 검토한다.
   이 경우에도 원본 프레임을 클라이언트에 보내지 않고 서버에서 가림·검증하며
   요청당 CPU·p95 시작 지연·동시 처리·장애 시 fail-closed를 측정한다.

사전 변형의 수가 늘어도 한 원본의 정답과 보이는 손 움직임이 공유되면
보안상 독립 문제의 수는 증가하지 않는다. CDN이나 서명 URL도 반복 관측을 방지하지 않는다.

## 11. SERVE-02 — challenge 발급·수명·재생

### 11.1 발급

POST /v1/challenges
- 입력: tenant/site ID, 보호 action, 허용된 사용자 옵션. client가 source ID를 고르지 않는다.
- 서버: 요청 제한 → 승인 pool version 선택 → 호환 source 선정 → 참조/재생 변형 잠금 →
  challenge ID 발급 → session/action/tenant 바인딩 → expiry·시도 수 저장.
- CSPRNG 기반 예측 불가능 ID를 사용한다. 구현 시작안은 128bit 이상 난수이며 보안 entropy와 영상 정답 entropy를 혼동하지 않는다.
- 선택에는 unbiased sampling을 사용한다. Math.random sort를 보안 배정에 사용하지 않는다.
- 부족한 pool·만료된 release·권리 미확인·검사 누락이면 발급 거부/대체 경로로 처리한다.
- 실패 시 원본이나 미검수 영상으로 fallback하지 않는다.
- actor별 반복 회피는 전역 고갈 방지와 함께 설계한다. 여러 계정/IP 우회를 고려해 전역 노출도 제한한다.

### 11.2 상태

ISSUED → ACTIVE → SUBMITTED → VERIFIED 또는 FAILED.
ISSUED/ACTIVE는 EXPIRED/REVOKED로 갈 수 있다.
최종 인증 권한은 원자적으로 CONSUMED 처리한다.
동시 제출 두 건이 모두 보호 동작을 허용하지 않도록 데이터베이스 조건부 갱신으로 제어한다.

### 11.3 media endpoint

GET /v1/challenges/{id}/media
- 만료·세션·tenant·artifact release 상태를 확인하고 가림 MP4만 반환.
- 미디어 읽기는 byte-range/seek/재시작 때문에 여러 번 허용할 수 있다.
- “미디어 첫 GET 한 번”과 “인증 권한 일회성 소비”를 혼동하지 않는다.
- 만료 시 이후 읽기를 차단하더라도 이미 다운로드한 바이트는 회수할 수 없다.
- URL 난수화·짧은 TTL은 대량 수집 비용 통제이며 영상 복사 방지 보장이 아니다.

### 11.4 짧은 수명 링크와 캐시

초기 구현은 같은 origin의 인증된 media proxy로 단순화할 수 있다.
CDN 도입 시:
- private origin 직접 접근 차단.
- viewer 요청마다 서명/세션 정책 검사. 캐시 적중도 접근 통제를 건너뛰지 않음.
- 인증 결과와 challenge 응답은 no-store. 자산 CDN 캐시와 사용자별 응답 캐시는 구분.
- 공용 URL 객체와 private 자산 key를 분리.
- 서명 URL은 bearer credential일 수 있으므로 URL만 공유해도 접근 가능한 범위를 기록.
- 진정한 session binding이 필요하면 쿠키/edge 검증을 구현·시험하고 서명만으로 있다고 주장하지 않음.
- CORS/Referer 검사만으로 권한 검증을 대신하지 않음.
- URL·토큰·정답은 분석 이벤트, referrer, 공개 로그에 남기지 않음.
- 객체 폐기 시 origin과 CDN을 함께 처리하고 활성 challenge는 REVOKED로 전환.

AWS 공식 자료는 signed URL/cookie 접근 제어와 origin 우회 차단을 별도 계층으로 설명한다.
여기서는 구조 참고용이며 AWS 도입/과금 승인이 아니다.

## 12. SERVE-03 — 기존 prod를 바꾸어야 하는 지점

| 기존 | 목표 |
|---|---|
| 전체 pool_manifest fetch | 현재 세션의 최소 challenge 응답 |
| landmarks_file fetch | 서버 reference 조회 |
| 클라이언트 목표각 기반 gate | 서버 gate 또는 검증된 보호 SDK의 판정 |
| 클라이언트 computeScores passed | 서버 판정 및 일회성 보호 동작 권한 |
| 화면에 clip ID/frame 번호 | 필요한 진행 안내만 |
| guide/ghost에 목표 정보 사용 가능성 | generic guide와 실제 정답 누출 여부 검사 |
| 임의 client 시간과 phase | 서버 세션 수명 + 신뢰도 구분된 client 이벤트 |

중요한 구현 선택:
- 기존 UX처럼 중간 자세를 실시간으로 확인하려면 서버로 손 특징을 보내거나 검증된 입력 SDK가 필요하다.
- 좌표만 서버로 보내도 출처는 조작 가능하다. 이는 계산 위치 이전이지 신뢰받는 카메라 증명이 아니다.
- 영상 전송은 서버 추론·지연·개인정보 비용이 늘어난다. 두 방식을 별도 입력 신뢰성 조건으로 비교한다.
- 원본 정답을 client에 다시 내려보내 UX를 복구하면 정답 비공개 목표는 실패다.
- WebSocket 등을 쓸 경우 세션 결합·순서·재전송·시간 제한을 명시한다.
- 자세 근접도·세부 점수의 실시간 반환은 탐색 oracle이 될 수 있다. 최소 진행 신호, query 한도, 실패 응답 정책을 정한다.
- 입력 보호 없이 운영 가능한 보안 제품이라고 결론 내리지 않는다.

## 13. POOL-04 — 재사용·수집·답안집 공격

원본과 가림 영상을 구분한다. 원본 공개 데이터셋을 쓰면 공격자도 원본을 가진 조건을 필수 포함한다.
서버에서 정답을 숨겨도 공개 원본과 가림 영상의 매칭이 쉬우면 비용 비대칭이 성립하지 않을 수 있다.

필수 공격 비교:
1. 기존 공개 8개 원본/정답을 아는 closed-set lookup.
2. 새 source를 모르는 held-out 추론.
3. 동일 자산 반복 노출 후 cache/replay.
4. 다른 crop/mirror/speed/배경 변형을 제거한 유사 영상 매칭.
5. 원 중심/크기만, 피부-bit만, 파일 길이/재생 구간만 쓰는 식별.
6. 같은 원본의 다른 마스크들을 시간 정렬해 보이는 영역을 결합.
7. 공개 원본 데이터셋에 대한 nearest-neighbor 검색.
8. 정상 사용자를 흉내 내며 challenge만 대량 발급받는 수집. 자체 격리 시스템에 한정.

측정:
budget별 고유 family 회수율, top-1/top-k, 잘못 찾은 답의 점수/gate/L3 통과,
한 문제당 추가 수집 비용, 준비비 상각, 반복노출 이후 공격 성공률.
영상 수 N에서 k개를 조합한 경우 N의 순열 수를 그대로 보안 공간으로 쓰지 않는다.
각 요소가 개별 식별되면 조합의 답도 쉽게 재구성될 수 있다.

운영 노출:
- artifact/source family별 발급·실제 전송·제출 수를 구분.
- pool별 exposure ceiling, rotation cadence, per-session query/retry, 전역 수집 한도를 실행 전에 정한다.
- 오래 쓴 자산의 교체는 무효화/새 family 충원과 함께 한다.
- TTL/횟수 상한은 용도·접근성·미디어 크기·트래픽에 따라 결정하며 아직 확정하지 않는다.
- 파일이 바뀌어도 같은 답이면 새로운 보안 자산으로 세지 않는다.
- 새 원본 충원 속도보다 공격자의 학습이 빠르면 풀 기반 방식을 재검토한다.

## 14. 비용·성능·운영 기록

측정 단위:
- 입수 원본 1개당 촬영/권리/주석 시간.
- 통과 자산 1개당 추출/굽기/재검사 CPU 시간.
- 후보 대비 release 수율.
- 서버 발급 p50/p95, 최초 프레임 표시시간, 전체 전송량.
- 재생 실패·seek 실패·만료 중단률.
- 서버 gate 왕복지연과 사람 완료시간.
- 월간 저장량·송출량·검증비·지원비·풀 갱신 작업량.

공식:
usable_yield = release_family_count / acquired_family_count
cost_per_released_family = 총 확보·검사 비용 / release_family_count
monthly_media_bytes = 실제 media 요청별 전송 byte 합
월 전체비용 = 확보 상각 + 저장 + 송출 + 검증 + 유지보수.

출시 자산이 0개면 비용을 0으로 쓰지 않고 생산 실패/분모 없음으로 표시한다.
가림 연산 자체가 싸더라도 사람 검수와 비공개 서버 운영이 비쌀 수 있다.
v0.3 V5의 공격 비용과 고객 순가치에 이 비용을 연결한다.

## 15. 필수 인수 시험

아래는 구현 시 수행할 시험이며 이번 문서 작성에서 실행한 결과가 아니다.

| ID | 시험 | 통과 조건 |
|---|---|---|
| T01 | 권리 UNKNOWN source 편입 | 운영 release 거부 |
| T02 | 공개/비공개 manifest 검사 | 브라우저 응답·bundle에 정답/전체목록 없음 |
| T03 | 첫·중간·끝 mask 누락 | 자산 격리, 원본 프레임 송출 없음 |
| T04 | 검출 불능 1프레임 | 전체 분모에 포함하고 출하 차단 |
| T05 | x,y 동일·z만 다른 입력 | 래스터 가림/2D gate 동일 |
| T06 | 프레임 삭제·역재생·시간변형 | 영상/정답/mask 타임라인 일치 |
| T07 | encoder 실패·부분 파일 | manifest RELEASED 생성 금지 |
| T08 | 최종 MP4 전체 decode | PTS·frame·mask 기대값 일치 |
| T09 | poster/thumbnail/다른 트랙 | 무가림 사본 없음 |
| T10 | legacy 재편입 | 동일 gate 실행, 자동 통과 예외 없음 |
| T11 | origin 직접 접근/목록 열람 | 비공개 자산 접근 거부 |
| T12 | 만료/다른 session/tenant 접근 | 정책대로 거부 |
| T13 | 캐시 warm 상태 무권한 요청 | 영상 반환 없음 |
| T14 | Range/seek/retry | 승인 세션에서 정상 재생, 제한 우회 없음 |
| T15 | 토큰 재사용·동시 submit | 보호 동작 1회만 허용 |
| T16 | client passed/score 변조 | 서버 허용에 영향 없음 |
| T17 | 원본 공개 lookup | 사전등록 공격 상한 충족 또는 후보 탈락 |
| T18 | 다중 마스크 합성 공격 | 결과/한계 기록, 미실행이면 통과 주장 금지 |
| T19 | 사람 조건 대응 비교 | 가림의 추가 효과와 허용 UX를 함께 만족 |
| T20 | source/capture split | 파생본·촬영자 연결에 의한 test 누출 없음 |
| T21 | 정답/landmark fetch 차단 후 UX | generic guide·서버 gate로 과제 완료 가능 |
| T22 | retired/revoked 자산 | 새 발급 금지 및 접근 정책 반영 |
| T23 | 후보 풀 부족/서버 장애 | 원본 공개 fallback 없음, 대체 흐름 명시 |
| T24 | 전체 증거 추적 | release의 코드/입력/권리/검사 버전 연결 |

T03–T08은 기계적 무결성, T17–T19는 경험적 보안·사용성이다.
전자가 통과했다고 후자도 통과한 것으로 표시하지 않는다.

## 16. 작업 패키지와 완료 순서

### WP0 기존 방안 감사 — 이번 문서의 범위

정적 증거 표, 수식 차이, 정답 공개 구조, 기존 pipeline 연결 공백, 권리 원문을 기록한다.
현재 영상 픽셀이나 실제 배포 보안이 검증됐다고 쓰지 않는다.

### WP1 확보·스키마

권리 대장, 촬영안, source family 분할, manifest schema, 합성 fixture를 작성.
외부 자료 사용 승인 없이 대량 다운로드하지 않는다.
필수 산출: rights_inventory, capture_protocol, split_manifest(비공개), schemas.

### WP2 오프라인 생성기 정비

누락 fail-closed, 2D 좌표, frame/PTS mapping, recipe version, 영상 굽기 연결, 재디코딩 검사.
기존 수식 baseline과 후보를 분리하며 기존 결과를 덮어쓰지 않는다.
필수 산출: build command, immutable artifact manifest, T03–T10 결과.

### WP3 가림·풀 공격 평가

권리·기하 검사 통과 자료로 v0.3 V1/V2/V4/V5 수행.
새 표본이 없으면 known-pool 회귀까지만 수행, held-out은 BLOCKED.
필수 산출: human/attack/cost 비교와 release 후보 목록.

### WP4 격리 송출·서버 판정 설계/구현

private store, challenge API, media authorization, server gate, protected test action.
실제 정답 없는 client가 동작하는지 검증.
필수 산출: API schema, threat model delta, T11–T16/T21–T24.

### WP5 제한 시험·운영 결정

승인된 환경에서 전체 경로·반복노출·풀 고갈·대체 UX 검증.
고객 수요와 경제성 없이 대형 데이터 구매/유료 CDN 도입을 먼저 하지 않는다.
필수 산출: release decision, 운영 조건, 폐기/복구 절차.

후속 구현이 승인되면 해당 범위 안의 의존 작업은 연속 진행한다.
자료/도구 부족은 항목별 BLOCKED로 남기고 독립 가능한 일을 계속한다.
이번 요청 자체로 참여자 모집·기업 연락·유료 결제·외부 배포를 실행하지 않는다.

## 17. 산출 경로 및 판정

향후 경로(현재 존재한다고 가정하지 않음):
- docs/pool_v04/audit.md, capture_protocol.md, release_policy.md, api_contract.md
- schemas/pool_v04/ : source/artifact/challenge JSON schema
- analysis/pool_v04/ : 검수·누출·비용 집계
- tests/pool_v04/ : 합성 fixture 및 인수 시험
- reports/pool_v04/<run_id>/ : 비식별 집계
- data/work/pool_v04/ : 비공개 원본·권리·mask·reference·source manifest

최종 결정:
- 원본/정답 노출 또는 mask 누락 → 운영 후보 차단, 구현 수정.
- 기하 gate가 모순돼 수율 0 → 수식/조건 정의 재검토, 통과 기준 몰래 완화 금지.
- 공격을 낮추지만 사람이 수행 못함 → 후보 탈락 또는 적용 범위 축소.
- 공개 원본 lookup/누적 노출이 싸게 성공 → 해당 source/풀 전략 재설계.
- 기술 통과·운영 비용 초과 → 배포 구조/대상 사용처 재검토.
- 자료·권리·실험 부족 → 판단 보류.
- 모든 관련 관문 충족 → 해당 버전/위협 모델/기간에 한정한 제한 시험 가능.

## 18. 출처 및 추적

### 저장소 고정 버전

아래는 정적 확인한 구현의 근거다.
- [handcaptcha prod](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/hand_captcha_prod.html)
- [pool manifest](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/pool_manifest.json)
- [기존 가림 수식](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/handtest1.py)
- [pipeline](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/dataset_pipeline/pipeline.py)
- [stage1](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/dataset_pipeline/stage1_extract.py)
- [stage2](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/dataset_pipeline/stage2_quality.py)
- [stage4](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/dataset_pipeline/stage4_length_norm.py)
- [stage5](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/dataset_pipeline/stage5_weights.py)
- [stage6](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/dataset_pipeline/stage6_occlusion.py)
- [stage7](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/dataset_pipeline/stage7_gate.py)
- [geometry](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/dataset_pipeline/geometry.py)
- [수식 충돌 회귀 test](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/dataset_pipeline/tests/test_stage7_gate.py)
- [legacy ingest](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/dataset_pipeline/ingest_experiment_folders.py)
- [별도 굽기 스크립트](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/dataset_expansion_bake_v1.py)

### 공식 외부 자료

- [Qualcomm Jester 소개](https://www.qualcomm.com/developer/software/jester-dataset)
- [IPN Hand 공식 프로젝트](https://gibranbenitez.github.io/IPN_Hand/)
- [IPN Hand 데이터·주석 라이선스 안내](https://github.com/GibranBenitez/IPN-hand#license)
- [IPN HandS 좌표·시간축·라이선스 안내](https://github.com/GibranBenitez/IPN-hand/blob/master/README_HandS.md)
- [Qualcomm Research Use 계약](https://www.qualcomm.com/content/dam/qcomm-martech/dm-assets/documents/jester_something_something_exercise_research_license_final_qti_28jul2022.pdf)
- [InterHand2.6M 공식 데이터 설명](https://mks0601.github.io/InterHand2.6M/)
- [InterHand 저장소 LICENSE](https://github.com/facebookresearch/InterHand2.6M/blob/main/LICENSE)
- [AWS private content 및 origin 접근 제한](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-overview.html)
- [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)

라이선스는 확인한 공개 원문 기준이며 실제 취득 때 적용되는 계약 버전을 권리 대장에 저장한다.
외부 문서는 구조·권리 확인의 근거이지 이 CAPTCHA 보안 성능의 검증 결과가 아니다.

추가 자료 계보: [로컬 source map 후보](reproducibility/local_source_map_candidate_2026-10-26.md)의 sessionLog 17건은 현재 pool과 구조상 연결되지만 기존 prod18/A·B10과 같은 코호트로 합치지 않는다. 공격 입력과 동일 source 대응은 별도 확인 대상이며 이번 pool 설계가 이를 완료했다고 간주하지 않는다.

후속 [pool overlap 확인](reproducibility/g4_human_attack_pool_overlap_2026-10-26.md)은 인간 17세션과 공격 결과가 7개 clip ID를 공유한다는 단서를 보강했다. 이는 same-pool 탐색 연결이며 동일 build·방향·관문·paired 설계 또는 held-out 증명은 아니다.
