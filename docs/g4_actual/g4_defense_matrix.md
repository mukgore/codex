# G4 방어 후보와 전후 비교

프로덕션 HTML/저장소를 직접 수정하지 않고 별도 worktree의 g4_lab에 통합했다. 기존 정답의 공개 이력을 없애거나 높은 모방 점수를 사람의 증명으로 바꾸는 방어는 구현되지 않았다.

| 후보 | 실제 구현/대조 | 확인 결과 | 판정과 남은 한계 |
|---|---|---|---|
| D1 서버 재계산과 최소 공개 응답 | server.py → actual.py → 실제 HTML computeScores/onRes. 허용 경로만 제공하며 reference/pool route 없음 | Client passed/score 추가 필드 거부, 무세션/다른 세션/만료/중복 거부, 동시에 한 grant/action만 허용. HTTP 검사 통과 | 프로토콜 기계적 방어 확인. 과거 서버 개선율은 측정 불가. 공개 자산 lookup/replay는 8/8 local L3 성공 |
| D2 입력 구조 검증 | validation.py: finite numeric, bool 제외, 21×2, 시간 순서, nonzero scale, null 보존 | 좌표 0 fixture 8/8 compute score 통과 → 입력 검증 거부. 정상 oracle 8/8 유지 | 잘못된 입력 거부 확인. 기존 gate도 좌표 0을 막았으므로 별도 L3 감소 효과로 과장하지 않음. 정상 모양의 위조 좌표는 통과 가능 |
| D3 정확히 정지한 입력 거부 | 동일 행의 stationary_filter 옵션 | 고정 자세 24행 중 기존 local L3 허용 16행을 모두 거부. 1e-8 잡음 응답에서는 5/8 다시 허용 | 유의미한 보안 방어로 반박됨. 독립 검토자의 1e-9 변형도 5/8 허용. 후보 보존·폐기, 기본값 비활성 |
| D4 누락 시 전체 차단·2D mask | masking.py strict wrapper; 실제 Stage6 AST 함수와 실제 영상 first 3 decoded pixels 비교 | 원래 함수는 첫 누락 때 입력 프레임 그대로 전달, 중간/길이 부족에는 stale mask. 새 wrapper는 모두 사전 거부. z-only 변경에 불변, 입력 배열 보존, 정상 3프레임 수용 | 기계적 결함 재현 및 방어 확인. 실제 배포 영상 누출을 관측한 주장은 아님. 전체 decode/encode/PTS·풀 출하 검사는 미완료 |

Stage6의 “unmasked” 표기는 해당 단계의 추가 마스크 없이 입력 프레임을 전달했다는 뜻이다. 실험 입력은 기존 공개 MP4의 프레임이며, 실제 무가림 원영상 유출을 입증하지 않는다. w3=1.95는 fault-injection용 scalar이고 새 pipeline의 calibration/보안 인수값이 아니다.

세션 수명 60초, JSON 2MB, 최대 3000프레임은 로컬 시험 설정·자원 제한이다. 운영 기준이나 연구 성공 목표로 제안하지 않는다. 제출 timestamps는 client 값이고 출처·실제 경과시간을 증명하지 않는다. 보호 action은 메모리 counter이며 RLock은 단일 프로세스에 한정된다. 실서비스의 DB 원자성·키 보호·신뢰 카메라를 입증하지 않는다.

정상 fixture는 공개 정답을 재생한 oracle 8건 및 mask 3프레임이다. 사람의 수행 허용오차/실패율은 평가하지 않았다. Threshold·weight·정규화 수치를 결과에 맞춰 재선택하지 않았다.

코드: [server.py](../../g4_lab/server.py), [validation.py](../../g4_lab/validation.py), [masking.py](../../g4_lab/masking.py). Mask 근거: [mask_summary.json](../../reports/g4_actual/mask_summary.json).
