#!/usr/bin/env python3
"""Independent, conditional replay for the existing A/B and prod_v2_pool records."""
import argparse,csv,hashlib,json,math,os,platform,sys
from datetime import datetime,timezone
from pathlib import Path

AT=[(0,5,6),(5,6,7),(6,7,8),(0,9,10),(9,10,11),(10,11,12),(0,13,14),(13,14,15),(14,15,16),(0,17,18),(17,18,19),(18,19,20),(0,1,2),(1,2,3),(2,3,4)]
LN=['WRIST','THUMB_CMC','THUMB_MCP','THUMB_IP','THUMB_TIP','INDEX_MCP','INDEX_PIP','INDEX_DIP','INDEX_TIP','MIDDLE_MCP','MIDDLE_PIP','MIDDLE_DIP','MIDDLE_TIP','RING_MCP','RING_PIP','RING_DIP','RING_TIP','PINKY_MCP','PINKY_PIP','PINKY_DIP','PINKY_TIP']
MX={'angle':46.9413,'dtw_angle':44.0014,'accel':0.1926}
WEIGHTS={'angle':0.25,'dtw_angle':0.38,'accel':0.37}; THRESHOLD=0.25; TOL=1e-10
ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'data'/'raw'
AB_DIR=Path(os.environ.get('CAPTCHA_AB_DIR',RAW/'ab'))
AB_BASE=Path(os.environ.get('CAPTCHA_AB_BASE',RAW/'references'/'landmarks_base.json'))
POOL_MANIFEST=Path(os.environ.get('CAPTCHA_POOL_MANIFEST',RAW/'references'/'pool_manifest.json'))
POOL_DIR=Path(os.environ.get('CAPTCHA_POOL_DIR',RAW/'references'/'pool_landmarks'))
AB_HTML=Path(os.environ.get('CAPTCHA_AB_HTML',RAW/'references'/'hand_captcha_ab.html'))
AB_HTML_BASE=Path(os.environ.get('CAPTCHA_AB_HTML_BASE',RAW/'references'/'hand_captcha_ab_base.html'))
PROD_HTML=Path(os.environ.get('CAPTCHA_PROD_HTML',RAW/'references'/'hand_captcha_prod.html'))
PROD_DIR=Path(os.environ.get('CAPTCHA_PROD_DIR',RAW/'prod_v2_pool'))

def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def load(p):
 with p.open(encoding='utf-8-sig') as f:return json.load(f)
def norm_px(data,mirror=False):
 info=data.get('video_info') or {}; w=float(info.get('width') or 720); h=float(info.get('height') or 720); out=[]
 for f in data.get('frames',[]):
  lm=f.get('landmarks_px')
  if not f.get('detected') or not lm: continue
  out.append([[(1-float(lm[n]['x'])/w if mirror else float(lm[n]['x'])/w),float(lm[n]['y'])/h] for n in LN])
 return out
def find_kfs(x):
 if not x or len(x)<10:return [0,len(x)//2,len(x)-1] if x else []
 v=[sum(math.hypot(x[i][j][0]-x[i-1][j][0],x[i][j][1]-x[i-1][j][1]) for j in range(21))/21 for i in range(1,len(x))]
 sm=[sum(v[max(0,i-5):min(len(v),i+6)])/len(v[max(0,i-5):min(len(v),i+6)]) for i in range(len(v))]
 m=[0]
 for i in range(5,len(sm)-5):
  if sm[i]<sm[i-1] and sm[i]<sm[i+1] and sm[i]<.005 and i-m[-1]>15:m.append(i)
 m.append(len(x)-1)
 if len(m)<=4:return m
 step=len(m)//3;return [m[0],m[step],m[step*2],m[-1]]
def to_xy(x,label):
 if x is None:return None
 if not isinstance(x,list) or len(x)!=21:raise ValueError(f'{label}: expected 21 points')
 y=[]
 for p in x:
  if not isinstance(p,list) or len(p)<2:raise ValueError(f'{label}: invalid point')
  a,b=float(p[0]),float(p[1])
  if not math.isfinite(a) or not math.isfinite(b):raise ValueError(f'{label}: nonfinite')
  y.append([a,b])
 return y
def pp(data):
 if len(data)<3:return None
 z=[]
 for fr in data:
  w=fr[0]; q=[[p[0]-w[0],p[1]-w[1]] for p in fr]; scale=max(math.hypot(*q[9]),1e-6)
  z.append([[p[0]/scale,p[1]/scale] for p in q])
 return z
def rs(x,n):
 if len(x)<3:return None
 if len(x)==n:return x
 if n<2:return None
 y=[]
 for t in range(n):
  s=t/(n-1)*(len(x)-1);lo=math.floor(s);hi=min(lo+1,len(x)-1);f=s-lo
  y.append([[p[0]*(1-f)+x[hi][j][0]*f,p[1]*(1-f)+x[hi][j][1]*f] for j,p in enumerate(x[lo])])
 return y
def ang(a,j,b):
 v=(a[0]-j[0],a[1]-j[1]);w=(b[0]-j[0],b[1]-j[1]);den=(math.hypot(*v)+1e-8)*(math.hypot(*w)+1e-8)
 return math.degrees(math.acos(max(-1,min(1,(v[0]*w[0]+v[1]*w[1])/den))))
def angerr(u,b):
 return sum(sum(abs(ang(b[i][p],b[i][j],b[i][q])-ang(u[i][p],u[i][j],u[i][q])) for i in range(len(b)))/len(b) for p,j,q in AT)/len(AT)
def accel(x):
 r=[]
 for i in range(1,len(x)-1):r.append(sum(math.hypot(x[i+1][j][0]-2*x[i][j][0]+x[i-1][j][0],x[i+1][j][1]-2*x[i][j][1]+x[i-1][j][1]) for j in range(1,21))/20)
 return r
def metrics(u,b):
 t=rs(u,len(b)); a=angerr(t,b) if t else None
 d=None
 if len(u)>=3 and len(b)>=3:
  tt=rs(u,round(len(b)*1.2));d=min(angerr(tt[s:s+len(b)],b) for s in range(len(tt)-len(b)+1))
 ac=None
 if len(b)>=5 and t:
  q,r=accel(t),accel(b);ac=sum(abs(a-b) for a,b in zip(q,r))/len(q)
 return {'angle':a,'dtw_angle':d,'accel':ac}
def calc(segments,kfs,bases):
 users=[];refs=[];excluded=0
 for n,s in enumerate(segments):
  det=[to_xy(f.get('lm'),f'segment{n}.lm') for f in s.get('frames',[]) if f.get('lm') is not None]
  if len(det)<3:excluded+=1;continue
  a,b=kfs[int(s['fromKf'])],kfs[int(s['toKf'])];u,v=a['id'],b['id']
  x,y=bases[u],bases[v]
  ref=x[int(a['frameIdx']):int(b['frameIdx'])+1] if u==v else x[int(a['frameIdx']):]+y[:int(b['frameIdx'])+1]
  users.extend(det);refs.extend(ref)
 tf=sum(len(s.get('frames',[])) for s in segments); dc=len(users); dr=dc/tf if tf else 0
 up,bp=pp(users),pp(refs); raw=metrics(up,bp) if up and bp else {'angle':None,'dtw_angle':None,'accel':None}
 est={k:(0.0 if raw[k] is None else max(0,min(1,dr*max(0,1-raw[k]/MX[k])))) for k in MX}
 return {'raw':raw,'estimated':est,'captcha':sum(est[k]*WEIGHTS[k] for k in MX),'tF':tf,'dC':dc,'dR':dr,'segments':len(segments),'segments_used':len(segments)-excluded,'segments_excluded_lt3':excluded}
def err(a,b):
 if a is None and b is None:return 0.0
 if a is None or b is None:return None
 return abs(float(a)-float(b))
def result_row(cohort,rid,cond,p,sha,c,raw0,est0,score0,tf0,dc0,dr0,nseg0,threshold0,passed0,kfmatch,duration):
 e={k:err(raw0.get(k),c['raw'][k]) for k in MX}; ee={k:err(est0.get(k),c['estimated'][k]) for k in MX}
 tfbad=tf0 is not None and int(tf0)!=c['tF']; dcbad=dc0 is not None and int(dc0)!=c['dC']
 row={'cohort':cohort,'record_id':rid,'condition':cond,'input_sha256':sha,'keyframe_match':kfmatch,'segments_saved':nseg0,'segments_used':c['segments_used'],'segments_excluded_lt3':c['segments_excluded_lt3'],'tF_saved':tf0,'tF_recalc':c['tF'],'dC_saved':dc0,'dC_recalc':c['dC'],'dR_saved':dr0,'dR_recalc':c['dR'],'dR_error':err(dr0,c['dR']),'frame_counts_match':not(tfbad or dcbad)}
 for k in MX:row.update({f'{k}_saved':raw0.get(k),f'{k}_recalc':c['raw'][k],f'{k}_abs_error':e[k],f'est_{k}_saved':est0.get(k),f'est_{k}_recalc':c['estimated'][k],f'est_{k}_abs_error':ee[k]})
 row.update({'captcha_saved':score0,'captcha_recalc':c['captcha'],'captcha_abs_error':err(score0,c['captcha']),'threshold_saved':threshold0,'passed_saved':passed0,'duration_ms':duration})
 errs=[x for x in [*e.values(),*ee.values(),row['dR_error'],row['captcha_abs_error']] if x is not None]
 row['numeric_match']=all(x<=TOL for x in errs) and row['frame_counts_match'] and kfmatch is not False
 return row
def ab_bases():
 d=load(AB_BASE);out={}
 for a in ('l1','l2','l3','r1','r2','r3'):
  key=next((k for k in d if k.startswith(a+'_baseline')),None)
  if key is None:raise KeyError('missing baseline action '+a)
  out[a]=norm_px(d[key])
 return out
def run_ab(p,rid,bases,sha):
 x=load(p);hand=x['experimentInfo']['selectedHand'].lower();acts=['l1','l2','l3'] if hand=='left' else ['r1','r2','r3']
 expected=[{'action':a,'frameIdx':i} for a in acts for i in find_kfs(bases[a])]
 saved=x['keyframeSpec'];km=(saved==expected);kfs=[{'id':z['action'],'frameIdx':int(z['frameIdx'])} for z in saved]
 rows=[]
 for field,cond in [('trialA','A'),('trialB','B')]:
  t=x[field];c=calc(t['segments'],kfs,bases)
  rows.append(result_row('AB',rid,cond,p,sha,c,{'angle':t.get('rA'),'dtw_angle':t.get('rDA'),'accel':t.get('rAc')},{'angle':t.get('sA'),'dtw_angle':t.get('sDA'),'accel':t.get('sAc')},t.get('captcha'),t.get('tF'),t.get('dC'),t.get('dR'),t.get('totalSegments'),None,None,km,t.get('duration')))
 return rows,{'record_id':rid,'version':x['experimentInfo'].get('version'),'abOrder':x['experimentInfo'].get('abOrder'),'keyframes_match_current_algorithm':km}
def main():
 global AB_BASE,AB_DIR,AB_HTML,AB_HTML_BASE,POOL_DIR,POOL_MANIFEST,PROD_DIR,PROD_HTML
 ap=argparse.ArgumentParser(description='Conditionally replay the archived A/B and prod_v2_pool records.')
 ap.add_argument('--out',type=Path,default=ROOT/'data'/'derived'/'reproducibility')
 ap.add_argument('--ab-dir',type=Path,default=AB_DIR);ap.add_argument('--prod-dir',type=Path,default=PROD_DIR)
 ap.add_argument('--ab-base',type=Path,default=AB_BASE);ap.add_argument('--pool-manifest',type=Path,default=POOL_MANIFEST);ap.add_argument('--pool-dir',type=Path,default=POOL_DIR)
 ap.add_argument('--ab-html',type=Path,default=AB_HTML);ap.add_argument('--ab-html-base',type=Path,default=AB_HTML_BASE);ap.add_argument('--prod-html',type=Path,default=PROD_HTML)
 args=ap.parse_args();out=args.out;out.mkdir(parents=True,exist_ok=True)
 AB_DIR=args.ab_dir;PROD_DIR=args.prod_dir;AB_BASE=args.ab_base;POOL_MANIFEST=args.pool_manifest;POOL_DIR=args.pool_dir;AB_HTML=args.ab_html;AB_HTML_BASE=args.ab_html_base;PROD_HTML=args.prod_html
 abfiles=sorted(AB_DIR.glob('captcha_ab_user_*.json'));prod_dir=PROD_DIR;prodfiles=sorted(prod_dir.glob('hand_captcha_*_user_*.json'))
 if len(abfiles)!=10 or len(prodfiles)!=18:raise RuntimeError(f'Expected 10 A/B and 18 prod records; found {len(abfiles)}, {len(prodfiles)}')
 for p in [AB_BASE,AB_HTML,AB_HTML_BASE,PROD_HTML,POOL_MANIFEST,*prodfiles,*abfiles]:
  if not p.exists():raise FileNotFoundError(p)
 hashes={};hash_rows=[]
 def add(logical,p):
  h=digest(p);hashes[p]=h;hash_rows.append({'logical_input':logical,'sha256':h,'bytes':p.stat().st_size});return h
 add('AB/reference/landmarks_base.json',AB_BASE);add('AB/candidate/hand_captcha_ab_(2).html',AB_HTML);add('AB/candidate/hand_captcha_ab.html',AB_HTML_BASE);add('PROD/candidate/hand_captcha_prod.html',PROD_HTML);manifest=load(POOL_MANIFEST);add('PROD/pool_manifest.json',POOL_MANIFEST)
 bases=ab_bases();rows=[];metas=[];seen=set()
 for i,p in enumerate(abfiles,1):
  x=load(p);pid=x['experimentInfo'].get('participantId')
  if pid in seen:raise RuntimeError('duplicate participantId in A/B inputs')
  seen.add(pid);rid=f'P{i:02d}';h=add(f'AB/{rid}.json',p);rr,m=run_ab(p,rid,bases,h);rows.extend(rr);metas.append(m)
 # pool reference files are resolved from manifest; each selected clip is loaded once.
 clips={z['clip_id']:z for z in manifest['clips']};cache={}
 def getbase(cid,hand):
  if cid not in clips:raise KeyError('clip absent from manifest: '+cid)
  if cid not in cache:
   lm=POOL_DIR/clips[cid]['landmarks_file'];cache[cid]=load(lm);add('PROD/reference/'+clips[cid]['landmarks_file'],lm)
  cl=clips[cid];mirror=cl.get('handedness','').lower()!=hand.lower()
  return norm_px(cache[cid],mirror)
 for i,p in enumerate(prodfiles,1):
  x=load(p);info=x.get('experimentInfo',{});hand=str(info.get('selectedHand','')).lower();kfs=[];bases2={}
  for z in x['keyframes']:
   cid=z.get('clip');cid=cid.get('clip_id') if isinstance(cid,dict) else cid;cid=str(cid)
   if cid not in bases2:bases2[cid]=getbase(cid,hand)
   kfs.append({'id':cid,'frameIdx':int(z['frameIdx'])})
  c=calc(x['segments'],kfs,bases2);sc=x['scores'];rid=f'S{i:02d}'
  add(f'PROD/{rid}.json',p)
  rows.append(result_row('PROD_V2_POOL',rid,'single',p,hashes[p],c,sc.get('raw',{}),sc.get('estimated',{}),sc.get('captcha'),sc.get('totalFrames'),sc.get('detectedFrames'),sc.get('detectionRate'),len(x['segments']),sc.get('threshold'),sc.get('passed'),None,None))
  metas.append({'record_id':rid,'version':info.get('version'),'selectedHand':hand,'keyframes':len(kfs),'segments':len(x['segments'])})
 with (out/'replay_errors.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 with (out/'input_sha256.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=['logical_input','sha256','bytes']);w.writeheader();w.writerows(hash_rows)
 failures=[r for r in rows if not r['numeric_match']]
 validation={'status':'CONDITIONAL_REPLAY','tolerance_abs':TOL,'AB_records':len(abfiles),'AB_trials':20,'prod_v2_pool_sessions':len(prodfiles),'comparison_rows':len(rows),'failures':len(failures),'keyframe_mismatches':sum(m.get('keyframes_match_current_algorithm') is False for m in metas),'all_numeric_checks_pass':not failures,'caveats':['No session-specific executed HTML/build hash.','No session-specific baseline or pool manifest digest.','Current candidate references make this a conditional replay.']}
 (out/'replay_validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
 manifest_out={'created_utc':datetime.now(timezone.utc).isoformat(),'python':sys.version,'platform':platform.platform(),'status':'CONDITIONAL_REPLAY','script_sha256':digest(Path(__file__)),'formula':{'AT':AT,'MX':MX,'weights':WEIGHTS,'threshold':THRESHOLD,'abs_tolerance':TOL,'dtw_angle':'resample user to round(1.2*base length), then minimum sliding-window angle error'},'records':metas,'hash_file':'input_sha256.csv','error_table':'replay_errors.csv','validation':'replay_validation.json'}
 (out/'replay_manifest.json').write_text(json.dumps(manifest_out,indent=2),encoding='utf-8')
 print(json.dumps(validation,indent=2))
 if failures:raise SystemExit(2)
if __name__=='__main__':main()
