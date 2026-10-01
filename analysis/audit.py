"""Read-only phase-one audit; individual records stay in ignored data/derived."""
from pathlib import Path
import collections, datetime, hashlib, importlib.metadata, json, platform, subprocess, sys, time
import numpy as np
from scipy import stats
from openpyxl import load_workbook

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'data/raw'
OUT=ROOT/'data/derived'
MX={'angle':46.9413,'dtw_angle':44.0014,'accel':0.1926}
WEIGHTS={'angle':.25,'dtw_angle':.38,'accel':.37}
SEED=20261001
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def dump(p,d):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def summary(x):
    x=np.array(x,dtype=float)
    return dict(n=len(x),mean=float(x.mean()),median=float(np.median(x)),sd_sample=float(x.std(ddof=1)) if len(x)>1 else None,min=float(x.min()),max=float(x.max()))
def wilson(k,n):
    z=stats.norm.ppf(.975); p=k/n; den=1+z*z/n
    mid=(p+z*z/(2*n))/den; half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [float(mid-half),float(mid+half)]
def pass_stats(x,t=.25):
    k=sum(v>=t for v in x); return dict(passed=k,total=len(x),rate=k/len(x),wilson95=wilson(k,len(x)))
def boolean(v):
    if isinstance(v,bool): return v
    if v in ('True','true'): return True
    if v in ('False','false'): return False
    raise ValueError(f'Not a boolean: {v!r}')
def score(raw,dr):
    sub={k:0. if raw[k] is None else float(np.clip(dr*max(0,1-raw[k]/MX[k]),0,1)) for k in MX}
    return sum(sub[k]*WEIGHTS[k] for k in MX),sub
def longest_missing(frames,key='lm'):
    longest=run=0
    for f in frames:
        run=run+1 if f.get(key) is None or f.get(key)==[] else 0
        longest=max(longest,run)
    return longest
def alpha(x):
    var=x.sum(axis=1).var(ddof=1)
    return float(x.shape[1]/(x.shape[1]-1)*(1-x.var(axis=0,ddof=1).sum()/var)) if var else None
def sus_transform(x):
    x=np.asarray(x,dtype=float)
    if x.ndim!=2 or x.shape[1]!=10 or not np.isfinite(x).all() or not ((x>=1)&(x<=5)&(x==np.floor(x))).all(): raise ValueError('Expected complete 10-item integer responses 1..5')
    y=x.copy(); y[:,::2]-=1; y[:,1::2]=5-y[:,1::2]
    return y
def main():
    start=time.perf_counter(); run_id=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    result={}; people=[]; phases=collections.defaultdict(lambda:[0,0]); hand=collections.defaultdict(lambda:[0,0]); clips=collections.defaultdict(lambda:[0,0]); thirds=np.zeros((3,2),dtype=int)
    for p in sorted(RAW.glob('2*/2*/*.json')):
        d=read(p); s=d['scores']; segs=d['segments']; frames=[f for seg in segs for f in seg['frames']]
        valid=sum(f['lm'] is not None for f in frames); total=len(frames); calc,sub=score(s['raw'],s['detectionRate'])
        short=sum(sum(f['lm'] is not None for f in seg['frames'])<3 for seg in segs)
        dup=rev=bad=nonfinite=outside=0; jumps=[]; deltas=[]
        for seg in segs:
            ts=np.array([f['t'] for f in seg['frames']]); dt=np.diff(ts); dup+=int(sum(dt==0)); rev+=int(sum(dt<0)); deltas.extend(dt[dt>0].tolist())
            prev=None
            for f in seg['frames']:
                if f['lm'] is None: prev=None; continue
                a=np.asarray(f['lm']); bad+=int(a.shape!=(21,3)); nonfinite+=int(not np.isfinite(a).all()); outside+=int(((a[:,:2]<0)|(a[:,:2]>1)).any())
                if prev is not None: jumps.append(float(np.linalg.norm(a[:,:2]-prev[:,:2],axis=1).max()))
                prev=a
            c=clips[seg['fromClip']+'->'+seg['toClip']]; c[0]+=len(seg['frames']); c[1]+=sum(f['lm'] is None for f in seg['frames'])
            for i,f in enumerate(seg['frames']):
                j=min(2,3*i//max(1,len(seg['frames']))); thirds[j,0]+=1; thirds[j,1]+=int(f['lm'] is None)
        logs=d.get('sessionLog',[])
        for f in logs:
            phases[f['phase']][0]+=1; phases[f['phase']][1]+=int(not f['detected'])
        hs=hand[d['experimentInfo']['selectedHand']]; hs[0]+=total; hs[1]+=total-valid
        duration=sum(seg['duration'] for seg in segs)/1000
        people.append(dict(file=p.relative_to(RAW).as_posix(),id=d['experimentInfo']['participantId'],hand=d['experimentInfo']['selectedHand'],score=s['captcha'],recomputed=calc,score_delta=calc-s['captcha'],total=total,detected=valid,recorded_total=s['totalFrames'],recorded_detected=s['detectedFrames'],missing=total-valid,dr=valid/total,detected_only=score(s['raw'],1)[0],whole_session_s=(logs[-1]['t']-logs[0]['t'])/1000 if logs else None,segment_s=duration,max_gap_frames=max(longest_missing(seg['frames']) for seg in segs),duplicates=dup,reversals=rev,bad_shapes=bad,nonfinite=nonfinite,outside_image_frames=outside,max_joint_step=max(jumps) if jumps else None,median_dt_ms=float(np.median(deltas)),effective_fps=total/duration,short_segments=short,log_frames=len(logs),log_missing=sum(not f['detected'] for f in logs),raw=s['raw']))
    dump(OUT/'human_audit.json',people)
    scores=[x['score'] for x in people]; missing=np.array([1-x['dr'] for x in people]); rho=stats.spearmanr(scores,missing)
    result['human']=dict(score=summary(scores),passing=pass_stats(scores),segment_seconds=summary([x['segment_s'] for x in people]),whole_session_seconds=summary([x['whole_session_s'] for x in people]),detected_only_score=summary([x['detected_only'] for x in people]),detected_only_passing=pass_stats([x['detected_only'] for x in people]),score_max_abs_delta=max(abs(x['score_delta']) for x in people),total_frames=sum(x['total'] for x in people),missing_frames=sum(x['missing'] for x in people),unique_participants=len(set(x['id'] for x in people)),sessions=len(people),short_segments=sum(x['short_segments'] for x in people),count_mismatches=sum(x['total']!=x['recorded_total'] or x['detected']!=x['recorded_detected'] for x in people),max_gap_frames=max(x['max_gap_frames'] for x in people),duplicates=sum(x['duplicates'] for x in people),reversals=sum(x['reversals'] for x in people),bad_shapes=sum(x['bad_shapes'] for x in people),nonfinite=sum(x['nonfinite'] for x in people),outside_image_frames=sum(x['outside_image_frames'] for x in people),effective_fps=summary([x['effective_fps'] for x in people]),missing_score_spearman=dict(rho=float(rho.statistic),p=float(rho.pvalue)),phase_counts=dict(phases),hand_counts=dict(hand),transition_counts=dict(clips),segment_thirds_counts=thirds.tolist())
    h=read(next(RAW.glob('해머3*/hammer_exp3_results.json'))); rows=[]
    for d in h['results']:
        s=d['prod_score']; fs=[f for t in d['transitions'] for f in t['frames']]; calc,_=score(s['raw'],s['detection_rate']); kfs=d['keyframes']
        rows.append(dict(pair=[d['clip_a'],d['clip_b']],score=s['captcha_score'],score_delta=calc-s['captcha_score'],n=len(fs),missing=sum(not f['detected'] for f in fs),gates_passed=sum(boolean(k['passed']) for k in kfs),gates=len(kfs),gate_all=all(boolean(k['passed']) for k in kfs),gate_recomputed_all=all(k['detected'] and k['error']<38 for k in kfs),string_bool_count=sum(isinstance(k['passed'],str) for k in kfs),fade_frames=sum(f['type']!='video' for f in fs),bad_shapes=sum(f['detected'] and np.asarray(f['landmarks']).shape!=(21,2) for f in fs)))
    dump(OUT/'hamer_audit.json',rows)
    hs=[x['score'] for x in rows]
    result['hamer']=dict(score=summary(hs),score_passing=pass_stats(hs),gate_all_passed=sum(x['gate_all'] for x in rows),gates_passed=sum(x['gates_passed'] for x in rows),gates_total=sum(x['gates'] for x in rows),gate_mismatches=sum(x['gate_all']!=x['gate_recomputed_all'] for x in rows),bool_strings=sum(x['string_bool_count'] for x in rows),frames=sum(x['n'] for x in rows),missing=sum(x['missing'] for x in rows),fade_frames=sum(x['fade_frames'] for x in rows),score_max_abs_delta=max(abs(x['score_delta']) for x in rows),unique_unordered_pairs=len(set(tuple(sorted(x['pair'])) for x in rows)),ordered_pairs=len(set(tuple(x['pair']) for x in rows)),bad_shapes=sum(x['bad_shapes'] for x in rows),stop_on_fail=h['metadata']['stop_on_fail'])
    # Historical independent tests reproduced for audit only, not valid population inference.
    result['historical_tests_only']={name:dict(statistic=float(test.statistic),p=float(test.pvalue)) for name,test in [('welch',stats.ttest_ind(scores,hs,equal_var=False)),('mannwhitney',stats.mannwhitneyu(scores,hs,alternative='two-sided')),('ks',stats.ks_2samp(scores,hs))]}
    rng=np.random.default_rng(SEED)
    result['human']['participant_bootstrap_mean95']=np.quantile(rng.choice(scores,(10000,len(scores)),replace=True).mean(axis=1),[.025,.975]).tolist()
    # Leave-one-source-gesture-out is sensitivity, not a CI over independent combinations.
    gesture_keys=sorted(set(k for row in rows for k in row['pair']))
    result['hamer']['leave_one_gesture_out_mean_range']=[min(np.mean([x['score'] for x in rows if k not in x['pair']]) for k in gesture_keys),max(np.mean([x['score'] for x in rows if k not in x['pair']]) for k in gesture_keys)]
    result['sus']={}
    for p in RAW.glob('*.xlsx'):
        wb=load_workbook(p,data_only=True); ws=wb.active; vals=list(ws.values); a=np.array([row[1:11] for row in vals[1:]],dtype=float)
        complete=np.isfinite(a).all(axis=1); y=sus_transform(a[complete]); total=y.sum(axis=1)*2.5
        result['sus'][str(len(a))]=dict(responses=len(a),complete=int(complete.sum()),missing_cells=int((~np.isfinite(a)).sum()),score=summary(total),alpha_reverse_coded=alpha(y),alpha_raw=alpha(a[complete]),raw_item_means=a[complete].mean(axis=0).tolist(),transformed_item_means=y.mean(axis=0).tolist(),mean95_t=[float(v) for v in stats.t.interval(.95,len(total)-1,loc=total.mean(),scale=stats.sem(total))])
    attack=read(RAW/'captcha_attack/results/attack_results_raw.json')
    result['existing_ik_saved_outputs']={}
    for condition in sorted(set(x['condition'] for x in attack)):
        rows2=[x for x in attack if x['condition']==condition]
        result['existing_ik_saved_outputs'][condition]={channel:dict(score=summary([x[channel+'_score'] for x in rows2]),passing=pass_stats([x[channel+'_score'] for x in rows2])) for channel in ['channelA','channelB']}
    result['table10_weighted_sum']=.747*.44+.464*.31+.337*.25
    dump(ROOT/'reports/phase1_aggregates.json',result)
    inventory=read(ROOT/'data/inventory.json'); mismatches=[]
    for row in inventory:
        for base in [RAW,ROOT.parent/'CAPTCHA']:
            p=base/row['path']
            if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']: mismatches.append(row['path'])
    assert not mismatches, mismatches
    git=['git','-c',f'safe.directory={ROOT.as_posix()}']
    commit=subprocess.check_output(git+['rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    config=dict(seed=SEED,max_norm=MX,weights=WEIGHTS,threshold=.25,exclusions='No person or trial excluded; incomplete SUS rows excluded with counts; no interpolation')
    code_hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'analysis').glob('*')) if p.is_file()}
    manifest=dict(run_id=run_id,code_commit=commit,code_hashes=code_hashes,config=config,config_sha256=hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest(),input_inventory_sha256=hashlib.sha256((ROOT/'data/inventory.json').read_bytes()).hexdigest(),input_hashes=inventory,environment=dict(python=platform.python_version(),platform=platform.platform(),packages={k:importlib.metadata.version(k) for k in ['numpy','scipy','openpyxl','pypdf']}),elapsed_s=time.perf_counter()-start,original_and_snapshot_verified=True,output='reports/phase1_aggregates.json')
    dump(OUT/f'{run_id}_run.json',manifest)
    public={k:v for k,v in manifest.items() if k!='input_hashes'}
    dump(ROOT/'reports/latest_run.json',public)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
