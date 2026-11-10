"""Export original frames and empty independent-rater forms without model hints."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import cv2

from g4_lab.actual import LANDMARK_NAMES


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pair-root',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();out=args.output.resolve()
    if (out.exists() or 'private_artifacts' not in out.parts
            or any((parent/'.git').exists() for parent in out.parents)):
        p.error('New private output outside repositories required')
    pair=json.loads((args.pair_root/'pair.private.json').read_text(encoding='utf-8'))
    source=args.pair_root/'unmasked.private.mkv'
    if hashlib.sha256(source.read_bytes()).hexdigest()!=pair['conditions']['unmasked']['sha256']:
        raise ValueError('Final unmasked bytes changed')
    chosen=sorted({round(i*(pair['frames']-1)/4) for i in range(5)})
    out.mkdir(parents=True);cap=cv2.VideoCapture(str(source));rows=[]
    try:
        for index in range(pair['frames']):
            ok,frame=cap.read()
            if not ok:raise ValueError('Missing original frame')
            if index in chosen:
                ok,encoded=cv2.imencode('.png',frame)
                if not ok:raise ValueError('PNG encode failed')
                name=f'frame_{index:03}.private.png';(out/name).write_bytes(encoded.tobytes())
                rows.append({'image':name,'frame_index':index,'time_seconds':index/pair['fps'],
                             'width':pair['width'],'height':pair['height'],
                             'landmarks':[{'name':name,'x_pixels':None,'y_pixels':None,
                                           'visibility':'UNANNOTATED','reason':None}
                                          for name in LANDMARK_NAMES]})
    finally:cap.release()
    for rater in [1,2]:
        form={'status':'EMPTY_NOT_HUMAN_ANNOTATED','rater_code':None,
              'coordinate_system':'original image pixels, origin top left; no mirroring',
              'visibility_values':['visible','not_visible','uncertain'],
              'instruction':'Mark visible points independently; leave unobservable coordinates null. No depth judgment.',
              'frames':copy.deepcopy(rows)}
        (out/f'rater_{rater}.private.json').write_text(json.dumps(form,indent=2)+'\n',encoding='utf-8')
    manifest={'frames':chosen,'images':len(rows),'raters_planned':2,'filled_points':0,
              'release_allowed':False,'sampling':'fixed quartile frame indices before annotations',
              'limitations':['One known source, not holdout.',
                             'No model coordinates supplied; actual independent human annotation pending.',
                             'Original visibility is not visibility under each mask.']}
    (out/'manifest.private.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'images':len(rows),'empty_rater_forms':2,'filled_points':0}))


if __name__=='__main__':main()
