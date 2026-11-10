/* Existing operator evidence only. No target/model call, reset or new run. */
const {chromium}=require(process.env.VALVULN_PLAYWRIGHT_CORE || 'playwright-core');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),directory=path.join(root,'artifacts/m4');
const runs=JSON.parse(fs.readFileSync(path.join(directory,'verification.json'),'utf8')).results;
const run=runs.find(row=>row.condition==='fixed').run_id;
const password=fs.readFileSync(path.join(root,'.local-data/demo-password.txt'),'utf8').trim();
const origin='http://127.0.0.1:8000';
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.VALVULN_CHROMIUM || path.join(process.env.LOCALAPPDATA,'ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true});
 const errors=[],external=[];
 try{
  const admin=await browser.newPage();admin.on('pageerror',e=>errors.push(e.message));admin.on('request',r=>{if(!r.url().startsWith(origin))external.push(r.url());});
  async function login(page,name){await page.goto(origin);await page.locator('#login-name').fill(name);await page.locator('#login-password').fill(password);await page.locator('#login-form button').click();await page.locator('#login-dialog').waitFor({state:'hidden'});}
  await login(admin,'admin');
  const ids=await admin.evaluate(async run=>{
   const p=(await api('/api/programs'))[0];
   const result=await api(`/api/runs/${run}`);
   for(const row of await api(`/api/programs/${p.program_id}/conversations`)){
    const c=await api(`/api/conversations/${row.conversation_id}`);
    if(c.run_ids.includes(run))return {conversation:c.conversation_id,evidence:result.evidence[1].evidence_id};
   }
   throw Error('Operator conversation not found');
  },run);
  await admin.evaluate(id=>openConversation(id),ids.conversation);
  await admin.getByRole('button',{name:'Bukti 2',exact:true}).click();
  await admin.locator('#dialog-body pre').filter({hasText:'screenshot_base64'}).waitFor();
  assert((await admin.locator('#dialog-body pre').textContent()).includes('onerror'));
  assert.equal(await admin.locator('#dialog-body img,#dialog-body script').count(),0);
  await admin.screenshot({path:path.join(directory,'admin-evidence-ui.png')});
  const hunterContext=await browser.newContext();const hunter=await hunterContext.newPage();
  await login(hunter,'hunter-a');
  assert.equal((await hunter.request.get(`${origin}/api/evidence/${ids.evidence}`)).status(),404);
  assert.equal((await hunter.request.get(`${origin}/api/runs/${run}/export`)).status(),404);
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  const result={status:'PASS',run_id:run,browser_evidence_text_inert:true,raw_screenshot_not_rendered_inline:true,
    hunter_evidence_and_cross_owner_export_denied:true,page_errors:errors,external_requests:external,new_runs:0,target_requests:0};
  fs.writeFileSync(path.join(directory,'ui-evidence-verification.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
