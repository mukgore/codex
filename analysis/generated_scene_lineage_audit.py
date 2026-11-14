"""Audit existing recorded surface fixtures; never make independent trials."""
import argparse
import copy
import json
from pathlib import Path
import sys

from validation_v03.execution_record import verify
from validation_v03.generated_scene_manifest import AXES, audit
from validation_v03.run_manifest import read, snapshot_file
from validation_v03.session_artifacts import canonical, decode, _private, _read


def execute(source_root, worker_root, execution_record, output):
    source_root=Path(source_root).resolve(strict=True);worker_root=Path(worker_root).resolve(strict=True)
    execution_record=_private(execution_record);output=_private(output)
    if output.exists():raise FileExistsError('Preserve previous scene audits')
    proof=verify(execution_record)
    receipt=decode(_read(execution_record/'receipt.private.json'))
    if (proof['mode']!='RECORDED_COMMAND_EXECUTION' or proof['state']!='EXITED_ZERO' or
            receipt['artifact_roots']!=[str(source_root)]):
        raise ValueError('Source root must be bound to the specified completed recorded command')
    manifest,_=read(execution_record/'provenance')
    if Path(manifest['repository']).resolve()!=worker_root:raise ValueError('Source record uses a different worker repository')
    # Import only owned procedural code, and require its exact recorded bytes.
    recorded={Path(row['path']).resolve():row for row in manifest['code_files']}
    code_paths=[p for parent in ('dataset_pipeline','experiments/motion_fixture') for p in (worker_root/parent).glob('*.py')]
    for path in code_paths:
        if path.resolve() not in recorded:raise ValueError('Worker source was not part of prior snapshot')
        actual=snapshot_file(path);before=recorded[path.resolve()]
        if any(actual[k]!=before[k] for k in ('bytes','sha256')):raise ValueError('Worker code changed since source execution')
    sys.path.insert(0,str(worker_root))
    from experiments.motion_fixture.grasp_contacts import KINDS, VERSION, records, reflect_depth
    from experiments.motion_fixture.surface_passes import MODES, VERSION as RENDERER
    expected_groups={kind+'_s'+str(seed) for seed in (7,19) for kind in KINDS}
    if {p.name for p in source_root.iterdir() if p.is_dir()}!=expected_groups:
        raise ValueError('Expected recorded four-recipe surface layout required')
    output.mkdir(parents=True,exist_ok=False)
    asset=output/'asset_family_record.private.json'
    asset.write_bytes(canonical({'scope':'self_authored_software_fixture_only_not_legal_certification',
        'learned_weights_used':False,'human_capture':False,'release_allowed':False,
        'family_definitions':{'hand_geometry':'same authored 21-point capsule graph and LENGTHS',
            'object_geometry':'same primitive sphere; radius changes remain within this family',
            'contact_plan':'two authored tip sets, not stable/anatomical grasp proof',
            'trajectory':'same approach/hold/carry/release schedule and authored IK procedure',
            'camera':'same fixed orthographic XY mapping, viewport and scale',
            'renderer':'same surface renderer; flat/lit and object toggle are variants'},
        'source_execution_run_id':receipt['run_id']}))
    packet={'schema_version':1,'data_scope':'real_files_synthetic_allocation','require_unexposed_test':True,
            'separate_axes':list(AXES),'scenes':[],'sources':[],'allocations':[]}
    source_meta={};reference_checks=0;counts={'raw':0,'candidate':0,'h264':0}
    def add(sid,path,scene,parents,stage,seed,control,mode):
        info=snapshot_file(path)
        packet['sources'].append({'source_id':sid,'path':str(path),'scene_id':scene,'parent_ids':parents,
            'lineage_status':'derived' if parents else 'root_of_supplied_material',
            'exposure':'used_in_development','sha256':info['sha256'],
            'variant_parameters':{'depth_control':control,'render_mode':mode,'media_stage':stage}})
        packet['allocations'].append({'allocation_id':sid,'split':'diagnostic','source_ids':[sid],
                                     'participant_ids':[],'capture_ids':[]})
        source_meta[sid]={'seed':seed,'control':control};counts[stage]+=1
    for seed in (7,19):
        for kind in KINDS:
            sid=kind+'_s'+str(seed);group=source_root/sid
            packet['scenes'].append({'scene_id':sid,'origin_type':'generated_3d','generator_version':VERSION,
                'generation_run_id':receipt['run_id'],'seed':seed,
                'parameters':{'kind':kind,'frames':24,'fps':12},
                'family_axes':{'hand_geometry':'authored_capsule_hand_graph_v1','object_geometry':'primitive_sphere_v1',
                    'contact_plan':kind+'_v1','trajectory':'approach_hold_carry_release_authored_ik_v1',
                    'camera':'orthographic_xy_512x420_scale150_v1','renderer':RENDERER},
                'asset_record':{'path':str(asset),'status':'self_authored_fixture'}})
            original=records(kind,seed,24,12)
            sequences={'source':original,'hand_reflection':reflect_depth(original,object_too=False),
                       'joint_reflection':reflect_depth(original,object_too=True)}
            for control,frames in sequences.items():
                case=group/control
                reference=decode(_read(case/'reference.private.json'))
                if reference!={'frames':frames,'source_info':{'width':512,'height':420,'fps':12,'total_frames':24}}:
                    raise ValueError('Actual private geometry does not match declared generator recipe')
                reference_checks+=len(frames)
                for mode in MODES:
                    mode_root=case/mode;row=decode(_read(mode_root/'report.private.json'))
                    if row['mode']!=mode or row['control']!=control or row['release_allowed'] is not False:
                        raise ValueError('Unexpected recorded surface mode/control')
                    raw_id=sid+'/'+control+'/'+mode+'/raw'
                    parents=[] if control=='source' else [sid+'/source/'+mode+'/raw']
                    add(raw_id,mode_root/'source.private.avi',sid,parents,'raw',seed,control,mode)
                    if row['artifact'] is None:
                        if row['rendition'] is not None or control!='hand_reflection':
                            raise ValueError('Unexpected missing or quarantined surface artifact')
                        continue
                    if control=='hand_reflection':raise ValueError('Invalid contact control must not issue a candidate')
                    candidate_id=raw_id+'/masked';candidate=mode_root/'candidates'/row['artifact']['artifact_id']/'masked.mp4'
                    if snapshot_file(candidate)['sha256']!=row['artifact']['output_sha256']:
                        raise ValueError('Candidate/report bytes differ')
                    add(candidate_id,candidate,sid,[raw_id],'candidate',seed,control,mode)
                    rendition=mode_root/'renditions'/row['rendition']['output_sha256']/'video.mp4'
                    if snapshot_file(rendition)['sha256']!=row['rendition']['output_sha256']:
                        raise ValueError('Rendition/report bytes differ')
                    add(candidate_id+'/h264',rendition,sid,[candidate_id],'h264',seed,control,mode)
    results={}
    for name in ('diagnostic_only','seed_only_split_counterexample','depth_variant_split_counterexample'):
        variant=copy.deepcopy(packet)
        for allocation in variant['allocations']:
            meta=source_meta[allocation['source_ids'][0]]
            if name=='seed_only_split_counterexample':allocation['split']='development' if meta['seed']==7 else 'test'
            if name=='depth_variant_split_counterexample':allocation['split']={'source':'development','joint_reflection':'validation','hand_reflection':'test'}[meta['control']]
        manifest_path=output/(name+'.manifest.private.json');manifest_path.write_bytes(canonical(variant))
        result=audit(variant,base=output);results[name]=result['summary']
        (output/(name+'.details.private.json')).write_bytes(canonical({k:v for k,v in result.items() if k not in ('summary','allocations')}))
    if results['seed_only_split_counterexample']['declared_constraints_satisfied'] or results['depth_variant_split_counterexample']['declared_constraints_satisfied']:
        raise ValueError('Synthetic unsafe allocations were not rejected')
    if verify(execution_record)!=proof:raise ValueError('Source execution record changed during scene audit')
    summary={'scope':'existing_recorded_generated_media_lineage_with_synthetic_split_counterexamples',
        'source_execution_record_verified_before_and_after':True,'geometry_frames_recomputed_and_matched':reference_checks,
        'actual_media_files_by_stage':counts,'actual_media_files_n':sum(counts.values()),
        'scene_entries_n':len(packet['scenes']),'unique_declared_families_by_axis':results['diagnostic_only']['unique_declared_families_by_axis'],
        'audits':results,'actual_participant_trials_n':0,'new_model_inference':False,
        'independent_partitions_created':False,'release_allowed':False,
        'limitations':['Existing authored scene media only; split assignments are intentionally synthetic diagnostics.',
            'Same recipe seeds/variants are not new families or independent evaluation data.',
            'Asset/family definitions are scoped engineering records, not rights/anatomical/security validation.']}
    (output/'summary.json').write_bytes(canonical(summary));return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for field in ('source-root','worker-root','execution-record','output'):parser.add_argument('--'+field,type=Path,required=True)
    args=parser.parse_args();print(json.dumps(execute(args.source_root,args.worker_root,args.execution_record,args.output)))
