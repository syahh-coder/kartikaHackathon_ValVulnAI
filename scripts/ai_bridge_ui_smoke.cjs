/* Focused QA: extraction -> confirmed snapshot, stale source and OOS. MOCK only. */
const {chromium}=require(process.env.VALVULN_PLAYWRIGHT_CORE||'playwright-core');
const {spawn}=require('node:child_process'),fs=require('node:fs'),path=require('node:path'),net=require('node:net');
const assert=require('node:assert/strict'),{randomBytes}=require('node:crypto');
const root=path.resolve(__dirname,'..'),folder=path.join(root,'artifacts/ai-bridge-20261113/ui',new Date().toISOString().replace(/[-:.]/g,''));
fs.mkdirSync(folder,{recursive:true});const sleep=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
 const socket=net.createServer();await new Promise(r=>socket.listen(0,'127.0.0.1',r));const port=socket.address().port;await new Promise(r=>socket.close(r));
 const origin=`http://127.0.0.1:${port}`,password=randomBytes(24).toString('hex');
 const child=spawn(path.join(root,'.venv/Scripts/python.exe'),['-m','scripts.ai_bridge_qa_server','--port',String(port)],{cwd:root,stdio:['pipe','pipe','pipe'],windowsHide:true});
 let stdout='',stderr='',browser;child.stdout.on('data',d=>stdout+=d);child.stderr.on('data',d=>stderr+=d);
 const closed=new Promise(r=>child.on('close',code=>r(code)));child.stdin.write(JSON.stringify({password})+'\n');
 const errors=[],external=[];let result={status:'FAIL',mode:'MOCK; disposable app; no target execution'};
 try{
  let ready=false;for(let i=0;i<100;i++){try{if((await fetch(origin+'/api/health')).ok){ready=true;break;}}catch{}await sleep(100);}assert(ready,'QA server not ready');
  browser=await chromium.launch({executablePath:process.env.VALVULN_CHROMIUM||path.join(process.env.LOCALAPPDATA,'ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true});
  for(const [width,user] of [[1366,'hunter-a'],[390,'hunter-b']]){
   const context=await browser.newContext({viewport:{width,height:900}});
   await context.route('**/*',route=>{if(route.request().url().startsWith(origin+'/'))return route.continue();external.push(route.request().url());return route.abort();});
   const p=await context.newPage();p.setDefaultTimeout(10000);p.on('pageerror',e=>errors.push(e.message));
   await p.goto(origin);await p.locator('#login-name').fill(user);await p.locator('#login-password').fill(password);await p.locator('#login-form button').click();await p.locator('#login-dialog').waitFor({state:'hidden'});
   await p.getByRole('button',{name:'Buat laporan',exact:true}).click();
   await p.locator('#message-input').fill('portal requester-a requester-b; korban /api/attachments/victim; kontrol /api/attachments/control.');await p.locator('#send-button').click();
   await p.waitForFunction(()=>state.conversation?.draft_version===1&&!document.querySelector('#message-input').value);
   await p.getByRole('button',{name:'Minta saran AI',exact:true}).click();
   await p.getByRole('button',{name:'Siapkan validasi dari saran AI',exact:true}).click();
   await p.getByLabel('Path lampiran korban (milik akun kedua)',{exact:true}).waitFor();
   assert.equal(await p.getByLabel('Path lampiran korban (milik akun kedua)',{exact:true}).inputValue(),'/api/attachments/victim');
   assert.equal(await p.getByLabel('Path lampiran kontrol (milik akun pertama)',{exact:true}).inputValue(),'/api/attachments/control');
   assert.equal(await p.evaluate(()=>window.qaInjected||false),false);
   await p.getByLabel('Pelaksanaan tools',{exact:true}).selectOption('NONE');
   await p.screenshot({path:path.join(folder,`confirmation-${width}-MOCK.png`),fullPage:true});
   await p.getByRole('button',{name:'Mulai validasi snapshot',exact:true}).click();
   await p.getByText(/Klaim dari saran MOCK/).waitFor();
   await p.locator('#message-input').fill('Revisi baru.');await p.locator('#send-button').click();
   await p.getByText(/Hasil lama: draf atau scope/).waitFor();assert.equal(await p.getByRole('button',{name:'Siapkan validasi dari saran AI',exact:true}).count(),0);
   if(width<600)await p.locator('#sidebar-open').click();
   await p.locator('#new-report').click();await p.getByRole('heading',{name:'Draf laporan',exact:true}).waitFor();
   await p.locator('#message-input').fill('QA_OOS portal requester-a requester-b; korban /outside/item; kontrol /api/attachments/control.');await p.locator('#send-button').click();
   await p.waitForFunction(()=>state.conversation?.draft_version===1&&!document.querySelector('#message-input').value);
   await p.getByRole('button',{name:'Minta saran AI',exact:true}).click();await p.getByRole('button',{name:'Siapkan validasi dari saran AI',exact:true}).click();
   await p.getByText(/Backend: OUT_OF_SCOPE/).waitFor();assert.equal(await p.getByRole('button',{name:'Mulai validasi snapshot',exact:true}).count(),0);
   await p.screenshot({path:path.join(folder,`oos-${width}-MOCK.png`),fullPage:true});await context.close();
  }
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);result={...result,status:'PASS',viewports:[1366,390],page_errors:errors,blocked_external:external};
 }catch(e){result.error=String(e);process.exitCode=1;}
 finally{
  if(browser)await browser.close();child.stdin.end('stop\n');
  const code=await Promise.race([closed,sleep(15000).then(()=>{throw Error('QA server shutdown timeout');})]);
  const final=stdout.split(/\r?\n/).find(line=>line.startsWith('QA_FINAL '));if(final)result.server=JSON.parse(final.slice(9));
  if(result.status==='PASS'){assert.equal(code,0);assert.equal(result.server.mock_dispatches,4);assert.equal(result.server.counts.runs,2);for(const t of ['actions','handoff_actions','evidence','assessments'])assert.equal(result.server.counts[t],0);assert.equal(result.server.target_requests,0);assert.equal(result.server.real_provider_requests,0);}
  fs.writeFileSync(path.join(folder,'result.json'),JSON.stringify(result,null,2)+'\n');fs.writeFileSync(path.join(folder,'server.log'),stderr);console.log(JSON.stringify({status:result.status,error:result.error,folder}));
 }
})().catch(e=>{console.error(e.message);process.exitCode=1;});
