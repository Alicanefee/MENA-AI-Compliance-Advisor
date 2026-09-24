// Web UI for the AI Compliance Advisor. Plain ES modules, no build step.

const I18N = {
  en: {
    app_title: "AI Compliance Advisor", app_sub: "UAE · Saudi Arabia · EU",
    tab_ask: "Ask", tab_cases: "Cases", tab_learn: "Learn", tab_scenarios: "Scenarios", tab_sources: "Sources",
    question: "Question", question_ph: "e.g. We want to use AI to screen CVs for our Dubai office. What do we need?",
    context: "AI use case (optional)", context_ph: "e.g. ranking applicants by skills and experience",
    jurisdictions: "Jurisdictions (none = detect from the question)", ask: "Ask", save_case: "Save as case",
    new_case: "New case", owner: "Owner", sector: "Sector", create_case: "Create case and run advisor",
    cases: "Cases", all: "All", learner: "Learner ID", load: "Load",
    working: "Working…", findings: "Verified findings", counterpoints: "Counterpoints and limitations",
    disputed: "Disputed", rejected: "Removed - quote not found in source", open_q: "Open questions",
    provisions: "Retrieved provisions", documents: "Document checklist", mandatory: "mandatory", optional: "conditional",
    practice: "good practice", basis: "Basis", coverage: "citation coverage", review: "Human review required",
    status: { answered: "answered", partial: "partial", insufficient_basis: "insufficient basis" },
    mode_generated: "LLM + verification", mode_extractive: "Extractive mode (no LLM)",
    check: { confirmed: "confirmed in official text", not_confirmed: "not confirmed", article_missing: "article not indexed", source_missing: "source not downloaded", unchecked: "unchecked" },
    alerts: "Alerts", docs: "Documents", upload: "Upload", received: "received", missing: "missing", waived: "waived",
    not_applicable: "not applicable", save: "Save", reviewer: "Reviewer", review_note: "Review note",
    actor: "Your name", log: "History", modules: "Modules", tracks: "Learning paths", open: "Open", submit: "Submit",
    correct: "Correct", wrong: "Not quite", score: "Module score", show_answer: "Show model answer",
    could_change: "What could change the answer", verdict: "Verdict", recommended: "Recommended training",
    stale: "stale", fresh: "current", check_now: "Check for updates", diffs: "Change reports", manual: "Manual download",
    passages_n: "passages", last_checked: "last checked", never: "never", ai_extraction: "AI transcription",
    unchanged: "No change since the last download.", changed: "Changed - see report below.",
    note: "note", min: "min", level: { beginner: "beginner", intermediate: "intermediate", advanced: "advanced" },
  },
  ar: {
    app_title: "مستشار الامتثال للذكاء الاصطناعي", app_sub: "الإمارات · السعودية · الاتحاد الأوروبي",
    tab_ask: "اسأل", tab_cases: "الحالات", tab_learn: "تعلّم", tab_scenarios: "سيناريوهات", tab_sources: "المصادر",
    question: "السؤال", question_ph: "مثال: نريد استخدام الذكاء الاصطناعي لفرز السير الذاتية لمكتب دبي. ماذا نحتاج؟",
    context: "حالة استخدام الذكاء الاصطناعي (اختياري)", context_ph: "مثال: ترتيب المتقدمين حسب المهارات والخبرة",
    jurisdictions: "الولايات القضائية (بدون اختيار = الكشف من السؤال)", ask: "اسأل", save_case: "حفظ كحالة",
    new_case: "حالة جديدة", owner: "المسؤول", sector: "القطاع", create_case: "إنشاء الحالة وتشغيل المستشار",
    cases: "الحالات", all: "الكل", learner: "معرّف المتعلم", load: "تحميل",
    working: "جارٍ العمل…", findings: "نتائج موثقة", counterpoints: "آراء مقابلة وقيود",
    disputed: "متنازع عليها", rejected: "محذوفة - الاقتباس غير موجود في المصدر", open_q: "أسئلة مفتوحة",
    provisions: "الأحكام المسترجعة", documents: "قائمة المستندات", mandatory: "إلزامي", optional: "مشروط",
    practice: "ممارسة جيدة", basis: "الأساس", coverage: "نسبة التوثيق", review: "مراجعة بشرية مطلوبة",
    status: { answered: "تمت الإجابة", partial: "جزئي", insufficient_basis: "أساس غير كافٍ" },
    mode_generated: "نموذج لغوي + تحقق", mode_extractive: "وضع الاستخراج (بدون نموذج)",
    check: { confirmed: "مؤكد في النص الرسمي", not_confirmed: "غير مؤكد", article_missing: "المادة غير مفهرسة", source_missing: "المصدر غير محمّل", unchecked: "لم يُفحص" },
    alerts: "تنبيهات", docs: "المستندات", upload: "رفع", received: "مستلم", missing: "ناقص", waived: "معفى",
    not_applicable: "لا ينطبق", save: "حفظ", reviewer: "المراجع", review_note: "ملاحظة المراجعة",
    actor: "اسمك", log: "السجل", modules: "الوحدات", tracks: "مسارات التعلم", open: "فتح", submit: "إرسال",
    correct: "صحيح", wrong: "غير صحيح", score: "درجة الوحدة", show_answer: "عرض الإجابة النموذجية",
    could_change: "ما الذي قد يغير الإجابة", verdict: "الحكم", recommended: "تدريب مقترح",
    stale: "قديم", fresh: "محدّث", check_now: "التحقق من التحديثات", diffs: "تقارير التغييرات", manual: "تحميل يدوي",
    passages_n: "مقاطع", last_checked: "آخر فحص", never: "أبداً", ai_extraction: "نسخ بالذكاء الاصطناعي",
    unchanged: "لا تغيير منذ آخر تحميل.", changed: "تم التغيير - انظر التقرير أدناه.",
    note: "ملاحظة", min: "دقيقة", level: { beginner: "مبتدئ", intermediate: "متوسط", advanced: "متقدم" },
  },
};

const state = { lang: readPref("lang", "en"), lastQuestion: null };
const $ = (sel) => document.querySelector(sel);
const t = (key) => key.split(".").reduce((o, k) => (o ? o[k] : undefined), I18N[state.lang]) ?? key;

function readPref(key, fallback) {
  try { return localStorage.getItem(`aca.${key}`) || fallback; } catch { return fallback; }
}
function writePref(key, value) {
  try { localStorage.setItem(`aca.${key}`, value); } catch { /* storage unavailable */ }
}
function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: options.body && !(options.body instanceof FormData) ? { "Content-Type": "application/json" } : {},
    ...options,
    body: options.body && !(options.body instanceof FormData) ? JSON.stringify(options.body) : options.body,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail ?? res.statusText));
  return data;
}

function busy(el) {
  el.innerHTML = `<p class="muted">${esc(t("working"))}</p>`;
}
function fail(el, err) {
  el.innerHTML = `<p class="error">${esc(err.message)}</p>`;
}

// ---------------- language & chrome ----------------
function applyLang() {
  document.documentElement.lang = state.lang;
  document.documentElement.dir = state.lang === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => { el.placeholder = t(el.dataset.i18nPlaceholder); });
  $("#lang-toggle").textContent = state.lang === "ar" ? "English" : "العربية";
  loadChrome();
}

async function loadChrome() {
  try {
    const [disc, health] = await Promise.all([api(`/api/disclaimer?lang=${state.lang}`), api("/api/health")]);
    $("#disclaimer").textContent = disc.full;
    const mode = $("#mode");
    mode.textContent = health.mode === "generated" ? t("mode_generated") : t("mode_extractive");
    mode.className = `pill ${health.mode === "generated" ? "ok" : "warn"}`;
  } catch (err) {
    $("#disclaimer").textContent = err.message;
  }
}

$("#lang-toggle").addEventListener("click", () => {
  state.lang = state.lang === "ar" ? "en" : "ar";
  writePref("lang", state.lang);
  applyLang();
  const active = document.querySelector('[role="tab"][aria-selected="true"]');
  if (active) activate(active, false);
});

// ---------------- tabs (WAI-ARIA tabs pattern) ----------------
const tabs = [...document.querySelectorAll('[role="tab"]')];
const loaders = { "tab-learn": loadLearn, "tab-scenarios": loadScenarios, "tab-sources": loadSources, "tab-cases": loadCases };

function activate(tab, focus = true) {
  tabs.forEach((other) => {
    const selected = other === tab;
    other.setAttribute("aria-selected", String(selected));
    other.tabIndex = selected ? 0 : -1;
    document.getElementById(other.getAttribute("aria-controls")).hidden = !selected;
  });
  if (focus) tab.focus();
  writePref("tab", tab.id);
  loaders[tab.id]?.();
}
tabs.forEach((tab, i) => {
  tab.addEventListener("click", () => activate(tab));
  tab.addEventListener("keydown", (e) => {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
    if (!step) return;
    const dir = document.documentElement.dir === "rtl" ? -step : step;
    activate(tabs[(i + dir + tabs.length) % tabs.length]);
  });
});

// ---------------- advice ----------------
function checkPill(check) {
  const cls = check === "confirmed" ? "ok" : check === "not_confirmed" ? "bad" : "warn";
  return `<span class="pill ${cls}">${esc(t(`check.${check}`))}</span>`;
}

function renderClaim(c, passages, kind) {
  const p = passages.find((sp) => sp.label === c.passage);
  const where = p ? `${p.passage.source_short}, ${/^\d/.test(p.passage.article) ? "Article " : ""}${p.passage.article}` : c.passage;
  return `<div class="claim ${kind}">
    <div>${esc(c.text)}</div>
    <blockquote>“${esc(c.quote)}”</blockquote>
    <div class="cite">[${esc(c.passage)}] ${esc(where)}${c.reason ? ` - ${esc(c.reason)}` : ""}</div>
  </div>`;
}

function renderDocuments(docs) {
  if (!docs?.length) return "";
  const rows = docs.map((d) => {
    const tag = d.kind === "practice" ? `<span class="pill">${esc(t("practice"))}</span>`
      : `<span class="pill ${d.mandatory ? "bad" : "warn"}">${esc(t(d.mandatory ? "mandatory" : "optional"))}</span>`;
    const basis = d.basis.map((b) => `${esc(b.source)}${b.article ? ` art. ${esc(b.article)}` : ""} ${checkPill(b.check)}`).join("<br>");
    return `<tr><td><strong>${esc(d.name)}</strong> ${tag}<div class="muted">${esc(d.why)}</div></td><td>${basis}</td></tr>`;
  }).join("");
  return `<div class="card"><h2>${esc(t("documents"))}</h2><div class="table-wrap"><table>
    <thead><tr><th>${esc(t("docs"))}</th><th>${esc(t("basis"))}</th></tr></thead><tbody>${rows}</tbody></table></div></div>`;
}

function renderAnswer(a) {
  const statusCls = { answered: "ok", partial: "warn", insufficient_basis: "bad" }[a.status];
  let html = `<div class="card">
    <div class="row">
      <span class="pill ${statusCls}">${esc(t(`status.${a.status}`))}</span>
      <span class="pill">${esc(a.jurisdictions.join(", "))}</span>
      ${a.mode === "generated" ? `<span class="pill">${esc(t("coverage"))}: ${Math.round(a.citation_coverage * 100)}%</span>` : ""}
      <span class="pill warn">${esc(t("review"))}</span>
    </div>
    <p>${esc(a.summary)}</p>`;
  if (a.findings.length) html += `<h3>${esc(t("findings"))}</h3>` + a.findings.map((c) => renderClaim(c, a.passages, "finding")).join("");
  const counter = a.counterpoints.filter((c) => c.status !== "disputed");
  const disputed = a.counterpoints.filter((c) => c.status === "disputed");
  if (counter.length) html += `<h3>${esc(t("counterpoints"))}</h3>` + counter.map((c) => renderClaim(c, a.passages, "counterpoint")).join("");
  if (disputed.length) html += `<h3>${esc(t("disputed"))}</h3>` + disputed.map((c) => renderClaim(c, a.passages, "disputed")).join("");
  if (a.rejected.length) html += `<h3>${esc(t("rejected"))}</h3>` + a.rejected.map((c) => renderClaim(c, a.passages, "rejected")).join("");
  if (a.open_questions.length) html += `<h3>${esc(t("open_q"))}</h3><ul>${a.open_questions.map((q) => `<li>${esc(q)}</li>`).join("")}</ul>`;
  html += `<p class="muted">${esc(a.disclaimer)}</p></div>`;
  html += renderDocuments(a.documents);
  if (a.passages.length) {
    html += `<div class="card"><h2>${esc(t("provisions"))}</h2>` + a.passages.map((sp) => {
      const p = sp.passage;
      const art = /^\d/.test(p.article) ? `Article ${p.article}` : p.article;
      return `<details class="passage"><summary><strong>[${esc(sp.label)}]</strong> ${esc(p.source_short)}, ${esc(art)}${p.heading ? ` - ${esc(p.heading)}` : ""}
        <span class="pill">${esc(p.jurisdiction)}</span> <span class="muted">${sp.score}</span></summary>
        ${p.notes ? `<p class="muted">${esc(p.notes)}</p>` : ""}<pre>${esc(p.text)}</pre></details>`;
    }).join("") + `</div>`;
  }
  return html;
}

function selectedJurisdictions() {
  const values = [...document.querySelectorAll('input[name="jur"]:checked')].map((el) => el.value);
  return values.length ? values : null;
}

$("#ask-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const out = $("#ask-out");
  const body = { question: $("#ask-q").value.trim(), context: $("#ask-context").value.trim(), jurisdictions: selectedJurisdictions(), lang: state.lang };
  state.lastQuestion = body;
  busy(out);
  try { out.innerHTML = renderAnswer(await api("/api/ask", { method: "POST", body })); } catch (err) { fail(out, err); }
});

$("#ask-to-case").addEventListener("click", () => {
  $("#case-q").value = $("#ask-q").value;
  $("#case-use").value = $("#ask-context").value;
  activate($("#tab-cases"));
  $("#case-owner").focus();
});

// ---------------- cases ----------------
async function loadCases() {
  const list = $("#case-list");
  try {
    const status = $("#case-filter").value;
    const cases = await api(`/api/cases${status ? `?status=${encodeURIComponent(status)}` : ""}`);
    if (!cases.length) { list.innerHTML = `<p class="muted">-</p>`; return; }
    list.innerHTML = `<div class="table-wrap"><table><thead><tr><th>ID</th><th>${esc(t("question"))}</th><th>${esc(t("owner"))}</th><th>Status</th><th>${esc(t("missing"))}</th></tr></thead><tbody>` +
      cases.map((c) => `<tr><td><button class="small" data-case="${esc(c.case_id)}">${esc(c.case_id)}</button></td>
        <td>${esc(c.question)}</td><td>${esc(c.owner)}</td><td>${esc(c.status)}</td>
        <td>${c.missing_mandatory ? `<span class="pill bad">${c.missing_mandatory}</span>` : "0"}</td></tr>`).join("") + `</tbody></table></div>`;
  } catch (err) { fail(list, err); }
}
$("#case-filter").addEventListener("change", loadCases);
$("#case-list").addEventListener("click", (e) => {
  const id = e.target.closest("[data-case]")?.dataset.case;
  if (id) openCase(id);
});

$("#case-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const detail = $("#case-detail");
  const btn = e.submitter; btn.disabled = true;
  busy(detail);
  try {
    const res = await api("/api/cases", { method: "POST", body: {
      owner: $("#case-owner").value.trim(), sector: $("#case-sector").value.trim(),
      question: $("#case-q").value.trim(), ai_use_case: $("#case-use").value.trim(), lang: state.lang,
    } });
    writePref("actor", $("#case-owner").value.trim());
    await loadCases();
    await openCase(res.case_id, res);
  } catch (err) { fail(detail, err); } finally { btn.disabled = false; }
});

async function openCase(caseId, created) {
  const detail = $("#case-detail");
  busy(detail);
  try {
    const c = await api(`/api/cases/${encodeURIComponent(caseId)}`);
    const actor = readPref("actor", "");
    let html = `<div class="card stack"><div class="row between"><h2>${esc(c.case_id)}</h2><span class="pill">${esc(c.status)}</span></div>
      <p>${esc(c.question)}</p><p class="muted">${esc(c.jurisdictions)} · ${esc(c.sector)} · ${esc(c.ai_use_case)}</p>`;
    if (c.alerts.length) html += `<div><strong>${esc(t("alerts"))}</strong><ul>${c.alerts.map((a) => `<li class="error">${esc(a)}</li>`).join("")}</ul></div>`;
    html += `<form id="review-form" class="grid2">
        <label><span>${esc(t("actor"))}</span><input name="actor" required value="${esc(actor)}"></label>
        <label><span>Status</span><select name="status">${["open", "in_review", "approved", "closed"].map((s) => `<option ${s === c.status ? "selected" : ""}>${s}</option>`).join("")}</select></label>
        <label><span>${esc(t("reviewer"))}</span><input name="reviewer" value="${esc(c.reviewer)}"></label>
        <label><span>${esc(t("review_note"))}</span><input name="review_note" value="${esc(c.review_note)}"></label>
        <div><button class="primary" type="submit">${esc(t("save"))}</button></div>
      </form></div>`;
    html += `<div class="card"><h2>${esc(t("docs"))}</h2><div class="table-wrap"><table><tbody>` + c.documents.map((d) => `
      <tr><td><strong>${esc(d.name)}</strong> ${d.mandatory ? `<span class="pill bad">${esc(t("mandatory"))}</span>` : ""}
        <div class="muted">${esc(d.note)}</div>${d.file ? `<div class="muted">${esc(d.file)}</div>` : ""}</td>
      <td><select data-doc-status="${esc(d.doc_id)}">${["missing", "received", "waived", "not_applicable"].map((s) => `<option value="${s}" ${s === d.status ? "selected" : ""}>${esc(t(s))}</option>`).join("")}</select></td>
      <td><input type="file" data-doc-file="${esc(d.doc_id)}" aria-label="${esc(t("upload"))}"></td></tr>`).join("") + `</tbody></table></div></div>`;
    if (created?.recommended_modules?.length) {
      html += `<div class="card"><h2>${esc(t("recommended"))}</h2><ul>${created.recommended_modules.map((m) => `<li>${esc(m.title)} <span class="muted">(${esc(m.level)})</span></li>`).join("")}</ul></div>`;
    }
    if (created?.answer) html += renderAnswer(created.answer);
    html += `<div class="card"><h2>${esc(t("log"))}</h2><ul>${c.log.map((l) => `<li class="muted">${esc(l.timestamp)} · ${esc(l.actor)} · ${esc(l.action)}</li>`).join("")}</ul></div>`;
    detail.innerHTML = html;

    $("#review-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const f = new FormData(e.target);
      writePref("actor", f.get("actor"));
      try {
        await api(`/api/cases/${encodeURIComponent(caseId)}`, { method: "PATCH", body: Object.fromEntries(f) });
        await loadCases(); await openCase(caseId);
      } catch (err) { alert(err.message); }
    });
    detail.querySelectorAll("[data-doc-status]").forEach((sel) => sel.addEventListener("change", async () => {
      try {
        await api(`/api/cases/${encodeURIComponent(caseId)}/documents/${encodeURIComponent(sel.dataset.docStatus)}`,
          { method: "PATCH", body: { status: sel.value, actor: readPref("actor", "") } });
        await loadCases(); await openCase(caseId);
      } catch (err) { alert(err.message); }
    }));
    detail.querySelectorAll("[data-doc-file]").forEach((input) => input.addEventListener("change", async () => {
      if (!input.files.length) return;
      const form = new FormData(); form.append("file", input.files[0]);
      try {
        await api(`/api/cases/${encodeURIComponent(caseId)}/documents/${encodeURIComponent(input.dataset.docFile)}/upload`, { method: "POST", body: form });
        await loadCases(); await openCase(caseId);
      } catch (err) { alert(err.message); }
    }));
  } catch (err) { fail(detail, err); }
}

// ---------------- learning ----------------
$("#learner-id").value = readPref("learner", "");
$("#learner-form").addEventListener("submit", (e) => { e.preventDefault(); writePref("learner", $("#learner-id").value.trim()); loadLearn(); });

async function loadLearn() {
  const out = $("#learn-out");
  const learner = readPref("learner", "");
  busy(out);
  try {
    const d = await api(`/api/learn/modules?lang=${state.lang}${learner ? `&learner_id=${encodeURIComponent(learner)}` : ""}`);
    out.innerHTML = `<div class="card"><h2>${esc(t("modules"))}</h2>` + d.modules.map((m) => {
      const p = m.progress;
      const prog = p ? `<span class="pill ${p.completed ? "ok" : ""}">${p.answered}/${p.total} · ${Math.round(p.score * 100)}%</span>` : "";
      return `<div class="row between" style="padding-block:8px;border-top:1px solid var(--border)">
        <div><strong>${esc(m.title)}</strong> <span class="pill">${esc(t(`level.${m.level}`))}</span> <span class="muted">${m.minutes} ${esc(t("min"))}</span> ${prog}
        <div class="muted">${esc(m.summary)}</div></div>
        <button class="ghost" data-module="${esc(m.id)}">${esc(t("open"))}</button></div>`;
    }).join("") + `</div><div class="card"><h2>${esc(t("tracks"))}</h2><ul>` +
      d.tracks.map((tr) => `<li><strong>${esc(tr.title)}</strong> - ${esc(tr.description)}</li>`).join("") + `</ul></div><div id="module-detail"></div>`;
    out.querySelectorAll("[data-module]").forEach((b) => b.addEventListener("click", () => openModule(b.dataset.module)));
  } catch (err) { fail(out, err); }
}

function renderPoint(p) {
  const cite = p.cite ? `<div class="cite muted">${esc(p.cite.source)}${p.cite.article ? ` art. ${esc(p.cite.article)}` : ""} ${checkPill(p.cite.check)}</div>` : "";
  const tag = p.kind === "law" ? "" : `<span class="pill ${p.kind === "note" ? "warn" : ""}">${esc(t(p.kind === "note" ? "note" : "practice"))}</span> `;
  return `<div class="point ${esc(p.kind)}">${tag}${esc(p.text)}${cite}</div>`;
}

async function openModule(id) {
  const box = $("#module-detail");
  const learner = readPref("learner", "");
  busy(box);
  try {
    const m = await api(`/api/learn/modules/${encodeURIComponent(id)}?lang=${state.lang}${learner ? `&learner_id=${encodeURIComponent(learner)}` : ""}`);
    box.innerHTML = `<div class="card"><h2>${esc(m.title)}</h2>` +
      m.lessons.map((l) => `<h3>${esc(l.title)}</h3>${l.points.map(renderPoint).join("")}`).join("") +
      `<h3>Quiz</h3>` + m.quiz.map((q) => `<form class="quiz-q" data-quiz="${esc(q.id)}"><strong>${esc(q.question)}</strong>
        ${q.options.map((o, i) => `<label><input type="radio" name="a" value="${i}" required> ${esc(o)}</label>`).join("")}
        <button class="ghost" type="submit">${esc(t("submit"))}</button><div class="feedback" aria-live="polite"></div></form>`).join("") +
      `<p class="muted">${esc(m.disclaimer)}</p></div>`;
    box.querySelectorAll("[data-quiz]").forEach((form) => form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const fb = form.querySelector(".feedback");
      if (!learner) { fb.innerHTML = `<p class="error">${esc(t("learner"))}?</p>`; $("#learner-id").focus(); return; }
      try {
        const r = await api("/api/learn/answer", { method: "POST", body: { learner_id: learner, quiz_id: form.dataset.quiz, answer: Number(new FormData(form).get("a")), lang: state.lang } });
        fb.innerHTML = `<p><span class="pill ${r.correct ? "ok" : "bad"}">${esc(t(r.correct ? "correct" : "wrong"))}</span> ${esc(r.explanation)}
          ${r.cite ? checkPill(r.cite.check) : ""}<br><span class="muted">${esc(t("score"))}: ${Math.round(r.module_progress.score * 100)}%</span></p>`;
      } catch (err) { fail(fb, err); }
    }));
  } catch (err) { fail(box, err); }
}

// ---------------- scenarios ----------------
async function loadScenarios() {
  const out = $("#scen-out");
  busy(out);
  try {
    const list = await api(`/api/learn/scenarios?lang=${state.lang}`);
    out.innerHTML = `<div class="card">` + list.map((s) => `<div class="row between" style="padding-block:8px;border-top:1px solid var(--border)">
      <div><strong>${esc(s.title)}</strong> <span class="pill">${esc(s.jurisdictions.join(", "))}</span> <span class="pill">${esc(t(`level.${s.level}`))}</span></div>
      <button class="ghost" data-scen="${esc(s.id)}">${esc(t("open"))}</button></div>`).join("") + `</div><div id="scen-detail"></div>`;
    out.querySelectorAll("[data-scen]").forEach((b) => b.addEventListener("click", () => openScenario(b.dataset.scen)));
  } catch (err) { fail(out, err); }
}

async function openScenario(id) {
  const box = $("#scen-detail");
  busy(box);
  try {
    const s = await api(`/api/learn/scenarios/${encodeURIComponent(id)}?lang=${state.lang}`);
    box.innerHTML = `<div class="card"><h2>${esc(s.title)}</h2><p>${esc(s.context)}</p>` + s.questions.map((q) => `
      <div class="quiz-q"><strong>${esc(q.question)}</strong><br>
      <button class="ghost" data-answer="${esc(q.id)}">${esc(t("show_answer"))}</button><div id="sa-${esc(q.id)}"></div></div>`).join("") + `</div>`;
    box.querySelectorAll("[data-answer]").forEach((b) => b.addEventListener("click", async () => {
      const target = document.getElementById(`sa-${b.dataset.answer}`);
      try {
        const a = await api(`/api/learn/scenarios/${encodeURIComponent(id)}/${encodeURIComponent(b.dataset.answer)}/answer?lang=${state.lang}`);
        target.innerHTML = (a.verdict ? `<p><strong>${esc(t("verdict"))}:</strong> ${esc(a.verdict)}</p>` : "") + a.points.map(renderPoint).join("") +
          (a.could_change?.length ? `<p><strong>${esc(t("could_change"))}</strong></p><ul>${a.could_change.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : "") +
          `<p class="muted">${esc(a.disclaimer)}</p>`;
      } catch (err) { fail(target, err); }
    }));
  } catch (err) { fail(box, err); }
}

// ---------------- sources ----------------
async function loadSources() {
  const out = $("#src-out");
  busy(out);
  try {
    const sources = await api(`/api/sources?lang=${state.lang}`);
    out.innerHTML = `<div class="card"><div class="table-wrap"><table><tbody>` + sources.map((s) => `
      <tr><td><strong>${esc(s.title)}</strong> <span class="pill">${esc(s.jurisdiction)}</span> <span class="pill">${esc(s.kind)}</span>
        <div class="muted">${esc(s.notes)}</div>
        ${s.extraction === "ai" ? `<div class="muted">${esc(t("ai_extraction"))}: ${s.ai_transcription ? "✓" : "-"}</div>` : ""}
        <div id="chk-${esc(s.id)}"></div></td>
      <td>${s.passages} ${esc(t("passages_n"))}<br>
        <span class="pill ${s.stale ? "warn" : "ok"}">${esc(t(s.stale ? "stale" : "fresh"))}</span>
        <div class="muted">${esc(t("last_checked"))}: ${esc(s.checked_at || t("never"))}</div></td>
      <td class="stack">${s.downloaded ? "" : `<a href="${esc(s.manual_url)}" target="_blank" rel="noopener">${esc(t("manual"))}</a>`}
        <button class="small" data-check="${esc(s.id)}">${esc(t("check_now"))}</button>
        <button class="small" data-diffs="${esc(s.id)}">${esc(t("diffs"))}</button></td></tr>`).join("") + `</tbody></table></div></div>`;
    out.querySelectorAll("[data-check]").forEach((b) => b.addEventListener("click", async () => {
      const box = document.getElementById(`chk-${b.dataset.check}`);
      b.disabled = true; busy(box);
      try {
        const r = await api(`/api/sources/${encodeURIComponent(b.dataset.check)}/check`, { method: "POST" });
        box.innerHTML = r.status === "changed" ? renderDiff(r) : `<p class="muted">${esc(r.status)} ${esc(r.detail || "")} - ${esc(t(r.status === "unchanged" ? "unchanged" : "changed"))}</p>`;
      } catch (err) { fail(box, err); } finally { b.disabled = false; }
    }));
    out.querySelectorAll("[data-diffs]").forEach((b) => b.addEventListener("click", async () => {
      const box = document.getElementById(`chk-${b.dataset.diffs}`);
      try {
        const reports = await api(`/api/sources/${encodeURIComponent(b.dataset.diffs)}/diffs`);
        box.innerHTML = reports.length ? reports.map(renderDiff).join("") : `<p class="muted">-</p>`;
      } catch (err) { fail(box, err); }
    }));
  } catch (err) { fail(out, err); }
}

function renderDiff(r) {
  const d = r.diff;
  return `<div class="stack"><p><strong>${esc(r.checked_at)}</strong> - added: ${esc(d.added.join(", ") || "-")} · removed: ${esc(d.removed.join(", ") || "-")} · unchanged: ${d.unchanged}</p>
    ${r.ai_summary?.text ? `<p class="pill warn">${esc(r.ai_summary.label)}</p><pre class="text">${esc(r.ai_summary.text)}</pre>` : ""}
    ${d.changed.map((c) => `<details><summary>Article ${esc(c.article)} (${Math.round(c.similarity * 100)}%)</summary><pre class="diff">${esc(c.diff)}</pre></details>`).join("")}</div>`;
}

// ---------------- init ----------------
applyLang();
const initial = document.getElementById(readPref("tab", "tab-ask"));
if (initial) activate(initial, false);
