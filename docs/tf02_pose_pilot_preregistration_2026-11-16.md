# TF-02 원형 없는 자세 제안 파일럿 사전등록 v1

**실행 후 갱신:** [TF-02 실제 결과/실패와 성공 ID 구분](deliveries/2026-11-16_template_free_pose_pilot.md), [별도 TF-02P 수정원출력 감사](deliveries/2026-11-16_projected_pose_audit.md), [TF-03 경로 결과](deliveries/2026-11-16_template_free_paths.md)에 연결한다. 아래는 실행 전에 고정했던 명세이며 당시 ‘대기’ 상태를 보존한다.

상태: **등록 완료, 코드/실행 대기**. [TF-01 적용표](tf01_constraint_application_2026-11-16.md)에 따라 모델용 prior만 적용한다. 실제 촬영/사람 입력이 오면 원래1→2→3A가 우선이다. 성공할 후보 수를 미리 정하지 않는다.

질문은 고정 굽힘-복귀 파형/원형ID 없이 제안한 PCA연동 자세가 현재 모델 prior·샘플표면 지표를 얼마나 만족하는지다. 움직임·사람 타당성·완성 공급기를 시험하는 실험이 아니다. 기존2PC 고정시간 envelope를 이름만 바꿔 재사용하지 않는다.

## 조건과 고정 예산

양손×seed7/19×8시도 = 각 arm32자세를 계획한다. NumPy PCG64/SeedSequence를 버전과 함께 고정하고 proposal stream을 hand/seed/attempt로 분리한다. B/U는 같은32제안을 짝지어 사용한다. geometry는 beta=0, root axis-angle=0, flat_hand_mean=true로 고정하고 appearance는 생성하지 않는다.

**실행 전 구현 명세 확정:** SeedSequence entropy는 `[seed, hand_index, attempt, 62026]`, hand_index는 right=0/left=1이다. 제안6계수는 float64 원추출과 float32 SDK입력을 모두 보존한다. 모델의6×45 float32 PCA기저로 전개하고, 실제 SDK의 PCA 경로와 full-pose 경로를1e-6으로 비교한다. A는 기존 recipe/선택프레임을 재사용하되 위의 beta=0을 공통 적용하는 새 정적 계산이다. 기존 beta 변형 영상/좌표를 그대로 재현했다는 주장은 하지 않는다. 모든 표현 검산은64개 본시도 전에 수행하며 계수/기저/최대오차를 비공개 보존한다. 코드: `analysis/runtime_benchmark/template_free_pose.py`, `mano_template_free_pose_pilot.py`.

| arm | 제안 | 검사·목적 |
|---|---|---|
| A | 기존 `middle_only_cues_open`/`preflex20`의 author_exact recipe에서25샘플 중 인덱스0,3,6,9,12,15,18,24의 자세. 기존seed7/19·양손 유지 | 기존 원형의 정적 비교 기준. full25파형/기존 산출물은 그대로 보존 |
| B | 모델의 첫6 PCA기저에 계수6개를 각각N(0,0.5²)에서 뽑아45비root축각으로 전개. 중심은 flat_hand_mean의0. 단일 자세만 제안하며 원형ID·시작/목표·파형 없음 | 실제 SDK출력에서 해부학축 재추출→고정 author_exact 모델 prior→기존 표면검사. 수정/최적화 없이 거부. 연동은 모델PCA기저의 상관이며 임상연동 주장이 아님 |
| U | B와 같은32 PCA제안·같은 SDK출력 | 무관문 제안 대조. 모든 위반/표면지표를 측정하고 결과를 보존하되 후보 통과로 승격하지 않음 |

N(0,0.5²),6PC,8시도와 A의 선택프레임은 **공학 제안값**이며 학습된 계수분포·사람 허용영역의 추정치가 아니다. PCA제안은 독립 관절별 균등 샘플링과 구분한다. B의 선별된 후보가 임상 허용자세라는 뜻도 아니다.

새 SDK 계산은 A32+B32+양손neutral2+표현대조4 =70 forward를 계획한다. 표현대조는 각손에서 seed7/attempt0의 동일 계수를 use_pca=true/false로 각각 한 번 계산한다. U는 B출력을 공유해 같은32제안을 평가한다. 공통/공유 계산을 명시하고 세 arm의 독립96추론이나 공정한 운영성능으로 부르지 않는다. 제안 수 예산은 각32로 같고 전체600초 상한, Torch1thread/기존CPU17pin을 사용한다. 예산을 넘기면 중단/부분실패를 보존하고 후보를 보충하지 않는다.

## 실행 전 필수 확인

1. 기존 모델 intake/연구 사용범위·라이선스 및 고정 저자원문 checksum을 검증한다. 새 설치/다운로드/Cloud전송은 하지 않는다.
2. 위4회 표현대조로 PCA기저와 계수 전개를 SDK `use_pca=true`와 `use_pca=false`의 실제 full_pose·관절/mesh와 확인한다. 기저 전개 차원이45/6이 아니거나 full_pose/관절/mesh의 최대절대차가1e-6을 넘으면 본시도를 시작하지 않는다. 이1e-6은 구현일치용 공학허용치이며 임상한계가 아니다. 추가대조가 필요하면 시작 전 새버전으로 계산분모를 다시 등록한다.
3. 양손neutral과 기존 모델 prior/축·surface 함수의 실제 입력계약,6개 미확정 한계·점종류/단위를 확인한다. author_exact와 반사 comparator를 합치지 않는다.
4. 새 코드/검사를 완료한 뒤 새 config의 전체worktree/코드·모델·원문·기저/환경·명령·예산과 사전등록 파일을 snapshot한다. 새 immutable root만 사용한다. 기록 실행 중 편집/커밋은 하지 않는다.

## 거부·기록·다음 단계

매 시도에 계수·전개된 입력/실제 full_pose·shape/root·16관절/표면tip/778정점·해부학축/각도·원모델/strict/zero-mask벌점·표면교차/퇴화·거부이유·wall/자체CPU/캐시를 비공개 보존한다. 임상/BMC한계·SI단위 미확정과 시간/연속충돌/물체/사람/최종영상 미검증을 별도 상태로 남긴다. 숫자/단위·왕복·기저가 불일치하면 오류이며0벌점으로 대체하지 않는다.

B의 모델/샘플표면 지표0인 후보 수와 A/U의 같은지표를 분모32와 함께 보고한다. 후보0개도 결과다. 통과 목표를 채우기 위한 scale변경·관문완화·사후재시도·학습·최적화는 하지 않는다. 조건을 바꾸면 새 prereg/version/run을 만든다.

전체 결과는 `MODEL_CONSTRAINED_RESEARCH_ONLY`, `release_allowed=false`, 풀/브라우저 채택0이다. TF-03은 이 결과와 표현검증을 본 뒤 별도 시간/경로/충돌 명세를 고정한다. TF-04의 author_region_union/카메라/최종영상·계보 관문과 TF-05 실제사람/독립평가는 계속 필요하다. TF-02 등록 자체를 새자세 생성 실험 완료로 세지 않는다.
