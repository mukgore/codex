# 승인된 로컬 자료의 challenge 계보 후보 — 2026-10-26

## 확인된 비공개 로컬 자료 구조

승인된 연구 폴더를 읽기 전용으로 조사했다. 이 공개 기록에는 원자료, 개인별 ID, 절대경로, 파일명, raw hash, 프레임 값 또는 좌표를 넣지 않았다.

한 수신 자료 폴더의 31 JSON은 스키마 기준으로 세 묶음이었다.

- **A/B 기록 10건:** `experimentInfo`, `keyframeSpec`, `trialA`, `trialB`. 내부 participant ID는 10건에서 서로 달랐다. 두 조건 모두 segment별 `frames`를 가지며 각 frame은 `lm`과 `t` 필드를 포함한다. 확인한 표본에서 `lm`은 21개 landmark로 구성됐다. 제시 순서는 A→B 4건, B→A 6건이었다.
- **sessionLog 기록 17건:** `experimentInfo`, `keyframes`, `scores`, `segments`, `sessionLog`. participant ID는 17건에서 서로 달랐고 A/B 10건과 겹치지 않았다. 각 기록의 keyframe/segment clip 참조는 현재 `pool_manifest.json`의 clip ID와 모두 일치했다(136/136 keyframe 참조, 238/238 segment endpoint 참조). 각 sessionLog 이벤트는 `detected`, `lm`, `phase`, `t` 필드를 가진다.
- **기타 trial 기록 4건:** `experimentInfo`와 `trials` 구조. 위 두 묶음과 같은 실험이라고 볼 근거는 아직 없다.

A/B 10건 중 2건은 12개 keyframe 참조가 모두 현재 pool manifest와 맞았고, 두 건의 keyframe specification은 서로 같았다. 나머지 8건은 현재 manifest에 직접 연결되지 않았다. A/B action 이름은 확인한 `landmarks_base.json` 최상위 키와 일치하지 않았다. 공격 reference library와의 직접 이름 일치도 확인되지 않았다. 따라서 A/B의 challenge가 기존 G4 공격 결과와 같다고 판정하지 않는다.

또한 이 수신 폴더의 MP4 18개는 A/B JSON의 participant ID나 내부 timestamp를 파일명에서 직접 찾을 수 없었고, JSON과 같은 basename을 갖는 영상도 없었다. 파일명 불일치는 별도 메타데이터를 통한 연결 가능성을 배제하지 않지만, 현재는 어느 영상이 어느 JSON/세션인지 매칭 근거가 없다. 영상 내용을 근거로 임의 연결하지 않았다.

## 증거 상태

- **확인됨:** 17개 sessionLog 자료는 현재 pool manifest와 구조상 직접 연결된다. 원영상 없이도 해당 JSON에 저장된 landmark/time log를 대상으로 인간 동작 자료 분석을 검토할 수 있다.
- **조건부 후보:** 17개 자료는 pool 기준의 인간 challenge 비교에 유용할 수 있다. 과거 수집 시점의 실제 HTML/build/browser/pool revision을 세션별로 입증하는 증거는 별개로 부족하다.
- **자료 부족:** 17개 sessionLog와 기존 G4 공격 output/reference library 사이의 공통 source gesture 및 동일 challenge 대응표는 아직 확인되지 않았다.
- **분리 유지:** A/B 10건, sessionLog 17건, prod_v2_pool 18건은 서로 다른 코호트로 취급한다. participant ID 비중복만으로 cohort 또는 프로토콜 동등성을 가정하지 않는다.
- **실행 제한:** 이 자료 연결은 G4 endpoint 성공을 입증하지 않는다. 실제 전체 인증 결과에는 격리된 시험 endpoint와 서버의 보호 동작 승인 로그가 여전히 필요하다.

## 다음에 조사할 연결

1. 승인된 코드·pool·challenge 산출물에서 sessionLog clip ID와 기존 G4 공격 입력 사이의 출처 연결이 있는지 확인한다.
2. 17개 sessionLog의 동일 challenge 조건과 저장 score의 정의를 요구사항 및 계산 코드에 대조한다.
3. MP4가 분석에 꼭 필요해지는 경우에만, 파일명·일반 메타데이터와 비공개 실험 기록을 이용해 연결한다. 원자료를 공개하거나 영상 내용을 임의로 판정하지 않는다.

이 문서는 집계 구조와 계보 상태만 공개하며, challenge별 또는 참가자별 대응표는 공개하지 않는다.
