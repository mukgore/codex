"""Compare selected published excursion entries without resolving clinical limits."""
import argparse
import json
from pathlib import Path

from validation_v03.session_artifacts import canonical,decode,_read,_private


def compare(extraction):
    if (extraction.get('source_id')!='BIO-07' or extraction.get('status')!='REFERENCE_EXTRACTION_NOT_ADMISSIBLE_PROFILE'
            or extraction.get('production_profile_applied') is not False):
        raise ValueError('Explicit unapplied source extraction required')
    selected=extraction['selected_static_comparison'];seen=set();comparisons=[]
    if selected['units']!='degree':raise ValueError('Explicit reported degree units required')
    for row in selected['rows']:
        key=(row['finger'],row['joint'])
        if key in seen:raise ValueError('Duplicate selected joint')
        seen.add(key)
        for axis in ('flexion','extension','abduction_adduction'):
            a=row['cobos'][axis];b=row['chen'][axis]
            for value in (a,b):
                if (not isinstance(value,list) or len(value)!=2 or any(type(v) not in (int,float) or not 0<=v<=360 for v in value)
                        or value[0]>value[1]):raise ValueError('Ordered bounded reported excursions required')
            comparisons.append({'finger':key[0],'joint':key[1],'reported_axis':axis,
                'BIO07_reported_degrees':a,'BIO06_reported_degrees':b,'exactly_equal':a==b})
    return {'scope':'selected_published_table_cell_comparison_not_admissible_profile',
        'joint_rows_n':len(seen),'reported_cell_comparisons_n':len(comparisons),
        'equal_reported_cells_n':sum(r['exactly_equal'] for r in comparisons),
        'different_reported_cells':[r for r in comparisons if not r['exactly_equal']],
        'source_id':'BIO-07','compared_source_id':'BIO-06','paper_error_proven':False,
        'axis_equivalence_verified':False,'profile_changed':False,'release_allowed':False}


def run(source,output):
    output=_private(output)
    if output.exists():raise FileExistsError('New private source comparison required')
    result=compare(decode(_read(source)));output.mkdir(parents=True)
    (output/'summary.json').write_bytes(canonical(result));return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();print(json.dumps(run(a.source,a.output)))
