"""File-backed source/split preflight. Never proves semantic independence or rights."""
import argparse
from collections import Counter, defaultdict, deque
import json
import sys
from pathlib import Path

from validation_v03.run_manifest import snapshot_file
from validation_v03.session_artifacts import canonical, decode, _private, _read

SPLITS=('diagnostic','development','validation','test')
EXPOSURES=('declared_unused','used_in_development','known_public','unknown')


def _id(value):return isinstance(value,str) and 0<len(value)<=256 and value.strip()==value


def _ids(values,*,empty=True):
    if (not isinstance(values,list) or len(values)>1000 or (not empty and not values) or
            not all(_id(value) for value in values) or len(set(values))!=len(values)):
        raise ValueError('Explicit unique source/group identifiers required')
    return set(values)


def audit(packet, *, base):
    if (not isinstance(packet,dict) or type(packet.get('schema_version')) is not int or packet['schema_version']!=1 or
            packet.get('data_scope') not in ('declared_metadata','synthetic_metadata','real_files_synthetic_allocation') or
            type(packet.get('require_unexposed_test')) is not bool):
        raise ValueError('Explicit source manifest schema, scope and exposure policy required')
    sources,allocations=packet.get('sources'),packet.get('allocations')
    if (not isinstance(sources,list) or not 1<=len(sources)<=1000 or
            not isinstance(allocations,list) or not 1<=len(allocations)<=10000):
        raise ValueError('Bounded source and allocation collections required')
    base=Path(base).resolve();records={};files={};snapshots={};hash_groups=defaultdict(set)
    required={'source_id','path','parent_ids','family_ids','capture_ids','lineage_status','exposure'}
    declared_memberships=0
    for source in sources:
        if (not isinstance(source,dict) or not required.issubset(source) or
                set(source)-required-{'sha256'} or not _id(source['source_id']) or
                source['source_id'] in records or not isinstance(source['path'],str) or not source['path']):
            raise ValueError('Missing, duplicate or unsupported source entry')
        parents=_ids(source['parent_ids']);_ids(source['family_ids']);_ids(source['capture_ids'])
        declared_memberships+=len(parents)+len(source['family_ids'])+len(source['capture_ids'])
        if declared_memberships>20000:raise ValueError('Declared membership budget exceeded')
        if source['lineage_status'] not in ('root_of_supplied_material','derived','unresolved') or source['exposure'] not in EXPOSURES:
            raise ValueError('Unknown lineage status or exposure declaration')
        if ((source['lineage_status']=='root_of_supplied_material' and parents) or
                (source['lineage_status']=='derived' and not parents)):
            raise ValueError('Root/derived parent declarations conflict')
        path=Path(source['path']);path=(path if path.is_absolute() else base/path).resolve(strict=True)
        if path not in snapshots:
            if sum(item['bytes'] for item in snapshots.values())+path.stat().st_size>4*1024**3:
                raise ValueError('Source hashing budget exceeded')
            snapshots[path]=snapshot_file(path)
        if sum(item['bytes'] for item in snapshots.values())>4*1024**3:raise ValueError('Source hashing budget exceeded')
        if 'sha256' in source and source['sha256']!=snapshots[path]['sha256']:
            raise ValueError('Declared source bytes do not match actual file')
        sid=source['source_id'];records[sid]=source;files[sid]=snapshots[path]
        hash_groups[files[sid]['sha256']].add(sid)
    # Validate the chronological parent DAG independently of content aliases.
    children=defaultdict(list);degree={sid:len(row['parent_ids']) for sid,row in records.items()}
    if sum(degree.values())>20000:raise ValueError('Parent-edge budget exceeded')
    for sid,row in records.items():
        for parent in row['parent_ids']:
            if parent not in records:raise ValueError('Unknown parent reference; use unresolved lineage explicitly')
            children[parent].append(sid)
    queue=deque(sid for sid,count in degree.items() if count==0);visited=0
    while queue:
        sid=queue.popleft();visited+=1
        for child in children[sid]:
            degree[child]-=1
            if degree[child]==0:queue.append(child)
    if visited!=len(records):raise ValueError('Cyclic source parent graph')
    effective={};closure_budget=0;group_budget=0
    for sid in records:
        reachable=set();queue=[sid]
        while queue:
            node=queue.pop()
            if node in reachable:continue
            reachable.add(node)
            queue.extend(records[node]['parent_ids'])
            queue.extend(hash_groups[files[node]['sha256']]-reachable)
        closure_budget+=len(reachable)
        if closure_budget>1000000:raise ValueError('Lineage closure budget exceeded')
        groups={('source_identity',node) for node in reachable}
        exposures=set();families=set();captures=set()
        for node in reachable:
            row=records[node]
            groups.add(('byte_identity',files[node]['sha256']))
            families.update(row['family_ids']);captures.update(row['capture_ids']);exposures.add(row['exposure'])
        groups.update(('family',value) for value in families)
        groups.update(('capture',value) for value in captures)
        group_budget+=len(groups)
        if group_budget>1000000:raise ValueError('Effective membership budget exceeded')
        effective[sid]={'reachable':reachable,'groups':groups,'family_ids':families,
                        'capture_ids':captures,'exposures':exposures}
    findings=[];used=set();split_groups={split:set() for split in SPLITS};allocation_map={}
    def issue(code,**fields):findings.append({'code':code,**fields})
    expected={'allocation_id','split','source_ids','participant_ids','capture_ids'}
    allocation_budget=0
    for row in allocations:
        if (not isinstance(row,dict) or set(row)!=expected or not _id(row['allocation_id']) or
                row['allocation_id'] in allocation_map or row['split'] not in SPLITS):
            raise ValueError('Malformed or duplicate allocation')
        source_ids=_ids(row['source_ids'],empty=False)
        participants=_ids(row['participant_ids']);captures=_ids(row['capture_ids'])
        allocation_budget+=len(participants)+len(captures)
        if allocation_budget>1000000:raise ValueError('Allocation membership budget exceeded')
        if not source_ids.issubset(records):raise ValueError('Allocation references missing source')
        groups=set();families=set();exposures=set()
        for sid in source_ids:
            value=effective[sid];used.update(value['reachable']);groups.update(value['groups'])
            families.update(value['family_ids']);exposures.update(value['exposures'])
            allocation_budget+=len(value['groups'])
            if allocation_budget>1000000:raise ValueError('Allocation membership budget exceeded')
        groups.update(('participant',value) for value in participants)
        groups.update(('capture',value) for value in captures)
        split_groups[row['split']].update(groups)
        allocation_map[row['allocation_id']]={'split':row['split'],'family_ids':families,
                                             'participant_ids':participants,'capture_ids':captures}
        if packet['require_unexposed_test'] and row['split']=='test':
            if exposures.intersection({'used_in_development','known_public'}):
                issue('EXPOSED_TEST_SOURCE',allocation_id=row['allocation_id'])
            if 'unknown' in exposures:issue('UNVERIFIED_TEST_EXPOSURE',allocation_id=row['allocation_id'])
    for sid in sorted(used):
        row=records[sid]
        if row['lineage_status']=='unresolved':issue('UNRESOLVED_PARENT_LINEAGE',source_id=sid)
        if not effective[sid]['family_ids']:issue('UNRESOLVED_SOURCE_FAMILY',source_id=sid)
        if not effective[sid]['capture_ids']:issue('UNRESOLVED_CAPTURE_LINEAGE',source_id=sid)
        inherited=set().union(*(effective[parent]['family_ids'] for parent in row['parent_ids'])) if row['parent_ids'] else set()
        if not inherited.issubset(row['family_ids']):issue('MISSING_DECLARED_PARENT_FAMILY',source_id=sid)
    for members in hash_groups.values():
        if len(members)>1 and members.intersection(used):
            declared={tuple(sorted(records[sid]['family_ids'])) for sid in members if records[sid]['family_ids']}
            if len(declared)>1:issue('BYTE_ALIAS_FAMILY_CONFLICT',source_ids=sorted(members))
    overlaps=Counter()
    for index,left in enumerate(SPLITS):
        for right in SPLITS[index+1:]:
            common=split_groups[left]&split_groups[right]
            for kind in sorted({kind for kind,_ in common}):
                values=sorted(value for token,value in common if token==kind)
                overlaps[kind]+=len(values)
                issue('CROSS_SPLIT_'+kind.upper(),splits=[left,right],group_values=values)
    actual_splits={row['split'] for row in allocations}
    if not {'development','validation','test'}.issubset(actual_splits):issue('MISSING_INDEPENDENT_PARTITIONS')
    for path,expected_file in snapshots.items():
        if snapshot_file(path)!=expected_file:raise ValueError('Source bytes changed during lineage audit')
    summary={'schema_version':1,'scope':'file_and_declared_lineage_constraints_only',
        'data_scope':packet['data_scope'],'source_entries_n':len(records),'source_paths_verified_n':len(snapshots),
        'unique_byte_sequences_n':len(hash_groups),'byte_duplicate_groups_n':sum(len(group)>1 for group in hash_groups.values()),
        'allocation_entries_n':len(allocations),'allocation_split_counts':dict(Counter(row['split'] for row in allocations)),
        'declared_constraint_findings':dict(Counter(row['code'] for row in findings)),
        'cross_split_overlap_counts_by_kind':dict(overlaps),'declared_constraints_satisfied':not findings,
        'source_bytes_rechecked':True,'independence_proven':False,'source_authentication_proven':False,
        'limitations':['IDs, parent edges, family/capture membership and exposure are caller declarations.',
                       'Byte identity catches exact copies; re-encoding/mirroring/semantic near duplicates need review.',
                       'No matched response trials, consent, unused-person status or authentication outcome verified.']}
    return {'summary':summary,'private_findings':findings,
        'private_sources':[{'source_id':sid,**files[sid],'effective_family_ids':sorted(effective[sid]['family_ids'])}
                           for sid in records],'allocations':allocation_map}


def validate_score_rows(rows, result):
    """Bind actual CSV trial IDs to checked allocations before threshold selection."""
    if not result['summary']['declared_constraints_satisfied']:
        raise ValueError('Lineage preflight found unresolved or overlapping split provenance')
    allocations=result['allocations']
    if {row['trial_id'] for row in rows}!=set(allocations):raise ValueError('Score rows and checked allocations differ')
    for row in rows:
        allocation=allocations[row['trial_id']]
        families={value.strip() for value in row['source_family_ids'].split(';')}
        participants={row['participant_id'].strip()} if row['participant_id'].strip() else set()
        if (allocation['split']!=row['split'] or allocation['family_ids']!=families or
                allocation['participant_ids']!=participants or row['capture_id'].strip() not in allocation['capture_ids']):
            raise ValueError('Score row lineage does not match verified allocation')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    args=p.parse_args()
    path=args.input.resolve(strict=True);result=audit(decode(_read(path)),base=path.parent)
    output=_private(args.output);output.mkdir(parents=True,exist_ok=False)
    (output/'summary.json').write_bytes(canonical(result['summary']))
    details={key:value for key,value in result.items() if key not in ('summary','allocations')}
    (output/'details.private.json').write_bytes(canonical(details))
    print(json.dumps(result['summary']))


if __name__=='__main__':
    try:main()
    except (OSError,ValueError,TypeError,KeyError,RecursionError) as error:
        print(json.dumps({'status':'REJECTED','error_type':type(error).__name__}),file=sys.stderr)
        sys.exit(2)
