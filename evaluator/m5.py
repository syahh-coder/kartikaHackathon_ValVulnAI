"""Explicit local M5 checks: product UP-04, operator UP-01..03, no live model."""
import argparse
import asyncio
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from evaluator.m2 import cli,compose,operator,ready
from evaluator.m3 import checked,login
from evaluator.m4 import browser_processes,lab_log
from evaluator.m4b import start,terminal

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'artifacts/m5'


def reset(point: str | None = None, condition: str = 'fixed') -> dict:
    ready();operator('maintenance_enter')
    args=['reset','--condition','fixed']
    if point:args.extend(['--upload-point',point,'--upload-condition',condition])
    snapshot=cli('lab','lab.maintenance',*args)
    operator('maintenance_release',{'snapshot_id':snapshot['snapshot_id']})
    return snapshot


async def product(results: list[dict]) -> None:
    a,b,admin=[await login(name) for name in ('hunter-a','hunter-b','admin')]
    active=None
    try:
        p=checked(await a.get('/api/programs'))[0]['program_id']
        await asyncio.to_thread(operator,'register_upload')
        for condition,expected in [('vulnerable','CONFIRMED'),('fixed','REFUTED')]:
            seed=await asyncio.to_thread(reset,'UP-04',condition)
            rid=seed['objects']['requester-a']['request_id']
            claim={'asset_alias':'portal','path':f'/requests/{rid}/attachments','method':'GET','category':'UPLOAD',
                'account_aliases':['requester-a','requester-b'],'primary_claim':'Nama fixture upload dapat mengeksekusi marker pada daftar lampiran'}
            cid,active=await start(a,p,'Development M5',claim)
            public=await terminal(a,active)
            private=checked(await admin.get(f'/api/runs/{active}'))
            record={'point':'UP-04','condition':condition,'run_id':active,'conversation_id':cid,'private_run':private,'status':'CHECKING','evidence':[]}
            results.append(record)
            assert private['process_status']=='COMPLETED',private.get('error_code')
            assert private['assessment']['system_verified']['verdict']==expected
            assert private['counters']['target_requests']==10 and private['counters']['browser_actions']==15
            assert len(private['evidence'])==5 and public['assessment'] is None and public['awaiting_review']
            assert (await b.get(f'/api/runs/{active}/export')).status_code==404
            for item in private['evidence']:
                assert (await a.get('/api/evidence/'+item['evidence_id'])).status_code==404
                record['evidence'].append(checked(await admin.get('/api/evidence/'+item['evidence_id'])))
            assert (await admin.post(f'/api/runs/{active}/publish')).status_code==409
            checked(await admin.post(f'/api/runs/{active}/review',json={'reviewer_note':'Private M5 operator review <svg onload=never>'}))
            checked(await admin.post(f'/api/runs/{active}/publish'))
            exported=checked(await a.get(f'/api/runs/{active}/export'))
            assert exported['assessment']['verdict']==expected
            for secret in ('<svg','requester-a','screenshot_base64','Private M5','evidence_id'):
                assert secret not in json.dumps(exported)
            assert sum(r[2] for r in await asyncio.to_thread(lab_log))==10
            assert not await asyncio.to_thread(browser_processes)
            record.update(status='PASS',verdict=expected,requests=10,publication_export='PASS')
            active=None
            print(json.dumps({'point':'UP-04','condition':condition,'status':'PASS','verdict':expected}),flush=True)
    finally:
        if active:await asyncio.to_thread(operator,'fail',{'run_id':active})
        for client in (a,b,admin):await client.aclose()


def operator_points(results: list[dict], points: tuple[str,...]) -> None:
    ready();operator('maintenance_enter')
    source=(ROOT/'evaluator/m5_lab_probe.py').read_text(encoding='utf-8')
    for point in points:
        for condition in ('vulnerable','fixed'):
            snapshot=cli('lab','lab.maintenance','reset','--condition','fixed','--upload-point',point,'--upload-condition',condition)
            config={'point':point,'snapshot_id':snapshot['snapshot_id'],'objects':snapshot['objects'],'run_id':str(uuid4())}
            raw=json.loads(compose('exec','-T','--user','10001:10001','worker','python','-',json.dumps(config),input=source))
            record={'point':point,'condition':condition,'run_id':config['run_id'],'snapshot_id':snapshot['snapshot_id'],'probe':raw,'status':'CHECKING'}
            results.append(record)
            (DIRECTORY/(config['run_id']+'.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
            assert raw['status']=='PASS',raw.get('error_type')
            observations=raw['observations']
            if point=='UP-03':
                assert len(observations)==1
                v=observations[0]
                assert v['before_sha256']==v['original_sha256']
                assert v['after_sha256']==(v['replacement_sha256'] if condition=='vulnerable' else v['original_sha256'])
                assert v['different_name_control'] and v['nonowner_read_denied'] and v['control_sha256']==v['after_sha256']
                assert v['victim_upload_id']!=v['attacker_upload_id']
                assert sum(row[2] for row in lab_log())==len(v['requests'])
            else:
                assert [o['kind'] for o in observations]==['inert','marker','safe']
                for obs in observations:
                    assert obs['js_control'] and obs['initial_storage_empty'] and obs['counters']['documents']==1 and obs['http']['status']==200
                    png=base64.b64decode(obs['screenshot_base64'],validate=True)
                    assert hashlib.sha256(png).hexdigest()==obs['screenshot_sha256']
                    (DIRECTORY/(obs['evidence_id']+'.png')).write_bytes(png)
                inert,marker,safe=observations
                assert inert['inert_label_visible'] and not inert['marker_events']
                assert len(marker['marker_events'])==(1 if condition=='vulnerable' else 0)
                if condition=='fixed':assert marker['payload_visible_as_text']
                assert not safe['marker_events']
                if point=='UP-01':
                    assert safe['counters']['download_events']==1 and safe['http']['headers']['content-disposition'].startswith('attachment;')
                    assert safe['http']['body_sha256']==safe['input_sha256']
                else:assert safe['payload_visible_as_text']
                assert sum(row[2] for row in lab_log())==len(safe['request_log'])
            assert not browser_processes()
            record.update(status='PASS',access_log=lab_log())
            (DIRECTORY/(config['run_id']+'.json')).write_text(json.dumps(record,indent=2),encoding='utf-8')
            print(json.dumps({'point':point,'condition':condition,'status':'PASS'}),flush=True)


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument('--point',choices=['UP-01','UP-02','UP-03','UP-04'],action='append')
    args=parser.parse_args()
    points=tuple(args.point) if args.point else ('UP-04','UP-01','UP-02','UP-03')
    DIRECTORY.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output={'status':'RUNNING','mode':'mock product UP-04; operator-only other points; no live model','points':points,'results':[],
        'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for d in ('app','boundary','worker','lab','evaluator') for p in (ROOT/d).rglob('*.py')}}
    try:
        if 'UP-04' in points:asyncio.run(product(output['results']))
        other=tuple(p for p in points if p!='UP-04')
        if other:operator_points(output['results'],other)
        output['status']='PASS'
    except BaseException as exc:
        output.update(status='FAILED',error_type=type(exc).__name__)
        raise
    finally:
        try:
            if browser_processes():raise RuntimeError('Browser still running; leave target unavailable')
            reset()
            output['final_state']={'heartbeat':operator('heartbeat'),'browser_processes':browser_processes(),'access_log':lab_log(),
                'images':json.loads(compose('images','--format','json'))}
        except BaseException as exc:output.update(status='FAILED',cleanup_error_type=type(exc).__name__)
        data=json.dumps(output,indent=2)
        (DIRECTORY/(stamp+'-verification.json')).write_text(data,encoding='utf-8')
        (DIRECTORY/'verification.json').write_text(data,encoding='utf-8')
    if output['status']!='PASS':raise RuntimeError('M5 verification incomplete')


if __name__=='__main__':main()
