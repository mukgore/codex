"""Synthetic interfaces around the owned legacy function, never a model run."""
import argparse
import ast
import json
import math
from pathlib import Path
from types import ModuleType, SimpleNamespace as N

from analysis.runtime_benchmark.stage_profile import Trace, JsonlSink, profile_stage1, rebuild_summary, recover_events
from validation_v03.session_artifacts import _private, canonical

CASES = ('complete', 'process_error', 'decode_open_error', 'rgb_error', 'close_error')


def fixture_module(worker_root, case):
    if case not in CASES: raise ValueError('Known synthetic case required')
    state = {'decoded_n': 0, 'process_attempts_n': 0, 'release_n': 0, 'close_n': 0}
    class Capture:
        def isOpened(self): return case != 'decode_open_error'
        def get(self, key):
            return {1: 64, 2: 48, 3: 8., 4: 2, 5: max(state['decoded_n']-1, 0)*125.}[key]
        def read(self):
            if state['decoded_n'] == 2: return False, None
            index = state['decoded_n']; state['decoded_n'] += 1
            return True, index
        def release(self): state['release_n'] += 1
    class Hands:
        def __init__(self, **kwargs): pass
        def process(self, rgb):
            state['process_attempts_n'] += 1
            if case == 'process_error' and state['process_attempts_n'] == 2:
                raise RuntimeError('synthetic process failure')
            points = [N(x=.1+i/100, y=.2, z=-.01) for i in range(21)]
            return N(multi_hand_landmarks=[N(landmark=points)] if rgb == 0 else None,
                     multi_hand_world_landmarks=[N(landmark=points)] if rgb == 0 else None,
                     multi_handedness=[N(classification=[N(score=.9, label='Right')])])
        def close(self):
            state['close_n'] += 1
            if case == 'close_error': raise RuntimeError('synthetic close failure')
    def cvt(frame, code):
        if case == 'rgb_error': raise RuntimeError('synthetic RGB conversion failure')
        return frame
    module = ModuleType('synthetic_owned_stage1')
    module.cv2 = N(VideoCapture=lambda path: Capture(), cvtColor=cvt, COLOR_BGR2RGB=42,
                   CAP_PROP_FRAME_WIDTH=1, CAP_PROP_FRAME_HEIGHT=2, CAP_PROP_FPS=3,
                   CAP_PROP_FRAME_COUNT=4, CAP_PROP_POS_MSEC=5)
    module.mp = N(solutions=N(hands=N(Hands=Hands))); module.math = math
    module.LANDMARK_NAMES = [f'P{i}' for i in range(21)]
    source = Path(worker_root)/'dataset_pipeline/stage1_extract.py'
    tree = ast.parse(source.read_text(encoding='utf-8-sig'))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == '_extract_landmarks_native']
    if len(functions) != 1 or functions[0].decorator_list:
        raise ValueError('Explicit undecorated owned native extractor required')
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), 'exec'), module.__dict__)
    return module, state


def invoke(module):
    try: return module._extract_landmarks_native('synthetic_input', .5), None
    except Exception as error: return None, type(error).__name__


def run(worker_root, output):
    output = _private(output)
    if output.exists(): raise FileExistsError('Fresh fixture output required')
    output.mkdir(); rows = []
    for case in CASES:
        baseline, baseline_state = fixture_module(worker_root, case)
        expected, expected_error = invoke(baseline)
        module, state = fixture_module(worker_root, case); original_cv, original_mp = module.cv2, module.mp
        sink = JsonlSink(output/(case+'.trace.private.jsonl'))
        trace = Trace(sink=sink, workload_role='synthetic_instrumentation_fixture_not_mediapipe')
        try:
            try:
                with profile_stage1(module, trace):
                    value = module._extract_landmarks_native('synthetic_input', .5)
                error = None
            except Exception as caught:
                value, error = None, type(caught).__name__
        finally: sink.close()
        if (value != expected or error != expected_error or state != baseline_state or
                module.cv2 is not original_cv or module.mp is not original_mp):
            raise ValueError('Instrumentation changed owned extraction semantics')
        summary = trace.summary(); raw = (output/(case+'.trace.private.jsonl')).read_bytes()
        if rebuild_summary(raw) != summary:
            raise ValueError('Persisted trace does not regenerate complete accounting')
        if summary['clock_role'] != 'actual_process_monotonic' or summary['measurement_metadata_errors_n']:
            raise ValueError('Fixture measurement integrity failed')
        (output/(case+'.summary.private.json')).write_bytes(canonical(summary))
        rows.append({'case': case, 'legacy_exception_type': error, 'semantics_match': True,
                     'namespace_restored': True, 'state': state, 'profile_status': summary['status'],
                     'profile_recovery_status': recover_events(raw)['state'],
                     'profile_window_wall_ns': summary['profile_window_wall_ns'],
                     'profile_window_own_cpu_ns': summary['profile_window_own_cpu_ns'],
                     'actual_model_executed': False})
    result = {'scope': 'synthetic_instrumentation_fixture_only', 'cases_n': len(rows), 'cases': rows,
              'actual_models_executed_n': 0, 'actual_model_stage_times_measured': False,
              'past_model_runs_repeated_n': 0, 'new_videos_n': 0, 'new_human_trials_n': 0,
              'profile_raw_summary_roundtrip_all': True, 'release_allowed': False,
              'limitations': ['Actual monotonic clocks timed synthetic interfaces, not MediaPipe/HaMeR performance.',
                              'Legacy source definition executed with synthetic dependencies, not its runtime import/resources.',
                              'No cold/warm, GPU, live-camera or authentication latency validation.']}
    (output/'summary.json').write_bytes(canonical(result)); return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker-root', type=Path, required=True); parser.add_argument('--output', type=Path, required=True)
    result = run(**vars(parser.parse_args()))
    print(json.dumps({'fixture_cases_n': result['cases_n'], 'actual_models_executed_n': 0}))
