"""Fresh private durable queue recording and independent file verification."""
import hashlib
import json

from .arrival_queue import ArrivalQueue
from .arrival_recovery import recover
from .journal import _private
from .stage_profile import JsonlSink


def _result(raw):
    # JSON normalization makes frame-ID object keys stable on disk/readback.
    return json.loads(json.dumps(dict(raw_sha256=hashlib.sha256(raw).hexdigest(),
                                     raw_bytes_n=len(raw), recovery=recover(raw)), allow_nan=False))


class RecordedQueue:
    def __init__(self, directory, **config):
        self.directory = _private(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        self.sink = JsonlSink(self.directory/'events.private.jsonl')
        self.finished = False
        try:
            self.queue = ArrivalQueue(sink=self.sink, **config)
        except BaseException:
            self.sink.close()
            raise

    def finish_recording(self):
        """Close storage, not the queue. Missing queue terminal stays interrupted."""
        if self.finished:
            raise RuntimeError('Recording already finalized')
        self.sink.close(); self.finished = True
        result = _result((self.directory/'events.private.jsonl').read_bytes())
        with (self.directory/'recovery.private.json').open('x', encoding='utf-8') as stream:
            json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
        if verify_directory(self.directory) != result:
            raise ValueError('Queue raw/recovery readback differs')
        return result


def verify_directory(directory):
    directory = _private(directory)
    actual = _result((directory/'events.private.jsonl').read_bytes())
    saved = json.loads((directory/'recovery.private.json').read_text(encoding='utf-8'))
    if saved != actual:
        raise ValueError('Stored queue raw/recovery/hash differs')
    return actual
