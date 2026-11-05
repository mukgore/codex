# 모델·자료 준비 상태

**2026-11-05 갱신:** 사용자가 직접 접근 가능/절차 안내 필요라고 회신했다. [공식 접근·저장·사전 검사 절차](2026-11-05_model_access_steps.md)를 안내하고 MANO ZIP 경로 회신을 기다린다. 아래 보유 없음은 이전 확인 상태이며, 아직 새 모델 파일의 수신/실제 추론은 없다.

사용자는 Text2HOI/HaMeR의 MANO 모델과 checkpoint를 이미 보유하는지 질문에 **없음**이라고 답했다. 원본 촬영 영상 질문과 별개의 확인이다. CLI workspace의 filename 점검에서도 .ckpt/.pth/.pkl은0개였다. 이는 PC 전체/클라우드에 파일이 없음을 증명하는 탐색이 아니다.

## 공식 실행 입력

2026-11-04 [공식 Text2HOI README](https://github.com/JunukCha/Text2HOI)는 demo 데이터 구조에 MANO 좌우 모델, 대상 dataset의 object 자료/mesh와 checkpoints를 명시한다. R1의 GRAB 경로를 정해도 실제 모델·물체 입력·환경이 필요하다. README의 코드 공개를 dataset/model의 서비스 사용 허가로 간주하지 않는다.

[GRAB 공식 안내](https://grab.is.tue.mpg.de/)는 가입·license 동의 후 dataset 접근과 subject별 제한 준수를 명시하고, 상업 사용 문의를 별도로 안내한다. [MANO 공식 안내](https://mano.is.tue.mpg.de/)도 가입·license 동의 후 다운로드하도록 설명한다. [MANO license 페이지](https://mano.is.tue.mpg.de/license.html)는 비상업 과학 연구용이라고 표기한다. 이번에는 계정 생성/동의/접촉·자료 다운로드를 수행하지 않았다. GRAB license 본문 조회는 timeout되어 전체 문구 검토를 완료했다고 표시하지 않는다.

[공식 HaMeR README](https://github.com/geopavlakos/hamer)는 학습 모델 다운로드와 별도의 MANO_RIGHT.pkl을 요구한다. 해당 파일이 없는데 실제 HaMeR 추론 시간을 측정했다고 보고하지 않는다. 모델 없는 runtime journal smoke는 로그 검증일 뿐이다.

## 현재 판정

- 자체 작성 3D skeleton fixture: 코드/렌더/가림 연결 완료 범위. 실제 사람/물체 접촉·정확한 3D 정답·R1 재현과 구분한다.
- 이미 저장소에 있던 baseline 영상1개: 실제 관찰 source이며 새 MediaPipe113frame 추정 가능. 독립 source 다수/정밀 3D 정답/권리 승인으로 승격하지 않는다.
- R1 Text2HOI/GRAB/MANO: 모델·자료·허용 범위·맞는 실행환경 입력 대기.
- 실제 HaMeR 추론·다조건 시간 비교: 모델·해당 환경 입력 대기. 과거10시간 회고로 빈 측정값을 채우지 않는다.
- 운영 release: 실제 권리/검수·사람·공격 기준/승격 증거 대기. 합성 registry test를 실제 승인으로 등록하지 않는다.

공식 요구를 확인한 준비 상태 보고서이며 새 논문 수치 재현·서비스 허가·특허 신규성 판단 결과가 아니다.
