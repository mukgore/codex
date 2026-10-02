# 재현 절차와 범위

## 실행 정보

- 분석 호스트: Windows 10 build 26200, Python 3.10.3, CPU로 분석 스크립트 실행.
- 당시 설치 버전: NumPy 2.2.6, SciPy 1.15.3, openpyxl 3.1.5, pypdf 6.19.0, OpenCV 4.12.0.88, Matplotlib 3.10.8. 집계 실행 환경은 `reports/latest_run.json`에 기록. GPU 정보는 WMI 조회 권한 오류로 미확인.
- 로컬 개인 입력을 전제로 한 스냅샷 164개, 157382505 bytes. `data/` 전체는 공개 저장소에서 제외.
- 입력 설정: score max norms `angle=46.9413, dtw_angle=44.0014, accel=.1926`; weights `angle=.25, dtw_angle=.38, accel=.37`; threshold .25. 사람 JSON의 저장 raw 오차를 사용하며 추가 보간·제외 없음. SUS 결측이 있으면 complete row만 계산하지만 실제 양 파일에 누락은 없음.

## 점수·통계 재현

```powershell
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe analysis\audit.py
```

집계 파일: `reports/phase1_aggregates.json`. 개인별 상세 파일과 입력 해시는 로컬 `data/derived/`에만 생성된다. 분석 코드는 사람/HaMeR에 대해 저장된 세 원오차와 detection rate로 JavaScript와 같은 `clip(max(0,1-raw/max_norm))*detectionRate` 및 가중합을 적용한다. 저장된 score와 최대 1.11e-16 차이를 확인했다. 이것은 21×좌표를 다시 정규화·리샘플·각도화한 원오차의 독립 전체 구현이 아니다.

사람 점수표는 xlsx의 18행에서 회수할 수 있고 18 session JSON score와 일치한다. SUS는 10/21개 설문 응답표에서 별도로 계산했다. 개인 연결 키가 없어 수행 참가자 중 설문 응답자가 누군지 매칭하지 않는다. HTML에서 segment.duration은 keyframe match 뒤 recording 구간 시간만 합산하므로 match 대기·전환을 포함한 완료 경과시간이 아니다.

## 공격 재현

```powershell
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe analysis\replay_existing.py
```

로컬 원본 스냅샷의 `circle_edge_attack` 코드/JSON을 임시 작업폴더에 복사하고 저장된 온라인 관측에서 sequence matching 및 scoring 평가를 다시 한다. 이 재생은 기존 summary와 5개 집계값 모두 일치한다. Stage 1/2의 영상 픽셀 분석 및 runtime 측정은 재실행하지 않았고, `level3_DIP.mp4` 원본 입력도 확인되지 않았다. 제공 visibility 공격은 원 주변 노출 손가락 5비트 + 사전 원본 좌표 사전이며, 원 중심/크기만으로 식별하는 사용자 설명과는 분리해야 한다.

## 재현되지 않은 단계

1. n=4 예비 사람 실험 및 25개 MediaPipe 파라미터 조합: 보고서에는 값이 있으나 실행 출력·사람별 원오차·모델 결과 파일이 없다.
2. n=10 참가자 A/B: 사람별 조건 점수와 참가자-조건 연결이 없어서 p≈.012와 평균 A/B 차이를 재계산할 수 없다. 10명 SUS 원응답은 있으나 A/B 성적은 아님.
3. HaMeR 첫 6클립, 28조합 동영상→추론: notebooks 저장 output 없고 원 clip 영상·모델 가중치·실행 환경·원본 runtime log가 없음. 저장된 28조합 좌표와 점수 결과의 raw 오차→score 단계만 검증했다.
4. 원영상에서 사람의 손동작 오류와 모델 감지 실패를 분리: 참여자 원영상 부재로 불가.
5. 온라인 인증에서 직접 답안 제출, 가상 카메라, 시연 웹서비스까지의 성공률: 시험하지 않았다.

## 지표 이름 및 의미 차이

HTML/코드의 `mDA`는 일반 dynamic time warping이 아니다. 목표를 1.2배 길이로 리샘플하고 가능한 길이의 모든 sliding window에서 angle error 평균 최솟값을 고른다. 이를 `sliding-window angle match`로 설명한다. `mAc`는 정규화 랜드마크의 frame index 상 이차 차분 차이를 비교하며 실제 timestamp/FPS 간격으로 나누지 않는다. 따라서 물리적 가속도나 초당 motion energy가 아니다. `E_max`는 metadata 값으로 사용되지만 산출용 데이터 범위, 평가 전 고정 시점, 사람/모델 간 공통 세트의 정당화는 아직 입증되지 않았다.
