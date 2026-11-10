"""Explicit M4a operator reproduction/security checks. Never runs at startup."""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import time

import httpx

from app.agent.xss import verify_pair
from boundary.browser import BrowserCapture
from evaluator.m2 import cli, compose, operator, reset

ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'artifacts/m4'


def action(run_id, fixture, account='requester-a'):
    return operator('browser_action',{'run_id':run_id,'arguments':{'account_alias':account,'fixture':fixture}})


def capture(observation):
    value=BrowserCapture.model_validate_json(observation['body'])
    assert value.initial_storage_empty and value.js_control
    assert observation['status']=='OK' and observation['http_status']==200
    assert observation['request_attempts']==2 and observation['responses_received']==2
    assert value.screenshot_base64
    (DIRECTORY/(observation['action_id']+'.png')).write_bytes(base64.b64decode(value.screenshot_base64))
    return value


def lab_log():
    code="import sqlite3,json; c=sqlite3.connect('/data/lab.sqlite3'); print(json.dumps(c.execute('SELECT method,path,count(*) FROM access_log GROUP BY method,path').fetchall()))"
    return json.loads(compose('exec','-T','--user','10001:10001','lab','python','-c',code))


def browser_processes():
    code="""import pathlib,json
names={'chrome','chrome_crashpad_handler','chrome-headless-shell'}
processes=[]
for path in pathlib.Path('/proc').glob('[0-9]*/cmdline'):
 try:
  command=path.read_bytes().split(b'\\0')[0].decode()
  if command and pathlib.Path(command).name in names: processes.append(path.parent.name)
 except OSError: pass
print(json.dumps(processes))
"""
    return json.loads(compose('exec','-T','--user','10001:10001','worker','python','-c',code))


@contextmanager
def api_admin():
    origin='http://127.0.0.1:8000'
    client=httpx.Client(base_url=origin,trust_env=False,headers={'Origin':origin},timeout=10)
    try:
        csrf=client.get('/api/auth/csrf').json()['csrf_token']
        password=(ROOT/'.local-data/demo-password.txt').read_text().strip()
        response=client.post('/api/auth/login',json={'login_name':'admin','password':password},headers={'X-CSRF-Token':csrf})
        response.raise_for_status()
        client.headers['X-CSRF-Token']=response.json()['csrf_token']
        yield client
    finally:
        client.close()


def verify(security=True,cancel_only=False,network_only=False):
    DIRECTORY.mkdir(parents=True,exist_ok=True)
    results=[]
    active=None
    output={'status':'RUNNING','mode':'operator only; no model and no product assessment','results':results}
    try:
        operator('register_browser')
        for condition,expected in ([] if cancel_only or network_only else [('vulnerable','CONFIRMED'),('fixed','REFUTED')]):
            reset('fixed',xss_condition=condition)
            active=operator('begin_browser')['run_id']
            accounts=[]
            for account in ('requester-a','requester-b'):
                control=action(active,'inert-v1',account)
                probe=action(active,'marker-v1',account)
                a,b=capture(control),capture(probe)
                assert not a.marker_events
                assert verify_pair(control,probe)==expected
                accounts.append({'account':account,'verdict':expected,'control_action_id':control['action_id'],
                    'probe_action_id':probe['action_id'],'marker_events':len(b.marker_events),'fresh_storage':True})
            assert sum(row[2] for row in lab_log())==8
            assert not browser_processes()
            operator('finish',{'run_id':active})
            results.append({'condition':condition,'run_id':active,'accounts':accounts,'requests':8,'evidence':4})
            active=None
            print(json.dumps({'phase':condition,'status':'PASS','verdict':expected}),flush=True)
        if security and not cancel_only:
            reset('fixed',xss_condition='fixed')
            cli('lab','lab.maintenance','arm-browser-network')
            active=operator('begin_browser')['run_id']
            control=action(active,'inert-v1')
            probe=action(active,'marker-v1','requester-a')
            a,b=capture(control),capture(probe)
            assert verify_pair(control,probe)=='REFUTED'
            assert b.denied_requests>=3 and b.websocket_blocks>=1 and b.popup_blocks>=1 and b.download_blocks>=1
            log=lab_log()
            assert sum(row[2] for row in log)==4
            assert {row[1] for row in log}=={'/api/auth/login','/notifications/preview'}
            assert not browser_processes()
            operator('finish',{'run_id':active})
            results.append({'network_run_id':active,'blocked_requests':b.denied_requests,'blocked_websockets':b.websocket_blocks,
                'blocked_popups':b.popup_blocks,'blocked_downloads':b.download_blocks,'actual_requests':4,
                'only_login_and_preview_reached_lab':True,'fresh_storage_after_previous_context_mutation':True})
            active=None
            print(json.dumps({'phase':'browser_network','status':'PASS'}),flush=True)
        if security and not network_only:
            reset('fixed',xss_condition='fixed')
            active=operator('begin_browser')['run_id']
            capture(action(active,'inert-v1'))
            cli('lab','lab.maintenance','arm-browser-delay')
            log_since=datetime.now(timezone.utc).isoformat()
            with ThreadPoolExecutor(max_workers=1) as pool:
                future=pool.submit(action,active,'marker-v1')
                for _ in range(25):
                    if cli('lab','lab.maintenance','inspect')['browser_delay_started']: break
                    time.sleep(.1)
                else: raise RuntimeError('Delayed browser navigation not observed')
                with api_admin() as admin:
                    response=admin.post(f'/api/runs/{active}/cancel')
                    response.raise_for_status()
                    result=admin.get(f'/api/runs/{active}').json()
                    assert result['process_status']=='CANCELLED' and result['assessment'] is None and len(result['evidence'])==1
                try: future.result(timeout=10)
                except RuntimeError: pass
                else: raise AssertionError('Cancelled browser action unexpectedly completed')
            for _ in range(15):
                if operator('heartbeat')['status']=='IDLE' and not browser_processes(): break
                time.sleep(.1)
            else: raise RuntimeError('Browser/context survived cancellation')
            # The server-side bounded delay can finish after its client has gone.
            # Keep the target dirty until that old handler is quiescent before reseeding.
            time.sleep(8.5)
            assert not browser_processes()
            logs=compose('logs','--since',log_since,'--no-log-prefix','worker')
            assert not any(marker in logs for marker in ('Traceback','TargetClosedError','Task exception'))
            results.append({'cancel_run_id':active,'cancel_during_navigation':True,'retained_evidence':1,'assessment':None,
                'browser_processes_after_cancel':0,'worker_callback_errors':0})
            active=None
            print(json.dumps({'phase':'browser_cancel','status':'PASS'}),flush=True)
        output['status']='PASS'
    except BaseException as exc:
        output['status']='FAILED'
        output['error_type']=type(exc).__name__
        raise
    finally:
        if active:
            operator('fail',{'run_id':active})
        reset('fixed',xss_condition='fixed')
        output['remaining_browser_processes']=len(browser_processes())
        filename='network-verification.json' if network_only else 'cancel-verification.json' if cancel_only else 'verification.json'
        (DIRECTORY/filename).write_text(json.dumps(output,indent=2),encoding='utf-8')
    print(json.dumps(output,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group()
    group.add_argument('--smoke-only',action='store_true')
    group.add_argument('--cancel-only',action='store_true')
    group.add_argument('--network-only',action='store_true')
    args=parser.parse_args()
    verify(security=not args.smoke_only,cancel_only=args.cancel_only,network_only=args.network_only)
