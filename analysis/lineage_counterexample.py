"""Audit real paired derivatives under deliberately synthetic, leaking splits.

No responses, participants, new captures or evaluation trials are generated.
All source metadata and fingerprints remain in a new private output directory.
"""
import argparse
import json
from pathlib import Path

from validation_v03.lineage_manifest import audit
from validation_v03.session_artifacts import canonical,_private


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pair-dir',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    pair=args.pair_dir.resolve(strict=True)
    output=_private(args.output)
    packet=dict(schema_version=1,data_scope='real_files_synthetic_allocation',
                require_unexposed_test=True,sources=[],allocations=[])
    files=('preserved_original.private.mp4','unmasked.private.mkv','black.private.mkv','skin.private.mkv')
    for index,name in enumerate(files):
        packet['sources'].append(dict(source_id='source-'+str(index),path=str(pair/name),
            parent_ids=['source-0'] if index else [],family_ids=['known-development-family'],
            capture_ids=['known-development-capture'],
            lineage_status='derived' if index else 'root_of_supplied_material',
            exposure='used_in_development'))
    for index,split in enumerate(('development','validation','test'),1):
        packet['allocations'].append(dict(allocation_id='synthetic-'+split,split=split,
            source_ids=['source-'+str(index)],participant_ids=[],capture_ids=[]))
    result=audit(packet,base=pair)
    required={'EXPOSED_TEST_SOURCE','CROSS_SPLIT_SOURCE_IDENTITY','CROSS_SPLIT_BYTE_IDENTITY',
              'CROSS_SPLIT_FAMILY','CROSS_SPLIT_CAPTURE'}
    if not required.issubset(result['summary']['declared_constraint_findings']):
        raise ValueError('Expected ancestor leakage was not detected')
    output.mkdir(parents=True,exist_ok=False)
    (output/'manifest.private.json').write_bytes(canonical(packet))
    details={key:value for key,value in result.items() if key!='allocations'}
    (output/'audit.private.json').write_bytes(canonical(details))
    (output/'summary.json').write_bytes(canonical(result['summary']))
    print(json.dumps(result['summary']))


if __name__=='__main__':main()
