"""Pinned prod JS on recorded model projections; no detector/UI/authentication."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import subprocess
import time

from analysis.runtime_benchmark.mano_author_surface_audit import bound
from validation_v03.session_artifacts import canonical, _private

CONTROLS=('self','recorded_alternative','static_start','static_peak','partial_half',
          'missing_alternate','missing_three_of_four','missing_all')
MODES=('full_interval','auto_keyframes')


def bridge(node, script, prod, payload):
    run=subprocess.run([str(node),str(script),str(prod)],input=json.dumps(payload),
                       text=True,capture_output=True,timeout=30,check=True,encoding='utf-8')
    return json.loads(run.stdout)


def execute(display,record,prod,node,output):
    display,record,_=bound(display,record)
    output=_private(output)
    if output.exists() or output.is_relative_to(display) or output.is_relative_to(record):
        raise ValueError('Fresh independent private output required')
    prod=Path(prod).resolve(strict=True);node=Path(node).resolve(strict=True)
    script=Path(__file__).resolve().parents[1]/'validation_v03/frozen_prod_score.cjs'
    ds=json.loads((display/'summary.json').read_text())
    if ds['cases_n']!=64 or ds['release_allowed'] is not False:
        raise ValueError('Complete quarantined64 display cases required')
    output.mkdir();utc=time.time_ns();wall=time.perf_counter_ns();cpu=time.process_time_ns()
    baselines={};converted={};metadata=None
    for case in ds['cases']:
        data=json.loads((display/case['directory_id']/'reference.private.json').read_text())
        if data['source_info']['total_frames']!=25 or len(data['frames'])!=25 or any(
                f.get('detection_semantics')!='known_model_reference_no_detector' for f in data['frames']):
            raise ValueError('Known model reference25 frames required; no detector inference')
        # Recorded exporter uses source_info. Prod expects video_info. Explicit
        # adapter uses actual512x420 dimensions, never silent720x720 fallback.
        data={**data,'video_info':data['source_info']}
        result=bridge(node,script,prod,{'landmark_data':data})
        converted[case['directory_id']]=result['converted']['frames']
        metadata={k:result[k] for k in ('extraction','constants')}
        if case['delta_degrees']==0:
            baselines[case['parent_case'],case['view']]=result['converted']['frames']
    rows=[]
    for case in ds['cases']:
        start=time.perf_counter_ns()
        base=baselines[case['parent_case'],case['view']];alt=converted[case['directory_id']]
        peak=max(range(25),key=lambda i:sum((base[i][j][a]-base[0][j][a])**2 for j in range(21) for a in range(2)))
        responses={'self':base,'recorded_alternative':alt,'static_start':[base[0]]*25,
          'static_peak':[base[peak]]*25,
          'partial_half':[[[(p[a]+base[0][j][a])/2 for a in range(2)] for j,p in enumerate(f)] for f in base],
          'missing_alternate':[f if i%2==0 else None for i,f in enumerate(base)],
          'missing_three_of_four':[f if i%4==0 else None for i,f in enumerate(base)],
          'missing_all':[None]*25}
        requests=[{'id':control+':'+mode,'mode':mode,'base':base,'response':responses[control]}
                  for control in CONTROLS for mode in MODES]
        result=bridge(node,script,prod,{'cases':requests})
        for r in result['results']:
            control,mode=r.pop('id').split(':')
            rows.append({**{k:case[k] for k in ('directory_id','case_id','parent_case','view','delta_degrees')},
                'control':control,'segmentation':mode,'static_peak_index':peak,
                'recorded_final_equal_to_parent':case['H264_comparison']['exact_whole_file_bytes_equal'],**r})
        with (output/'progress.private.jsonl').open('ab') as stream:
            stream.write(canonical({'directory_id':case['directory_id'],'completed_diagnostics_n':len(rows),
                                   'wall_ns':time.perf_counter_ns()-start})+b'\n')
    groups=defaultdict(list)
    for r in rows:groups[r['control'],r['segmentation']].append(r)
    aggregates=[]
    for (control,mode),items in groups.items():
        values=[r['score']['captcha'] for r in items]
        aggregates.append({'control':control,'segmentation':mode,'diagnostics_n':len(items),
          'score_min':min(values),'score_max':max(values),
          'score_threshold_met_n':sum(r['score_threshold_met'] for r in items),
          'all_keyframe_angle_conditions_met_n':sum(all(k['below_threshold'] for k in r['keyframe_angles']) for r in items),
          'rDA_nonzero_n':sum(r['score']['rDA'] is not None and r['score']['rDA']>0 for r in items)})
    exact=[r for r in rows if r['control']=='recorded_alternative' and r['segmentation']=='full_interval'
           and r['delta_degrees']!=0 and r['recorded_final_equal_to_parent']]
    summary={'version':'frozen_prod_coordinate_diagnostic_v1','cases_n':64,'diagnostics_n':len(rows),
      'independent_families_n':0,'human_trials_n':0,'new_inference_n':0,'new_videos_n':0,'accepted_into_pool_n':0,
      'release_allowed':False,'hold_validated':False,'authentication_validated':False,
      'source':'known model projection; no camera/detector; source_info explicitly adapted to video_info',
      'segmentation':'synthetic full interval and prod findKeyframes; inclusive boundary response duplication',
      'missingness':'null frames, fixed index schedule; computeScores filters detections and index-resamples',
      'metrics':'mDA sliding window; mAc index second difference; no physical time derivative',
      'aggregates':aggregates,'exact_final_nonzero_alternatives_n':len(exact),
      'exact_final_alternative_score_min':min(r['score']['captcha'] for r in exact),
      'exact_final_alternative_score_max':max(r['score']['captcha'] for r in exact),
      'exact_final_alternative_threshold_met_n':sum(r['score_threshold_met'] for r in exact),
      'timing':{'started_utc_epoch_ns':utc,'ended_utc_epoch_ns':time.time_ns(),
                'wall_ns':time.perf_counter_ns()-wall,'own_python_cpu_ns':time.process_time_ns()-cpu,
                'node_child_cpu_measured':False,'receipt_verification_included':False},**metadata}
    (output/'diagnostics.private.json').write_bytes(canonical({'rows':rows}))
    (output/'summary.json').write_bytes(canonical(summary))
    (output/'extraction.private.json').write_bytes(canonical(metadata))
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('display','record','prod','node','output'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();r=execute(**vars(args))
    print(json.dumps({'diagnostics_n':r['diagnostics_n'],'release_allowed':r['release_allowed']}))
