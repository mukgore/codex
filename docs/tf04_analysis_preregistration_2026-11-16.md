# TF-04 완료 영상의 점수·계보·정적 표시 선별 — 사전등록 v1

등록 시점에 native/display 두 실행은 `EXITED_ZERO`이며 출력74/361개 검산을 통과했다. source32개·800프레임, 가림/H.264각8개가 완료됐고 A8시점만 최종영상이 있다. B/C각8시점은 union반경구간이 비었고 U는 upstream모델위반이다. 이 이미 관측한 결과와 아래 후속 분석의 계획을 구분한다. 완료SDK/영상은 재실행하지 않는다.

## 고정 분석

1. **32시점과48영상 집계:** native/display receipt와 모든산출물을 검증한다. 조건별 model/legacy/union/가림/final 분모, 반경 하한–상한 차이, 실제영상별 ready/검산완료 UTC/wall/자체CPU·phase·bytes/FPS/길이를 남긴다. source32+가림8+H.2648을48개 독립문제로 세지 않는다.
2. **고정 prod 수치256건:**32source투영 각각에4좌표조건×2구간방식. 자기기준/자기응답, 자기기준/첫자세정지, 자기기준/XY진폭절반, 동일손·seed·시점의A기준/현재arm응답을 비교한다. 각25프레임·실제512×420정보를 source_info→video_info로 명시 연결하고 mirror=false. 기존 hash고정 JS원문/가중치/.25·38도 기준을 유지한다. full_interval/auto_keyframes를 분리하며 실제검출·UI/200ms hold/인증을 주장하지 않는다. B/C/U의 최종영상 부재와 raw모델투영 점수를 구분한다.
3. **실제 파일/픽셀/계보:**16native payload,32source FFV1·존재하는8후보/8H.264를 확인한다. native는vertex/joint/time payload, 영상은 전체파일바이트와 실제decode의25프레임/PTS/픽셀을 별도로 묶는다. hash그룹은 실제payload 또는 decode비교로 대조한다. 계보는 제공bundle의native16을 경계root로 두고source→후보→final을 연결한다. 모두 같은보수적개발family/노출/diagnostic이며 독립split은없다. 이전미사용평가자료가 생긴것처럼 쓰지 않는다.
4. **18개 자세의 고정화면 선별:**B로선택한4자세만으로 모든18자세가 실패했다고 일반화하지 않는다. 성공한TF-02P 감사의 모델/표면 후보18개를 양손 고정등록·같은camera·author_region_union에서2시점씩 검사한다. 기존실제SDK출력만 사용하고 새SDK/영상은0, 정적raster36개다. 기존legacy/표면반경·Stage7·2픽셀core·최소2개원밖tip patch/경계관문을 그대로 쓴다. 정적조건은 같은프레임25회로검사하며 실제사람선별이아니다. raster/mask/owner와 판정·실제시간을private에보존한다. 0개도결과다.

## 입력·실행·보존

원생산자 `PROCESS_ERROR`와 별도 정적원출력 감사 `EXITED_ZERO`는 모두 보존·명시검증한다. 모델/표면통과만으로새표시를허용하지않고 보호영역/기준을줄이지않는다. 원출력/모델·원문/코드/전체worktree/Node/고정prod/26pin환경과명령·입출력·UTC/시간/실패를새config/snapshot/receipt로기록한다. 분석예산300초·Node호출별30초,새immutable root만사용하고실행중편집/커밋하지않는다.

추가추론·인코딩·사람/카메라/독립family/풀채택0이다. 실제행동·안전/물리·연속충돌·사람이해/모방·운영/보안은미검증이다. 결과를공개할때개별hash/원좌표/모델/상세로그는private에남기고합성과정의집계/영상별생성시간만내보낸다. 실제앞단계입력이오면원래순서부터우선한다.
