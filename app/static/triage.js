"use strict";
// Text inference has its own polling lifecycle; run polling never starts inference.
const triageUI = {
  current:null, readiness:null, timer:null, epoch:0, pending:false, error:"", keys:new Map(),
  active(){return this.current && ["PENDING","RUNNING"].includes(this.current.status);},
  stop(){clearTimeout(this.timer);this.timer=null;this.epoch++;},
  reset(clearKeys=false){this.stop();this.current=null;this.pending=false;this.error="";if(clearKeys){this.keys.clear();this.readiness=null;}},
  matches(id,view,epoch){return state.user && state.conversation?.conversation_id===id && state.viewVersion===view && this.epoch===epoch;},
  async status(){this.readiness=await api("/api/readiness");this.badge();},
  badge(){
    const r=this.readiness, mode=r?.triage_mode||this.current?.mode||"belum diketahui";
    const meta=this.current?.attempts?.filter(a=>a.metadata?.resolved_model).at(-1)?.metadata;
    $(".mode-label").textContent=`Triage ${mode.toUpperCase()}`;
    $("#model-info").textContent=meta?.resolved_model||this.current?.requested_model||r?.triage_requested_model||"Status model";
    $("#model-info").title="Status triage teks dan planner lab";
    $("#runtime-label").textContent=`Triage ${mode.toUpperCase()} · planner lab ${r?.lab_planner_mode||"belum diketahui"}`;
  },
  async mount(c,view){
    this.reset();this.render();const epoch=this.epoch;
    if(c.latest_triage_id)await this.load(c.latest_triage_id,c.conversation_id,view,epoch);
    else this.badge();
  },
  async load(id,conversationId=state.conversation?.conversation_id,view=state.viewVersion,epoch=this.epoch){
    const result=await api(`/api/triages/${id}`);
    if(!this.matches(conversationId,view,epoch))return;
    this.current=result;this.pending=false;this.error="";this.badge();this.render();
    clearTimeout(this.timer);
    if(this.active()&&!document.hidden)this.timer=setTimeout(()=>guard(async()=>{
      try{await this.load(id,conversationId,view,epoch);}catch(e){if(this.matches(conversationId,view,epoch)){this.error=e.message;this.render();}}
    }),1000);
  },
  async refresh(){
    const c=state.conversation,view=state.viewVersion;if(!c)return;
    this.stop();this.pending=false;const epoch=this.epoch;
    await this.status();
    const latest=await api(`/api/conversations/${c.conversation_id}`);
    if(!this.matches(c.conversation_id,view,epoch))return;
    if(latest.latest_triage_id)await this.load(latest.latest_triage_id,c.conversation_id,view,epoch);
    else this.render();
  },
  async request(){
    const c=state.conversation,view=state.viewVersion;
    if(!c||!own()||this.pending||this.active())return;
    if($("#message-input").value.trim()){notice("Kirim perubahan draf terlebih dahulu agar saran memakai teks yang tersimpan.");return;}
    const keyId=`${c.conversation_id}:${c.draft_version}`;
    if(!this.keys.has(keyId))this.keys.set(keyId,crypto.randomUUID());
    this.pending=true;this.error="";this.render();const epoch=this.epoch;
    try{
      const result=await api(`/api/conversations/${c.conversation_id}/triages`,{method:"POST",headers:{"Idempotency-Key":this.keys.get(keyId)},body:JSON.stringify({expected_draft_version:c.draft_version})});
      this.keys.delete(keyId);
      if(!this.matches(c.conversation_id,view,epoch))return;
      c.latest_triage_id=result.triage_id;
      this.pending=false;
      await this.load(result.triage_id,c.conversation_id,view,epoch);
    }catch(e){if(this.matches(c.conversation_id,view,epoch)){this.error=e.message;this.pending=false;this.render();}}
    // Failed/uncertain POST keeps the key for a deliberate retry, never an automatic POST.
  },
  async cancel(){
    if(!this.current)return;const id=this.current.triage_id,cid=state.conversation.conversation_id,view=state.viewVersion;
    this.stop();const epoch=this.epoch;
    const result=await api(`/api/triages/${id}/cancel`,{method:"POST"});
    if(this.matches(cid,view,epoch)){this.current=result;this.render();}
  },
  render(){
    const area=$(".triage-area"),c=state.conversation;if(!area||!c)return;
    area.replaceChildren();const box=node("article",undefined,"assessment-card triage-card"),body=node("div",undefined,"assessment-content");
    body.append(node("h2","Saran triage teks"),node("p","Minta bantuan memahami klaim dan informasi yang kurang. Saran tidak mengubah izin atau memulai validasi lab.","fine-print"));
    const readiness=this.readiness;
    body.append(node("p",`Mode triage dikonfigurasi: ${(readiness?.triage_mode||"belum diketahui").toUpperCase()} · konfigurasi: ${readiness?.text_provider||"belum diperiksa"}`),
      node("p",`Planner lab: ${readiness?.lab_planner_mode||"belum diketahui"}. Pemeriksaan target dimulai terpisah melalui Validasi snapshot.`,"fine-print"));
    if(readiness?.text_provider==="CONFIGURATION_REQUIRED")body.append(node("p","AI teks belum dapat dipakai. Operator perlu melengkapi profil provider dan key lokal. Tidak beralih ke mock otomatis."));
    if(readiness?.text_provider==="CONFIGURED_NOT_VERIFIED")body.append(node("p","Konfigurasi tersedia; akses model nyata belum dibuktikan oleh pemeriksaan konfigurasi."));
    if(this.current){
      const r=this.current,meta=r.attempts?.filter(a=>a.metadata?.resolved_model).at(-1)?.metadata;
      body.append(node("h3",r.label),node("p",`Mode hasil tersimpan: ${r.mode.toUpperCase()}`),node("p",`Status saran: ${r.status}`),
        node("p",`Provider: ${r.provider} · model diminta: ${r.requested_model}`));
      body.append(node("p",meta?`Model aktual: ${meta.resolved_model} · inference: ${meta.inference_provider}`:"Model aktual: belum ada respons provider."));
      if(!r.is_current)body.append(node("p","Hasil lama: draf atau scope sudah berubah. Jangan gunakan sebagai saran untuk konteks terbaru.","stale-result"));
      if(r.error_code)body.append(node("p",`Saran belum tersedia: ${r.error_code}`,"composer-error"));
      if(r.suggestion){
        const s=r.suggestion;body.append(node("p",`Klaim utama: ${s.primary_claim}`),node("p",`Kategori/subtype yang disarankan: ${s.category} / ${s.subtype}`),
          node("p",`Saran scope: ${s.scope_suggestion} · kemampuan: ${s.capability_suggestion}`),node("p",s.reason));
        if(s.missing_information.length){body.append(node("h3","Informasi yang kurang"));const list=node("ul");s.missing_information.forEach(x=>list.append(node("li",x)));body.append(list);}
        body.append(node("p","Hasil verifier lab ditampilkan pada kartu terpisah. Saran ini bukan CONFIRMED/REFUTED atau GT.","fine-print"));
      }
    }else body.append(node("p","Belum ada saran. Chat dan lampiran hanya menyimpan draf."));
    if($("#message-input").value.trim())body.append(node("p","Ada teks belum dikirim; kirim dahulu sebelum meminta saran.","fine-print"));
    if(this.error){const error=node("p",this.error,"composer-error");error.setAttribute("role","alert");body.append(error);}
    const actions=node("div",undefined,"draft-actions");
    if(own()){
      const request=button(this.pending?"Meminta saran…":"Minta saran AI",()=>this.request());
      request.disabled=this.pending||this.active()||c.draft_version<1||!!$("#message-input").value.trim();actions.append(request);
    }
    if(this.active()&&(own()||state.program.role==="PROGRAM_ADMIN"))actions.append(button("Batalkan saran",()=>this.cancel()));
    actions.append(button("Perbarui status saran",()=>this.refresh()));body.append(actions);box.append(body);area.append(box);
  },
  info(){const box=node("div");box.append(node("p",`Triage teks: ${this.readiness?.triage_mode||"belum diketahui"} · ${this.readiness?.text_provider||"belum diperiksa"}`),
    node("p",`Planner lab: ${this.readiness?.lab_planner_mode||"belum diketahui"}; mode ini tidak diubah oleh saran AI.`));
    if(this.current){const r=this.current,meta=r.attempts?.filter(a=>a.metadata?.resolved_model).at(-1)?.metadata;box.append(node("p",`Model diminta: ${r.requested_model} · provider: ${r.provider}`),node("p",meta?`Model aktual: ${meta.resolved_model} · inference: ${meta.inference_provider}`:"Belum ada respons provider."));}
    box.append(node("p","MOCK adalah simulasi. CONFIGURED_NOT_VERIFIED hanya menunjukkan konfigurasi lengkap. Tombol status ini tidak memanggil model."));panel("Status model",box);},
  visibility(){this.stop();if(!document.hidden&&this.current)guard(()=>this.load(this.current.triage_id));}
};

async function showObservationSummary(run){
  const id=state.conversation?.conversation_id,view=state.viewVersion;
  const data=await api(`/api/runs/${run.run_id}/observations-summary`);
  if(view!==state.viewVersion||id!==state.conversation?.conversation_id)return;
  const box=node("div");box.append(node("p",data.label),node("p",data.summary));
  if(!data.is_current)box.append(node("p","Snapshot lama: draf, revisi laporan atau scope saat ini berbeda.","stale-result"));
  if(data.binding)box.append(node("p",`Revisi laporan ${data.binding.report_revision_number} · snapshot ${data.binding.target_snapshot_id}`));
  data.observations.forEach(o=>{const fact=node("div",undefined,"observation-fact");fact.append(
    node("p",`Observasi ${o.action_seq}: ${o.tool} ${o.method} · ${o.status} · HTTP ${o.http_status??"tidak tersedia"}`),
    node("p",`Respons ${o.responses_received}/${o.request_attempts} · terpotong: ${o.truncated?"ya":"tidak"}`),node("code",`Evidence ID: ${o.evidence_id}`));box.append(fact);});
  box.append(node("p","Ringkasan ini membaca observasi tersimpan. Tidak memanggil AI/worker dan tidak menetapkan atau mengubah verdict.","fine-print"));
  panel("Ringkasan observasi",box,"Bukti tersimpan · terpisah dari saran AI dan verifier");
}
