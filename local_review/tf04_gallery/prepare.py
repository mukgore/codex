"""Prepare private viewing metadata/copies; never generate model poses or render."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import time

from validation_v03.execution_record import verify


def digest(path):
    result=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):result.update(block)
    return result.hexdigest()


def probe(tool,path):
    return json.loads(subprocess.check_output([str(tool),'-v','error','-select_streams','v:0',
        '-show_entries','stream=codec_name,codec_tag_string,pix_fmt,width,height,r_frame_rate,nb_frames',
        '-show_entries','format=format_name,duration','-of','json',str(path)]))


def prepare(source,record,output,ffmpeg,ffprobe,ui_url):
    source,record,output,ffmpeg,ffprobe=map(lambda p:Path(p).resolve(),(source,record,output,ffmpeg,ffprobe))
    if (output.exists() or 'private_artifacts' not in output.parts
            or any(output.is_relative_to(root) or root.is_relative_to(output) for root in (source,record))
            or any((parent/'.git').exists() for parent in output.parents)):
        raise ValueError('Fresh separate private viewer directory required')
    before=verify(record)
    receipt=json.loads((record/'receipt.private.json').read_text())
    if before['state']!='EXITED_ZERO' or receipt['artifact_roots']!=[str(source)]:
        raise ValueError('Verified exact display record/source required')
    summary=json.loads((source/'summary.json').read_text())
    kinds=Counter(m['kind'] for m in summary['media'])
    # Names are taken from the saved producer metadata, not inferred from extension.
    if sorted(kinds.values())!=[8,8,32] or len(summary['cases'])!=32:
        raise ValueError('Exact 32/8/8 completed media scope required')
    output.mkdir();(output/'viewing_mp4').mkdir()
    clips=[];conversions=[]
    for case in summary['cases']:
        directory=source/case['directory_id']
        records=[m for m in summary['media'] if (m['case'],m['view'])==(case['case'],case['view'])]
        for media in records:
            if 'unmasked' in media['kind'].lower():
                kind='source';original=directory/'source.private.avi'
            elif 'candidate' in media['kind'].lower():
                kind='candidate';paths=list((directory/'candidates').rglob('masked.mp4'))
                if len(paths)!=1:raise ValueError('One recorded candidate required')
                original=paths[0]
            elif '264' in media['kind']:
                kind='final';paths=list((directory/'renditions').rglob('video.mp4'))
                if len(paths)!=1:raise ValueError('One recorded final required')
                original=paths[0]
            else:raise ValueError('Unknown saved media kind: '+media['kind'])
            metadata=probe(ffprobe,original);stream=metadata['streams'][0]
            original_hash=digest(original)
            if original.stat().st_size!=media['video_bytes']:raise ValueError('Saved media byte count differs')
            identity=case['directory_id']+'_'+kind
            compatible=(stream['codec_name']=='h264' and stream['pix_fmt']=='yuv420p' and original.suffix=='.mp4')
            playable=original
            if not compatible:
                playable=output/'viewing_mp4'/(identity+'.mp4')
                command=[str(ffmpeg),'-nostdin','-hide_banner','-loglevel','error','-n','-i',str(original),
                    '-map','0:v:0','-an','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p',
                    '-fps_mode','passthrough','-movflags','+faststart',str(playable)]
                started=time.time_ns();run=subprocess.run(command,capture_output=True,timeout=60)
                conversion=dict(id=identity,command=command,started_utc_epoch_ns=started,
                    ended_utc_epoch_ns=time.time_ns(),exit_code=run.returncode,stderr=run.stderr.decode('utf-8','replace'))
                conversions.append(conversion)
                (output/'conversion_log.private.json').write_text(json.dumps(conversions,indent=2),encoding='utf-8')
                run.check_returncode()
            viewed=probe(ffprobe,playable);target=viewed['streams'][0]
            if (any(target[k]!=stream[k] for k in ('width','height','r_frame_rate','nb_frames'))
                    or viewed['format']['duration']!=metadata['format']['duration']):
                raise ValueError('Viewing conversion changed dimensions/frame count/rate/duration')
            clips.append(dict(id=identity,kind=kind,arm=case['arm'],hand=case['hand'],seed=case['seed'],
                view=case['view'],directory_id=case['directory_id'],case=case['case'],
                original_path=str(original),original_relative=original.relative_to(source).as_posix(),
                original_sha256=original_hash,playable_path=str(playable),playable_sha256=digest(playable),
                converted_for_viewing=not compatible,codec=stream['codec_name'],playback_codec=target['codec_name'],
                width=stream['width'],height=stream['height'],fps=media['fps'],frames_n=media['frames_n'],
                duration=float(metadata['format']['duration']),original_bytes=original.stat().st_size,
                preview_path=str(directory/'source_preview.private.png'),
                generated_ready_seconds=media['timing']['video_ready_wall_ns']/1e9,
                generated_validated_seconds=media['timing']['validated_pipeline_wall_ns']/1e9,
                surface_interval_feasible=case['surface_interval_feasible'],
                model_surface_eligible=case['upstream_model_surface_eligible'],release_allowed=False))
            if len(clips)%8==0:print(f'Checked/viewable clips {len(clips)}/48',flush=True)
    if Counter(c['kind'] for c in clips)!=Counter(source=32,candidate=8,final=8):
        raise ValueError('Media classification mismatch')
    if any(digest(Path(c['original_path']))!=c['original_sha256'] for c in clips) or verify(record)!=before:
        raise ValueError('Original media or experiment evidence changed')
    manifest=dict(scope='private_local_viewer_not_new_generation_or_experiment',source_root=str(source),
        record_root=str(record),record_verification=before,original_experiment_artifacts_n=361,
        original_videos_n=48,counts=dict(source=32,candidate=8,final=8),clips=clips,
        viewing_copies_n=len(conversions),original_h264_reused_n=48-len(conversions),
        source_record_unchanged=True,ui_url=ui_url,
        copy_note='Viewing H.264 copies are lossy, retain 25 frames/8fps/512x420/3.125s; never analysis inputs.',
        new_generation_or_rendering=False)
    (output/'manifest.private.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:manifest[k] for k in ('counts','viewing_copies_n','original_h264_reused_n','source_record_unchanged')}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('source','record','output','ffmpeg','ffprobe','ui-url'):parser.add_argument('--'+name,required=True)
    prepare(**vars(parser.parse_args()))
