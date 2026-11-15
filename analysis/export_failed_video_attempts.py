"""Export actual media timings from failed/rejected synthetic diagnostic runs."""
import argparse
import csv
import json
from pathlib import Path

from analysis.export_conditioned_timings import bound, timing_row
from validation_v03.execution_record import verify
from validation_v03.session_artifacts import _private


def export(records, report, timings):
    report, timings = Path(report).resolve(),Path(timings).resolve()
    if report.exists() or timings.exists(): raise FileExistsError('Fresh exports required')
    attempts=[]; rows=[]
    for number, record in enumerate(records):
        record=_private(record)
        receipt=json.loads((record/'receipt.private.json').read_text())
        if len(receipt['artifact_roots']) != 1: raise ValueError('Single source root per attempt required')
        root=_private(receipt['artifact_roots'][0]); status,manifest=bound(root,record)
        if status['state']=='EXITED_ZERO': raise ValueError('Only failed or rejected run evidence belongs here')
        if any(p.is_relative_to(r) for p in (report,timings) for r in (root,record)):
            raise ValueError('Do not alter evidence roots')
        count=0
        for file in sorted(list(root.glob('*/timing.private.json'))+list(root.glob('*/source_timing.private.json'))):
            timer=json.loads(file.read_text()); metadata={}
            proposal=file.parent/'proposal.private.json'
            if proposal.exists():
                proposal=json.loads(proposal.read_text())
                metadata={'hand':proposal['hand'],'policy':proposal['policy'],'primitive':proposal['recipe']['primitive']}
            row=timing_row(file.parent.name,timer,'rejected_attempt_'+str(number+1),metadata=metadata)
            row.update(run_state=status['state'],process_exit_code=receipt['process_exit_code'],
                       producer_code_commit=manifest['code_commit'],timing_boundary=timer['boundary'],
                       accepted_as_completed_experiment=False)
            rows.append(row); count+=1
        attempts.append({'attempt':number+1,'execution_record':status,'producer_code_commit':manifest['code_commit'],
                         'process_exit_code':receipt['process_exit_code'],'timed_video_attempts_n':count,
                         'accepted_as_completed_experiment':False})
        verify(record)
    if not rows: raise ValueError('No actual timing records; never invent video times for preflight failures')
    with timings.open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    with report.open('x',encoding='utf-8') as stream:
        json.dump({'attempts':attempts,'timing_rows_n':len(rows),
                   'scope':'actual failed/rejected synthetic media attempts; not successful experiment results',
                   'release_allowed':False},stream,indent=2);stream.write('\n')
    return {'attempts_n':len(attempts),'timing_rows_n':len(rows)}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--record',type=Path,action='append',required=True)
    p.add_argument('--report',type=Path,required=True);p.add_argument('--timings',type=Path,required=True)
    a=p.parse_args();print(json.dumps(export(a.record,a.report,a.timings)))
