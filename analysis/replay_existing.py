"""Replay provided attack stage 3/4 from saved observations in a local work copy."""
from pathlib import Path
import datetime, hashlib, json, os, shutil, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[1]
raw=ROOT/'data/raw/circle_edge_attack'
work=ROOT/'data/work/circle_edge_attack'
work.mkdir(parents=True,exist_ok=True)
files=['common.py','phase2_attack.py','scoring.py','phase3_evaluate.py','reference_library.json','attack_results.json']
for name in files: shutil.copy2(raw/name,work/name)
start=time.perf_counter()
env=dict(os.environ,PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1')
run=subprocess.run([sys.executable,'phase3_evaluate.py'],cwd=work,env=env,capture_output=True,text=True,encoding='utf-8')
(work/'replay_stdout.txt').write_text(run.stdout,encoding='utf-8')
(work/'replay_stderr.txt').write_text(run.stderr,encoding='utf-8')
if run.returncode: raise RuntimeError(run.stderr[-2000:])
new=json.loads((work/'results/summary.json').read_text(encoding='utf-8'))
old=json.loads((raw/'results/summary.json').read_text(encoding='utf-8'))
keys=['n_correct_hamming_top1','n_correct_majority_top1','stage4_n_passed_of_16','stage4_avg_score','stage2_overall_bit_accuracy']
report={'run_id':datetime.datetime.now(datetime.timezone.utc).isoformat(),'code_commit':subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'input_sha256':{name:hashlib.sha256((raw/name).read_bytes()).hexdigest() for name in files},'config':{'stage':'saved observations -> matching -> coordinate scoring','threshold':.25,'seed':None},'result':{k:new[k] for k in keys},'delta':{k:new[k]-old[k] for k in keys},'current_replay_seconds':time.perf_counter()-start,'historical_pixel_ms_per_frame':new['runtime_ms_per_frame_avg'],'limitations':['Pixel extraction not rerun: original level3 videos absent from supplied folder.','Reverse sequences reuse reversed forward bits, not independent videos.','Coordinate score is not server or camera end-to-end authentication.','Provided method uses fingertip visibility bits, not circle-center/radius-only matching.']}
# Test unique identification separately from deterministic argmin top-1.
sys.path.insert(0,str(work))
from phase2_attack import match_sequence
ref=json.loads((work/'reference_library.json').read_text(encoding='utf-8'))
attack=json.loads((work/'attack_results.json').read_text(encoding='utf-8'))
ties=0
for d in attack.values():
    bits=[f['bits'] for f in d['per_frame']]
    for seq in [bits,list(reversed(bits))]:
        dist=match_sequence(seq,ref)['hamming']['all_scores']; ties+=int(dist.count(min(dist))>1)
report['top1_tie_cases']=ties
(ROOT/'reports/attack_replay.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
