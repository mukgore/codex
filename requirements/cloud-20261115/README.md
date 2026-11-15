# 실제 Cloud 설치 metadata pins

2026-11-15 Debian13 x86_64에서 분리 설치 후 pip freeze한 값이다.
research: CPython3.12.14 / video: CPython3.10.22 / ui: CPython3.12.14.
research 원 입력은 root requirements.txt, video는 handcaptcha의
requirements-win-py310.txt(버전 선택 참고, Windows lock 재사용 아님),
ui는 websockets16.0이다. 환경별 pip check가 통과했다.

이 파일은 Linux wheel hash lock이 아니다. 최초 설치한 wheel 바이트의
동일성을 보장하지 않는다. 재설치 시 별도 wheelhouse/hash·pip check·검사를
다시 기록한다. cv2 배포물을 한 환경에 중복 설치하지 않는다.
MANO 환경/torch/smplx/chumpy는 설치하지 않았다.
