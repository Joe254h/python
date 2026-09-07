/* Provenance dashboard.
 *
 * Vanilla JS, no framework and no build step. The application holds almost no
 * state of its own: `GET /api/me` and `GET /api/submissions` are the two
 * sources of truth, and everything on screen is rendered from them. In
 * particular the credit balance is never adjusted locally after an upload --
 * it is re-fetched, because the balance is the sum of a server-side ledger and
 * a number computed in a browser is a number that can be wrong.
 */

'use strict';

const $  = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const state = {
  me: null,
  submissions: [],
  view: 'dashboard',
  reportId: null,
  poll: null,
};

/* ------------------------------------------------------------------- http -- */

async function api(path, options = {}) {
  const res = await fetch(path, {
    credentials: 'same-origin',
    headers: options.body instanceof FormData
      ? {}
      : { 'Content-Type': 'application/json' },
    ...options,
  });
  if (res.status === 401) {
    state.me = null;
    showAuth();
    throw new Error('not signed in');
  }
  const text = await res.text();
  const data = text ? JSON.parse(text) : {};
  if (!res.ok) throw new Error(data.detail || `request failed (${res.status})`);
  return data;
}

/* ------------------------------------------------------------- formatting -- */

const pct = (v) => `${(v * 100).toFixed(1)}%`;

function timeAgo(iso) {
  if (!iso) return '—';
  const then = new Date(iso.includes('T') ? iso : iso.replace(' ', 'T') + 'Z');
  const secs = Math.max(0, (Date.now() - then.getTime()) / 1000);
  if (secs < 60) return 'just now';
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return `${Math.floor(secs / 86400)}d ago`;
}

const BAND_LABEL = { ok: 'No action', watch: 'Review', warn: 'Substantial', stop: 'Escalate' };

function bandBadge(row) {
  if (row.stage === 'failed') return `<span class="badge badge-fail"><i class="dot"></i>Failed</span>`;
  if (row.stage !== 'complete') {
    return `<span class="badge badge-run"><i class="dot dot-pulse"></i>${escapeHtml(row.stage)}</span>`;
  }
  const band = row.band || 'ok';
  return `<span class="badge badge-${band}"><i class="dot"></i>${pct(row.similarity || 0)} · ${BAND_LABEL[band]}</span>`;
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

/* ------------------------------------------------------------------- auth -- */

function showAuth() {
  stopPolling();
  $('#auth').hidden = false;
  $('#app').hidden = true;
}

let authMode = 'signin';

$$('.tab').forEach((tab) => tab.addEventListener('click', () => {
  authMode = tab.dataset.mode;
  $$('.tab').forEach((t) => t.classList.toggle('is-active', t === tab));
  $$('[data-signup-only]').forEach((el) => { el.hidden = authMode !== 'signup'; });
  $('#auth-submit').textContent = authMode === 'signup' ? 'Create account' : 'Sign in';
  $('#auth-error').hidden = true;
}));

$('#auth-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const err = $('#auth-error');
  err.hidden = true;
  const button = $('#auth-submit');
  button.disabled = true;

  try {
    const body = {
      email: form.get('email'),
      password: form.get('password'),
    };
    if (authMode === 'signup') {
      body.display_name = form.get('display_name') || '';
      body.corpus_consent = form.get('corpus_consent') === 'on';
    }
    await api(`/api/auth/${authMode}`, { method: 'POST', body: JSON.stringify(body) });
    await boot();
  } catch (e) {
    err.textContent = e.message;
    err.hidden = false;
  } finally {
    button.disabled = false;
  }
});

$('#signout').addEventListener('click', async () => {
  await api('/api/auth/signout', { method: 'POST' }).catch(() => {});
  state.me = null;
  showAuth();
});

/* ------------------------------------------------------------------ views -- */

function setView(view) {
  state.view = view;
  $$('.view').forEach((el) => { el.hidden = el.dataset.view !== view; });
  $$('.nav-item').forEach((el) => el.classList.toggle('is-active', el.dataset.view === view));
  if (view === 'credits') loadLedger();
}

$$('.nav-item').forEach((el) => el.addEventListener('click', () => setView(el.dataset.view)));
$$('[data-view-jump]').forEach((el) =>
  el.addEventListener('click', () => setView(el.dataset.viewJump)));
$('#report-back').addEventListener('click', () => setView('dashboard'));

/* -------------------------------------------------------------- dashboard -- */

function renderMe() {
  const me = state.me;
  if (!me) return;

  $('#demo-banner').hidden = !me.demo_mode;
  $('#greet-name').textContent = me.user.display_name;
  $('#who-name').textContent = me.user.display_name;
  $('#who-email').textContent = me.user.email;

  $('#stat-credits').textContent = me.credits;
  $('#stat-processing').textContent = me.counts.processing;
  $('#stat-completed').textContent = me.counts.completed;

  $('#credit-pill').textContent = `${me.credits} credit${me.credits === 1 ? '' : 's'} available`;
  $('#quick-sub').textContent =
    `Upload a document for processing (${me.cost_per_submission} credit).`;
  $('#accepts').textContent =
    `${me.accepted_types.join(', ')} — up to ${me.max_upload_mb}MB`;

  $('#low-credits').hidden = me.credits > 1;
  $('#file').setAttribute('accept', me.accepted_types.join(','));
}

function submissionsTable(rows, limit) {
  const shown = limit ? rows.slice(0, limit) : rows;
  if (!shown.length) {
    return `<p class="empty">Nothing here yet. Upload a document to get started.</p>`;
  }
  return `<div class="table-wrap"><table>
    <thead><tr>
      <th>Document</th><th>Status</th><th class="num">Words</th><th class="num">Submitted</th>
    </tr></thead>
    <tbody>${shown.map((row) => `
      <tr class="${row.stage === 'complete' ? 'clickable' : ''}" data-id="${row.submission_id}">
        <td>
          ${escapeHtml(row.filename)}
          ${row.is_mock ? '<span class="badge badge-mock">mock</span>' : ''}
          ${row.error ? `<div class="muted small">${escapeHtml(row.error)}</div>` : ''}
        </td>
        <td>${bandBadge(row)}</td>
        <td class="num">${row.word_count ?? '—'}</td>
        <td class="num muted">${timeAgo(row.created_at)}</td>
      </tr>`).join('')}
    </tbody></table></div>`;
}

function renderSubmissions() {
  $('#recent').innerHTML = submissionsTable(state.submissions, 5);
  $('#all-submissions').innerHTML = submissionsTable(state.submissions);
  $$('tr.clickable').forEach((tr) =>
    tr.addEventListener('click', () => openReport(tr.dataset.id)));
}

/* ----------------------------------------------------------------- upload -- */

const drop = $('#drop');
const fileInput = $('#file');

$('#browse').addEventListener('click', () => fileInput.click());
$('#new-submission').addEventListener('click', () => { setView('dashboard'); fileInput.click(); });
fileInput.addEventListener('change', () => {
  if (fileInput.files.length) upload(fileInput.files[0]);
});

['dragenter', 'dragover'].forEach((ev) => drop.addEventListener(ev, (e) => {
  e.preventDefault();
  drop.classList.add('is-over');
}));
['dragleave', 'drop'].forEach((ev) => drop.addEventListener(ev, (e) => {
  e.preventDefault();
  drop.classList.remove('is-over');
}));
drop.addEventListener('drop', (e) => {
  if (e.dataTransfer.files.length) upload(e.dataTransfer.files[0]);
});

async function upload(file) {
  const err = $('#upload-error');
  err.hidden = true;
  const body = new FormData();
  body.append('file', file);
  try {
    await api('/api/submissions', { method: 'POST', body });
    fileInput.value = '';
    await refresh();
    startPolling();
  } catch (e) {
    err.textContent = e.message;
    err.hidden = false;
  }
}

/* ---------------------------------------------------------------- credits -- */

$('#redeem-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const err = $('#redeem-error');
  const ok = $('#redeem-ok');
  err.hidden = true;
  ok.hidden = true;
  try {
    const data = await api('/api/credits/redeem', {
      method: 'POST',
      body: JSON.stringify({ code: new FormData(event.target).get('code') }),
    });
    ok.textContent = `Redeemed. Your balance is now ${data.credits}.`;
    ok.hidden = false;
    event.target.reset();
    await refresh();
    loadLedger();
  } catch (e) {
    err.textContent = e.message;
    err.hidden = false;
  }
});

async function loadLedger() {
  const { entries } = await api('/api/credits/history').catch(() => ({ entries: [] }));
  $('#ledger').innerHTML = entries.length
    ? `<div class="table-wrap"><table>
        <thead><tr><th>Reason</th><th class="num">Change</th><th class="num">When</th></tr></thead>
        <tbody>${entries.map((e) => `<tr>
          <td>${escapeHtml(e.reason)}</td>
          <td class="num" style="color:${e.delta > 0 ? 'var(--ok)' : 'var(--text-2)'}">
            ${e.delta > 0 ? '+' : ''}${e.delta}</td>
          <td class="num muted">${timeAgo(e.created_at)}</td>
        </tr>`).join('')}</tbody></table></div>`
    : `<p class="empty">No ledger entries yet.</p>`;
}

/* ----------------------------------------------------------------- report -- */

const BAND_COLOR = {
  ok: 'var(--ok)', watch: 'var(--watch)', warn: 'var(--warn)', stop: 'var(--stop)',
};

function highlight(text, matches) {
  /* Build the marked-up document by walking non-overlapping match spans in
   * order. Overlapping spans are merged first: rendering nested <mark> tags
   * would double-count visually and imply more coverage than exists. */
  if (!matches.length) return escapeHtml(text);

  const spans = matches
    .map((m) => ({ start: m.span.start, end: m.span.end, kind: m.kind }))
    .sort((a, b) => a.start - b.start);

  const merged = [spans[0]];
  for (const s of spans.slice(1)) {
    const last = merged[merged.length - 1];
    if (s.start <= last.end) {
      last.end = Math.max(last.end, s.end);
    } else {
      merged.push(s);
    }
  }

  let out = '';
  let cursor = 0;
  for (const s of merged) {
    out += escapeHtml(text.slice(cursor, s.start));
    const cls = s.kind === 'paraphrase' ? 'hit hit-paraphrase' : 'hit';
    out += `<mark class="${cls}">${escapeHtml(text.slice(s.start, s.end))}</mark>`;
    cursor = s.end;
  }
  return out + escapeHtml(text.slice(cursor));
}

function aiPanel(report) {
  if (!report.ai_signals || !report.ai_signals.length) {
    return `<div class="notice">
      <strong>AI-writing detection did not run.</strong> No calibration is
      configured on this deployment, so no estimate is shown. That is not the
      same as a score of zero.</div>`;
  }
  const p = report.ai_probability ?? 0;
  const fpr = report.ai_signals[0].fpr_at_threshold;
  return `
    <div class="score"><span class="score-value">${pct(p)}</span></div>
    <p class="muted small">Estimated probability this document was machine-written.</p>
    <div class="notice" style="margin-top:.9rem">
      <strong>Read this as an estimate, not a verdict.</strong>
      At the operating threshold used here the measured false positive rate is
      ${(fpr * 100).toFixed(1)}%. Detectors of this kind flag second-language
      English writing far more often than first-language writing, so this number
      is evidence to investigate with, never on its own grounds for an
      accusation.</div>`;
}

async function openReport(id) {
  const data = await api(`/api/submissions/${id}`);
  state.reportId = id;
  setView('report');

  $('#report-title').textContent = data.filename;
  $('#report-meta').textContent =
    `${data.word_count ?? 0} words scored · submitted ${timeAgo(data.created_at)}`;

  const report = data.report;
  if (!report) {
    $('#report-body').innerHTML =
      `<section class="panel"><p class="empty">${escapeHtml(data.error || 'No report.')}</p></section>`;
    return;
  }

  const band = report.band || 'ok';
  const sources = report.sources || [];

  $('#report-body').innerHTML = `
    ${report.is_mock ? `<div class="panel" style="border-color:#7a4a20">
      <strong style="color:#ffb457">These results are fabricated.</strong>
      <p class="muted small" style="margin-top:.3rem">This deployment runs
      MockDetector. No document was actually analysed.</p></div>` : ''}

    <div class="report-grid">
      <div>
        <section class="panel">
          <div class="panel-head"><h2>Matched text</h2>
            <span class="pill">${report.matches.length} match${report.matches.length === 1 ? '' : 'es'}</span>
          </div>
          <div class="doc-text">${highlight(data.text || '', report.matches)}</div>
        </section>
      </div>

      <div>
        <section class="panel">
          <div class="panel-head"><h2>Similarity</h2></div>
          <div class="score">
            <span class="score-value" style="color:${BAND_COLOR[band]}">${pct(report.similarity)}</span>
            <span class="score-of">of ${report.word_count} scored words</span>
          </div>
          <div class="bar"><i style="width:${Math.min(100, report.similarity * 100)}%;
            background:${BAND_COLOR[band]}"></i></div>
          <p class="muted small">${BAND_LABEL[band]} · quotations and the
            reference list are excluded from both the matched text and the total.</p>
        </section>

        <section class="panel">
          <div class="panel-head"><h2>Sources</h2></div>
          ${sources.length ? `<div class="src-list">${sources.map((s) => `
            <div class="src">
              <div class="src-title">${escapeHtml(s.title)}</div>
              <div class="src-meta">${escapeHtml(s.origin)}${s.anonymised ? ' · anonymised' : ''}</div>
              ${s.url ? `<a class="src-meta" href="${escapeHtml(s.url)}" target="_blank"
                 rel="noopener noreferrer">${escapeHtml(s.url)}</a>` : ''}
            </div>`).join('')}</div>`
            : `<p class="empty">No sources matched.</p>`}
        </section>

        <section class="panel">
          <div class="panel-head"><h2>AI-writing detection</h2></div>
          ${aiPanel(report)}
        </section>

        <section class="panel">
          <div class="panel-head"><h2>Run details</h2></div>
          ${Object.entries(report.detector_versions || {}).map(([k, v]) =>
            `<div class="kv"><span>${escapeHtml(k)}</span><span>${escapeHtml(v)}</span></div>`).join('')}
        </section>
      </div>
    </div>`;
}

/* ------------------------------------------------------------------ polling */

function startPolling() {
  stopPolling();
  state.poll = setInterval(async () => {
    await refresh();
    if (!state.submissions.some((s) => s.stage !== 'complete' && s.stage !== 'failed')) {
      stopPolling();
    }
  }, 1500);
}

function stopPolling() {
  if (state.poll) clearInterval(state.poll);
  state.poll = null;
}

/* --------------------------------------------------------------------- boot */

async function refresh() {
  const [me, subs] = await Promise.all([api('/api/me'), api('/api/submissions')]);
  state.me = me;
  state.submissions = subs.submissions;
  renderMe();
  renderSubmissions();
}

async function boot() {
  try {
    await refresh();
    $('#auth').hidden = true;
    $('#app').hidden = false;
    setView('dashboard');
    if (state.submissions.some((s) => s.stage !== 'complete' && s.stage !== 'failed')) {
      startPolling();
    }
  } catch {
    showAuth();
  }
}

boot();
