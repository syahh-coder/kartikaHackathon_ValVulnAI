/* Read-only UI QA against a completed product run: no new target transport/run. */
const {chromium}=require(process.env.VALVULN_PLAYWRIGHT_CORE||'playwright-core');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),directory=path.join(root,'artifacts/m5'),origin='http://127.0.0.1:8000';
const password=fs.readFileSync(path.join(root,'.local-data/demo-password.txt'),'utf8').trim();
const record=fs.readdirSync(directory).filter(n=>/^\d{8}T\d{6}Z-verification\.json$/.test(n)).sort().reverse().map(n=>JSON.parse(fs.readFileSync(path.join(directory,n),'utf8'))).flatMap(x=>x.results||[]).find(x=>x.point==='UP-04'&&x.condition==='vulnerable'&&x.status==='PASS');
assert(record,'Completed UP-04 product run required');
const result={status:'RUNNING',run_id:record.run_id,new_runs:0,target_requests:0,page_errors:[],external_requests:[]};
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.VALVULN_CHROMIUM||path.join(process.env.LOCALAPPDATA,'ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true});
 try{
  async function context(){const c=await browser.newContext({viewport:{width:1366,height:900},acceptDownloads:true});await c.route('**/*',r=>{const u=r.request().url();if(u.startsWith(origin+'/')||u.startsWith('blob:'+origin+'/'))return r.continue();result.external_requests.push(u);return r.abort();});return c;}
  async function login(page,name){page.on('pageerror',e=>result.page_errors.push(e.message));await page.goto(origin);await page.locator('#login-name').fill(name);await page.locator('#login-password').fill(password);await page.locator('#login-form button').click();await page.locator('#login-dialog').waitFor({state:'hidden'});}
  const hc=await context(),hunter=await hc.newPage();await login(hunter,'hunter-a');
  await hunter.evaluate(id=>openConversation(id),record.conversation_id);
  await hunter.locator('.assessment-title').getByText('CONFIRMED',{exact:true}).waitFor();
  await hunter.getByRole('button',{name:'Validasi snapshot',exact:true}).click();
  const select=hunter.getByLabel('Kemampuan validasi',{exact:true});await select.selectOption('UPLOAD');
  const uploadLabel='Path daftar lampiran permintaan milik A (/requests/ID/attachments)';
  const route=await hunter.getByLabel(uploadLabel,{exact:true}).inputValue();assert(route.endsWith('/attachments'));
  assert.equal(await hunter.getByLabel('Path lampiran kontrol (milik akun pertama)',{exact:true}).isVisible(),false);
  await select.selectOption('XSS');assert.equal(await hunter.getByLabel('Rute pratinjau terdaftar',{exact:true}).inputValue(),'/notifications/preview');
  await select.selectOption('UPLOAD');assert.equal(await hunter.getByLabel(uploadLabel,{exact:true}).inputValue(),route);
  assert((await hunter.locator('#dialog-body').innerText()).includes('File laporan tidak dieksekusi'));
  await hunter.locator('#dialog-close').click();
  assert.equal(await hunter.getByRole('button',{name:'Bukti 1',exact:true}).count(),0);
  const ac=await context(),admin=await ac.newPage();await login(admin,'admin');
  await admin.evaluate(id=>openConversation(id),record.conversation_id);
  await admin.locator('.assessment-title').getByText('CONFIRMED',{exact:true}).waitFor();
  await admin.getByRole('button',{name:'Bukti 4',exact:true}).click();
  await admin.locator('#dialog-body pre').filter({hasText:'screenshot_base64'}).waitFor();
  const evidence=JSON.parse(await admin.locator('#dialog-body pre').textContent()),capture=JSON.parse(evidence.observation.body);
  assert.equal(capture.marker_events.length,1);assert.equal(await admin.locator('#dialog-body img,#dialog-body svg,#dialog-body script').count(),0);
  await admin.screenshot({path:path.join(directory,'admin-evidence.png')});await admin.locator('#dialog-close').click();
  const event=hunter.waitForEvent('download');await hunter.getByRole('button',{name:'Ekspor JSON',exact:true}).click();
  const downloaded=await event;result.download={filename:downloaded.suggestedFilename(),failure:await downloaded.failure()};
  const exported=JSON.parse(fs.readFileSync(await downloaded.path(),'utf8'));assert.equal(exported.assessment.verdict,'CONFIRMED');
  for(const forbidden of ['<svg','screenshot_base64','Private M5','requester-a','evidence_id'])assert(!JSON.stringify(exported).includes(forbidden));
  for(const width of [1366,1024,768,390,360]){await hunter.setViewportSize({width,height:900});await hunter.screenshot({path:path.join(directory,`hunter-${width}.png`)});assert(await hunter.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));}
  assert.equal(result.page_errors.length,0);assert.equal(result.external_requests.length,0);
  result.status='PASS';result.upload_form_and_switch='PASS';result.inert_evidence='PASS';result.private_projection_export='PASS';result.viewports=[1366,1024,768,390,360];
 }catch(e){result.status='FAILED';result.error=e.message;throw e;}finally{await browser.close();fs.writeFileSync(path.join(directory,`ui-${new Date().toISOString().replace(/[:.]/g,'-')}.json`),JSON.stringify(result,null,2));fs.writeFileSync(path.join(directory,'ui-verification.json'),JSON.stringify(result,null,2));}
 console.log(JSON.stringify(result));
})().catch(e=>{console.error(e.message);process.exitCode=1;});
