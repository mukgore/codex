# MANO·HaMeR·Text2HOI 접근과 실행 준비

사용자가 직접 접근 절차를 진행할 수 있다고 답했다. 파일 보유 없음은 이전 상태이며, 현재 MANO 다운로드 진행을 요청한 상태다. 비밀번호·인증코드·가입 이메일을 이 문서나 Git에 기록하지 않는다.

## 지금 사용자에게 필요한 단계

1. [MANO Register](https://mano.is.tue.mpg.de/register.php)에서 본인 계정 가입/개인정보/라이선스를 직접 확인한다. 가입 화면은 비상업 연구 목적 조건을 명시한다. 이 안내가 별도의 서비스 이용 허가를 뜻하지 않는다.
2. [MANO 로그인](https://mano.is.tue.mpg.de/login.php) 후 Download에서 MANO 모델 ZIP을 받는다. Text2HOI의 공식 경로는 mano_v1_2/models 아래의 MANO_LEFT.pkl·MANO_RIGHT.pkl·LICENSE.txt·info.txt다. HaMeR는 MANO_RIGHT.pkl을 요구한다. SMPL/SMPL-X body 모델로 대신하지 않는다.
3. 원본 ZIP과 동봉 license를 보존해 workspace의 `deliverables-review/private_artifacts/model_inputs/mano`에 저장한다. 사용자 다운로드 완료 후 파일명/경로를 회신한다. 모델/개인정보를 GitHub에 올리지 않는다.
4. 편입 도구 `python -m analysis.runtime_benchmark.model_assets --archive <downloaded_zip> --output ../private_artifacts/model_inputs/mano_intake_v1`가 ZIP 경로·중복 role·동일 version directory·동봉 license·크기·CRC·SHA256을 확인하고 새 폴더에 복사한다. pickle을 deserialize하지 않는다. 상태는 FILES_STAGED_NOT_LOADED/rights UNREVIEWED이며 유효한 model 구조나 이용 권한의 최종 판정이 아니다.

## 실제 실행 환경

PC GPU 조회는 Intel Iris Xe를 반환했고 PATH에서 nvidia-smi는 발견되지 않았다. 다른 장치/외부 GPU의 부재까지 증명하지 않는다. 현재 확인된 환경에서 CUDA 실행 가능하다고 가정하지 않는다.

HaMeR: [공식 README](https://github.com/geopavlakos/hamer#installation)의 Python3.10 환경/torch·모델·추가 dependency 절차와 [공식 Colab 링크](https://colab.research.google.com/drive/1rQbQzegFWGVOm1n1d-S6koOWDo7F2ucu?usp=sharing)를 우선한다. Colab 페이지는 이 세션의 비로그인 조회에서 Sign in만 표시되어 notebook 셀 전체를 검토하거나 실행했다고 주장하지 않는다. 사용자 계정으로 열고 GPU가 할당되는지 확인해야 한다. 유료 runtime을 생성하거나 과금을 승인하지 않았다.

실제 detector+HaMeR demo와 이미 알려진 손 ROI만 받는 model-only 실행은 다른 조건이다. 알려진 ROI/추정 자세를 주고 독립 공격 성능이라고 보고하지 않는다. 공식 demo는 추가 detector/ViTPose 가중치 및 렌더링을 포함하고 내부 다운로드도 호출하므로, 측정 시 setup 다운로드·load·추론·전송/동기화·렌더·저장을 구분해야 한다.

Text2HOI: [공식 install script](https://github.com/JunukCha/Text2HOI/blob/main/scripts/install.sh)는 Python3.8/PyTorch1.13/CUDA11.6 계열을 제시한다. 별도 환경을 준비한다. [README Demo tree](https://github.com/JunukCha/Text2HOI#folder-tree-for-demo)와 [checkpoint 목록](https://github.com/JunukCha/Text2HOI#checkpoints)에서 GRAB 경로를 따른다. obj.pkl·processed_object_meshes·contact_meshes와 해당 GRAB checkpoint가 필요하다. GRAB 전체 subject 학습 데이터부터 임의로 다운로드하지 않는다. [GRAB 공식 사이트](https://grab.is.tue.mpg.de/)의 본인 가입/약관·subject별 제한 확인이 별도다.

2026-11-05 공식 main revision을 GitHub connector의 main/main compare로 확인했다: HaMeR `3a01849f4148352e9260b69bf28b65d1671a4905`, Text2HOI `9643c209f08e28d7ed870095cea78c7244e4fd42`. 실제 실행에서 checkout/hash·모델 SHA·입력 SHA·설정/노출·frame 분모를 다시 고정한다. 가변 main만으로 과거 재현을 주장하지 않는다.

## 현재 준비 결과와 아직 하지 않은 것

파일 편입 검사4개 통과. Windows owned-process supervisor, 실제 MediaPipe113frame/timeout와 bundle 복구 기반은 이미 준비했다. 아직 MANO 구조 로드·HaMeR/Text2HOI 가중치 다운로드·해당 GPU 환경 설치·실제 추론은 수행하지 않았다. 공식 사이트 가입/약관 동의는 사용자가 직접 진행한다.

## 필요한 파일 사전 검사

`model_profiles.json`에 공식 고정 revision의 demo 핵심 파일 경로를 정리했다. Text2HOI GRAB은 `checkpoints/grab/`의 seq_cvae.pth·pointfeat.pth·contact_estimator.pth·texthom.pth·refiner.pth와 GRAB obj.pkl/processed_object_meshes를 사용한다. [고정 config](https://github.com/JunukCha/Text2HOI/tree/9643c209f08e28d7ed870095cea78c7244e4fd42/configs)와 [demo](https://github.com/JunukCha/Text2HOI/blob/9643c209f08e28d7ed870095cea78c7244e4fd42/demo/demo.py)를 대조했다. MPNet/CLIP는 추가 외부 model 자산이다. 학습용 전체 subject 데이터가 demo의 핵심 파일 목록에 포함된다고 가정하지 않는다.

`python -m analysis.runtime_benchmark.model_preflight --profile text2hoi_grab_demo --root <private_demo_root> --output ../private_artifacts/<new_report>`로 실제 존재·해시/byte를 검사한다. HaMeR는 --profile hamer_core다. 현재 빈 모델 입력 폴더에서는 HaMeR핵심3개/Text2HOI핵심9파일+1디렉터리 미확인으로 기록됐다. 이것은 전체 추가 의존성까지 포함한 파일 수가 아니다.

핵심 파일이 모두 있어도 CORE_ASSETS_PRESENT_NOT_LOADED이며 inference_ready=false다. 파일명만 맞춘 가짜 내용을 유효한 모델로 승인하지 않는 계약 검사3개가 통과했다. 실제 config 경로 해석·모델 구조 로드·source revision·허용 범위·GPU 실행은 다음 단계다. 모델 파일을 deserialize하는 것은 공식 출처와 사용자 접근 확인 후 실제 격리 runtime에서 수행한다.
