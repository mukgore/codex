"""One pixel-only MediaPipe video worker; isolated existing ASCII resource fix."""
import argparse
from contextlib import contextmanager
import importlib.metadata
import inspect
import json
import math
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace


@contextmanager
def relative_resources(solution_base,resources):
    relative=os.path.relpath(resources,Path.cwd())
    if not relative.isascii():raise ValueError('Same-drive ASCII-relative resource directory required')
    previous=solution_base.os
    class ResourcePath:
        def __getattr__(self,name):return getattr(os.path,name)
        def abspath(self,value):
            if value==solution_base.__file__:return str(Path(relative)/'mediapipe/python/solution_base.py')
            return os.path.abspath(value)
    solution_base.os=SimpleNamespace(sep=os.sep,path=ResourcePath())
    try:yield
    finally:solution_base.os=previous


def execute(request_path,output,worker_root,stage_profile_output=None):
    from validation_v03.session_artifacts import _private,canonical
    request=json.loads(_private(request_path).read_text());output=_private(output)
    if set(request)!={'video_path','confidence','expected_resource_fingerprint'} or request['confidence']!=.5:
        raise ValueError('Registered pixel-only request and existing offline confidence.5 required')
    if output.exists():raise FileExistsError('Never overwrite worker predictions')
    if stage_profile_output is not None:
        stage_profile_output=_private(stage_profile_output)
        if stage_profile_output.exists() or stage_profile_output.parent!=output.parent:
            raise ValueError('Fresh stage profile directory beside new predictions required')
    source=_private(request['video_path']).resolve(strict=True)
    utc=time.time_ns();wall=time.perf_counter_ns();cpu=time.process_time_ns()
    sys.path.insert(0,str(Path(worker_root).resolve(strict=True)))
    import cv2
    import mediapipe as mp
    import mediapipe.python.solution_base as solution_base
    from dataset_pipeline.resource_worker import _prepare_resources
    from dataset_pipeline.stage1_extract import _extract_landmarks_native
    from dataset_pipeline import stage1_extract as stage1_module
    if importlib.metadata.version('mediapipe')!='0.10.14':raise ValueError('Existing pinned MediaPipe0.10.14 required')
    if inspect.signature(mp.solutions.hands.Hands).parameters['model_complexity'].default!=1:
        raise ValueError('Existing full model complexity1 default required')
    if 'self._simulated_timestamp += 33333' not in Path(solution_base.__file__).read_text():
        raise ValueError('Known Python graph timestamp convention required')
    cv2.setNumThreads(1)
    resources,fingerprint=_prepare_resources(Path(mp.__file__).parent)
    if fingerprint!=request['expected_resource_fingerprint']:raise ValueError('Installed/cache model assets differ from preflight')
    import_wall=time.perf_counter_ns()-wall;import_cpu=time.process_time_ns()-cpu
    start=time.perf_counter_ns();pcpu=time.process_time_ns()
    with relative_resources(solution_base,resources):
        if stage_profile_output is None:
            frames,info=_extract_landmarks_native(str(source),.5)
        else:
            from analysis.runtime_benchmark.stage_profile import Trace,JsonlSink,profile_stage1,rebuild_summary,recover_events
            stage_profile_output.mkdir()
            events=stage_profile_output/'events.private.jsonl'
            sink=JsonlSink(events);trace=Trace(sink=sink,workload_role='installed_mediapipe_native_video_extraction')
            try:
                with profile_stage1(stage1_module,trace):
                    frames,info=_extract_landmarks_native(str(source),.5)
            finally:
                sink.close()
                profile=trace.summary() if trace.closed else {'status':'INCOMPLETE','recovery':recover_events(events.read_bytes())}
                with (stage_profile_output/'summary.private.json').open('xb') as stream:stream.write(canonical(profile))
                if trace.closed and rebuild_summary(events.read_bytes())!=profile:
                    raise ValueError('Stage trace cannot regenerate measured summary')
            if profile['measurement_metadata_errors_n']:
                raise ValueError('Stage measurement metadata failed')
    batch_wall=time.perf_counter_ns()-start;batch_cpu=time.process_time_ns()-pcpu
    if len(frames)!=25 or info['decoded_frames']!=25 or (info['width'],info['height'])!=(512,420) or info['fps']!=8. or not info['timestamps_monotonic']:
        raise ValueError('Matched25-frame8FPS source grid required')
    for i,f in enumerate(frames):
        if f['frame_idx']!=i or type(f['detected']) is not bool or abs(f['source_pts_ms']-i*125.)>.01:
            raise ValueError('Actual decoded frame identity/PTS differs')
        if f['detected'] and any(not math.isfinite(p[k]) for p in f['landmarks_px'].values() for k in ('x','y','z')):
            raise ValueError('Nonfinite actual model prediction')
    result={'frames':frames,'video_info':info,'resource_fingerprint':fingerprint,
      'parameters':{'static_image_mode':False,'max_num_hands':1,'model_complexity':1,
        'min_detection_confidence':.5,'min_tracking_confidence':.5,'graph_reset_per_video':True,
        'input_PTS_passed_to_graph':False,'graph_simulated_step_microseconds':33333,
        'profile':'existing_offline_stage1_not_browser_prod_detector'},
      'versions':{n:importlib.metadata.version(n) for n in ('mediapipe','opencv-contrib-python','numpy','protobuf')},
      'timing':{'started_utc_epoch_ns':utc,'ended_utc_epoch_ns':time.time_ns(),
        'import_and_resources_wall_ns':import_wall,'import_and_resources_own_cpu_ns':import_cpu,
        'batch_extract_wall_ns':batch_wall,'batch_extract_own_cpu_ns':batch_cpu,
        'worker_validated_wall_ns':time.perf_counter_ns()-wall,'worker_own_cpu_ns':time.process_time_ns()-cpu,
        'scope':'after request validation through runtime/resources, decoder+Hands setup/process/close and checks; JSON store/Python startup excluded'},
      'input_scope':'video pixels only; request contains no native/reference coordinates','gpu_used':False,
      'stage_profile_collected':stage_profile_output is not None,
      'world_prediction_scope':'raw model output only; no metric groundtruth/depth evaluation'}
    with output.open('xb') as stream:stream.write(canonical(result))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('request','output','worker-root'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--stage-profile-output',type=Path)
    a=p.parse_args();execute(a.request,a.output,a.worker_root)
