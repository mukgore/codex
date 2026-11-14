# 실험 실행 증거 기록 — 2026-11-14

사용자 요청에 따라 새 실험에는 **어떤 조건으로 무엇을 실행했고, 무엇이 남았는지** 다시 확인할 수 있는 기록을 붙인다. 원래 연구 우선순위와 각 단계의 선행 조건은 그대로다. 도구 실행 성공을 사람 실험·성능 입증·운영 승인으로 바꾸지 않는다.

## 새 실행에서 남길 내용

1. 실행 ID, 질문/가설, 절차 버전, 조건·seed·분할, 계획한 사례와 성공/실패 분모, 판단 기준. 조건을 변경하면 새 실행 ID를 사용한다.
2. 실행 전 코드 commit/변경 fingerprint, 입력·참조/설정 파일, 고정 package 버전과 실제 설치 metadata, OS·기기·브라우저·모델/가중치·권리 근거. 자동 확인과 연구자 진술을 구분한다.
3. 실제 명령 인자·작업 디렉터리·실행기 파일, 시작 UTC 시각·경과 시간·종료 코드, stdout/stderr. 중단·시간 초과·오류도 별도 상태로 보존한다.
4. 실행 후 코드·입력·환경 일치 여부, 결과 파일 전체 목록·크기·SHA256. 성공 집계뿐 아니라 거부·결측·부분 실패도 기록한다. 기존 실행 폴더를 덮어쓰지 않는다.
5. 실제 관찰/계산 결과와 해석, 한계·필요 입력, 공개 집계와 비공개 실행 ID의 대응. 사람/모델/합성·재실행을 구분한다. 같은 자료의 재실행은 새 참가자나 독립 표본이 아니다.

## 공통 명령 기록 도구

[execution_record.py](../validation_v03/execution_record.py)는 기존 [사전 snapshot](../validation_v03/run_manifest.py)에 실제 foreground 명령 실행과 출력 파일 연결을 추가한다. shell을 거치지 않고 명령 인자 배열로 실행한다. 실행기는 절대 경로로 지정하며, 새 결과 폴더와 별도의 새 기록 폴더를 사용한다. 설정은 기존 run_manifest 계약을 따른다.

```powershell
python -m validation_v03.execution_record run --config PRIVATE_CONFIG.json --repo REPOSITORY --record ../private_artifacts/NEW_RECORD --artifact-root ../private_artifacts/NEW_RESULTS -- ABSOLUTE_EXECUTABLE ARGUMENTS
python -m validation_v03.execution_record verify --record ../private_artifacts/NEW_RECORD
```

설정의 시간 예산을 실제로 적용한다. timeout/중단 때 이 명령의 process group/tree를 종료하고 실제 종료 상태를 남긴다. 별도 background 서비스로 분리되는 명령은 이 도구의 지원 범위가 아니다. 도구가 정상 종료하지 못하면 시작 기록만 남을 수 있으며 이를 완료로 세지 않는다.

`EXITED_ZERO`는 **해당 명령이 0으로 종료했고 사후 snapshot이 일치하며 출력 파일을 연결했다**는 뜻이다. 출력 내용의 과학적 타당성·영상의 진위·참가자의 동의·사람 인증·효과 크기를 증명하지 않는다. 별도 task 검사와 원문 요구의 선행 조건이 필요하다. 실패 상태도 로그와 존재하는 출력/미생성 폴더를 기록하고 재검사할 수 있다.

기록 폴더에는 실행 전 manifest와 checksum, started 기록, recorder 코드 사본, stdout/stderr, 실행 당시 postflight, 최종 receipt/checksum을 보존한다. 결과 파일은 비공개 결과 폴더에 유지하며 receipt가 전체 파일 집합을 연결한다. 파일 변경/추가/삭제와 로그·receipt·manifest 손상은 검출한다. 이후 Git commit이나 환경이 바뀌어도 **당시 기록된 파일 검사**는 할 수 있다. 새 실행과 현재 환경의 일치 여부는 기존 run_manifest `--verify`의 별도 범위다.

실행 전 manifest는 recorder Python 환경의 metadata를 기록한다. 별도 Node/브라우저/모델 실행기의 버전·설정·모델 자산도 실험 config의 입력/코드/parameters에 명시해야 한다. 자동 수집되지 않는 GPU·디스플레이·기기·동의/배정 정보는 실제 수집 절차와 event log로 보완한다. 사람 실험은 실제 영상/응답·노출/배정·시각·중단 기록이 필요하며 프로세스 종료만으로 시행 완료를 인정하지 않는다.

## 기존 실험은 사후 보존으로 구분

```powershell
python -m validation_v03.execution_record inventory --run-id EXISTING_RUN_ID --record ../private_artifacts/NEW_INVENTORY --artifact-root ../private_artifacts/EXISTING_RESULTS
```

`RETROSPECTIVE_ARTIFACT_INVENTORY`는 **지금 확인한 파일들의 목록**이다. 과거의 명령·실행 시각·종료 코드는 만들지 않고 null로 둔다. 기존 사전 snapshot/postflight가 있으면 별도 보존해 대조한다. mtime이나 결과 파일 존재만으로 과거 실제 실행·처리시간을 증명했다고 쓰지 않는다. 확인되지 않은 과거 실행은 미기록/근거 부족 상태로 유지한다.

## 보관과 검증의 경계

원본 영상·좌표·참가자 자료·연결표·모델·개별 입력 해시·상세 receipt/log는 연구용 비공개 영구 보관한다. GitHub에는 코드·절차·제한·식별자 없는 집계와 실행 ID 대응만 올린다. 외부 서비스에 원자료를 업로드하지 않는다. 상세 검증은 권한 있는 담당자가 로컬 기록과 산출물을 사용한다.

checksum은 기록 이후의 파일 변화를 검사한다. 모든 기록을 함께 다시 작성할 수 있는 작성자를 인증하지 않으며 로컬 시각도 독립 타임스탬프가 아니다. 이 기록은 감사·재현을 돕는 증거이며 독립적인 제3자 실행 인증을 주장하지 않는다. 공개 기록 없이 사후 바꿀 수 없다는 강한 보장이 필요하면 별도의 승인된 증거 보관 절차가 필요하다.
