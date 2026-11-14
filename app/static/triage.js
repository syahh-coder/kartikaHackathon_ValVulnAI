"use strict";
// Text inference has its own polling lifecycle; run polling never starts inference.
function statusTone(status) {
  if (["SUCCEEDED", "COMPLETED", "CONFIRMED", "CONSISTENT", "ACTIVE"].includes(status)) return "success";
  if (["PENDING", "RUNNING", "QUEUED", "LEASED", "INCONCLUSIVE", "UNABLE_TO_VERIFY", "REVIEWED"].includes(status)) return "warning";
  if (["FAILED", "CANCELLED", "REFUTED", "REJECTED", "INCONSISTENT"].includes(status)) return "danger";
  return "neutral";
}

function makeMetricCell(label, value, mono = false) {
  const cell = node("div", undefined, "metric-cell");
  cell.append(node("span", label));
  const val = node("strong", value);
  if (mono) val.classList.add("mono");
  cell.append(val);
  return cell;
}

function makeStatusPill(text, tone = "neutral", iconName = "info") {
  const pill = node("span", undefined, `status-pill ${tone}`.trim());
  pill.append(makeSvg(iconName));
  pill.append(document.createTextNode(text));
  return pill;
}

const triageUI = {
  current: null,
  readiness: null,
  timer: null,
  epoch: 0,
  pending: false,
  error: "",
  keys: new Map(),

  active() {
    return this.current && ["PENDING", "RUNNING"].includes(this.current.status);
  },

  stop() {
    clearTimeout(this.timer);
    this.timer = null;
    this.epoch++;
  },

  reset(clearKeys = false) {
    this.stop();
    this.current = null;
    this.pending = false;
    this.error = "";
    if (clearKeys) {
      this.keys.clear();
      this.readiness = null;
    }
  },

  matches(id, view, epoch) {
    return state.user && state.conversation?.conversation_id === id && state.viewVersion === view && this.epoch === epoch;
  },

  async status() {
    this.readiness = await api("/api/readiness");
    this.badge();
  },

  badge() {
    const r = this.readiness;
    const mode = r?.triage_mode || this.current?.mode || "belum diketahui";
    const meta = this.current?.attempts?.filter(a => a.metadata?.resolved_model).at(-1)?.metadata;
    $(".mode-label").textContent = `Triage ${mode.toUpperCase()}`;
    const infoBtn = $("#model-info");
    infoBtn.textContent = meta?.resolved_model || this.current?.requested_model || r?.triage_requested_model || "Status model";
    infoBtn.title = "Status triage teks dan planner lab";
    const runtimeLabel = $("#runtime-label");
    if (runtimeLabel) {
      runtimeLabel.textContent = `Triage ${mode.toUpperCase()} · planner lab ${r?.lab_planner_mode || "belum diketahui"}`;
    }
    const isBusy = Boolean(this.pending || this.active() || active(state.run));
    $("#topbar-status-dot")?.classList.toggle("is-live", isBusy);
    $("#runtime-dot")?.classList.toggle("is-live", isBusy);
  },

  async mount(c, view) {
    this.reset();
    this.render();
    const epoch = this.epoch;
    if (c.latest_triage_id) await this.load(c.latest_triage_id, c.conversation_id, view, epoch);
    else this.badge();
  },

  async load(id, conversationId = state.conversation?.conversation_id, view = state.viewVersion, epoch = this.epoch) {
    const result = await api(`/api/triages/${id}`);
    if (!this.matches(conversationId, view, epoch)) return;
    this.current = result;
    this.pending = false;
    this.error = "";
    this.badge();
    this.render();
    clearTimeout(this.timer);
    if (this.active() && !document.hidden) {
      this.timer = setTimeout(() => guard(async () => {
        try {
          await this.load(id, conversationId, view, epoch);
        } catch (e) {
          if (this.matches(conversationId, view, epoch)) {
            this.error = e.message;
            this.render();
          }
        }
      }), 1000);
    }
  },

  async refresh() {
    const c = state.conversation, view = state.viewVersion;
    if (!c) return;
    this.stop();
    this.pending = false;
    const epoch = this.epoch;
    await this.status();
    const latest = await api(`/api/conversations/${c.conversation_id}`);
    if (!this.matches(c.conversation_id, view, epoch)) return;
    if (latest.latest_triage_id) await this.load(latest.latest_triage_id, c.conversation_id, view, epoch);
    else this.render();
  },

  async request() {
    const c = state.conversation, view = state.viewVersion;
    if (!c || !own() || this.pending || this.active()) return;
    if ($("#message-input").value.trim()) {
      notice("Kirim perubahan draf terlebih dahulu agar saran memakai teks yang tersimpan.");
      return;
    }
    const keyId = `${c.conversation_id}:${c.draft_version}`;
    if (!this.keys.has(keyId)) this.keys.set(keyId, crypto.randomUUID());
    this.pending = true;
    this.error = "";
    this.badge();
    this.render();
    if (typeof scrollToInspector === "function") scrollToInspector($(".triage-area"));
    else smoothScrollTo($(".triage-area"), $("#chat-scroll"), 460);
    const epoch = this.epoch;
    try {
      const result = await api(`/api/conversations/${c.conversation_id}/triages`, {
        method: "POST",
        headers: { "Idempotency-Key": this.keys.get(keyId) },
        body: JSON.stringify({ expected_draft_version: c.draft_version })
      });
      this.keys.delete(keyId);
      if (!this.matches(c.conversation_id, view, epoch)) return;
      c.latest_triage_id = result.triage_id;
      this.pending = false;
      await this.load(result.triage_id, c.conversation_id, view, epoch);
    } catch (e) {
      if (this.matches(c.conversation_id, view, epoch)) {
        this.error = e.message;
        this.pending = false;
        this.badge();
        this.render();
      }
    }
  },

  async cancel() {
    if (!this.current) return;
    const id = this.current.triage_id, cid = state.conversation.conversation_id, view = state.viewVersion;
    this.stop();
    const epoch = this.epoch;
    const result = await api(`/api/triages/${id}/cancel`, { method: "POST" });
    if (this.matches(cid, view, epoch)) {
      this.current = result;
      this.badge();
      this.render();
    }
  },

  async prepareValidation() {
    const r = this.current, c = state.conversation, view = state.viewVersion, epoch = this.epoch;
    if (!r || !c || !own() || r.status !== "SUCCEEDED" || !r.is_current) return;
    if ($("#message-input").value.trim()) {
      notice("Kirim perubahan draf dan minta saran terbaru terlebih dahulu.");
      return;
    }
    const proposal = await api(`/api/triages/${r.triage_id}/validation-draft`, { method: "POST" });
    if (!this.matches(c.conversation_id, view, epoch)) return;
    if (["OUT_OF_SCOPE", "POLICY_BLOCKED", "UNSUPPORTED"].includes(proposal.policy_status)) {
      const box = node("div");
      box.append(node("p", `Backend: ${proposal.scope_decision} · ${proposal.policy_status}. Tidak ada pengujian target yang dimulai.`));
      proposal.missing_information.forEach(text => box.append(node("p", text)));
      panel("Draf validasi belum dapat dilanjutkan", box);
      return;
    }
    await validation(proposal);
  },

  render() {
    const area = $(".triage-area"), c = state.conversation;
    if (!area || !c) return;
    area.replaceChildren();

    const box = node("article", undefined, "assessment-card triage-card vv-reveal");
    const top = node("div", undefined, "assessment-top");
    const topLabel = node("div", undefined, "assessment-top-label");
    topLabel.append(makeSvg("sparkles"), node("span", "SARAN AI (TEKS ONLY) · NON-OTORITATIF"));
    top.append(topLabel);
    if (this.current) {
      const pillIcon = this.current.status === "SUCCEEDED" ? "check-circle" : this.active() ? "clock" : "info";
      top.append(makeStatusPill(this.current.status, statusTone(this.current.status), pillIcon));
    } else {
      top.append(makeStatusPill(this.pending ? "MEMINTA" : "SIAP", this.pending ? "warning" : "neutral", this.pending ? "clock" : "circle"));
    }
    box.append(top);

    const body = node("div", undefined, "assessment-content");
    const heading = node("h2");
    heading.textContent = "Saran triage teks";
    body.append(heading);
    body.append(node("p", "Minta bantuan memahami klaim dan informasi yang kurang. Saran tidak mengubah izin atau memulai validasi lab.", "fine-print"));

    const readiness = this.readiness;
    const grid = node("div", undefined, "metric-grid");
    grid.append(
      makeMetricCell("Konfigurasi Triage", `Mode triage dikonfigurasi: ${(readiness?.triage_mode || "belum diketahui").toUpperCase()} · konfigurasi: ${readiness?.text_provider || "belum diperiksa"}`),
      makeMetricCell("Planner Lab", `Planner lab: ${readiness?.lab_planner_mode || "belum diketahui"}. Pemeriksaan target dimulai terpisah melalui Validasi snapshot.`)
    );
    grid.lastChild.querySelector("strong").classList.add("fine-print");
    body.append(grid);

    if (readiness?.text_provider === "CONFIGURATION_REQUIRED") {
      const warn = node("div", undefined, "notice-callout warning");
      warn.append(makeSvg("warning"), node("span", "AI teks belum dapat dipakai. Operator perlu melengkapi profil provider dan key lokal. Tidak beralih ke mock otomatis."));
      body.append(warn);
    }
    if (readiness?.text_provider === "CONFIGURED_NOT_VERIFIED") {
      const info = node("div", undefined, "notice-callout");
      info.append(makeSvg("info"), node("span", "Konfigurasi tersedia; akses model nyata belum dibuktikan oleh pemeriksaan konfigurasi."));
      body.append(info);
    }

    if (this.current) {
      const r = this.current;
      const meta = r.attempts?.filter(a => a.metadata?.resolved_model).at(-1)?.metadata;
      const resGrid = node("div", undefined, "metric-grid");
      resGrid.append(
        makeMetricCell("Mode Tersimpan", `Mode hasil tersimpan: ${r.mode.toUpperCase()}`),
        makeMetricCell("Status Saran", `Status saran: ${r.status}`),
        makeMetricCell("Provider & Diminta", `Provider: ${r.provider} · model diminta: ${r.requested_model}`, true),
        makeMetricCell("Model Aktual", meta ? `Model aktual: ${meta.resolved_model} · inference: ${meta.inference_provider}` : "Model aktual: belum ada respons provider.", true)
      );
      body.append(node("h3", r.label), resGrid);

      if (!r.is_current) {
        body.append(node("p", "Hasil lama: draf atau scope sudah berubah. Jangan gunakan sebagai saran untuk konteks terbaru.", "stale-result"));
      }
      if (r.error_code) {
        const errCode = node("p", `Saran belum tersedia: ${r.error_code}`, "composer-error");
        errCode.setAttribute("role", "alert");
        body.append(errCode);
      }
      if (r.suggestion) {
        const s = r.suggestion;
        const sugGrid = node("div", undefined, "metric-grid");
        sugGrid.append(
          makeMetricCell("Klaim Utama", `Klaim utama: ${s.primary_claim}`),
          makeMetricCell("Kategori / Subtype", `Kategori/subtype yang disarankan: ${s.category} / ${s.subtype}`),
          makeMetricCell("Scope & Kemampuan", `Saran scope: ${s.scope_suggestion} · kemampuan: ${s.capability_suggestion}`)
        );
        body.append(sugGrid, node("p", s.reason));
        if (s.missing_information.length) {
          body.append(node("h3", "Informasi yang kurang"));
          const list = node("ul");
          s.missing_information.forEach(x => {
            const li = node("li");
            li.append(makeSvg("warning"), node("span", x));
            list.append(li);
          });
          body.append(list);
        }
        body.append(node("p", "Hasil verifier lab ditampilkan pada kartu terpisah. Saran ini bukan CONFIRMED/REFUTED atau GT.", "fine-print"));
      }
    } else {
      body.append(node("p", "Belum ada saran. Chat dan lampiran hanya menyimpan draf."));
    }

    if ($("#message-input").value.trim()) {
      body.append(node("p", "Ada teks belum dikirim; kirim dahulu sebelum meminta saran.", "fine-print"));
    }
    if (this.error) {
      const error = node("p", this.error, "composer-error");
      error.setAttribute("role", "alert");
      body.append(error);
    }

    const actions = node("div", undefined, "draft-actions");
    if (own()) {
      const reqBtn = button(undefined, () => this.request(), "primary-button");
      if (this.pending) {
        reqBtn.append(node("span", undefined, "vv-spinner"), node("span", "Meminta saran…"));
      } else {
        reqBtn.append(makeSvg("sparkles"), node("span", "Minta saran AI"));
      }
      reqBtn.disabled = this.pending || this.active() || c.draft_version < 1 || !!$("#message-input").value.trim();
      actions.append(reqBtn);
      if (this.current?.status === "SUCCEEDED" && this.current.is_current && ["BAC-08", "XSS-08", "UP-04"].includes(this.current.suggestion?.subtype)) {
        const prepareBtn = button("Siapkan validasi dari saran AI", () => this.prepareValidation(), "primary-button");
        prepareBtn.disabled = !!$("#message-input").value.trim();
        actions.append(prepareBtn);
      }
    }
    if (this.active() && (own() || state.program.role === "PROGRAM_ADMIN")) {
      const cancelBtn = button(undefined, () => this.cancel(), "secondary-button");
      cancelBtn.append(makeSvg("stop"), node("span", "Batalkan saran"));
      actions.append(cancelBtn);
    }
    const refreshBtn = button(undefined, () => this.refresh(), "secondary-button");
    refreshBtn.append(makeSvg("refresh"), node("span", "Perbarui status saran"));
    actions.append(refreshBtn);

    body.append(actions);
    box.append(body);
    area.append(box);
    scheduleRevealCleanup(box);
  },

  info() {
    const box = node("div");
    box.append(
      node("p", `Triage teks: ${this.readiness?.triage_mode || "belum diketahui"} · ${this.readiness?.text_provider || "belum diperiksa"}`),
      node("p", `Planner lab: ${this.readiness?.lab_planner_mode || "belum diketahui"}; mode ini tidak diubah oleh saran AI.`)
    );
    if (this.current) {
      const r = this.current, meta = r.attempts?.filter(a => a.metadata?.resolved_model).at(-1)?.metadata;
      box.append(
        node("p", `Model diminta: ${r.requested_model} · provider: ${r.provider}`),
        node("p", meta ? `Model aktual: ${meta.resolved_model} · inference: ${meta.inference_provider}` : "Belum ada respons provider.")
      );
    }
    box.append(node("p", "MOCK adalah simulasi. CONFIGURED_NOT_VERIFIED hanya menunjukkan konfigurasi lengkap. Tombol status ini tidak memanggil model."));
    panel("Status model", box);
  },

  visibility() {
    this.stop();
    if (!document.hidden && this.current) guard(() => this.load(this.current.triage_id));
  }
};

async function showObservationSummary(run) {
  const id = state.conversation?.conversation_id, view = state.viewVersion;
  const data = await api(`/api/runs/${run.run_id}/observations-summary`);
  if (view !== state.viewVersion || id !== state.conversation?.conversation_id) return;
  const box = node("div");
  box.append(node("p", data.label), node("p", data.summary));
  if (!data.is_current) {
    box.append(node("p", "Snapshot lama: draf, revisi laporan atau scope saat ini berbeda.", "stale-result"));
  }
  if (data.binding) {
    box.append(node("p", `Revisi laporan ${data.binding.report_revision_number} · snapshot ${data.binding.target_snapshot_id}`));
  }
  data.observations.forEach(o => {
    const fact = node("div", undefined, "observation-fact");
    fact.append(
      node("p", `Observasi ${o.action_seq}: ${o.tool} ${o.method} · ${o.status} · HTTP ${o.http_status ?? "tidak tersedia"}`),
      node("p", `Respons ${o.responses_received}/${o.request_attempts} · terpotong: ${o.truncated ? "ya" : "tidak"}`),
      node("code", `Evidence ID: ${o.evidence_id}`)
    );
    box.append(fact);
  });
  box.append(node("p", "Ringkasan ini membaca observasi tersimpan. Tidak memanggil AI/worker dan tidak menetapkan atau mengubah verdict.", "fine-print"));
  panel("Ringkasan observasi", box, "Bukti tersimpan · terpisah dari saran AI dan verifier");
}
