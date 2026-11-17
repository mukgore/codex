"""Build an offline overview from public aggregates and selected Git histories.

Never reads private_artifacts, images, video, models or participant-level data.
GitHub main/ref metadata is an explicitly saved, sanitized connector snapshot.
"""
import json
from pathlib import Path
import re
import subprocess
from datetime import datetime,timezone,timedelta

REPO=Path(__file__).resolve().parents[1]
OUT=REPO/'dashboard/research-overview-20261117/dist'
CUTOFF='9f1a68e'
HANDCAPTCHA_CUTOFF='9f29ac44adb42509ca7a6c475b82031c9d30f198'
KST=timezone(timedelta(hours=9))


def read(name):return json.loads((REPO/name).read_text(encoding='utf-8'))
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args]).decode('utf-8').strip()
def plain(s):
    s=re.sub(r'\[([^\]]+)\]\([^)]*\)',r'\1',s)
    s=re.sub(r'\[([^\]]+)\]\[[^\]]*\]',r'\1',s)
    return s.replace('`','').replace('**','').strip()
def section_rows(name,heading):
    text=(REPO/name).read_text(encoding='utf-8').split(heading,1)[1].split('\n## ',1)[0]
    return [[plain(x) for x in line.split('|')[1:-1]] for line in text.splitlines() if line.startswith('|')][2:]


STAGES=[
 dict(id='1',title='촬영·자극 제작',question='비교할 수 있는 원본이 준비됐나?',status='새 원본 접수 대기',
      done=['기존 원본과 가림 수준을 대응시키는 제작·검사 경로','촬영21행·권리/계보·원본 시각 접수 양식'],
      pending=['등록21행의 새 source_path는0개','새 통제 촬영과 수행자·동작 family 계보'],source='docs/deliveries/2026-11-10_rights_capture_screening_protocol.md'),
 dict(id='2',title='의미·모호성 선별',question='사람이 같은 동작으로 이해하는가?',status='사람 응답·주석 대기',
      done=['노출 전후 자유 응답·확신도·판단 불가 기준안','모델 궤적이 달라도 같은 화면이 되는 대조'],
      pending=['새 응답 관측값0개·독립 주석 좌표0개','실제 사람의 해석/수행 자료와 사전 판정 기준'],source='docs/research_goal_followups_2026-11-10.md'),
 dict(id='3A',title='모방·정지 비교',question='정상 모방과 정지·오답을 구별하는가?',status='실제 대응 자료 대기',
      done=['기존 좌표/저장 답·정지·부분 동작의 수치 대조','점수와 offline gate를 별도 평가'],
      pending=['같은 참가자·문제·카메라의 정상/정지/오답','추적 실패·완료·지연의 실제 사건 기록'],source='docs/deliveries/2026-11-09_work_offline_controls.md'),
 dict(id='3B',title='채점·보정',question='고정 기준이 독립 자료에서도 유효한가?',status='후보 구현 · 독립 평가 대기',
      done=['DTW 후보·실제 초 미분·결측/gap/분할 검사','군집 단위 위험 상한과 계보/누출 사전 검사'],
      pending=['미사용 참가자/source의 보정·평가 split','정상 수용·오답 거부의 실제 대응 점수'],source='docs/deliveries/2026-11-17_simultaneous_risk.md'),
 dict(id='4',title='사람·모델 비교',question='같은 영상·정보·시간으로 비교했나?',status='일부 모델 진단 · 사람 대기',
      done=['합성48영상의 실제 MediaPipe1,200프레임 추론','계측/queue/HTTP/원로그 재구성 기반'],
      pending=['독립 사람 주석과 같은 정보 조건','HaMeR/Text2HOI 핵심 자산·허용 runtime'],source='docs/deliveries/2026-11-17_mediapipe_matched_video.md'),
 dict(id='5',title='인증·운영',question='보호할 동작까지 안전하게 이어지는가?',status='localhost 검증 · 운영 대기',
      done=['서버 재채점·세션/만료·일회 사용·입력/자원 상한','새 localhost의 점수/gate/grant/action 분리'],
      pending=['실제 capture trust·gateway·운영 인수','미사용 문제와 강한 같은 정보 공격'],source='docs/deliveries/2026-11-17_local_http_timing.md'),
 dict(id='6',title='사용성·공급 확대',question='사람이 쓰기 쉽고 공급 가능한가?',status='UI·3D 개발 · 인수 대기',
      done=['prod 기반 선택/중첩/준비 시간 UI6요인64조합','MANO 생성·표면/가림·같은 표시 대조'],
      pending=['편안함·동작 이해·다기기/접근성·비용','생체/물리/연속 충돌과 실제 pool/배포 승인'],source='docs/remaining_work_master_2026-11-15.md'),
]


def milestone(date,title,summary,meaning,limit,track,path,kind='개발 진단'):
    return dict(date=date,title=title,summary=summary,meaning=meaning,limit=limit,track=track,source=path,kind=kind)


MILESTONES=[
 milestone('2026-02-22','작품의 출발: HTML 동작 시험','handcaptcha의 초기 HTML과 동작 시험 파일 갱신이 GitHub에 남아 있다.','원래 작품 구현의 이력을 볼 수 있다.','커밋 날짜가 참가자 실험 수집 날짜는 아니다.','기존 개발','https://github.com/mukgore/handcaptcha/commits/main/','기존 GitHub'),
 milestone('2026-07-14','영상·좌표 pipeline 구성','검출→품질/정면성→길이→가림→관문의 단계 코드와 검사가 추가됐다.','반복 가능한 자료 제작의 기반이다.','완성된 코드 자체가 가림 효과나 보안을 입증하지 않는다.','기존 개발','https://github.com/mukgore/handcaptcha/tree/main/dataset_pipeline','기존 GitHub'),
 milestone('2026-09-13','prod 시연 흐름 정비','완료 후 시작 화면 복귀와 전시 중 로컬 JSON 다운로드 동작을 정비했다.','시제품 시연·운영 편의의 개선이다.','실제 사용자 효과/인증 성능과는 별도다.','기존 개발','https://github.com/mukgore/handcaptcha/commits/main/','기존 GitHub'),
 milestone('2026-10-02','기존 결과를 다시 읽다','사람18세션·HaMeR28조합·설문·공격 저장값을 재검토했다.','점수 통과와 gate/전체 인증의 차이가 드러났다.','과거 timer/build·일부 A/B 계보와 독립성은 한계로 남았다.','자료 검토','docs/phase1_review.md','저장 자료 분석'),
 milestone('2026-10-28','G3의 수용 범위를 정리','자료 분모·경계와 FR1–FR5 해석을 연결하고 연구자 범위에서 종료했다.','이미 수용한 연구를 계속 복구 대상으로 되돌리지 않는다.','과거 세션별 build·독립 검증을 새로 입증한 것은 아니다.','자료 검토','docs/reproducibility/g3_dr3_fr5_researcher_update_2026-10-28.md','기존 범위 수용'),
 milestone('2026-10-28','G4: 실제 코드와 새 서버 연결','알려진8source의 조회/저장 답 재생과 새 localhost 보호 동작을 비교했다.','점수·offline gate·서버 동작을 단계별로 볼 수 있다.','신뢰 카메라·미사용 source·과거 운영 인증의 시험은 아니다.','인증·채점','docs/g4_actual/g4_final_report.md','실제 로컬 실행'),
 milestone('2026-11-04','실행 순서와 전체 백로그 고정','62ID와 촬영→선별→모방/정지→보정→모델→운영→확장의 순서를 연결했다.','할 일과 필요한 입력을 함께 추적한다.','문서/양식 준비는 실제 수집 완료가 아니다.','연구 설계','docs/backlog_execution_audit_2026-11-10.md','설계·준비'),
 milestone('2026-11-10','앞 단계 수집·분석 도구 준비','촬영21행·선별/주석 양식, sampling/잡음·시간 미분, 계보·세션 기록을 검산했다.','원자료가 들어오면 비교 가능한 형태로 접수할 수 있다.','새 통제 원본/사람 관측은 아직0이다.','연구 설계','docs/deliveries/2026-11-10_all_stage_execution.md','준비·일부 진단'),
 milestone('2026-11-13','자원 상한과 UI 대조 기반','서버/평가기 시간 상한과 prod 기반 UI6요인64조건을 준비했다.','오류/대기를 구분하고 UI효과를 비교할 틀을 만들었다.','실제 참가자에게 어떤 조합이 좋은지는 미검증이다.','인증·채점','docs/deliveries/2026-11-13_ui_factorial.md','개발 검증'),
 milestone('2026-11-14','실제 MANO와 기록 실행','허용된 모델을 CPU에서 계산하고 원래 관절/손끝·생산 입력·출력 기록을 연결했다.','추상 fixture를 넘어 실제 모델 데이터의 조건부 진단이 가능해졌다.','임상 축·생체 한계·물리·사람 편안함은 별도다.','3D·표시','docs/deliveries/2026-11-14_mano_controlled_producer.md','실제 SDK 실행'),
 milestone('2026-11-15','같은 화면, 다른 궤적 대조','8부모의 변경48시점 중46개 최종 H.264가 부모와 정확히 같았다.','이 생성 조건에서 정밀 모델 궤적의 비유일성을 보였다.','실제 사람에게 유효한 복수 정답/공격 성공을 확정하지 않는다.','3D·표시','docs/deliveries/2026-11-15_relative_middle_display_counterfactual.md','실제 SDK·영상'),
 milestone('2026-11-16','원형 없는 자세와 경로를 시도','TF-02/투영/TF-03을 분리 실행하고 원본 실패와 후속 감사를 보존했다.','제약 생성의 시도/거부와 경로 샘플 결과를 얻었다.','prior/샘플 표면 통과를 사람/연속 충돌 통과로 승격하지 않는다.','3D·표시','docs/deliveries/2026-11-16_template_free_paths.md','실제 SDK 실행'),
 milestone('2026-11-16','최종 표시·채점까지 대조','TF-04 source32/후보8/최종8영상과256수치·36정적 표시를 비교했다.','모델 통과·가림 제작·숫자 점수를 구분했다.','B/C는 union 반경 불가, 실제 검출/hold/사람 인증은 별도다.','3D·표시','docs/deliveries/2026-11-16_matched_display.md','실제 렌더·채점'),
 milestone('2026-11-17','같은48영상의 실제 MediaPipe 진단','1,200입력/769검출. source와 가림 후보/최종의 결과를 나눴다.','검출 실패를0오차로 처리하지 않고 분모를 보존했다.','합성 source의 개발 진단이며 사람/브라우저 parity/인증 비교는 아니다.','모델·실행시간','docs/deliveries/2026-11-17_mediapipe_matched_video.md','실제 모델 추론'),
 milestone('2026-11-17','샘플 표면과 연속 시간의 경계','공유 simplex와 새96중간시점·조건부 SDK경계를 검사했다.','샘플 검사와 연속 무충돌의 차이를 수치로 드러냈다.','v2의4leaf 미확정·backend 오차 가정 미검증, CCD승인false다.','3D·표시','docs/deliveries/2026-11-17_conditional_sdk_envelopes.md','조건부 계산'),
 milestone('2026-11-17','R4/R7: 계측과 도착 대기열','합성 stage5경로·process7경로의 정상/오류/timeout/drop을 기록했다.','새 측정에서 완료·미완료와 실제 도착을 구분할 기반이다.','합성 인터페이스의 시간은 모델 속도가 아니다.','모델·실행시간','docs/deliveries/2026-11-17_process_replay_fixture.md','합성 경로 검산'),
 milestone('2026-11-17','R8: 실제 localhost 시간','reference는1회 허용/재사용 거부, 정지는 점수 통과·gate거부, schema400.','점수→관문→grant→시험 동작의 차이를 직접 관측했다.','한 known-source의 offline replay이며 실제 화면/카메라/운영 인증은 아니다.','모델·실행시간','docs/deliveries/2026-11-17_local_http_timing.md','실제 HTTP·JS'),
 milestone('2026-11-17','R9: 새 process에서 원로그 재구성','원출력812개·공개JSON4/CSV59행이 일치했다.','보고서를 저장 예측/원로그로 다시 연결했다.','독립 구현/새 실측 세션/제3자 검증은 아니다.','모델·실행시간','docs/deliveries/2026-11-17_runtime_reconstruction.md','읽기 전용 검산'),
 milestone('2026-11-17','현재: browser 기록 준비와 전체 정리','선택적 시간 기록 UI와 callback 상태 처리를 준비했고 전체384검사(skip1)를 통과했다.','현재까지의 활동을 한 화면에서 이해할 대시보드로 정리한다.','실제 브라우저 표시/새 사람·독립 운영 검증은 아직 남는다.','모델·실행시간','docs/browser_timing_page_2026-11-17.md','준비·코드 검증'),
]


def category(subject):
    s=subject.lower()
    for name,pattern in [('3D·표시',r'mano|3d|mesh|bmc|biomech|surface|simplex|template.free|rodrigues|kinematic|grasp'),
                         ('모델·실행시간',r'runtime|timing|record|reconstruct|journal|snapshot|supervisor|mediapipe|queue|deadline|process'),
                         ('인증·채점',r'scor|gate|session|auth|dtw|attack|risk|captcha|paired|calibrat'),
                         ('UI·제작',r'html|palm|ui|overlay|video|mask|occlu|pipeline|frontality|render|hand selection')]:
        if re.search(pattern,s):return name
    return '자료 검토·계획'


def build():
    snapshot=read('reports/dashboard_github_snapshot_20261117.json');commits={};repo_stats=[]
    for name,path,head in [('codex',REPO,CUTOFF),('handcaptcha',REPO.parent/'handcaptcha-ui-20261113',HANDCAPTCHA_CUTOFF)]:
        ref=next(r for r in snapshot['repositories'] if r['full_name'].endswith('/'+name));remote=ref['remote_sha']
        published=set(git(path,'rev-list',remote).splitlines());local_head=set(git(path,'rev-list',head).splitlines())
        for line in git(path,'log',head,'--format=%H%x1f%cI%x1f%s').splitlines():
            sha,stamp,subject=line.split('\x1f',2)
            commits[name+sha]=dict(sha=sha,subject=subject,timestamp=stamp,repo=name,published=sha in published,
                                   lane='작업 브랜치' if sha in published else '로컬 연구',url=f'https://github.com/mukgore/{name}/commit/{sha}' if sha in published else None)
        for row in snapshot['main_commits']:
            if row['repo']!=name:continue
            key=name+row['sha']
            if key in commits:commits[key]['lane']='main · 작업 브랜치'
            else:commits[key]=dict(sha=row['sha'],subject=row['subject'],timestamp=row['timestamp'],repo=name,published=True,lane='main',url=row['url'])
        rows=[c for c in commits.values() if c['repo']==name]
        repo_stats.append(dict(name=name,remote_sha=remote,remote_url=ref['branch_url'],local_head=git(path,'rev-parse',head),
                               selected_local_history_n=len(local_head),local_only_n=sum(not c['published'] for c in rows),
                               unique_commits_n=len(rows),shallow=git(path,'rev-parse','--is-shallow-repository')=='true'))
    records=list(commits.values())
    for c in records:
        dt=datetime.fromisoformat(c['timestamp'].replace('Z','+00:00')).astimezone(KST)
        c.update(timestamp=dt.isoformat(),date=dt.date().isoformat(),month=dt.strftime('%Y-%m'),category=category(c['subject']),short=c['sha'][:7])
    records.sort(key=lambda c:(c['timestamp'],c['repo']),reverse=True)
    daily={}
    for c in records:
        row=daily.setdefault(c['date'],dict(date=c['date'],codex=0,handcaptcha=0,local=0))
        row[c['repo']]+=1;row['local']+=not c['published']
    backlog=section_rows('docs/remaining_work_master_2026-11-15.md','## 전체 62개 백로그별 남은 일')
    audit=(REPO/'docs/backlog_execution_audit_2026-11-10.md').read_text(encoding='utf-8')
    evidence={cells[0]:cells[2] for line in audit.splitlines() if line.startswith('|') for cells in [[plain(x) for x in line.split('|')[1:-1]]] if len(cells)==4 and re.fullmatch(r'(?:NOW-\d+|[A-Z]\d+|V00)',cells[0])}
    items=[]
    for id,stage,remaining in backlog:
        state='기존 범위 수용' if id in ('R02','R03','R04','R07') else '상시 관리' if id in ('NOW-01','W01') else '추가 검증·입력 필요'
        items.append(dict(id=id,stage=stage,remaining=remaining,evidence=evidence.get(id,''),state=state))
    assert len(items)==62 and len({r['id'] for r in items})==62
    docs=[]
    for p in sorted((REPO/'docs/deliveries').glob('*.md')):
        text=p.read_text(encoding='utf-8');title=next((s.lstrip('# ').strip() for s in text.splitlines() if s.startswith('# ')),p.stem)
        docs.append(dict(title=title,path=p.relative_to(REPO).as_posix(),date=p.name[:10]))
    mp=read('reports/mediapipe_matched_20261117.json');http=read('reports/r8_local_timing_20261117.json')
    data=dict(title='손동작 CAPTCHA 연구 지도',as_of='2026-11-17',research_cutoff=git(REPO,'rev-parse',CUTOFF),github_verified_at=snapshot['verified_at'],
              coverage=snapshot['coverage'],commits=records,daily=sorted(daily.values(),key=lambda x:x['date']),repositories=repo_stats,
              stages=STAGES,milestones=MILESTONES,backlog=items,documents=docs,
              metrics=dict(stored_human_sessions=18,registered_new_capture_jobs=21,registered_source_paths=0,tests_run=384,tests_skipped=1,
                           backlog_ids=62,geometry_detail_rows=44,runtime_items=10,reconstructed_artifacts=812),
              detector_groups=[{k:r[k] for k in ('arm','kind','videos_n','attempted_frames_n','detected_frames_n')} for r in mp['aggregates']],
              local_http=[{k:r[k] for k in ('case','score_captcha','score_pass','offline_gate_pass','server_grant_issued','new_local_test_action_allowed','repeat_action_allowed','issue_trace_start_to_first_action_body_ms')} for r in http['cases']],
              current_inputs=read('reports/priority_input_gates_20261117.json'))
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT.parent/'data.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    template=(OUT.parent/'template.html').read_text(encoding='utf-8')
    encoded=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    (OUT/'index.html').write_text(template.replace('__DASHBOARD_DATA__',encoded),encoding='utf-8')
    print(json.dumps(dict(commits=len(records),local_only=sum(not c['published'] for c in records),documents=len(docs),backlog=len(items)),ensure_ascii=False))


if __name__=='__main__':build()
