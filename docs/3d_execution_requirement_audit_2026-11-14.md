# 3D 요구별 현재 근거와 공백 — 2026-11-14

[3D 명세 v0.1](3d_hand_object_challenge_requirements_v0.1.md)의 요구 범위를 유지한다. 아래 ‘부분’은 전체 요구 완료가 아니다. 코드/fixture 검사는 실제 사람·강한 공격·운영 인수의 대체가 아니다. 원래 [연구 순서](research_goal_followups_2026-11-10.md)의 1–5단계 실제 입력은 [등록 기록 확인](deliveries/2026-11-14_execution_evidence_and_priority_resume.md)대로 대기다.

근거: [접촉 대조][CONTACT], [표면/단서 실제 실행][SURFACE], [기존 MANO 산출물 재검사][MANO], [실행 증거 기준][RECORD]. 외부 연구/권리 문헌은 원 명세의 기존 기록을 유지하며 이번에 새로 확인한 법적 판단으로 쓰지 않는다.

| 원 요구 | 현재 근거/상태 | 완료를 위해 필요한 것 |
|---|---|---|
| §3 G0/G1/G2 의미 분리 | G0 후보 유지. 접촉은 생성 장면의 속성 | 사람에게 요구할 행동·판정 기준 잠금. G1/G2는 G0 결과 뒤 |
| GEN3D-01 형태·좌우손 | 자체 proxy/기존 MANO 산출물 일부 | 근거 있는 형태 범위와 실제 과제별 좌우손 검증 |
| GEN3D-01 물체 mesh/크기/질량 | 작성 구 반경 변화만 있음 | 원기둥/손잡이/상자 등 실제 형상과 질량/지지 근사 |
| GEN3D-01 카메라·조명·renderer/encoder | 고정 정사영·flat/lit·코드와 ffmpeg snapshot | 카메라 설정 계약·독립 camera/renderer family와 실제 표시 조건 |
| GEN3D-01 초기/목표·관절 궤적·접촉/해제·물체 궤적 | 작성 두 tip 접촉 계획/시각·이동을 비공개 참조로 보존 | 전체 scene manifest와 실행 기록 연결, 의미 있는 family 식별 |
| GEN3D-01 seed/version 재현·비공개 정답 | 두 seed 재현 검사, 원자료 비공개 | 실제 서버 발급/송출 계약과 생성기 공개 조건 평가 |
| GEN3D-02 관절 범위·연동·속도 | 임의 공학 범위임을 명시 | 인체/모델 근거·개인차·통증 없는 수행 기준과 관측 |
| GEN3D-02 자기 관통 금지 | 손바닥 mesh·손 자체 충돌 없음 | 해부학적 표면/충돌 구현과 검증 |
| GEN3D-02 손·물체 비관통/접촉면 | capsule–sphere 거리·두 tip 토폴로지 부분 검사 | 실제 손/물체 표면 접촉 패치·관통 주석 |
| GEN3D-02 유지·중력·지지/회전 | prescribed kinematics, 역학 없음 | 검증 가능한 지지/안정성/마찰 등 물리 가정과 검사 |
| GEN3D-02 사람 편안함 | 미실행 | 동의한 참가자 G0 파일럿·실제 수행/중단 기록 |
| GEN3D-02 렌더 전후 가림 검사 | 기존 gate + 두 중지 뼈 proxy의 visible surface 검사 | 실제 숨길 해부학적 영역 정의·최종 raster 전체 검사 |
| GEN3D-03 제한 primitive/두 grasp 사건 | 두 작성 접촉 proxy와 접근/유지/이동/해제 | 자연스러운 제한 grasp 두 종류와 형상 다양성 검증 |
| GEN3D-03 비슷한 손/가림·다른 물체/접촉의 정답쌍 | 깊이 반전 제어와 물체 표시/제거 진단 부분 | 다른 형상/접촉 계획의 대응 문제와 실제 유효 정답 |
| GEN3D-03 물체 단서의 필요성 | 일부 proxy에서 flat object 차이 확인 | 사람의 물체 단서 이해/모방과 강한 공격의 같은 정보 비교 |
| GEN3D-03 단서 없으면 찍기·손만으로 같으면 장식 | 최종 영상이 같은 유효 3D 대안 및 조명 단서 분리 | 제외/수정/복수 정답 기준과 실제 선별 응답 |
| GEN3D-03 색/ID 외우기 통제 | 조건마다 같은 색·문구, 원답 이름 미표시 | 보지 않은 형상·재질·접촉 계획에서 지름길 공격 |
| GEN3D-04 그림자·반사·실루엣 누출 | opaque surface 가림/조명 진단. cast shadow/반사 없음 | 실제 renderer에서 그 효과를 포함한 최종 누출 검사 |
| GEN3D-04 손/물체 별도 가림 비율 | proxy 소유권·보이는 물체 픽셀을 비공개 기록 | 요구 단서와 보호 영역의 과제별 비율·사람 검사 |
| GEN3D-04 배경/occluder/물체 궤적 지름길 | 고정 조건의 대조만 있음 | 각 요인만 쓰는 A4와 교차 조건 평가 |
| GEN3D-04 masked-only 송출 | 비공개 research output, 미배포 | 실제 endpoint/페이지가 depth/원본/seed를 제공하지 않는지 인수 |
| GEN3D-04 오프라인/요청/캐시 선택 | offline 실제 인코딩 수행 | 동일 품질/범위의 runtime·저장·전송/검수 비용 비교 |
| GEN3D-04 fail-closed·최종 bytes·권리 | 기존 gate/codec/container와 research-only 적용 | 실제 운영 발급·철회·접근 통제·자산 권리 인수 |
| SCORE3D 3D 정답과 단안 사용자 추정 구분 | 문서/참조 분리 유지, 사용자 3D 실측 없음 | 추정 불확실성·보정/좌우손/기기 기록 |
| SCORE3D G0 2D/각도/순서 baseline | 기존 채점 도구 있음 | 새 장면/사람 반응과 기존 baseline의 연결·독립 평가 |
| SCORE3D 손모양/엄지/phase 구분력 | 접촉 proxy만 있음 | 사전 정의 특징·정답 행동·지각/모방/추적 분리 분석 |
| SCORE3D 복수 허용 자세 | 같은 최종 영상의 다른 3D 제어 확인 | 사람 자료로 허용 집합/접촉 영역 정의. 단일 깊이 강요 금지 |
| SCORE3D 유사도와 인증 분리 | release false, 기존 국소 보안 검사 | 실제 입력 위조/가상 카메라/신뢰 경계 평가 |
| EVAL3D B0–B3 | 계획 유지. hand-only는 B2 전체의 대체가 아님 | 같은 표시/정보/시간/입력의 실제 대응 조건 |
| EVAL3D A1 | 단순 기하/픽셀 반례만 있음 | 같은 영상만 받는 구체적 공격 실행·예산/분모 기록 |
| EVAL3D A2 | oracle 물체 깊이 제어는 공격이 아님 | 화면만 보는 pose fitting/IK/접촉·충돌 공격 |
| EVAL3D A3 | 미실행 | 허용된 생성/학습 자산·분할·실행 환경과 실제 학습 추정기 |
| EVAL3D A4 | renderer 단서 부분 대조 | artifact-only·물체/원 이동-only·반복 수집/lookup의 대응 실행 |
| EVAL3D 조건 노출/순서 | UI/실험 계획 있음, 실제 배정 없음 | 반복 기억 통제·사람 배정/노출 기록 |
| EVAL3D family 단위 dev/test | seed 변화가 독립 family가 아님을 명시 | scene/object/contact/trajectory/camera/renderer 계보 계약과 누출 사전검사 |
| EVAL3D 공통 정보/시간/재시도 | 요구 유지 | 실제 공격/정상 사용자에게 같은 정보/예산 적용한 기록 |
| EVAL3D 보호 동작 성공·정상 성공·보조지표 | 미관측 | 실제 보호 동작까지 연결한 결과, 오류/시간/비용/접근성 분모 |
| §7 관문 1 | 두 접촉 proxy/양성·음성 제어 부분 구현 | 실제 제한 grasp·단서 쌍의 과제 타당성 |
| §7 관문 2 | 두 seed·32 H.264·768프레임 surface 검사 | 전체 상태/해부학·비공개 송출 인수, 새 family 재현 |
| §7 관문 3–4 | 사람·A1–A4 미실행 | 모집 전 기준/표본 잠금, 실제 사람과 강한 공격 |
| §7 관문 5–6 | 최종 결정/확대 미실행 | 사람/공격/비용/권리 결과로 연구자 결정. G0 결과 전 G1/G2 운영 채택 금지 |
| §8 자산/신규성 | 원 명세의 제한 유지, 자체 코드/기하와 외부 모델 구분 | 외부 자산별 실제 사용 범위/승인, 필요한 문헌 본문/별도 검토 |
| §9 POOL-01/02 | 비공개 생성 참조는 있으나 전체 scene family 계약 부족 | origin/권리/계보와 유효 고유 문제 정의를 pool manifest에 연결 |
| §9 MASK-03/SERVE-01/V1–V3 | 개발용 가림·codec·로컬 보안 일부 | 원본 render pass 누출·비용 대조·같은 과제의 실제 사람/공격/위조 평가 |

다음 독립 개발은 GEN3D-01·EVAL3D·POOL-01/02의 **장면 계보 계약과 분할 사전검사**다. 입력이 없는 사람 실험이나 운영 판정을 만들어 대신하지 않는다. 신규 촬영/사람 자료가 접수되면 원래 우선순위 1→2→3A→3B→4를 먼저 따른다. 표의 행 개수나 파일 존재는 완료 증거가 아니며 전체 목표는 계속 진행 중이다.

[CONTACT]: deliveries/2026-11-13_grasp_contact_counterexamples.md
[SURFACE]: deliveries/2026-11-14_surface_depth_cues.md
[MANO]: deliveries/2026-11-13_mano_artifact_review.md
[RECORD]: experiment_evidence_protocol_2026-11-14.md
