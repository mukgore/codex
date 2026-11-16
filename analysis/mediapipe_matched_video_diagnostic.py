"""Recorded pixel-only MediaPipe on completed synthetic source/candidate/final media."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import subprocess
import sys
import time

from analysis.frozen_prod_score_diagnostic import bridge
from analysis.mediapipe_matched_metrics import evaluate
from analysis.runtime_benchmark.mano_author_surface_audit import bound
from analysis.runtime_benchmark.journal import Journal,export_bundle,verify_bundle
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import canonical,_private


def execute(display,display_record,resource_preflight,prod,node,worker_root,output):
    display,display_record,before=bound(display,display_record);output=_private(output)
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for p in (display,display_record)):
        raise ValueError('Fresh independent inference output required')
    preflight=json.loads(_private(resource_preflight).read_text())
    ds=json.loads((display/'summary.json').read_text())
    if ds['rendered_source_cases_n']!=32 or ds['H264_rendition_videos_n']!=8 or ds['release_allowed'] is not False:
        raise ValueError('Complete quarantined matched32-source/8-final display required')
    sys.path.insert(0,str(Path(worker_root).resolve(strict=True)))
    from dataset_pipeline.common import LANDMARK_NAMES
    media=[]
    for c in ds['cases']:
        folder=display/c['directory_id'];items=[('source',folder/'source.private.avi')]
        for kind,pattern,present in [('candidate','candidates/*/masked.mp4',c['masked_candidate_created']),
                                     ('final','renditions/*/video.mp4',c['H264_rendition_created'])]:
            if present:
                found=list(folder.glob(pattern))
                if len(found)!=1:raise ValueError('Unique actual media required')
                items.append((kind,found[0]))
        media.extend({'case':c['case'],'arm':c['arm'],'hand':c['hand'],'seed':c['seed'],'view':c['view'],
                      'kind':kind,'video':path,'reference':folder/'reference.private.json'} for kind,path in items)
    if len(media)!=48:raise ValueError('Registered48 video denominator differs')
    journal=Journal(output/'journal',{'condition_id':'TF04_INSTALLED_MEDIAPIPE_PIXEL_ONLY_BASELINE',
      'endpoint':'actual_offline48-video_extraction_and_known_projection_error_plus_fixed_prod_scores',
      'input_exposure':'worker sees video pixels only; references used in parent after extraction',
      'cache_state':'fresh worker/graph per video; warm verified resource cache; OS/import caches uncontrolled',
      'planned_frames':1200,'timeout_seconds':600,'scope':'synthetic diagnostic; not human comparison, strong attack, online authentication or browser detector parity'})
    rows=[];score_rows=[];completed=0;wall=time.perf_counter_ns();cpu=time.process_time_ns();utc=time.time_ns()
    script=Path(__file__).resolve().parents[1]/'validation_v03/frozen_prod_score.cjs'
    try:
        for i,m in enumerate(media):
            journal.check_budget();folder=output/f'm{i:02d}';folder.mkdir();start=time.perf_counter_ns();case_utc=time.time_ns()
            request={'video_path':str(m['video'].resolve()),'confidence':.5,
              'expected_resource_fingerprint':preflight['resource_fingerprint']}
            (folder/'request.private.json').write_bytes(canonical(request))
            command=[sys.executable,'-m','analysis.runtime_benchmark.mediapipe_video_worker','--request',str(folder/'request.private.json'),
              '--output',str(folder/'predictions.private.json'),'--worker-root',str(Path(worker_root).resolve())]
            (folder/'command.private.json').write_bytes(canonical({'command':command,'cwd':str(Path.cwd()),'started_utc_epoch_ns':case_utc}))
            with journal.stage(f'm{i:02d}_actual_pixel_only_worker'):
                with (folder/'stdout.private.log').open('xb') as stdout,(folder/'stderr.private.log').open('xb') as stderr:
                    result=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=90,check=False)
                subprocess_wall=time.perf_counter_ns()-start
                if result.returncode:raise RuntimeError('Pixel-only worker failed; request/command/stdout/stderr retained')
                inference=json.loads((folder/'predictions.private.json').read_text());predicted=inference['frames']
                if len(predicted)!=25:raise ValueError('Complete prediction denominator required')
                for f in predicted:journal.frame_completed(completed,f['detected']);completed+=1
            # Groundtruth/reference coordinates enter only after worker exit;
            # they never appear in its request or Hands.process input.
            with journal.stage(f'm{i:02d}_reference_metrics_and_verbatim_prod_score'):
                ref=json.loads(m['reference'].read_text());metrics=evaluate(ref['frames'],predicted,LANDMARK_NAMES)
                converted=bridge(node,script,prod,{'landmark_data':{**ref,'video_info':ref['source_info']}})
                base=converted['converted']['frames'];info=ref['source_info']
                response=[None if not f['detected'] else [[f['landmarks_px'][n]['x']/info['width'],
                  f['landmarks_px'][n]['y']/info['height']] for n in LANDMARK_NAMES] for f in predicted]
                scores=bridge(node,script,prod,{'cases':[{'id':mode,'mode':mode,'base':base,'response':response}
                  for mode in ('full_interval','auto_keyframes')]})
                for s in scores['results']:
                    mode=s.pop('id');score_rows.append({**{k:m[k] for k in ('case','arm','hand','seed','view','kind')},'segmentation':mode,**s})
                (folder/'metrics.private.json').write_bytes(canonical(metrics));(folder/'scores.private.json').write_bytes(canonical(scores))
            row={**{k:m[k] for k in ('case','arm','hand','seed','view','kind')},
              **{k:v for k,v in metrics.items() if k!='per_frame'},
              'started_utc_epoch_ns':case_utc,'ended_utc_epoch_ns':time.time_ns(),'worker_subprocess_wall_ns':subprocess_wall,
              'worker_own_cpu_ns':inference['timing']['worker_own_cpu_ns'],
              'worker_batch_extract_wall_ns':inference['timing']['batch_extract_wall_ns'],
              'worker_batch_extract_own_cpu_ns':inference['timing']['batch_extract_own_cpu_ns'],
              'validated_video_diagnostic_wall_ns':time.perf_counter_ns()-start,'graph_reset_per_video':True,
              'frame_events_scope':'accounted after complete batch extraction, not per-frame latency'}
            rows.append(row);(folder/'summary.private.json').write_bytes(canonical(row))
            print('MediaPipe diagnostic videos '+str(len(rows))+'/48',flush=True)
        if completed!=1200 or len(rows)!=48 or len(score_rows)!=96:raise ValueError('Registered inference/score denominators differ')
        if verify(display_record)!=before:raise ValueError('Completed display evidence changed')
        journal.finish('COMPLETED')
    finally:
        if not journal.closed:journal.close_without_terminal()
    export_bundle(output/'journal',output/'journal_bundle.private.zip');checked=verify_bundle(output/'journal_bundle.private.zip')
    groups=defaultdict(list)
    for r in rows:groups[r['arm'],r['kind']].append(r)
    aggregates=[]
    for (arm,kind),values in groups.items():
        points=sum(r['detected_point_comparisons_n'] for r in values)
        weighted=sum(r['conditional_mean_point_error_pixels']*r['detected_point_comparisons_n'] for r in values if r['conditional_mean_point_error_pixels'] is not None)
        detected=sum(r['detected_frames_n'] for r in values)
        target=sum(r['conditional_middle_PIP_error_pixels']*r['detected_frames_n'] for r in values if r['conditional_middle_PIP_error_pixels'] is not None)
        norm_n=sum(r['normalized_point_comparisons_n'] for r in values)
        norm=sum(r['conditional_mean_error_reference_hand_lengths']*r['normalized_point_comparisons_n'] for r in values if r['conditional_mean_error_reference_hand_lengths'] is not None)
        aggregates.append({'arm':arm,'kind':kind,'videos_n':len(values),'attempted_frames_n':25*len(values),
          'detected_frames_n':detected,'detected_point_comparisons_n':points,
          'conditional_mean_point_error_pixels':weighted/points if points else None,
          'conditional_middle_PIP_error_pixels':target/detected if detected else None,
          'normalized_point_comparisons_n':norm_n,'conditional_mean_error_reference_hand_lengths':norm/norm_n if norm_n else None})
    score_groups=defaultdict(list)
    for r in score_rows:score_groups[r['arm'],r['kind'],r['segmentation']].append(r)
    score_summary=[{'arm':k[0],'kind':k[1],'segmentation':k[2],'videos_n':len(v),
      'score_threshold_met_n':sum(r['score_threshold_met'] for r in v),
      'all_keyframe_angle_conditions_met_n':sum(all(x['below_threshold'] for x in r['keyframe_angles']) for r in v),
      'score_and_keyframe_conditions_met_n':sum(r['score_threshold_met'] and all(x['below_threshold'] for x in r['keyframe_angles']) for r in v),
      'score_min':min(r['score']['captcha'] for r in v),'score_max':max(r['score']['captcha'] for r in v)} for k,v in score_groups.items()]
    summary={'version':'mediapipe_matched_video_pixel_only_v1','videos_n':48,'actual_model_frames_n':1200,
      'detected_frames_n':sum(r['detected_frames_n'] for r in rows),'score_diagnostics_n':96,
      'aggregates':aggregates,'score_aggregates':score_summary,
      'parameters':inference['parameters'],'versions':inference['versions'],
      'source_info_to_video_info_adapter':True,'mirror':False,'new_model_or_asset_downloads_n':0,
      'new_video_generation_n':0,'new_human_trials_n':0,'new_independent_families_n':0,'accepted_into_pool_n':0,'release_allowed':False,
      'browser_prod_detector_equivalence_proven':False,'hold_or_authentication_validated':False,
      'journal_status':checked['status'],'frame_event_scope':'batch accounted; not per-frame model timestamps',
      'timing':{'started_utc_epoch_ns':utc,'ended_utc_epoch_ns':time.time_ns(),'wall_ns':time.perf_counter_ns()-wall,
        'parent_own_cpu_ns':time.process_time_ns()-cpu,'worker_own_cpu_sum_ns':sum(r['worker_own_cpu_ns'] for r in rows),
        'node_child_cpu_measured':False,'scope':'worker import/extract/validate, parent errors/prod score/store and parent recheck; recorder excluded'},
      'limitations':['Synthetic model references are not independent human truth or observed imitation.',
        'Conditional errors exclude missing detections; missing frames stay in full denominators and prod score inputs.',
        'Existing Python video-mode confidence.5 differs from browser prod.35/.4; no detector parity claim.',
        'Python graph simulates33333us per call; decoded8FPS PTS are retained for analysis but not fed to graph.',
        'Fresh worker/graph per video, warm resource/OS caches uncontrolled; not a controlled cold/warm or online latency test.',
        'Raw world/handedness outputs are retained privately; no metric depth or handedness correctness claim.']}
    (output/'summary.json').write_bytes(canonical(summary));(output/'videos.private.json').write_bytes(canonical({'rows':rows}))
    (output/'scores.private.json').write_bytes(canonical({'rows':score_rows}))
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (output/'video_metrics.csv').open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('display','display-record','resource-preflight','prod','node','worker-root','output'):
        p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();s=execute(**vars(a));print(json.dumps({'videos_n':s['videos_n'],'actual_model_frames_n':s['actual_model_frames_n'],'detected_frames_n':s['detected_frames_n']}))
