# CAPTCHA 비공개 문제·정답 구조 비교 및 두 저장소 감사 — 2026-10-26

## 0. 범위와 판정

- 저장소 기준: `mukgore/handcaptcha` main `037873299a9e45435250aa158857b35e07668259`, `mukgore/codex` main `86fcda1b9653b8538705d051b5c7d94ac5613310`.
- 코드와 공개 파일의 정적 검사, 공식 공급자 문서 확인, 저장소 단위시험을 수행했다. 비공개 원자료·영상의 전 프레임·실제 서비스 인증·실제 공격 트래픽은 검증하지 않았다.
- 본 문서의 '권장'은 구현 계약이고 '확인'은 위 커밋에 직접 근거한다. 영상이 실제로 무가림 프레임을 포함한다고 단정하지 않는다.
- 공개용 문서에는 개인별 로그, 원본 답 좌표, 비공개 asset key, 인증 비밀을 추가하지 않는다.

## 1. 다른 CAPTCHA와 무엇이 비슷한가

| 공급자/공식 근거 | 공식 문서에서 확인한 통신 경계 | 이 프로젝트에 적용할 수 있는 원칙 |
|---|---|---|
| [reCAPTCHA verify](https://developers.google.com/recaptcha/docs/verify) | 브라우저 응답 token을 서비스 백엔드가 secret으로 검증하며 token은 짧은 수명·일회용 | 클라이언트의 '통과' 표시를 보호 동작의 근거로 쓰지 않는다 |
| [Turnstile Siteverify](https://developers.cloudflare.com/turnstile/get-started/server-side-validation/) | 브라우저 token을 백엔드만 Siteverify로 검증; action/hostname도 확인 권장 | challenge/tenant/action/만료·소비 상태를 서버에서 확인 |
| [hCaptcha Developer Guide](https://docs.hcaptcha.com/) | 사용자 response를 백엔드가 계정 secret과 함께 siteverify에 보냄 | 서버의 검증 경계·비밀 분리 |

**결론:** '사용자에게 문제 표시, 정답 판정/인증 권한은 신뢰 가능한 서버에 둠'이라는 경계는 이들 시스템의 공개 검증 방식과 유사하다. 그러나 세 서비스의 내부 이미지·문제 데이터셋, 정답 파일 형식·보관 방법은 위 공개 문서만으로 확인되지 않는다. 세 서비스가 '비공개 영상 문제-답 파일'을 실제로 같은 방식으로 저장한다고 말하지 않는다. Turnstile과 reCAPTCHA v3는 매번 이미지 정답을 맞히는 형태만으로 설명할 수 없다. 비밀 원본 보관은 유출 경로를 줄이지만, 화면에 나간 영상 자체의 복사나 공개 원본 검색을 막지는 못한다.

## 2. 현재 저장소 구조와 확인된 상태

| 항목 | 확인 근거 | 현재 상태 |
|---|---|---|
| 시연 영상 목록 | [pool_manifest.json](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/pool_manifest.json) | `custom01`–`08` 여덟 clip. 공개 mp4와 동일 이름 계열의 공개 landmark JSON을 가리킴 |
| 그 외 공개 연구 영상 | 위 commit Git tree | `l1`–`l3`와 `r1`–`r3`의 level 1–3 영상 18개가 별도 존재. 이 18개를 현재 운영 승인 풀로 세지 않음 |
| 현행 화면 | [hand_captcha_prod.html](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/hand_captcha_prod.html) | 정적 GitHub Pages에서 manifest와 기준 관절을 fetch; 클라이언트가 score/`passed` 계산 |
| 정답 비공개·서버 연동 | 같은 HTML `UPLOAD_URL=''`, `SAVE_LOCAL_JSON=false` | 구성 그대로면 결과 업로드와 자동 로컬 저장도 수행되지 않음. 백엔드의 보호 action 인증이 없음 |
| 영상 확장 | [pipeline.py](https://github.com/mukgore/handcaptcha/blob/037873299a9e45435250aa158857b35e07668259/dataset_pipeline/pipeline.py) | 단계 1–5/7 기반 후보 manifest 생성. stage6 최종 영상 renderer 호출·재디코딩 검사·권리 승인과 연결되지 않음 |
| 역사적 실험 | [재현성 상태](reproducibility/v0_2_evidence_gaps_and_researcher_decisions_2026-10-26.md) | score 재현과 일부 기존 closed-set 공격은 확인됐으나 실제 실행 빌드, 독립 source, 보호 action end-to-end 성능은 미확인 |
| 3D 손·물체 | [3D 요구사항](3d_hand_object_challenge_requirements_v0.1.md) | 설계 후보. 생성된 운영 자산이나 인간·공격 비교 없음 |

## 3. 우선순위별 결함·조치·검증 경계

| ID / 우선 | 직접 확인한 문제 | 수행/요구 조치 | 남은 판정 |
|---|---|---|---|
| SEC-01 / P0 | 브라우저가 모든 문제 경로와 선택된 기준 JSON을 읽으며 최종 합격을 스스로 계산 | 기존 공개 demo는 연구용으로 표시. 신규 보안 경로는 비공개 reference + 서버 채점 + 일회성 보호 action 권한. 과거 Git 공개 좌표는 '숨기기'로 회수되지 않음 | 서버·입력 신뢰성 구현 전 운영 보안 BLOCKED |
| POOL-01 / P0 | 공식 운영 승인 source family, 원본 권리 대장, source별 노출 상한 없음 | [영상 풀 v0.4](video_pool_occlusion_delivery_requirements_v0.4.md)의 권리·중복·출하 상태를 신규 자료에 적용. 기존 8개는 closed-set 회귀용 | 신규 영상·사용권·가림 검수 자료가 없으므로 운영 풀 크기 미확정 |
| MASK-01 / P1 | stage6가 첫 유효 마스크 전 원본 프레임을 쓸 수 있고 검출 누락 때 직전 mask 재사용 | 별도 코드 변경에서 매 frame 원본 인덱스·landmark 검사, 오류 시 임시 파일 폐기, 전부 생성된 뒤에만 결과 이름 등록 | 디코딩 개수 검사는 최종 가림 픽셀 전수 검사 아님. 배포 QA 미완료 |
| MASK-02 / P1 | 이미지 x/y는 픽셀, z는 정규화 상대값인데 기존 dist는 3축 | mask 위치와 기하 gate를 화면 x/y로 통일 | 전체 영상 및 실제 픽셀 ROI는 실자료로 재검증 필요 |
| MASK-03 / P1 | stage7은 미검출 frame을 실패 목록에는 넣지만 pass 분모에서는 제외 | 모든 frame을 분모에 포함, 미검출은 실패 | w3>1일 때 '손목은 가림 원 밖' 관문과 중점 원 수식 충돌; 데이터 보기 전 임계값 완화 금지 |
| PIPE-01 / P1 | stage2/4가 프레임 제거·reverse를 하므로 `frames[idx]`가 원본 frame과 다를 수 있음 | renderer는 1:1 원본 인덱스만 수용, 변형의 PTS 매핑이 구현될 때까지 확장 후보를 굽지 않음 | run_batch의 `accepted`는 운영 승인이나 최종 MP4 아님 |
| PIPE-02 / P1 | `ingest_experiment_folders.py`는 tree에 없는 `dataset_pipeline.export_pool`을 import하고, legacy mask를 검증 없이 복사하도록 설계 | 해당 legacy 경로 사용 금지·의존성 확인·동일 출하 gate 설계 | 입력 원본과 검수 규칙 없이 안전한 자동 편입은 BLOCKED |
| SCORE-01 / P1 | 기존 점수는 브라우저 기반, 0.25 기준은 공격 분류 검증이 아님 | [표준 채점 v0.3](scoring_standardization_v0.3.md)의 V1/held-out 분리와 서버 판정 연결 | 현재 17/18 인간 score 및 공격 결과를 인증 성공률로 쓰지 않음 |
| INPUT-01 / P1 | 카메라 영상/좌표 출처를 신뢰할 수 없고 OBS·pass-signal 통과 경로 미평가 | 격리 test endpoint에서 입력 출처 위조·replay·서버 권한 소비 비교 | 브라우저 카메라 이름 확인만으로 방어 완료라 하지 않음 |
| DOC-01 / P2 | [README](../README.md)와 [PROJECT_STATUS](../PROJECT_STATUS.md) 첫 문단은 2026-10-17 이전 승인 범위를 '현재'로 읽히게 함 | 최신 상태 링크와 설계/구현/검증 표식을 상단에 두고 과거 본문은 역사로 보존 | 상태 문서와 현행 Git commit의 차이는 계속 추적 |

## 4. 권장 문제·정답 전달 구조

1. **자료 준비:** 원본 영상 또는 생성 3D 장면, 손 기준, 접촉/관문, 소유권/상업 송출 범위를 각각 비공개 원천 대장에 연결. source family 중복 분리.
2. **가림 자산 검사:** 원본→좌표/PTS 동기화→가림 픽셀→인코딩/분할→최종 산출 바이트 전수 재디코딩→누출/사람 수행성/공격 검사. 합격본만 `RELEASED` 상태. MP4 사전 생성, 수요 시 생성, 캐시 중 방식은 동일 검사 계약 적용.
3. **문제 발급:** 서버가 공개되지 않은 승인 풀에서 자산 선택. 예측 불가능한 challenge ID, tenant·action·세션·만료·재시도 횟수·노출 예산을 결합. 브라우저에는 가린 영상 접근권과 최소 재생 지시만 제공.
4. **미디어 응답:** 처음에는 인증된 media endpoint와 `<video>`의 byte-range 재생을 쓴다. 비공개 origin 및 로그·poster·다른 rendition에서 원본 누출 점검. CDN이나 signed URL은 접근 제어 수단이지 영상 복제 방지는 아님.
5. **답 제출:** 클라이언트의 관절값·카메라 프레임은 조작 가능 입력으로 취급. 서버의 비공개 기준에서 gate/score를 계산하고, 입력 신뢰성 검사를 별도 적용. score를 사람 확률로 명명하지 않음.
6. **인증 소비:** challenge/action/tenant/만료/시도 수를 서버에서 원자적으로 확인하여 한 번만 보호 동작 허용. 연구 점수와 서비스 승인 이벤트/로그를 분리.
7. **노출 교체:** family별 발급·전송·풀이·공격 회수율을 기록. 새 파일 수보다 독립 family 수를 보고하고, 반복 매칭이 쉬워지면 새 source를 확보하거나 방식 자체를 재검토.

## 5. 작업 결과와 남은 실행 조건

- `handcaptcha` 진단 코드 수정은 [검토 가능한 패치](../patches/handcaptcha_fail_closed_mask_2026-10-26.patch)로 보존했다. 수정된 Stage 6/7의 합성 영상 및 기존 검사 `python -m pytest dataset_pipeline/tests -q`는 24개 통과했다. `codex`의 `python -m unittest discover -s tests -v`는 16개 통과했다. 어느 것도 공개 시연 HTML을 보안 서비스로 승격하지 않는다. 이 시점의 GitHub 연결은 `handcaptcha` 브랜치 생성에 403을 반환해 해당 저장소에 반영하지 못했다. 따라서 패치는 적용 전 제안이며 기본 브랜치 코드의 결함은 여전히 남아 있다.
- 로컬 164개 연구 원자료, 촬영 원영상, 사람별 로그·영상과 비공개 실행 빌드는 공개 Git에 없으므로 이 감사에서 열거나 재실행하지 않았다. 참여자 촬영 원영상은 기존 사용자 진술상 보존되지 않았으며, 다른 경로의 자료와 혼동하지 않는다.
- 현실 자료에 대한 출하 판정은 별도 `rights_record`, 원본-출력 frame/PTS map, 모든 최종 렌디션의 mask 검사, 운영 저비용 공격과 사람 완료율이 준비될 때까지 `BLOCKED`다.
- `handcaptcha` 기본 브랜치의 GitHub Pages는 공개 demo이므로, 변경 코드의 존재나 `passed=true`를 서버 인증과 동등시하지 않는다.
