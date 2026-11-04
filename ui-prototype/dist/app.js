/* UI-only fixtures. No backend, authentication, LLM, fetch, or target access. */
"use strict";

const $ = (selector, root = document) => root.querySelector(selector);
const icons = {
  mark: '<path d="m3 6 5 12 5-12m-2 0 5 12 5-12"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  close: '<path d="m6 6 12 12M18 6 6 18"/>',
  box: '<path d="m12 3 9 5-9 5-9-5 9-5ZM3 8v9l9 5 9-5V8M12 13v9M7.5 5.5l9 5"/>',
  chevrons: '<path d="m9 8 3-3 3 3m-6 8 3 3 3-3"/>',
  search: '<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 4 4"/>',
  chat: '<path d="M20 11a8 8 0 0 1-8 8H5l-3 3V11a9 9 0 0 1 18 0Z"/>',
  book: '<path d="M12 5c-3-2-6-2-10-1v15c4-1 7-1 10 1 3-2 6-2 10-1V4c-4-1-7-1-10 1Zm0 0v15"/>',
  "arrow-up-right": '<path d="M7 17 17 7M7 7h10v10"/>',
  "arrow-right": '<path d="M4 12h16m-6-6 6 6-6 6"/>',
  "arrow-up": '<path d="M12 20V4m-6 6 6-6 6 6"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>',
  moon: '<path d="M20.5 14a8.5 8.5 0 0 1-10.5-10 8.5 8.5 0 1 0 10.5 10Z"/>',
  paperclip: '<path d="m8 12 6-6a3 3 0 0 1 4 4l-8 8a5 5 0 0 1-7-7l9-9m-3 13 7-7"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  file: '<path d="M14 2H5v20h14V7l-5-5Zm0 0v6h5M8 12h8m-8 4h6"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  "check-circle": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
  circle: '<circle cx="12" cy="12" r="8"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  lock: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 5v2"/>',
  more: '<circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/>',
  copy: '<rect x="8" y="8" width="12" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>',
  download: '<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
  inbox: '<path d="M5 3h14l3 12v6H2v-6L5 3ZM2 15h6l2 3h4l2-3h6"/>',
  sliders: '<path d="M4 7h5m4 0h7M4 17h9m4 0h3M9 4v6m4-3h-4m4 7v6m4-3h-4"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.1"/>',
  warning: '<path d="m12 3 10 18H2L12 3Zm0 6v5m0 3v.1"/>',
  stop: '<rect x="5" y="5" width="14" height="14" rx="2"/>',
  refresh: '<path d="M20 5v5h-5M4 19v-5h5m11-4a8 8 0 0 0-14-5M4 14a8 8 0 0 0 14 5"/>',
  eye: '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>'
};
const icon = name => `<svg viewBox="0 0 24 24" aria-hidden="true">${icons[name] || icons.info}</svg>`;
const escapeHtml = value => String(value).replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
function hydrate(root = document) { root.querySelectorAll("[data-icon]").forEach(node => { node.innerHTML = icon(node.dataset.icon); }); }

const exampleReport = "Saya menemukan kemungkinan akses invoice lintas akun.\n\nSaat memakai akun uji A, detail invoice milik akun uji B masih bisa dibaca setelah referensi objek diganti. Akun A seharusnya hanya dapat melihat invoice miliknya.\n\nMohon periksa kontrol kepemilikan dan apakah isi invoice benar-benar dapat diakses. Seluruh akun dan data pada contoh ini sintetis.";
const fixtures = [
  {id:"invoice",title:"Akses invoice lintas akun",code:"VV-DEMO-014",state:"confirmed",owner:"hunter",category:"BAC / IDOR",body:exampleReport,attachment:"laporan-invoice.md"},
  {id:"missing",title:"Informasi aset belum lengkap",code:"VV-DEMO-013",state:"missing",owner:"hunter",category:"Belum ditentukan",body:"Ada kemungkinan XSS di halaman pencarian. Saya belum mencantumkan alias aset, langkah reproduksi lengkap dan akun uji yang diperlukan."},
  {id:"oos",title:"Laporan di luar scope",code:"VV-DEMO-012",state:"oos",owner:"hunter",category:"Di luar program",body:"Saya ingin melaporkan masalah pada aset yang tidak tercantum dalam program Portal Pengadaan & Logistik. Tolong periksa apakah laporan ini sesuai aturan program."},
  {id:"other",title:"Validasi alur persetujuan",code:"VV-DEMO-011",state:"inconclusive",owner:"other",category:"Business logic",body:"Pelapor demo B meminta pemeriksaan urutan persetujuan permintaan barang. Bukti yang diberikan belum cukup untuk membuktikan dampak bisnis."}
];
const state = {role:"hunter",view:"chat",currentId:null,custom:[],attachment:null,fileGeneration:0,newDraft:"",newAttachment:null,scopeVersion:"1.0",guidelineDirty:false,guidelineDraft:null,published:new Set(),adminNotes:new Map()};
const scenarios = {
  confirmed:{pill:"Klaim terbukti",tone:"warning",title:"Kontrol kepemilikan belum membatasi akses.",copy:"Pada contoh ini, akun uji A dapat membaca isi invoice milik akun uji B. Kontrol pembanding menunjukkan bahwa invoice tersebut memang bukan milik akun A.",scope:"Sesuai scope",scopeIcon:"check-circle",process:"Pemeriksaan selesai"},
  refuted:{pill:"Klaim terbantahkan",tone:"neutral",title:"Bukti penyangkal mendukung kontrol akses.",copy:"Pada contoh ini, akun A ditolak saat meminta objek akun B. Kontrol pemilik sah tetap berhasil, sehingga klaim akses lintas akun terbantahkan untuk kondisi yang diperiksa.",scope:"Sesuai scope",scopeIcon:"check-circle",process:"Pemeriksaan selesai"},
  inconclusive:{pill:"Belum dapat dipastikan",tone:"neutral",title:"Dampaknya belum dapat dibuktikan.",copy:"Bukti yang tersedia belum cukup untuk mendukung atau menyangkal klaim. Lengkapi prasyarat dan kontrol pembanding sebelum mengambil keputusan.",scope:"Sesuai scope",scopeIcon:"check-circle",process:"Pemeriksaan selesai"},
  missing:{pill:"Informasi belum lengkap",tone:"neutral",title:"Lengkapi konteks aset terlebih dahulu.",copy:"Cantumkan alias aset yang tercatat pada program, langkah reproduksi dan prasyarat akun uji. Tanpa informasi tersebut, kesesuaian scope belum dapat dipastikan.",scope:"Scope belum pasti",scopeIcon:"info",process:"Menunggu informasi"},
  oos:{pill:"Di luar scope",tone:"neutral",title:"Aset tidak tercakup dalam program ini.",copy:"Laporan mengarah pada aset di luar daftar program. Pengujian internal tidak dijalankan. Lihat guideline program untuk memastikan aset dan jenis pengujian yang diterima.",scope:"Di luar scope",scopeIcon:"info",process:"Pemeriksaan scope selesai"},
  running:{pill:"Pengujian berjalan",tone:"neutral",title:"Memeriksa klaim dan kontrol pembanding.",copy:"Contoh tahap pengujian setelah scope dan prasyarat lolos. Gunakan Lanjutkan simulasi untuk melihat tampilan hasil; tidak ada request yang benar-benar dikirim.",scope:"Sesuai scope",scopeIcon:"check-circle",process:"Pengujian berjalan · simulasi"},
  failed:{pill:"Proses gagal",tone:"danger",title:"Pemeriksaan terhenti sebelum ada kesimpulan.",copy:"Contoh gangguan layanan model. Draft dan catatan proses tetap tersedia. Error ini tidak membuat laporan menjadi salah; ulangi setelah konfigurasi siap.",scope:"Sesuai scope",scopeIcon:"check-circle",process:"Gangguan layanan — contoh"},
  cancelled:{pill:"Dihentikan",tone:"neutral",title:"Pemeriksaan telah dihentikan.",copy:"Tidak ada langkah lanjutan. Catatan yang sudah tersedia tetap disimpan pada percakapan contoh ini. Penghentian bukan kesimpulan mengenai kebenaran klaim.",scope:"Sesuai scope",scopeIcon:"check-circle",process:"Dihentikan pengguna"},
  draft:{pill:"Draft laporan",tone:"neutral",title:"Laporan siap diperiksa.",copy:"Periksa kembali klaim utama dan prasyaratnya, lalu pilih Validasi laporan. Pada prototipe ini, hasil dipilih sebagai skenario tampilan; tidak ada model atau akses target.",scope:"Belum diperiksa",scopeIcon:"circle",process:"Belum dimulai"}
};

function notify(message) {
  const region = $("#notification"); region.replaceChildren();
  const text = document.createElement("span"); text.textContent = message; region.append(text);
  const dismiss = document.createElement("button"); dismiss.type="button"; dismiss.textContent="Tutup"; dismiss.addEventListener("click",()=>region.replaceChildren()); region.append(dismiss);
}
function allReports(){return [...state.custom,...fixtures];}
function permitted(report){return state.role === "admin" || report.owner === "hunter";}
function currentReport(){return allReports().find(report=>report.id===state.currentId && permitted(report));}
function saveComposer(){ if(state.view!=="chat")return;const report=currentReport();if(report){report.draft=$("#message-input").value;report.draftAttachment=state.attachment;}else{state.newDraft=$("#message-input").value;state.newAttachment=state.attachment;} }
function clearAttachment(){state.fileGeneration++;state.attachment=null;$("#file-input").value="";renderAttachment();saveComposer();}
function closeSidebar(){ $(".sidebar").classList.remove("is-open"); $("#sidebar-scrim").hidden=true; $("#sidebar-open").setAttribute("aria-expanded","false"); $(".sidebar").inert=window.matchMedia("(max-width:760px)").matches;$(".workspace-main").inert=false;$(".prototype-bar").inert=false; }
function openSidebar(){ $(".sidebar").inert=false; $(".sidebar").classList.add("is-open");$("#sidebar-scrim").hidden=false;$("#sidebar-open").setAttribute("aria-expanded","true");$(".workspace-main").inert=true;$(".prototype-bar").inert=true;$("#sidebar-close").focus(); }
function renderHistory(){
  const query=$("#history-query").value.toLocaleLowerCase("id");
  const reports=allReports().filter(report=>permitted(report)&&report.title.toLocaleLowerCase("id").includes(query));
  $("#conversation-list").innerHTML=reports.length?reports.map(report=>`<button type="button" class="conversation-item ${state.currentId===report.id&&state.view==="chat"?"selected":""}" data-report="${report.id}" title="${escapeHtml(report.title)}" ${state.currentId===report.id&&state.view==="chat"?'aria-current="page"':""}>${icon("chat")}<span class="conversation-text">${escapeHtml(report.title)}</span><span class="thread-state ${report.state==="confirmed"?"warning":""}"></span></button>`).join(""):'<p class="empty-search">Tidak ada laporan yang cocok.</p>';
  $("#admin-nav").hidden=state.role!=="admin";
  $("#account-role").textContent=state.role==="admin"?"Admin program":"Bug hunter";
  $("#history-label").textContent=state.role==="admin"?"Percakapan program":"Laporan saya";
  document.querySelectorAll("[data-view]").forEach(button=>button.classList.toggle("selected",button.dataset.view===state.view));
}
function welcomeMarkup(){return `<div class="welcome"><div class="welcome-mark">${icon("mark")}</div><h1 tabindex="-1">Mulai dari laporannya.</h1><p>Unggah laporan atau ceritakan temuanmu.<br>Validasi dimulai dari scope, dilanjutkan dengan bukti.</p><div class="welcome-actions"><button type="button" data-action="example">Coba laporan contoh ${icon("arrow-right")}</button><button type="button" data-action="scope">Lihat aturan program ${icon("arrow-up-right")}</button></div></div>`;}
function stepsMarkup(report){
  if(!["confirmed","refuted","running"].includes(report.state))return "";
  const steps=[["Scope & prasyarat diperiksa","Alias aset dan akun uji sesuai aturan."],["Kontrol pembanding diperiksa","Perilaku pemilik sah dibandingkan lintas akun."],[report.state==="running"?"Reproduksi klaim — contoh":"Bukti dikaitkan ke klaim",report.state==="running"?"Menunggu langkah simulasi berikutnya.":"Ringkasan dampak siap ditinjau admin."]];
  return `<ol class="step-list">${steps.map(([title,description],index)=>`<li><span class="step-icon">${icon(report.state==="running"&&index===2?"clock":"check-circle")}</span><span><strong>${title}</strong><small>${description}</small></span></li>`).join("")}</ol>`;
}
function assessmentMarkup(report){
  const s=scenarios[report.state];
  const noAccess=["oos","missing","draft"].includes(report.state);
  let footer=state.role==="admin"&&!noAccess?`<span class="footer-note">${icon("lock")}Bukti internal · hanya admin</span><button type="button" class="inline-action" data-action="evidence">Tinjau bukti ${icon("arrow-right")}</button>`:`<span class="footer-note">${icon(noAccess?"info":"lock")}${noAccess?"Pengujian internal belum dijalankan":state.published.has(report.id)?"Bukti tersanitasi tersedia":"Bukti detail menunggu tinjauan admin"}</span><button type="button" class="inline-action" data-action="${noAccess?"scope":"summary"}">${noAccess?"Lihat scope":"Lihat ringkasan"} ${icon("arrow-right")}</button>`;
  return `<div class="assessment-card"><div class="assessment-top"><span>Pemeriksaan laporan</span><span class="subtle">${escapeHtml(s.process)}</span></div><div class="assessment-content"><div class="check-row"><span class="status-pill ${noAccess?"neutral":""}">${icon(s.scopeIcon)}${escapeHtml(s.scope)}</span><span>${escapeHtml(report.category)}</span><span class="scope-reference">guideline v${escapeHtml(report.scopeVersion||state.scopeVersion)}</span></div><h2 class="assessment-title">${escapeHtml(s.title)}</h2><p class="assessment-copy">${escapeHtml(s.copy)}</p>${stepsMarkup(report)}<div class="draft-actions">${report.state==="draft"?`<button type="button" class="primary-button" data-action="validate">Validasi laporan ${icon("arrow-right")}</button>`:report.state==="running"?`<span class="status-pill neutral">${icon("clock")}Pengujian berjalan</span><button type="button" class="secondary-button" data-action="cancel">${icon("stop")}Hentikan</button><button type="button" class="primary-button" data-action="advance">Lanjutkan simulasi ${icon("arrow-right")}</button>`:`<span class="status-pill ${s.tone}">${icon(report.state==="confirmed"?"warning":report.state==="failed"?"info":"check-circle")}${escapeHtml(s.pill)}</span>`}</div></div><div class="assessment-footer">${footer}</div></div>`;
}
function renderChat(){
  const report=currentReport(); const empty=!report;
  $("#chat-view").classList.toggle("is-empty",empty);
  if(empty){$("#chat-content").innerHTML=welcomeMarkup();document.title="Laporan baru · ValVuln AI — Prototipe";return;}
  document.title=`${report.title} · ValVuln AI — Prototipe`;
  $("#chat-content").innerHTML=`<div class="chat-heading"><div><h1 tabindex="-1">${escapeHtml(report.title)}</h1><div class="report-meta"><span class="report-code">${report.code}</span><span>·</span><span>${report.owner==="other"?"Pelapor demo B":"Laporan Anda"}</span><span>·</span><span>Contoh tampilan</span></div></div><button type="button" class="icon-button more-button" data-action="scenarios" aria-label="Lihat variasi status tampilan">${icon("more")}</button></div><article class="message"><div class="message-author"><span class="avatar">${report.owner==="other"?"PB":"UK"}</span><span>${report.owner==="other"?"Pelapor demo B":"Anda"}</span><time>Contoh pesan</time></div><div class="user-bubble">${escapeHtml(report.body)}${report.attachment?`<div class="message-attachment">${icon("file")}${escapeHtml(report.attachment)}<span>· teks laporan</span></div>`:""}</div></article><article class="message"><div class="message-author">${icon("mark")}<span>ValVuln AI</span><time>Respons simulasi</time></div><div class="assistant-body"><p>${report.state==="draft"?"Draft tersimpan untuk percakapan ini. Pilih satu klaim utama dan lengkapi prasyarat sebelum melanjutkan.":report.state==="oos"?"Scope laporan sudah dibandingkan dengan guideline contoh. Aset ini tidak terdaftar pada program.":report.state==="missing"?"Konteks asetnya masih perlu dilengkapi. Pengujian internal belum dimulai.":"Klaim utama pada laporan ini telah diringkas. Berikut contoh tampilan pemeriksaan dan hasilnya."}</p>${assessmentMarkup(report)}<div class="message-actions"><button type="button" data-action="copy">${icon("copy")}Salin ringkasan</button><button type="button" data-action="export">${icon("download")}Ekspor contoh</button></div></div></article>${(report.messages||[]).map(message=>`<article class="message"><div class="message-author"><span class="avatar">UK</span><span>Anda</span><time>Pesan tambahan</time></div><div class="user-bubble">${escapeHtml(message)}</div></article><article class="message"><div class="message-author">${icon("mark")}<span>ValVuln AI</span><time>Respons simulasi</time></div><div class="assistant-body"><p>Pesan tambahan tersimpan di percakapan. Hasil contoh di atas tetap memakai snapshot sebelumnya; pesan ini tidak memulai pengujian baru.</p></div></article>`).join("")}`;
}
function showChat(id=null,{focus=true}={}){
  saveComposer(); state.view="chat";state.currentId=id;
  $("#chat-view").hidden=false;$("#page-view").hidden=true;
  $("#message-input").value=currentReport()?.draft||(id?"":state.newDraft);
  state.fileGeneration++;state.attachment=currentReport()?.draftAttachment||(id?null:state.newAttachment);$("#file-input").value="";
  $("#composer-error").textContent="";renderAttachment();renderHistory();renderChat();closeSidebar();
  if(focus) $("#chat-content h1")?.focus({preventScroll:true});
  $("#chat-scroll").scrollTop=0;
}
function openDialog(title,body,kicker="Contoh tampilan · data simulasi"){
  $("#dialog-title").textContent=title;$("#dialog-kicker").textContent=kicker;$("#dialog-body").innerHTML=body;hydrate($("#detail-dialog"));
  if(!$("#detail-dialog").open)$("#detail-dialog").showModal();
}
function scopeDialog(){openDialog("Scope program",`<span class="status-pill">${icon("check-circle")}Aktif · v${escapeHtml(state.scopeVersion)}</span><h3>Portal Pengadaan & Logistik</h3><p>Program lab demo dengan akun uji dan data sintetis. Aturan di bawah adalah contoh untuk meninjau UI, bukan konfigurasi target yang sudah aktif.</p><h3>In-scope</h3><ul><li>Alias aset: Portal Pengadaan & Logistik.</li><li>BAC/IDOR, XSS, file upload dan business logic pada fitur yang diizinkan.</li><li>Pengujian terstruktur menggunakan akun uji terdaftar.</li></ul><h3>Out-of-scope</h3><ul><li>Aset pihak ketiga dan infrastruktur di luar program.</li><li>DoS, race condition, eksekusi shell atau script bebas.</li><li>Data pribadi nyata dan pengujian tanpa otorisasi.</li></ul><h3>Aturan kepemilikan</h3><p>Akun pemohon hanya boleh mengakses objek miliknya. Bukti harus membedakan kontrol pemilik sah dari akses lintas akun.</p><div class="notice-line">${icon("lock")}Guideline ditetapkan admin program. Scope yang ditulis pelapor tidak dapat mengganti aturan aktif.</div>`,"Guideline publik · hanya-baca");}
function modelDialog(){
  openDialog("Model validator",`<dl class="detail-meta"><div><dt>Model rencana</dt><dd>Qwen3-Coder</dd></div><div><dt>Akses rencana</dt><dd>OpenRouter</dd></div><div><dt>Mode saat ini</dt><dd>Simulasi UI</dd></div><div><dt>Status koneksi</dt><dd>Belum terhubung</dd></div></dl><h3>Identitas model</h3><pre>qwen/qwen3-coder</pre><p>Nama ini menunjukkan model yang direncanakan untuk validator. Respons dan bukti pada prototipe masih fixture, tanpa pemanggilan model atau akses target.</p>`,"Konfigurasi rencana · belum live");
}
function summaryDialog(){
  const report=currentReport();if(!report)return;
  openDialog("Ringkasan untuk pelapor",`<span class="status-pill ${scenarios[report.state].tone}">${escapeHtml(scenarios[report.state].pill)}</span><h3>Klaim yang diperiksa</h3><p>${escapeHtml(report.title)}</p><h3>Penilaian contoh</h3><p>${escapeHtml(scenarios[report.state].copy)}</p><h3>Batas kesimpulan</h3><p>Hasil ini hanya fixture antarmuka; bukan hasil model atau reproduksi kerentanan. Tidak menyatakan seluruh aplikasi aman atau semua klaim report telah diperiksa.</p><div class="notice-line">${icon("lock")}${state.published.has(report.id)?"Contoh bukti tersanitasi: perbandingan kontrol akses mendukung penilaian. Tidak ada trace atau data internal yang dibagikan.":"Bukti detail menunggu tinjauan admin. Request/response mentah dan identitas internal tidak tersedia bagi pelapor."}</div>`);
}
function evidenceDialog(){
  if(state.role!=="admin")return;
  const report=currentReport();if(!report)return;
  openDialog("Bukti pemeriksaan",`<div class="notice-line">${icon("info")}Artefak di bawah sepenuhnya contoh UI. Belum ada request/response aktual.</div><dl class="detail-meta"><div><dt>Run</dt><dd>run-demo-014</dd></div><div><dt>Evidence</dt><dd>ev-demo-002</dd></div><div><dt>Aktor uji</dt><dd>requester_a</dd></div><div><dt>Visibilitas</dt><dd>Internal · admin program</dd></div></dl><h3>Perbandingan kontrol</h3><p>Pemilik sah dapat membaca objeknya. Pada fixture hasil terkonfirmasi, akun lain juga menerima isi objek yang bukan miliknya.</p><pre>CONTOH OBSERVASI — BUKAN TRAFFIC AKTUAL\nAktor         Objek               Hasil contoh\nPemilik sah   invoice sintetis    isi tersedia\nAkun lain     invoice yang sama   isi tersedia\n\nCookie / token: [DIREDAKSI]\nOrigin target: [ALIAS INTERNAL]</pre><h3>Tinjauan admin</h3><label class="sr-only" for="review-note">Catatan tinjauan admin</label><textarea id="review-note" class="review-textarea" maxlength="2000" placeholder="Tambahkan catatan untuk peninjauan hasil…">${escapeHtml(state.adminNotes.get(report.id)||"")}</textarea><p class="fine-print">Catatan tersimpan di memori tab; hasil agent contoh tetap dipertahankan.</p><div class="dialog-footer-actions"><button type="button" class="secondary-button" data-action="save-review">Simpan catatan</button><button type="button" class="primary-button" data-action="publish">${icon("eye")}Bagikan ringkasan</button></div>`,"Bukti internal · hanya pratinjau admin");
}
function scenarioDialog(){
  if(!currentReport())return;
  openDialog("Variasi status pemeriksaan",`<p>Pilih state untuk meninjau tampilan. Ini kontrol prototipe, bukan klasifikasi laporan atau keputusan model.</p><div class="scenario-list">${["draft","missing","oos","running","confirmed","refuted","inconclusive","failed","cancelled"].map(key=>`<button class="conversation-item" type="button" data-scenario="${key}">${icon(key==="confirmed"?"warning":"circle")}<span>${escapeHtml(scenarios[key].pill)}</span>${icon("arrow-right")}</button>`).join("")}</div>`,"Kontrol prototipe · tanpa eksekusi target");
}
function renderReports(){
  if(state.role!=="admin")return showChat();
  saveComposer();state.view="reports";$("#chat-view").hidden=true;$("#page-view").hidden=false;
  $("#page-view").innerHTML=`<div class="page-inner"><div class="page-title"><h1 tabindex="-1">Laporan program</h1><span class="status-pill neutral">Data simulasi</span></div><p class="page-intro">Tinjau klaim, hasil pemeriksaan dan bukti pada satu program. Hasil asli agent dan catatan admin tetap dibedakan.</p><div class="table-wrap"><table class="report-table"><caption class="sr-only">Daftar laporan contoh pada program</caption><thead><tr><th scope="col">Laporan</th><th scope="col">Pelapor</th><th scope="col">Status</th><th scope="col">Scope</th></tr></thead><tbody>${allReports().map(report=>`<tr><td><button class="table-title" type="button" data-report="${report.id}">${escapeHtml(report.title)}</button><small>${report.code} · ${escapeHtml(report.category)}</small></td><td>${report.owner==="other"?"Pelapor demo B":"Ukasyah"}</td><td><span class="status-pill ${scenarios[report.state].tone}">${escapeHtml(scenarios[report.state].pill)}</span></td><td>${escapeHtml(scenarios[report.state].scope)}</td></tr>`).join("")}</tbody></table></div></div>`;
  renderHistory();closeSidebar();$("#page-view h1").focus({preventScroll:true});document.title="Laporan program · ValVuln AI — Prototipe";
}
function renderGuidelines(){
  if(state.role!=="admin")return showChat();
  saveComposer();state.view="guidelines";$("#chat-view").hidden=true;$("#page-view").hidden=false;
  $("#page-view").innerHTML=`<div class="page-inner"><div class="page-title"><h1 tabindex="-1">Guideline program</h1><span class="status-pill">${icon("check-circle")}Aktif · v${escapeHtml(state.scopeVersion)}</span></div><p class="page-intro">Atur batas pemeriksaan di sini, terpisah dari laporan pelapor. Perubahan disimpan sebagai draf sebelum menjadi aturan aktif.</p><div class="guideline-form"><div class="guideline-version">${icon("file")}guideline-lab.md <span>·</span><span id="guideline-state">${state.guidelineDirty?"Draf diubah · belum aktif":"Contoh sumber guideline"}</span></div><form id="guideline-form"><div class="form-group"><label for="guideline-asset">Aset terdaftar</label><select id="guideline-asset"><option>Portal Pengadaan & Logistik — Lab Demo</option></select><p>Binding target ditetapkan operator. Host/IP bebas tidak dapat ditambahkan di sini.</p></div><div class="form-group"><label for="guideline-in">In-scope</label><textarea id="guideline-in" maxlength="5000">BAC/IDOR, XSS, file upload dan business logic pada fitur portal yang diizinkan. Gunakan akun uji terdaftar dan data sintetis.</textarea></div><div class="form-group"><label for="guideline-out">Out-of-scope</label><textarea id="guideline-out" maxlength="5000">Aset pihak ketiga; DoS/race condition; eksekusi shell/script bebas; data pribadi nyata dan pengujian tanpa otorisasi.</textarea></div><div class="form-group"><label for="guideline-rules">Aturan bisnis & prasyarat</label><textarea id="guideline-rules" maxlength="5000">Pemohon hanya dapat membaca/mengubah objek miliknya. Perbandingan lintas akun harus menggunakan objek sintetis yang disiapkan evaluator.</textarea></div><div class="guideline-actions"><button class="secondary-button" type="button" data-action="guideline-upload">${icon("paperclip")}Unggah TXT / MD</button><button class="secondary-button" type="submit">Simpan draf</button><button class="primary-button" type="button" data-action="activate">Aktifkan versi baru ${icon("arrow-right")}</button></div><input type="file" id="guideline-file" accept=".txt,.md,text/plain,text/markdown" hidden><p class="guideline-notice" id="guideline-notice">Aktivasi pada prototipe hanya mengubah label versi di tab ini. Tidak ada perubahan policy atau target nyata.</p></form></div></div>`;
  hydrate($("#page-view"));renderHistory();closeSidebar();$("#page-view h1").focus({preventScroll:true});document.title="Guideline program · ValVuln AI — Prototipe";
  if(state.guidelineDraft){$("#guideline-in").value=state.guidelineDraft.inScope;$("#guideline-out").value=state.guidelineDraft.outOfScope;$("#guideline-rules").value=state.guidelineDraft.rules;}
}
function renderAttachment(){
  const wrapper=$("#attachment-preview");wrapper.hidden=!state.attachment;
  if(!state.attachment){wrapper.replaceChildren();return;}
  wrapper.innerHTML=`${icon("file")}<div class="attachment-info"><strong>${escapeHtml(state.attachment.name)}</strong><small>${Math.ceil(state.attachment.bytes/1024)||1} KiB · teks siap dilampirkan · belum dikirim</small><pre>${escapeHtml(state.attachment.text.slice(0,180))}</pre></div><button type="button" class="icon-button" data-action="remove-attachment" aria-label="Hapus lampiran">${icon("close")}</button>`;
}
async function readTextFile(file){
  if(!file||!(/\.(txt|md)$/i).test(file.name))throw new Error("Format belum didukung. Pilih file TXT atau MD UTF-8.");
  if(file.size>128*1024)throw new Error("File melebihi 128 KiB. Ringkas laporan lalu unggah kembali.");
  const buffer=await file.arrayBuffer();let text;
  try{text=new TextDecoder("utf-8",{fatal:true}).decode(buffer);}catch{throw new Error("File harus berisi teks UTF-8. Simpan ulang sebagai TXT/MD UTF-8.");}
  if(text.length>32000)throw new Error("Teks melebihi 32.000 karakter. Ringkas laporan terlebih dahulu.");
  if(text.includes("\0"))throw new Error("File mengandung data biner. Pilih laporan teks TXT atau MD.");
  return{name:file.name,bytes:file.size,text};
}
function sendMessage(event){
  event.preventDefault();const input=$("#message-input");const text=input.value.trim();const file=state.attachment;
  if(!text&&!file){$("#composer-error").textContent="Tulis pesan atau lampirkan laporan terlebih dahulu.";input.focus();return;}
  if((text.length+(file?.text.length||0))>32000){$("#composer-error").textContent="Gabungan pesan dan lampiran melebihi 32.000 karakter. Ringkas isinya terlebih dahulu.";input.focus();return;}
  $("#composer-error").textContent="";
  let report=currentReport();
  const body=[text,file?.text].filter(Boolean).join("\n\n");
  if(!report){
    report={id:`draft-${Date.now()}`,title:(text||file?.name||"Laporan baru").split("\n")[0].slice(0,100),code:`VV-DRAFT-${state.custom.length+1}`,state:"draft",owner:"hunter",category:"Belum ditentukan",body,attachment:file?.name,scopeVersion:state.scopeVersion,draft:""};state.custom.unshift(report);state.currentId=report.id;
  }else{report.messages ||= [];report.messages.push(body);report.draft="";}
  state.newDraft="";state.newAttachment=null;input.value="";clearAttachment();renderHistory();renderChat();$("#chat-scroll").scrollTop=$("#chat-scroll").scrollHeight;input.focus();
}
function exportExample(){
  const report=currentReport();if(!report)return;
  const content=`# CONTOH UI — BUKAN HASIL VALIDASI\n\nLaporan: ${report.title}\nStatus contoh: ${scenarios[report.state].pill}\nScope: ${scenarios[report.state].scope}\nMode: simulasi UI, tanpa model/target\n\n${scenarios[report.state].copy}\n\nTidak ada raw trace, credential, host internal atau GT dalam ekspor ini.\n`;
  const link=document.createElement("a");const url=URL.createObjectURL(new Blob([content],{type:"text/markdown;charset=utf-8"}));link.href=url;link.download=`${report.code}-contoh-ui.md`;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);notify("Contoh ringkasan diekspor. Ini bukan hasil validasi.");
}
function activateDialog(){
  if(state.role!=="admin")return;
  openDialog("Aktifkan versi guideline?",`<p>Pada aplikasi nanti, aturan baru akan membatalkan job versi lama yang masih antre dan menghentikan tindakan run aktif. Hasil lama tetap menyimpan versi sebelumnya.</p><p>Pada prototipe ini, hanya nomor versi tampilan yang berubah. Draf tidak diperiksa oleh backend atau AI.</p><div class="dialog-footer-actions"><button type="button" class="secondary-button" data-action="close-dialog">Kembali ke draf</button><button type="button" class="primary-button" data-action="confirm-activate">Aktifkan contoh versi</button></div>`);
}
const actions={
  example:()=>showChat("invoice"),scope:scopeDialog,summary:summaryDialog,evidence:evidenceDialog,scenarios:scenarioDialog,validate:scenarioDialog,
  cancel:()=>{const report=currentReport();if(report){report.state="cancelled";renderChat();renderHistory();notify("Simulasi dihentikan; catatan tetap tersedia.");}},
  advance:()=>{const report=currentReport();if(report){report.state="confirmed";renderChat();renderHistory();notify("Tampilan hasil contoh ditampilkan. Tidak ada pengujian aktual.");}},
  "remove-attachment":clearAttachment,
  copy:async()=>{const report=currentReport();if(!report)return;const text=`CONTOH UI, BUKAN VALIDASI: ${report.title}\n${scenarios[report.state].pill}\n${scenarios[report.state].copy}`;try{await navigator.clipboard.writeText(text);notify("Ringkasan contoh disalin.");}catch{openDialog("Salin ringkasan",`<p>Clipboard tidak tersedia. Pilih dan salin teks berikut.</p><pre>${escapeHtml(text)}</pre>`);}},
  export:exportExample,
  "save-review":()=>{if(state.role!=="admin"||!currentReport())return;state.adminNotes.set(currentReport().id,$("#review-note").value);notify("Catatan contoh disimpan selama tab terbuka.");},
  publish:()=>{if(state.role!=="admin"||!currentReport())return;state.published.add(currentReport().id);$("#detail-dialog").close();renderChat();notify("Ringkasan contoh ditandai siap untuk pelapor. Data internal tidak disertakan.");},
  "guideline-upload":()=>$("#guideline-file")?.click(),activate:activateDialog,
  "close-dialog":()=>$("#detail-dialog").close(),
  "confirm-activate":()=>{if(state.role!=="admin")return;state.scopeVersion=`1.${Number(state.scopeVersion.split(".")[1])+1}`;state.guidelineDirty=false;$("#scope-button span:last-child").textContent=`Scope v${state.scopeVersion}`;$("#scope-button").setAttribute("aria-label",`Scope v${state.scopeVersion}`);$("#detail-dialog").close();renderGuidelines();notify("Versi contoh diaktifkan di tab ini. Policy nyata belum tersedia.");},
  "open-program":()=>{$("#detail-dialog").close();showChat();}
};

document.addEventListener("click",event=>{
  const action=event.target.closest("[data-action]");if(action&&actions[action.dataset.action]){actions[action.dataset.action]();return;}
  const thread=event.target.closest("[data-report]");if(thread){const report=allReports().find(r=>r.id===thread.dataset.report);if(report&&permitted(report))showChat(report.id);return;}
  const scenario=event.target.closest("[data-scenario]");if(scenario&&currentReport()&&scenarios[scenario.dataset.scenario]){currentReport().state=scenario.dataset.scenario;currentReport().scopeVersion ||= state.scopeVersion;$("#detail-dialog").close();renderHistory();renderChat();return;}
  const view=event.target.closest("[data-view]");if(view){if(view.dataset.view==="reports")renderReports();else renderGuidelines();}
});
$("#composer-form").addEventListener("submit",sendMessage);
$("#message-input").addEventListener("keydown",event=>{if(event.key==="Enter"&&!event.shiftKey&&!event.isComposing){event.preventDefault();$("#composer-form").requestSubmit();}});
$("#message-input").addEventListener("input",()=>{$("#composer-error").textContent="";saveComposer();});
$("#attach-button").addEventListener("click",()=>$("#file-input").click());
$("#file-input").addEventListener("change",async event=>{const token=++state.fileGeneration;const file=event.target.files[0];if(!file)return;try{const attachment=await readTextFile(file);if(token!==state.fileGeneration)return;state.attachment=attachment;$("#composer-error").textContent="";renderAttachment();}catch(error){if(token!==state.fileGeneration)return;clearAttachment();$("#composer-error").textContent=error.message;}});
$("#new-report").addEventListener("click",()=>showChat());
$("#scope-button").addEventListener("click",scopeDialog);$("#sidebar-guide").addEventListener("click",scopeDialog);
$("#model-info").addEventListener("click",modelDialog);
$("#dialog-close").addEventListener("click",()=>$("#detail-dialog").close());
$("#preview-role").addEventListener("change",event=>{saveComposer();state.role=event.target.value;$("#detail-dialog").close();if(state.role==="hunter"&&(!currentReport()||state.view!=="chat"))showChat();else{renderHistory();renderChat();}});
$("#theme-toggle").addEventListener("click",()=>{const theme=document.documentElement.dataset.theme==="dark"?"light":"dark";document.documentElement.classList.add("no-transition");document.documentElement.dataset.theme=theme;$("#theme-toggle").innerHTML=icon(theme==="dark"?"sun":"moon");$("#theme-toggle").setAttribute("aria-label",`Gunakan tema ${theme==="dark"?"terang":"gelap"}`);try{localStorage.setItem("valvuln-ui-theme",theme);}catch{}requestAnimationFrame(()=>requestAnimationFrame(()=>document.documentElement.classList.remove("no-transition")));});
$("#search-toggle").addEventListener("click",()=>{const search=$("#history-search");search.hidden=!search.hidden;$("#search-toggle").setAttribute("aria-expanded",String(!search.hidden));if(!search.hidden)$("#history-query").focus();else{$("#history-query").value="";renderHistory();}});
$("#history-query").addEventListener("input",renderHistory);
$("#sidebar-open").addEventListener("click",openSidebar);$("#sidebar-close").addEventListener("click",()=>{closeSidebar();$("#sidebar-open").focus();});$("#sidebar-scrim").addEventListener("click",()=>{closeSidebar();$("#sidebar-open").focus();});
document.addEventListener("keydown",event=>{if(event.key==="Escape"&&$(".sidebar").classList.contains("is-open")){closeSidebar();$("#sidebar-open").focus();}if(event.altKey&&event.key.toLowerCase()==="n"&&!$("dialog[open]")){event.preventDefault();showChat();$("#message-input").focus();}});
window.matchMedia("(max-width:760px)").addEventListener("change",closeSidebar);
$("#workspace-switch").addEventListener("click",()=>openDialog("Pilih program",`<p>Anda terdaftar pada satu program dalam prototipe ini.</p><div class="program-card"><strong>Portal Pengadaan & Logistik</strong><p>Lab demo · data sintetis<br>Peran pratinjau: ${state.role==="admin"?"Admin program":"Bug hunter"}</p><button type="button" class="primary-button" data-action="open-program">Buka program ${icon("arrow-right")}</button></div><p>Role aplikasi nantinya ditentukan server setelah login.</p>`,"Pilihan program · contoh tampilan"));
$("#preview-login").addEventListener("click",()=>$("#login-dialog").showModal());$("#login-close").addEventListener("click",()=>$("#login-dialog").close());
$("#login-form").addEventListener("submit",event=>{event.preventDefault();$("#login-form").reset();$("#login-dialog").close();$("#workspace-switch").click();notify("Pratinjau login selesai. Tidak ada credential yang dikirim atau disimpan.");});
document.addEventListener("submit",event=>{if(event.target.id==="guideline-form"){event.preventDefault();state.guidelineDirty=true;$("#guideline-state").textContent="Draf tersimpan di tab · belum aktif";notify("Draf contoh tersimpan; versi aktif tidak berubah.");}});
document.addEventListener("input",event=>{if(event.target.closest("#guideline-form")&&event.target.id!=="guideline-file"){state.guidelineDirty=true;state.guidelineDraft={inScope:$("#guideline-in").value,outOfScope:$("#guideline-out").value,rules:$("#guideline-rules").value};$("#guideline-state").textContent="Draf diubah · belum aktif";}});
document.addEventListener("keydown",event=>{if(event.key!=="Tab"||!$(".sidebar").classList.contains("is-open"))return;const controls=[...$(".sidebar").querySelectorAll('button,input,select,a[href]')].filter(el=>el.getClientRects().length&&!el.disabled);const first=controls[0],last=controls.at(-1);if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}});
document.addEventListener("change",async event=>{if(event.target.id!=="guideline-file")return;try{const file=await readTextFile(event.target.files[0]);if(state.role!=="admin"||state.view!=="guidelines")return;state.guidelineDirty=true;$("#guideline-state").textContent=`${file.name} · sumber draf, belum aktif`;$("#guideline-notice").textContent="Sumber guideline dibaca sebagai teks. Prototipe tidak mengekstrak atau mengaktifkan aturan otomatis; tinjau dan isi field terstruktur.";notify("Sumber guideline dibaca. Aturan aktif tidak berubah.");}catch(error){notify(error.message);}});

hydrate();
try{if(localStorage.getItem("valvuln-ui-theme")==="light")$("#theme-toggle").click();}catch{}
showChat(null,{focus:false});
