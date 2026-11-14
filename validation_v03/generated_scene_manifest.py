"""Typed generated-scene families plus file-backed source/split constraints.

Family labels/asset metadata remain caller assertions. Different seeds are
not evidence of held-out object/contact/trajectory/camera/renderer families.
"""
import argparse
from collections import Counter, defaultdict, deque
import hashlib
import json
from pathlib import Path
import re

from validation_v03.lineage_manifest import audit as lineage_audit, SPLITS
from validation_v03.run_manifest import snapshot_file
from validation_v03.session_artifacts import canonical, decode, _private, _read

AXES=('hand_geometry','object_geometry','contact_plan','trajectory','camera','renderer')


def _label(value):
    return isinstance(value,str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,159}',value) is not None


def audit(packet, *, base):
    required={'schema_version','data_scope','require_unexposed_test','separate_axes','scenes','sources','allocations'}
    if not isinstance(packet,dict) or set(packet)!=required or type(packet['schema_version']) is not int or packet['schema_version']!=1:
        raise ValueError('Explicit generated-scene manifest required')
    selected=packet['separate_axes']
    if not isinstance(selected,list) or not selected or len(selected)>len(AXES) or len(set(selected))!=len(selected) or any(a not in AXES for a in selected):
        raise ValueError('Explicit distinct held-out family axes required')
    scenes=packet['scenes'];sources=packet['sources'];base=Path(base).resolve()
    if not isinstance(scenes,list) or not 1<=len(scenes)<=1000 or not isinstance(sources,list) or not 1<=len(sources)<=1000:
        raise ValueError('Bounded nonempty scene/source collections required')
    scene_map={};asset_files={};recipes=defaultdict(list);findings=[]
    fields={'scene_id','origin_type','generator_version','generation_run_id','seed','parameters','family_axes','asset_record'}
    for row in scenes:
        if not isinstance(row,dict) or set(row)!=fields or row['origin_type']!='generated_3d' or any(not _label(row[k]) for k in ('scene_id','generator_version','generation_run_id')) or row['scene_id'] in scene_map:
            raise ValueError('Unique generated scene/version/run identity required')
        if type(row['seed']) is not int or row['seed']<0 or not isinstance(row['parameters'],dict) or not row['parameters']:
            raise ValueError('Explicit seed and nonempty recipe parameters required')
        if len(canonical(row['parameters']))>65536:raise ValueError('Recipe parameter budget exceeded')
        axes=row['family_axes']
        if not isinstance(axes,dict) or set(axes)!=set(AXES) or any(v is not None and not _label(v) for v in axes.values()):
            raise ValueError('All typed family axes must be declared or explicitly unresolved')
        asset=row['asset_record']
        if not isinstance(asset,dict) or set(asset)!={'path','status'} or asset['status'] not in ('self_authored_fixture','external_terms_recorded','unreviewed') or not isinstance(asset['path'],str) or not asset['path']:
            raise ValueError('Explicit local asset/rights record required; no automatic approval')
        path=Path(asset['path']);path=(path if path.is_absolute() else base/path).resolve(strict=True)
        if path not in asset_files:
            if path.stat().st_size>32*1024*1024 or sum(v['bytes'] for v in asset_files.values())+path.stat().st_size>64*1024*1024:
                raise ValueError('Asset record byte budget exceeded')
            asset_files[path]=snapshot_file(path)
        recipe=hashlib.sha256(canonical({k:row[k] for k in ('generator_version','seed','parameters')})).hexdigest()
        recipes[recipe].append(row['scene_id']);scene_map[row['scene_id']]={**row,'recipe_id':recipe}
    records={};degree={};children=defaultdict(list)
    source_fields={'source_id','path','scene_id','parent_ids','lineage_status','exposure','variant_parameters'}
    for row in sources:
        if not isinstance(row,dict) or not source_fields.issubset(row) or set(row)-source_fields-{'sha256'} or not _label(row['source_id']) or row['source_id'] in records or row['scene_id'] not in scene_map:
            raise ValueError('Unique source linked to an explicit scene required')
        if not isinstance(row['variant_parameters'],dict) or not row['variant_parameters'] or len(canonical(row['variant_parameters']))>32768:
            raise ValueError('Explicit bounded source variant parameters required')
        parents=row['parent_ids']
        if not isinstance(parents,list) or len(parents)>1000 or not all(_label(p) for p in parents) or len(set(parents))!=len(parents):
            raise ValueError('Unique bounded source parent identities required')
        records[row['source_id']]=row;degree[row['source_id']]=len(parents)
    if sum(degree.values())>20000:raise ValueError('Source parent budget exceeded')
    for sid,row in records.items():
        for parent in row['parent_ids']:
            if parent not in records:raise ValueError('Missing generated source parent')
            children[parent].append(sid)
    queue=deque(sid for sid,n in degree.items() if not n);order=[]
    while queue:
        sid=queue.popleft();order.append(sid)
        for child in children[sid]:
            degree[child]-=1
            if degree[child]==0:queue.append(child)
    if len(order)!=len(records):raise ValueError('Cyclic generated source lineage')
    # Alias closure must be expanded before auto-declaring inherited families.
    # A child of a byte-identical parent otherwise acquires extra families only
    # inside the generic audit and is falsely reported as omitting metadata.
    hashes=defaultdict(set);file_cache={};source_hash={}
    for sid,row in records.items():
        if not isinstance(row['path'],str) or not row['path']:raise ValueError('Explicit source file path required')
        path=Path(row['path']);path=(path if path.is_absolute() else base/path).resolve(strict=True)
        if path not in file_cache:
            if sum(v['bytes'] for v in file_cache.values())+path.stat().st_size>4*1024**3:
                raise ValueError('Scene source hashing budget exceeded')
            file_cache[path]=snapshot_file(path)
        fingerprint=file_cache[path]['sha256']
        if 'sha256' in row and row['sha256']!=fingerprint:raise ValueError('Declared scene source bytes differ')
        hashes[fingerprint].add(sid);source_hash[sid]=fingerprint
    closures={};budget=0
    for sid in records:
        reachable=set();todo=[sid]
        while todo:
            node=todo.pop()
            if node in reachable:continue
            reachable.add(node);todo.extend(records[node]['parent_ids']);todo.extend(hashes[source_hash[node]]-reachable)
        budget+=len(reachable)
        if budget>1000000:raise ValueError('Scene closure budget exceeded')
        closures[sid]=reachable
    adapted=[]
    for sid in order:
        row=records[sid];families=set()
        for node in closures[sid]:
            scene=scene_map[records[node]['scene_id']]
            families.update(('scene:'+scene['scene_id'],'recipe:'+scene['recipe_id']))
            families.update('axis:'+axis+':'+scene['family_axes'][axis] for axis in selected if scene['family_axes'][axis] is not None)
        adapted.append({k:row[k] for k in ('source_id','path','parent_ids','lineage_status','exposure')})
        adapted[-1].update(family_ids=sorted(families),capture_ids=[],sha256=source_hash[sid])
    result=lineage_audit({'schema_version':1,'data_scope':packet['data_scope'],
        'require_unexposed_test':packet['require_unexposed_test'],'source_origin':'generated_3d',
        'sources':adapted,'allocations':packet['allocations']},base=base)
    findings.extend(result['private_findings'])
    used=set();by_split={split:{axis:set() for axis in AXES} for split in SPLITS}
    for allocation in packet['allocations']:
        reachable=set().union(*(closures[s] for s in allocation['source_ids']));used.update(reachable)
        for sid in reachable:
            axes=scene_map[records[sid]['scene_id']]['family_axes']
            for axis in AXES:
                if axes[axis] is not None:by_split[allocation['split']][axis].add(axes[axis])
    used_scenes={records[s]['scene_id'] for s in used}
    for sid in sorted(used_scenes):
        scene=scene_map[sid]
        for axis in AXES:
            if scene['family_axes'][axis] is None:findings.append({'code':'UNRESOLVED_SCENE_FAMILY_AXIS','scene_id':sid,'axis':axis})
        if scene['asset_record']['status']=='unreviewed':findings.append({'code':'UNREVIEWED_SCENE_ASSETS','scene_id':sid})
    axis_overlap=Counter()
    for i,left in enumerate(SPLITS):
        for right in SPLITS[i+1:]:
            for axis in AXES:
                common=by_split[left][axis]&by_split[right][axis]
                if common:
                    axis_overlap[axis]+=len(common)
                    if axis in selected:findings.append({'code':'CROSS_SPLIT_SCENE_AXIS','axis':axis,'splits':[left,right],'family_values':sorted(common)})
    for path,before in asset_files.items():
        if snapshot_file(path)!=before:raise ValueError('Asset record changed during audit')
    summary={**result['summary'],'scope':'generated_scene_declared_axes_and_file_lineage_only',
        'scene_entries_n':len(scenes),'used_scene_entries_n':len(used_scenes),
        'generation_runs_n':len({scene_map[s]['generation_run_id'] for s in used_scenes}),
        'seed_values_n':len({scene_map[s]['seed'] for s in used_scenes}),
        'scene_recipe_alias_groups_n':sum(len(v)>1 for v in recipes.values()),
        'byte_alias_distinct_scene_groups_n':sum(len({records[s]['scene_id'] for s in group})>1 for group in hashes.values()),
        'separate_axes':selected,'all_six_axes_requested':set(selected)==set(AXES),
        'unique_declared_families_by_axis':{a:len({scene_map[s]['family_axes'][a] for s in used_scenes if scene_map[s]['family_axes'][a] is not None}) for a in AXES},
        'cross_split_overlap_counts_by_axis':dict(axis_overlap),
        'declared_constraint_findings':dict(Counter(row['code'] for row in findings)),
        'declared_constraints_satisfied':not findings,'asset_records_rechecked_n':len(asset_files),
        'rights_or_semantic_independence_proven':False,
        'limitations':result['summary']['limitations']+[
            'Scene axes, generator recipe and asset status are declarations; hashes do not prove their semantics/rights.',
            'Generated stimulus sources have no fabricated camera capture IDs; response capture/participants remain separate.',
            'A seed or generation batch count is not an independent family count.',
            'A subset of held-out axes supports only that declared preflight scope, never a general independence claim.']}
    return {**result,'summary':summary,'private_findings':findings,
            'private_scene_assets':list(asset_files.values())}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();path=args.input.resolve(strict=True)
    result=audit(decode(_read(path)),base=path.parent)
    output=_private(args.output);output.mkdir(parents=True,exist_ok=False)
    (output/'summary.json').write_bytes(canonical(result['summary']))
    (output/'details.private.json').write_bytes(canonical({k:v for k,v in result.items() if k not in ('summary','allocations')}))
    print(json.dumps(result['summary']))


if __name__=='__main__':main()
