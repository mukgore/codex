# 실행 기록 기반

2026-11-10 [공통 사전 실행 snapshot과 기존 journal 연결](../../docs/deliveries/2026-11-10_session_artifacts_and_run_manifest.md)을 추가했다. `validation_v03.run_manifest`는 실제 코드/입력/lock·설치 metadata를 고정하고 후검사한다. `analysis.provenance_guard_smoke`는 소유 JS export/storage 기술 실행을 그 SHA로 journal에 연결한다. 준비/후검사 성공 자체를 사람/모델 과제 완료로 표시하지 않는다. 민감한 manifest와 입력 hash는 private에만 보관한다.

모델을 실행하지 않아도 완료/오류/timeout/중단/미할당/로그 유실을 구분하고 보존 bundle을 다시 읽을 수 있는 기반이다. 설치/체크포인트 다운로드·HaMeR 성능·GPU 측정·인증 성공을 실행한 결과가 아니다.

```powershell
python -m analysis.runtime_benchmark.smoke --output ../private_artifacts/runtime_journal_smoke_v1
python -m unittest tests.test_runtime_journal -v
```

manifest에 조건 ID, 종점, 입력 노출, cache 상태, 계획 frame 수와 시간 예산을 명시한다. Journal.stage에서 실제 perf_counter_ns 경과시간을 기록하고 모든 frame의 처리/누락을 남긴다. 중복/누락 frame을 완료로 표시하지 않는다. 예외/KeyboardInterrupt/시간 초과는 서로 다른 상태다. timeout은 협조적 경계 검사이며 블로킹 모델/GPU를 강제 선점하지 않는다. 장기 모델에는 별도 process supervisor가 필요하다.

JSONL은 순서와 SHA chain, 실제 flush/fsync로 프로세스 중단·손상을 탐지한다. 디스크/OS 전원 상실을 완전히 보장하거나 악의적 작성자의 서명을 인증하는 장치가 아니다. ERROR/ABORTED는 일부 stage가 끝나지 않아도 기록할 수 있다. 빈 로그는 LOG_LOST, 마지막 불완전 줄은 INTERRUPTED, 중간 변조는 LOG_CORRUPT다. 실제 미완료 경과시간을0으로 채우지 않는다. 주입한 가상 시계는 실제 성능 증거가 아니라고 별도 표시한다.

export_bundle/verify_bundle은 manifest/event bytes의 hash, event chain, manifest 결합과 복구 결과를 대조한다. bundle에는 비공개 조건/해시/경로가 포함될 수 있어 정적 웹/Git에 올리지 않는다. 도구는 저장소 밖 새 경로만 허용한다. 모델 없는 smoke는 실제 별도 프로세스 종료와 별도 프로세스의 bundle 재검산까지 실행한다. 실제 Colab VM 밖 보관/복구는 아직 시험하지 않았다.

GPU clock adapter, 고정된 실제 입력/모델 manifest, HaMeR 단계별 계측, 조건별 반복/인과적 스트리밍/서버 전체시간 연결은 다음 단계다. 모델 없는 기록기 검사를 그 항목들의 실행 완료로 세지 않는다.

## 강제 시간 제한 실행

`supervisor.run(command_array, new_private_output, cwd=existing_directory, timeout_seconds=...)`는 신뢰하는 로컬 명령을 shell 없이 실행한다. Windows Job Object에 bootstrap을 먼저 연결하고 gate를 연 뒤 명령과 자식들을 실행한다. timeout/중단/정상 leader 종료 모두 job을 닫아 남은 자식을 회수한다. POSIX는 새 process group을 사용하며 스스로 group을 벗어나는 비신뢰 코드를 격리하는 보안 sandbox는 아니다.

worker는 환경 변수 `RUNTIME_JOURNAL_DIRECTORY`에 Journal을 작성할 수 있다. supervisor_result.json의 감독기 상태와 worker 복구 상태는 별개다. exit0만으로 완료가 되지 않으며 정상 journal의 COMPLETED도 요구한다. 강제 종료는 worker 기록에 가짜 종료 event를 덧붙이지 않는다. supervisor 경과시간은 시작/회수 오버헤드 포함이고 실제 모델 성능과 구분한다. 명령/cwd는 private manifest에 보관하고 stdout/stderr는 수집하지 않는다.
