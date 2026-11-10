/* Disposable product UI QA, no lab/model transport and no existing user storage. */
const {chromium}=require(process.env.VALVULN_PLAYWRIGHT_CORE||'playwright-core');
const {spawn,execFileSync}=require('node:child_process');
const fs=require('node:fs');const path=require('node:path');const net=require('node:net');
const assert=require('node:assert/strict');const {randomBytes,randomUUID}=require('node:crypto');
const root=path.resolve(__dirname,'..'),python=path.join(root,'.venv/Scripts/python.exe');
const stamp=new Date().toISOString().replace(/[-:.]/g,''),folder=path.join(root,'artifacts/business-review',stamp);
fs.mkdirSync(folder,{recursive:true});
const fixture=Buffer.from(execFileSync(python,['-c',"import sys,json;sys.path.insert(0,'tests');from test_business_trace_audit import record;print(json.dumps(record()))"],{cwd:root,encoding:'utf8'}));
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function port(){const server=net.createServer();await new Promise(resolve=>server.listen(0,'127.0.0.1',resolve));const value=server.address().port;await new Promise(resolve=>server.close(resolve));return value;}
(async()=>{
 const number=await port(),origin=`http://127.0.0.1:${number}`,password=randomBytes(24).toString('hex');
 const child=spawn(python,['-m','scripts.business_review_qa_server','--port',String(number)],{cwd:root,stdio:['pipe','pipe','pipe'],windowsHide:true});
 let output='',serverError='',exitCode=null,childError=null;
 child.stdout.on('data',data=>output+=data);child.stderr.on('data',data=>serverError+=data);
 child.on('error',error=>childError=error);const closed=new Promise(resolve=>child.on('close',code=>{exitCode=code;resolve();}));
 child.stdin.write(JSON.stringify({password})+'\n');
 let browser;const errors=[],external=[];let result={status:'FAIL',mode:'disposable app UI; synthetic uploaded record only'};
 try{
  let ready=false;for(let i=0;i<100;i++){if(childError)throw childError;if(exitCode!==null)throw Error('QA app stopped before ready');try{const response=await fetch(origin+'/api/health');if(response.ok){ready=true;break;}}catch{}await sleep(100);}assert(ready,'QA app not ready');
  browser=await chromium.launch({executablePath:process.env.VALVULN_CHROMIUM||path.join(process.env.LOCALAPPDATA,'ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true});
  async function session(name){const context=await browser.newContext({viewport:{width:1366,height:900},acceptDownloads:true});await context.route('**/*',route=>{const url=route.request().url();if(url.startsWith(origin+'/')||url.startsWith('blob:'))return route.continue();external.push(url);return route.abort();});const page=await context.newPage();page.setDefaultTimeout(8000);page.on('pageerror',error=>errors.push(error.message));await page.goto(origin);await page.locator('#login-name').fill(name);await page.locator('#login-password').fill(password);await page.locator('#login-form button').click();await page.locator('#login-dialog').waitFor({state:'hidden'});return page;}
  const admin=await session('admin');
  await admin.locator('[data-view="guidelines"]').click();await admin.getByLabel('Teks guideline').fill('Aturan kontrol bisnis sintetis untuk QA review rekaman.');
  await admin.getByLabel('Aturan scope terstruktur (JSON)').fill(JSON.stringify({in_scope_rules:[{asset_alias:'portal',path_template:'/api/attachments/{id}',methods:['GET','DELETE'],capabilities:['BAC']}],out_of_scope_rules:[],business_rules_version:'procurement-controls-v1',business_rules:'DRAFT -> SUBMITTED -> APPROVED -> FULFILLED. Kuantitas 1-1000, stok tidak negatif, satu pemenuhan.'}));
  await admin.getByRole('button',{name:'Simpan draf guideline',exact:true}).click();await admin.getByRole('button',{name:/Aktifkan draf v/}).click();await admin.getByText(/Status: ACTIVE/).waitFor();await admin.locator('#dialog-close').click();
  const hunter=await session('hunter-a'),title=`Review bisnis ${randomUUID()} <b>teks saja</b>`;
  await hunter.locator('#new-report').click();await hunter.locator('#message-input').fill(title);await hunter.locator('#send-button').click();await hunter.locator('.user-bubble').filter({hasText:title}).waitFor();assert.equal(await hunter.locator('.user-bubble b').count(),0);
  await hunter.getByRole('button',{name:'Siapkan review bukti bisnis',exact:true}).click();await hunter.getByRole('button',{name:'Simpan snapshot untuk review',exact:true}).click();await hunter.getByRole('heading',{name:'Review rekaman bisnis',exact:true}).waitFor();
  assert.equal(await hunter.getByRole('button',{name:'Unggah rekaman JSON',exact:true}).count(),0);
  await admin.locator('[data-view="reports"]').click();await admin.getByRole('button',{name:title,exact:true}).click();await admin.getByRole('button',{name:'Unggah rekaman JSON',exact:true}).click();
  await admin.getByLabel('File rekaman bisnis').setInputFiles({name:'bad.json',mimeType:'application/json',buffer:Buffer.from('{"credentials":"DO_NOT_ECHO"}')});await admin.getByRole('button',{name:'Periksa dan simpan rekaman',exact:true}).click();await admin.getByText(/Rekaman JSON tidak sesuai format/).waitFor();assert(!(await admin.locator('#dialog-body').innerText()).includes('DO_NOT_ECHO'));
  await admin.getByLabel('File rekaman bisnis').setInputFiles({name:'normal.json',mimeType:'application/json',buffer:fixture});await admin.getByRole('button',{name:'Periksa dan simpan rekaman',exact:true}).click();await admin.getByRole('heading',{name:'Konsistensi rekaman: CONSISTENT',exact:true}).waitFor();
  await admin.getByRole('button',{name:'Langkah berikutnya',exact:true}).click();await admin.locator('#dialog-body p').filter({hasText:'Rekaman konsisten, tetapi sumber'}).waitFor();assert.equal(await admin.locator('#dialog-body li').count(),4);
  const contextDownloadEvent=admin.waitForEvent('download');await admin.getByRole('button',{name:'Ekspor konteks review',exact:true}).click();const contextDownload=await contextDownloadEvent;await contextDownload.saveAs(path.join(folder,'admin-workflow-context.json'));const workflow=JSON.parse(fs.readFileSync(path.join(folder,'admin-workflow-context.json'),'utf8'));assert.equal(workflow.phase,'NEEDS_SOURCE_AND_IMPACT_EVIDENCE');assert.equal(workflow.target_execution_allowed,false);assert.equal(workflow.model_dispatch_allowed,false);assert.equal(workflow.vulnerability_verdict,null);await admin.locator('#dialog-close').click();
  await admin.getByRole('button',{name:'Lihat rekaman unggahan',exact:true}).click();await admin.locator('#dialog-body pre').waitFor();assert.equal(await admin.locator('#dialog-body pre').evaluate(element=>element.querySelectorAll('*').length),0);await admin.locator('#dialog-close').click();
  await admin.getByRole('button',{name:'Tinjau rekaman',exact:true}).click();await admin.getByLabel('Catatan review rekaman').fill('INTERNAL_NOTE <b>catatan privat</b>');await admin.getByRole('button',{name:'Simpan review rekaman',exact:true}).click();await admin.getByRole('button',{name:'Bagikan ringkasan rekaman',exact:true}).waitFor();assert.equal(await admin.locator('.business-area b').count(),0);
  await admin.screenshot({path:path.join(folder,'admin-desktop.png'),fullPage:true});await admin.getByRole('button',{name:'Bagikan ringkasan rekaman',exact:true}).click();await admin.getByText(/Status review: REVIEWED.*PUBLISHED/).waitFor();
  await hunter.reload();await hunter.getByRole('button',{name:title,exact:true}).click();await hunter.getByRole('heading',{name:'Ringkasan review rekaman',exact:true}).waitFor();assert(!(await hunter.locator('.business-area').innerText()).includes('INTERNAL_NOTE'));assert.equal(await hunter.getByRole('button',{name:'Lihat rekaman unggahan',exact:true}).count(),0);
  const downloadEvent=hunter.waitForEvent('download');await hunter.getByRole('button',{name:'Ekspor review rekaman',exact:true}).click();const download=await downloadEvent;await download.saveAs(path.join(folder,'hunter-export.json'));const exported=fs.readFileSync(path.join(folder,'hunter-export.json'),'utf8');for(const hidden of ['INTERNAL_NOTE','actor_id','record_sha256','provenance'])assert(!exported.includes(hidden));
  for(const width of [1366,390]){await hunter.setViewportSize({width,height:900});assert(await hunter.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));await hunter.screenshot({path:path.join(folder,`hunter-${width}.png`),fullPage:true});}
  await admin.getByRole('button',{name:'Tinjau rekaman',exact:true}).click();await admin.getByLabel('Catatan review rekaman').fill('Review ulang, publikasi ditarik.');await admin.getByRole('button',{name:'Simpan review rekaman',exact:true}).click();await admin.getByText(/Status review: REVIEWED.*PRIVATE/).waitFor();
  await hunter.setViewportSize({width:1366,height:900});await hunter.reload();await hunter.getByRole('button',{name:title,exact:true}).click();await hunter.getByText(/Ringkasan akan tampil setelah admin/).waitFor();assert.equal(await hunter.getByRole('heading',{name:'Ringkasan review rekaman',exact:true}).count(),0);
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);result={...result,status:'PASS',viewports:[1366,390],checks:['snapshot','admin import','malformed rejection','workflow context and human steps','private original','review','publish','safe export','withdraw','escaped text','responsive'],page_errors:errors,blocked_external:external};
 }catch(error){result.error=error.message;throw error;}
 finally{if(browser)await browser.close();if(exitCode===null){child.stdin.write('stop\n');child.stdin.end();await Promise.race([closed,sleep(10000)]);if(exitCode===null){child.kill();await closed;result.status='FAIL';result.shutdown='forced';}}
  const line=output.split(/\r?\n/).find(line=>line.startsWith('QA_FINAL '));if(line)result.server=JSON.parse(line.slice(9));
  if(result.status==='PASS'){assert.equal(exitCode,0);assert(result.server?.temporary_storage_removed);assert.deepEqual(result.server.counts,{business_record_reviews:1,runs:0,actions:0,evidence:0,ledger:0,provider_attempts:0});}
  fs.writeFileSync(path.join(folder,'result.json'),JSON.stringify({...result,server_exit:exitCode},null,2));if(serverError)fs.writeFileSync(path.join(folder,'server-log.txt'),serverError);console.log(JSON.stringify({artifact:folder,...result},null,2));
 }
})().catch(error=>{console.error(error.message);process.exitCode=1;});
