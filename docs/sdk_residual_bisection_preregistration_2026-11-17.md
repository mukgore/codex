# SDK 조건부 경계의 잔여4구간 — 제한 이분할 사전등록

앞 단계 실제 촬영/선별/정상·오답·독립평가 입력은 대기다. 기존 v2의768leaf 중764유한/4미확정 결과를 보존하고, `SDK_SHIFTED_NORM_INCLUDES_ZERO`인4구간만 별도 계산한다. 이는 새로운 시간 샘플이나 SDK forward가 아니라 기존 경계 함수를 더 작은 전체 시간구간에 적용하는 계산이다. 완료한764leaf를 재계산하거나 기존 결과를 덮어쓰지 않는다.

각 잔여 parent를 시간 오름차순으로 최대6깊이 이분할한다. 시작 parent도 새 실행의 첫 평가로 기록하며, 유한 후보는 더 분할하지 않는다. 동일한 영분모 사유만 재시도한다. 다른 미확정 사유는 그대로 terminal에 남기고 예기치 않은 오류는 실행 실패다. 최대 평가는 parent당127회, 전체508회다. 유한/미확정 terminal은 부모 전 구간을 빈틈 없이 덮어야 하며 최대깊이나 인접 float 때문에 더 나눌 수 없는 경우를 기록한다. 결과를 본 뒤 깊이/예산/오차 pad를 바꾸지 않는다.

기존 source/성공 receipt, v2의 leaf/모델buffer와 assumptions를 정확히 연결한다. SDK 모델을 새로 불러오거나 forward하지 않는다. 고정 SciPy/float32/SDK Rodrigues/LBS 함수·IV40자리·오차1e-12/1e-14/1e-6을 유지한다. 원래 parent의 저장 양끝을 읽어 새 유한 terminal의 조건부 chord remainder를 계산한다. 새 시점의 model 추론이나 샘플 포함 검사는 하지 않는다. raw bounds/시각/입력 hash/세부 기록은 영구 비공개다.

측정은 새700초 상한·fresh immutable output/record/config·전체 worktree/입력/17pin snapshot·명령/시각/자체CPU/stdout/stderr/종료/전체 출력 hash를 남긴다. 실행 중에는 작업트리를 편집하거나 커밋하지 않는다. 준비 코드/합성 단위검사와 실제4구간 계산 결과를 구분한다.

이분할로 유한 후보가 늘어도 backend 오차 가정의 검증은 되지 않는다. 부모 전체 후보가 생기는지·terminal별 미확정 이유·시도 분모·시간·폭/remainder만 보고한다. `backend_error_bounds_validated=false`, `continuous_collision_free_proven=false`, `CCD_clearance=false`, `release_allowed=false`를 유지한다. continuous narrow phase·생체/물리·사람/운영 승인은 별도 미완료이며 전체62ID·3D44표행·R0–R9를 유지한다. 대시보드는 사용자 지시로 더 수정하지 않는다.
