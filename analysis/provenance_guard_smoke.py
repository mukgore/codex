"""Bind a real owned-JS export run to a pre-execution private provenance snapshot."""
import argparse
import json
from pathlib import Path
import subprocess

from analysis.runtime_benchmark.journal import Journal, export_bundle, verify_bundle
from validation_v03.run_manifest import prepare, read, verify_current
from validation_v03.session_artifacts import canonical, save


def execute(config_path,repo,output):
    output=Path(output).resolve()
    if output.exists():raise FileExistsError('Preserve prior guard runs')
    manifest,fingerprint=prepare(config_path,repo,output/'provenance')
    config=manifest['configuration']
    journal=Journal(output/'journal',{'condition_id':config['run_id'],'endpoint':config['endpoint'],
        'input_exposure':config['input_exposure'],'cache_state':'no_model; file/module cache not controlled',
        'planned_frames':0,'timeout_seconds':config['timeout_seconds'],
        'provenance_manifest_sha256':fingerprint,'scope':'local_export_contract_test_not_camera_or_model_timing'})
    try:
        with journal.stage('owned_javascript_export'):
            raw=subprocess.check_output(['node',str(Path(repo)/'analysis/export_event_fixtures.cjs'),
                                         config['parameters']['handcaptcha_root']],timeout=10)
            packet=json.loads(raw)
            if packet['data_scope']!='synthetic_mock_clock_no_camera':raise ValueError('Synthetic-only run required')
        inspections=[]
        with journal.stage('write_reload_and_validate_actual_exports'):
            for name,payload in packet['fixtures'].items():
                if name not in ('bridge_completed','bridge_aborted','demo_truncated'):
                    raise ValueError('Unknown export fixture')
                source=output/(name+'.source.json');source.write_bytes(canonical(payload))
                inspections.append(save(source,output/name))
            if len(inspections)!=3:raise ValueError('Every planned JS export is required')
        with journal.stage('verify_frozen_code_inputs_environment'):
            postflight=verify_current(output/'provenance')
            (output/'postflight.private.json').write_bytes(canonical(postflight))
        journal.finish('COMPLETED')
    finally:
        if not journal.closed:journal.close_without_terminal()
    export_bundle(output/'journal',output/'journal_bundle.private.zip')
    recovered=verify_bundle(output/'journal_bundle.private.zip')
    _,actual=read(output/'provenance')
    runtime_manifest=json.loads((output/'journal/manifest.json').read_text(encoding='utf-8'))
    if actual!=runtime_manifest['provenance_manifest_sha256'] or actual!=postflight['manifest_sha256']:
        raise ValueError('Runtime/provenance linkage mismatch')
    result={'scope':'pre_execution_metadata_guard_and_owned_js_export_contract_run',
            'pre_execution_snapshot_created':True,'postflight_snapshot_matched':True,
            'journal_provenance_link_verified':True,'journal_bundle_recovery':recovered['status'],
            'planned_js_exports':3,'validated_js_exports':len(inspections),'planned_video_frames':0,
            'new_human_observations':0,'model_inference':False,'camera_opened':False,
            'limitations':['Checks source/code/dependency metadata and the declared synthetic export task.',
                           'Browser/permissions/hardware descriptions are not independently verified.',
                           'Runtime includes local process/serialization/storage overhead, not camera or model latency.']}
    (output/'summary.json').write_bytes(canonical(result))
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('config','repo','output'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args();print(json.dumps(execute(args.config,args.repo,args.output)))
