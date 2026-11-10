/* Explicit host UI QA; target execution stays inside the Docker worker. */
const {chromium}=require(process.env.VALVULN_PLAYWRIGHT_CORE || 'playwright-core');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const {execFileSync}=require('node:child_process');
const {randomUUID}=require('node:crypto');
const root=path.resolve(__dirname,'..'),directory=path.join(root,'artifacts/m4b');fs.mkdirSync(directory,{recursive:true});
const python=path.join(root,'.venv/Scripts/python.exe'),origin='http://127.0.0.1:8000';
const password=fs.readFileSync(path.join(root,'.local-data/demo-password.txt'),'utf8').trim();
const hunterName=process.env.VALVULN_SMOKE_HUNTER || 'hunter-b';assert(['hunter-a','hunter-b'].includes(hunterName));
const resumeRun=process.env.VALVULN_SMOKE_RESUME_RUN; if(resumeRun)assert(/^[a-f0-9-]{36}$/.test(resumeRun));
function reset(condition){execFileSync(python,['-m','evaluator.m2','reset','--condition','fixed','--xss-condition',condition],{cwd:root,stdio:'pipe'});}
const result={status:'RUNNING',page_errors:[],external_requests:[]};
const stamp=new Date().toISOString().replace(/[:.]/g,'-');
(async()=>{
 if(!resumeRun)reset('vulnerable');
 const browser=await chromium.launch({executablePath:process.env.VALVULN_CHROMIUM || path.join(process.env.LOCALAPPDATA,'ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true});
 try{
  function monitor(p){p.on('pageerror',e=>result.page_errors.push(e.message));p.on('request',r=>{if(!r.url().startsWith(origin)&&!r.url().startsWith('blob:'))result.external_requests.push(r.url());});}
  async function login(p,name){monitor(p);await p.goto(origin);await p.locator('#login-name').fill(name);await p.locator('#login-password').fill(password);await p.locator('#login-form button').click();await p.locator('#login-dialog').waitFor({state:'hidden'});}
  const hc=await browser.newContext({viewport:{width:1366,height:900},acceptDownloads:true});const hunter=await hc.newPage();await login(hunter,hunterName);
  let rid,text;
  if(resumeRun){
   const existing=await hunter.evaluate(async rid=>{const p=(await api('/api/programs'))[0];for(const row of await api(`/api/programs/${p.program_id}/conversations`)){const c=await api(`/api/conversations/${row.conversation_id}`);if(c.run_ids.includes(rid))return {id:c.conversation_id,title:c.draft_title};}throw Error('Existing run conversation not found');},resumeRun);
   rid=resumeRun;text=existing.title;await hunter.evaluate(id=>openConversation(id),existing.id);result.resumed_existing_run=true;result.target_requests_this_check=0;
  }else{
  await hunter.locator('#new-report').click();text=`QA M4b ${randomUUID()} <img src=x onerror=alert(1)>`;
  await hunter.locator('#message-input').fill(text);await hunter.locator('#send-button').click();await hunter.locator('.user-bubble').filter({hasText:text}).waitFor();
  assert.equal(await hunter.locator('.user-bubble img').count(),0);
  await hunter.getByRole('button',{name:'Validasi snapshot',exact:true}).click();
  await hunter.getByLabel('Path lampiran korban (milik akun kedua)',{exact:true}).fill('/api/attachments/ui-draft');
  await hunter.getByLabel('Kemampuan validasi',{exact:true}).selectOption('XSS');
  assert.equal(await hunter.getByLabel('Rute pratinjau terdaftar',{exact:true}).inputValue(),'/notifications/preview');
  assert(await hunter.getByLabel('Rute pratinjau terdaftar',{exact:true}).evaluate(n=>n.readOnly));
  assert.equal(await hunter.getByLabel('Path lampiran kontrol (milik akun pertama)',{exact:true}).isVisible(),false);
  await hunter.getByLabel('Kemampuan validasi',{exact:true}).selectOption('BAC');
  assert.equal(await hunter.getByLabel('Path lampiran korban (milik akun kedua)',{exact:true}).inputValue(),'/api/attachments/ui-draft');
  await hunter.getByLabel('Kemampuan validasi',{exact:true}).selectOption('XSS');
  const response=hunter.waitForResponse(r=>r.url().endsWith('/runs')&&r.request().method()==='POST');
  await hunter.getByRole('button',{name:'Mulai validasi snapshot'}).click();
  const created=await (await response).json();assert(created.run_id,created.error_code);rid=created.run_id;
  Object.assign(result,{category_switch_preserves_bac_draft:true,xss_route_fixed:true});
  console.log('M4b UI: snapshot submitted');
  }
  result.run_id=rid;
  for(let i=0;i<190;i++){const status=await (await hunter.request.get(`${origin}/api/runs/${rid}`)).json();if(!['QUEUED','LEASED'].includes(status.queue_status)){assert.equal(status.process_status,'COMPLETED',`Product run ended ${status.process_status}: ${status.error_code}`);break;}if(i===189)throw Error('PRODUCT_RUN_DID_NOT_TERMINATE');await hunter.waitForTimeout(1000);}
  await hunter.getByText('Pengujian selesai; ringkasan menunggu review dan publikasi admin.',{exact:true}).waitFor({timeout:5000});
  console.log('M4b UI: browser workflow completed');
  assert.equal(await hunter.getByRole('button',{name:'Bukti 1',exact:true}).count(),0);
  assert((await hunter.locator('.fine-print').allTextContents()).some(t=>t.includes('browser lab aktual')));
  const ac=await browser.newContext({viewport:{width:1366,height:900}});const admin=await ac.newPage();await login(admin,'admin');
  await admin.getByRole('button',{name:text.slice(0,80),exact:true}).click();
  await admin.locator('.assessment-title').getByText('CONFIRMED',{exact:true}).waitFor();
  await admin.getByRole('button',{name:'Bukti 2',exact:true}).click();
  await admin.locator('#dialog-body pre').filter({hasText:'screenshot_base64'}).waitFor();
  const evidence=JSON.parse(await admin.locator('#dialog-body pre').textContent());const capture=JSON.parse(evidence.observation.body);
  assert.equal(capture.fixture,'marker-v1');assert.equal(capture.marker_events.length,1);
  assert.equal(await admin.locator('#dialog-body img,#dialog-body script').count(),0);
  await admin.screenshot({path:path.join(directory,'admin-evidence.png')});await admin.locator('#dialog-close').click();
  await admin.getByRole('button',{name:'Review hasil',exact:true}).click();
  await admin.getByLabel('Catatan review internal',{exact:true}).fill('QA-private-XSS <script>never publish</script>');
  await admin.getByRole('button',{name:'Simpan review',exact:true}).click();await admin.locator('#detail-dialog').waitFor({state:'hidden'});
  await admin.getByRole('button',{name:'Bagikan ringkasan',exact:true}).click();await admin.getByText('Ringkasan aman dibagikan ke pelapor.',{exact:true}).waitFor();
  await hunter.reload();await hunter.getByRole('button',{name:text.slice(0,80),exact:true}).click();await hunter.locator('.assessment-title').getByText('CONFIRMED',{exact:true}).waitFor();
  const event=hunter.waitForEvent('download');await hunter.getByRole('button',{name:'Ekspor JSON',exact:true}).click();
  const download=await event;const exported=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
  assert.equal(exported.assessment.verdict,'CONFIRMED');assert.equal(exported.counters.target_requests,8);assert.equal(exported.counters.browser_actions,20);
  const publicText=JSON.stringify(exported);for(const secret of ['QA-private','screenshot_base64','raw_model','requester-a','evidence_id','<script>'])assert(!publicText.includes(secret));
  assert(exported.assessment.summary.includes('fixture'));assert(exported.assessment.summary.includes('browser lab aktual'));
  await hunter.screenshot({path:path.join(directory,'hunter-desktop.png')});
  for(const width of [320,390,768,1366,1440]){await hunter.setViewportSize({width,height:900});assert(await hunter.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));}
  await hunter.setViewportSize({width:390,height:844});await hunter.screenshot({path:path.join(directory,'hunter-mobile.png')});
  assert.deepEqual(result.page_errors,[]);assert.deepEqual(result.external_requests,[]);
  result.status='PASS';Object.assign(result,{review_publish_export:true,evidence_inert_admin_only:true,viewports:[320,390,768,1366,1440],requests:8,browser_actions:20});
  reset('fixed');
 }catch(e){result.status='FAILED';result.error=e.message;throw e;}
 finally{await browser.close();const output=JSON.stringify(result,null,2);fs.writeFileSync(path.join(directory,`ui-${stamp}.json`),output);fs.writeFileSync(path.join(directory,'ui-verification.json'),output);}
 console.log(JSON.stringify(result));
})().catch(e=>{console.error(e.message);process.exitCode=1;});
