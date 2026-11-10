/* Focused desktop/mobile QA on a disposable app; no lab or live model. */
const {chromium}=require(process.env.VALVULN_PLAYWRIGHT_CORE||'playwright-core');
const {spawn}=require('node:child_process'),fs=require('node:fs'),path=require('node:path'),net=require('node:net');
const assert=require('node:assert/strict');const {randomBytes}=require('node:crypto');
const root=path.resolve(__dirname,'..'),folder=path.join(root,'artifacts/r2',new Date().toISOString().replace(/[-:.]/g,''));
fs.mkdirSync(folder,{recursive:true});const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function port(){const s=net.createServer();await new Promise(r=>s.listen(0,'127.0.0.1',r));const p=s.address().port;await new Promise(r=>s.close(r));return p;}
(async()=>{
 const number=await port(),origin=`http://127.0.0.1:${number}`,password=randomBytes(24).toString('hex');
 const child=spawn(path.join(root,'.venv/Scripts/python.exe'),['-m','scripts.r2_ui_qa_server','--port',String(number)],{cwd:root,stdio:['pipe','pipe','pipe'],windowsHide:true});
 let output='',serverError='',exitCode=null;child.stdout.on('data',d=>output+=d);child.stderr.on('data',d=>serverError+=d);
 const closed=new Promise(r=>child.on('close',code=>{exitCode=code;r();}));child.stdin.write(JSON.stringify({password})+'\n');
 let browser;const errors=[],external=[],posts=[];let result={status:'FAIL',mode:'MOCK; disposable app; synthetic stored observation'};
 try{
  let ready=false;for(let i=0;i<100;i++){if(exitCode!==null)throw Error('QA app exited before ready');try{if((await fetch(origin+'/api/health')).ok){ready=true;break;}}catch{}await sleep(100);}assert(ready);
  browser=await chromium.launch({executablePath:process.env.VALVULN_CHROMIUM||path.join(process.env.LOCALAPPDATA,'ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true});
  async function session(name){const context=await browser.newContext({viewport:{width:1366,height:900}});await context.route('**/*',route=>{const u=route.request().url();if(u.startsWith(origin+'/'))return route.continue();external.push(u);return route.abort();});const p=await context.newPage();p.setDefaultTimeout(9000);p.on('pageerror',e=>errors.push(e.message));p.on('request',r=>{if(r.method()==='POST'&&/\/triages$/.test(r.url()))posts.push(r.url());});await p.goto(origin);await p.locator('#login-name').fill(name);await p.locator('#login-password').fill(password);await p.locator('#login-form button').click();await p.locator('#login-dialog').waitFor({state:'hidden'});return p;}
  const hunter=await session('hunter-a'),admin=await session('admin');
  if(process.argv.includes('--configuration-only')){
   await hunter.getByRole('button',{name:'R2 Observasi sintetis',exact:true}).click();
   await admin.evaluate(()=>fetch('/qa/configuration',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':state.csrf},body:JSON.stringify({mode:'live'})}));
   await hunter.getByRole('button',{name:'Perbarui status saran',exact:true}).click();
   await hunter.getByText(/Mode triage dikonfigurasi: LIVE/).waitFor();assert.equal(await hunter.locator('.mode-label').innerText(),'Triage LIVE');
   await hunter.getByRole('button',{name:'Minta saran AI',exact:true}).click();await hunter.locator('.triage-area [role="alert"]').getByText(/CONFIGURATION_REQUIRED/).waitFor();
   await hunter.locator('#model-info').click();await hunter.getByText(/Triage teks: live.*CONFIGURATION_REQUIRED/).waitFor();await hunter.locator('#dialog-close').click();
   for(const width of [1366,390]){await hunter.setViewportSize({width,height:900});assert(await hunter.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await hunter.screenshot({path:path.join(folder,`configuration-${width}.png`),fullPage:true});}
   assert.equal(posts.length,1);assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
   result={...result,status:'PASS',viewports:[1366,390],triage_post_requests:posts.length,checks:['configuration labels','read-only model info','missing key does not fallback','responsive'],page_errors:errors,blocked_external:external};
  }else{
  await hunter.getByRole('button',{name:'R2 Observasi sintetis',exact:true}).click();
  await hunter.getByRole('heading',{name:'Saran triage teks',exact:true}).waitFor();assert.equal(posts.length,0);
  await hunter.locator('#model-info').click();await hunter.getByText(/MOCK adalah simulasi/).waitFor();await hunter.locator('#dialog-close').click();
  await hunter.getByRole('button',{name:'Perbarui status saran',exact:true}).click();assert.equal(posts.length,0);
  await hunter.getByRole('button',{name:'Minta saran AI',exact:true}).evaluate(b=>{b.click();b.click();});
  await hunter.getByText('Status saran: SUCCEEDED',{exact:true}).waitFor();assert.equal(posts.length,1);
  assert((await hunter.locator('.triage-area').innerText()).includes('MOCK'));
  assert((await hunter.locator('.triage-area').innerText()).includes('<img src=x'));
  assert.equal(await hunter.locator('.triage-area img').count(),0);assert(!(await hunter.evaluate(()=>window.r2Injected)));
  await hunter.reload();await hunter.getByRole('button',{name:'R2 Observasi sintetis',exact:true}).click();await hunter.getByText('Status saran: SUCCEEDED',{exact:true}).waitFor();assert.equal(posts.length,1);
  await hunter.getByRole('button',{name:'Ringkasan observasi',exact:true}).click();await hunter.getByText(/Ringkasan menunggu review dan publikasi/).waitFor();await hunter.locator('#dialog-close').click();
  await admin.getByRole('button',{name:'R2 Observasi sintetis',exact:true}).click();assert.equal(await admin.getByRole('button',{name:'Minta saran AI',exact:true}).count(),0);
  await admin.getByRole('button',{name:'Ringkasan observasi',exact:true}).click();await admin.getByText(/Observasi 1: HTTP GET/).waitFor();
  const privateText=await admin.locator('#dialog-body').innerText();for(const secret of ['INTERNAL_NOTE','PRIVATE_MODEL','PRIVATE_DOM','PRIVATE_EVALUATOR_LABEL','secret-only-fixture','PRIVATE_SUMMARY'])assert(!privateText.includes(secret));
  await admin.screenshot({path:path.join(folder,'admin-observations.png'),fullPage:true});await admin.locator('#dialog-close').click();
  await admin.getByRole('button',{name:'Review hasil',exact:true}).click();await admin.getByLabel('Catatan review internal').fill('INTERNAL_NOTE_QA');await admin.getByRole('button',{name:'Simpan review',exact:true}).click();
  await admin.getByRole('button',{name:'Bagikan ringkasan',exact:true}).click();
  await hunter.reload();await hunter.getByRole('button',{name:'R2 Observasi sintetis',exact:true}).click();await hunter.getByRole('button',{name:'Ringkasan observasi',exact:true}).click();await hunter.getByText('Ringkasan yang dibagikan admin',{exact:true}).waitFor();assert(!(await hunter.locator('#dialog-body').innerText()).includes('Evidence ID:'));await hunter.locator('#dialog-close').click();
  for(const width of [1366,390]){await hunter.setViewportSize({width,height:900});assert(await hunter.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await hunter.screenshot({path:path.join(folder,`hunter-${width}.png`),fullPage:true});}
  await hunter.locator('#message-input').fill('Tambahan draf QA.');assert(await hunter.getByRole('button',{name:'Minta saran AI',exact:true}).isDisabled());await hunter.locator('#send-button').click();await hunter.getByText(/Hasil lama: draf atau scope/).waitFor();assert.equal(posts.length,1);
  await hunter.setViewportSize({width:1366,height:900});await hunter.locator('#new-report').click();await hunter.getByRole('heading',{name:'Draf laporan',exact:true}).waitFor();await hunter.locator('#message-input').fill('R2_WAIT untuk pembatalan simulasi.');await hunter.locator('#send-button').click();await hunter.waitForFunction(()=>state.conversation?.draft_version===1&&!document.querySelector('#message-input').value);await hunter.getByRole('button',{name:'Minta saran AI',exact:true}).click();await hunter.getByRole('button',{name:'Batalkan saran',exact:true}).waitFor();
  await hunter.waitForFunction(()=>triageUI.current?.attempts?.length===1);await hunter.getByRole('button',{name:'Batalkan saran',exact:true}).click();await hunter.getByText('Status saran: CANCELLED',{exact:true}).waitFor();assert.equal(posts.length,2);
  await admin.evaluate(async()=>{const r=await fetch('/qa/configuration',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':state.csrf},body:JSON.stringify({mode:'live'})});if(!r.ok)throw Error('QA configuration rejected');});
  await hunter.getByRole('button',{name:'Perbarui status saran',exact:true}).click();await hunter.getByText(/AI teks belum dapat dipakai/).waitFor();await hunter.getByRole('button',{name:'Minta saran AI',exact:true}).click();await hunter.locator('.triage-area [role="alert"]').getByText(/CONFIGURATION_REQUIRED/).waitFor();
  await hunter.setViewportSize({width:390,height:900});assert(await hunter.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await hunter.screenshot({path:path.join(folder,'configuration-mobile.png'),fullPage:true});
  await admin.evaluate(()=>fetch('/qa/configuration',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':state.csrf},body:JSON.stringify({mode:'mock'})}));
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);result={...result,status:'PASS',viewports:[1366,390],triage_post_requests:posts.length,checks:['explicit inference only','double-click guard','reload discovery','escaped output','owner/admin projection','published summary','stale draft','cancel','missing configuration','responsive'],page_errors:errors,blocked_external:external};
  }
 }catch(error){result.error=error.message;throw error;}
 finally{
  if(browser)await browser.close();if(exitCode===null){child.stdin.write('stop\n');child.stdin.end();await Promise.race([closed,sleep(10000)]);if(exitCode===null){child.kill();await closed;result.status='FAIL';}}
  const line=output.split(/\r?\n/).find(l=>l.startsWith('QA_FINAL '));if(line)result.server=JSON.parse(line.slice(9));
  if(result.status==='PASS'){assert.equal(exitCode,0);assert(result.server?.temporary_storage_removed);assert.equal(result.server.mock_dispatches,process.argv.includes('--configuration-only')?0:2);for(const table of ['runs','actions','handoff_actions','evidence','assessments'])assert.equal(result.server.counts[table],result.server.baseline[table]);assert.equal(result.server.real_provider_requests,0);assert.equal(result.server.target_requests,0);}
  fs.writeFileSync(path.join(folder,'result.json'),JSON.stringify({...result,server_exit:exitCode},null,2));if(serverError)fs.writeFileSync(path.join(folder,'server-log.txt'),serverError);console.log(JSON.stringify({artifact:folder,...result},null,2));
 }
})().catch(error=>{console.error(error.message);process.exitCode=1;});
