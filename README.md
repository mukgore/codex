# 가려진 손동작 CAPTCHA 연구 검증

이 저장소는 기존 연구의 결과를 재현하고 한계를 검토하는 공개 분석 저장소입니다. 원본 보고서·참여자 응답·개인별 좌표·영상·모델 산출물은 공개 저장소에 포함하지 않습니다. 공개 가능한 집계 결과와 분석 코드만 제공합니다.

현재 범위는 1차 연구 검증입니다. 후보 CAPTCHA 설계, 입력 UI, 웹서비스 및 신규 참여자 실험은 아직 사용자 승인 단계 전입니다. 진행 상황은 [PROJECT_STATUS.md](PROJECT_STATUS.md), 상세 1차 결과는 [phase1_review.md](docs/phase1_review.md)에서 확인할 수 있습니다.

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
