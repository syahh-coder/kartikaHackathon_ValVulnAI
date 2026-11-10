/* Render repository-owned presentation graphics and capture actual disposable UI, with explicit MOCK labels. */
const {chromium}=require(process.env.VALVULN_PLAYWRIGHT_CORE||'playwright-core');
const {spawn}=require('node:child_process'),fs=require('node:fs'),path=require('node:path'),net=require('node:net');
const {pathToFileURL}=require('node:url'),{randomBytes}=require('node:crypto'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),assets=path.join(root,'submission'),artifacts=path.join(root,'artifacts/r4');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function freePort(){const s=net.createServer();await new Promise(r=>s.listen(0,'127.0.0.1',r));const p=s.address().port;await new Promise(r=>s.close(r));return p;}
(async()=>{
 fs.mkdirSync(path.join(assets,'screenshots'),{recursive:true});fs.mkdirSync(path.join(artifacts,'video-capture'),{recursive:true});
 const uiOnly=process.argv.includes('--ui-only');
 for(const file of uiOnly?['demo-preview-MOCK.webm']:['thumbnail.png','slides.pdf','demo-preview-MOCK.webm'])assert(!fs.existsSync(path.join(assets,file)),`Refuse overwrite ${file}`);
 const browser=await chromium.launch({executablePath:process.env.VALVULN_CHROMIUM||path.join(process.env.LOCALAPPDATA,'ms-playwright/chromium-1248/chrome-win64/chrome.exe'),headless:true});
 const graphic=await browser.newPage({viewport:{width:1200,height:630},deviceScaleFactor:1});
 await graphic.route('http**/*',r=>r.abort());if(!uiOnly){await graphic.goto(pathToFileURL(path.join(assets,'thumbnail.html')).href);await graphic.screenshot({path:path.join(assets,'thumbnail.png')});}
 const png=fs.readFileSync(path.join(assets,'thumbnail.png'));assert.equal(png.readUInt32BE(16),1200);assert.equal(png.readUInt32BE(20),630);assert(png.length<=500000);
 await graphic.setViewportSize({width:1280,height:720});await graphic.goto(pathToFileURL(path.join(assets,'slides.html')).href);
 assert.equal(await graphic.locator('.slide').count(),9);if(!uiOnly)await graphic.pdf({path:path.join(assets,'slides.pdf'),preferCSSPageSize:true,printBackground:true});await graphic.close();
 const port=await freePort(),origin=`http://127.0.0.1:${port}`,password=randomBytes(24).toString('hex');
 const server=spawn(path.join(root,'.venv/Scripts/python.exe'),['-m','scripts.r4_capture_server','--port',String(port)],{cwd:root,windowsHide:true,stdio:['pipe','pipe','pipe']});
 let stdout='',stderr='';server.stdout.on('data',d=>stdout+=d);server.stderr.on('data',d=>stderr+=d);const closed=new Promise(r=>server.once('close',r));server.stdin.write(JSON.stringify({password})+'\n');
 const errors=[],external=[];let result={status:'FAIL',origin:'DISPOSABLE_APP_MOCK_AND_SYNTHETIC_STORED_OBSERVATION'};
 try{
  let ready=false;for(let i=0;i<100;i++){try{if((await fetch(origin+'/api/health')).ok){ready=true;break;}}catch{}await sleep(100);}assert(ready);
  const context=await browser.newContext({viewport:{width:1280,height:720},recordVideo:{dir:path.join(artifacts,'video-capture'),size:{width:1280,height:720}}});
  await context.route('**/*',r=>{if(r.request().url().startsWith(origin+'/'))return r.continue();external.push(r.request().url());return r.abort();});
  await context.addInitScript(()=>document.addEventListener('DOMContentLoaded',()=>{const banner=document.createElement('div');banner.textContent='REVIEW LOKAL • MOCK • REKAMAN SINTETIS • TANPA MODEL LIVE / REQUEST TARGET';banner.style='position:fixed;bottom:0;left:0;right:0;z-index:999999;background:#102e42;color:#b0f6d4;text-align:center;font:12px Segoe UI;padding:7px;pointer-events:none';document.body.append(banner);}));
  const page=await context.newPage();page.setDefaultTimeout(10000);page.on('pageerror',e=>errors.push(e.message));const video=page.video();
  async function login(name){await page.goto(origin);await page.locator('#login-name').fill(name);await page.locator('#login-password').fill(password);await page.locator('#login-form button').click();await page.locator('#login-dialog').waitFor({state:'hidden'});await page.reload();await page.locator('#login-dialog').waitFor({state:'hidden'});await page.getByRole('button',{name:'R2 Observasi sintetis',exact:true}).click();await page.getByRole('heading',{name:'Saran triage teks',exact:true}).waitFor();}
  await login('hunter-a');await sleep(1500);await page.getByRole('button',{name:'Minta saran AI',exact:true}).click();await page.getByText('Status saran: SUCCEEDED',{exact:true}).waitFor();await sleep(2000);
  await page.screenshot({path:path.join(assets,'screenshots/01-triage-MOCK.png'),fullPage:true});
  await page.setViewportSize({width:390,height:900});await page.screenshot({path:path.join(assets,'screenshots/02-hunter-mobile-MOCK.png'),fullPage:true});await page.setViewportSize({width:1280,height:720});
  await page.locator('#logout').click();await login('admin');await page.getByRole('button',{name:'Ringkasan observasi',exact:true}).click();await page.getByText(/Observasi 1: HTTP GET/).waitFor();await sleep(2000);
  const text=await page.locator('#dialog-body').innerText();for(const secret of ['INTERNAL_NOTE','PRIVATE_MODEL','PRIVATE_DOM','PRIVATE_EVALUATOR_LABEL','secret-only-fixture'])assert(!text.includes(secret));
  await page.screenshot({path:path.join(assets,'screenshots/03-observations-SYNTHETIC.png'),fullPage:true});await sleep(1500);
  await context.close();await video.saveAs(path.join(assets,'demo-preview-MOCK.webm'));assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  result={...result,status:'PASS',thumbnail:{width:1200,height:630,bytes:png.length},slide_count:9,screenshot_count:3,
   video_status:'DRAFT_MOCK_PREVIEW_WITHOUT_NARRATION_NOT_SUBMISSION_VIDEO',page_errors:errors,blocked_external:external};
 }finally{
  server.stdin.end('stop\n');await closed;await browser.close();
  const summary=stdout.split(/\r?\n/).find(l=>l.startsWith('QA_FINAL '));result.qa=summary?JSON.parse(summary.slice(9)):null;
  fs.writeFileSync(path.join(artifacts,'capture-result.json'),JSON.stringify(result,null,2)+'\n');if(result.status!=='PASS')process.exitCode=1;
 }
 console.log(JSON.stringify({status:result.status,thumbnail:result.thumbnail,screenshots:result.screenshot_count,output:assets}));
})().catch(e=>{console.error(e.message);process.exitCode=1;});
