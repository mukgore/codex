# 가려진 손동작 CAPTCHA 연구 검증

이 저장소는 기존 연구의 결과를 재현하고 한계를 검토하는 공개 분석 저장소입니다. 원본 보고서·참여자 응답·개인별 좌표·영상·모델 산출물은 공개 저장소에 포함하지 않습니다. 공개 가능한 집계 결과와 분석 코드만 제공합니다.

1차 연구 검증 결과는 [PROJECT_STATUS.md](PROJECT_STATUS.md)와 [phase1_review.md](docs/phase1_review.md)에 보존되어 있습니다. 이후 추가 지시에 따라 영상 풀·3D 손/물체 CAPTCHA 및 실용성 검증 **명세**를 작성했습니다. [2026-10-26 저장소 감사 및 CAPTCHA 아키텍처 비교](docs/captcha_architecture_and_repo_audit_2026-10-26.md)에 현재 확인된 구현 결함과 미검증 항목을 모았습니다. 이 저장소의 명세를 신규 서비스 구현·보안성 검증·참여자 실험 완료로 읽지 마세요.

`handcaptcha` 확장 렌더러의 누락 가림·시간축 검사 수정안은 [별도 적용 패치](patches/handcaptcha_fail_closed_mask_2026-10-26.patch)에 보존했습니다. GitHub 연결이 그 저장소의 브랜치 쓰기를 거부하여 아직 원 저장소에 반영되지 않았습니다.

## 재현 가능한 분석

Windows PowerShell에서 저장소 루트로 이동하고, Python 3.10 이상으로 로컬 가상환경을 만든 다음:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe analysis\audit.py
```

`analysis/audit.py`는 로컬 `data/raw/`에 원자료 스냅샷이 있을 때 개인 자료를 읽어 집계합니다. `data/`는 Git에서 제외되어 있으므로, 명세에 따라 확보한 원본 파일을 사용자가 로컬에 배치해야 합니다. 입력 데이터는 수정하지 않습니다. 집계 보고서는 `reports/phase1_aggregates.json`에 씁니다. 원문 값, 결측 분모, 공개용 집계 해시 및 실행 환경 정보는 별도 로컬 `data/derived/`에 기록됩니다.

기존 원 움직임 기반 공격은 `analysis/replay_existing.py`로 저장된 관측 결과부터 재생할 수 있습니다. 이 재생은 원본 동영상을 다시 처리하지 않으며, 픽셀 추출·카메라 입력·서버 인증 경로를 검증하지 않습니다. 필요한 코드와 원자료 스냅샷은 비공개 로컬 보관본에 있습니다.

## 자료 처리

- 보고서 원문은 수정하지 않습니다.
- 참여자 단위 자료, 설문 원응답, 좌표, 동영상, 로컬 파일 목록과 해시, 임시 작업 산출물은 공개하지 않습니다.
- 결과를 재현할 수 없는 과거 실험은 수행된 것처럼 표현하지 않습니다.
- 핵심 검증 결과와 남은 자료 공백은 [docs/phase1_review.md](docs/phase1_review.md)에 있습니다.


## Reproducibility follow-up (2026-10)

Independent, conditional replay of the archived A/B and prod_v2_pool records and the paired A/B summary are organized under [analysis/reproducibility](analysis/reproducibility), [docs/reproducibility](docs/reproducibility), and [reports/reproducibility](reports/reproducibility). See the [artifact map](docs/reproducibility/README.md). Raw records, participant-level rows, per-session errors, and input hashes remain local and are excluded from Git. Historical executed-build provenance remains unresolved.

## 실용성 검증 및 표준 채점 전환 v0.3

- [실용성·사업성 검증 요구사항](docs/practical_validation_requirements_v0.3.md): 오답 거부, 미관찰 문제, 입력 보호와 가림의 추가 효과, 사용자 부담, 비용, 구매 증거를 분리합니다.
- [prod 분석 및 표준 수학 기반 채점 전환](docs/scoring_standardization_v0.3.md): handcaptcha prod의 고정 버전을 분석하고 DTW·시간 미분·오류율 곡선·임계값 선택의 이행 요구사항을 정의합니다.
- [실험용 수학 모듈](validation_v03/standard_metrics.py)과 [합성 테스트](tests/test_standard_metrics.py)를 추가했습니다. 실제 사람/공격 성능 개선이나 prod 교체·배포를 의미하지 않습니다.

```bash
python -m unittest discover -s tests -p test_standard_metrics.py -v
```

## 영상 풀·가림 생성·송출 설계 v0.4

[동작 영상 풀 확보·가림 생성·보안 송출 요구사항](docs/video_pool_occlusion_delivery_requirements_v0.4.md)은 기존 handcaptcha 구현의 정적 감사, 영상 확보·사용권·중복 관리, 전 프레임 가림 및 재디코딩 검사, 정답 비공개·세션 기반 송출, 반복노출 공격과 운영 인수 시험을 정의합니다. 설계 문서이며 신규 영상 생성·보안 실험·배포를 수행했다는 의미가 아닙니다.

[3D 손·물체 상호작용 후보](docs/3d_hand_object_challenge_requirements_v0.1.md)는 물체의 접촉 단서를 포함하는 생성형 과제와 사람/강한 공격 비교를 정의합니다. 현재는 제안·미검증이며 기존 촬영 영상 풀을 대체하거나 실시간 렌더링이 가능하다고 확정하지 않습니다.
