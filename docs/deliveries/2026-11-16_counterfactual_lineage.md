# 같은 최종 파일과 모델 답의 계보 정리 — 2026-11-16

사용자 재개 지시로 [기존 실행 순서](../research_goal_followups_2026-11-10.md#실행-순서와-기존-백로그-연결)를 다시 확인했다. 등록 촬영21행 원본 경로0개·선별 관측값0개다. 이전 [안전 중단](2026-11-16_safe_stop.md)은 당시 이력이며 현재 작업은 재개 상태다. 실제 입력이 필요한 단계는 대기로 유지하고 가능한 파일/답 계보 진단을 진행한다.

## 실행 전 고정한 방법

[기존 상대 중지 대조](2026-11-15_relative_middle_display_counterfactual.md)의32개 native 좌표 조건과64개 실제 최종 H.264, 기존8개 SDK 부모/16시점 원본을 연결한다. 새 모델 계산·영상 제작·새 사람 시행은 없다.

native 좌표와 시간의 정확한 payload, 최종 H.264 파일 바이트를 각각 묶는다. hash로 찾은 묶음은 payload 바이트도 대조해 확인한다. archive 파일 포장 metadata의 차이를 다른 손 움직임으로 세지 않는다. 실제 좌표·개별 hash는 private에만 두고 공개 집계에는 순번 그룹 ID와 synthetic 사례 연결만 남긴다. 같은 파일에 연결된 다른 모델 궤적을 사람의 허용 정답으로 자동 승인하지 않는다.

120개 실제 파일 항목의 계보는8개 SDK 부모 +16개 기존 H.264 +32개 새 native 결과 +64개 최종 H.264다. 현재 동작/seed/좌우손 정책/변경량/시점은 보수적으로 같은 개발용 동작 family에 둔다. 제공된 기록의 경계를 root로 삼은 것이며 모델의 세계적 원출처나 통계적 독립성을 인증한 것은 아니다.

기존 `validation_v03.lineage_manifest.audit`를 두 방식으로 실행한다.

1. 모두 diagnostic에 두어 파일/선언된 계보를 검사한다. 독립 development/validation/test가 없다는 finding은 정상적으로 남겨 독립 평가 자료가 아님을 표시한다.
2. 같은 final bytes지만 다른 actual native 궤적을 갖는3개를 development/validation/test로 **일부러 잘못 나눈 가상 배정**을 만든다. 실제 사람/모델 시행이 아니며, 검사기가 해당 final H.264의 정확한 byte alias와 부모/가족/노출 전파를 잡는지 확인한다. group findings에 실제 final-file key가 포함됐는지 private에서 대조한다.

현재263개 검사 기반을 유지하며, 새 파일 집계는 실제120개 입력과 기존 계보 검사기 결과를 직접 검산한다. 모든 후보는 격리이고 실제 독립 평가/보안 성능·사람 답 집합·entropy를 주장하지 않는다. 실행 뒤 실제 묶음 수와 필요한 다음 입력을 추가한다.

## 실제 결과

120개 파일을 확인했다.32개 native 조건의 좌표/시간 payload는24종,64개 최종 H.264의 전체 바이트는14종이었다.14개 최종 파일 묶음 중12개에는 서로 다른 실제 모델 궤적이 연결됐다. 같은 seed/정책·카메라·미세 변경을 독립 문제로 세지 않으며 사람의 허용 답 집합으로도 아직 확정하지 않는다.

전체를 diagnostic에 둔 계보 검사에서는 `MISSING_INDEPENDENT_PARTITIONS`1건만 남았다. 이는 현재 자료가 독립적인 개발/검증/평가 세트를 갖췄다는 의미가 아니며, 알려진 개발 자료의 목록/계보만 정리한 결과다.

의도적으로 같은 final bytes의3개를 서로 다른 split으로 나눈 가상 배정에서는 `CROSS_SPLIT_BYTE_IDENTITY`·`CROSS_SPLIT_FAMILY`·`CROSS_SPLIT_SOURCE_IDENTITY`가 각각3건, `EXPOSED_TEST_SOURCE`가1건 나왔다. 실제 final H.264의 key가 finding에 포함됐는지도 private에서 확인했다. 동일 영상·공유 부모/가족·기존 노출을 다른 seed/변경량 이름만으로 독립 평가처럼 나누는 오류를 기존 검사기가 감지했다. 실제 사람이 세 split에 참여한 실험은 아니다.

[공개 집계/순번 그룹별 사례 연결](../../reports/counterfactual_lineage_20261116.json)을 추가했다. raw 좌표/개별 hash·실제 파일 경로·계보 finding 상세는 private에만 보존했다. 새 모델 계산·영상 제작·새 시행은0회이며 영상별 생성시간을 새로 만들지 않았다. 핵심 inventory 자체의 wall약3.932초·자체CPU3.844초를 기록했고 실행기 snapshot/전체 부모 검산 시간과는 구분한다.

생산자 `97964ee`, 입력1763개·26pin·산출물5개, `EXITED_ZERO`·전후 snapshot/출력 검산 통과다. 기존 계보 검사15개도 통과했다. 비공개 위치는 `private_artifacts/mcl_20261116/`, `counterfactual_lineage_record_20261116/`, `counterfactual_lineage_config_20261116.json`, `mcl_prerequisites_20261116.private.json`이다. 이전4개 실행의 원본/receipt는 보존했다.

## 완료한 일과 다음 단계

완료는 실제 모델/최종 파일의 중복 묶음·계보·가상 split 오류의 검출이다. 현재 batch의 수이며 생성기 전체 다양성·보안 entropy·사람 답/독립 평가 성능은 미확인이다. 이 결과를 원래 사람 자료가 필요한 단계의 대체로 쓰지 않는다.

다음은 고정된 prod 원문 채점 함수로 원본·대안·정지/부분 좌표의 점수와 각도 관문을 진단하는 일이다. 실제 카메라·검출/세션 timing·200ms hold·인증 결과와 구분하고 기존 가중치/기준을 재보정하지 않는다. 실제 촬영/독립 주석/참가자 입력이 접수되면 기존 앞 단계부터 우선한다. 모든 결과는 격리, 풀/브라우저 채택0개다.
