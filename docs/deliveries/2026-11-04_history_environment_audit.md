# 이력 패턴 검사와 관찰 실행환경

## Git 이력 검사 범위

두 저장소의 원격 heads/tags를 fetch한 뒤 모든 로컬 reachable ref의 고유 blob을 읽었다. codex190개/2,167,352byte, handcaptcha240개/57,454,484byte와 ZIP 내부7개 파일을 검사했다. 정의한 private-key/GitHub-token/AWS-key/API-key 형태 후보는 두 저장소 모두0건이었다. archive 크기 예산으로 건너뛴 항목은0건이었다. 검사 도구는 `tools/audit_git_history.py`다.

이는 비밀값·개인정보 전체 부재를 입증하지 않는다. dangling/deleted/hidden ref, 중첩·암호화 archive, 모든 영상/이미지의 의미상 개인정보 검토는 포함하지 않는다. 로컬 작업 중 미커밋 변경도 Git blob 범위에 들어가지 않는다. 명시한 패턴 밖의 값은 탐지하지 못할 수 있다.

handcaptcha에는 media/archive 경로를 가진 blob60개, 좌표 JSON 후보 blob9개, archive 내 좌표 JSON 후보1개가 있다. 이것은 고유 촬영 수나 개인정보 위반 확정 수가 아니다. 기존 공개 정답/원본 매칭 가능성과 직접 연결된 연구 한계도 유지된다. 상세 ref/object/path와 archive 구성은 비공개 private_artifacts/history_audit에만 보관했고 민감값 payload는 보고서에 복사하지 않았다. 이력을 삭제/재작성하지 않았다. N01의 의미상 전수 검토는 완료로 승격하지 않는다.

## 현재 관찰 환경

`tools/capture_environment.py`로 Python3.10.3/CPython, Windows release10/AMD64, Node24.18.0을 관찰했다. NumPy2.2.6, SciPy1.15.3, OpenCV runtime4.12.0, MediaPipe0.10.9, protobuf5.29.6이다. opencv-python/opencv-contrib-python distribution은 둘 다4.12.0.88, matplotlib3.10.8이다. 현재 interpreter에는 openpyxl/pypdf/opencv-python-headless가 없다.

`pip check`는 MediaPipe0.10.9가 요구하는 protobuf<4,>=3.11과 설치된5.29.6의 충돌을 보고했다. 저장소 dataset_pipeline 요구 MediaPipe0.10.14와 관찰 설치0.10.9도 다르다. 환경을 설치 가능 lock 또는 깨끗한 재현환경으로 표시하지 않는다. 패키지 변경·추가 설치는 수행하지 않았다. 호환성 복구가 필요하면 격리 환경과 실제 지원 버전/모델 API를 별도로 확인해야 한다.

한글 설치 경로의 MediaPipe graph 초기화 실패는 별도 원본 점검 프로세스에서 이미 설치된 resource의 복사본과 ASCII 상대 경로로 우회해 실제 추출을 실행했다. 이 우회가 일반 CLI 전체에 적용된 것은 아니다. 프로세스의 scope와 실제113frame 추출은 재개 기록을 따른다.

모든 설치 distribution의 이름/버전과 pip-check 원문은 비공개 environment_snapshot_v1에 보관한다. 사용자 절대경로·모델/원본 해시·식별자는 공개 문서에 넣지 않았다. N02의 과거 build 복원·wheel hash/깨끗한 재설치 검증은 남는다.

## 새 main 자료 연결

최신 main08a9558의 초기 점수 재계산 결과와 runtime 검증 TODO를 작업 브랜치에 merge했다. main은 변경하지 않았다. 기존 초기값0.493/0.557 문제는 [새 보고서](../reproducibility/initial_score_reconciliation_results_2026-11-04.md)의 부분 해명 범위를 따른다. 0.557을 참가자 동일 비중의 정답으로 대체하지 않으며 미확정 원자료 생성 경로를 유지한다. 해당 새 코드의 합성 unittest3개를 이 환경에서도 통과했다. 새 사람/기존 사람 연구 재실행은 하지 않았다.
