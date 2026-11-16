# 완료 영상의 픽셀만 이용한 MediaPipe 진단 — 2026-11-17

기존 TF-04 영상48개를 새 worker/graph에서 각각 추정했다. 무가림32영상800프레임 중769프레임을 검출했고, A의 가림 후보8영상과 최종 H.264 8영상은 각각200프레임 모두 미검출이었다. 이 결과는 현재 합성 영상과 기존 Python MediaPipe 설정의 관측이다. 사람 이해도·강한 공격 저항·실제 인증 성능을 입증하지 않는다.

[사전등록](../mediapipe_matched_video_preregistration_2026-11-16.md), [집계 JSON](../../reports/mediapipe_matched_20261117.json), [영상별 지표·추론 시간48행](../../reports/mediapipe_matched_timings_20261117.csv), [실행 코드](../../analysis/mediapipe_matched_video_diagnostic.py), [집계 내보내기](../../analysis/export_mediapipe_matched.py).

## 실행과 보존

생산 commit은 `03971e6`이다. 비공개 출력 `../private_artifacts/mp4p_20261117_v1`, 기록 `mediapipe_tf04_record_20261117_v1`, 설정 `mediapipe_tf04_config_20261117_v1.json`을 유지한다. 실행은 `EXITED_ZERO`, 사후 snapshot 일치이며391개 출력의 전체 집합·크기·SHA256 검산은 `RECORDED_FILES_MATCH`다. 입력394개(설정 포함), 환경26pin을 기록했다. 중단 후 재개에서는 기존 결과만 읽고 내보냈으며 추론·렌더·인코딩을 반복하지 않았다.

실제 RGB를 받는 worker의 요청에는 영상 경로·confidence·리소스 fingerprint만 들어간다. 참조 좌표는 worker 종료 후 부모가 읽는다. 48개 영상에25프레임씩 총1,200회 이미지 입력을 처리했다. 이는 tracking/검출의 조건부 내부 실행을 포함하므로1,200회 CNN forward를 뜻하지 않는다. 모델·자산 설치/다운로드, 새 영상·사람 시행·독립 family·풀 채택은 모두0이다.

## 검출과 조건부 오차

각 행은8영상·200프레임이다. A는 기존 원형, B는 수정 정지 자세, C는 원형 없는 경로, U는 수정 전 PCA 정지 대조다. B/C는 현재 가림 관문을 통과하지 못했으므로 source만 존재한다. U는 상위 모델 prior 위반 대조이며 유효 공급 후보가 아니다.

| 조건 | 검출/전체 | 검출된21점 평균 오차(px) | 중지 PIP 평균 오차(px) | 참조 손 길이로 나눈 평균 오차 |
|---|---:|---:|---:|---:|
| A source | 200/200 | 8.578 | 7.864 | 0.05994 |
| A candidate | 0/200 | null | null | null |
| A final | 0/200 | null | null | null |
| B source | 175/200 | 8.565 | 5.921 | 0.05984 |
| C source | 194/200 | 8.614 | 6.127 | 0.06019 |
| U source | 200/200 | 8.411 | 6.475 | 0.05877 |

총 검출점 비교는16,149개(769×21)다. 미검출431프레임은 전체1,200분모에 남고 오차0으로 채우지 않았다. 오차는 검출된 프레임에 조건부이며 참조는 생성 모델의 투영이다. 독립 사람 주석이 아니며 관절/표면 손끝 의미·self-occlusion 차이는 남는다.

## 고정 prod 수치와 시간

기존 prod 원문·가중치·기준을 유지한48×2구간=96진단이다. 자동 keyframe 구간에서 `.25` 점수/모든38도 각도 조건을 함께 만족한 영상은 A source8/8, candidate0/8, final0/8, B source7/8, C source7/8, U source8/8이다. C는 점수만 보면8/8이다. 정지 대조도 높은 수치를 얻으므로 점수·각도·추적 실패를 구분해야 한다. 200ms hold와 UI·실제 카메라·최종 인증을 실행한 결과는 아니다.

핵심 처리 wall161.082초, 부모 자체CPU11.172초, worker 자체CPU 합118.172초다. worker import/추정/검산과 부모 오차·prod 수치·저장/재검사를 포함하고 recorder 준비/봉인은 제외한다. Node 자식CPU는 미측정이다. 영상별 subprocess/batch/검산 시간은 CSV에 따로 보존했다. batch 반환 후 기록한 frame event를 프레임별 추론 지연으로 쓰지 않는다.

기존 Python video-mode 설정은 `static_image_mode=False`, maxhands1, complexity1, confidence `.5/.5`다. browser prod `.35/.4`와 동등하지 않다. graph 내부는 호출마다33,333μs를 진행하며 원영상8FPS PTS를 graph에 전달하지 않는다. 실제8FPS 온라인 성능·통제한 cold/warm 성능으로 확대하지 않는다. world 좌표·handedness는 비공개 보존하며 실제 깊이·손 방향 정확도는 평가하지 않았다.

## 백로그 연결과 다음 조건

4단계/M02·V00·V02·G07의 합성 픽셀 기준선, S01/S06의 결측 분모·고정 함수 진단, R1/R3/R4/R9의 일부 기록 근거다. 같은 자료를 다시 사용했으므로 독립 평가를 추가한 것이 아니다. 실제 촬영·선별·3A 대응·3B 독립 보정·사람/모델 비교·운영 보안의 완료 상태는 바꾸지 않는다. 전체62개 ID·3D44요구·R0–R9와 원래 우선순위를 유지한다.

현재 독립적으로 가능한 앞 단계 엔지니어링은 S05의 최악 유형 동시 상한이다. 기존 군집 bootstrap의 주변 구간과 구분하고, 독립 단위/누락 유형/선택된 기준의 조건을 명시한 도구를 준비한다. 실제 자료가 없는 경우 합성 검산만 수행하며 성능값을 만들어 넣지 않는다.
