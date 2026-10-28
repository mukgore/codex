"""Actual HTML computation adapter, isolated from DOM/network/camera startup."""
from __future__ import annotations
import json
from collections import deque
from pathlib import Path
import queue
import subprocess
import threading
import numpy as np

LANDMARK_NAMES = ['WRIST','THUMB_CMC','THUMB_MCP','THUMB_IP','THUMB_TIP','INDEX_MCP','INDEX_PIP','INDEX_DIP','INDEX_TIP','MIDDLE_MCP','MIDDLE_PIP','MIDDLE_DIP','MIDDLE_TIP','RING_MCP','RING_PIP','RING_DIP','RING_TIP','PINKY_MCP','PINKY_PIP','PINKY_DIP','PINKY_TIP']

class ActualEvaluator:
    def __init__(self, source_root: Path):
        self.source_root = source_root.resolve()
        self.process = subprocess.Popen(['node',str(Path(__file__).with_name('js_bridge.cjs')),str(self.source_root/'hand_captcha_prod.html')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8')
        self.lock = threading.Lock()
        self.replies=queue.Queue();self.stderr_tail=deque(maxlen=20)
        def read_replies():
            for line in self.process.stdout:self.replies.put(line)
            self.replies.put(None)
        def read_errors():
            for line in self.process.stderr:self.stderr_tail.append(line)
        threading.Thread(target=read_replies,daemon=True).start()
        threading.Thread(target=read_errors,daemon=True).start()
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
        with self.lock:
            self.process.stdin.write(json.dumps(request,allow_nan=False,separators=(',',':'))+'\n')
            self.process.stdin.flush()
            try:line=self.replies.get(timeout=15)
            except queue.Empty:
                self.process.kill();raise TimeoutError('actual evaluator response timeout')
        if not line: raise RuntimeError('actual JS evaluator exited')
        reply=json.loads(line)
        if not reply['ok']: raise ValueError(reply['error'])
        return reply['result']

    def evaluate(self, key, frames):
        return self.call({'op':'evaluate','base':self.sources[key]['base'],'frames':frames})

    def frames(self,key,array=None):
        source=self.sources[key]
        if array is None:return source['raw_frames']
        indices=source['orig_idx'] if len(array)==len(source['orig_idx']) else range(len(array))
        return [{'t_ms':indices[i]*1000/source['fps'],'lm':None if lm is None else np.asarray(lm).tolist()} for i,lm in enumerate(array)]

    def close(self):
        if not self.process.stdin.closed:self.process.stdin.close()
        try:self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:self.process.kill();self.process.wait(timeout=5)

    def __enter__(self): return self
    def __exit__(self,*args): self.close()
