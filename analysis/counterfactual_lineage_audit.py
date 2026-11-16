"""Actual file/geometry equivalence and synthetic split checks for saved cases.

No new model/video generation, human answers, independent task count or entropy
claim. Hash buckets are verified by exact payload bytes and kept private.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from analysis.runtime_benchmark.mano_author_surface_audit import bound
from validation_v03.execution_record import verify
from validation_v03.lineage_manifest import audit
from validation_v03.session_artifacts import canonical,_private

FAMILY='F_CURRENT_MANO_MIDDLE_ONLY_ENGINEERING_DEVELOPMENT'


def execute(source,source_record,native,native_record,display,display_record,guarded,guarded_record,output):
    bindings=[bound(root,record) for root,record in ((source,source_record),(native,native_record),
                                                   (display,display_record),(guarded,guarded_record))]
    source,source_record,_=bindings[0];native,native_record,_=bindings[1]
    display,display_record,_=bindings[2];guarded,guarded_record,_=bindings[3]
    output=_private(output)
    if output.exists() or any(output.is_relative_to(p) or p.is_relative_to(output) for root,record,_ in bindings for p in (root,record)):
        raise ValueError('Fresh output outside immutable source/evidence roots required')
    ns=json.loads((native/'summary.json').read_text());ds=json.loads((display/'summary.json').read_text())
    gs=json.loads((guarded/'summary.json').read_text())
    if ns['cases_n']!=32 or ds['cases_n']!=64 or ds['H264_videos_n']!=64 or ds['release_allowed'] is not False:
        raise ValueError('Complete quarantined32-native/64-display recorded experiment required')
    output.mkdir();start=time.perf_counter_ns();cpu=time.process_time_ns();utc=time.time_ns()
    entries=[];source_ids={};native_ids={};baseline_ids={};native_payloads={};native_keys={};buckets={}
    def entry(sid,path,parents):
        entries.append({'source_id':sid,'path':str(path.resolve(strict=True)),'parent_ids':parents,
            'family_ids':[FAMILY],'capture_ids':[],'lineage_status':'derived' if parents else 'root_of_supplied_material',
            'exposure':'used_in_development'})
    parents=list(dict.fromkeys(c['parent_case'] for c in ns['cases']))
    for i,parent in enumerate(parents):
        sid=f'P{i:02d}';source_ids[parent]=sid
        entry(sid,source/parent/'native_output.private.npz',[])
    for i,parent in enumerate(c for c in gs['cases'] if c['H264_rendition_created']):
        sid=f'B{i:02d}';baseline_ids[(parent['case'],parent['view'])]=sid
        paths=list((guarded/parent['directory_id']).glob('renditions/*/video.mp4'))
        if len(paths)!=1:raise ValueError('Unique actual baseline H264 file required')
        entry(sid,paths[0],[source_ids[parent['case']]])
    for i,case in enumerate(ns['cases']):
        sid=f'N{i:02d}';native_ids[case['case_id']]=sid
        path=native/case['case_id']/'native_output.private.npz'
        with np.load(path,allow_pickle=False) as data:
            v=data['vertices'];j=data['canonical_joints'];t=data['times_seconds']
            if v.shape!=(25,778,3) or j.shape!=(25,21,3) or t.shape!=(25,) or not all(np.isfinite(x).all() for x in (v,j,t)):
                raise ValueError('Complete finite actual native arrays required')
            payload=v.tobytes()+j.tobytes()+t.tobytes()
        key=hashlib.sha256(payload).hexdigest()
        if key in native_payloads and native_payloads[key]!=payload:raise ValueError('Native hash bucket not exact bytes')
        native_payloads.setdefault(key,payload);native_keys[case['case_id']]=key
        entry(sid,path,[source_ids[case['parent_case']]])
    private_rows=[]
    for i,case in enumerate(ds['cases']):
        paths=list((display/case['directory_id']).glob('renditions/*/video.mp4'))
        if not case['H264_created'] or len(paths)!=1:raise ValueError('All actual64 final renditions required')
        path=paths[0];payload=path.read_bytes();key=hashlib.sha256(payload).hexdigest();sid=f'V{i:02d}'
        bucket=buckets.setdefault(key,{'payload':payload,'members':[]})
        if bucket['payload']!=payload:raise ValueError('Video hash bucket not exact bytes')
        member={'source_id':sid,'case_id':case['case_id'],'parent_case':case['parent_case'],'hand':case['hand'],
                'view':case['view'],'delta_degrees':case['delta_degrees'],'native_geometry_time_key':native_keys[case['case_id']]}
        bucket['members'].append(member)
        entry(sid,path,[native_ids[case['case_id']],baseline_ids[(case['parent_case'],case['view'])]])
        private_rows.append({'source_id':sid,'video_sha256':key,'native_geometry_time_sha256':native_keys[case['case_id']]})
    groups=[];private_groups=[]
    for index,(key,bucket) in enumerate(buckets.items()):
        members=bucket['members'];geometry=set(m['native_geometry_time_key'] for m in members)
        group={'group_id':f'E{index+1:02d}','H264_files_n':len(members),'distinct_native_geometry_time_n':len(geometry),
            'multiple_model_references_for_exact_file':len(geometry)>1,
            'members':[{k:v for k,v in m.items() if k!='native_geometry_time_key'} for m in members],
            'human_acceptable_answer_set_defined':False}
        groups.append(group);private_groups.append({'group_id':group['group_id'],'video_sha256':key,
            'native_geometry_time_sha256s':sorted(geometry)})
    packet={'schema_version':1,'data_scope':'real_files_synthetic_allocation','source_origin':'generated_3d',
        'require_unexposed_test':True,'sources':entries,
        'allocations':[{'allocation_id':'ALL_DIAGNOSTIC','split':'diagnostic','source_ids':[e['source_id'] for e in entries],
                        'participant_ids':[],'capture_ids':[]}]}
    diagnostic=audit(packet,base=output)
    if diagnostic['summary']['declared_constraint_findings']!={'MISSING_INDEPENDENT_PARTITIONS':1}:
        raise ValueError('Diagnostic-only file/declared-family inventory has unexpected findings')
    # Intentionally invalid metadata allocation: use three final-file aliases
    # with different actual native geometry as development/validation/test.
    selected=next(b for b in buckets.values() if len({m['native_geometry_time_key'] for m in b['members']})>=3)
    chosen=[];seen=set()
    for m in selected['members']:
        if m['native_geometry_time_key'] not in seen:
            chosen.append(m);seen.add(m['native_geometry_time_key'])
        if len(chosen)==3:break
    bad={**packet,'allocations':[{'allocation_id':'SYNTHETIC_'+split,'split':split,'source_ids':[m['source_id']],
        'participant_ids':[],'capture_ids':[]} for split,m in zip(('development','validation','test'),chosen)]}
    counterexample=audit(bad,base=output)
    final_key=hashlib.sha256(selected['payload']).hexdigest()
    specific_final_alias_detected=any(f['code']=='CROSS_SPLIT_BYTE_IDENTITY' and final_key in f['group_values']
                                      for f in counterexample['private_findings'])
    if not specific_final_alias_detected:raise ValueError('Existing lineage checker failed to detect actual final-video alias leakage')
    (output/'diagnostic_packet.private.json').write_bytes(canonical(packet))
    (output/'invalid_partition_packet.private.json').write_bytes(canonical(bad))
    (output/'lineage_details.private.json').write_bytes(canonical({
        'diagnostic':{k:v for k,v in diagnostic.items() if k!='allocations'},
        'invalid_partition':{k:v for k,v in counterexample.items() if k!='allocations'}}))
    (output/'file_geometry_groups.private.json').write_bytes(canonical({'files':private_rows,'groups':private_groups}))
    summary={'version':'actual_counterfactual_file_geometry_lineage_v1','groups':groups,'source_entries_n':len(entries),
        'native_coordinate_sequences_n':32,'native_geometry_time_unique_n':len(native_payloads),
        'H264_files_n':64,'H264_exact_byte_groups_n':len(groups),
        'H264_groups_with_multiple_model_references_n':sum(g['multiple_model_references_for_exact_file'] for g in groups),
        'conservative_current_development_families_n':1,
        'diagnostic_inventory_findings':diagnostic['summary']['declared_constraint_findings'],
        'synthetic_invalid_partition_findings':counterexample['summary']['declared_constraint_findings'],
        'specific_final_H264_alias_cross_split_detected':specific_final_alias_detected,
        'allocation_is_real_human_or_model_evaluation':False,'new_independent_trials_n':0,
        'new_model_inference':False,'new_video_created':False,'human_acceptable_answers_defined':False,
        'scope':'exact file/geometry inventory and declared lineage only; roots bound the supplied recorded material, not independent origin',
        'family_definition':'conservative same procedural middle-only development family; no new family from seed, policy, delta or view labels',
        'started_utc_epoch_ns':utc,'ended_utc_epoch_ns':time.time_ns(),'audit_wall_ns':time.perf_counter_ns()-start,
        'audit_own_process_cpu_ns':time.process_time_ns()-cpu,'accepted_into_pool_n':0,'release_allowed':False}
    (output/'summary.json').write_bytes(canonical(summary))
    for root,record,before in bindings:
        if verify(record)!=before:raise ValueError('Source evidence changed during inventory')
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','source-record','native','native-record','display','display-record','guarded','guarded-record','output'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();result=execute(a.source,a.source_record,a.native,a.native_record,a.display,a.display_record,a.guarded,a.guarded_record,a.output)
    print(json.dumps({k:v for k,v in result.items() if k!='groups'}))
