"use strict";
const $ = (q, root = document) => root.querySelector(q);
const state = {user:null, programs:[], program:null, conversation:null, run:null, csrf:"", timer:null, pollVersion:0, viewVersion:0, authVersion:0, drafts:new Map(), busy:false};
const active = r => r && ["QUEUED", "LEASED"].includes(r.queue_status);
function node(tag, text, cls) { const n = document.createElement(tag); if (text !== undefined) n.textContent = text; if (cls) n.className = cls; return n; }
function button(text, action, cls="secondary-button") { const b=node("button",text,cls); b.type="button"; b.addEventListener("click",()=>guard(action)); return b; }
function iconize() { document.querySelectorAll("[data-icon]").forEach(n=>{const key=n.dataset.icon;if(icons[key]){const svg=document.createElementNS("http://www.w3.org/2000/svg","svg");svg.setAttribute("viewBox","0 0 24 24");svg.setAttribute("aria-hidden","true");svg.innerHTML=icons[key];n.replaceChildren(svg);}}); }
function notice(text) { $("#notification").textContent=text; }
async function guard(action) {try{return await action();}catch(e){if(!e.stale)notice(e.message || "Permintaan gagal.");}}
async function api(path, options={}) {
  const authVersion=state.authVersion;
  const headers = {...options.headers};
  if(options.body && !(options.body instanceof FormData)) headers["Content-Type"]="application/json";
  if(options.method && options.method!=="GET") headers["X-CSRF-Token"]=state.csrf;
  let response;
  try { response=await fetch(path,{...options,headers,credentials:"same-origin",cache:"no-store"}); }
  catch {throw Error("Koneksi aplikasi gagal. Muat ulang status sebelum mencoba kembali.");}
  const data=await response.json();
  if(authVersion!==state.authVersion)throw Object.assign(Error("Sesi sudah berubah."),{stale:true});
  if(!response.ok){if(response.status===401) logoutView();const details=Array.isArray(data.field_errors)?data.field_errors.map(e=>e.message).filter(m=>typeof m==="string").join(" "):"";throw Error(`${data.message || "Permintaan ditolak"}${details?" "+details:""} (${data.error_code || response.status})`);}
  return data;
}
function stopPoll(){clearTimeout(state.timer);state.timer=null;state.pollVersion++;}
function logoutView(){stopPoll();triageUI.reset(true);state.authVersion++;state.user=null;state.program=null;state.programs=[];state.csrf="";state.conversation=null;state.run=null;state.drafts.clear();$("#message-input").value="";$("#conversation-list").replaceChildren();$("#chat-content").replaceChildren();$("#detail-dialog").close();$("#dialog-body").replaceChildren();$("#app-shell").inert=true;$("#logout").hidden=true;if(!$("#login-dialog").open)$("#login-dialog").showModal();}
function field(form,label,value="",type="text") {const group=node("div",undefined,"form-group");const id="field-"+crypto.randomUUID();const l=node("label",label);l.htmlFor=id;const input=node(type==="textarea"?"textarea":"input");input.id=id;if(type!=="textarea") input.type=type;input.value=value;group.append(l,input);form.append(group);return input;}
function select(form,label,choices,value) {const group=node("div",undefined,"form-group"),id="field-"+crypto.randomUUID(),l=node("label",label),s=node("select");l.htmlFor=id;s.id=id;choices.forEach(([v,t])=>{const o=node("option",t);o.value=v;s.append(o);});s.value=value;group.append(l,s);form.append(group);return s;}
function panel(title,content,kicker="ValVuln AI") {$("#dialog-title").textContent=title;$("#dialog-kicker").textContent=kicker;$("#dialog-body").replaceChildren(content);if(!$("#detail-dialog").open)$("#detail-dialog").showModal();}
function saveUnsent(){if(state.conversation)state.drafts.set(state.conversation.conversation_id,$("#message-input").value);}
function own(){return state.conversation?.owner_user_id===state.user?.user_id;}
function closeNav(){ $(".sidebar").classList.remove("is-open");$("#sidebar-scrim").hidden=true;$(".workspace-main").inert=false;$("#sidebar-open").setAttribute("aria-expanded","false");}
async function chooseProgram(program){saveUnsent();stopPoll();triageUI.reset();const version=++state.viewVersion;state.program=program;state.conversation=null;state.run=null;triageUI.badge();$(".program-name").textContent=program.display_name;$("#account-role").textContent=program.role==="PROGRAM_ADMIN"?"Admin program":"Bug hunter";$("#admin-nav").hidden=program.role!=="PROGRAM_ADMIN";$("#history-label").textContent=program.role==="PROGRAM_ADMIN"?"Laporan program":"Laporan saya";await history();if(version===state.viewVersion)welcome();}
async function history(){if(!state.program)return;const programId=state.program.program_id,version=state.viewVersion;const rows=await api(`/api/programs/${programId}/conversations`);if(version!==state.viewVersion||programId!==state.program?.program_id)return;const list=$("#conversation-list");list.replaceChildren();const query=$("#history-query").value.toLowerCase();rows.filter(r=>(r.draft_title||"Draf baru").toLowerCase().includes(query)).forEach(r=>{const b=button(r.draft_title||"Draf baru",()=>openConversation(r.conversation_id),"conversation-item");b.classList.toggle("selected",r.conversation_id===state.conversation?.conversation_id);list.append(b);});}
function welcome(){const area=$("#chat-content");area.replaceChildren();const box=node("div",undefined,"welcome");box.append(node("h1","Laporan apa yang ingin diperiksa?"),node("p","Kirim teks atau lampiran TXT/MD untuk menyimpan draf. Minta saran AI dan Validasi snapshot merupakan tindakan terpisah."),node("p",`Lab sintetis lokal · triage ${triageUI.readiness?.triage_mode||"belum diketahui"} · planner ${triageUI.readiness?.lab_planner_mode||"belum diketahui"}.`));box.append(button("Buat laporan",newConversation,"primary-button"));area.append(box);$("#composer-region").hidden=true;}
async function newConversation(){saveUnsent();stopPoll();const version=++state.viewVersion;const c=await api(`/api/programs/${state.program.program_id}/conversations`,{method:"POST"});if(version!==state.viewVersion)return;await openConversation(c.conversation_id,version);}
async function openConversation(id,requestedVersion){saveUnsent();stopPoll();triageUI.reset();const version=requestedVersion??++state.viewVersion;const c=await api(`/api/conversations/${id}`);if(version!==state.viewVersion)return;state.conversation=c;state.run=null;$("#message-input").value=state.drafts.get(id)||"";renderConversation();await history();if(version!==state.viewVersion)return;closeNav();await triageUI.mount(c,version);if(version===state.viewVersion&&c.run_ids.length)await loadRun(c.run_ids[0]);}
function renderConversation(){const c=state.conversation,area=$("#chat-content");area.replaceChildren();const heading=node("div",undefined,"chat-heading");heading.append(node("h1",c.draft_title||"Draf laporan"));area.append(heading);c.messages.forEach(m=>{const box=node("article",undefined,"message");box.append(node("div","Laporan · tersimpan", "message-author"),node("div",m.body,"user-bubble"));area.append(box);});if(c.attachment){const box=node("div",`Lampiran tersimpan: ${c.attachment.original_name} · ${c.attachment.byte_size} byte`,"attachment-preview");area.append(box);}if(!c.messages.length&&!c.attachment)area.append(node("p","Tulis laporan di bawah, lalu tekan Kirim untuk menyimpannya."));
 const actions=node("div",undefined,"draft-actions");if(own()){actions.append(button("Validasi snapshot",validation,"primary-button"));actions.append(button("Siapkan review bukti bisnis",businessSnapshot));}else actions.append(node("p","Draf milik pelapor; admin meninjau hasil tanpa mengubah draf."));
 if(c.run_ids.length>1){const list=node("div",undefined,"draft-actions");c.run_ids.forEach((id,i)=>list.append(button(`Run ${c.run_ids.length-i}`,()=>loadRun(id))));area.append(list);}area.append(actions,node("div",undefined,"triage-area"),node("div",undefined,"run-area"),node("div",undefined,"business-area"));$("#composer-region").hidden=!own();$("#attachment-preview").hidden=true;guard(()=>loadBusinessRecords(c,state.viewVersion));
}

function businessSnapshot(){
 const c=state.conversation,form=node("form");form.append(node("p","Simpan snapshot untuk review rekaman oleh admin. Langkah ini tidak menjalankan worker, model atau pengujian target."));
 const claim=field(form,"Klaim bisnis yang akan ditinjau",c.latest_claim?.category==="BUSINESS_LOGIC"?c.latest_claim.primary_claim:"Pemenuhan barang harus mengikuti persetujuan dan hanya mengurangi stok sekali");claim.required=true;
 const asset=field(form,"Alias aset laporan",c.latest_claim?.asset_alias||"portal"),path=field(form,"Path fitur yang dilaporkan",c.latest_claim?.category==="BUSINESS_LOGIC"?c.latest_claim.path||"/api/requests/":"/api/requests/");
 const error=node("p",undefined,"composer-error");error.role="alert";const submit=node("button","Simpan snapshot untuk review","primary-button");submit.type="submit";form.append(error,submit);
 form.addEventListener("submit",async event=>{event.preventDefault();submit.disabled=true;try{await api(`/api/conversations/${c.conversation_id}/reports`,{method:"POST",body:JSON.stringify({expected_draft_version:c.draft_version,claim:{category:"BUSINESS_LOGIC",primary_claim:claim.value,asset_alias:asset.value||null,path:path.value||null,method:"POST",account_aliases:[]}})});$("#detail-dialog").close();if(state.conversation?.conversation_id===c.conversation_id)await openConversation(c.conversation_id);notice("Snapshot bisnis tersimpan. Admin dapat mengunggah rekaman untuk review; pengujian target belum dimulai.");}catch(e){error.textContent=e.message;}finally{submit.disabled=false;}});
 panel("Siapkan review bukti bisnis",form,"Snapshot laporan · tanpa pengujian otomatis");
}

async function loadBusinessRecords(c,version){
 const rows=c.report_id?await api(`/api/reports/${c.report_id}/business-records`):[];
 if(version!==state.viewVersion||state.conversation?.conversation_id!==c.conversation_id)return;
 const area=$(".business-area");if(!area)return;area.replaceChildren();const admin=state.program.role==="PROGRAM_ADMIN";
 if(c.latest_claim?.category!=="BUSINESS_LOGIC"&&!rows.length)return;
 area.append(node("h2","Review rekaman bisnis"),node("p","Rekaman unggahan diperiksa konsistensinya. Ini bukan pengujian target atau keputusan kerentanan.","fine-print"));
 if(admin&&c.latest_claim?.category==="BUSINESS_LOGIC"&&c.latest_report_revision_id)area.append(button("Unggah rekaman JSON",()=>businessImport(c)));
 if(!rows.length)area.append(node("p",admin?"Belum ada rekaman. Unggah JSON kontrol alur normal untuk ditinjau.":"Snapshot tersimpan. Ringkasan akan tampil setelah admin meninjau dan membagikannya."));
 rows.forEach(row=>{
  const card=node("article",undefined,"assessment-card"),body=node("div",undefined,"assessment-content");body.append(node("h3",admin?`Konsistensi rekaman: ${row.result.status}`:"Ringkasan review rekaman"),node("p",`Snapshot laporan: versi ${row.report_revision_number}`),node("p",row.summary||"Rekaman internal; belum dibagikan ke pelapor."));
  const actions=node("div",undefined,"draft-actions");actions.append(button("Ekspor review rekaman",()=>downloadBusinessReview(row)));
  if(admin){body.append(node("p",`Status review: ${row.review_status} · publikasi: ${row.publication_status}`),node("p",`SHA-256 rekaman: ${row.record_sha256}`),node("p",row.reviewer_note||"Belum ada catatan review."));const detail=node("details");detail.append(node("summary","Hasil konsistensi dan asal rekaman"),node("pre",JSON.stringify({result:row.result,provenance:row.provenance},null,2)));body.append(detail);
   actions.append(button("Lihat rekaman unggahan",async()=>{const record=await api(`/api/business-records/${row.review_id}/record`);panel("Rekaman unggahan",node("pre",JSON.stringify(record,null,2)),"Data unggahan · asal dan izin aktor belum disahkan");}));
   actions.append(button("Tinjau rekaman",()=>businessReview(c,row)));
   actions.append(button("Langkah berikutnya",()=>businessWorkflow(row)));
   if(row.review_status==="REVIEWED")actions.append(button("Bagikan ringkasan rekaman",async()=>{await api(`/api/business-records/${row.review_id}/publish`,{method:"POST"});if(state.conversation?.conversation_id===c.conversation_id)await loadBusinessRecords(state.conversation,state.viewVersion);notice("Ringkasan rekaman dibagikan; catatan dan data mentah tetap internal.");}));
  }body.append(actions);card.append(body);area.append(card);
 });
}

function businessImport(c){
 const form=node("form");form.append(node("p","Unggah JSON kontrol normal empat event, maksimal 128 KiB. Versi aturan guideline aktif harus procurement-controls-v1. Data ini dilampirkan ke snapshot laporan; keaslian sumber dan izin aktor belum dibuktikan."));
 const file=field(form,"File rekaman bisnis","","file");file.accept=".json,application/json";file.required=true;const error=node("p",undefined,"composer-error");error.role="alert";const submit=node("button","Periksa dan simpan rekaman","primary-button");submit.type="submit";form.append(error,submit);
 form.addEventListener("submit",async event=>{event.preventDefault();submit.disabled=true;error.textContent="";try{const selected=file.files[0];if(!selected||selected.size>131072)throw Error("Pilih file JSON maksimal 128 KiB.");const data=new FormData();data.append("file",selected);await api(`/api/reports/${c.report_id}/revisions/${c.latest_report_revision_id}/business-records`,{method:"POST",body:data});$("#detail-dialog").close();if(state.conversation?.conversation_id===c.conversation_id)await loadBusinessRecords(state.conversation,state.viewVersion);notice("Rekaman tersimpan untuk review; tidak ada request target atau model.");}catch(e){error.textContent=e.message;}finally{submit.disabled=false;}});
 panel("Unggah rekaman bisnis",form,"Hanya admin · hasil konsistensi, bukan verdict kerentanan");
}

function businessReview(c,row){
 const form=node("form");form.append(node("p","Tinjau konsistensi dan sumber rekaman. Catatan ini tidak menetapkan CONFIRMED/REFUTED dan tidak dibagikan ke pelapor."));const note=field(form,"Catatan review rekaman",row.reviewer_note||"","textarea");note.required=true;note.maxLength=2000;const error=node("p",undefined,"composer-error");error.role="alert";const submit=node("button","Simpan review rekaman","primary-button");submit.type="submit";form.append(error,submit);
 form.addEventListener("submit",async event=>{event.preventDefault();submit.disabled=true;try{await api(`/api/business-records/${row.review_id}/review`,{method:"POST",body:JSON.stringify({reviewer_note:note.value})});$("#detail-dialog").close();if(state.conversation?.conversation_id===c.conversation_id)await loadBusinessRecords(state.conversation,state.viewVersion);notice("Review tersimpan. Publikasi sebelumnya ditarik; bagikan kembali setelah siap.");}catch(e){error.textContent=e.message;}finally{submit.disabled=false;}});panel("Tinjau rekaman bisnis",form,"Catatan admin · tanpa perubahan hasil mentah");
}

function downloadBusinessReview(row){const url=URL.createObjectURL(new Blob([JSON.stringify(row,null,2)],{type:"application/json"}));const link=node("a");link.href=url;link.download=`valvuln-business-review-${row.review_id}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}

async function businessWorkflow(row){
 const context=await api(`/api/business-records/${row.review_id}/workflow`),box=node("div");
 box.append(node("p",context.summary),node("p",`Konteks memakai snapshot laporan versi ${context.binding.report_revision_number} dan aturan yang terikat pada rekaman.`));
 const steps=node("ol");context.next_actions.forEach(action=>steps.append(node("li",action.instruction)));box.append(steps);
 box.append(node("p","Langkah ini perlu ditinjau admin. Tidak ada pengujian target, panggilan model atau keputusan kerentanan yang dijalankan.","fine-print"));
 const detail=node("details");detail.append(node("summary","Konteks terstruktur untuk integrasi berikutnya"),node("pre",JSON.stringify(context,null,2)));box.append(detail);
 box.append(button("Ekspor konteks review",()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(context,null,2)],{type:"application/json"}));const link=node("a");link.href=url;link.download=`valvuln-business-context-${row.review_id}.json`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}));
 panel("Langkah berikutnya",box,"Workflow bukti · hanya admin program");
}
async function sendMessage(event){event?.preventDefault();if(state.busy)return;state.busy=true;$("#send-button").disabled=true;try{if(!state.conversation)await newConversation();const text=$("#message-input").value;if(!text.trim())return;const c=state.conversation;await api(`/api/conversations/${c.conversation_id}/messages`,{method:"POST",body:JSON.stringify({body:text,title:c.draft_title||text.slice(0,80),expected_draft_version:c.draft_version})});state.drafts.delete(c.conversation_id);$("#message-input").value="";await openConversation(c.conversation_id);notice("Pesan tersimpan. Validasi belum dimulai.");}finally{state.busy=false;$("#send-button").disabled=false;}}
async function upload(){const file=$("#file-input").files[0];if(!file||!state.conversation)return;const data=new FormData();data.append("file",file);await api(`/api/conversations/${state.conversation.conversation_id}/attachments`,{method:"POST",body:data});await openConversation(state.conversation.conversation_id);notice("Lampiran tersimpan; belum diuji.");$("#file-input").value="";}
async function validation(proposal=null){const c=state.conversation;if(proposal&&(proposal.conversation_id!==c?.conversation_id||proposal.expected_draft_version!==c.draft_version))throw Error("Draf berubah. Muat ulang saran AI.");const form=node("form");const help=node("p");form.append(help);
 const prev=proposal?.claim||c.latest_claim||{};
 if(proposal){form.prepend(node("p",`Draf dari saran ${proposal.mode.toUpperCase()} · scope backend: ${proposal.scope_decision} · ${proposal.policy_status}. Periksa semua field sebelum memulai.`));if(proposal.missing_information.length){const list=node("ul");proposal.missing_information.forEach(text=>list.append(node("li",text)));form.append(list);}}
 const kind=select(form,"Kemampuan validasi",[["BAC","BAC · hapus lampiran lintas akun"],["XSS","XSS · pratinjau notifikasi (fixture tetap)"],["UPLOAD","Upload · nama lampiran (fixture tetap)"]],["BAC","XSS","UPLOAD"].includes(prev.category)?prev.category:"BAC");
 const claim=field(form,"Klaim utama",prev.primary_claim||"Akun penguji dapat menghapus lampiran milik akun lain");
 const asset=field(form,"Alias aset terdaftar",prev.asset_alias||"portal");
 const victim=field(form,"Path lampiran korban (milik akun kedua)",prev.path||"/api/attachments/");
 const control=field(form,"Path lampiran kontrol (milik akun pertama)",prev.control_path||"/api/attachments/");
 const account=select(form,"Akun penguji → akun pemilik korban",[["requester-a","requester-a → requester-b"],["requester-b","requester-b → requester-a"]],prev.account_aliases?.[0]||"requester-a");
 const mode=select(form,"Pelaksanaan tools",[["LAB","Lab aktual · planner mock"],["NONE","Simulasi plumbing · tanpa request target"]],"LAB");
 const bacDraft={path:prev.category&&prev.category!=="BAC"?"/api/attachments/":victim.value,claim:prev.category&&prev.category!=="BAC"?"Akun penguji dapat menghapus lampiran milik akun lain":claim.value};
 const uploadDraft={path:prev.category==="UPLOAD"?prev.path:"/requests/",claim:prev.category==="UPLOAD"?prev.primary_claim:"Nama fixture upload dapat mengeksekusi marker pada daftar lampiran"};let lastKind=kind.value;
 const xssClaim="Fixture marker dapat mengeksekusi JavaScript pada pratinjau notifikasi";
 function capabilityChanged(initial=false){const xss=kind.value==="XSS",upload=kind.value==="UPLOAD";if(!initial){const draft=lastKind==="BAC"?bacDraft:lastKind==="UPLOAD"?uploadDraft:null;if(draft){draft.path=victim.value;draft.claim=claim.value;}}if(xss){victim.value="/notifications/preview";if(!initial||!prev.primary_claim)claim.value=xssClaim;}else if(upload){victim.value=uploadDraft.path;claim.value=uploadDraft.claim;}else if(!initial){victim.value=bacDraft.path;claim.value=bacDraft.claim;}lastKind=kind.value;
   victim.readOnly=xss;victim.parentElement.querySelector("label").textContent=upload?"Path daftar lampiran permintaan milik A (/requests/ID/attachments)":xss?"Rute pratinjau terdaftar":"Path lampiran korban (milik akun kedua)";control.parentElement.hidden=xss||upload;control.disabled=xss||upload;account.parentElement.hidden=xss||upload;
   help.textContent=upload?"Sistem mengunggah dua fixture teks kecil dengan nama kontrol/marker, lalu membaca daftar melalui akun B yang ditugaskan. File laporan tidak dieksekusi. Isi berkas dan penimpaan tidak diuji pada run ini; operator perlu reset.":xss?"Kontrol inert dan marker tetap diuji di dua akun melalui browser lab. Payload laporan tidak dijalankan; verdict hanya untuk fixture dan rute ini. Operator perlu reset sebelum run berikutnya.":"Satu klaim utama: penghapusan lampiran lintas akun. HTTP lab akan benar-benar mengubah data sintetis, termasuk objek kontrol. Operator perlu reset sebelum run berikutnya.";
 }kind.addEventListener("change",()=>capabilityChanged());capabilityChanged(true);
 const error=node("p",undefined,"composer-error");error.role="alert";
 const submit=node("button","Mulai validasi snapshot","primary-button");submit.type="submit";form.append(error,submit);
 const key=crypto.randomUUID();
 form.addEventListener("submit",async e=>{e.preventDefault();submit.disabled=true;error.textContent="";try{
   const xss=kind.value==="XSS",upload=kind.value==="UPLOAD";
   const snapshot=await api(`/api/conversations/${c.conversation_id}/reports`,{method:"POST",body:JSON.stringify({expected_draft_version:c.draft_version,source_triage_id:proposal?.source_triage_id||null,claim:{asset_alias:asset.value||null,path:xss?"/notifications/preview":victim.value||null,control_path:xss||upload?null:control.value||null,method:xss||upload?"GET":"DELETE",category:kind.value,account_aliases:xss||upload?["requester-a","requester-b"]:[account.value,account.value==="requester-a"?"requester-b":"requester-a"],primary_claim:claim.value,claim_count:prev.claim_count||1}})});
   const run=await api(`/api/reports/${snapshot.report_id}/runs`,{method:"POST",headers:{"Idempotency-Key":key},body:JSON.stringify({report_revision_id:snapshot.report_revision_id,execution_mode:"mock",tool_execution_mode:mode.value})});
   $("#detail-dialog").close();await openConversation(c.conversation_id);await loadRun(run.run_id);
 }catch(e){error.textContent=e.message;}finally{submit.disabled=false;}});panel("Validasi snapshot",form,"Kirim menyimpan draf; Validasi memulai run");}
async function loadRun(id){stopPoll();const version=state.pollVersion,conversationId=state.conversation?.conversation_id;const run=await api(`/api/runs/${id}`);if(version!==state.pollVersion||conversationId!==state.conversation?.conversation_id)return;state.run=run;renderRun();if(active(run)&&!document.hidden)state.timer=setTimeout(()=>guard(()=>loadRun(id)),2000);}
function renderRun(){const run=state.run,area=$(".run-area");if(!area)return;area.replaceChildren();const card=node("article",undefined,"assessment-card");card.append(node("div",`${run.process_status} · ${run.execution_mode} / tools ${run.tool_execution_mode}`,"assessment-top"));const body=node("div",undefined,"assessment-content");body.append(node("p",`Scope: ${run.scope_decision} · kemampuan: ${run.capability_decision}`),node("p",`Request target: ${run.counters.target_requests} · model calls: ${run.counters.model_calls}`));
 if(run.claim_origin)body.append(node("p",`Klaim dari saran ${run.claim_origin.mode.toUpperCase()} · ${run.claim_origin.provider} · model diminta ${run.claim_origin.requested_model}; dikonfirmasi pemilik laporan.`,"fine-print"));
 if(run.error_code)body.append(node("p",`Alasan: ${run.error_code}`,"composer-error"));
 if(run.assessment){const a=run.assessment.system_verified||run.assessment;body.append(node("h2",a.verdict,"assessment-title"),node("p",a.reasoning||a.summary));if(run.assessment.analyst_override)body.append(node("p",`Keputusan analis: ${run.assessment.analyst_override}`));}
 else if(run.awaiting_review)body.append(node("p","Pengujian selesai; ringkasan menunggu review dan publikasi admin."));
 if(run.tool_execution_mode==="LAB")body.append(node("p",run.validation_kind==="UPLOAD"?"Planner mock; upload fixture dan browser lab aktual. Bukan hasil model live.":run.validation_kind==="XSS"?"Planner mock; bukti browser lab aktual dengan fixture tetap. Bukan hasil model live.":"Planner mock; bukti HTTP lab aktual. Bukan hasil model live.","fine-print"));
 const actions=node("div",undefined,"draft-actions");if(active(run))actions.append(button("Batalkan run",async()=>{await api(`/api/runs/${run.run_id}/cancel`,{method:"POST"});await loadRun(run.run_id);}));
 actions.append(button("Ekspor JSON",()=>exportRun(run.run_id)));
 actions.append(button("Ringkasan observasi",()=>showObservationSummary(run)));
 if(state.program.role==="PROGRAM_ADMIN"&&run.assessment){actions.append(button("Review hasil",()=>review(run)));actions.append(button("Bagikan ringkasan",async()=>{await api(`/api/runs/${run.run_id}/publish`,{method:"POST"});await loadRun(run.run_id);notice("Ringkasan aman dibagikan ke pelapor.");}));const raw=node("details");raw.append(node("summary","Hasil mentah dan assessment verifier"),node("pre",JSON.stringify(run.assessment,null,2)));body.append(raw);}
 if(run.evidence?.length){const list=node("div",undefined,"draft-actions");run.evidence.forEach((e,i)=>list.append(button(`Bukti ${i+1}`,async()=>{const data=await api(`/api/evidence/${e.evidence_id}`);panel("Bukti internal",node("pre",JSON.stringify(data,null,2)),"Hanya admin program · respons ditampilkan sebagai teks");})));body.append(list);}body.append(actions);card.append(body);area.append(card);}
async function exportRun(id){const data=await api(`/api/runs/${id}/export`);const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:"application/json"}));const a=node("a");a.href=url;a.download=`valvuln-${id}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function review(run){const form=node("form"),choice=select(form,"Keputusan analis (hasil mentah tetap tersimpan)",[["","Ikuti verifier"],["CONFIRMED","CONFIRMED"],["REFUTED","REFUTED"],["INCONCLUSIVE","INCONCLUSIVE"]],run.assessment.analyst_override||"");const note=field(form,"Catatan review internal",run.assessment.reviewer_note||"","textarea");note.required=true;const submit=node("button","Simpan review","primary-button");submit.type="submit";form.append(submit);form.addEventListener("submit",e=>{e.preventDefault();guard(async()=>{await api(`/api/runs/${run.run_id}/review`,{method:"POST",body:JSON.stringify({analyst_override:choice.value||null,reviewer_note:note.value})});$("#detail-dialog").close();await loadRun(run.run_id);});});panel("Review hasil",form,"Catatan internal tidak dibagikan ke pelapor");}
function guidelineRules(value){let parsed;try{parsed=JSON.parse(value);}catch{throw Error("Aturan scope terstruktur: JSON tidak sah. Salin objek JSON tanpa penanda ``` dan periksa tanda kutip/kurung/koma.");}if(!parsed||typeof parsed!=="object"||Array.isArray(parsed))throw Error("Aturan scope terstruktur harus berupa objek JSON.");return parsed;}
async function guidelines(edit=false){const g=await api(`/api/programs/${state.program.program_id}/guidelines`);const box=node("div");box.append(node("p",`Status: ${g.state} · versi ${g.version||"belum aktif"}`),node("pre",g.source_text||"Admin perlu membuat dan mengaktifkan guideline."));if(g.rules)box.append(node("pre",JSON.stringify(g.rules,null,2)));
 if(edit&&state.program.role==="PROGRAM_ADMIN"){const form=node("form"),source=field(form,"Teks guideline",g.source_text||"","textarea"),rules=field(form,"Aturan scope terstruktur (JSON)",JSON.stringify(g.rules||{in_scope_rules:[],out_of_scope_rules:[],business_rules:""},null,2),"textarea");source.required=true;rules.required=true;form.append(node("p","Isi kedua kolom: teks guideline yang dapat dibaca dan objek JSON aturan scope. Simpan draf tidak langsung mengaktifkan aturan."));const submit=node("button","Simpan draf guideline","primary-button");submit.type="submit";form.append(submit);form.addEventListener("submit",e=>{e.preventDefault();guard(async()=>{if(!source.value.trim())throw Error("Teks guideline wajib diisi; kolom JSON saja belum cukup.");const parsed=guidelineRules(rules.value);const draft=await api(`/api/programs/${state.program.program_id}/scope-drafts`,{method:"POST",body:JSON.stringify({...parsed,source_text:source.value})});notice(`Draf v${draft.version} tersimpan; belum aktif.`);await guidelines(true);});});box.append(form);const drafts=await api(`/api/programs/${state.program.program_id}/scope-drafts`);drafts.forEach(d=>box.append(button(`Aktifkan draf v${d.version}`,async()=>{await api(`/api/programs/${state.program.program_id}/scope-drafts/${d.scope_version_id}/activate`,{method:"POST"});notice("Scope diaktifkan; run lama dihentikan.");await guidelines(true);})));}panel(edit?"Guideline program":"Scope program",box);}
async function labResetPanel(){
 const programId=state.program.program_id,authVersion=state.authVersion;
 const current=await api(`/api/programs/${programId}/lab-reset`);
 if(programId!==state.program?.program_id||authVersion!==state.authVersion)return;
 const box=node("div");box.append(node("p","Pilih kondisi lab untuk membandingkan pengujian yang sama. Mode kontrol diperbaiki memakai konfigurasi pembanding yang sudah disiapkan, bukan perbaikan oleh AI. Verdict tetap dihitung dari bukti."),node("p","Reset mengganti data sintetis dan ID objek lab. Laporan, bukti dan ledger tetap tersimpan. Gunakan ID baru untuk laporan BAC/upload; tunggu atau batalkan validasi aktif sebelum reset."));
 const condition=select(box,"Kondisi target setelah reset",[["vulnerable","Lab rentan"],["fixed","Lab kontrol diperbaiki"]],current.applied_condition||"vulnerable");
 const conditionLabel=value=>value==="fixed"?"Lab kontrol diperbaiki":value==="vulnerable"?"Lab rentan":"Belum tercatat untuk snapshot ini";
 const applied=node("p");box.append(applied);
 const status=node("p"),objects=node("pre"),error=node("p",undefined,"composer-error");status.role="status";error.role="alert";
 const manual=button("Aktifkan pengujian manual",async()=>{
  manual.disabled=true;error.textContent="";
  try{await api(`/api/programs/${programId}/lab-manual-session`,{method:"POST",body:JSON.stringify({confirm:"OPEN_SHARED_MANUAL_LAB"})});render(await api(`/api/programs/${programId}/lab-reset`));}
  catch(e){error.textContent=e.message;manual.disabled=false;}
 });
 const manualLink=node("a","Buka lab manual di port 8001","secondary-button");manualLink.href="http://127.0.0.1:8001/";manualLink.target="_blank";manualLink.rel="noopener noreferrer";manualLink.hidden=true;
 const reset=button("Terapkan kondisi & reset data lab",async()=>{
  reset.disabled=true;condition.disabled=true;error.textContent="";status.textContent="Menyiapkan ulang data lab…";
  try{const result=await api(`/api/programs/${programId}/lab-reset`,{method:"POST",body:JSON.stringify({confirm:"RESET_DEMO_LAB",condition:condition.value})});render(result);await poll();}
  catch(e){error.textContent=e.message;reset.disabled=false;condition.disabled=false;}
 },"primary-button");
 function render(result){
  reset.disabled=!current.configured||result.status==="RUNNING";
  condition.disabled=reset.disabled;
  manual.disabled=!current.manual_available||result.status==="RUNNING"||!!result.manual_active;
  manualLink.hidden=!result.manual_active;
  const installed=result.applied_condition??(result.status==="SUCCEEDED"&&!result.target?result.condition:null);
  const coverage=result.applied_coverage??(!result.target&&result.status==="SUCCEEDED"?result.coverage:null);
  applied.textContent=`Kondisi terpasang: ${conditionLabel(installed)}. ${coverage==="ALL_IMPLEMENTED"?"Berlaku untuk seluruh 13 titik lab yang sudah diimplementasikan, termasuk pencarian katalog.":"Reset lama hanya mencakup sebagian fitur; terapkan ulang kondisi untuk seluruh titik lab."} Validasi otomatis agent tetap BAC-08, XSS-08 dan UP-04.`;
  const needsReset=result.target&&(result.target.dirty||result.target.maintenance||!result.target.ready);
  status.textContent=result.manual_active?"Pengujian manual aktif pada target worker yang sama. Validasi agent dikunci. Setelah selesai, terapkan kondisi dan reset data untuk membuka validasi kembali.":result.status==="RUNNING"?`Menerapkan ${conditionLabel(result.condition)}. Menunggu health dan sinkronisasi worker…`:result.status==="SUCCEEDED"&&!needsReset?`Lab siap. Kondisi terpasang: ${conditionLabel(installed)}. Lo bisa mulai validasi lagi.`:result.status==="FAILED"?`Reset belum berhasil (${result.error_code||"RESET_FAILED"}). Target tetap terkunci; periksa operator sebelum mencoba kembali.`:`Status target: ${needsReset?"perlu reset":result.target?.ready?"siap":"belum siap"}.`;
  objects.textContent=result.objects?JSON.stringify(result.objects,null,2):"";objects.hidden=!result.objects;
 }
 async function poll(){
  for(let i=0;i<60;i++){
   await new Promise(resolve=>setTimeout(resolve,1000));
   if(authVersion!==state.authVersion||programId!==state.program?.program_id||!$("#detail-dialog").open||!box.isConnected)return;
   const result=await api(`/api/programs/${programId}/lab-reset`);render(result);
   if(result.status!=="RUNNING"){await triageUI.status();return;}
  }
  error.textContent="Status belum selesai. Tutup lalu buka panel ini untuk memeriksa kembali; jangan mengirim reset berulang.";
 }
 if(!current.configured)error.textContent="Reset UI belum diaktifkan pada instalasi ini.";
 box.append(status,node("p","Port 8001 sekarang membuka target yang sama dengan worker. Aktifkan pengujian manual terlebih dahulu; selama sesi ini validasi agent dikunci."),manual,manualLink,objects,error,reset);panel("Kondisi dan reset lab",box,"Admin program · kontrol pengujian lab");render(current);
 if(current.status==="RUNNING")await poll();
}
async function boot(){const me=await api("/api/me");state.user=me;state.csrf=me.csrf_token;state.programs=await api("/api/programs");await triageUI.status();$("#login-dialog").close();$("#app-shell").inert=false;$("#logout").hidden=false;$("#account-name").textContent=me.login_name;if(!state.programs.length){notice("Akun tidak mempunyai keanggotaan program aktif.");return;}await chooseProgram(state.programs[0]);}
$("#login-form").addEventListener("submit",e=>{e.preventDefault();guard(async()=>{const b=$("#login-form button");b.disabled=true;try{state.csrf=(await api("/api/auth/csrf")).csrf_token;await api("/api/auth/login",{method:"POST",body:JSON.stringify({login_name:$("#login-name").value,password:$("#login-password").value})});$("#login-password").value="";$("#login-error").textContent="";await boot();}catch(error){$("#login-error").textContent=error.message;}finally{b.disabled=false;}});});
$("#login-dialog").addEventListener("cancel",e=>e.preventDefault());
$("#logout").addEventListener("click",()=>guard(async()=>{await api("/api/auth/logout",{method:"POST"});logoutView();}));
$("#new-report").addEventListener("click",()=>guard(newConversation));
$("#composer-form").addEventListener("submit",e=>guard(()=>sendMessage(e)));
$("#message-input").addEventListener("input",()=>{saveUnsent();triageUI.render();});
$("#message-input").addEventListener("keydown",e=>{if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();guard(()=>sendMessage());}});
$("#attach-button").addEventListener("click",()=>$("#file-input").click());$("#file-input").addEventListener("change",()=>guard(upload));
$("#detail-dialog").addEventListener("close",()=>{if(state.user)$("#scope-button").focus();});$("#dialog-close").addEventListener("click",()=>$("#detail-dialog").close());
[$("#scope-button"),$("#sidebar-guide")].forEach(b=>b.addEventListener("click",()=>guard(()=>guidelines())));
$("#model-info").addEventListener("click",()=>triageUI.info());
$("#workspace-switch").addEventListener("click",()=>{const box=node("div");state.programs.forEach(p=>box.append(button(p.display_name,async()=>{$("#detail-dialog").close();await chooseProgram(p);})));panel("Pilih program",box);});
$("[data-view=lab-reset]").addEventListener("click",()=>guard(labResetPanel));
$("[data-view=guidelines]").addEventListener("click",()=>guard(()=>guidelines(true)));$("[data-view=reports]").addEventListener("click",()=>guard(async()=>{await history();notice("Sidebar menampilkan laporan program yang diizinkan server.");}));
$("#theme-toggle").addEventListener("click",()=>{document.documentElement.dataset.theme=document.documentElement.dataset.theme==="light"?"dark":"light";});
$("#search-toggle").addEventListener("click",()=>{const input=$("#history-search");input.hidden=!input.hidden;$("#search-toggle").setAttribute("aria-expanded",String(!input.hidden));if(!input.hidden)$("#history-query").focus();});$("#history-query").addEventListener("input",()=>guard(history));
$("#sidebar-open").addEventListener("click",()=>{$(".sidebar").classList.add("is-open");$("#sidebar-scrim").hidden=false;$(".workspace-main").inert=true;$("#sidebar-close").focus();$("#sidebar-open").setAttribute("aria-expanded","true");});[$("#sidebar-close"),$("#sidebar-scrim")].forEach(b=>b.addEventListener("click",()=>{closeNav();$("#sidebar-open").focus();}));
document.addEventListener("visibilitychange",()=>{stopPoll();triageUI.visibility();if(!document.hidden&&active(state.run))guard(()=>loadRun(state.run.run_id));});
iconize();guard(boot);
