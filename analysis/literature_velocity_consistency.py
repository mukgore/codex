"""Conditional arithmetic audit of a visually checked published velocity table.

This records a cycle-definition ambiguity; it does not resolve the paper's
intent, set a human safety limit or change the project's biomechanical profile.
"""
import argparse
import json
import math
from pathlib import Path

from validation_v03.session_artifacts import canonical,decode,_read,_private


def predicted_peak(excursion_degrees,cycle_seconds,*,t1_fraction_of_cycle):
    values=(excursion_degrees,cycle_seconds,t1_fraction_of_cycle)
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in values):
        raise ValueError('Finite positive excursion, cycle seconds and phase fraction required')
    return math.pi*math.radians(excursion_degrees)/(2*cycle_seconds*t1_fraction_of_cycle)


def audit(extraction):
    if (extraction.get('source_id')!='BIO-06' or extraction.get('status')!='REFERENCE_EXTRACTION_NOT_ADMISSIBLE_PROFILE'
            or extraction.get('production_profile_applied') is not False):
        raise ValueError('Explicit unapplied source extraction required')
    v=extraction['velocity_reference'];rows=[]
    for group in ('male','female'):
        cycle=v['measurement_window_seconds']/v['mean_cycles'][group]
        for joint in ('MCP','PIP','DIP'):
            excursion=v['index_excursions_degrees'][joint]
            literal=predicted_peak(excursion,cycle,t1_fraction_of_cycle=1.)
            half=predicted_peak(excursion,cycle,t1_fraction_of_cycle=.5)
            reported=v['table9_reported_max_rad_s'][group][joint]
            rows.append({'group':group,'joint':joint,'reported_rad_s':reported,
                'literal_t1_equals_cycle_rad_s':literal,'t1_equals_half_cycle_rad_s':half,
                'reported_to_literal_ratio':reported/literal,
                'half_cycle_abs_residual_rad_s':abs(reported-half)})
    return {'scope':'published_formula_table_arithmetic_with_two_explicit_phase_interpretations',
        'source_id':'BIO-06','rows':rows,'rows_n':len(rows),
        'max_half_cycle_residual_rad_s':max(r['half_cycle_abs_residual_rad_s'] for r in rows),
        'phase_intent_resolved':False,'paper_error_proven':False,'human_speed_limit_established':False,
        'biomechanical_profile_changed':False,'release_allowed':False,
        'interpretation':'Reported rounded table values agree closely with half-cycle t1; literal stated full-cycle t1 gives about half. Author intent and task applicability remain unresolved.'}


def run(source,output):
    output=_private(output)
    if output.exists():raise FileExistsError('New private arithmetic record required')
    result=audit(decode(_read(source)));output.mkdir(parents=True)
    (output/'summary.json').write_bytes(canonical(result));return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();print(json.dumps(run(a.source,a.output)))
