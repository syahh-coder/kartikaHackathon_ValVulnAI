/* Reuse the completed M3 QA run. No lab reset, model dispatch or new run. */
const {chromium}=require(process.env.VALVULN_PLAYWRIGHT_CORE || 'playwright-core');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..');
const output=path.join(root,'artifacts/m3');
const {run_id:run}=JSON.parse(fs.readFileSync(path.join(output,'ui-verification.json'),'utf8'));
const password=fs.readFileSync(path.join(root,'.local-data/demo-password.txt'),'utf8').trim();
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.VALVULN_CHROMIUM || path.join(process.env.LOCALAPPDATA,'ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true});
 try{
  const page=await browser.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('http://127.0.0.1:8000');
  async function login(name){await page.locator('#login-name').fill(name);await page.locator('#login-password').fill(password);await page.locator('#login-form button').click();await page.locator('#login-dialog').waitFor({state:'hidden'});}
  await login('admin');
  const conversation=await page.evaluate(async run=>{
   const programs=await api('/api/programs');
   const conversations=await api(`/api/programs/${programs[0].program_id}/conversations`);
   for(const row of conversations){const data=await api(`/api/conversations/${row.conversation_id}`);if(data.run_ids.includes(run))return row.conversation_id;}
   throw Error('Completed QA conversation not found');
  },run);
  await page.evaluate(id=>openConversation(id),conversation);
  await page.getByRole('button',{name:'Bukti 1',exact:true}).click();
  await page.locator('#dialog-body pre').filter({hasText:'owner_alias'}).waitFor();
  await page.locator('#dialog-close').click();
  let release,captured;
  const gate=new Promise(resolve=>release=resolve),ready=new Promise(resolve=>captured=resolve);
  await page.route('**/api/evidence/*',async route=>{const response=await route.fetch();captured();await gate;await route.fulfill({response});});
  await page.getByRole('button',{name:'Bukti 1',exact:true}).click();await ready;
  await page.locator('#logout').click();await page.locator('#login-dialog').waitFor({state:'visible'});
  assert.equal(await page.locator('#dialog-body').textContent(),'');
  await login('hunter-a');release();await page.waitForTimeout(500);
  assert.equal(await page.locator('#detail-dialog').isVisible(),false);
  assert.equal(await page.locator('#dialog-body').textContent(),'');
  assert.equal(await page.locator('.assessment-card').count(),0);
  assert.equal(await page.locator('#admin-nav').isVisible(),false);
  assert.deepEqual(errors,[]);
  const result={status:'PASS',run_id:run,previous_admin_evidence_response_discarded:true,private_panel_cleared_on_logout:true,new_runs:0,target_requests:0,page_errors:errors};
  fs.writeFileSync(path.join(output,'session-verification.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result));
 }finally{await browser.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
