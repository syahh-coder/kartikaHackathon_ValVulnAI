"""Trusted operator probe, streamed on stdin during maintenance. No report/GT input."""
import asyncio
import base64
import hashlib
import json
from pathlib import Path
import sys
from uuid import UUID, uuid4

import httpx
from playwright.async_api import async_playwright, Error as PlaywrightError
from boundary.contracts import LAB_IP, ORIGIN
from worker.browser_tool import LAUNCH_ARGS


async def reproduce(config: dict, observations: list[dict]) -> None:
    point=config['point']
    assert point in {'UP-01','UP-02','UP-03'}
    for alias in ('requester-a','requester-b'):UUID(config['objects'][alias]['request_id'])
    UUID(config['snapshot_id']);UUID(config['run_id'])
    accounts=json.loads(Path('/run/secrets/lab_accounts').read_text())
    clients={};requests=[]
    try:
        for alias in accounts:
            c=httpx.AsyncClient(base_url=f'http://{LAB_IP}:8001',trust_env=False,follow_redirects=False,timeout=8,
                headers={'Host':'lab:8001','Origin':ORIGIN,'Accept-Encoding':'identity'})
            clients[alias]=c
            r=await c.post('/api/auth/login',json={'login_name':alias,'password':accounts[alias]['password']})
            r.raise_for_status();assert r.json()['account_alias']==alias
            c.headers['X-CSRF-Token']=r.json()['csrf_token']
            requests.append({'actor':alias,'method':'POST','path':'/api/auth/login','status':r.status_code})

        async def exchange(alias,method,relative,body=None):
            async with clients[alias].stream(method,relative,json=body) as r:
                raw=bytearray()
                async for chunk in r.aiter_bytes():
                    if len(raw)+len(chunk)>1048576:raise ValueError('RESPONSE_LIMIT')
                    raw.extend(chunk)
                requests.append({'actor':alias,'method':method,'path':relative,'status':r.status_code,'sha256':hashlib.sha256(raw).hexdigest()})
                return r,bytes(raw)

        async def upload(alias,name,data,media):
            r,raw=await exchange(alias,'POST','/api/attachments',{'request_id':config['objects'][alias]['request_id'],
                'filename':name,'media_type':media,'content_base64':base64.b64encode(data).decode()})
            assert r.status_code==200
            value=json.loads(raw);assert value['content_sha256']==hashlib.sha256(data).hexdigest()
            return value['upload_id']

        def provenance():
            return {'run_id':config['run_id'],'snapshot_id':config['snapshot_id'],'action_id':str(uuid4()),'evidence_id':str(uuid4())}

        if point=='UP-03':
            nonce=str(uuid4());name='collision-'+nonce+'.txt'
            old,new=b'Synthetic owner B original',b'Synthetic writer A replacement'
            victim=await upload('requester-b',name,old,'text/plain');route=f'/attachments/{victim}/download'
            before,before_bytes=await exchange('requester-b','GET',route)
            denied,_=await exchange('requester-a','GET',route)
            assert before.status_code==200 and before_bytes==old and denied.status_code==404
            attacker=await upload('requester-a',name,new,'text/plain')
            after,after_bytes=await exchange('requester-b','GET',route);assert after.status_code==200
            await upload('requester-a','different-'+nonce+'.txt',b'Synthetic unrelated content','text/plain')
            control,control_bytes=await exchange('requester-b','GET',route)
            assert control.status_code==200 and control_bytes==after_bytes
            observations.append(provenance()|{'source':'operator_http','victim_upload_id':victim,'attacker_upload_id':attacker,'nonce':nonce,'requests':requests,
                'before_sha256':hashlib.sha256(before_bytes).hexdigest(),'after_sha256':hashlib.sha256(after_bytes).hexdigest(),
                'original_sha256':hashlib.sha256(old).hexdigest(),'replacement_sha256':hashlib.sha256(new).hexdigest(),
                'control_sha256':hashlib.sha256(control_bytes).hexdigest(),'different_name_control':True,'nonowner_read_denied':True})
            return

        async with async_playwright() as pw:
            browser=await pw.chromium.launch(channel='chromium',headless=True,chromium_sandbox=True,args=LAUNCH_ARGS)
            try:
                async def browse(relative,nonce,content,download=False):
                    ctx=await browser.new_context(viewport={'width':800,'height':600},service_workers='block',accept_downloads=False)
                    pending,background,events=set(),[],[]
                    counters={'documents':0,'denied_requests':0,'download_events':0,'popup_blocks':0,'websocket_blocks':0}
                    http={};closing=False;page=None;url=ORIGIN+relative
                    try:
                        assert not await ctx.cookies()
                        await ctx.add_init_script("Object.defineProperty(window,'__vvStorageEmpty',{value:localStorage.length===0&&sessionStorage.length===0});")
                        await ctx.add_cookies([{'name':c.name,'value':c.value,'url':ORIGIN,'httpOnly':True,'sameSite':'Strict'} for c in clients['requester-a'].cookies.jar])
                        async def route_request(route):
                            task=asyncio.current_task();pending.add(task)
                            try:
                                r=route.request
                                if closing or r.url!=url or r.method!='GET' or r.resource_type!='document' or r.frame!=page.main_frame or r.redirected_from or counters['documents']:
                                    counters['denied_requests']+=1;await route.abort('blockedbyclient');return
                                counters['documents']+=1
                                response,raw=await exchange('requester-a','GET',relative)
                                assert response.status_code==200 and response.headers.get('content-encoding','identity')=='identity'
                                headers={k:v for k,v in response.headers.items() if k in {'content-type','content-disposition','content-security-policy','x-content-type-options','cache-control'}}
                                http.update(status=200,headers=headers,body_sha256=hashlib.sha256(raw).hexdigest())
                                await route.fulfill(status=200,body=raw,headers=headers)
                            except asyncio.CancelledError:
                                try:await route.abort('blockedbyclient')
                                except PlaywrightError:pass
                                if not closing:raise
                            finally:pending.discard(task)
                        await ctx.route('**/*',route_request)
                        async def websocket(ws):
                            counters['websocket_blocks']+=1;await ws.close(code=1008,reason='POLICY_BLOCKED')
                        await ctx.route_web_socket('**/*',websocket)
                        async def marker(source,value):
                            if source['page']==page and source['frame']==page.main_frame and source['frame'].url==url and value==nonce and not events:
                                events.append({'nonce':nonce,'origin':ORIGIN,'path':relative,'frame':'main'})
                        await ctx.expose_binding('__vvMarker',marker)
                        def opened(other):
                            if page is not None and other!=page:
                                counters['popup_blocks']+=1;background.append(asyncio.create_task(other.close()))
                        ctx.on('page',opened);page=await ctx.new_page()
                        def downloaded(item):
                            counters['download_events']+=1;background.append(asyncio.create_task(item.cancel()))
                        page.on('download',downloaded)
                        try:await page.goto(url,wait_until='domcontentloaded',timeout=10000)
                        except PlaywrightError:
                            if not download:raise
                        await page.wait_for_timeout(250)
                        js=await page.evaluate('() => 6*7')==42
                        empty=await page.evaluate('() => window.__vvStorageEmpty') is True
                        if download and page.url=='about:blank':empty=True
                        text=await page.evaluate('() => document.documentElement.textContent')
                        png=await page.screenshot(type='png',full_page=False,timeout=3000);assert len(png)<=262144
                        return provenance()|{'source':'operator_chromium','nonce':nonce,'path':relative,'page_url':page.url,'http':http,
                            'browser_version':browser.version,'sandbox_requested':True,'initial_storage_empty':empty,'js_control':js,
                            'payload_visible_as_text':content in text,'dom_excerpt':text[:8192],'marker_events':events.copy(),'counters':counters.copy(),
                            'screenshot_base64':base64.b64encode(png).decode(),'screenshot_sha256':hashlib.sha256(png).hexdigest()}
                    finally:
                        closing=True;running=list(pending)
                        for task in running:task.cancel()
                        await asyncio.gather(*running,return_exceptions=True)
                        await ctx.close();await asyncio.gather(*background,return_exceptions=True)
                for kind in ('inert','marker'):
                    async with asyncio.timeout(30):
                        nonce=str(uuid4());label='Kontrol '+kind+' '+nonce
                        if point=='UP-01':
                            event=f' onload="window.__vvMarker(\'{nonce}\')"' if kind=='marker' else ''
                            content=f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600"{event}><text x="10" y="30">{label}</text></svg>'
                            media='image/svg+xml'
                        else:
                            event=f'<script>window.__vvMarker(\'{nonce}\')</script>' if kind=='marker' else ''
                            content=f'<!doctype html><html><body><p>{label}</p>{event}</body></html>';media='text/html'
                        uid=await upload('requester-a','fixture-'+nonce+('.svg' if point=='UP-01' else '.html'),content.encode(),media)
                        relative=f'/attachments/{uid}/preview' if point=='UP-01' else f'/documents/{uid}/preview'
                        capture=await browse(relative,nonce,content)
                        capture.update(kind=kind,upload_id=uid,input_sha256=hashlib.sha256(content.encode()).hexdigest(),inert_label_visible=label in capture['dom_excerpt'])
                        observations.append(capture)
                        if kind=='marker':
                            safe=f'/attachments/{uid}/download' if point=='UP-01' else f'/documents/{uid}/text'
                            capture=await browse(safe,nonce,content,download=point=='UP-01')
                            capture.update(kind='safe',upload_id=uid,input_sha256=hashlib.sha256(content.encode()).hexdigest());observations.append(capture)
                observations[-1]['request_log']=requests
            finally:await browser.close()
    finally:
        for client in clients.values():await client.aclose()


async def main() -> None:
    output={'status':'RUNNING','observations':[]}
    try:
        async with asyncio.timeout(110):await reproduce(json.loads(sys.argv[1]),output['observations'])
        output['status']='PASS'
    except Exception as exc:output.update(status='FAILED',error_type=type(exc).__name__)
    print(json.dumps(output))


if __name__=='__main__':asyncio.run(main())
