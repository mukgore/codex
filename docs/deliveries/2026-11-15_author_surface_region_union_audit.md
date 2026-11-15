# 저자 표면 부위 대응과 기존 가림의 합집합 검사 — 2026-11-15

[원래 연구 실행 순서](../research_goal_followups_2026-11-10.md#실행-순서와-기존-백로그-연결)를 다시 확인했다. 등록 촬영21행 원본 경로0개·선별 관측값0개이며 실제 촬영/사람 입력은 대기다. 앞선 [시작 자세 비교](2026-11-15_visible_cue_conditioned_generation.md)의 다음 독립 개발인 표면 부위의 근거를 보강한다. 모델 영역/기술 가림과 임상·사람·보안을 구분한다.

## 확인한 원문과 저자 코드

BIO-09 CPF [보충자료](https://openaccess.thecvf.com/content/ICCV2021/supplemental/Yang_CPF_Learning_a_ICCV_2021_supplemental.pdf) §A.2–A.3/PDF1–2쪽, 그림3–4를 렌더하고 읽었다. 저자는 뼈 연결과 control point를 이용해 모델 정점을17개 부위로 나눈다. 우리 기존 방식은 가장 가까운 **선분**으로 배정한 임시 영역으로, 같은17부위 자료를 이미 쓴 것은 아니다.

숫자 ID와 부위 이름의 대응표는 논문에 직접 인쇄돼 있지 않다. 그림3의 부위 이름/색과 고정 [CPF 색상 코드](https://github.com/lixiny/CPF/blob/a9577729716f7579c206b8978bdd10af42dad0ab/lib/viztools/utils.py)의 `CONTACT_REGION` 값을 대조해 프로젝트 대응표를 만들었다. [대응표/원출처](../../references/cpf_model_surface_region_review.json)는 코드 import 없이 AST로 원저자 RGB 리터럴과 대조하며, 실제 모델의 부위 중심점/뼈와 추가 확인한다. 숫자/이름 대응을 저자가 제공한 임상 정답표로 표시하지 않는다.

CPF `a9577729`와 manotorch `a2a70c59`의 `assets/anchor` tree는 동일 `9e95457b…`이고 `merged_vertex_assignment.txt` blob은 `139d6127…`로 같다. 이미 보관한778개·17label 자료와 연결된다. 현재 [저자 MANO loader](https://github.com/lixiny/manotorch/blob/a2a70c591f91551078b7bb2af9b5d9f275b626e0/manotorch/manolayer.py)는 원 모델의 정점·face 배열을 읽고 손끝과 관절 순서를 별도로 처리한다. 우리 실제 양손의 index 연결 구조와 기하를 확인해야 하며 크기가778이라는 사실만으로 호환을 단정하지 않는다.

**원문 불일치 보존:** §A.2의 Palm Metacarpal/Carpal control point 병합 이름은 그림4와 §A.3의 Carpal CP5/10/20 설명과 맞지 않는 부분이 있다. 임의로 고친 병합 알고리즘을 원논문 재현이라고 하지 않는다. 이 검사는 저자 제공 label을 읽고 손가락 부위를 검토하며, 문제의 control point 병합을 새로 실행하지 않는다. 손바닥/손목의 세부 해부학 주석은 미확인이다.

고정 CPF palette·manotorch loader 두 파일은 원 Git blob 바이트와 일치하는 private 사본으로 보존했다. 저자 코드를 import/설치하지 않았고 pickle mapping은 받거나 실행하지 않았다. CPF palette 코드의 별도 배포 허가는 확인하지 않았으므로 사본을 공개 저장소에 넣지 않는다. manotorch 코드 Apache-2.0과 MANO 모델의 별도 라이선스를 구분한다.

## 실제 실행 전 계획

1. 양손 mean-neutral의17개 label 비어 있음 여부,15손가락 부위 중심점과 예상 뼈 선분, vertex-index 기반 삼각형 연결을 검사한다. 중심점 일치만으로 모든 경계를 임상적으로 검증했다고 하지 않는다.
2. 중지의 proximal/intermediate 부위 정점과 접하는 **면 전체**를 선택한다. 이를 기존 nearest-rest-bone 보호 면과 합친다. 기존 영역을 빼거나 줄이지 않는다.
3. [기존 paired-preflex32렌더](2026-11-15_visible_cue_conditioned_generation.md)의 저장 좌표·고정 중립 회전·카메라를 그대로 사용해800프레임의 합집합 amodal 영역을 다시 그린다. 투영이 기존 저장 좌표와 같고 원래 proxy 픽셀이 모두 합집합에 포함되는지 확인한다.
4. 기존 가림/H.264가 있는16쌍에서는 **원래 가림 반경/픽셀을 그대로** 두고 합집합 ROI/기존2픽셀 codec core와 양쪽 영상의 기존 채널값30 기준을 확인한다. 추가 영역이 드러나면 별도 hold로 기록하며 새 원/임계값에 맞춰 결과를 바꾸지 않는다.
5. 모델 추론·새 영상 인코딩·운영 영역 변경은0회다. 사례별 시각·wall/자체CPU는 검사 시간으로 기록하며 새 영상 생성시간이라고 하지 않는다. 모든 원본/기존 receipt를 전후 검산한다.

관련 기하 검사4개와 실제 오프라인 camera 연계15개 검사를 통과했다. 실제 실행 뒤 결과와 필요한 입력을 아래에 추가한다. 기존16개 기술 후보는 결과와 관계없이 연구용 격리이며 풀/브라우저 채택0개를 유지한다.

## 실제 완료 결과

| 확인 범위 | 실제 결과 | 해석 한계 |
| --- | --- | --- |
| author palette·assignment·loader | 원 Git blob 바이트 일치, AST RGB 대조 통과 | 저자 numeric ID/이름표를 직접 받은 것은 아님 |
|17label의 모델 정점 | 양손 모두17부위 비어 있지 않음 | 사람 피부의 실측/독립 해부학 경계는 아님 |
| 손가락 부위 중심점→예상 선분 | 오른손15/15, 왼손15/15 | 각 부위의 모든 정점/경계가 맞다는 증명은 아님 |
| 양손 vertex-index 삼각형 연결 | face 순서/방향을 제외한 연결 일치 | 모든 MANO 버전/자산에 대한 호환 보장은 아님 |
| 합집합 amodal 재투영 |32렌더·800프레임, 기존 저장 투영 일치 | 새 모델 자세/새 카메라 표본은 아님 |
| 기존 proxy 영역 보존 |800/800프레임에서 원래 픽셀 전부 포함 | 기존 영역을 줄이지 않는 추가 검사 |
| 기존 가림/codec core·재생 픽셀 |16가림 후보 +16 H.264, 각25프레임 모두 합집합까지 통과 | 기존 채널30·2픽셀 여유의 모델 영역 검사이며 송출 보안 인수는 아님 |
| 추가 hold / 풀 채택 |0 / 0 | 기존 모든 후보의 연구용 격리는 계속 유지 |

합집합은 기존 proxy보다 총263,864픽셀 검사 건을 추가했다. 이는800프레임·양손/시점/중복 정책을 합친 횟수이며 고유 피부 면적이나 독립 표본 수가 아니다. 일정 반경의 가능 여부는 기존과 같이16/32였고, 이미 생성된16쌍은 **반경·영상·임계값을 고치지 않고** 추가 영역도 가렸다. source array·기존 영상·기존 manifest/receipt는 바꾸지 않았다.

양손·두시점의 부위 도식4장을 직접 시각 확인했다. 논문 그림3의 손가락 순서/색과 모델 도식이 대응하고 손바닥/손목 색도 확인했다. 원문의 control point 병합 이름 불일치를 해소한 것은 아니며 해당 문장으로 새 segmentation을 생성하지 않았다. 이 검토 결과는 모델용 부위 대응의 부분 근거이고 독립 해부학 주석/임상/사람 검증은 아니다. 현 renderer의 기본 보호 정의도 이번 실행에서 변경하지 않았다.

[집계 JSON](../../reports/mano_author_region_union_20261115.json)과 [사례별 검사 시간32행](../../reports/mano_author_region_union_audit_timings_20261115.csv)에 실제 시작/끝·wall/자체CPU·각 단계 결과를 남겼다. 새 모델 추론/영상 인코딩은0회이므로 이를 새 영상 생성시간으로 세지 않았다. 기존 영상별 생성시간 CSV는 그대로다. 캐시/배경 부하 미통제인 단일 로컬 검사로 방법 간 성능 우열이나 Cloud 지연을 주장하지 않는다.

실행 기록은 `EXITED_ZERO`, journal `COMPLETED800/800`, 코드 `4519de9`·입력691개·고정 dependency26개·산출물124개이며 전후 snapshot/출력 검산을 통과했다. 실제 비공개 위치:

- `private_artifacts/cpf_region_review_20261115/`: 원문 PDF1–2쪽 렌더, source blob 두 파일, source manifest와 원문 불일치 기록.
- `private_artifacts/manotorch_region_source_20261115/`: 이전에 확보한 저자 assignment/loader/코드 License. 기존 파일은 수정하지 않았다.
- `private_artifacts/mano_author_region_audit_20261115/`: 양손 centroid/도식·정점/face 선택·합집합 마스크·프레임별 QC/journal.
- `private_artifacts/mano_author_region_audit_record_20261115/`와 `mano_author_region_audit_config_20261115.json`: 실행 명령·시각·코드/입력/환경 snapshot·종료/산출물 receipt.

공개 파일에는 원 모델 배열·centroid 좌표·vertex/face ID·실제 마스크·카메라 행렬·개별 원본 hash·도식을 넣지 않았다. handcaptcha prod UI는 변경하지 않았다.

연구 전체256개 검사와 실제 오프라인 환경의 region/camera15개 검사가 통과했다. 새 기하4개는 잘못 바뀐 부위 대응·좌우 반사·whole-face 합집합·연결 방향/순서·누락 label·퇴화 뼈/범위를 확인한다. 이 검사를 원논문 전체 재현/임상/사람 인수로 확대하지 않는다.

## 완료한 일, 필요한 입력, 다음 단계

완료는 원문/저자 palette와 숫자 부위의 프로젝트 대응표, 현재 양손 모델의 기하/연결 검토, 기존 보호 영역을 줄이지 않은 합집합과 실제 가림 영상의 전 프레임 검사다. 학술 색인에 출처와 읽은 범위를 추가했다.

다음 독립 개발은 이 버전의 추가 보호 검사를 이후 진단 생성의 관문에도 연결하고, 최종 영상의 공개 단서·복수 유효 답/지름길을 검사하는 일이다. 손바닥/손목 control point 설명의 불일치·모든 경계의 독립 해부학 의미·임상 한계·사람 이해/편안함·그림자/반사·공격/운영 검증은 여전히 미완료다. 숫자 부위의 대응을 확인한 것만으로 사람의 안전한 가동 범위를 승인하지 않는다.

등록 촬영21take·독립 주석·선별/모방/정지 응답·모델/운영 입력은 대기이며, 접수되면 원래1→2→3A→3B→4→5→6 순서부터 처리한다. UI64조합의 실제 효과 시험과 Cloud 보류도 유지한다.
