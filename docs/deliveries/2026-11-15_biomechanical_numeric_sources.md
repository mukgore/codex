# 생체 제약 수치의 출처 추적과 적용 전 대조

이번에는 학술 수치의 출처를 추적했다. 기존 BMC 수식 구현을 보편적인 허용값 확보로 바꾸지 않는다. [선택 수치/근거 JSON](../../references/chen2013_constraint_extraction.json), [계산 결과](../../reports/literature_velocity_consistency_20261115.json).

## 무엇을 확인했는가

BMC 본문 §3.1은 허용 한계를 측정·문헌·3D주석에서 얻는다고 설명하며 참고문헌[9]의 Chen Chen et al.2013과[33]의 Ryf/Weymann1995를 제시한다. 보충 §2의 HO-3D 설명은 제한된 동작 자료에서 얻은 각도 영역이 다른 동작을 지나치게 제한할 수 있음을 보여준다. 수식과 특정 자료의 범위를 구분한다. [BMC 본문](https://jankautz.com/publications/WeaklySupervised3DHand_ECCV20.pdf), [보충 자료](https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123620205-supp.pdf).

BIO-06 Chen Chen et al., *Constraint Study for a Hand Exoskeleton: Human Hand Kinematics and Dynamics*, Journal of Robotics2013, Article910961의 선택 부분을 읽었다. [DOI/출판사](https://doi.org/10.1155/2013/910961), [동일 논문 PDF 사본](https://pdfs.semanticscholar.org/5a84/3ade1ba00d075c4a9ae93c331dc7ee2c4b70.pdf). DOI/title/저자를 대조했고 원본2·6·11·12쪽을 로컬에서 렌더해 확인했다. 출판사 직접 열기는 timeout, 웹 PDF screenshot 일부도 실패해 별도 renderer를 사용했다. 논문 전체 검토나 독립 검토자 검증은 아니다.

## 추출한 사실과 아직 적용하지 않는 이유

| 추출 항목 | 위치·저장 범위 | 적용 전 남은 것 |
|---|---|---|
| 정적 가동 범위 | 표6의 엄지TMC·검지MCP/PIP/DIP 선택4행, degree | 표는 Cobos et al.[13]을 재인용한다. 원측정·개인차·중립자세/축·모델 대응 확인 필요 |
| 손가락 안의 연동 | §3.1 식(1)의 DIP/PIP·PIP/MCP 근사 관계 | 논문도 엄격한 등식이 아님을 명시. 모든 동작에 강제하거나 근거 없는 잔차 한계를 만들지 않음 |
| 속도 참고 | §6/표9의10초 무부하 빠른 쥐기·펴기, 남녀각10명, 검지3관절의 집계값 | 가정한 sinusoid와 주기 정의·과제/대상 의존. 사람의 안전/편안한 속도 한계가 아님 |

예를 들어 표6의 ‘굽힘50–90도’ 같은 보고값을 허용 자세 `[50,90]`으로 자동 바꾸지 않았다. MDH 회전과 BMC local 굽힘/벌림·MANO axis-angle/PCA는 같지 않다. radian 변환만으로 대응이 끝나지 않는다. 연동·가동 범위·속도의 참고 수치를 담은 이 JSON은 `REFERENCE_EXTRACTION_NOT_ADMISSIBLE_PROFILE`이며 실행 프로필 형식과 분리했다.

## 속도 수식/표의 조건부 재계산

§6은 `theta(t)=(D/2)*(cos(pi*t/t1)-1)`, 최대 속도 `pi*D/(2*t1)`, `t1=10/횟수`를 함께 적는다. 한 주기를 `T=10/평균 횟수`로 두고 다음 두 해석을 계산했다.

| 조건 | 결과 |
|---|---|
| `t1=T` | 표 값 / 계산값 비율이6개 모두 약2 |
| `t1=T/2` | 표와 최대 절대 차이 약0.000473rad/s |

이는 주기/반주기 용어와 곡선 해석의 **추가 확인 필요**를 보여준다. 논문 오류나 저자의 의도를 확정하지 않는다. 변환을 임의 선택해 속도 프로필에 적용하지 않았다. 표의 빠른 운동 집계가 일반적인 속도·가속도 허용 경계를 제공한다고 보지도 않는다.

## 코드·검사·기록

코드 `3895576`의 `analysis/literature_velocity_consistency.py`가 두 주기 해석을 명시해 계산한다. degree/radian과 주기 배율·참고 추출의 비승인 상태를 확인하는2개 검사를 추가했고 연구 전체200개가 통과했다. 실제 외부 기록은 코드·추출JSON·원PDF/렌더4페이지 등6입력과 기존 환경을 묶어 실행했다. 종료 `EXITED_ZERO`, 전후 snapshot 일치, 출력1개 재검사 통과다. 이는 문헌 산술 대조이며 새 손/사람 실험이 아니다.

실행 기록은 로컬 `private_artifacts/literature_velocity_record_20261115/`, 결과는 `literature_velocity_consistency_20261115/`에 있다. PDF/렌더는 `literature_review_20261115/`에 보관했다. 렌더는 별도 도구 폴더 `private_tools/pdf_review_20261115/`의 pypdfium2 4.30.0을 사용했다. 기존 모델·영상·연구 venv에 설치하거나 변경하지 않았다. 원문 다운로드/렌더·시각 검토는 산술 실행 기록 **이전에** 수행했으며, 그 시각/명령을 새 wrapper 안에서 실행한 것으로 소급하지 않는다.

## 다음 확인

BIO-07 Cobos et al.2008의 [저자기관 저장소](https://oa.upm.es/4040/)에서 원문과 측정/모델 정의를 더 확인한다. 기관 서지/초록은 확인했지만 PDF 직접 열기는 timeout이었다. BIO-08 Ryf/Weymann1995 [DOI](https://doi.org/10.1016/0020-1383(95)90116-7)는 BMC 참고문헌의 서지까지만 연결했으며 원문은 미열람이다. 이후 중립자세·관절축/부호·엄지·대상/측정 오차를 대응하고, coupled 영역과 실제 과제의 시간 한계를 확보한다. 기존 여섯 profile 규칙은 계속 미확인·랜덤8동작은 격리 상태다. [학술 색인](../academic_reference_index.md)과 [앞으로 할 일](../remaining_work_master_2026-11-15.md)을 함께 갱신했다.
