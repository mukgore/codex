# 독립 손 관절 추정 검증 보고서

평가 원자료: `reports/independent_hand_verification/external_hand_verification.json`
A/B 학습 원자료: `reports/independent_hand_verification/training_report.json`
평가 코드: `analysis/external_hand_verification.py`; 지표 근거와 공식은 `docs/reproducibility/hand_pose_metric_audit.md` 참고.
입력·소스·모델·결과 SHA-256 재현 명세: `reports/independent_hand_verification/provenance_github.json`.

## 데이터와 조건

- 데이터: GigaHands five official demo sequences; CC BY-NC 4.0; markerless capture-derived annotations
- 선택: one camera per each of five demo sessions, chosen before inference to maximize the share of annotated palm centers within the fixed center disk; this is a mask-focused convenience sample, not a random benchmark split
- 평가 영상 5개, 총 1,397프레임. p41 세션 영상 2개가 포함된 4명 편의 표본이며 모집단 무작위 표본이 아니다.
- 참조 좌표: GigaHands per-frame 2D keypoint JSONL; transformed with the same aspect-preserving contain geometry; labels with confidence <= 0 omitted. 독립 수작업 해부학 주석이 아닌 markerless 캡처 기반 좌표다.
- 가림 조건: 512×420, 중심 (256, 210), r=95px, RGB(7, 11, 16), 모든 프레임 적용; 경계 포함.
- 프레임별 `circle`과 `unoccluded`는 동일한 원본 영상·정답 좌표를 사용한다. 숨은 관절은 정답 좌표 중심이 원형 마스크 안에 있는 경우로 정의했다.
- 가림 적용 재생 영상 5개와 해시/프레임 인덱스: `reports/independent_hand_verification/occlusion_previews`.
- HaMeR는 손 좌우 정보를 받았고, MediaPipe는 양손 검출 후 정답 손목에 가장 가까운 손을 선택했다. MediaPipe의 손 선택은 평가 정답을 참조한 사후 매칭이다.

## 가림 조건 결과

MPJPE는 유효 좌표를 낸 프레임에 조건부로 계산했다. 실패 프레임은 이 오차에서 제외하되 검출 실패율에 남기고, PCK 분모에는 실패를 오답으로 포함했다. 각도·거리·가림 수준·연속 가림 시간·가속도·VERA-Hand 안정성은 원 JSON에 영상별로 보존돼 있다. A/B, C ridge, HaMeR는 손 검출기가 아니라 매 프레임 좌표를 내므로 이들의 1.0은 유효 좌표 출력률이다. MediaPipe만 실제 검출 성공률이며, HaMeR는 정답 손 방향을 사용한 고정 전체 프레임 crop이다.

| 모델 | MPJPE px | MPJPE palm | 가린 관절 palm | 보이는 관절 palm | PCK@0.2 | 유효 출력/MP 검출률 | 실패 | PCK AUC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| C offline 2D | 196.48 | 6.3734 | 6.4173 | 5.7341 | 0.0008 | 1.0000 | 0.0000 | 0.0029 |
| C offline 3D-projection | 135.76 | 4.3549 | 4.3407 | 4.5628 | 0.0023 | 1.0000 | 0.0000 | 0.0079 |
| A current-only 2D | 76.62 | 2.3513 | 2.3046 | 3.0324 | 0.0030 | 1.0000 | 0.0000 | 0.0108 |
| B past+current 2D | 79.31 | 2.4457 | 2.3998 | 3.1139 | 0.0027 | 1.0000 | 0.0000 | 0.0096 |
| A current-only 3D-projection | 77.98 | 2.4031 | 2.3577 | 3.0639 | 0.0012 | 1.0000 | 0.0000 | 0.0085 |
| B past+current 3D-projection | 80.22 | 2.4762 | 2.4320 | 3.1187 | 0.0023 | 1.0000 | 0.0000 | 0.0093 |
| HaMeR | 65.39 | 2.0530 | 2.0296 | 2.3939 | 0.0258 | 1.0000 | 0.0000 | 0.0405 |
| MediaPipe Hands | 74.27 | 3.1736 | 3.4457 | 0.3783 | 0.0139 | 0.2742 | 0.7258 | 0.0135 |

### 영상별 가린 관절 오차

| 영상 | C offline 2D | C offline 3D-projection | A current-only 2D | B past+current 2D | A current-only 3D-projection | B past+current 3D-projection | HaMeR | MediaPipe Hands |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| brics-odroid-016_cam0_1727030430697566 | 12.086 | 9.162 | 4.055 | 4.274 | 4.103 | 4.309 | 2.341 | 3.467 |
| brics-odroid-026_cam1_1726962101793664 | 3.302 | 1.988 | 1.639 | 1.681 | 1.684 | 1.710 | 1.632 | n/a |
| brics-odroid-023_cam0_1726963265350610 | 2.464 | 2.280 | 1.010 | 0.967 | 0.989 | 0.964 | 0.506 | n/a |
| brics-odroid-015_cam1_1725202053204578 | 7.295 | 3.961 | 2.476 | 2.566 | 2.595 | 2.623 | 3.382 | 1.099 |
| brics-odroid-024_cam0_1726248075919808 | 2.980 | 1.748 | 0.880 | 0.984 | 0.902 | 1.005 | 0.939 | n/a |

## 시간 정보 효과와 대응 비교

왼쪽 모델 − 오른쪽 모델의 차이다. 음수 MPJPE는 왼쪽 오차가 낮음을 뜻한다. 95% 구간은 프레임이 아니라 영상 단위 10,000회 대응 부트스트랩이다. 영상 5개라 구간은 탐색적이다.

| 비교 (왼쪽−오른쪽) | Δ MPJPE palm | 95% 영상 bootstrap CI | Δ PCK@0.2 | 95% CI |
|---|---:|---:|---:|---:|
| A current-only 2D − B past+current 2D | -0.0812 | [-0.1527, -0.0097] | 0.0014 | [-0.0015, 0.0064] |
| HaMeR − A current-only 2D | -0.2601 | [-1.0434, 0.4459] | 0.0363 | [0.0023, 0.0848] |
| HaMeR − B past+current 2D | -0.3413 | [-1.1867, 0.3789] | 0.0377 | [0.0007, 0.0912] |
| MediaPipe Hands − A current-only 2D | -1.2076 | [-1.5262, -0.8890] | 0.0068 | [-0.0084, 0.0284] |
| MediaPipe Hands − B past+current 2D | -1.3579 | [-1.6177, -1.0982] | 0.0082 | [-0.0021, 0.0271] |
| C offline 3D-projection − A current-only 2D | 1.7821 | [0.7189, 3.3700] | -0.0005 | [-0.0080, 0.0066] |
| C offline 3D-projection − B past+current 2D | 1.7009 | [0.6913, 3.2323] | 0.0009 | [-0.0032, 0.0064] |

### 가림 지속 시간별 숨은 관절 오차

영상별 joint-frame 수로 가중한 요약이며, 긴 구간은 서로 독립 표본으로 간주하지 않는다.

| 모델 | 연속 가림 | 관절 프레임 수 | 오차 palm |
|---|---:|---:|---:|
| A current-only 2D | <0.1s | 553 | 3.4745 |
| A current-only 2D | 0.1-0.5s | 2,155 | 3.5830 |
| A current-only 2D | 0.5-1s | 1,125 | 1.7800 |
| A current-only 2D | >=1s | 23,265 | 2.1837 |
| B past+current 2D | <0.1s | 553 | 3.6471 |
| B past+current 2D | 0.1-0.5s | 2,155 | 3.7659 |
| B past+current 2D | 0.5-1s | 1,125 | 1.8310 |
| B past+current 2D | >=1s | 23,265 | 2.2711 |
| HaMeR | <0.1s | 553 | 2.5389 |
| HaMeR | 0.1-0.5s | 2,155 | 2.5942 |
| HaMeR | 0.5-1s | 1,125 | 1.7911 |
| HaMeR | >=1s | 23,265 | 1.9767 |
| MediaPipe Hands | <0.1s | 394 | 3.5883 |
| MediaPipe Hands | 0.1-0.5s | 1,383 | 3.8575 |
| MediaPipe Hands | 0.5-1s | 58 | 2.0148 |
| MediaPipe Hands | >=1s | 11,918 | 2.0754 |

## 실행 시간

모델 시간은 영상 디코드·공통 가림 변환 시간과 분리했다. A/B의 프레임 시간에는 입력 크기 변환이 포함된다. HaMeR 시간은 8프레임 배치 추론 시간의 합이며, MP와 A/B는 프레임 호출 시간의 합이다. C 오프라인 ridge는 전체 영상 벡터화 실행이라 프레임별 분포가 없다.

| 모델/조건 | 전체 5영상 초 | 평균 초/영상 | 평균 ms/프레임 | 관측 p50 ms | 관측 p95 ms | p95 영상평균 ms | 지연 표본 단위 | 1.5× 평균 초과 영상 |
|---|---:|---:|---:|---:|---:|---:|---|---:|
| C offline 2D / unoccluded | 2.53 | 0.506 | 1.808 | 1.859 | 1.895 | 1.960 | per-video average | 없음 |
| C offline 3D-projection / unoccluded | 2.42 | 0.483 | 1.785 | 1.746 | 1.767 | 2.186 | per-video average | 없음 |
| A current-only 2D / unoccluded | 3.82 | 0.763 | 2.718 | 2.668 | 3.476 | 2.850 | per-frame | 없음 |
| B past+current 2D / unoccluded | 5.86 | 1.171 | 4.174 | 4.089 | 5.324 | 4.265 | per-frame | 없음 |
| A current-only 3D-projection / unoccluded | 3.66 | 0.733 | 2.616 | 2.564 | 3.315 | 2.758 | per-frame | 없음 |
| B past+current 3D-projection / unoccluded | 5.73 | 1.146 | 4.103 | 3.990 | 5.173 | 4.331 | per-frame | 없음 |
| HaMeR / unoccluded | 2427.47 | 485.495 | 1699.446 | 1625.551 | 2195.787 | 1990.128 | per-chunk divided by frames | brics-odroid-016_cam0_1727030430697566 |
| MediaPipe Hands / unoccluded | 30.57 | 6.115 | 22.349 | 21.102 | 30.439 | 24.471 | per-frame | 없음 |
| C offline 2D / circle | 2.32 | 0.464 | 1.658 | 1.726 | 1.734 | 1.822 | per-video average | 없음 |
| C offline 3D-projection / circle | 2.63 | 0.527 | 1.935 | 2.091 | 2.164 | 2.183 | per-video average | brics-odroid-016_cam0_1727030430697566 |
| A current-only 2D / circle | 3.69 | 0.738 | 2.657 | 2.577 | 3.311 | 2.823 | per-frame | 없음 |
| B past+current 2D / circle | 5.81 | 1.163 | 4.149 | 4.114 | 5.196 | 4.261 | per-frame | 없음 |
| A current-only 3D-projection / circle | 3.80 | 0.760 | 2.717 | 2.616 | 3.582 | 2.862 | per-frame | 없음 |
| B past+current 3D-projection / circle | 5.55 | 1.110 | 3.961 | 3.962 | 5.042 | 4.118 | per-frame | 없음 |
| HaMeR / circle | 2328.45 | 465.691 | 1646.278 | 1607.879 | 2127.303 | 1788.776 | per-chunk divided by frames | 없음 |
| MediaPipe Hands / circle | 22.83 | 4.566 | 15.239 | 12.686 | 30.621 | 22.725 | per-frame | brics-odroid-016_cam0_1727030430697566 |

### 모델별·영상별 시간 (원본초/가림초)

| 모델 | brics-odroid-016_cam0_1727030430697566 | brics-odroid-026_cam1_1726962101793664 | brics-odroid-023_cam0_1726963265350610 | brics-odroid-015_cam1_1725202053204578 | brics-odroid-024_cam0_1726248075919808 |
|---|---:|---:|---:|---:|---:|
| C offline 2D | 0.71/0.55 | 0.69/0.67 | 0.34/0.27 | 0.56/0.58 | 0.23/0.24 |
| C offline 3D-projection | 0.67/0.82 | 0.56/0.67 | 0.28/0.36 | 0.59/0.47 | 0.32/0.30 |
| A current-only 2D | 1.06/1.02 | 1.05/0.94 | 0.47/0.50 | 0.86/0.87 | 0.37/0.36 |
| B past+current 2D | 1.58/1.59 | 1.54/1.57 | 0.72/0.72 | 1.45/1.37 | 0.57/0.57 |
| A current-only 3D-projection | 0.96/1.04 | 0.95/1.02 | 0.45/0.50 | 0.95/0.89 | 0.36/0.36 |
| B past+current 3D-projection | 1.54/1.46 | 1.48/1.47 | 0.76/0.69 | 1.41/1.40 | 0.54/0.54 |
| HaMeR | 790.81/692.89 | 595.25/604.00 | 280.44/276.98 | 542.20/534.22 | 218.77/220.36 |
| MediaPipe Hands | 8.25/9.38 | 7.38/4.69 | 4.32/2.08 | 7.41/5.04 | 3.22/1.65 |

### 초기화·warm-up을 포함한 모델 실행 총계

모델별 추론 시간에 한 번의 backend 모델 초기화와 모든 영상·조건별 초기화/warm-up을 더했다. 공통 영상 디코드·좌표 변환은 별도라 이 표에 없다.

| 모델 | backend 초기화 초 | 영상별 모델 초기화 합계 초 | warm-up 합계 초 | 추론 합계 초 | 위 항목 합계 초 |
|---|---:|---:|---:|---:|---:|
| C offline 2D | 0.187 | 0.000 | 0.000 | 4.850 | 5.037 |
| C offline 3D-projection | 0.187 | 0.000 | 0.000 | 5.051 | 5.238 |
| A current-only 2D | 0.072 | 0.000 | 0.034 | 7.506 | 7.612 |
| B past+current 2D | 0.072 | 0.000 | 0.034 | 11.671 | 11.778 |
| A current-only 3D-projection | 0.072 | 0.000 | 0.029 | 7.464 | 7.565 |
| B past+current 3D-projection | 0.072 | 0.000 | 0.031 | 11.284 | 11.386 |
| HaMeR | 29.972 | 0.000 | 34.634 | 4755.928 | 4820.534 |
| MediaPipe Hands | 0.000 | 0.070 | 0.439 | 53.406 | 53.915 |

### 학습 held-out 결과

| 도메인 | 모델 | 검증 NME | held-out NME | held-out 가림 관절 NME | PCK@0.2 | 클립/프레임 |
|---|---|---:|---:|---:|---:|---:|
| 2d | A_current | 0.005362 | 0.005598 | 0.004826 | 1.0000 | 240/9,066 |
| 2d | B_past_current | 0.004824 | 0.004955 | 0.004213 | 1.0000 | 240/9,066 |
| 3d | A_current | 0.004498 | 0.004592 | 0.003910 | 1.0000 | 240/9,066 |
| 3d | B_past_current | 0.004890 | 0.004946 | 0.004260 | 1.0000 | 240/9,066 |
| recorded | A_current | 0.213907 | 0.159651 | n/a | 0.7730 | 2/55 |
| recorded | B_past_current | 0.202499 | 0.257630 | n/a | 0.4345 | 2/55 |

### 기존 CAPTCHA 점수 계산과의 관계

아래 값은 각 모델의 전체 영상 관절 시퀀스를 production 방식에 대입한 **점수 유사값**이다. 실제 CAPTCHA 시도나 통과율이 아니다. MediaPipe는 유효 검출 영상이 1개뿐이라 그 영상만 요약한다.

| 모델 / 가림 | 점수 유사값 평균 | 범위 | 임계값 통과 영상 | 유효 영상 |
|---|---:|---:|---:|---:|
| C offline 2D / circle | 0.3056 | 0.0000–0.5979 | 3/5 | 5 |
| C offline 3D-projection / circle | 0.4483 | 0.0000–0.8329 | 3/5 | 5 |
| A current-only 2D / circle | 0.3042 | 0.0000–0.5328 | 3/5 | 5 |
| B past+current 2D / circle | 0.4135 | 0.0000–0.7267 | 3/5 | 5 |
| A current-only 3D-projection / circle | 0.3915 | 0.0000–0.7256 | 3/5 | 5 |
| B past+current 3D-projection / circle | 0.4093 | 0.0000–0.7084 | 3/5 | 5 |
| HaMeR / circle | 0.3087 | 0.0000–0.6486 | 2/5 | 5 |
| MediaPipe Hands / circle | 0.0385 | 0.0385–0.0385 | 0/1 | 1 |

## 실행 환경

- 하드웨어: Windows 10 Pro 26H2, build 26300; Intel Core i5-1135G7 @ 2.40 GHz; 8 logical processors; 15.8 GiB RAM; CPU-only inference.
- HaMeR 전 모델 초기화는 29.972초였고 전체 추론 파일은 11:47에 저장됐다. 개별 모델의 준비·warm-up·프레임/배치 시간은 backend JSON에 분리 기록했다.

## 소프트웨어·모델 버전

- **local:** {"device": "CPU", "inference_stack": "NumPy/OpenCV ridge regression", "numpy": "1.23.5", "opencv": "4.10.0", "python": "3.10.3 (tags/v3.10.3:a342a49, Mar 16 2022, 13:07:40) [MSC v.1929 64 bit (AMD64)]", "weights": {"2d": "03ce1ef70b32d92994a8397aa519955d5b6062b7d2188a9b28188fff57a8cbdc", "3d": "a6f5c0d2a7278655d746718d3ec0189d73249bfc7a7d88be831d9cfd4c409fc2"}}; 초기화 0.187초.
- **realtime:** {"device": "CPU", "inference": "frame-by-frame A/B; resize included in per-frame timing", "models": {"2d_A_current": {"checkpoint_sha256": "ca6848fd3b6677ab27afe065c018ca9678d2e8a33f138afa3d88dc68d79b765b", "domain": "2d", "input_size_wh": [80, 66], "mode": "A_current"}, "2d_B_past_current": {"checkpoint_sha256": "490c8abb0785765adcb9e7a48990c8c7fc6ef3ed3b776b471745e182db2dcc82", "domain": "2d", "input_size_wh": [80, 66], "mode": "B_past_current"}, "3d_A_current": {"checkpoint_sha256": "8065b2365b787270999250215ec0f8eeb3bc186061f9aac0ff55cc166d138c04", "domain": "3d", "input_size_wh": [80, 66], "mode": "A_current"}, "3d_B_past_current": {"checkpoint_sha256": "0bd1507763d868352fbfb46a86e996c47da123ab53f71bf9e9cabc3dee035473", "domain": "3d", "input_size_wh": [80, 66], "mode": "B_past_current"}}, "numpy": "1.23.5", "opencv": "4.10.0", "python": "3.10.3 (tags/v3.10.3:a342a49, Mar 16 2022, 13:07:40) [MSC v.1929 64 bit (AMD64)]", "threads": 4, "torch": "2.5.1+cpu"}; 초기화 0.072초.
- **hamer:** {"checkpoint_sha256": "e5cc06f294d88a92dee24e603480aab04de532b49f0e08200804ee7d90e16f53", "device": "CPU", "numpy": "1.23.5", "opencv": "4.10.0", "python": "3.10.3 (tags/v3.10.3:a342a49, Mar 16 2022, 13:07:40) [MSC v.1929 64 bit (AMD64)]", "threads": 4, "torch": "2.5.1+cpu", "upstream_revision": "3a01849f4148352e9260b69bf28b65d1671a4905"}; 초기화 29.972초.
- **mediapipe:** {"device": "CPU", "graph": "mediapipe.solutions.hands.Hands", "mediapipe": "0.10.14", "numpy": "1.26.4", "opencv": "4.10.0", "python": "3.10.3 (tags/v3.10.3:a342a49, Mar 16 2022, 13:07:40) [MSC v.1929 64 bit (AMD64)]"}; 초기화 0.000초.

### 프로세스 메모리 고수위

Windows PROCESS_MEMORY_COUNTERS_EX의 process peak working set이다. C/A/B/MediaPipe는 한 backend 프로세스가 전체 영상·조건을 처리할 때의 값으로, 모델별 단독 RAM 사용량은 아니다.

| backend | peak working set GiB | 측정 방식 |
|---|---:|---|
| local | 1.212 | Windows PROCESS_MEMORY_COUNTERS_EX at process exit |
| realtime | 1.337 | Windows PROCESS_MEMORY_COUNTERS_EX at process exit |
| mediapipe | 1.229 | Windows PROCESS_MEMORY_COUNTERS_EX at process exit |
| HaMeR | 약 3.39 | 실행 중 Get-Process 표본에서 관측된 최대 working set; OS high-water 계측은 아님 |

## 결론과 한계

- 이 5개 가림 영상에서 HaMeR가 A/B보다 pooled 위치 오차가 낮았다. A current-only는 B past+current보다 2D 모델의 가린 관절 평균 오차가 낮았다. A−B 정규화 MPJPE CI는 0을 포함하지 않았지만, HaMeR−A/B MPJPE CI는 0을 포함해 HaMeR 우위를 통계적으로 확정할 수 없다.
- A/B의 합성 held-out 이점은 외부 실제 영상에 그대로 전이되지 않았다. 현재 표본에서는 두 실시간 모델 모두 가림 관절 오차가 크고, PCK@0.2가 매우 낮아 정확한 추정 성능을 입증하지 못했다.
- MediaPipe는 보이는 관절에는 낮은 오차를 보였지만 가림 조건 검출 성공률이 낮았다. 조건부 MPJPE와 전체 PCK를 함께 봐야 한다.
- 표본 5개, 참여자 4명, p41 영상 2개, convenience selection 및 자동 참조 라벨 때문에 일반화 주장은 불가하다. bootstrap은 영상 단위이며 모집단 근거가 아닌 기술 통계다.
- A/B는 hand-present 자료로 학습됐다. 좌표를 매 프레임 반환하지만 손 부재를 판별하지 않으므로, 독립 hand-presence 검출/실패 정책이 필요한 배포 기능으로 남아 있다. 브라우저 직접 실행은 아직 검증하지 않았다.
- 세부 관절별/가림 수준/연속 가림 시간/실패 프레임/production 점수 구성요소/모든 영상별 결과는 연결된 JSON에 보존했다.
