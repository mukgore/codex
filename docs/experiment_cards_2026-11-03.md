# 최소 후속 실험 카드와 기록 계약

현재 산출물은 실행 준비안이다. 새 참가자를 모집·촬영하지 않았고 실제 사람/공격 결과를 생성하지 않았다. 연구자의 표본·효과 기준 선택과 필요한 자료가 남아 있다. G3의 수용·종료를 변경하지 않는다.

## 카드 A — 가림 모호성과 수행 가능성

**질문:** 동일한 가린 화면에서 허용 가능한 답이 여러 개인가? 오류는 화면 해석, 손으로 재현하는 과정, 추적기 중 어디서 발생하는가?

**조건:** 같은 원동작의 무가림/가림 대응 조건. 가림 원 중심·크기, 경계 피부/손끝, metadata·길이 단서를 별도 채널로 기록한다. 동일 참여자에게 같은 동작의 답을 먼저 알려주는 순서는 피하고, 조건 순서를 균형화한다. 반복 노출량·카메라·손 방향·기기·동작 난도를 고정/기록한다.

**측정:** 지각 단계에서는 동작 설명·허용 답 판단을, 수행 단계에서는 의도한 행동·완료 여부를, tracker 단계에서는 명시적 검출 실패를 구분한다. 높은 점수 자체를 이해의 정답으로 삼지 않는다. 촬영이 필요하면 목적·동의·보관/삭제·접근자를 먼저 정한다. 촬영이 없으면 tracker 실패와 운동 오류의 완전 분해가 불가능하다고 보고한다.

**분석 단위:** 참가자와 원동작 family. frame을 독립 표본으로 세지 않는다. 여러 정답을 허용하는 주석 기준을 관측 전에 작성하고 판단 불일치도 기록한다. 군집을 보존한 대응 효과와 구간 추정을 계획한다.

**종점/분모:** 배정된 모든 시도 수, 이해 가능한 시도, 실제 수행 성공, tracker 실패, 기술 오류, 중단, 불확정. 분모에서 오류를 삭제하지 않는다. 전체 경과·도움 요청·첫 올바른 시도까지 시간을 분리한다.

**잠금 전 미결정:** 주 종점 하나, 허용 답 기준, 표본 수/목표 정밀도, 최소 의미 차이, 통증/불편 중단 및 실패·불확정 판정 기준. 이 값을 임의의 ‘연구 기준’으로 채우지 않는다.

**판정:** 모호성이 크면 정답 집합/문제 선별을 수정한다. 물리적으로 불편하거나 이해 불가한 동작은 시도 확대를 멈춘다. 자료가 부족하면 INCONCLUSIVE.

## 카드 B — 손 선택과 UI의 효과 분리

**B-A 손 선택:** 같은 UI 아래 선검출 1손 baseline과 큰 손 안정화·유지 후보를 비교한다. 시작 검출 순서, 크기 비, 배열 재정렬, 다른 손 등장, 소실, 교차, 좌우손, 부분 잘림을 포함한다. 의도한 수행자 손은 시험 전에 지정한다. 알고리즘의 선택을 정답으로 쓰지 않는다.

**B-B 화면 안내:** 같은 손 선택 정책 아래 분리/중첩 화면을 비교한다. 추가 AI 후보는 한 문장 상태안내·별도 연습·작은 보조 화면 등에서 소수만 선택한다. clip·가림·gate·점수·시간 조건을 맞추고 비교 순서와 학습을 통제한다.

**계측:** 잘못 선택/전환, 안정화 시간, 소실·재선택, 도움 요청, 첫 올바른 시도, 전체 완료·중단·오류, 피로/혼동 이유. 공개 산출물은 비식별 집계다. 원본 카메라가 검출 입력이고 합성 canvas는 표시 전용인지 확인한다.

**현재 프로토타입 정책:** bbox 면적, 안정화 8 callback, 크기 동률 비율 1.1, 이동 한계 0.35×이전 bbox 면적의 제곱근, 면적 비율 상한 2, 후보 비용차 모호성 0.08. 모두 조정 가능한 공학 초기값이며 시간 기반 안정화·사람 성능·최종 연구 임계값으로 검증되지 않았다. callback 속도 차이는 별도 확인한다. 면적 순위는 같은 프레임 내에서 원본 픽셀 면적 순위와 같다.

**추적 한계:** 관절·위치·크기만으로 소유자 신원을 알 수 없다. 유사 손이 같은 위치를 차지하면 오연결 가능성이 남는다. 현재 시연은 소실/모호성 후 즉시 중단하고 전체 재시작한다. 원안의 짧은 재연결은 자동 채택하지 않았다. prod 시간·coverage·gate 정책 연결은 후속 작업이다.

**기록 이벤트 계약:** `schema_version`, `protocol_version`, `ui_condition`, `selection_policy_version`, `scoring_version`, trial 내 상대 monotonic ms, `selection_stabilizing/selected/lost/reselect/attempt_started/attempt_finished/technical_error/aborted`, 이유 코드, outcome. 재선택은 새로운 시도 ID로 시작하고 앞뒤 손의 좌표를 이어 붙이지 않는다. raw 좌표/영상·사람 ID는 별도 동의된 private 저장에만 둔다. 현재 UI는 이 수집기를 구현하지 않았고 자료를 자동 저장·전송하지 않는다.

## 카드 C — 동일 trial의 기존/후보 채점 비교

**질문:** 잠근 source/참가자/캡처 분할에서 후보 점수가 기존 점수보다 정상/오답을 잘 구분하는가? gate·L3 결과와 분리한다.

**단계:** private manifest 확인 → 연속 segment/time/missing adapter → 같은 trial의 legacy/candidate 특징·점수 산출 → 독립 일부 검산 → development 비교 → validation에서 사전 제약에 맞는 threshold 선택 → test 한 번 적용. test로 파라미터를 바꾸면 새 버전과 새 미사용 test가 필요하다.

**CSV 계약:** `trial_id,label,split,source_family_ids,participant_id,capture_id,outcome,legacy_score,candidate_score`. label은 human/attack, split은 development/validation/test, source family 전 구성요소는 세미콜론 구분, outcome은 scored/technical_error/aborted. human은 participant_id 필수. 모든 시도 capture_id 필수. scored는 두 점수가 모두 유한해야 하며 실패 행은 두 점수를 비워 둔다. 형제 파생 영상은 동일 family ID다. 공격자의 실제 source provenance는 별도 manifest로 검증한다.

```powershell
python -m validation_v03.compare_scores --input data/work/paired_scores.csv --output data/derived/score_comparison.json --min-human-accept <사전결정값> --max-attack-accept <사전결정값>
```

실행 때 꺾쇠 자리표시자는 실제 사전 고정값으로 바꾼다. 출력은 private fingerprint를 포함하므로 검토 없이 공개하지 않는다. CLI는 기존 파일 덮어쓰기를 거부한다. 필요 라이브러리는 기존 NumPy이며 신규 분류기를 학습하지 않는다. CLI의 source/participant/capture 중복 검사는 제공 ID가 정직하고 정확하다는 전제이며 독립성을 스스로 증명하지 않는다.

**보고:** score 수용/거부, scored 분모 비율, 전체 attempted 분모의 관측 수용, 기술 오류/중단을 함께 제시한다. technical_error를 공격 거부 성공으로 세지 않는다. 군집 CI와 공격군별 최악 성능은 별도 후속 구현이다. 표본 부족·허용 threshold 부재는 자료 부족/후보 수정 결과로 남긴다.

## 모든 카드의 실행 전 입력

질문·허용 주장·주 종점, 미사용 source와 참가자 단위, 원자료 동의/보관 계획, 표본 정밀도 근거, 조건 순서, 공격자 정보/도구/시간/재시도 예산, 고정 score/gate/timeout, 실패·불확정 분모, 중단 기준, 코드/config/환경 manifest, 독립 검산과 결과 검토 담당을 채운다. 현재 기록만으로 이 입력이 확보됐다고 표시하지 않는다.
