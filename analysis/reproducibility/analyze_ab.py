#!/usr/bin/env python3
"""Paired, descriptive/exact small-sample analysis of the original 10 A/B JSON records."""
import argparse,csv,glob,hashlib,itertools,json,math,os,sys
from pathlib import Path
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
OUT_DIR=ROOT/'data'/'derived'/'reproducibility'
sys.path.insert(0,str(HERE))
import reproduce_scores as replay
AB_DIR=Path(os.environ.get('CAPTCHA_AB_DIR',ROOT/'data'/'raw'/'ab'))
FIELDS={'captcha':('captcha',1),'angle':('rA',1),'dtw_angle':('rDA',1),'accel':('rAc',1),'sA':('sA',1),'sDA':('sDA',1),'sAc':('sAc',1),'duration_sec':('duration',0.001),'detection_rate':('dR',1),'total_frames':('tF',1),'detected_frames':('dC',1)}
def load_json(p):
 with p.open(encoding='utf-8-sig') as f:return json.load(f)
def exact_flip(d):
 d=np.asarray(d,float);obs=abs(d.mean());vals=[abs(np.mean(d*np.array(s))) for s in itertools.product([-1,1],repeat=len(d))]
 return sum(v>=obs-1e-14 for v in vals)/len(vals)
def ci_mean(d,level=.95):
 d=np.asarray(d,float);m=d.mean();se=stats.sem(d);q=stats.t.ppf((1+level)/2,len(d)-1)
 return [float(m-q*se),float(m+q*se)]
def summarize(d):
 d=np.asarray(d,float);d=d[np.isfinite(d)];n=len(d);m=float(d.mean());sd=float(d.std(ddof=1)); dz=m/sd if sd else None
 return {'n':n,'mean':m,'median':float(np.median(d)),'sd':sd,'mean_ci95':ci_mean(d),'dz':dz,'sign_flip_exact_p':exact_flip(d),'sign_test_two_sided_p':float(stats.binomtest(int(np.sum(d>0)),n,0.5).pvalue) if np.all(d!=0) else None,'positive':int(np.sum(d>0)),'negative':int(np.sum(d<0)),'ties':int(np.sum(d==0))}
def summarize_condition(d):
 d=np.asarray(d,float);d=d[np.isfinite(d)]
 return {'n':len(d),'mean':float(d.mean()),'median':float(np.median(d)),'sd':float(d.std(ddof=1)),'mean_ci95':ci_mean(d)}
def main():
 global AB_DIR,OUT_DIR
 ap=argparse.ArgumentParser(description='Paired analysis of archived A/B JSON records.')
 ap.add_argument('--ab-dir',type=Path,default=AB_DIR);ap.add_argument('--ab-base',type=Path,default=replay.AB_BASE);ap.add_argument('--out',type=Path,default=OUT_DIR)
 args=ap.parse_args();AB_DIR=args.ab_dir;OUT_DIR=args.out;OUT_DIR.mkdir(parents=True,exist_ok=True);replay.AB_DIR=AB_DIR;replay.AB_BASE=args.ab_base
 ps=sorted(Path(x) for x in glob.glob(str(AB_DIR/'captcha_ab_user_*.json')))
 if len(ps)!=10:raise RuntimeError(f'Expected 10 original A/B JSON files, found {len(ps)}')
 rec=[];seen=set()
 for p in ps:
  x=load_json(p);info=x['experimentInfo'];pid=str(info['participantId'])
  if pid in seen:raise RuntimeError('duplicate participantId '+pid)
  seen.add(pid)
  vals={}
  for cond,key in [('A','trialA'),('B','trialB')]:
   tr=x[key];vals[cond]={}
   if len(tr.get('segments',[]))!=11:raise RuntimeError(f"{p.name} {key}: expected 11 saved segments")
   for name,(field,mul) in FIELDS.items():
    z=tr.get(field)
    vals[cond][name]=None if z is None else float(z)*(mul or 1)
  order=info.get('abOrder');order=''.join(order) if isinstance(order,list) else str(order)
  rec.append({'pid':pid,'order':order,'version':info.get('version'),'vals':vals,'file':p})
 if any(set(r['vals'])!={'A','B'} for r in rec):raise RuntimeError('unpaired record')
 rows=[]
 for i,r in enumerate(rec,1):
  row={'participant':f'P{i:02d}','order':r['order'],'version':r['version'],'source_file':r['file'].name}
  for m in FIELDS:
   a=r['vals']['A'][m];b=r['vals']['B'][m]
   row[m+'_A']=a;row[m+'_B']=b;row[m+'_B_minus_A']=None if a is None or b is None else b-a
  rows.append(row)
 with (OUT_DIR/'ab_participant_results.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 output={'status':'CONDITIONAL_INTERPRETATION','participants':len(rec),'unique_participant_ids':len(seen),'AB_order_counts':{o:sum(r['order']==o for r in rec) for o in sorted({r['order'] for r in rec})},'condition_summary':{},'paired_B_minus_A':{},'order_interaction':{},'data_checks':{'all_records_have_two_trials':True,'all_sessions_11_segments':True,'threshold_pass_status_observed':False,'timing_unit':'seconds converted from stored performance.now() duration milliseconds'}}
 for m in FIELDS:
  output['condition_summary'][m]={c:summarize_condition([r['vals'][c][m] for r in rec]) for c in ('A','B')}
  d=[r['vals']['B'][m]-r['vals']['A'][m] for r in rec if r['vals']['A'][m] is not None and r['vals']['B'][m] is not None]
  output['paired_B_minus_A'][m]=summarize(d)
 for m in ('captcha','duration_sec'):
  ab=np.array([r['vals']['B'][m]-r['vals']['A'][m] for r in rec if r['order']=='AB'],float)
  ba=np.array([r['vals']['B'][m]-r['vals']['A'][m] for r in rec if r['order']=='BA'],float)
  # exact permutation of order labels, preserving observed group sizes
  vals=[]
  allv=np.array([r['vals']['B'][m]-r['vals']['A'][m] for r in rec],float)
  n=len(ab);obs=abs(ab.mean()-ba.mean())
  for idx in itertools.combinations(range(len(allv)),n):
   mask=np.zeros(len(allv),bool);mask[list(idx)]=True
   vals.append(abs(allv[mask].mean()-allv[~mask].mean()))
  output['order_interaction'][m]={'AB_n':len(ab),'AB_mean_delta':float(ab.mean()),'BA_n':len(ba),'BA_mean_delta':float(ba.mean()),'BA_minus_AB_delta':float(ba.mean()-ab.mean()),'exact_group_permutation_p':sum(v>=obs-1e-14 for v in vals)/len(vals),'exploratory':True}
 # Independently exercise the coordinate replay on every original A/B JSON before interpreting stored values.
 bases=replay.ab_bases();replay_checks=[]
 for i,r in enumerate(rec,1):
  rr,meta=replay.run_ab(r['file'],f'P{i:02d}',bases,replay.digest(r['file']))
  replay_checks.extend(rr)
 if len(replay_checks)!=20 or any(not z['numeric_match'] for z in replay_checks):raise RuntimeError('independent raw-coordinate replay mismatch')
 output['coordinate_replay_check']={'trials':len(replay_checks),'all_stored_values_match':True,'max_score_abs_error':max(z['captcha_abs_error'] for z in replay_checks)}
 (OUT_DIR/'ab_stats_summary.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
 with (OUT_DIR/'ab_condition_summary.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f);w.writerow(['metric','condition','n','mean','median','sd','ci95_low','ci95_high'])
  for m,cs in output['condition_summary'].items():
   for c,s in cs.items():w.writerow([m,c,s['n'],s['mean'],s['median'],s['sd'],*s['mean_ci95']])
 with (OUT_DIR/'ab_paired_summary.csv').open('w',newline='',encoding='utf-8-sig') as f:
  w=csv.writer(f);w.writerow(['metric','n','mean_B_minus_A','median_B_minus_A','sd','ci95_low','ci95_high','dz','exact_sign_flip_p','positive','negative','ties'])
  for m,s in output['paired_B_minus_A'].items():w.writerow([m,s['n'],s['mean'],s['median'],s['sd'],*s['mean_ci95'],s['dz'],s['sign_flip_exact_p'],s['positive'],s['negative'],s['ties']])
 fig,axs=plt.subplots(1,3,figsize=(12,4))
 for ax,m,title in zip(axs,['captcha','duration_sec','detection_rate'],['Final score','Duration (s)','Landmark detection rate']):
  for r in rec:
   ax.plot([0,1],[r['vals']['A'][m],r['vals']['B'][m]],color='#667788',alpha=.55,marker='o')
  ax.set_xticks([0,1],['A','B']);ax.set_title(title);ax.grid(alpha=.2)
 fig.tight_layout();fig.savefig(OUT_DIR/'ab_paired_plot.png',dpi=160);plt.close(fig)
 print(json.dumps({'participants':10,'trials':20,'score_delta':output['paired_B_minus_A']['captcha'],'duration_delta':output['paired_B_minus_A']['duration_sec'],'coordinate_replay_check':output['coordinate_replay_check']},indent=2))
if __name__=='__main__':main()
