# 데이터 사전과 품질 점검

실제 JSON 스키마를 파일에서 확인했다. 아래 타입은 관측한 핵심 필드이며, 모든 파일에 완전히 동일한 타입이 보장되는 것은 아니다.

## 사람 세션 JSON (18개)

| 경로/필드 | 뜻·관측 타입 | 결측/해석 주의 |
|---|---|---|
| `experimentInfo.participantId` | 익명화한 사용자 키 문자열 | 가명은 공개 데이터로 안전하다는 뜻이 아님 |
| `experimentInfo.selectedHand` | `left` 또는 `right` | 세션 선택 손. 개인 좌우 손 성능 일반화로 확대 금지 |
| `experimentInfo.timestamp` | epoch ms 정수 | 코드상 저장 시각에 가까우며 세션 시작 시각이 아님 |
| `experimentInfo.version` | `prod_v2_pool` | 이 버전 외 버전 호환을 보장하지 않음 |
| `keyframes[]` | 클립 ID와 프레임 번호 | 목표 클립/시작 방식의 변이를 보존 |
| `segments[]` | 전환 7개의 from/to 및 각 기록 프레임 | 한 segment에 검출/미검출을 모두 포함. 프레임 수는 사람/참가자 수 아님 |
| `segments[].frames[].t` | 세그먼트 내 ms | 일부 int/float, 간격 가변. 보고된 FPS와 동일하지 않음 |
| `segments[].frames[].lm` | 검출 시 21×3 `[x,y,z]`, 실패는 null | 기록된 null만 명시적 실패. JSON에 나타나지 않는 시간 틈은 실패로 판정 불가 |
| `scores.totalFrames/detectedFrames/detectionRate` | 공식 집계 분모/분자/비율 | 18개 모두 프레임 합과 일치 |
| `scores.raw` | angle, dtw_angle, accel 원오차 | 좌표에서 다시 계산한 것이 아니라 저장 raw 값에서 가중합을 재계산 |
| `scores.estimated`, `captcha`, `threshold`, `passed`, `weights` | 점수 결과와 설정 | 점수는 인증의 운영/서버 검증 로그가 아니라 이 HTML의 클라이언트 세션 기록 |
| `sessionLog[]` | 세션 전체의 t/phase/detected/lm 기록 | 대기·matching 포함. 미검출도 phase에 따라 기록됨 |

## HaMeR 28조합 JSON

`metadata`에는 `exp3_pool28`, clip 목록 8개, `stop_on_fail=false`, 관문 38°, fps 24, fade out/load/in 각각 500/100/500ms, 최종 점수 threshold 0.25, weight `.38/.37/.25`, 정규화 최대값 `46.9413/44.0014/.1926`이 들어 있다. `results[]`는 unordered clip pair마다 keyframes, transitions, `stopped_at`, `prod_score`를 가진다. 전환 프레임은 `type`(video/fade/black 관련), detected, 21×2 정규화 랜드마크다. 저장된 gate `passed` 값은 Boolean이 아니라 문자열 `'True'/'False'`다. 일반 언어 truthiness로 해석하면 실패를 통과로 오판한다.

모든 28개 조합에 224개 관문 기록이 있다. 이 중 189개 성공, 모든 관문 성공 조합은 10/28. 하지만 실험 전체가 `stop_on_fail=false`이므로 운영 흐름과 달리 초기 포인트 관문 실패 이후에도 후속 입력·전체 점수 기록이 계속되었다. 점수 통과(28/28)와 운영 전체 흐름 통과(실패 관문에서 중단)를 동일시하지 않는다.

## SUS 원응답

두 xlsx 모두 10개 문항, 1~5의 정수 리커트 응답, 결측 0. 항목 1·3·5·7·9는 긍정, 2·4·6·8·10은 부정 방향으로 변환했다. 표준 점수는 긍정 응답에 `x-1`, 부정에 `5-x`, 합계×2.5. 데이터의 개인 이름/응답은 비공개 원자료 폴더에서만 읽는다.

## 결측·시간 품질 결과

- 사람 18세션 전체 8,782 segment-frame 기록, 141개 명시적 null(1.606%). 저장 detection rate의 세션별 분자·분모와 일치. 모든 점수를 감지율을 포함해 계산.
- 미검출의 1,900/2,306은 `detecting_hand`, 670/948은 `matching`, `recording`은 141/8,764, `done`은 0/375. `recording` 세션 로그 합 8,764와 segment 저장 프레임 8,782가 18개 차이이며 세션마다 log recording 수가 segment 합보다 정확히 1 적다. 단계 경계 기록 방식의 영향일 수 있으나 저장 코드/인덱스 관계를 더 추적하기 전 원인을 확정하지 않는다.
- 중복·역전 segment timestamp 0, 잘못된 좌표 shape 0, 비유한 좌표 0. 손/화면 밖 좌표가 포함된 검출 프레임 369개는 비정상 자동판정에서 제외하지 않았다. 랜드마크 카메라 좌표가 화면 경계를 넘을 수 있으므로 보이는 버그의 증거가 아니다.
- 기록 간격 기반 유효 빈도는 사람별 10.8~57.1 기록/s이며 실제 camera FPS가 아니다. 미검출/탭 지연/브라우저 기록을 함께 포함한다. 장시간 공백 중 2153의 `sessionLog` 범위는 110.91초, 7332는 29.32초; segment 합 시간은 18명 평균 12.699초다.
- 보고된 segment duration 평균 12.699초와 sessionLog 첫/마지막 시각 평균 21.571초는 서로 다른 범위다. HTML상 각 segment duration은 keyframe 관문이 통과된 뒤 recording 구간의 재생/수행 시간이고, matching 대기/전환 pause를 포함하지 않는다. 따라서 보고서의 “완료시간 12.70초”는 recording duration 합으로 재현되지만 인증 완료까지의 전체 경과시간으로 해석하면 안 된다.
- segment duration 합의 평균은 .0127초 정밀도이고 표본 SD(ddof=1)는 4.450초. 기존 보고서 SD 4.32초는 모집단 방식(ddof=0)으로 재현된다.
- 누락 프레임을 성공으로 바꾸는 보간은 수행하지 않았다. 현재 규칙 점수는 검출률로 이미 penalty를 곱함. 검출 프레임만의 점수(dr=1) 민감도는 평균 .66858, 17/18 통과로 원 규칙의 17/18과 통과 건수가 같다. 이는 보간 결과가 아니다.
- n=18 사람 누락률과 점수 Spearman ρ=-.255, p=.308. 작은 n의 탐색적 단변량 관계로서 결측이 무작위임을 증명하지 않으며, 동작·자세별 결측 선택성은 원영상 없이 평가 불가.
