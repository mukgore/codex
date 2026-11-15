# MANO 해부학적 기준축의 저자 코드 대조 — 2026-11-15

[실행 순서](../research_goal_followups_2026-11-10.md#실행-순서와-기존-백로그-연결)를 유지했다. 등록 촬영21행의 원본 경로0개·모두 `AWAITING_CAPTURE`, 선별 응답 관측값0개를 재확인했다. 실제 수집/사람 단계는 대기다. [이전24조건 BMC 대조](2026-11-15_mano_bmc_context_controls.md) 다음으로, 현재 저자 구현의 해부학적 기준축 표현을 실제 SDK와 대조했다.

## 근거와 검증 범위

[BIO-09](../academic_reference_index.md#bio-09--cpf의-a-mano와-저자-구현)의 CPF2021 본문§3/보충§A.1과 현재 [manotorch 고정 revision](https://github.com/lixiny/manotorch/tree/a2a70c591f91551078b7bb2af9b5d9f275b626e0)을 구분한다. 이전 원문 검토에서 확보한 본문/보충PDF를 이번 입력 snapshot에도 연결했다.

고정 revision의 `axislayer.py`, `utils/geometry.py`, README, LICENSE 원본을 Git blob 바이트와 대조했다. 원문과 소스는 비공개로 보존했다. 필요한 저자 함수/클래스 정의만 AST로 읽어 실행하고 MANO 로딩 생성자는 우회했다. 실제 smplx SDK의 중립 관절과, SDK 회전 함수로 구성한 관절 변환을 저자 메서드에 공급했다. **전체 manotorch 패키지/그 MANO 생산자의 동일성 검사는 아니다.** 패키지 설치나 환경 변경도 없다.

현재 `AxisAdaptiveLayer`의 mean-neutral 기준은 들어오는 링크 방향, 손가락별 up 기준과 외적으로 구성한다. 엄지는 별도 up 기준이며 좌우 부호가 다르다. 이 현재 코드의 incoming 방향을 2021 보충자료의 child 방향 설명이나 deprecated `AxisLayer`와 동일하다고 기록하지 않는다. root 축과 엄지 up도 모델 좌표 관례이며 개인의 임상 관절축 측정값이 아니다.

## 독립 계산과 설계

관절 j의 기준축 열행렬을 B_j라 하면 현재 저자 FK의 비root 상대 회전은 `B_j^T R_native,j B_j`로 정리된다. 독립 계산은 이에 따라 `R_native,j = B_j Rx(x) Ry(y) Rz(z) B_j^T`로 만들고 역변환한다. Euler 순서는 intrinsic `XYZ`다. 외재적 `xyz`와 구분하는 복합 회전 대조를 포함했다. 특이점 근처는 이 진단 계약 밖으로 명시적으로 거부한다.

- 기준 자세94개: 영 자세1개, 15관절×3축×양·음0.12라디안90개, 세 복합 회전3개.
- 양손 × beta0 `-1/0/+1` × root 영/`(.2,-.1,.15)` = 12조건. 다른 형상 계수는0이다.
- SDK 순전파: 94×12 + 양손 기준 template2 = **1130개**.
- 저자 compose는 손마다94개, 저자 forward는 SDK의1128개 변환에 적용했다. 같은 compose 비교값을 조건마다 반복 기록한 것을 새로운 독립 비교로 세지 않는다.

모든 값은 공학 대조용이다. 사람의 가동 범위·인구 분포·자연스러운 동작을 뜻하지 않으며 시간 순서도 없다. 기준축은 저자 방식처럼 평균 영 자세에서 한 번 만들고 실제 관절 회전을 통해 운반한다. 이전의 root만 운반한 frozen BMC 대조와 다른 방법이다.

## 실제 결과

| 대조 | 전체 선택 조건의 최대 절대 차이 |
| --- | ---: |
| 저자/독립 template 기준축 | 8.51e-8 |
| 저자/독립 compose 회전행렬 | 1.02e-7 |
| 저자/독립 추출 각도 | 2.09e-7라디안 |
| 의도한/독립 추출 각도 | 7.41e-9라디안 |
| 독립 왕복 회전행렬 | 8.61e-16 |
| 잘못된 Euler 순서 대조의 회전행렬 | 0.01154 |

수치 차이는 선택한 작은 자세에서의 구현 대응 결과이며 보편 허용 오차나 임상 정확도 기준이 아니다. 저자 root의 부모는 자기 자신이어서 추출 root는 수치 정밀도 수준의 영, 영 root를 넣은 compose도 영이다. 실제 손 전체 회전은 별도 SDK 입력/출력으로 보존했고 최대 차이5.97e-9라디안이었다. 비root Euler만 저장하고 손 전체 방향까지 복원했다고 주장하지 않는다. translation·물리 단위·전체 패키지 동등성은 검증하지 않았다.

## 실행·검사 증거

생산 코드 `1a291bb`, `analysis/runtime_benchmark/mano_anatomical_frame_probe.py`. 실제 CPU 실행 `EXITED_ZERO`, 일지 `COMPLETED` 1130/1130, 출력20개 `RECORDED_FILES_MATCH`. 설정 포함 입력60개·고정 의존성17개, 명령·시각·코드·입력/환경·전후 snapshot·종료·출력 검산값을 비공개 기록했다. 무결성 확인은 학술/출처/동의의 독립 인증이 아니다.

연구 전체221개 검사는 재실행에서 통과했다. 첫 전체 실행은 기존 supervisor fixture2개가1.5초 전에 heartbeat/journal을 만들지 못해 실패했다. 같은 두 검사 개별 재실행은2개 통과, 전체 재실행은221개 통과였다. 코드나 시험/운영 제한 시간은 바꾸지 않았다. 일시적 시작 지연은 가능한 해석이며 원인 확정은 아니다. 새6개 검사는 incoming/엄지 기준, 열행렬 합성, 명시적 Euler 순서, 왼손 반사, 왕복, 퇴화/특이점/root 입력 거부를 확인한다.

[공개 집계](../../reports/mano_anatomical_frame_20261115.json)는 수치/상태 요약만 담는다. 모델·좌표·상세 입력 hash·제3자 소스 원본을 Git에 추가하지 않는다. 비공개 위치는 저장소 인접 `private_artifacts/mano_anatomical_frame_20261115/`, `mano_anatomical_frame_record_20261115/`, `mano_anatomical_frame_config_20261115.json`, `mano_anatomical_test_observations_20261115.private.json`, `manotorch_source_review_20261115/`다.

## 다음과 필요한 입력

완료: 현재 저자 구현에 맞춘 모델 기준축·좌우손/엄지·작은 복합 회전·비root 왕복과 root 분리 검산.

다음은 관절별 제한값의 근거/적용 범위와 랜덤 결과의 실제 진단이다. 저자 구현의 기본값은 먼저 **모델용 제약**으로 출처와 버전을 기록하고, 기존 랜덤8동작에 적용했을 때의 위반을 별도 계산한다. 이를 임상·편안함·모든 사람의 한계로 간주하지 않는다. 이후 조건부 생성과 충돌·최종 영상 관문 연결을 진행한다. 임상축 검증0개, 기존 여섯 BMC 허용 한계 미확인과 랜덤 격리는 유지한다.

필요 입력은 촬영 원본·독립 주석·사람 응답·실제 운영/공격 조건이다. 새 입력은 앞 단계부터 우선 처리한다. Cloud 보류와 root prod UI 기준을 유지한다. [전체 남은 일](../remaining_work_master_2026-11-15.md).
