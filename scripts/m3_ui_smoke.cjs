/* Optional host Chromium QA; uses existing playwright-core, never worker browser. */
const {chromium}=require(process.env.VALVULN_PLAYWRIGHT_CORE || 'playwright-core');
const fs=require('node:fs');
const path=require('node:path');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict');
const {randomUUID}=require('node:crypto');
const root=path.resolve(__dirname,'..');
const output=path.join(root,'artifacts/m3');fs.mkdirSync(output,{recursive:true});
const python=path.join(root,'.venv/Scripts/python.exe');
function reset(condition){return JSON.parse(execFileSync(python,['-m','evaluator.m2','reset','--condition',condition],{cwd:root,encoding:'utf8'}));}
const password=fs.readFileSync(path.join(root,'.local-data/demo-password.txt'),'utf8').trim();
const origin='http://127.0.0.1:8000';
const hunterName=process.env.VALVULN_SMOKE_HUNTER || 'hunter-a';
assert(['hunter-a','hunter-b'].includes(hunterName));
const errors=[],external=[],polls=[];
async function login(page,name){await page.goto(origin);await page.locator('#login-name').fill(name);await page.locator('#login-password').fill(password);await page.locator('#login-form button').click();await page.locator('#login-dialog').waitFor({state:'hidden'});}
function monitor(page){page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(!r.url().startsWith(origin)&&!r.url().startsWith('blob:'))external.push(r.url());if(/\/api\/runs\/[a-f0-9-]+$/.test(r.url())&&r.method()==='GET')polls.push(Date.now());});}
async function noOverflow(page){assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));}
(async()=>{
 const snapshot=reset('vulnerable');
 const browser=await chromium.launch({executablePath:process.env.VALVULN_CHROMIUM || path.join(process.env.LOCALAPPDATA,'ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true});
 const contexts=[];
 try{
  const hunter=await browser.newContext({viewport:{width:1366,height:768},acceptDownloads:true});contexts.push(hunter);
  const page=await hunter.newPage();monitor(page);await login(page,hunterName);
  assert.equal(await page.locator('#preview-role').count(),0);assert.equal(await page.locator('#admin-nav').isVisible(),false);
  await page.locator('#workspace-switch').click();await page.locator('#dialog-body button').first().click();
  await page.locator('#new-report').click();
  const body=`QA M3 ${randomUUID()} <img src=x onerror=alert(1)>\nLaporan development penghapusan lampiran lintas akun.`;
  const title=body.slice(0,80);
  await page.locator('#message-input').fill(body);await page.locator('#send-button').click();
  await page.getByText(body,{exact:true}).waitFor();assert.equal(await page.locator('.user-bubble img').count(),0);
  await page.locator('#message-input').fill('Draf belum dikirim tetap di tab');
  let releaseNavigation, navigationCaptured;
  const navigationGate=new Promise(resolve=>releaseNavigation=resolve);
  const navigationReady=new Promise(resolve=>navigationCaptured=resolve);
  const conversationRoute=async route=>{
   if(route.request().method()!=='POST')return route.continue();
   const response=await route.fetch();navigationCaptured();await navigationGate;await route.fulfill({response});
  };
  await page.route('**/api/programs/*/conversations',conversationRoute);
  await page.locator('#new-report').click();await navigationReady;
  await page.getByRole('button',{name:title,exact:true}).click();
  releaseNavigation();await page.waitForTimeout(250);await page.unroute('**/api/programs/*/conversations',conversationRoute);
  assert.equal(await page.locator('#message-input').inputValue(),'Draf belum dikirim tetap di tab');
  await page.locator('#message-input').fill('');
  await page.locator('#file-input').setInputFiles({name:'development.md',mimeType:'text/markdown',buffer:Buffer.from('<script>alert(2)</script>\nSynthetic development text.')});
  await page.getByText(/Lampiran tersimpan: development.md/).waitFor();
  await page.reload();await page.getByRole('button',{name:title,exact:true}).click();await page.getByText(body,{exact:true}).waitFor();
  await page.getByRole('button',{name:'Validasi snapshot',exact:true}).click();
  const victim='/api/attachments/'+snapshot.objects['requester-b'].attachment_id;
  const control='/api/attachments/'+snapshot.objects['requester-a'].attachment_id;
  await page.getByLabel('Path lampiran korban (milik akun kedua)',{exact:true}).fill(victim);
  await page.getByLabel('Path lampiran kontrol (milik akun pertama)',{exact:true}).fill(control);
  const response=page.waitForResponse(r=>r.url().endsWith('/runs')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Mulai validasi snapshot'}).click();
  const run=(await (await response).json()).run_id;
  await page.getByText('Pengujian selesai; ringkasan menunggu review dan publikasi admin.',{exact:true}).waitFor({timeout:30000});
  assert.equal(await page.getByRole('button',{name:'Bukti 1',exact:true}).count(),0);
  const terminalPolls=polls.length;await page.waitForTimeout(2200);assert.equal(polls.length,terminalPolls);
  console.log('M3 UI: hunter snapshot and worker completed');
  await noOverflow(page);await page.screenshot({path:path.join(output,'hunter-desktop.png')});
  const admin=await browser.newContext({viewport:{width:1366,height:768}});contexts.push(admin);
  const review=await admin.newPage();monitor(review);await login(review,'admin');
  await review.getByRole('button',{name:title,exact:true}).click();
  await review.locator('.assessment-title').getByText('CONFIRMED',{exact:true}).waitFor();
  await review.getByRole('button',{name:'Bukti 1',exact:true}).click();await review.locator('#dialog-body pre').filter({hasText:'owner_alias'}).waitFor();
  assert.equal(await review.locator('#dialog-body img,#dialog-body script').count(),0);
  await review.locator('#dialog-close').click();
  await review.getByRole('button',{name:'Review hasil',exact:true}).click();await review.getByLabel('Catatan review internal',{exact:true}).fill('QA internal-cookie-secret; kontrol dan dampak ditinjau.');
  await review.getByRole('button',{name:'Simpan review',exact:true}).click();await review.locator('#detail-dialog').waitFor({state:'hidden'});
  await review.getByRole('button',{name:'Bagikan ringkasan',exact:true}).click();await review.getByText('Ringkasan aman dibagikan ke pelapor.',{exact:true}).waitFor();
  await review.screenshot({path:path.join(output,'admin-desktop.png')});
  await page.reload();await page.getByRole('button',{name:title,exact:true}).click();await page.locator('.assessment-title').getByText('CONFIRMED',{exact:true}).waitFor();
  const downloadEvent=page.waitForEvent('download');await page.getByRole('button',{name:'Ekspor JSON'}).click();const download=await downloadEvent;const location=await download.path();const exported=JSON.parse(fs.readFileSync(location,'utf8'));
  assert.equal(exported.assessment.verdict,'CONFIRMED');for(const key of ['evidence','target_id','requested_by'])assert(!Object.hasOwn(exported,key));assert(!JSON.stringify(exported).includes('internal-cookie-secret'));
  for(const width of [320,390,768,1366,1440]){await page.setViewportSize({width,height:900});await noOverflow(page);}
  await page.setViewportSize({width:390,height:844});await page.locator('#sidebar-open').click();await page.locator('#sidebar-close').click();await page.screenshot({path:path.join(output,'hunter-mobile.png')});
  await page.locator('#theme-toggle').evaluate(b=>b.click());assert.equal(await page.locator('html').getAttribute('data-theme'),'light');
  await page.locator('#scope-button').click();await page.locator('#detail-dialog').waitFor({state:'visible'});await page.keyboard.press('Escape');await page.locator('#detail-dialog').waitFor({state:'hidden'});
  await page.locator('#logout').click();await page.locator('#login-dialog').waitFor({state:'visible'});assert.equal(await page.locator('#chat-content').textContent(),'');
  console.log('M3 UI: review, export and responsive checks completed');
  // Hold an actual admin response while a newer poll/session takes over.
  // Neither an obsolete poll nor private data from the old login may render.
  async function heldRunResponse(){
   let release, captured;
   const gate=new Promise(resolve=>release=resolve);
   const ready=new Promise(resolve=>captured=resolve);
   let held=false;
   const pattern=`**/api/runs/${run}`;
   const handler=async route=>{
    if(held)return route.continue();held=true;
    const response=await route.fetch();const data=await response.json();
    captured();await gate;
    await route.fulfill({response,json:{...data,process_status:'STALE_RESPONSE'}});
   };
   await review.route(pattern,handler);
   await review.evaluate(id=>{void guard(()=>loadRun(id));},run);
   await ready;
   return async()=>{release();await review.waitForTimeout(250);await review.unroute(pattern,handler);};
  }
  let release=await heldRunResponse();
  await review.evaluate(id=>loadRun(id),run);await release();
  assert(!(await review.locator('#chat-content').textContent()).includes('STALE_RESPONSE'));
  release=await heldRunResponse();
  await review.locator('#logout').click();await review.locator('#login-dialog').waitFor({state:'visible'});
  await review.locator('#login-name').fill(hunterName==='hunter-a'?'hunter-b':'hunter-a');await review.locator('#login-password').fill(password);
  await review.locator('#login-form button').click();await review.locator('#login-dialog').waitFor({state:'hidden'});
  await release();
  assert.equal(await review.locator('.assessment-card').count(),0);
  assert(!(await review.locator('#chat-content').textContent()).includes('internal-cookie-secret'));
  assert.equal(await review.locator('#admin-nav').isVisible(),false);
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  fs.writeFileSync(path.join(output,'ui-verification.json'),JSON.stringify({status:'PASS',run_id:run,browser:browser.version(),viewports:[320,390,768,1366,1440],login_upload_snapshot_worker_review_export:'PASS',draft_reload_navigation:'PASS',inert_report_and_response:'PASS',late_poll_and_previous_session_discarded:'PASS',terminal_polling_stopped:true,external_requests:external,page_errors:errors,mode:'mock planner; real lab HTTP'},null,2));
  console.log(JSON.stringify({status:'PASS',run_id:run,browser:browser.version(),screenshots:3,page_errors:errors.length,external_requests:external.length}));
 } finally {for(const context of contexts)await context.close();await browser.close();reset('fixed');}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
