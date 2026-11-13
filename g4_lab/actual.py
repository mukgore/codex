"""Actual HTML computation adapter, isolated from DOM/network/camera startup."""
from __future__ import annotations
import json
import math
from collections import deque
from pathlib import Path
import queue
import subprocess
import threading
import time
import numpy as np

LANDMARK_NAMES = ['WRIST','THUMB_CMC','THUMB_MCP','THUMB_IP','THUMB_TIP','INDEX_MCP','INDEX_PIP','INDEX_DIP','INDEX_TIP','MIDDLE_MCP','MIDDLE_PIP','MIDDLE_DIP','MIDDLE_TIP','RING_MCP','RING_PIP','RING_DIP','RING_TIP','PINKY_MCP','PINKY_PIP','PINKY_DIP','PINKY_TIP']

class ActualEvaluator:
    def __init__(self, source_root: Path, *, call_timeout=15):
        if type(call_timeout) not in (int,float) or not math.isfinite(call_timeout) or not 0<call_timeout<=60:
            raise ValueError('Evaluator deadline must be finite and at most 60 seconds')
        self.call_timeout=call_timeout;self.failed=False;self.writer=None
        self.source_root = source_root.resolve()
        self.process = subprocess.Popen(['node',str(Path(__file__).with_name('js_bridge.cjs')),str(self.source_root/'hand_captcha_prod.html')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
        self.lock = threading.Lock()
        self.replies=queue.Queue();self.stderr_tail=deque(maxlen=20)
        def read_replies():
            for line in self.process.stdout:self.replies.put(line)
            self.replies.put(None)
        def read_errors():
            for line in self.process.stderr:self.stderr_tail.append(line)
        self.readers=[threading.Thread(target=read_replies,daemon=True),threading.Thread(target=read_errors,daemon=True)]
        for reader in self.readers:reader.start()
        try:
            manifest=json.loads((self.source_root/'pool_manifest.json').read_text(encoding='utf-8'))
            self.clips={clip['clip_id']:clip for clip in manifest['clips']}
            self.sources={}
            for key, clip in self.clips.items():
                path=(self.source_root/clip['landmarks_file']).resolve()
                if not path.is_relative_to(self.source_root): raise ValueError('unsafe source manifest')
                data=json.loads(path.read_text(encoding='utf-8'))
                prepared=self.call({'op':'prepare','data':data})
                info=data['video_info'];raw=[]
                for i,f in enumerate(data['frames']):
                    lm=f.get('landmarks_px') if f.get('detected') else None
                    raw.append({'t_ms':f.get('frame_idx',i)*1000/info['fps'],'lm':[[lm[n]['x']/info['width'],lm[n]['y']/info['height']] for n in LANDMARK_NAMES] if lm else None})
                self.sources[key]={'base':prepared['frames'],'orig_idx':prepared['origIdx'],'fps':info['fps'],'keyframes':prepared['keyframeIndices'],'constants':prepared['constants'],'raw_frames':raw}
        except Exception:
            self.close();raise

    def call(self, request):
        deadline=time.monotonic()+self.call_timeout
        if not self.lock.acquire(timeout=self.call_timeout):
            # A queued caller must not kill the process serving a different call.
            raise TimeoutError('actual evaluator queue timeout')
        try:
            if self.failed or self.process.poll() is not None:
                raise RuntimeError('actual evaluator unavailable')
            payload=json.dumps(request,allow_nan=False,separators=(',',':'))+'\n'
            def remaining():
                value=deadline-time.monotonic()
                if value<=0:raise queue.Empty
                return value
            sent=queue.Queue(maxsize=1)
            def write_request():
                try:
                    self.process.stdin.write(payload);self.process.stdin.flush()
                    sent.put(True)
                except (OSError,ValueError):sent.put(False)
            try:
                remaining()
                self.writer=threading.Thread(target=write_request,daemon=True)
                self.writer.start()
                if not sent.get(timeout=remaining()):
                    self._abort();raise RuntimeError('actual evaluator input pipe failed')
                line=self.replies.get(timeout=remaining())
                if not line:
                    self._abort();raise RuntimeError('actual JS evaluator exited')
                try:
                    reply=json.loads(line)
                    if (not isinstance(reply,dict) or type(reply.get('ok')) is not bool or
                            ('result' not in reply if reply.get('ok') else not isinstance(reply.get('error'),str))):
                        raise ValueError('invalid reply')
                except (ValueError,TypeError,RecursionError):
                    self._abort();raise RuntimeError('actual evaluator protocol failed') from None
                remaining()
            except queue.Empty:
                self._abort()
                raise TimeoutError('actual evaluator call deadline exceeded') from None
            if not reply['ok']:raise ValueError(reply['error'])
            return reply['result']
        finally:self.lock.release()

    def _abort(self):
        # Poison the stream before releasing the lock: late replies cannot serve another call.
        self.failed=True
        if self.process.poll() is None:
            try:self.process.kill()
            except OSError:pass
        try:self.process.wait(timeout=1)
        except subprocess.TimeoutExpired:pass
        if self.writer is not None and self.writer.is_alive():self.writer.join(timeout=1)

    def evaluate(self, key, frames):
        return self.call({'op':'evaluate','base':self.sources[key]['base'],'frames':frames})

    def frames(self,key,array=None):
        source=self.sources[key]
        if array is None:return source['raw_frames']
        indices=source['orig_idx'] if len(array)==len(source['orig_idx']) else range(len(array))
        return [{'t_ms':indices[i]*1000/source['fps'],'lm':None if lm is None else np.asarray(lm).tolist()} for i,lm in enumerate(array)]

    def close(self):
        # Kill before closing stdin: TextIO close may otherwise wait on a blocked writer.
        self._abort()
        if self.process.poll() is None:raise RuntimeError('actual evaluator process did not terminate')
        for reader in self.readers:reader.join(timeout=1)
        for stream in (self.process.stdin,self.process.stdout,self.process.stderr):
            if not stream.closed:
                try:stream.close()
                except OSError:pass

    def __enter__(self): return self
    def __exit__(self,*args): self.close()
