"use strict";
const $ = (q, root = document) => root.querySelector(q);
const state = {
  user: null,
  programs: [],
  program: null,
  conversation: null,
  run: null,
  csrf: "",
  timer: null,
  pollVersion: 0,
  viewVersion: 0,
  authVersion: 0,
  drafts: new Map(),
  inspectorTab: "all",
  adminPage: null,
  adminQueueFilters: { query: "", status: "all", verdict: "all" },
  busy: false
};

function syncAdminNavHighlight() {
  document.querySelectorAll("#admin-nav button[data-view]").forEach(btn => {
    btn.classList.toggle("selected", Boolean(state.adminPage) && btn.dataset.view === state.adminPage);
  });
  if (state.adminPage) {
    document.querySelectorAll("#conversation-list .conversation-item.selected").forEach(el => el.classList.remove("selected"));
  }
}

function closePageView() {
  const pageView = $("#page-view");
  const chatView = $("#chat-view");
  state.adminPage = null;
  if (pageView) {
    pageView.hidden = true;
    pageView.replaceChildren();
  }
  if (chatView) chatView.hidden = false;
  syncAdminNavHighlight();
}

function setInspectorTab(tab = "all") {
  const safe = ["all", "verifier", "triage"].includes(tab) ? tab : "all";
  state.inspectorTab = safe;
  document.querySelectorAll("[data-inspector-tab]").forEach(btn => {
    const activeTab = btn.dataset.inspectorTab === safe;
    btn.classList.toggle("is-active", activeTab);
    btn.setAttribute("aria-selected", String(activeTab));
  });
  const runEl = $(".run-area");
  const triageEl = $(".triage-area");
  const bizEl = $(".business-area");
  if (runEl) runEl.hidden = safe === "triage";
  if (bizEl) bizEl.hidden = safe === "triage";
  if (triageEl) triageEl.hidden = safe === "verifier";
}

function scrollToInspector(target) {
  const inspector = $("#chat-inspector");
  if (!inspector || inspector.hidden) return;
  if (target?.classList?.contains("triage-area") && state.inspectorTab === "verifier") {
    setInspectorTab("all");
  } else if (!target?.classList?.contains("triage-area") && state.inspectorTab === "triage") {
    setInspectorTab("all");
  }
  const container = window.innerWidth >= 1280 ? $("#inspector-scroll") : $("#chat-view");
  smoothScrollTo(target || inspector, container || window, 460);
}

function renderRunPlaceholder() {
  const area = $(".run-area");
  if (!area || state.run) return;
  const box = node("div", undefined, "inspector-empty-placeholder");
  box.append(
    node("strong", "VERIFIER LAB · MENUNGGU RUN"),
    node("p", "Belum ada run validasi. Klik Validasi snapshot di area laporan untuk menjalankan uji lab.")
  );
  area.replaceChildren(box);
}

const active = r => r && ["QUEUED", "LEASED"].includes(r.queue_status);

function node(tag, text, cls) {
  const n = document.createElement(tag);
  if (text !== undefined) n.textContent = text;
  if (cls) n.className = cls;
  return n;
}

function button(text, action, cls = "secondary-button") {
  const b = node("button", text, cls);
  b.type = "button";
  b.addEventListener("click", () => guard(action));
  return b;
}

function iconButton(iconKey, text, action, cls = "secondary-button") {
  const b = button(undefined, action, cls);
  b.append(makeSvg(iconKey), node("span", text));
  return b;
}

const activeScrollRafs = new WeakMap();

function smoothScrollTo(targetOrY, container = window, duration = 640, extraOffset = 0) {
  if (targetOrY === null || targetOrY === undefined) return;
  const isWin = container === window;
  const getScrollY = () => (isWin ? window.scrollY || window.pageYOffset : container.scrollTop);
  const maxScroll = () => (isWin
    ? Math.max(0, document.documentElement.scrollHeight - window.innerHeight)
    : Math.max(0, container.scrollHeight - container.clientHeight));

  let targetY = 0;
  let arrivalEl = null;
  if (typeof targetOrY === "number") {
    targetY = targetOrY;
  } else if (targetOrY instanceof Element) {
    arrivalEl = targetOrY;
    if (isWin) {
      if (targetOrY.id === "top") {
        targetY = 0;
      } else {
        const nav = $(".landing-nav");
        const navH = nav && !$("#landing-view")?.hidden ? nav.getBoundingClientRect().height : 0;
        targetY = getScrollY() + targetOrY.getBoundingClientRect().top - navH - 14 + extraOffset;
      }
    } else {
      const cRect = container.getBoundingClientRect();
      const eRect = targetOrY.getBoundingClientRect();
      targetY = getScrollY() + (eRect.top - cRect.top) - 18 + extraOffset;
    }
  } else {
    return;
  }

  targetY = Math.max(0, Math.min(maxScroll(), targetY));
  const startY = getScrollY();
  const delta = targetY - startY;

  const prevRaf = activeScrollRafs.get(container);
  if (prevRaf) cancelAnimationFrame(prevRaf);

  const pulseArrival = () => {
    if (!arrivalEl) return;
    arrivalEl.classList.remove("vv-scroll-focus");
    void arrivalEl.offsetWidth;
    arrivalEl.classList.add("vv-scroll-focus");
    setTimeout(() => arrivalEl.classList.remove("vv-scroll-focus"), 520);
  };

  if (Math.abs(delta) < 2) {
    container.scrollTo({ top: targetY, behavior: "instant" });
    pulseArrival();
    return;
  }

  const startTime = performance.now();
  const easeOutExpo = t => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t));
  let cancelled = false;
  const abort = () => {
    cancelled = true;
    const cur = activeScrollRafs.get(container);
    if (cur) cancelAnimationFrame(cur);
    activeScrollRafs.delete(container);
    detach();
  };
  const onKey = e => {
    if (["ArrowUp", "ArrowDown", "PageUp", "PageDown", "Home", "End", " "].includes(e.key)) abort();
  };
  const detach = () => {
    container.removeEventListener("wheel", abort);
    container.removeEventListener("touchstart", abort);
    if (isWin) window.removeEventListener("keydown", onKey);
  };

  container.addEventListener("wheel", abort, { passive: true, once: true });
  container.addEventListener("touchstart", abort, { passive: true, once: true });
  if (isWin) window.addEventListener("keydown", onKey, { passive: true });

  const step = now => {
    if (cancelled) return;
    const elapsed = now - startTime;
    const progress = Math.min(1, elapsed / duration);
    const nextY = startY + delta * easeOutExpo(progress);
    container.scrollTo({ top: nextY, behavior: "instant" });
    if (progress < 1) {
      activeScrollRafs.set(container, requestAnimationFrame(step));
    } else {
      activeScrollRafs.delete(container);
      detach();
      pulseArrival();
    }
  };
  activeScrollRafs.set(container, requestAnimationFrame(step));
}

function scrollSidebarToSelected() {
  const list = $("#conversation-list");
  const selected = list?.querySelector(".conversation-item.selected");
  if (!list || !selected) return;
  const centerOffset = -(list.clientHeight / 2) + selected.offsetHeight / 2;
  smoothScrollTo(selected, list, 400, centerOffset);
}

function scheduleRevealCleanup(el, delayClass = "") {
  if (!el) return;
  if (delayClass) el.classList.add(delayClass);
  setTimeout(() => {
    el.classList.remove("vv-reveal", "vv-d1", "vv-d2", "vv-d3", "vv-d4", "vv-d5");
  }, 640);
}

function iconize() {
  document.querySelectorAll("[data-icon]").forEach(n => {
    if (n.id === "landing-theme-toggle") return;
    const key = n.dataset.icon;
    if (icons[key]) n.replaceChildren(makeSvg(key));
  });
}

function notice(text) {
  const el = $("#notification");
  if (el) el.textContent = text;
}

async function guard(action) {
  try {
    return await action();
  } catch (e) {
    if (!e.stale) notice(e.message || "Permintaan gagal.");
  }
}

async function api(path, options = {}) {
  const authVersion = state.authVersion;
  const headers = { ...options.headers };
  if (options.body && !(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  if (options.method && options.method !== "GET") headers["X-CSRF-Token"] = state.csrf;
  let response;
  try {
    response = await fetch(path, { ...options, headers, credentials: "same-origin", cache: "no-store" });
  } catch {
    throw Error("Koneksi aplikasi gagal. Muat ulang status sebelum mencoba kembali.");
  }
  const data = await response.json();
  if (authVersion !== state.authVersion) throw Object.assign(Error("Sesi sudah berubah."), { stale: true });
  if (!response.ok) {
    if (response.status === 401) logoutView();
    const details = Array.isArray(data.field_errors)
      ? data.field_errors.map(e => e.message).filter(m => typeof m === "string").join(" ")
      : "";
    throw Error(`${data.message || "Permintaan ditolak"}${details ? " " + details : ""} (${data.error_code || response.status})`);
  }
  return data;
}

function stopPoll() {
  clearTimeout(state.timer);
  state.timer = null;
  state.pollVersion++;
}

function logoutView() {
  stopPoll();
  triageUI.reset(true);
  state.authVersion++;
  state.user = null;
  state.program = null;
  state.programs = [];
  state.csrf = "";
  state.conversation = null;
  state.run = null;
  state.drafts.clear();
  $("#message-input").value = "";
  $("#conversation-list").replaceChildren();
  $("#chat-content").replaceChildren();
  $(".run-area")?.replaceChildren();
  $(".triage-area")?.replaceChildren();
  $(".business-area")?.replaceChildren();
  if ($("#chat-inspector")) $("#chat-inspector").hidden = true;
  $("#detail-dialog").close();
  $("#dialog-body").replaceChildren();
  $("#login-dialog").close();
  closePageView();
  $("#app-shell").inert = true;
  $("#app-shell").hidden = true;
  $("#prototype-bar").hidden = true;
  $("#logout").hidden = true;
  $("#landing-view").hidden = false;
  $("#account-name").textContent = "Belum masuk";
  $("#account-avatar").textContent = "VV";
  const showPass = $("#login-show-password");
  if (showPass) {
    showPass.checked = false;
    $("#login-password").type = "password";
  }
  triageUI.badge();
  landingUI.resumeHeroScene();
  smoothScrollTo(0, window, 420);
}

function field(form, label, value = "", type = "text") {
  const group = node("div", undefined, "form-group");
  const id = "field-" + crypto.randomUUID();
  const l = node("label", label);
  l.htmlFor = id;
  const input = node(type === "textarea" ? "textarea" : "input");
  input.id = id;
  if (type !== "textarea") input.type = type;
  input.value = value;
  group.append(l, input);
  form.append(group);
  return input;
}

function select(form, label, choices, value) {
  const group = node("div", undefined, "form-group");
  const id = "field-" + crypto.randomUUID();
  const l = node("label", label);
  const s = node("select");
  l.htmlFor = id;
  s.id = id;
  choices.forEach(([v, t]) => {
    const o = node("option", t);
    o.value = v;
    s.append(o);
  });
  s.value = value;
  group.append(l, s);
  form.append(group);
  return s;
}

function panel(title, content, kicker = "ValVuln AI") {
  $("#dialog-title").textContent = title;
  $("#dialog-kicker").textContent = kicker;
  $("#dialog-body").replaceChildren(content);
  const dlg = $("#detail-dialog");
  if (!dlg.open) dlg.showModal();
  smoothScrollTo(0, dlg, 260);
}

function saveUnsent() {
  if (state.conversation) state.drafts.set(state.conversation.conversation_id, $("#message-input").value);
}

function own() {
  return state.conversation?.owner_user_id === state.user?.user_id;
}

function closeNav() {
  $(".sidebar").classList.remove("is-open");
  $("#sidebar-scrim").hidden = true;
  $(".workspace-main").inert = false;
  $("#sidebar-open").setAttribute("aria-expanded", "false");
}

function initials(name) {
  if (!name) return "VV";
  const parts = name.trim().split(/[-_\s]+/).filter(Boolean);
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return name.slice(0, 2).toUpperCase();
}

let activeThemeTransition = null;
let themeCleanupTimer = 0;

function commitThemeState(theme) {
  document.documentElement.dataset.theme = theme;
  [$("#theme-toggle"), $("#landing-theme-toggle")].forEach(toggle => {
    if (!toggle) return;
    if (toggle.id === "landing-theme-toggle") {
      toggle.checked = theme === "dark";
      toggle.setAttribute("aria-label", theme === "light" ? "Gunakan tema gelap" : "Gunakan tema terang");
      return;
    }
    toggle.dataset.icon = theme === "light" ? "moon" : "sun";
    toggle.setAttribute("aria-label", theme === "light" ? "Gunakan tema gelap" : "Gunakan tema terang");
    const icon = makeSvg(toggle.dataset.icon);
    toggle.replaceChildren(icon);
  });
  try {
    localStorage.setItem("valvuln-theme", theme);
  } catch {}
  if (typeof landingUI !== "undefined" && landingUI.syncTheme) {
    landingUI.syncTheme(theme);
  }
}

function spawnFallbackThemeWave() {
  document.querySelector(".vv-theme-wave")?.remove();
  const wave = document.createElement("div");
  wave.className = "vv-theme-wave";
  wave.setAttribute("aria-hidden", "true");
  document.body.append(wave);
  setTimeout(() => wave.remove(), 700);
}

function applyTheme(theme, animate = false) {
  const root = document.documentElement;
  if (!animate) {
    commitThemeState(theme);
    return;
  }

  const radius = Math.ceil(Math.hypot(window.innerWidth / 2, window.innerHeight / 2)) + 120;
  root.style.setProperty("--vv-vt-radius", `${radius}px`);

  if (typeof document.startViewTransition === "function") {
    clearTimeout(themeCleanupTimer);
    if (activeThemeTransition?.skipTransition) {
      try { activeThemeTransition.skipTransition(); } catch {}
    }
    root.classList.add("is-theme-transitioning");
    const transition = document.startViewTransition(() => {
      commitThemeState(theme);
    });
    activeThemeTransition = transition;
    const cleanup = () => {
      if (activeThemeTransition === transition) {
        activeThemeTransition = null;
        clearTimeout(themeCleanupTimer);
        root.classList.remove("is-theme-transitioning");
      }
    };
    themeCleanupTimer = setTimeout(cleanup, 900);
    transition.ready?.catch(() => {});
    transition.finished.catch(() => {}).finally(cleanup);
    return;
  }

  spawnFallbackThemeWave();
  commitThemeState(theme);
}

async function chooseProgram(program) {
  saveUnsent();
  stopPoll();
  triageUI.reset();
  closePageView();
  const version = ++state.viewVersion;
  state.program = program;
  state.conversation = null;
  state.run = null;
  triageUI.badge();
  $(".program-name").textContent = program.display_name;
  $("#account-role").textContent = program.role === "PROGRAM_ADMIN" ? "Admin program" : "Bug hunter";
  $("#admin-nav").hidden = program.role !== "PROGRAM_ADMIN";
  $("#history-label").textContent = program.role === "PROGRAM_ADMIN" ? "Laporan program" : "Laporan saya";
  await history();
  if (version === state.viewVersion) welcome();
}

async function history() {
  if (!state.program) return;
  const programId = state.program.program_id, version = state.viewVersion;
  const rows = await api(`/api/programs/${programId}/conversations`);
  if (version !== state.viewVersion || programId !== state.program?.program_id) return;
  const list = $("#conversation-list");
  list.replaceChildren();
  const query = $("#history-query").value.toLowerCase();
  const filtered = rows.filter(r => (r.draft_title || "Draf baru").toLowerCase().includes(query));
  if (!filtered.length && query) {
    list.append(node("p", "Tidak ada laporan yang cocok.", "empty-search"));
    return;
  }
  filtered.forEach(r => {
    const b = button(undefined, () => openConversation(r.conversation_id), "conversation-item");
    const icon = makeSvg("chat");
    const titleSpan = node("span", r.draft_title || "Draf baru", "conversation-text");
    const isSelected = !state.adminPage && r.conversation_id === state.conversation?.conversation_id;
    const dot = node("span", undefined, `thread-state${r.conversation_id === state.conversation?.conversation_id ? " active" : ""}`);
    dot.setAttribute("aria-hidden", "true");
    b.append(icon, titleSpan, dot);
    b.classList.toggle("selected", isSelected);
    list.append(b);
  });
}

async function startWithStarter(templateText) {
  saveUnsent();
  stopPoll();
  closePageView();
  const version = ++state.viewVersion;
  const c = await api(`/api/programs/${state.program.program_id}/conversations`, { method: "POST" });
  if (version !== state.viewVersion) return;
  state.drafts.set(c.conversation_id, templateText);
  await openConversation(c.conversation_id, version);
  $("#message-input").focus();
}

function welcome() {
  closePageView();
  const area = $("#chat-content");
  area.replaceChildren();
  $(".chat-view")?.classList.add("is-empty");
  if ($("#chat-inspector")) $("#chat-inspector").hidden = true;
  $(".run-area")?.replaceChildren();
  $(".triage-area")?.replaceChildren();
  $(".business-area")?.replaceChildren();

  const box = node("div", undefined, "welcome vv-crosshair vv-reveal");
  const badge = node("div", undefined, "welcome-badge");
  badge.append(makeSvg("shield-check"), node("span", "Validasi Terisolasi"));
  box.append(
    badge,
    node("h1", "Laporan apa yang ingin diperiksa?"),
    node("p", "Kirim teks atau lampiran TXT/MD untuk menyimpan draf sebelum meminta saran atau verifikasi.")
  );

  const starters = node("div", undefined, "welcome-starters");
  const templates = [
    {
      code: "BAC-08",
      icon: "lock",
      title: "BAC · Akses Lintas Akun",
      desc: "Uji penghapusan atau baca lampiran milik akun kedua.",
      draft: "Pengguna requester-a dapat menghapus lampiran milik requester-b melalui endpoint /api/attachments/{id} tanpa otorisasi kepemilikan."
    },
    {
      code: "XSS-08",
      icon: "terminal",
      title: "XSS · Pratinjau Notifikasi",
      desc: "Validasi eksekusi marker pada rute /notifications/preview.",
      draft: "Payload XSS tersimpan muncul tidak ter-escape saat pratinjau notifikasi dibuka oleh akun kedua pada /notifications/preview."
    },
    {
      code: "UP-04",
      icon: "file-code",
      title: "Upload · Nama Lampiran",
      desc: "Periksa sanitasi nama file lampiran pada daftar permintaan.",
      draft: "Nama berkas lampiran yang diunggah pada /requests/{id}/attachments memicu marker pada halaman daftar lampiran."
    }
  ];
  templates.forEach((tpl, idx) => {
    const card = button(undefined, () => startWithStarter(tpl.draft), `starter-card vv-reveal vv-d${idx + 1}`);
    const head = node("div", undefined, "starter-head");
    const ico = node("span", undefined, "starter-icon");
    ico.append(makeSvg(tpl.icon));
    head.append(ico, node("span", tpl.code, "starter-code"));
    card.append(head, node("strong", tpl.title), node("small", tpl.desc));
    starters.append(card);
    scheduleRevealCleanup(card);
  });

  const startBtn = iconButton("plus", "Buat laporan", newConversation, "primary-button");
  box.append(starters, startBtn);
  area.append(box);
  scheduleRevealCleanup(box);
  $("#composer-region").hidden = true;
}

async function newConversation() {
  saveUnsent();
  stopPoll();
  closePageView();
  const version = ++state.viewVersion;
  const c = await api(`/api/programs/${state.program.program_id}/conversations`, { method: "POST" });
  if (version !== state.viewVersion) return;
  await openConversation(c.conversation_id, version);
}

async function openConversation(id, requestedVersion) {
  saveUnsent();
  stopPoll();
  triageUI.reset();
  closePageView();
  const version = requestedVersion ?? ++state.viewVersion;
  const c = await api(`/api/conversations/${id}`);
  if (version !== state.viewVersion) return;
  state.conversation = c;
  state.run = null;
  $("#message-input").value = state.drafts.get(id) || "";
  renderConversation();
  await history();
  if (version !== state.viewVersion) return;
  closeNav();
  await triageUI.mount(c, version);
  if (version === state.viewVersion && c.run_ids.length) await loadRun(c.run_ids[0]);
  if (version === state.viewVersion) scrollSidebarToSelected();
}

function renderConversation() {
  const c = state.conversation, area = $("#chat-content");
  area.replaceChildren();
  $(".chat-view")?.classList.remove("is-empty");

  const heading = node("div", undefined, "chat-heading vv-reveal");
  const jumpBtn = iconButton("activity", "Inspektor Bukti", () => scrollToInspector($(".run-area") || $("#chat-inspector")), "secondary-button inspector-jump-only");
  jumpBtn.id = "jump-inspector-btn";
  heading.append(
    node("h1", c.draft_title || "Draf laporan"),
    jumpBtn
  );
  area.append(heading);
  scheduleRevealCleanup(heading);

  c.messages.forEach((m, idx) => {
    const box = node("article", undefined, `message vv-reveal vv-d${Math.min(idx + 1, 5)}`);
    const author = node("div", undefined, "message-author");
    author.append(makeSvg("user"), node("span", "Laporan · tersimpan"));
    box.append(author, node("div", m.body, "user-bubble"));
    area.append(box);
    scheduleRevealCleanup(box);
  });

  if (c.attachment) {
    const box = node("div", undefined, "attachment-preview vv-reveal");
    box.append(makeSvg("file"), node("span", `Lampiran tersimpan: ${c.attachment.original_name} · ${c.attachment.byte_size} byte`));
    area.append(box);
    scheduleRevealCleanup(box);
  }

  if (!c.messages.length && !c.attachment) {
    area.append(node("p", "Tulis laporan di bawah, lalu tekan Kirim untuk menyimpannya.", "empty-state-note"));
  }

  const actions = node("div", undefined, "draft-actions");
  if (own()) {
    actions.append(iconButton("shield-check", "Validasi snapshot", validation, "primary-button"));
    actions.append(iconButton("layers", "Siapkan review bukti bisnis", businessSnapshot, "secondary-button"));
  } else {
    actions.append(node("p", "Draf milik pelapor; admin meninjau hasil tanpa mengubah draf.", "fine-print"));
  }

  if (c.run_ids.length > 1) {
    const list = node("div", undefined, "run-switcher");
    c.run_ids.forEach((id, i) => {
      const b = button(`Run ${c.run_ids.length - i}`, async () => {
        await loadRun(id);
        scrollToInspector($(".run-area"));
      });
      if (state.run?.run_id === id) b.classList.add("primary-button");
      list.append(b);
    });
    area.append(list);
  }

  area.append(actions);
  if ($("#chat-inspector")) $("#chat-inspector").hidden = false;
  $(".run-area")?.replaceChildren();
  $(".triage-area")?.replaceChildren();
  $(".business-area")?.replaceChildren();
  renderRunPlaceholder();
  setInspectorTab("all");

  $("#composer-region").hidden = !own();
  $("#attachment-preview").hidden = true;
  guard(() => loadBusinessRecords(c, state.viewVersion));
}

function setSubmitBusy(btn, busy, idleText, busyText) {
  btn.disabled = busy;
  if (busy) {
    btn.replaceChildren(node("span", undefined, "vv-spinner"), node("span", busyText));
  } else {
    btn.replaceChildren(node("span", idleText));
  }
}

function businessSnapshot() {
  const c = state.conversation, form = node("form");
  form.append(node("p", "Simpan snapshot untuk review rekaman oleh admin. Langkah ini tidak menjalankan worker, model atau pengujian target."));
  const claim = field(form, "Klaim bisnis yang akan ditinjau", c.latest_claim?.category === "BUSINESS_LOGIC" ? c.latest_claim.primary_claim : "Pemenuhan barang harus mengikuti persetujuan dan hanya mengurangi stok sekali");
  claim.required = true;
  const asset = field(form, "Alias aset laporan", c.latest_claim?.asset_alias || "portal");
  const path = field(form, "Path fitur yang dilaporkan", c.latest_claim?.category === "BUSINESS_LOGIC" ? c.latest_claim.path || "/api/requests/" : "/api/requests/");
  const error = node("p", undefined, "composer-error");
  error.role = "alert";
  const submit = node("button", "Simpan snapshot untuk review", "primary-button");
  submit.type = "submit";
  form.append(error, submit);
  form.addEventListener("submit", async event => {
    event.preventDefault();
    setSubmitBusy(submit, true, "Simpan snapshot untuk review", "Menyimpan…");
    try {
      await api(`/api/conversations/${c.conversation_id}/reports`, {
        method: "POST",
        body: JSON.stringify({
          expected_draft_version: c.draft_version,
          claim: {
            category: "BUSINESS_LOGIC",
            primary_claim: claim.value,
            asset_alias: asset.value || null,
            path: path.value || null,
            method: "POST",
            account_aliases: []
          }
        })
      });
      $("#detail-dialog").close();
      if (state.conversation?.conversation_id === c.conversation_id) await openConversation(c.conversation_id);
      notice("Snapshot bisnis tersimpan. Admin dapat mengunggah rekaman untuk review; pengujian target belum dimulai.");
    } catch (e) {
      error.textContent = e.message;
    } finally {
      setSubmitBusy(submit, false, "Simpan snapshot untuk review", "Menyimpan…");
    }
  });
  panel("Siapkan review bukti bisnis", form, "Snapshot laporan · tanpa pengujian otomatis");
}

async function loadBusinessRecords(c, version) {
  const rows = c.report_id ? await api(`/api/reports/${c.report_id}/business-records`) : [];
  if (version !== state.viewVersion || state.conversation?.conversation_id !== c.conversation_id) return;
  const area = $(".business-area");
  if (!area) return;
  area.replaceChildren();
  const admin = state.program.role === "PROGRAM_ADMIN";
  if (c.latest_claim?.category !== "BUSINESS_LOGIC" && !rows.length) return;

  const title = node("h2");
  title.append(makeSvg("layers"), node("span", "Review rekaman bisnis"));
  area.append(title, node("p", "Rekaman unggahan diperiksa konsistensinya. Ini bukan pengujian target atau keputusan kerentanan.", "fine-print"));
  if (admin && c.latest_claim?.category === "BUSINESS_LOGIC" && c.latest_report_revision_id) {
    area.append(iconButton("upload", "Unggah rekaman JSON", () => businessImport(c), "secondary-button"));
  }
  if (!rows.length) {
    area.append(node("p", admin ? "Belum ada rekaman. Unggah JSON kontrol alur normal untuk ditinjau." : "Snapshot tersimpan. Ringkasan akan tampil setelah admin meninjau dan membagikannya.", "empty-state-note"));
  }
  rows.forEach(row => {
    const card = node("article", undefined, "assessment-card vv-reveal");
    const top = node("div", undefined, "assessment-top");
    const topLabel = node("div", undefined, "assessment-top-label");
    topLabel.append(makeSvg("file-code"), node("span", `Snapshot versi ${row.report_revision_number}`));
    top.append(topLabel, makeStatusPill(admin ? row.result.status : row.publication_status, statusTone(row.result.status), "check-circle"));
    card.append(top);

    const body = node("div", undefined, "assessment-content");
    body.append(
      node("h3", admin ? `Konsistensi rekaman: ${row.result.status}` : "Ringkasan review rekaman"),
      node("p", `Snapshot laporan: versi ${row.report_revision_number}`),
      node("p", row.summary || "Rekaman internal; belum dibagikan ke pelapor.")
    );
    const actions = node("div", undefined, "draft-actions");
    actions.append(iconButton("download", "Ekspor review rekaman", () => downloadBusinessReview(row), "secondary-button"));

    if (admin) {
      const grid = node("div", undefined, "metric-grid");
      grid.append(
        makeMetricCell("Status Review", `Status review: ${row.review_status} · publikasi: ${row.publication_status}`),
        makeMetricCell("Checksum", `SHA-256 rekaman: ${row.record_sha256}`, true)
      );
      body.append(grid, node("p", row.reviewer_note || "Belum ada catatan review."));
      const detail = node("details");
      const summary = node("summary", "Hasil konsistensi dan asal rekaman");
      summary.append(makeSvg("chevron-down"));
      detail.append(summary, node("pre", JSON.stringify({ result: row.result, provenance: row.provenance }, null, 2)));
      body.append(detail);

      actions.append(iconButton("file", "Lihat rekaman unggahan", async () => {
        const record = await api(`/api/business-records/${row.review_id}/record`);
        panel("Rekaman unggahan", node("pre", JSON.stringify(record, null, 2)), "Data unggahan · asal dan izin aktor belum disahkan");
      }, "secondary-button"));
      actions.append(iconButton("sliders", "Tinjau rekaman", () => businessReview(c, row), "secondary-button"));
      actions.append(iconButton("arrow-right", "Langkah berikutnya", () => businessWorkflow(row), "secondary-button"));
      if (row.review_status === "REVIEWED") {
        actions.append(iconButton("check-circle", "Bagikan ringkasan rekaman", async () => {
          await api(`/api/business-records/${row.review_id}/publish`, { method: "POST" });
          if (state.conversation?.conversation_id === c.conversation_id) await loadBusinessRecords(state.conversation, state.viewVersion);
          notice("Ringkasan rekaman dibagikan; catatan dan data mentah tetap internal.");
        }, "primary-button"));
      }
    }
    body.append(actions);
    card.append(body);
    area.append(card);
    scheduleRevealCleanup(card);
  });
}

function businessImport(c) {
  const form = node("form");
  form.append(node("p", "Unggah JSON kontrol normal empat event, maksimal 128 KiB. Versi aturan guideline aktif harus procurement-controls-v1. Data ini dilampirkan ke snapshot laporan; keaslian sumber dan izin aktor belum dibuktikan."));
  const file = field(form, "File rekaman bisnis", "", "file");
  file.accept = ".json,application/json";
  file.required = true;
  const error = node("p", undefined, "composer-error");
  error.role = "alert";
  const submit = node("button", "Periksa dan simpan rekaman", "primary-button");
  submit.type = "submit";
  form.append(error, submit);
  form.addEventListener("submit", async event => {
    event.preventDefault();
    setSubmitBusy(submit, true, "Periksa dan simpan rekaman", "Memeriksa…");
    error.textContent = "";
    try {
      const selected = file.files[0];
      if (!selected || selected.size > 131072) throw Error("Pilih file JSON maksimal 128 KiB.");
      const data = new FormData();
      data.append("file", selected);
      await api(`/api/reports/${c.report_id}/revisions/${c.latest_report_revision_id}/business-records`, { method: "POST", body: data });
      $("#detail-dialog").close();
      if (state.conversation?.conversation_id === c.conversation_id) await loadBusinessRecords(state.conversation, state.viewVersion);
      notice("Rekaman tersimpan untuk review; tidak ada request target atau model.");
    } catch (e) {
      error.textContent = e.message;
    } finally {
      setSubmitBusy(submit, false, "Periksa dan simpan rekaman", "Memeriksa…");
    }
  });
  panel("Unggah rekaman bisnis", form, "Hanya admin · hasil konsistensi, bukan verdict kerentanan");
}

function businessReview(c, row) {
  const form = node("form");
  form.append(node("p", "Tinjau konsistensi dan sumber rekaman. Catatan ini tidak menetapkan CONFIRMED/REFUTED dan tidak dibagikan ke pelapor."));
  const note = field(form, "Catatan review rekaman", row.reviewer_note || "", "textarea");
  note.required = true;
  note.maxLength = 2000;
  const error = node("p", undefined, "composer-error");
  error.role = "alert";
  const submit = node("button", "Simpan review rekaman", "primary-button");
  submit.type = "submit";
  form.append(error, submit);
  form.addEventListener("submit", async event => {
    event.preventDefault();
    setSubmitBusy(submit, true, "Simpan review rekaman", "Menyimpan…");
    try {
      await api(`/api/business-records/${row.review_id}/review`, { method: "POST", body: JSON.stringify({ reviewer_note: note.value }) });
      $("#detail-dialog").close();
      if (state.conversation?.conversation_id === c.conversation_id) await loadBusinessRecords(state.conversation, state.viewVersion);
      notice("Review tersimpan. Publikasi sebelumnya ditarik; bagikan kembali setelah siap.");
    } catch (e) {
      error.textContent = e.message;
    } finally {
      setSubmitBusy(submit, false, "Simpan review rekaman", "Menyimpan…");
    }
  });
  panel("Tinjau rekaman bisnis", form, "Catatan admin · tanpa perubahan hasil mentah");
}

function downloadBusinessReview(row) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(row, null, 2)], { type: "application/json" }));
  const link = node("a");
  link.href = url;
  link.download = `valvuln-business-review-${row.review_id}.json`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function businessWorkflow(row) {
  const context = await api(`/api/business-records/${row.review_id}/workflow`), box = node("div");
  box.append(node("p", context.summary), node("p", `Konteks memakai snapshot laporan versi ${context.binding.report_revision_number} dan aturan yang terikat pada rekaman.`));
  const steps = node("ol");
  context.next_actions.forEach(action => steps.append(node("li", action.instruction)));
  box.append(steps);
  box.append(node("p", "Langkah ini perlu ditinjau admin. Tidak ada pengujian target, panggilan model atau keputusan kerentanan yang dijalankan.", "fine-print"));
  const detail = node("details");
  detail.append(node("summary", "Konteks terstruktur untuk integrasi berikutnya"), node("pre", JSON.stringify(context, null, 2)));
  box.append(detail);
  box.append(button("Ekspor konteks review", () => {
    const url = URL.createObjectURL(new Blob([JSON.stringify(context, null, 2)], { type: "application/json" }));
    const link = node("a");
    link.href = url;
    link.download = `valvuln-business-context-${row.review_id}.json`;
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }));
  panel("Langkah berikutnya", box, "Workflow bukti · hanya admin program");
}

async function sendMessage(event) {
  event?.preventDefault();
  if (state.busy) return;
  state.busy = true;
  $("#send-button").disabled = true;
  try {
    if (!state.conversation) await newConversation();
    const text = $("#message-input").value;
    if (!text.trim()) return;
    const c = state.conversation;
    await api(`/api/conversations/${c.conversation_id}/messages`, {
      method: "POST",
      body: JSON.stringify({ body: text, title: c.draft_title || text.slice(0, 80), expected_draft_version: c.draft_version })
    });
    state.drafts.delete(c.conversation_id);
    $("#message-input").value = "";
    await openConversation(c.conversation_id);
    const chatScroll = $("#chat-scroll");
    if (chatScroll) smoothScrollTo(chatScroll.scrollHeight, chatScroll, 480);
    notice("Pesan tersimpan. Validasi belum dimulai.");
  } finally {
    state.busy = false;
    $("#send-button").disabled = false;
  }
}

async function upload() {
  const file = $("#file-input").files[0];
  if (!file || !state.conversation) return;
  const data = new FormData();
  data.append("file", file);
  await api(`/api/conversations/${state.conversation.conversation_id}/attachments`, { method: "POST", body: data });
  await openConversation(state.conversation.conversation_id);
  const chatScroll = $("#chat-scroll");
  if (chatScroll) smoothScrollTo(chatScroll.scrollHeight, chatScroll, 480);
  notice("Lampiran tersimpan; belum diuji.");
  $("#file-input").value = "";
}

async function validation(proposal = null) {
  const c = state.conversation;
  if (proposal && (proposal.conversation_id !== c?.conversation_id || proposal.expected_draft_version !== c.draft_version)) {
    throw Error("Draf berubah. Muat ulang saran AI.");
  }
  const form = node("form");
  const help = node("p");
  form.append(help);
  const prev = proposal?.claim || c.latest_claim || {};
  if (proposal) {
    form.prepend(node("p", `Draf dari saran ${proposal.mode.toUpperCase()} · scope backend: ${proposal.scope_decision} · ${proposal.policy_status}. Periksa semua field sebelum memulai.`));
    if (proposal.missing_information.length) {
      const list = node("ul");
      proposal.missing_information.forEach(text => list.append(node("li", text)));
      form.append(list);
    }
  }
  const kind = select(form, "Kemampuan validasi", [
    ["BAC", "BAC · hapus lampiran lintas akun"],
    ["XSS", "XSS · pratinjau notifikasi (fixture tetap)"],
    ["UPLOAD", "Upload · nama lampiran (fixture tetap)"]
  ], ["BAC", "XSS", "UPLOAD"].includes(prev.category) ? prev.category : "BAC");
  const claim = field(form, "Klaim utama", prev.primary_claim || "Akun penguji dapat menghapus lampiran milik akun lain");
  const asset = field(form, "Alias aset terdaftar", prev.asset_alias || "portal");
  const victim = field(form, "Path lampiran korban (milik akun kedua)", prev.path || "/api/attachments/");
  const control = field(form, "Path lampiran kontrol (milik akun pertama)", prev.control_path || "/api/attachments/");
  const account = select(form, "Akun penguji → akun pemilik korban", [
    ["requester-a", "requester-a → requester-b"],
    ["requester-b", "requester-b → requester-a"]
  ], prev.account_aliases?.[0] || "requester-a");
  const mode = select(form, "Pelaksanaan tools", [
    ["LAB", "Lab aktual · planner mock"],
    ["NONE", "Simulasi plumbing · tanpa request target"]
  ], "LAB");
  const bacDraft = {
    path: prev.category && prev.category !== "BAC" ? "/api/attachments/" : victim.value,
    claim: prev.category && prev.category !== "BAC" ? "Akun penguji dapat menghapus lampiran milik akun lain" : claim.value
  };
  const uploadDraft = {
    path: prev.category === "UPLOAD" ? prev.path : "/requests/",
    claim: prev.category === "UPLOAD" ? prev.primary_claim : "Nama fixture upload dapat mengeksekusi marker pada daftar lampiran"
  };
  let lastKind = kind.value;
  const xssClaim = "Fixture marker dapat mengeksekusi JavaScript pada pratinjau notifikasi";

  function capabilityChanged(initial = false) {
    const xss = kind.value === "XSS", up = kind.value === "UPLOAD";
    if (!initial) {
      const draft = lastKind === "BAC" ? bacDraft : lastKind === "UPLOAD" ? uploadDraft : null;
      if (draft) {
        draft.path = victim.value;
        draft.claim = claim.value;
      }
    }
    if (xss) {
      victim.value = "/notifications/preview";
      if (!initial || !prev.primary_claim) claim.value = xssClaim;
    } else if (up) {
      victim.value = uploadDraft.path;
      claim.value = uploadDraft.claim;
    } else if (!initial) {
      victim.value = bacDraft.path;
      claim.value = bacDraft.claim;
    }
    lastKind = kind.value;
    victim.readOnly = xss;
    victim.parentElement.querySelector("label").textContent = up
      ? "Path daftar lampiran permintaan milik A (/requests/ID/attachments)"
      : xss ? "Rute pratinjau terdaftar" : "Path lampiran korban (milik akun kedua)";
    control.parentElement.hidden = xss || up;
    control.disabled = xss || up;
    account.parentElement.hidden = xss || up;
    help.textContent = up
      ? "Sistem mengunggah dua fixture teks kecil dengan nama kontrol/marker, lalu membaca daftar melalui akun B yang ditugaskan. File laporan tidak dieksekusi. Isi berkas dan penimpaan tidak diuji pada run ini; operator perlu reset."
      : xss
        ? "Kontrol inert dan marker tetap diuji di dua akun melalui browser lab. Payload laporan tidak dijalankan; verdict hanya untuk fixture dan rute ini. Operator perlu reset sebelum run berikutnya."
        : "Satu klaim utama: penghapusan lampiran lintas akun. HTTP lab akan benar-benar mengubah data sintetis, termasuk objek kontrol. Operator perlu reset sebelum run berikutnya.";
  }

  kind.addEventListener("change", () => capabilityChanged());
  capabilityChanged(true);
  const error = node("p", undefined, "composer-error");
  error.role = "alert";
  const submit = node("button", "Mulai validasi snapshot", "primary-button");
  submit.type = "submit";
  form.append(error, submit);
  const key = crypto.randomUUID();
  form.addEventListener("submit", async e => {
    e.preventDefault();
    setSubmitBusy(submit, true, "Mulai validasi snapshot", "Memulai run…");
    error.textContent = "";
    try {
      const xss = kind.value === "XSS", up = kind.value === "UPLOAD";
      const snapshot = await api(`/api/conversations/${c.conversation_id}/reports`, {
        method: "POST",
        body: JSON.stringify({
          expected_draft_version: c.draft_version,
          source_triage_id: proposal?.source_triage_id || null,
          claim: {
            asset_alias: asset.value || null,
            path: xss ? "/notifications/preview" : victim.value || null,
            control_path: xss || up ? null : control.value || null,
            method: xss || up ? "GET" : "DELETE",
            category: kind.value,
            account_aliases: xss || up ? ["requester-a", "requester-b"] : [account.value, account.value === "requester-a" ? "requester-b" : "requester-a"],
            primary_claim: claim.value,
            claim_count: prev.claim_count || 1
          }
        })
      });
      const run = await api(`/api/reports/${snapshot.report_id}/runs`, {
        method: "POST",
        headers: { "Idempotency-Key": key },
        body: JSON.stringify({ report_revision_id: snapshot.report_revision_id, execution_mode: "mock", tool_execution_mode: mode.value })
      });
      $("#detail-dialog").close();
      await openConversation(c.conversation_id);
      await loadRun(run.run_id);
      scrollToInspector($(".run-area"));
    } catch (err) {
      error.textContent = err.message;
    } finally {
      setSubmitBusy(submit, false, "Mulai validasi snapshot", "Memulai run…");
    }
  });
  panel("Validasi snapshot", form, "Kirim menyimpan draf; Validasi memulai run");
}

async function loadRun(id) {
  stopPoll();
  const version = state.pollVersion, conversationId = state.conversation?.conversation_id;
  const run = await api(`/api/runs/${id}`);
  if (version !== state.pollVersion || conversationId !== state.conversation?.conversation_id) return;
  state.run = run;
  triageUI.badge();
  renderRun();
  if (active(run) && !document.hidden) {
    state.timer = setTimeout(() => guard(() => loadRun(id)), 2000);
  }
}

function renderRun() {
  const run = state.run, area = $(".run-area");
  if (!area) return;
  area.replaceChildren();

  const card = node("article", undefined, "assessment-card vv-reveal");
  const verdict = (run.assessment?.system_verified || run.assessment)?.verdict;
  if (verdict === "CONFIRMED") card.classList.add("verdict-confirmed", "vv-crosshair");
  else if (verdict === "REFUTED") card.classList.add("verdict-refuted", "vv-crosshair");
  else if (verdict || run.awaiting_review) card.classList.add("verdict-warning", "vv-crosshair");
  else card.classList.add("verdict-verifier");
  const top = node("div", undefined, "assessment-top");
  const topLabel = node("div", undefined, "assessment-top-label");
  topLabel.append(makeSvg("activity"), node("span", `VERIFIER LAB · ${run.process_status} · ${run.execution_mode} / tools ${run.tool_execution_mode}`));
  const topPill = makeStatusPill(run.process_status, statusTone(run.process_status), active(run) ? "clock" : "shield-check");
  top.append(topLabel, topPill);
  card.append(top);

  const body = node("div", undefined, "assessment-content");
  const grid = node("div", undefined, "metric-grid");
  grid.append(
    makeMetricCell("Scope & Kemampuan", `Scope: ${run.scope_decision} · kemampuan: ${run.capability_decision}`),
    makeMetricCell("Counter Eksekusi", `Request target: ${run.counters.target_requests} · model calls: ${run.counters.model_calls}`, true)
  );
  body.append(grid);

  if (run.claim_origin) {
    body.append(node("p", `Klaim dari saran ${run.claim_origin.mode.toUpperCase()} · ${run.claim_origin.provider} · model diminta ${run.claim_origin.requested_model}; dikonfirmasi pemilik laporan.`, "fine-print"));
  }

  if (run.error_code) {
    const err = node("p", `Alasan: ${run.error_code}`, "composer-error");
    err.setAttribute("role", "alert");
    body.append(err);
  }

  if (run.assessment) {
    const a = run.assessment.system_verified || run.assessment;
    const banner = node("div", undefined, "verdict-banner");
    const vTitle = node("h2", a.verdict, "assessment-title");
    const vPill = makeStatusPill(a.verdict, statusTone(a.verdict), a.verdict === "CONFIRMED" ? "shield-check" : a.verdict === "REFUTED" ? "shield-alert" : "info");
    banner.append(vTitle, vPill);
    body.append(banner, node("p", a.reasoning || a.summary));
    if (run.assessment.analyst_override) {
      body.append(node("p", `Keputusan analis: ${run.assessment.analyst_override}`));
    }
  } else if (run.awaiting_review) {
    const waitCallout = node("div", undefined, "notice-callout warning");
    waitCallout.append(makeSvg("clock"), node("span", "Pengujian selesai; ringkasan menunggu review dan publikasi admin."));
    body.append(waitCallout);
  }

  if (run.tool_execution_mode === "LAB") {
    body.append(node("p",
      run.validation_kind === "UPLOAD"
        ? "Planner mock; upload fixture dan browser lab aktual. Bukan hasil model live."
        : run.validation_kind === "XSS"
          ? "Planner mock; bukti browser lab aktual dengan fixture tetap. Bukan hasil model live."
          : "Planner mock; bukti HTTP lab aktual. Bukan hasil model live.",
      "fine-print"
    ));
  }

  const actions = node("div", undefined, "draft-actions");
  if (active(run)) {
    actions.append(iconButton("stop", "Batalkan run", async () => {
      await api(`/api/runs/${run.run_id}/cancel`, { method: "POST" });
      await loadRun(run.run_id);
    }, "secondary-button"));
  }
  actions.append(iconButton("download", "Ekspor JSON", () => exportRun(run.run_id), "secondary-button"));
  actions.append(iconButton("activity", "Ringkasan observasi", () => showObservationSummary(run), "secondary-button"));

  if (state.program.role === "PROGRAM_ADMIN" && run.assessment) {
    actions.append(iconButton("sliders", "Review hasil", () => review(run), "secondary-button"));
    actions.append(iconButton("check-circle", "Bagikan ringkasan", async () => {
      await api(`/api/runs/${run.run_id}/publish`, { method: "POST" });
      await loadRun(run.run_id);
      notice("Ringkasan aman dibagikan ke pelapor.");
    }, "primary-button"));

    const raw = node("details");
    const summary = node("summary", "Hasil mentah dan assessment verifier");
    summary.append(makeSvg("chevron-down"));
    raw.append(summary, node("pre", JSON.stringify(run.assessment, null, 2)));
    body.append(raw);
  }

  if (run.evidence?.length) {
    const list = node("div", undefined, "draft-actions");
    run.evidence.forEach((e, i) => list.append(iconButton("file", `Bukti ${i + 1}`, async () => {
      const data = await api(`/api/evidence/${e.evidence_id}`);
      panel("Bukti internal", node("pre", JSON.stringify(data, null, 2)), "Hanya admin program · respons ditampilkan sebagai teks");
    }, "secondary-button")));
    body.append(list);
  }

  body.append(actions);
  card.append(body);
  area.append(card);
  scheduleRevealCleanup(card);
}

async function exportRun(id) {
  const data = await api(`/api/runs/${id}/export`);
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
  const a = node("a");
  a.href = url;
  a.download = `valvuln-${id}.json`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function review(run) {
  const form = node("form");
  const choice = select(form, "Keputusan analis (hasil mentah tetap tersimpan)", [
    ["", "Ikuti verifier"],
    ["CONFIRMED", "CONFIRMED"],
    ["REFUTED", "REFUTED"],
    ["INCONCLUSIVE", "INCONCLUSIVE"]
  ], run.assessment.analyst_override || "");
  const note = field(form, "Catatan review internal", run.assessment.reviewer_note || "", "textarea");
  note.required = true;
  const submit = node("button", "Simpan review", "primary-button");
  submit.type = "submit";
  form.append(submit);
  form.addEventListener("submit", e => {
    e.preventDefault();
    guard(async () => {
      setSubmitBusy(submit, true, "Simpan review", "Menyimpan…");
      try {
        await api(`/api/runs/${run.run_id}/review`, {
          method: "POST",
          body: JSON.stringify({ analyst_override: choice.value || null, reviewer_note: note.value })
        });
        $("#detail-dialog").close();
        await loadRun(run.run_id);
      } finally {
        setSubmitBusy(submit, false, "Simpan review", "Menyimpan…");
      }
    });
  });
  panel("Review hasil", form, "Catatan internal tidak dibagikan ke pelapor");
}

const SCOPE_ALLOWED_METHODS = new Set(["GET", "POST", "PUT", "PATCH", "DELETE"]);
const SCOPE_ALLOWED_CAPS = new Set(["BAC", "XSS", "UPLOAD", "BUSINESS_LOGIC"]);
const SCOPE_ALLOWED_ROOT_KEYS = new Set(["in_scope_rules", "out_of_scope_rules", "business_rules", "business_rules_version"]);
const SCOPE_ALLOWED_RULE_KEYS = new Set(["asset_alias", "path_template", "methods", "capabilities"]);
const SCOPE_BASIC_TEMPLATE = {
  source_text: "Lab lokal portal pengadaan. Izin eksplisit validasi BAC lampiran menggunakan dua akun uji terisolasi (requester-a dan requester-b).",
  rules: {
    in_scope_rules: [
      {
        asset_alias: "portal",
        path_template: "/api/attachments/{id}",
        methods: ["GET", "DELETE"],
        capabilities: ["BAC"]
      }
    ],
    out_of_scope_rules: [],
    business_rules: "",
    business_rules_version: null
  }
};

function validateScopeRuleList(list, listKey, listLabel, minItems) {
  const errors = [];
  if (!Array.isArray(list)) {
    errors.push({ field: listKey, message: `${listLabel}: harus berupa array JSON ([ ... ]).` });
    return errors;
  }
  if (list.length < minItems) {
    errors.push({ field: listKey, message: `${listLabel}: tambahkan minimal ${minItems} aturan target.` });
  }
  if (list.length > 24) {
    errors.push({ field: listKey, message: `${listLabel}: maksimal 24 aturan per daftar.` });
  }
  list.slice(0, 24).forEach((rule, idx) => {
    const prefix = `${listLabel} · ${idx + 1}`;
    const pathPrefix = `${listKey}.${idx}`;
    if (!rule || typeof rule !== "object" || Array.isArray(rule)) {
      errors.push({ field: pathPrefix, message: `${prefix}: setiap item aturan harus berupa objek JSON.` });
      return;
    }
    Object.keys(rule).forEach(k => {
      if (!SCOPE_ALLOWED_RULE_KEYS.has(k)) {
        errors.push({ field: `${pathPrefix}.${k}`, message: `${prefix}: field tambahan "${k}" ditolak (extra_forbidden).` });
      }
    });
    if (typeof rule.asset_alias !== "string" || !/^[a-z0-9-]{1,64}$/.test(rule.asset_alias)) {
      errors.push({ field: `${pathPrefix}.asset_alias`, message: `${prefix} · Alias aset: gunakan huruf kecil, angka, dan tanda minus (1–64 karakter, contoh: portal).` });
    }
    if (typeof rule.path_template !== "string" || rule.path_template.length < 1 || rule.path_template.length > 200 || !rule.path_template.startsWith("/") || /[\s?#%]/.test(rule.path_template)) {
      errors.push({ field: `${pathPrefix}.path_template`, message: `${prefix} · Pola path: awali dengan "/" (1–200 karakter) tanpa spasi, ?, #, atau %.` });
    }
    if (!Array.isArray(rule.methods) || rule.methods.length < 1 || rule.methods.length > 5) {
      errors.push({ field: `${pathPrefix}.methods`, message: `${prefix} · Metode HTTP: wajib array 1–5 item (GET, POST, PUT, PATCH, DELETE).` });
    } else if (rule.methods.some(m => !SCOPE_ALLOWED_METHODS.has(m))) {
      errors.push({ field: `${pathPrefix}.methods`, message: `${prefix} · Metode HTTP: hanya mendukung GET, POST, PUT, PATCH, atau DELETE.` });
    }
    if (!Array.isArray(rule.capabilities) || rule.capabilities.length < 1 || rule.capabilities.length > 4) {
      errors.push({ field: `${pathPrefix}.capabilities`, message: `${prefix} · Kategori kemampuan: wajib array 1–4 item (BAC, XSS, UPLOAD, BUSINESS_LOGIC).` });
    } else if (rule.capabilities.some(c => !SCOPE_ALLOWED_CAPS.has(c))) {
      errors.push({ field: `${pathPrefix}.capabilities`, message: `${prefix} · Kategori kemampuan: hanya mendukung BAC, XSS, UPLOAD, atau BUSINESS_LOGIC.` });
    }
  });
  return errors;
}

function validateScopeEditorInput(sourceText, rawJsonText) {
  const errors = [];
  const utf8Bytes = new TextEncoder().encode(sourceText).length;
  if (!sourceText.trim()) {
    errors.push({ field: "source_text", message: "Teks guideline: wajib diisi dan tidak boleh hanya spasi." });
  } else if (sourceText.length > 32000 || utf8Bytes > 131072) {
    errors.push({ field: "source_text", message: "Teks guideline: melampaui batas maksimal 32.000 karakter atau 128 KiB UTF-8." });
  }

  let parsed = null;
  if (!rawJsonText.trim()) {
    errors.push({ field: "rules", message: "Aturan scope terstruktur (JSON): wajib diisi objek JSON." });
  } else {
    try {
      parsed = JSON.parse(rawJsonText);
    } catch {
      errors.push({ field: "rules", message: "Aturan scope terstruktur (JSON): JSON tidak sah. Hapus penanda ``` dan periksa tanda kutip, kurung, serta koma." });
    }
  }

  if (parsed !== null && (typeof parsed !== "object" || Array.isArray(parsed))) {
    errors.push({ field: "rules", message: "Aturan scope terstruktur (JSON): harus berupa objek JSON ({ ... })." });
    parsed = null;
  }

  if (parsed) {
    if (Object.prototype.hasOwnProperty.call(parsed, "source_text")) {
      errors.push({ field: "source_text", message: "Hapus key source_text dari kolom JSON; teks diambil otomatis dari kolom Teks guideline." });
    }
    Object.keys(parsed).forEach(k => {
      if (k !== "source_text" && !SCOPE_ALLOWED_ROOT_KEYS.has(k)) {
        errors.push({ field: k, message: `Field tambahan "${k}" tidak diizinkan oleh skema ScopeDraft.` });
      }
    });
    errors.push(...validateScopeRuleList(parsed.in_scope_rules, "in_scope_rules", "Aturan in-scope", 1));
    if (parsed.out_of_scope_rules !== undefined) {
      errors.push(...validateScopeRuleList(parsed.out_of_scope_rules, "out_of_scope_rules", "Aturan out-of-scope", 0));
    }
    if (Array.isArray(parsed.in_scope_rules) && Array.isArray(parsed.out_of_scope_rules)) {
      const serialize = r => JSON.stringify({
        asset_alias: r?.asset_alias,
        path_template: r?.path_template,
        methods: r?.methods,
        capabilities: r?.capabilities
      });
      const deniedSet = new Set(parsed.out_of_scope_rules.map(serialize));
      if (parsed.in_scope_rules.some(r => deniedSet.has(serialize(r)))) {
        errors.push({ field: "in_scope_rules", message: "AMBIGUOUS_RULE: terdapat aturan yang identik pada in_scope_rules dan out_of_scope_rules." });
      }
    }
    if (parsed.business_rules !== undefined) {
      if (typeof parsed.business_rules !== "string") {
        errors.push({ field: "business_rules", message: "Aturan bisnis: harus berupa string teks." });
      } else if (parsed.business_rules.length > 4000) {
        errors.push({ field: "business_rules", message: "Aturan bisnis: maksimal 4.000 karakter." });
      }
    }
    if (parsed.business_rules_version !== undefined && parsed.business_rules_version !== null) {
      if (typeof parsed.business_rules_version !== "string" || !/^[A-Za-z0-9._-]{1,64}$/.test(parsed.business_rules_version)) {
        errors.push({ field: "business_rules_version", message: "Versi aturan bisnis: gunakan 1–64 karakter alfanumerik, titik, garis bawah, atau tanda minus tanpa spasi." });
      }
    }
  }

  return { valid: errors.length === 0, errors, parsed, utf8Bytes };
}

function renderAdminShellHeader(mode, titleText, subtitleText) {
  const header = node("header", undefined, "admin-header vv-crosshair");
  const info = node("div");
  const kicker = node("span", undefined, "admin-kicker");
  kicker.append(makeSvg("shield-check"), node("span", "ADMINISTRASI PROGRAM · ROLE SERVER-SIDE"));
  info.append(kicker, node("h1", titleText, "admin-title"), node("p", subtitleText, "admin-subtitle"));

  const actions = node("div", undefined, "admin-header-actions");
  const tabs = node("div", undefined, "admin-mode-tabs");
  tabs.setAttribute("role", "tablist");
  tabs.setAttribute("aria-label", "Navigasi halaman admin");

  const repTab = button(undefined, () => openAdminPage("reports"), `admin-mode-tab${mode === "reports" ? " is-active" : ""}`);
  repTab.setAttribute("role", "tab");
  repTab.setAttribute("aria-selected", String(mode === "reports"));
  repTab.append(makeSvg("inbox"), node("span", "Antrean Laporan"));

  const guideTab = button(undefined, () => openAdminPage("guidelines"), `admin-mode-tab${mode === "guidelines" ? " is-active" : ""}`);
  guideTab.setAttribute("role", "tab");
  guideTab.setAttribute("aria-selected", String(mode === "guidelines"));
  guideTab.append(makeSvg("sliders"), node("span", "Guideline & Scope JSON"));

  tabs.append(repTab, guideTab);
  actions.append(tabs, iconButton("chat", "Ruang Kerja", () => closePageView(), "secondary-button"));
  header.append(info, actions);
  return header;
}

function effectiveRunVerdict(run) {
  if (!run?.assessment) return null;
  return run.assessment.analyst_override || (run.assessment.system_verified || run.assessment).verdict || null;
}

function openAdminQuickReview(row, onUpdated) {
  const run = row.latestRun;
  if (!run?.assessment) return;
  const sys = run.assessment.system_verified || run.assessment;
  const box = node("div");

  const banner = node("div", undefined, "verdict-banner");
  banner.append(
    node("h2", sys.verdict || run.process_status, "assessment-title"),
    makeStatusPill(sys.verdict || run.process_status, statusTone(sys.verdict || run.process_status), sys.verdict === "CONFIRMED" ? "shield-check" : sys.verdict === "REFUTED" ? "shield-alert" : "info")
  );
  const grid = node("div", undefined, "metric-grid");
  grid.append(
    makeMetricCell("Run & Kategori", `${run.validation_kind} · ${run.execution_mode} / ${run.tool_execution_mode}`, true),
    makeMetricCell("Status Publikasi", `${run.assessment.review_status || "UNREVIEWED"} · ${run.assessment.publication_status || "PRIVATE"}`)
  );
  box.append(banner, node("p", sys.reasoning || sys.summary || "Belum ada ringkasan sistem."), grid);

  const form = node("form");
  const choice = select(form, "Keputusan analis (hasil mentah tetap tersimpan)", [
    ["", "Ikuti verifier"],
    ["CONFIRMED", "CONFIRMED"],
    ["REFUTED", "REFUTED"],
    ["INCONCLUSIVE", "INCONCLUSIVE"]
  ], run.assessment.analyst_override || "");
  const note = field(form, "Catatan review internal", run.assessment.reviewer_note || "", "textarea");
  note.required = true;
  const errorEl = node("p", undefined, "composer-error");
  errorEl.role = "alert";
  const submit = node("button", "Simpan review", "primary-button");
  submit.type = "submit";
  const actionRow = node("div", undefined, "draft-actions");
  actionRow.append(submit);

  if (run.assessment.review_status === "REVIEWED" && run.assessment.publication_status !== "PUBLISHED") {
    actionRow.append(iconButton("check-circle", "Bagikan ringkasan", async () => {
      await api(`/api/runs/${run.run_id}/publish`, { method: "POST" });
      const freshRun = await api(`/api/runs/${run.run_id}`);
      $("#detail-dialog").close();
      notice("Ringkasan aman dibagikan ke pelapor.");
      await onUpdated(freshRun);
    }, "secondary-button"));
  }
  actionRow.append(iconButton("chat", "Buka Thread Penuh", async () => {
    $("#detail-dialog").close();
    await openConversation(row.conversation_id);
  }, "secondary-button"));

  form.append(errorEl, actionRow);
  form.addEventListener("submit", e => {
    e.preventDefault();
    errorEl.textContent = "";
    guard(async () => {
      setSubmitBusy(submit, true, "Simpan review", "Menyimpan…");
      try {
        await api(`/api/runs/${run.run_id}/review`, {
          method: "POST",
          body: JSON.stringify({ analyst_override: choice.value || null, reviewer_note: note.value })
        });
        const freshRun = await api(`/api/runs/${run.run_id}`);
        $("#detail-dialog").close();
        notice("Review hasil tersimpan; siap dibagikan ke pelapor.");
        await onUpdated(freshRun);
      } catch (err) {
        errorEl.textContent = err.message;
      } finally {
        setSubmitBusy(submit, false, "Simpan review", "Menyimpan…");
      }
    });
  });

  box.append(form);
  panel(`Review cepat · ${row.draft_title || "Draf baru"}`, box, "Hanya admin program · catatan internal tetap privat");
}

async function showAdminReportsPage() {
  const pageView = $("#page-view");
  const program = state.program;
  if (!pageView || !program || program.role !== "PROGRAM_ADMIN") return;

  const version = ++state.viewVersion;
  const programId = program.program_id;
  pageView.replaceChildren(
    (() => {
      const shell = node("div", undefined, "admin-shell");
      shell.append(renderAdminShellHeader("reports", "Antrean Laporan Program", "Pantau seluruh laporan masuk, status run verifier lab, review analis, dan publikasi ringkasan ke pelapor."));
      const loadingBox = node("div", undefined, "admin-panel");
      loadingBox.append(node("div", undefined, "vv-skeleton"), node("p", "Memuat daftar laporan dan ringkasan run dari server…", "fine-print"));
      shell.append(loadingBox);
      return shell;
    })()
  );

  const [convos, reports] = await Promise.all([
    api(`/api/programs/${programId}/conversations`),
    api(`/api/programs/${programId}/reports`)
  ]);
  if (version !== state.viewVersion || state.adminPage !== "reports" || state.program?.program_id !== programId) return;

  const reportByConvo = new Map(reports.map(r => [r.conversation_id, r]));
  const queueRows = convos.map(c => ({
    conversation_id: c.conversation_id,
    draft_title: c.draft_title || "Draf baru",
    draft_version: c.draft_version ?? 0,
    owner_user_id: c.owner_user_id,
    report_id: reportByConvo.get(c.conversation_id)?.report_id || null,
    hydrated: false,
    hasAttachment: false,
    messageCount: 0,
    runCount: 0,
    latestClaim: null,
    latestRun: null,
    businessCount: 0
  }));

  const shell = node("div", undefined, "admin-shell");
  shell.append(renderAdminShellHeader("reports", "Antrean Laporan Program", "Pantau seluruh laporan masuk, status run verifier lab, review analis, dan publikasi ringkasan ke pelapor."));

  const kpiGrid = node("div", undefined, "admin-kpi-grid");
  const makeKpi = (id, label, sub) => {
    const card = node("div", undefined, "admin-kpi-card");
    const val = node("strong", "0");
    val.id = id;
    card.append(node("span", label), val, node("small", sub));
    return card;
  };
  kpiGrid.append(
    makeKpi("admin-kpi-total", "TOTAL PERCAKAPAN", "Laporan & draf di program"),
    makeKpi("admin-kpi-review", "MENUNGGU REVIEW", "Run selesai belum dipublikasi"),
    makeKpi("admin-kpi-active", "RUN AKTIF / ANTRE", "Sedang QUEUED atau LEASED"),
    makeKpi("admin-kpi-confirmed", "TERKONFIRMASI LAB", "Verdict CONFIRMED nyata")
  );
  shell.append(kpiGrid);

  const toolbar = node("div", undefined, "admin-toolbar");
  const searchGroup = node("div", undefined, "admin-filter-group");
  const searchLabel = node("label", "Cari Laporan / ID");
  searchLabel.htmlFor = "admin-queue-search";
  const searchInput = node("input");
  searchInput.id = "admin-queue-search";
  searchInput.type = "search";
  searchInput.placeholder = "Judul laporan, ID percakapan, atau kategori…";
  searchInput.value = state.adminQueueFilters.query;
  searchGroup.append(searchLabel, searchInput);

  const statusGroup = node("div", undefined, "admin-filter-group");
  const statusLabel = node("label", "Filter Status");
  statusLabel.htmlFor = "admin-filter-status";
  const statusSelect = node("select");
  statusSelect.id = "admin-filter-status";
  [
    ["all", "Semua status"],
    ["awaiting_review", "Menunggu review / publikasi"],
    ["published", "Sudah dipublikasi"],
    ["running", "Sedang antre / jalan"],
    ["draft", "Draf (belum run)"]
  ].forEach(([val, txt]) => {
    const opt = node("option", txt);
    opt.value = val;
    statusSelect.append(opt);
  });
  statusSelect.value = state.adminQueueFilters.status;
  statusGroup.append(statusLabel, statusSelect);

  const verdictGroup = node("div", undefined, "admin-filter-group");
  const verdictLabel = node("label", "Filter Verdict");
  verdictLabel.htmlFor = "admin-filter-verdict";
  const verdictSelect = node("select");
  verdictSelect.id = "admin-filter-verdict";
  [
    ["all", "Semua verdict"],
    ["CONFIRMED", "CONFIRMED"],
    ["REFUTED", "REFUTED"],
    ["INCONCLUSIVE", "INCONCLUSIVE"],
    ["BUSINESS_LOGIC", "Rekaman BUSINESS_LOGIC"],
    ["NONE", "Belum ada verdict"]
  ].forEach(([val, txt]) => {
    const opt = node("option", txt);
    opt.value = val;
    verdictSelect.append(opt);
  });
  verdictSelect.value = state.adminQueueFilters.verdict;
  verdictGroup.append(verdictLabel, verdictSelect);

  const refreshBtn = iconButton("refresh", "Muat ulang", () => showAdminReportsPage(), "secondary-button");
  toolbar.append(searchGroup, statusGroup, verdictGroup, refreshBtn);
  shell.append(toolbar);

  const metaBar = node("div", undefined, "admin-toolbar-meta");
  const countText = node("span", `Menampilkan ${queueRows.length} percakapan…`);
  countText.id = "admin-queue-count";
  countText.setAttribute("aria-live", "polite");
  const hydrateStatus = node("span", queueRows.length ? "Menyelaraskan status run…" : "Antrean kosong");
  metaBar.append(countText, hydrateStatus);
  shell.append(metaBar);

  const tableWrap = node("div", undefined, "ledger-table-wrap");
  const table = node("table", undefined, "ledger-table");
  const thead = node("thead");
  const headRow = node("tr");
  ["Laporan", "Kategori & Mode", "Status & Review", "Verdict", "Aksi Cepat"].forEach(h => headRow.append(node("th", h)));
  thead.append(headRow);
  const tbody = node("tbody");
  tbody.id = "admin-queue-tbody";
  table.append(thead, tbody);
  tableWrap.append(table);

  const emptyHolder = node("div");
  shell.append(tableWrap, emptyHolder);
  pageView.replaceChildren(shell);

  const renderQueue = () => {
    if (version !== state.viewVersion || state.adminPage !== "reports") return;
    const total = queueRows.length;
    const awaiting = queueRows.filter(r => r.latestRun && (r.latestRun.awaiting_review || (r.latestRun.assessment && r.latestRun.assessment.publication_status !== "PUBLISHED"))).length;
    const activeRuns = queueRows.filter(r => active(r.latestRun)).length;
    const confirmed = queueRows.filter(r => effectiveRunVerdict(r.latestRun) === "CONFIRMED").length;
    $("#admin-kpi-total").textContent = String(total);
    $("#admin-kpi-review").textContent = String(awaiting);
    $("#admin-kpi-active").textContent = String(activeRuns);
    $("#admin-kpi-confirmed").textContent = String(confirmed);

    const q = state.adminQueueFilters.query.trim().toLowerCase();
    const fs = state.adminQueueFilters.status;
    const fv = state.adminQueueFilters.verdict;

    const filtered = queueRows.filter(r => {
      const run = r.latestRun;
      const verdict = effectiveRunVerdict(run);
      const isPub = run?.assessment?.publication_status === "PUBLISHED";
      const isAwait = Boolean(run && (run.awaiting_review || (run.assessment && !isPub)));
      const isAct = active(run);

      if (fs === "awaiting_review" && !isAwait) return false;
      if (fs === "published" && !isPub) return false;
      if (fs === "running" && !isAct) return false;
      if (fs === "draft" && run) return false;

      if (fv === "NONE" && verdict) return false;
      if (fv === "BUSINESS_LOGIC" && r.latestClaim?.category !== "BUSINESS_LOGIC" && r.businessCount === 0) return false;
      if (["CONFIRMED", "REFUTED", "INCONCLUSIVE"].includes(fv) && verdict !== fv) return false;

      if (q) {
        const hay = [
          r.draft_title,
          r.conversation_id,
          r.report_id || "",
          r.owner_user_id || "",
          run?.run_id || "",
          run?.validation_kind || "",
          r.latestClaim?.category || "",
          r.latestClaim?.asset_alias || ""
        ].join(" ").toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });

    countText.textContent = `Menampilkan ${filtered.length} dari ${total} percakapan program`;
    tbody.replaceChildren();
    emptyHolder.replaceChildren();

    if (!filtered.length) {
      tableWrap.hidden = true;
      const empty = node("div", undefined, "vv-empty-state");
      empty.append(
        node("strong", total ? "Tidak ada laporan yang cocok dengan filter" : "Belum ada laporan pada program ini"),
        node("p", total ? "Sesuaikan kata kunci, filter status, atau filter verdict untuk melihat seluruh antrean." : "Bug hunter belum membuat draf percakapan atau snapshot validasi di program aktif.")
      );
      if (total) {
        empty.append(button("Reset filter", () => {
          state.adminQueueFilters = { query: "", status: "all", verdict: "all" };
          searchInput.value = "";
          statusSelect.value = "all";
          verdictSelect.value = "all";
          renderQueue();
        }, "secondary-button"));
      }
      emptyHolder.append(empty);
      return;
    }

    tableWrap.hidden = false;
    filtered.forEach(r => {
      const tr = node("tr");
      const run = r.latestRun;
      const verdict = effectiveRunVerdict(run);

      const tdTitle = node("td");
      tdTitle.append(node("span", r.draft_title || "Draf baru", "admin-row-title"));
      const meta = node("span", undefined, "admin-row-meta");
      meta.append(node("span", `CID ${r.conversation_id.slice(0, 8)}`), node("span", `v${r.draft_version}`));
      if (r.hasAttachment) meta.append(node("span", "Lampiran TXT/MD"));
      if (r.runCount > 1) meta.append(node("span", `${r.runCount} run`));
      tdTitle.append(meta);

      const tdKind = node("td");
      const cat = run?.validation_kind || r.latestClaim?.category || (r.report_id ? "SNAPSHOT" : "DRAF");
      tdKind.append(node("span", cat, "admin-tag"));
      if (run) {
        tdKind.append(node("span", `${run.execution_mode} · tools ${run.tool_execution_mode}`, "admin-row-sub"));
      } else if (r.businessCount > 0) {
        tdKind.append(node("span", `${r.businessCount} rekaman bisnis`, "admin-row-sub"));
      } else {
        tdKind.append(node("span", r.hydrated ? "Belum ada run" : "Memuat…", "admin-row-sub"));
      }

      const tdStatus = node("td");
      if (!r.hydrated && r.report_id) {
        tdStatus.append(node("div", undefined, "vv-skeleton"));
      } else if (run) {
        tdStatus.append(makeStatusPill(run.process_status, statusTone(run.process_status), active(run) ? "clock" : "activity"));
        const pub = run.assessment ? `${run.assessment.review_status || "UNREVIEWED"} · ${run.assessment.publication_status || "PRIVATE"}` : (run.error_code || "Tanpa assessment");
        tdStatus.append(node("span", pub, "admin-row-sub"));
      } else {
        tdStatus.append(makeStatusPill(r.report_id ? "SNAPSHOT" : "DRAFT", "neutral", "file"));
        tdStatus.append(node("span", r.businessCount ? "Siap review rekaman" : "Menunggu snapshot validasi", "admin-row-sub"));
      }

      const tdVerdict = node("td");
      if (verdict) {
        tdVerdict.append(makeStatusPill(verdict, statusTone(verdict), verdict === "CONFIRMED" ? "shield-check" : verdict === "REFUTED" ? "shield-alert" : "info"));
        if (run?.assessment?.analyst_override) {
          tdVerdict.append(node("span", "Override analis", "admin-row-sub"));
        }
      } else {
        tdVerdict.append(node("span", "—", "mono-cell"));
      }

      const tdActions = node("td");
      const actWrap = node("div", undefined, "admin-row-actions");
      actWrap.append(iconButton("chat", "Buka", () => openConversation(r.conversation_id), "secondary-button"));
      if (run?.assessment) {
        actWrap.append(iconButton("sliders", "Review cepat", () => openAdminQuickReview(r, async freshRun => {
          r.latestRun = freshRun;
          if (state.run?.run_id === freshRun.run_id) state.run = freshRun;
          renderQueue();
        }), "secondary-button"));
        if (run.assessment.review_status === "REVIEWED" && run.assessment.publication_status !== "PUBLISHED") {
          actWrap.append(iconButton("check-circle", "Publikasi", async () => {
            await api(`/api/runs/${run.run_id}/publish`, { method: "POST" });
            r.latestRun = await api(`/api/runs/${run.run_id}`);
            if (state.run?.run_id === r.latestRun.run_id) state.run = r.latestRun;
            notice("Ringkasan aman dibagikan ke pelapor.");
            renderQueue();
          }, "primary-button"));
        }
      }
      tdActions.append(actWrap);

      tr.append(tdTitle, tdKind, tdStatus, tdVerdict, tdActions);
      tbody.append(tr);
    });
  };

  searchInput.addEventListener("input", () => {
    state.adminQueueFilters.query = searchInput.value;
    renderQueue();
  });
  statusSelect.addEventListener("change", () => {
    state.adminQueueFilters.status = statusSelect.value;
    renderQueue();
  });
  verdictSelect.addEventListener("change", () => {
    state.adminQueueFilters.verdict = verdictSelect.value;
    renderQueue();
  });

  renderQueue();

  for (let i = 0; i < queueRows.length; i += 4) {
    if (version !== state.viewVersion || state.adminPage !== "reports" || state.program?.program_id !== programId) return;
    const chunk = queueRows.slice(i, i + 4);
    await Promise.all(chunk.map(async row => {
      try {
        const detail = await api(`/api/conversations/${row.conversation_id}`);
        row.hasAttachment = Boolean(detail.attachment);
        row.messageCount = detail.messages?.length || 0;
        row.runCount = detail.run_ids?.length || 0;
        row.latestClaim = detail.latest_claim || null;
        if (detail.run_ids?.length) {
          row.latestRun = await api(`/api/runs/${detail.run_ids[0]}`);
        }
        if (row.report_id && detail.latest_claim?.category === "BUSINESS_LOGIC") {
          const biz = await api(`/api/reports/${row.report_id}/business-records`);
          row.businessCount = biz.length;
        }
      } catch {
        // Keep partial row readable if individual conversation fetch fails
      } finally {
        row.hydrated = true;
      }
    }));
    if (version !== state.viewVersion || state.adminPage !== "reports" || state.program?.program_id !== programId) return;
    renderQueue();
  }
  hydrateStatus.textContent = "Semua antrean sinkron";
}

async function showAdminGuidelinesPage(prefill = null) {
  const pageView = $("#page-view");
  const program = state.program;
  if (!pageView || !program || program.role !== "PROGRAM_ADMIN") return;

  const version = ++state.viewVersion;
  const programId = program.program_id;
  pageView.replaceChildren(
    (() => {
      const shell = node("div", undefined, "admin-shell");
      shell.append(renderAdminShellHeader("guidelines", "Guideline & Validator Scope JSON", "Susun teks kebijakan serta aturan scope JSON terstruktur, validasi skema sebelum dikirim, lalu aktifkan draf terpisah."));
      const loadingBox = node("div", undefined, "admin-panel");
      loadingBox.append(node("div", undefined, "vv-skeleton"), node("p", "Memuat konfigurasi guideline dan daftar draf scope…", "fine-print"));
      shell.append(loadingBox);
      return shell;
    })()
  );

  const [g, drafts] = await Promise.all([
    api(`/api/programs/${programId}/guidelines`),
    api(`/api/programs/${programId}/scope-drafts`)
  ]);
  if (version !== state.viewVersion || state.adminPage !== "guidelines" || state.program?.program_id !== programId) return;

  const initialSource = prefill?.source_text ?? (g.source_text || "");
  const initialRulesObj = prefill?.rules ?? (g.rules || {
    in_scope_rules: [],
    out_of_scope_rules: [],
    business_rules: "",
    business_rules_version: null
  });
  const initialJson = typeof initialRulesObj === "string" ? initialRulesObj : JSON.stringify(initialRulesObj, null, 2);

  const shell = node("div", undefined, "admin-shell");
  shell.append(renderAdminShellHeader("guidelines", "Guideline & Validator Scope JSON", "Susun teks kebijakan serta aturan scope JSON terstruktur, validasi skema sebelum dikirim, lalu aktifkan draf terpisah."));

  const statusCard = node("div", undefined, "admin-guide-status");
  const statusInfo = node("div", undefined, "admin-guide-status-info");
  statusInfo.append(
    node("strong", g.state === "ACTIVE" ? `Scope aktif: versi v${g.version}` : "Scope program belum dikonfigurasi (NOT_CONFIGURED)"),
    node("span", g.scope_version_id ? `ID Versi: ${g.scope_version_id}` : "Simpan minimal satu draf valid lalu klik Aktifkan draf untuk mengizinkan validasi worker.")
  );
  const statusRight = node("div", undefined, "admin-header-actions");
  statusRight.append(makeStatusPill(g.state || "NOT_CONFIGURED", g.state === "ACTIVE" ? "success" : "warning", g.state === "ACTIVE" ? "shield-check" : "warning"));
  if (g.rules) {
    statusRight.append(button("Muat versi aktif", () => {
      sourceEl.value = g.source_text || "";
      jsonEl.value = JSON.stringify(g.rules, null, 2);
      serverError.textContent = "";
      runLiveValidation();
      notice("Konten versi aktif dimuat ke editor (belum disimpan sebagai draf baru).");
    }, "secondary-button"));
  }
  statusCard.append(statusInfo, statusRight);
  shell.append(statusCard);

  const grid = node("div", undefined, "admin-guide-grid");

  // Left: Editor Form
  const formPanel = node("section", undefined, "admin-panel vv-crosshair");
  const formHead = node("div", undefined, "admin-panel-head");
  formHead.append(node("h2", "Editor Draf Guideline"), node("span", "DRAFT TIDAK OTOMATIS AKTIF", "admin-tag"));
  const form = node("form");

  const srcGroup = node("div", undefined, "form-group");
  const srcHead = node("div", undefined, "admin-field-head");
  const srcLabel = node("label", "Teks guideline (wajib)");
  srcLabel.htmlFor = "admin-guide-source";
  const byteCounter = node("span", "0 / 131.072 byte", "admin-byte-counter");
  byteCounter.id = "admin-guide-bytes";
  srcHead.append(srcLabel, byteCounter);
  const sourceEl = node("textarea");
  sourceEl.id = "admin-guide-source";
  sourceEl.rows = 5;
  sourceEl.maxLength = 32000;
  sourceEl.required = true;
  sourceEl.placeholder = "Jelaskan cakupan target yang diizinkan, batas akun uji, serta aturan pelaporan untuk program ini…";
  sourceEl.value = initialSource;
  srcGroup.append(srcHead, sourceEl);

  const jsonGroup = node("div", undefined, "form-group");
  const jsonHead = node("div", undefined, "admin-field-head");
  const jsonLabel = node("label", "Aturan scope terstruktur (JSON · wajib)");
  jsonLabel.htmlFor = "admin-guide-json";
  const toolbar = node("div", undefined, "admin-json-toolbar");
  const formatBtn = button("Format JSON", () => {
    try {
      const obj = guidelineRules(jsonEl.value);
      jsonEl.value = JSON.stringify(obj, null, 2);
      serverError.textContent = "";
      runLiveValidation();
    } catch (e) {
      serverError.textContent = e.message;
      runLiveValidation();
    }
  }, "secondary-button");
  const templateBtn = button("Template BAC Dasar", () => {
    if (!sourceEl.value.trim()) sourceEl.value = SCOPE_BASIC_TEMPLATE.source_text;
    jsonEl.value = JSON.stringify(SCOPE_BASIC_TEMPLATE.rules, null, 2);
    serverError.textContent = "";
    runLiveValidation();
    notice("Template dasar BAC (alias portal) dimuat ke editor.");
  }, "secondary-button");
  toolbar.append(formatBtn, templateBtn);
  jsonHead.append(jsonLabel, toolbar);

  const jsonEl = node("textarea", undefined, "admin-json-textarea");
  jsonEl.id = "admin-guide-json";
  jsonEl.rows = 14;
  jsonEl.required = true;
  jsonEl.spellcheck = false;
  jsonEl.value = initialJson;
  jsonGroup.append(jsonHead, jsonEl, node("p", "Kedua kolom wajib diisi. Schema ScopeDraft hanya menerima in_scope_rules, out_of_scope_rules, business_rules, dan business_rules_version (extra_forbidden)."));

  const serverError = node("p", undefined, "composer-error");
  serverError.id = "admin-guide-server-error";
  serverError.role = "alert";

  const submitBtn = node("button", "Simpan draf guideline", "primary-button");
  submitBtn.type = "submit";
  const formActions = node("div", undefined, "draft-actions");
  formActions.append(submitBtn);

  form.append(srcGroup, jsonGroup, serverError, formActions);
  formPanel.append(formHead, form);

  // Right: Validator + Saved Drafts
  const aside = node("div", undefined, "admin-guide-aside");
  const validatorPanel = node("section", undefined, "admin-panel");
  validatorPanel.id = "admin-guide-validator";
  const valHead = node("div", undefined, "admin-panel-head");
  const valPillSlot = node("div");
  valHead.append(node("h2", "Validator Skema JSON"), valPillSlot);
  const valList = node("ul", undefined, "admin-validator-list");
  const ruleSummary = node("div", undefined, "admin-rule-summary");
  validatorPanel.append(valHead, valList, ruleSummary, node("p", "Validasi client memeriksa struktur JSON & batas panjang. Kecocokan alias target operator tetap dipastikan server saat simpan/aktivasi.", "fine-print"));

  const draftsPanel = node("section", undefined, "admin-panel");
  draftsPanel.id = "admin-drafts-panel";
  const draftsHead = node("div", undefined, "admin-panel-head");
  draftsHead.append(node("h2", "Antrean Draf Scope"), node("span", `${drafts.length} draf`, "admin-tag"));
  const draftsList = node("div", undefined, "admin-drafts-list");

  if (!drafts.length) {
    const emptyDraft = node("div", undefined, "vv-empty-state");
    emptyDraft.append(
      node("strong", "Belum ada draf tersimpan"),
      node("p", "Isi Teks guideline dan Aturan scope JSON lalu simpan sebagai draf baru.")
    );
    draftsList.append(emptyDraft);
  } else {
    drafts.forEach(d => {
      let parsedRules = null;
      try {
        parsedRules = JSON.parse(d.rules_json);
      } catch {}
      const inCount = parsedRules?.in_scope_rules?.length || 0;
      const outCount = parsedRules?.out_of_scope_rules?.length || 0;
      const card = node("article", undefined, "admin-draft-card");
      const dHead = node("div", undefined, "admin-draft-head");
      dHead.append(node("strong", `Draf v${d.version}`), node("span", `${inCount} in-scope · ${outCount} out-of-scope`, "admin-tag"));
      const dAct = node("div", undefined, "draft-actions");
      dAct.append(
        button("Muat ke editor", () => {
          sourceEl.value = d.source_text || "";
          jsonEl.value = parsedRules ? JSON.stringify(parsedRules, null, 2) : (d.rules_json || "{}");
          serverError.textContent = "";
          runLiveValidation();
          notice(`Draf v${d.version} dimuat ke editor.`);
        }, "secondary-button"),
        iconButton("check-circle", `Aktifkan draf v${d.version}`, async () => {
          await api(`/api/programs/${programId}/scope-drafts/${d.scope_version_id}/activate`, { method: "POST" });
          notice("Scope diaktifkan; run lama dihentikan.");
          await showAdminGuidelinesPage();
        }, "primary-button")
      );
      card.append(dHead, node("p", d.source_text || "", "admin-draft-snippet"), dAct);
      draftsList.append(card);
    });
  }
  draftsPanel.append(draftsHead, draftsList);

  aside.append(validatorPanel, draftsPanel);
  grid.append(formPanel, aside);
  shell.append(grid);
  pageView.replaceChildren(shell);

  const runLiveValidation = () => {
    const check = validateScopeEditorInput(sourceEl.value, jsonEl.value);
    byteCounter.textContent = `${check.utf8Bytes.toLocaleString("id-ID")} / 131.072 byte`;
    byteCounter.classList.toggle("is-over", check.utf8Bytes > 131072);

    valPillSlot.replaceChildren(
      makeStatusPill(check.valid ? "SIAP SIMPAN" : `${check.errors.length} MASALAH SKEMA`, check.valid ? "success" : "danger", check.valid ? "check-circle" : "warning")
    );
    valList.replaceChildren();

    if (check.valid) {
      const okItem = node("li", undefined, "admin-validator-item is-ok");
      okItem.append(makeSvg("check-circle"), node("span", "Format teks dan objek JSON ScopeDraft valid di sisi client."));
      valList.append(okItem);
    } else {
      check.errors.slice(0, 8).forEach(err => {
        const li = node("li", undefined, "admin-validator-item");
        const copy = node("div");
        copy.append(node("span", err.field, "admin-validator-field"), node("span", err.message));
        li.append(makeSvg("warning"), copy);
        valList.append(li);
      });
    }

    ruleSummary.replaceChildren();
    if (check.parsed) {
      const inRules = Array.isArray(check.parsed.in_scope_rules) ? check.parsed.in_scope_rules : [];
      const outRules = Array.isArray(check.parsed.out_of_scope_rules) ? check.parsed.out_of_scope_rules : [];
      const appendChips = (items, kindLabel) => {
        items.slice(0, 6).forEach(rule => {
          if (!rule || typeof rule !== "object") return;
          const chip = node("div", undefined, "admin-rule-chip");
          const top = node("div", undefined, "admin-rule-chip-top");
          const methodsStr = Array.isArray(rule.methods) ? rule.methods.join(",") : "?";
          const capsStr = Array.isArray(rule.capabilities) ? rule.capabilities.join(" · ") : "?";
          top.append(node("span", `${kindLabel} · ${rule.asset_alias || "?"}`, "admin-tag"), node("small", capsStr));
          chip.append(top, node("code", `${methodsStr} ${rule.path_template || "?"}`));
          ruleSummary.append(chip);
        });
      };
      appendChips(inRules, "IN_SCOPE");
      appendChips(outRules, "OUT_OF_SCOPE");
    }
    return check;
  };

  sourceEl.addEventListener("input", () => {
    serverError.textContent = "";
    runLiveValidation();
  });
  jsonEl.addEventListener("input", () => {
    serverError.textContent = "";
    runLiveValidation();
  });
  form.addEventListener("submit", e => {
    e.preventDefault();
    serverError.textContent = "";
    const check = runLiveValidation();
    if (!check.valid || !check.parsed) {
      serverError.textContent = check.errors[0]?.message || "Periksa kembali isian teks dan JSON guideline.";
      return;
    }
    guard(async () => {
      setSubmitBusy(submitBtn, true, "Simpan draf guideline", "Menyimpan draf…");
      try {
        const draft = await api(`/api/programs/${programId}/scope-drafts`, {
          method: "POST",
          body: JSON.stringify({ ...check.parsed, source_text: sourceEl.value })
        });
        notice(`Draf v${draft.version} tersimpan; belum aktif.`);
        await showAdminGuidelinesPage({ source_text: sourceEl.value, rules: check.parsed });
      } catch (err) {
        serverError.textContent = err.message;
      } finally {
        setSubmitBusy(submitBtn, false, "Simpan draf guideline", "Menyimpan draf…");
      }
    });
  });

  runLiveValidation();
}

async function openAdminPage(mode = "reports") {
  if (!state.program || state.program.role !== "PROGRAM_ADMIN") {
    notice("Halaman ini memerlukan peran admin program.");
    return;
  }
  saveUnsent();
  stopPoll();
  closeNav();
  const safeMode = mode === "guidelines" ? "guidelines" : "reports";
  state.adminPage = safeMode;
  const chatView = $("#chat-view");
  const pageView = $("#page-view");
  if (chatView) chatView.hidden = true;
  if (pageView) pageView.hidden = false;
  syncAdminNavHighlight();
  if (safeMode === "guidelines") {
    await showAdminGuidelinesPage();
  } else {
    await showAdminReportsPage();
  }
}

function guidelineRules(value) {
  let parsed;
  try {
    parsed = JSON.parse(value);
  } catch {
    throw Error("Aturan scope terstruktur: JSON tidak sah. Salin objek JSON tanpa penanda ``` dan periksa tanda kutip/kurung/koma.");
  }
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
    throw Error("Aturan scope terstruktur harus berupa objek JSON.");
  }
  return parsed;
}

async function guidelines(edit = false) {
  if (edit && state.program?.role === "PROGRAM_ADMIN") {
    await openAdminPage("guidelines");
    return;
  }
  const g = await api(`/api/programs/${state.program.program_id}/guidelines`);
  const box = node("div");
  box.append(
    node("p", `Status: ${g.state} · versi ${g.version || "belum aktif"}`),
    node("pre", g.source_text || "Admin perlu membuat dan mengaktifkan guideline.")
  );
  if (g.rules) box.append(node("pre", JSON.stringify(g.rules, null, 2)));
  panel("Scope program", box);
}

async function boot() {
  const me = await api("/api/me");
  notice("");
  state.user = me;
  state.csrf = me.csrf_token;
  state.programs = await api("/api/programs");
  await triageUI.status();
  landingUI.pauseHeroScene(true);
  $("#login-dialog").close();
  $("#landing-view").hidden = true;
  $("#prototype-bar").hidden = false;
  $("#app-shell").hidden = false;
  $("#app-shell").inert = false;
  $("#logout").hidden = false;
  window.scrollTo({ top: 0, behavior: "instant" });
  $("#account-name").textContent = me.login_name;
  $("#account-avatar").textContent = initials(me.login_name);
  if (!state.programs.length) {
    notice("Akun tidak mempunyai keanggotaan program aktif.");
    return;
  }
  await chooseProgram(state.programs[0]);
}

$("#login-form").addEventListener("submit", e => {
  e.preventDefault();
  guard(async () => {
    const b = $("#login-form button");
    b.disabled = true;
    b.replaceChildren(node("span", undefined, "vv-spinner"), node("span", "Memverifikasi…"));
    try {
      state.csrf = (await api("/api/auth/csrf")).csrf_token;
      await api("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ login_name: $("#login-name").value, password: $("#login-password").value })
      });
      $("#login-password").value = "";
      $("#login-error").textContent = "";
      await boot();
    } catch (error) {
      $("#login-error").textContent = error.message;
    } finally {
      b.disabled = false;
      const arrowWrap = node("span", undefined, "btn-arrow");
      arrowWrap.append(makeSvg("arrow-right"));
      b.replaceChildren(node("span", "Masuk ke ruang kerja"), arrowWrap);
    }
  });
});

$("#login-show-password")?.addEventListener("change", e => {
  $("#login-password").type = e.target.checked ? "text" : "password";
});

const landingUI = {
  isoIndex: 0,
  heroZoneIndex: 0,
  heroController: null,
  heroLoading: false,
  heroIdleHandle: 0,
  heroIdleIsTimeout: false,
  heroInView: true,
  heroObserver: null,
  heroAutoTimer: null,
  heroManualInteracted: false,
  heroZones: [
    {
      code: "ZONA 01 · SCOPE GATE",
      title: "Kunci Versi Scope & Triage Teks",
      rule: "Triage AI hanya memproses teks; job worker hanya dibuat setelah scope versi admin lolos."
    },
    {
      code: "ZONA 02 · WORKER SANDBOX",
      title: "Eksekusi HTTP & Browser Terisolasi",
      rule: "Worker berjalan tanpa API key model dan tanpa ground truth dengan dua sesi akun terpisah."
    },
    {
      code: "ZONA 03 · TARGET LAB",
      title: "Portal Target Deterministik & Pembanding",
      rule: "Uji BAC-08, XSS-08, dan UP-04 selalu dibandingkan terhadap kontrol negatif yang aman."
    }
  ],
  isoLayers: [
    {
      label: "Layer 01 · Scope Gate",
      title: "Scope dan verdict dikendalikan aplikasi.",
      desc: "Triage AI hanya memproses teks. Pengujian tetap melewati validasi versi scope admin dan verifier terpisah."
    },
    {
      label: "Layer 02 · Worker Sandbox",
      title: "Worker berjalan tanpa API key dan ground truth.",
      desc: "Eksekusi HTTP dan browser hanya menerima alias terotorisasi serta mengisolasi kredensial uji."
    },
    {
      label: "Layer 03 · Target Lab",
      title: "Portal target terisolasi dengan reset deterministik.",
      desc: "Setiap uji membandingkan kontrol negatif dan kondisi target tanpa menjalankan payload mentah laporan."
    }
  ],

  openLogin() {
    $("#login-error").textContent = "";
    if (!$("#login-dialog").open) $("#login-dialog").showModal();
    $("#login-name").focus();
  },

  canUseWebGL() {
    const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
    const saveData = Boolean(navigator.connection?.saveData);
    if (reduced || saveData) return false;
    try {
      const c = document.createElement("canvas");
      const opts = { antialias: true, alpha: false, powerPreference: "high-performance" };
      return Boolean(c.getContext("webgl2", opts) || c.getContext("webgl", opts));
    } catch {
      return false;
    }
  },

  setHeroTierBadge(tier) {
    const shell = $("#hero-scene-shell");
    const badge = $("#hero-render-tier");
    if (shell) shell.dataset.renderTier = tier;
    if (!badge) return;
    if (tier === "webgl-full") badge.textContent = "TIER 1 · WEBGL";
    else if (tier === "webgl-lite") badge.textContent = "TIER 2 · WEBGL LITE";
    else badge.textContent = "TIER 3 · CSS 3D";
  },

  selectHeroZone(idx, isManual = false) {
    const safeIdx = Math.max(0, Math.min(this.heroZones.length - 1, Number(idx) || 0));
    if (isManual) {
      this.heroManualInteracted = true;
      clearInterval(this.heroAutoTimer);
      this.heroAutoTimer = null;
    }
    this.heroZoneIndex = safeIdx;
    const info = this.heroZones[safeIdx];
    const code = $("#hero-focus-code");
    const title = $("#hero-focus-title");
    const rule = $("#hero-focus-rule");
    if (code) code.textContent = info.code;
    if (title) title.textContent = info.title;
    if (rule) rule.textContent = info.rule;

    document.querySelectorAll("[data-hero-target]").forEach(btn => {
      const match = Number(btn.dataset.heroTarget) === safeIdx;
      btn.classList.toggle("is-active", match);
      btn.setAttribute("aria-selected", String(match));
    });
    document.querySelectorAll("[data-hero-block]").forEach(block => {
      block.classList.toggle("is-active", Number(block.dataset.heroBlock) === safeIdx);
    });
    try { this.heroController?.setActiveLayer?.(safeIdx); } catch {} 
  },

  loadSceneVendorScript() {
    if (window.ValVulnMonolithScene) return Promise.resolve(window.ValVulnMonolithScene);
    return new Promise((resolve, reject) => {
      const existing = document.querySelector('script[data-vv-vendor="monolith-scene"]');
      if (existing) {
        existing.addEventListener("load", () => resolve(window.ValVulnMonolithScene), { once: true });
        existing.addEventListener("error", () => reject(new Error("Vendor 3D gagal dimuat")), { once: true });
        return;
      }
      const s = document.createElement("script");
      s.src = "/static/vendor/monolith-scene.js";
      s.defer = true;
      s.dataset.vvVendor = "monolith-scene";
      s.onload = () => resolve(window.ValVulnMonolithScene);
      s.onerror = () => reject(new Error("Vendor 3D gagal dimuat"));
      document.head.append(s);
    });
  },

  mountHeroWebGL() {
    if (this.heroController || this.heroLoading) return;
    const canvas = document.getElementById("segel-3d-canvas");
    if (!canvas) return;
    this.heroLoading = true;
    import("/static/vendor/segel-scene.js")
      .then(mod => {
        this.heroController = mod.initSegelScene("segel-3d-canvas");
        this.syncHeroPlayback();
        document.querySelectorAll(".lab-track-card, .lab-track-item").forEach((el, idx) => {
          el.addEventListener("mouseenter", () => mod.rotateCapsuleToTrack(idx + 1));
        });
      })
      .catch(e => console.warn("3D segel scene skipped", e))
      .finally(() => { this.heroLoading = false; });
  },
  scheduleHeroSceneLoad() {
    if ($("#landing-view")?.hidden || !$("#app-shell")?.hidden) return;
    if (!this.canUseWebGL()) {
      this.setHeroTierBadge("css3d-fallback");
      return;
    }
    if (this.heroController) {
      this.syncHeroPlayback();
      return;
    }
    if (this.heroIdleHandle) return;
    const run = () => {
      this.heroIdleHandle = 0;
      this.mountHeroWebGL();
    };
    if (typeof window.requestIdleCallback === "function") {
      this.heroIdleIsTimeout = false;
      this.heroIdleHandle = window.requestIdleCallback(run, { timeout: 450 });
    } else {
      this.heroIdleIsTimeout = true;
      this.heroIdleHandle = window.setTimeout(run, 120);
    }
  },

  startAutoCycle() {
    clearInterval(this.heroAutoTimer);
    this.heroAutoTimer = null;
    const reduced = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;
    if (reduced || this.heroManualInteracted || document.hidden || $("#landing-view")?.hidden || !this.heroInView) {
      return;
    }
    this.heroAutoTimer = setInterval(() => {
      if (document.hidden || $("#landing-view")?.hidden || !this.heroInView || this.heroManualInteracted) return;
      this.selectHeroZone((this.heroZoneIndex + 1) % this.heroZones.length, false);
    }, 5200);
  },

  syncHeroPlayback() {
    const paused = document.hidden || Boolean($("#landing-view")?.hidden) || !$("#app-shell")?.hidden || !this.heroInView;
    this.heroController?.setPaused(paused);
    if (paused) {
      clearInterval(this.heroAutoTimer);
      this.heroAutoTimer = null;
    } else {
      this.startAutoCycle();
    }
  },

  pauseHeroScene(enteringApp = false) {
    if (this.heroIdleHandle) {
      if (this.heroIdleIsTimeout) clearTimeout(this.heroIdleHandle);
      else if (typeof window.cancelIdleCallback === "function") window.cancelIdleCallback(this.heroIdleHandle);
      this.heroIdleHandle = 0;
    }
    clearInterval(this.heroAutoTimer);
    this.heroAutoTimer = null;
    if (enteringApp || $("#landing-view")?.hidden) {
      this.heroController?.setPaused(true);
    }
  },

  resumeHeroScene() {
    if ($("#landing-view")?.hidden) return;
    const shell = $("#hero-scene-shell");
    if (this.heroObserver && shell) {
      this.heroObserver.unobserve(shell);
      this.heroObserver.observe(shell);
    }
    this.mountHeroWebGL();
    this.syncHeroPlayback();
  },

  syncTheme(theme) {
    this.heroController?.setTheme(theme === "light" ? "light" : "dark");
  },

  selectIsoLayer(idx) {
    const safeIdx = Number(idx);
    if (Number.isNaN(safeIdx) || !this.isoLayers[safeIdx]) return;
    this.isoIndex = safeIdx;
    const info = this.isoLayers[safeIdx];
    const readout = $("#iso-readout");
    const title = $("#iso-detail-title");
    const desc = $("#iso-detail-desc");
    if (readout) readout.textContent = info.label;
    if (title) title.textContent = info.title;
    if (desc) desc.textContent = info.desc;
    document.querySelectorAll("[data-iso-target]").forEach(btn => {
      const match = Number(btn.dataset.isoTarget) === safeIdx;
      btn.classList.toggle("is-active", match);
      btn.setAttribute("aria-selected", String(match));
    });
    document.querySelectorAll("[data-iso-layer]").forEach(layer => {
      layer.classList.toggle("is-active", Number(layer.dataset.isoLayer) === safeIdx);
    });
  },

  initSmoothNavigation() {
    const syncScrollSpy = () => {
      if ($("#landing-view")?.hidden) return;
      const sections = ["kapabilitas", "keamanan", "alur"]
        .map(id => document.getElementById(id))
        .filter(Boolean);
      const nav = $(".landing-nav");
      const threshold = (nav ? nav.getBoundingClientRect().height : 74) + 70;
      let activeId = "";
      sections.forEach(sec => {
        if (sec.getBoundingClientRect().top <= threshold) activeId = sec.id;
      });
      document.querySelectorAll(".landing-links a, #landing-mobile-drawer a").forEach(a => {
        const match = activeId && a.getAttribute("href") === `#${activeId}`;
        a.classList.toggle("is-active", Boolean(match));
      });
    };

    document.addEventListener("click", e => {
      const link = e.target.closest('a[href^="#"]');
      if (!link) return;
      const hash = link.getAttribute("href");
      if (!hash || hash === "#") return;
      const targetId = hash.slice(1);
      const target = document.getElementById(targetId);
      if (!target) return;
      e.preventDefault();

      const drawer = $("#landing-mobile-drawer");
      if (drawer && !drawer.hidden) {
        drawer.hidden = true;
        $("#landing-menu-btn")?.setAttribute("aria-expanded", "false");
      }

      if (targetId === "main-content" && !$("#app-shell")?.hidden) {
        smoothScrollTo(0, $("#chat-scroll") || window, 480);
        target.focus({ preventScroll: true });
        return;
      }

      try {
        window.history.replaceState(null, "", hash);
      } catch {}
      smoothScrollTo(target, window, 680);
    });

    let spyRaf = 0;
    window.addEventListener("scroll", () => {
      if (spyRaf) return;
      spyRaf = requestAnimationFrame(() => {
        syncScrollSpy();
        spyRaf = 0;
      });
    }, { passive: true });
    syncScrollSpy();

    if (window.location.hash && window.location.hash.length > 1) {
      const initialTarget = document.getElementById(window.location.hash.slice(1));
      if (initialTarget && !$("#landing-view")?.hidden) {
        setTimeout(() => smoothScrollTo(initialTarget, window, 680), 90);
      }
    }
  },

  init() {
    this.initSmoothNavigation();
    document.querySelectorAll("[data-hero-target]").forEach(btn => {
      btn.addEventListener("click", () => this.selectHeroZone(btn.dataset.heroTarget, true));
    });
    document.querySelectorAll("[data-hero-block]").forEach(block => {
      block.addEventListener("click", () => this.selectHeroZone(block.dataset.heroBlock, true));
    });
    $("#hero-camera-reset")?.addEventListener("click", () => {
      this.heroController?.resetCamera();
    });
    this.selectHeroZone(0, false);

    document.querySelectorAll("[data-iso-target]").forEach(btn => {
      btn.addEventListener("click", () => this.selectIsoLayer(btn.dataset.isoTarget));
    });
    document.querySelectorAll("[data-iso-layer]").forEach(layer => {
      layer.addEventListener("click", () => this.selectIsoLayer(layer.dataset.isoLayer));
    });
    this.selectIsoLayer(0);

    [$("#landing-login-btn"), $("#hero-login-cta"), $("#closing-login-btn")].forEach(b =>
      b?.addEventListener("click", () => this.openLogin())
    );
    $("#login-close")?.addEventListener("click", () => $("#login-dialog").close());
    $("#landing-theme-toggle")?.addEventListener("change", (e) => {
      const next = e.target.checked ? "dark" : "light";
      applyTheme(next, true);
    });

    $("#valvuln-brand-logo")?.addEventListener("click", (e) => {
      e.preventDefault();
      const loader = $("#brand-loader-overlay");
      if (loader) {
        loader.hidden = false;
        setTimeout(() => {
          loader.hidden = true;
        }, 1200);
      }
    });

    // ColorOS Popover Dialog Telemetry Handler
    const popover = $("#telemetry-popover");
    const pBadge = $("#telemetry-modal-badge");
    const pTitle = $("#telemetry-modal-title");
    const pDesc = $("#telemetry-modal-desc");

    const openPopover = (badge, title, desc) => {
      if (!popover) return;
      if (pBadge) pBadge.textContent = badge;
      if (pTitle) pTitle.textContent = title;
      if (pDesc) pDesc.textContent = desc;
      if (!popover.open) popover.showModal();
    };

    $("#chip-key")?.addEventListener("click", () => {
      openPopover(
        "Worker sandbox",
        "Ruang eksekusi tanpa kunci API dan tanpa ground truth",
        "Worker berjalan di container terpisah tanpa izin akses jaringan live internet. Eksekusi HTTP dan browser sandboxed hanya menerima kredensial uji alias terotorisasi, memisahkan sepenuhnya saran teks AI dari hasil verifikasi lab."
      );
    });

    $("#chip-lab")?.addEventListener("click", () => {
      openPopover(
        "Jalur target lab",
        "Tiga jalur deterministik pengujian lab",
        "Target lab mencakup BAC-08 (akses kontrol lintas akun), XSS-08 (injeksi pratinjau tersimpan), dan UP-04 (integritas berkas). Setiap klaim diuji terhadap kontrol negatif yang aman sebelum status konfirmasi diterbitkan."
      );
    });

    $("#specimen-card")?.addEventListener("click", () => {
      openPopover(
        "Objek tersegel",
        "Integritas laporan tersegel SHA-256",
        "Laporan kerentanan yang masuk langsung dikunci dengan hash kriptografis dan diverifikasi batas scope-nya oleh server sebelum pekerjaan lab dapat dijadwalkan."
      );
    });

    [$("#telemetry-modal-close"), $("#telemetry-modal-action")].forEach(btn => {
      btn?.addEventListener("click", () => popover?.close());
    });
    popover?.addEventListener("click", e => {
      if (e.target === popover) popover.close();
    });
    $("#landing-menu-btn")?.addEventListener("click", () => {
      const drawer = $("#landing-mobile-drawer");
      const open = drawer.hidden;
      drawer.hidden = !open;
      $("#landing-menu-btn").setAttribute("aria-expanded", String(open));
    });
    document.querySelectorAll("#landing-mobile-drawer a").forEach(a =>
      a.addEventListener("click", () => {
        $("#landing-mobile-drawer").hidden = true;
        $("#landing-menu-btn").setAttribute("aria-expanded", "false");
      })
    );

    // Active navigation state observer & click feedback
    const navLinks = Array.from(document.querySelectorAll(".segel-nav-link"));
    if (navLinks.length) {
      const updateActiveNav = (activeId) => {
        navLinks.forEach(link => {
          const href = link.getAttribute("href") || "";
          link.classList.toggle("is-active", href === `#${activeId}`);
        });
      };

      const syncScrollActive = () => {
        const scrollPos = window.scrollY + 220;
        let currentId = "";
        for (const id of ["lab", "sandbox", "scope"]) {
          const el = document.getElementById(id);
          if (el && el.offsetTop <= scrollPos) {
            currentId = id;
            break;
          }
        }
        updateActiveNav(currentId);
      };

      window.addEventListener("scroll", syncScrollActive, { passive: true });

      navLinks.forEach(link => {
        link.addEventListener("click", () => {
          const href = link.getAttribute("href");
          if (href?.startsWith("#")) {
            updateActiveNav(href.slice(1));
          }
        });
      });

      syncScrollActive();
    }

    const heroShell = $("#hero-scene-shell");
    if ("IntersectionObserver" in window && heroShell) {
      this.heroObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
          this.heroInView = entry.isIntersecting;
          this.syncHeroPlayback();
        });
      }, { threshold: 0.05 });
      this.heroObserver.observe(heroShell);
    }

    const revealNodes = document.querySelectorAll("[data-reveal]");
    if ("IntersectionObserver" in window && revealNodes.length) {
      const io = new IntersectionObserver((entries) => {
        entries.forEach((entry, idx) => {
          if (!entry.isIntersecting) return;
          const el = entry.target;
          el.classList.add("vv-reveal", `vv-d${Math.min(idx + 1, 3)}`);
          scheduleRevealCleanup(el);
          io.unobserve(el);
        });
      }, { threshold: 0.08, rootMargin: "0px 0px -20px 0px" });
      revealNodes.forEach(n => io.observe(n));
    }

    this.mountHeroWebGL();
    this.startAutoCycle();
  }
};

landingUI.init();
$("#logout").addEventListener("click", () => guard(async () => {
  await api("/api/auth/logout", { method: "POST" });
  logoutView();
}));
$("#new-report").addEventListener("click", () => guard(newConversation));
$("#composer-form").addEventListener("submit", e => guard(() => sendMessage(e)));
$("#message-input").addEventListener("input", () => {
  saveUnsent();
  triageUI.render();
});
$("#message-input").addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    guard(() => sendMessage());
  }
});
$("#attach-button").addEventListener("click", () => $("#file-input").click());
$("#file-input").addEventListener("change", () => guard(upload));
$("#detail-dialog").addEventListener("close", () => {
  if (state.user) $("#scope-button").focus();
});
$("#dialog-close").addEventListener("click", () => $("#detail-dialog").close());
[$("#scope-button"), $("#sidebar-guide")].filter(Boolean).forEach(b => b.addEventListener("click", () => guard(() => guidelines())));
$("#model-info").addEventListener("click", () => triageUI.info());
$("#workspace-switch").addEventListener("click", () => {
  const box = node("div");
  state.programs.forEach(p => box.append(button(p.display_name, async () => {
    $("#detail-dialog").close();
    await chooseProgram(p);
  })));
  panel("Pilih program", box);
});
$("[data-view=guidelines]").addEventListener("click", () => guard(() => openAdminPage("guidelines")));
$("[data-view=reports]").addEventListener("click", () => guard(() => openAdminPage("reports")));
$("#theme-toggle").addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
  applyTheme(next, true);
});
$("#search-toggle").addEventListener("click", () => {
  const input = $("#history-search");
  input.hidden = !input.hidden;
  $("#search-toggle").setAttribute("aria-expanded", String(!input.hidden));
  if (!input.hidden) $("#history-query").focus();
});
$("#history-query")?.addEventListener("input", () => guard(history));
$("#history-filter")?.addEventListener("input", () => guard(history));
[$("#sidebar-close"), $("#sidebar-scrim")].filter(Boolean).forEach(b => b.addEventListener("click", () => {
  closeNav();
  $("#sidebar-open").focus();
}));
document.querySelectorAll("[data-inspector-tab]").forEach(btn => {
  btn.addEventListener("click", () => setInspectorTab(btn.dataset.inspectorTab));
});
document.addEventListener("visibilitychange", () => {
  stopPoll();
  triageUI.visibility();
  landingUI.syncHeroPlayback();
  if (!document.hidden && active(state.run)) guard(() => loadRun(state.run.run_id));
});

try {
  const saved = localStorage.getItem("valvuln-theme");
  commitThemeState(saved === "dark" ? "dark" : "light");
} catch {}
iconize();
guard(boot);
