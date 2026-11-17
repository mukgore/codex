import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from analysis.runtime_benchmark.stage_profile import Trace, profile_stage1, recover_events, rebuild_summary
from analysis.runtime_benchmark.stage_profile_fixture import CASES, fixture_module, invoke
from analysis.runtime_benchmark import mediapipe_video_worker as video_worker

WORKER = Path(__file__).resolve().parents[2]/'handcaptcha-ui-20261113'
OWNED_SOURCE_AVAILABLE = (WORKER/'dataset_pipeline/stage1_extract.py').is_file()
requires_owned_source = unittest.skipUnless(OWNED_SOURCE_AVAILABLE, 'Owned sibling source is not configured; no clone/download is performed')


def raw(events): return b''.join(json.dumps(e).encode()+b'\n' for e in events)


class Clock:
    def __init__(self): self.wall = 0; self.cpu = 0
    def __call__(self): return self.wall, self.cpu
    def advance(self, wall, cpu): self.wall += wall; self.cpu += cpu


class StageProfileTests(unittest.TestCase):
    def test_worker_cli_passes_profile_option_and_preserves_default(self):
        base = ['--request', 'request.json', '--output', 'prediction.json', '--worker-root', 'owned_source']
        with patch.object(video_worker, 'execute') as execute:
            video_worker.main(base+['--stage-profile-output', 'new_profile'])
            execute.assert_called_once_with(Path('request.json'), Path('prediction.json'), Path('owned_source'), Path('new_profile'))
        with patch.object(video_worker, 'execute') as execute:
            video_worker.main(base)
            execute.assert_called_once_with(Path('request.json'), Path('prediction.json'), Path('owned_source'), None)

    def test_existing_or_unrelated_profile_destination_rejected_before_runtime_import(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); request = root/'request.json'
            request.write_text(json.dumps({'video_path': 'not_opened', 'confidence': .5, 'expected_resource_fingerprint': 'fixture'}))
            existing = root/'existing_profile'; existing.mkdir()
            for profile in (existing, root/'other_parent'/'profile'):
                with self.assertRaises(ValueError):
                    video_worker.execute(request, root/'prediction.json', root/'not_imported', profile)
            self.assertEqual(list(existing.iterdir()), [])
            self.assertFalse((root/'prediction.json').exists())

    def test_call_excludes_durable_io_and_gaps_partition_both_clocks(self):
        clock = Clock(); trace = Trace(sink=lambda e: clock.advance(5, 2), clock=clock)
        trace.start()
        trace.call('hands_process', lambda: clock.advance(7, 3))
        trace.finish('COMPLETED')
        result = trace.summary()
        self.assertEqual(result['phases']['hands_process']['wall_ns'], 7)
        self.assertEqual(result['phases']['hands_process']['own_cpu_ns'], 3)
        self.assertEqual(result['profile_window_wall_ns'], 22)
        self.assertEqual(result['profile_window_own_cpu_ns'], 9)
        self.assertEqual(result['clock_role'], 'injected_fixture')
        self.assertEqual(rebuild_summary(raw(trace.events)), result)

    @requires_owned_source
    def test_owned_legacy_results_errors_and_cleanup_are_unchanged(self):
        for case in CASES:
            baseline, before = fixture_module(WORKER, case); expected, expected_error = invoke(baseline)
            module, after = fixture_module(WORKER, case); cv, mp = module.cv2, module.mp
            trace = Trace()
            try:
                with profile_stage1(module, trace): value = module._extract_landmarks_native('synthetic_input', .5)
                error = None
            except Exception as e: value, error = None, type(e).__name__
            self.assertEqual((value, error, after), (expected, expected_error, before), case)
            self.assertIs(module.cv2, cv); self.assertIs(module.mp, mp)
            self.assertEqual(rebuild_summary(raw(trace.events)), trace.summary())

    @requires_owned_source
    def test_eof_read_is_counted_separately_from_model_frames(self):
        module, state = fixture_module(WORKER, 'complete'); trace = Trace()
        with profile_stage1(module, trace): frames, info = module._extract_landmarks_native('synthetic_input', .5)
        result = trace.summary()
        self.assertEqual(len(frames), 2)
        self.assertEqual(result['phases']['decoder_read']['calls_or_gaps_n'], 3)
        self.assertEqual(result['phases']['hands_process']['calls_or_gaps_n'], 2)
        reads = [e for e in trace.events if e['kind']=='call_finished' and e['phase']=='decoder_read']
        self.assertEqual([e['read_success'] for e in reads], [True, True, False])

    @requires_owned_source
    def test_nested_and_invalid_namespace_cannot_leak_lock_or_mutation(self):
        with self.assertRaises(AttributeError):
            with profile_stage1(SimpleNamespace(), Trace()): pass
        module, state = fixture_module(WORKER, 'complete'); cv, mp = module.cv2, module.mp
        with profile_stage1(module, Trace()):
            with self.assertRaises(RuntimeError):
                with profile_stage1(module, Trace()): pass
        self.assertIs(module.cv2, cv); self.assertIs(module.mp, mp)
        trace = Trace()
        with profile_stage1(module, trace): module._extract_landmarks_native('synthetic_input', .5)
        self.assertEqual(trace.summary()['status'], 'COMPLETED')

    def test_incomplete_and_truncated_traces_never_fabricate_duration(self):
        trace = Trace(clock=Clock()); trace.start()
        events = trace.events+[{'kind':'call_started','call_id':0,'phase':'hands_process'}]
        result = recover_events(raw(events))
        self.assertEqual(result['state'], 'INCOMPLETE'); self.assertEqual(result['unknown_outcome_calls_n'], 1)
        self.assertIsNone(result['unknown_call_durations'])
        self.assertEqual(recover_events(raw(events)+b'{')['state'], 'TRUNCATED')
        self.assertEqual(recover_events(b'')['state'], 'LOG_LOST')
        with self.assertRaises(ValueError): rebuild_summary(raw(events))

    def test_corrupt_phase_and_clock_boundaries_are_rejected(self):
        clock = Clock(); trace = Trace(clock=clock); trace.start()
        trace.call('hands_process', lambda: clock.advance(3, 1)); trace.finish('COMPLETED')
        changed = copy.deepcopy(trace.events)
        end = next(e for e in changed if e['kind']=='call_finished'); end['phase'] = 'decoder_read'
        with self.assertRaises(ValueError): recover_events(raw(changed))
        changed = copy.deepcopy(trace.events)
        end = next(e for e in changed if e['kind']=='call_finished'); end['wall_ns'] += 1
        with self.assertRaises(ValueError): rebuild_summary(raw(changed))
        with self.assertRaises(ValueError): recover_events(raw(trace.events)+raw([trace.events[-1]]))

    def test_cpu_may_exceed_wall_and_clock_regression_is_not_clamped(self):
        clock = Clock(); trace = Trace(clock=clock); trace.start()
        trace.call('hands_process', lambda: clock.advance(3, 8)); trace.finish('COMPLETED')
        self.assertEqual(trace.summary()['profile_window_own_cpu_ns'], 8)
        clock = Clock(); trace = Trace(clock=clock); trace.start()
        with self.assertRaises(ValueError): trace.call('hands_process', lambda: clock.advance(-1, 0))

    @requires_owned_source
    def test_keyboard_interrupt_restores_namespaces_and_records_abort(self):
        module, state = fixture_module(WORKER, 'complete'); cv, mp = module.cv2, module.mp; trace = Trace()
        with self.assertRaises(KeyboardInterrupt):
            with profile_stage1(module, trace): raise KeyboardInterrupt()
        self.assertIs(module.cv2, cv); self.assertIs(module.mp, mp)
        self.assertEqual(trace.summary()['status'], 'ABORTED')
        self.assertEqual(recover_events(raw(trace.events))['state'], 'ABORTED')


if __name__ == '__main__': unittest.main()
