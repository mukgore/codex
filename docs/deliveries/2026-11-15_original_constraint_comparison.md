# 가동 범위 원출처 확보와 인용표 대조

## 이번에 확인한 것

BIO-07 Cobos et al.2008, *Efficient Human Hand Kinematics for Manipulation Tasks*의 [저자기관 서지](https://oa.upm.es/4040/)와 [원PDF](https://oa.upm.es/4040/1/INVE_MEM_2008_58022.pdf)를 확보했다. 제목/저자/학회·2246–2251쪽을 대조하고6쪽을 렌더해 읽었다. 이전의 웹 timeout/로컬 TLS 오류 기록은 당시 결과로 남긴다. 이번 Windows curl 권한 재시도는 기본 인증서 검증을 유지한 채 성공했다. 시스템 TLS 설정·인증서 검증을 바꾸지 않았다.

§II/Table I–II는 일반 D-H 모델·손가락별 wrist offset·CMC와 MCP abduction/flexion의 순서를 설명한다. §III/Table III는 active/passive 가동 범위를 정리하고 더 앞선 문헌[11],[12]를 인용한다. Cyberglove 모델 실험을 우리 과제의 참가자/생체 검증으로 보지 않는다.

## 두 논문의 같은 칸이 다른 사례

BIO-07 표III(원문2249쪽)와 이를 인용한 BIO-06 Chen Chen2013 표6에서 엄지3관절·검지3관절의6행×3열을 비교했다. [선택 사실JSON](../../references/cobos2008_constraint_extraction.json), [비교 결과](../../reports/literature_constraint_comparison_20261115.json).

| 항목 | Cobos2008 | Chen Chen2013 |
|---|---|---|
| 엄지MCP 벌림/모음 | 0도 | 5도 |
| 엄지IP 벌림/모음 | 0도 | 5도 |

선택18칸 중16칸은 같고2칸은 달랐다. 어떤 쪽의 오류인지 확정하거나 더 넓은/좁은 값을 자동 채택하지 않는다. 독립적인 두 측정의 합의로 세지도 않는다. [2013년 논문과 이전 대조](2026-11-15_biomechanical_numeric_sources.md).

## 좌표계와 다음 출처

2008년 일반 D-H와2013년 수정 D-H를 같은 표기라고 가정하지 않는다. BMC의 기하 local frame·MANO axis-angle/PCA·임상 중립/부호/축도 별도 대응이 필요하다. 값에 degree→radian 변환만 적용해 실행 한계를 만들지 않았다.

Cobos가 표III의 근거로 적은 책[11] Kapandji의 *The Physiology of the Joints*, vol.I(논문 기재1970년2판)와[12] Pérez Casas/Bengoechea의 스페인어 기능해부학 책(논문 기재1978년)을 기록했다. **두 책 원문은 아직 읽지 않았다.** 서지는 논문에서 전사한 것으로 원도서판/대상·측정법·active/passive·허용 범위/개인차를 더 확인해야 한다. 참고 논문을 추적했다고 모든 사람의 일반 생체 한계를 확보한 것은 아니다.

## 검증과 기록

코드 `bc3146a`의 `analysis/literature_constraint_comparison.py`가 양쪽 수치를 보존하고 같은 칸/다른 칸을 센다. 단위·순서/중복·미적용 상태 검사2개를 추가했고 연구 전체202개가 통과했다. 실제 명령·코드/11입력·기존26pin 환경·종료·출력은 `private_artifacts/literature_constraint_record_20261115/`에 기록했다. `EXITED_ZERO`, 전후 snapshot 일치·출력1개 재검사 통과다. 원PDF와 렌더는 기존 `literature_review_20261115/`에 비공개 보관하고 Git에 복제하지 않는다. 비교 실행과 별도로 먼저 수행한 다운로드·렌더를 wrapper 실행에 소급하지 않는다.

이번 단위는 문헌/계산 대조다. 사람/손동작 생성 실험·프로필 변경·원래 격리 해제·임상 축 검증은 없다. 다음은 원도서/측정 조건과 D-H/수정D-H/BMC의 실제 좌표 대응이다. 실제 촬영·선별·정상/정지 대응 입력이 오면 [연구 순서](../research_goal_followups_2026-11-10.md)를 먼저 따른다.
