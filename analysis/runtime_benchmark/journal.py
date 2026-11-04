"""Private fsynced runtime journal with explicit crash/corruption recovery.

Times are real monotonic wall times, including logging overhead. This does
not turn a fake-clock evaluator into an online camera measurement.
"""
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import time
import uuid
import zipfile

FINAL = {'COMPLETED', 'TIMED_OUT', 'ERROR', 'ABORTED', 'UNAVAILABLE'}
REPO = Path(__file__).resolve().parents[2]


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf8')


def _private(path):
    path = Path(path).resolve()
    if path.is_relative_to(REPO) or REPO.is_relative_to(path):
        raise ValueError('Runtime evidence belongs outside the repository web/static root')
    return path


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def recover_bytes(raw):
    if not raw:
        return {'status':'LOG_LOST','valid_events':0,'reason':'empty_journal'}
    previous = '0'*64
    records = []
    terminal = None
    elapsed = -1
    outcomes = set()
    active_stage = None
    for index, line in enumerate(raw.splitlines(keepends=True)):
        if not line.endswith(b'\n'):
            return {'status':'LOG_CORRUPT' if terminal else 'INTERRUPTED', 'valid_events':len(records), 'reason':'incomplete_tail'}
        try:
            record = json.loads(line)
            if not isinstance(record,dict) or type(record.get('seq')) is not int or record.get('schema_version') != 1:
                raise ValueError('Invalid journal schema')
            signature = record.pop('sha256')
            if (terminal or record['seq'] != index or record['previous_sha256'] != previous
                    or _sha(_canonical(record)) != signature or type(record['elapsed_ns']) is not int
                    or record['elapsed_ns'] < elapsed or (index == 0 and record['kind'] != 'run_started')):
                raise ValueError('Journal sequence or checksum mismatch')
            if index and record['run_id'] != records[0]['run_id']:
                raise ValueError('Run IDs changed')
            if record['kind'] not in ('run_started','stage_started','stage_finished','frame_completed','frame_dropped','run_finished') or (index and record['kind']=='run_started'):
                raise ValueError('Unexpected event kind')
            if record['kind'] == 'stage_started':
                if active_stage is not None:raise ValueError('Overlapping stages')
                active_stage=record['fields']['stage']
            if record['kind'] == 'stage_finished':
                if active_stage != record['fields']['stage']:raise ValueError('Stage mismatch')
                active_stage=None
            if record['kind'] in ('frame_completed','frame_dropped'):
                frame=record['fields']['frame_index']
                if type(frame) is not int or not 0<=frame<records[0]['fields']['planned_frames'] or frame in outcomes:
                    raise ValueError('Invalid duplicate/missing frame outcome')
                outcomes.add(frame)
            if record['kind'] == 'run_finished':
                terminal = record['fields']['status']
                if terminal not in FINAL:
                    raise ValueError('Invalid terminal status')
                if terminal=='COMPLETED' and (active_stage is not None or len(outcomes)!=records[0]['fields']['planned_frames']):
                    raise ValueError('Incomplete work cannot be COMPLETED')
            previous = signature;elapsed = record['elapsed_ns'];records.append(record)
        except (ValueError, KeyError, TypeError):
            return {'status':'LOG_CORRUPT', 'valid_events':len(records), 'reason':'invalid_record'}
    return {'status':terminal or 'INTERRUPTED', 'valid_events':len(records),
            'elapsed_ns':elapsed if terminal else None,
            'completed_frames':sum(r['kind']=='frame_completed' for r in records),
            'dropped_frames':sum(r['kind']=='frame_dropped' for r in records),
            'reason':None if terminal else 'missing_terminal_event'}


class Journal:
    def __init__(self, directory, manifest, *, clock=time.perf_counter_ns):
        for name in ('condition_id', 'endpoint', 'input_exposure', 'cache_state'):
            if not isinstance(manifest.get(name), str) or not manifest[name].strip():
                raise ValueError('Explicit condition, endpoint, exposure and cache state required')
        if type(manifest.get('planned_frames')) is not int or manifest['planned_frames'] < 0:
            raise ValueError('Explicit nonnegative planned frame count required')
        budget = manifest.get('timeout_seconds')
        if isinstance(budget,bool) or not isinstance(budget,(int,float)) or not math.isfinite(budget) or budget<=0:
            raise ValueError('Explicit finite positive timeout required')
        self.directory = _private(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        payload = _canonical(manifest)
        (self.directory/'manifest.json').write_bytes(payload+b'\n')
        self.clock=clock;self.start=clock();self.last=0;self.seq=0;self.previous='0'*64
        self.run_id=uuid.uuid4().hex;self.closed=False;self.active_stage=None
        self.planned_frames=manifest['planned_frames'];self.outcomes=set()
        self.deadline_ns=int(budget*1e9)
        self.stream=(self.directory/'events.jsonl').open('xb')
        self._append('run_started', {'manifest_sha256':_sha(payload),
                                    'clock':'perf_counter_ns' if clock is time.perf_counter_ns else 'injected_clock_not_runtime_evidence',
                                    'planned_frames':self.planned_frames,
                                    'scope':'wall_time_including_journal_overhead'})

    def _append(self, kind, fields):
        if self.closed:
            raise ValueError('Run already finished')
        elapsed=self.clock()-self.start
        if type(elapsed) is not int or elapsed < self.last:
            raise ValueError('Clock regressed or did not return integer nanoseconds')
        record={'schema_version':1,'run_id':self.run_id,'seq':self.seq,'kind':kind,
                'elapsed_ns':elapsed,'fields':fields,'previous_sha256':self.previous}
        signature=_sha(_canonical(record));record['sha256']=signature
        self.stream.write(_canonical(record)+b'\n');self.stream.flush();os.fsync(self.stream.fileno())
        self.last=elapsed;self.previous=signature;self.seq+=1
        return elapsed

    def check_budget(self):
        if self.clock()-self.start >= self.deadline_ns:
            self.finish('TIMED_OUT')
            raise TimeoutError('Runtime budget exceeded')

    @contextmanager
    def stage(self, name):
        if not isinstance(name,str) or not name.strip() or self.active_stage is not None:
            raise ValueError('Named, nonoverlapping stages required')
        self.check_budget();self.active_stage=name
        start=self._append('stage_started',{'stage':name})
        try:
            yield
            self.check_budget()
            self._append('stage_finished',{'stage':name,'duration_ns':self.clock()-self.start-start})
        except BaseException as error:
            if not self.closed:self.finish('ABORTED' if isinstance(error,KeyboardInterrupt) else 'ERROR', reason=type(error).__name__)
            raise
        finally:
            self.active_stage=None

    def frame_completed(self, index, detected):
        if type(index) is not int or not 0<=index<self.planned_frames or index in self.outcomes or type(detected) is not bool:
            raise ValueError('Explicit frame index and detection outcome required')
        self.check_budget();self._append('frame_completed',{'frame_index':index,'detected':detected})
        self.outcomes.add(index)

    def frame_dropped(self, index, reason):
        if type(index) is not int or not 0<=index<self.planned_frames or index in self.outcomes or not isinstance(reason,str) or not reason or len(reason)>128:
            raise ValueError('Unique planned frame and bounded drop reason required')
        self.check_budget();self._append('frame_dropped',{'frame_index':index,'reason':reason});self.outcomes.add(index)

    def finish(self, status, *, reason=None):
        if status not in FINAL:
            raise ValueError('Explicit terminal status required')
        if reason is not None and (not isinstance(reason,str) or len(reason)>128):
            raise ValueError('Bounded reason code required')
        if status=='COMPLETED':
            self.check_budget()
            if self.active_stage is not None or len(self.outcomes)!=self.planned_frames:
                raise ValueError('Every planned frame needs an explicit outcome before completion')
        self._append('run_finished',{'status':status,'reason':reason})
        self.closed=True;self.stream.close()

    def close_without_terminal(self):
        """Release file resources while preserving an interrupted journal."""
        if not self.stream.closed:self.stream.close()
        self.closed=True


def export_bundle(directory, destination):
    directory=_private(directory);destination=_private(destination)
    if (directory/'events.jsonl').stat().st_size>32*1024*1024:
        raise ValueError('Journal exceeds bundle budget')
    events=(directory/'events.jsonl').read_bytes();manifest=(directory/'manifest.json').read_bytes()
    summary=recover_bytes(events)
    descriptor={'schema_version':1,'manifest_sha256':_sha(manifest),'events_sha256':_sha(events),'recovered':summary}
    with destination.open('xb') as output:
        with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('manifest.json',manifest);archive.writestr('events.jsonl',events)
            archive.writestr('bundle.json',_canonical(descriptor))
    return descriptor


def verify_bundle(path):
    with zipfile.ZipFile(path) as archive:
        if sorted(archive.namelist()) != ['bundle.json','events.jsonl','manifest.json']:
            raise ValueError('Unexpected or duplicate bundle members')
        if sum(x.file_size for x in archive.infolist())>64*1024*1024:
            raise ValueError('Bundle expansion exceeds budget')
        manifest=archive.read('manifest.json');events=archive.read('events.jsonl')
        descriptor=json.loads(archive.read('bundle.json'))
    if _sha(manifest)!=descriptor['manifest_sha256'] or _sha(events)!=descriptor['events_sha256']:
        raise ValueError('Bundle bytes changed')
    first=json.loads(events.splitlines()[0]) if events.splitlines() else None
    if first is not None and first['fields']['manifest_sha256']!=_sha(_canonical(json.loads(manifest))):
        raise ValueError('Journal is not bound to this condition manifest')
    if recover_bytes(events)!=descriptor['recovered']:
        raise ValueError('Recovered result differs from bundle summary')
    return descriptor['recovered']
