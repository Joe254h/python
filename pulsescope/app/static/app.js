/* PulseScope front end. No build step, no CDN — plain DOM + inline SVG. */

const $ = (id) => document.getElementById(id);
const SVG_NS = "http://www.w3.org/2000/svg";

/* Categorical slots in fixed order — a subject keeps its colour no matter
   how the ranking reshuffles. Slot 9+ folds into "Other". */
const SERIES_SLOTS = 8;
const seriesColor = (i) => `var(--series-${Math.min(i, SERIES_SLOTS - 1) + 1})`;

/* Documented sequential blue ramp, light -> dark. */
const SEQ = ["#cde2fb", "#b7d3f6", "#9ec5f4", "#86b6ef", "#6da7ec", "#5598e7",
             "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95", "#104281", "#0d366b"];

const EXAMPLES = [
  "Rate Philip Munialo against Moses Lupao, Emmanuel Waswa, Dawson Mudenyo, Peter Mukiri, Kitur Kibiyego and Nick Biketi, in terms of momentum building, message clarity and manifesto, social media presence and ground visibility.",
  "Compare Safaricom against Airtel Kenya and Telkom Kenya on social media presence, public sentiment and momentum over the last 60 days.",
  "Rank Bungoma, Kakamega and Busia county governments on message clarity and ground visibility.",
];

let state = { run: null, subjectIndex: new Map() };

/* ------------------------------------------------------------------ utils */

const el = (tag, attrs = {}, text) => {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v; else node.setAttribute(k, v);
  }
  if (text !== undefined) node.textContent = text;
  return node;
};

const svgEl = (tag, attrs = {}) => {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
  return node;
};

const fmt = (n) => (n >= 1_000_000 ? (n / 1e6).toFixed(1) + "M"
  : n >= 1_000 ? (n / 1e3).toFixed(1) + "k" : String(n));

const escapeHtml = (s) => String(s ?? "").replace(/[&<>"']/g,
  (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* Rounded-end horizontal bar: 4px radius on the value end only, so the
   bar stays anchored to its baseline. */
function barPath(x0, y, w, h, r = 4) {
  const radius = Math.min(r, Math.max(0, w), h / 2);
  const x1 = x0 + Math.max(w, 0.5);
  if (radius <= 0.5) return `M${x0},${y}H${x1}V${y + h}H${x0}Z`;
  return `M${x0},${y}H${x1 - radius}A${radius},${radius} 0 0 1 ${x1},${y + radius}` +
         `V${y + h - radius}A${radius},${radius} 0 0 1 ${x1 - radius},${y + h}H${x0}Z`;
}

/* ---------------------------------------------------------------- tooltip */

const tip = $("tooltip");
function showTip(evt, title, rows) {
  tip.innerHTML = `<div class="t-title">${escapeHtml(title)}</div>` +
    rows.map((r) => `<div class="t-row">${escapeHtml(r)}</div>`).join("");
  tip.classList.remove("hidden");
  moveTip(evt);
}
function moveTip(evt) {
  const pad = 14;
  const rect = tip.getBoundingClientRect();
  let x = evt.clientX + pad, y = evt.clientY + pad;
  if (x + rect.width > window.innerWidth - 8) x = evt.clientX - rect.width - pad;
  if (y + rect.height > window.innerHeight - 8) y = evt.clientY - rect.height - pad;
  tip.style.left = `${Math.max(8, x)}px`;
  tip.style.top = `${Math.max(8, y)}px`;
}
const hideTip = () => tip.classList.add("hidden");

function attachTip(node, title, rows) {
  node.addEventListener("mouseenter", (e) => showTip(e, title, rows));
  node.addEventListener("mousemove", moveTip);
  node.addEventListener("mouseleave", hideTip);
}

/* ----------------------------------------------------------------- charts */

/**
 * Horizontal ranked bars. Every bar is direct-labelled with its subject and
 * value, so identity never depends on colour alone.
 */
function rankedBars(container, rows, { max = 100, showAxis = true, unit = "" } = {}) {
  container.innerHTML = "";
  if (!rows.length) return;

  const rowH = 26, gap = 6, padTop = showAxis ? 18 : 6, padBottom = 6;
  const labelW = 150, valueW = 46, right = 12;
  const height = padTop + rows.length * (rowH + gap) - gap + padBottom;
  const width = 640;
  const plotX = labelW, plotW = width - labelW - valueW - right;

  const svg = svgEl("svg", {
    viewBox: `0 0 ${width} ${height}`, role: "img",
    "aria-label": rows.map((r) => `${r.label} ${r.value}`).join(", "),
  });

  if (showAxis) {
    for (const t of [0, 25, 50, 75, 100]) {
      const x = plotX + (t / max) * plotW;
      svg.appendChild(svgEl("line", {
        x1: x, x2: x, y1: padTop - 4, y2: height - padBottom,
        class: t === 0 ? "baseline" : "gridline",
      }));
      const label = svgEl("text", { x, y: padTop - 8, class: "axis-label", "text-anchor": "middle" });
      label.textContent = t;
      svg.appendChild(label);
    }
  }

  rows.forEach((row, i) => {
    const y = padTop + i * (rowH + gap);
    const w = Math.max(1, (row.value / max) * plotW);

    const name = svgEl("text", { x: labelW - 10, y: y + rowH / 2 + 4, class: "bar-label", "text-anchor": "end" });
    name.textContent = row.label.length > 22 ? row.label.slice(0, 21) + "…" : row.label;
    svg.appendChild(name);

    const bar = svgEl("path", {
      d: barPath(plotX, y + 3, w, rowH - 6),
      fill: row.color, class: "bar",
    });
    attachTip(bar, row.label, row.tip || [`${row.value}${unit}`]);
    svg.appendChild(bar);

    const value = svgEl("text", { x: plotX + w + 8, y: y + rowH / 2 + 4, class: "bar-value" });
    value.textContent = `${row.value}${unit}`;
    svg.appendChild(value);
  });

  container.appendChild(svg);
}

/** Weekly mention counts as a thin line with a soft area under it. */
function timeline(container, weeks, counts, color, subject) {
  container.innerHTML = "";
  const width = 340, height = 96, padL = 26, padR = 8, padT = 10, padB = 18;
  const plotW = width - padL - padR, plotH = height - padT - padB;
  const max = Math.max(1, ...counts);

  const svg = svgEl("svg", {
    viewBox: `0 0 ${width} ${height}`, role: "img",
    "aria-label": `${subject}: ${counts.reduce((a, b) => a + b, 0)} items across ${weeks.length} weeks`,
  });

  svg.appendChild(svgEl("line", {
    x1: padL, x2: width - padR, y1: padT + plotH, y2: padT + plotH, class: "baseline",
  }));
  const top = svgEl("text", { x: padL - 6, y: padT + 4, class: "axis-label", "text-anchor": "end" });
  top.textContent = max;
  svg.appendChild(top);

  const xAt = (i) => padL + (weeks.length <= 1 ? plotW / 2 : (i / (weeks.length - 1)) * plotW);
  const yAt = (v) => padT + plotH - (v / max) * plotH;

  if (weeks.length) {
    const line = counts.map((c, i) => `${i ? "L" : "M"}${xAt(i).toFixed(1)},${yAt(c).toFixed(1)}`).join("");
    svg.appendChild(svgEl("path", {
      d: `${line}L${xAt(counts.length - 1).toFixed(1)},${padT + plotH}L${xAt(0).toFixed(1)},${padT + plotH}Z`,
      fill: color, opacity: "0.14",
    }));
    svg.appendChild(svgEl("path", { d: line, fill: "none", stroke: color, "stroke-width": 2,
      "stroke-linejoin": "round", "stroke-linecap": "round" }));

    counts.forEach((c, i) => {
      const hit = svgEl("circle", { cx: xAt(i), cy: yAt(c), r: 9, fill: "transparent" });
      attachTip(hit, subject, [`${weeks[i]}: ${c} item${c === 1 ? "" : "s"}`]);
      svg.appendChild(hit);
      if (c === max) {
        svg.appendChild(svgEl("circle", { cx: xAt(i), cy: yAt(c), r: 4, fill: color,
          stroke: "var(--surface-1)", "stroke-width": 2 }));
      }
    });

    const first = svgEl("text", { x: padL, y: height - 5, class: "axis-label" });
    first.textContent = weeks[0];
    svg.appendChild(first);
    if (weeks.length > 1) {
      const last = svgEl("text", { x: width - padR, y: height - 5, class: "axis-label", "text-anchor": "end" });
      last.textContent = weeks[weeks.length - 1];
      svg.appendChild(last);
    }
  }
  container.appendChild(svg);
}

/* -------------------------------------------------------------- rendering */

function renderLegend(run) {
  const box = $("legend");
  box.innerHTML = "";
  run.results.forEach((r) => {
    const item = el("span", { class: "legend-item" });
    const sw = el("span", { class: "swatch" });
    sw.style.background = seriesColor(state.subjectIndex.get(r.subject));
    item.appendChild(sw);
    item.appendChild(el("span", {}, r.subject));
    box.appendChild(item);
  });
}

function renderOverall(run) {
  const rows = run.results.map((r) => ({
    label: r.subject,
    value: r.overall,
    color: seriesColor(state.subjectIndex.get(r.subject)),
    tip: [
      `Overall ${r.overall}/100 · rank ${r.rank}`,
      `${r.mention_count} items collected`,
      `${fmt(r.total_engagement)} total engagement`,
      r.simulated_share > 0 ? `${Math.round(r.simulated_share * 100)}% simulated` : "live data",
    ],
  }));
  rankedBars($("overallChart"), rows, { max: 100 });
}

function renderMetrics(run) {
  const host = $("metricCharts");
  host.innerHTML = "";
  run.query.metrics.forEach((metric) => {
    const panel = el("div");
    const ordered = [...run.results].sort(
      (a, b) => b.metrics[metric].score - a.metrics[metric].score);
    panel.appendChild(el("p", { class: "chart-title" }, metricLabel(metric)));
    panel.appendChild(el("p", { class: "chart-note" },
      `Leader: ${ordered[0].subject} (${ordered[0].metrics[metric].score})`));
    const chart = el("div");
    panel.appendChild(chart);
    host.appendChild(panel);

    rankedBars(chart, ordered.map((r) => {
      const ms = r.metrics[metric];
      return {
        label: r.subject,
        value: ms.score,
        color: seriesColor(state.subjectIndex.get(r.subject)),
        tip: [`${metricLabel(metric)}: ${ms.score}/100 (rank ${ms.rank})`,
          ...Object.entries(ms.components).map(([k, v]) => `${k.replace(/_/g, " ")}: ${v}`)],
      };
    }), { max: 100 });
  });
}

function heatColor(score) {
  const dark = document.documentElement.dataset.theme === "dark" ||
    (!document.documentElement.dataset.theme &&
      window.matchMedia("(prefers-color-scheme: dark)").matches);
  const t = Math.max(0, Math.min(1, score / 100));
  const idx = Math.round(t * (SEQ.length - 1));
  // On a dark surface "near zero" must recede toward the surface, so the ramp flips.
  const step = dark ? SEQ[SEQ.length - 1 - idx] : SEQ[idx];
  const ink = dark ? (idx > 6 ? "#0b0b0b" : "#ffffff") : (idx > 6 ? "#ffffff" : "#0b0b0b");
  return { bg: step, ink };
}

function renderHeat(run) {
  const table = $("heatTable");
  table.innerHTML = "";
  const head = el("tr");
  ["#", "Subject", "Overall", ...run.query.metrics.map(metricLabel), "Items", "Engagement", "Source"]
    .forEach((h, i) => head.appendChild(el("th", { class: i >= 2 ? "num" : "" }, h)));
  table.appendChild(head);

  run.results.forEach((r) => {
    const tr = el("tr");
    tr.appendChild(el("td", { class: "num" }, String(r.rank)));
    const name = el("td", { class: "subject" });
    const sw = el("span", { class: "swatch" });
    sw.style.cssText = `background:${seriesColor(state.subjectIndex.get(r.subject))};display:inline-block;margin-right:7px;vertical-align:-1px`;
    name.appendChild(sw);
    name.appendChild(document.createTextNode(r.subject));
    tr.appendChild(name);

    [r.overall, ...run.query.metrics.map((m) => r.metrics[m].score)].forEach((v) => {
      const td = el("td", { class: "num" });
      const cell = el("span", { class: "heat-cell" }, String(v));
      const { bg, ink } = heatColor(v);
      cell.style.background = bg;
      cell.style.color = ink;
      td.appendChild(cell);
      tr.appendChild(td);
    });

    tr.appendChild(el("td", { class: "num" }, String(r.mention_count)));
    tr.appendChild(el("td", { class: "num" }, fmt(r.total_engagement)));
    tr.appendChild(el("td", { class: "num" },
      r.simulated_share >= 0.999 ? "simulated"
        : r.simulated_share > 0 ? `${Math.round((1 - r.simulated_share) * 100)}% live` : "live"));
    table.appendChild(tr);
  });
}

function renderTimelines(run) {
  const host = $("timelineCharts");
  host.innerHTML = "";
  run.results.forEach((r) => {
    const weeks = Object.keys(r.timeline);
    const panel = el("div");
    panel.appendChild(el("p", { class: "chart-title" }, r.subject));
    panel.appendChild(el("p", { class: "chart-note" },
      `${r.mention_count} items · ${Object.keys(r.platforms).length} platforms`));
    const chart = el("div");
    panel.appendChild(chart);
    host.appendChild(panel);
    timeline(chart, weeks.map((w) => w.replace(/^\d{4}-/, "")),
      weeks.map((w) => r.timeline[w]),
      seriesColor(state.subjectIndex.get(r.subject)), r.subject);
  });
}

function renderDetails(run) {
  const host = $("details");
  host.innerHTML = "";
  run.results.forEach((r) => {
    const d = el("details");
    const s = el("summary");
    s.appendChild(document.createTextNode(`${r.rank}. ${r.subject} — ${r.overall}/100`));
    s.appendChild(el("span", { class: "rank-pill" },
      `${r.mention_count} items · ${fmt(r.total_engagement)} engagement` +
      (r.simulated_share > 0 ? ` · ${Math.round(r.simulated_share * 100)}% simulated` : "")));
    d.appendChild(s);

    const body = el("div", { class: "detail-body" });

    run.query.metrics.forEach((m) => {
      const ms = r.metrics[m];
      const box = el("div");
      box.appendChild(el("p", { class: "chart-title" }, `${metricLabel(m)} — ${ms.score}/100`));
      const list = el("div", { class: "kv" });
      Object.entries(ms.components).forEach(([k, v]) => {
        const line = el("div");
        line.innerHTML = `${escapeHtml(k.replace(/_/g, " "))}: <b>${v}</b>`;
        list.appendChild(line);
      });
      box.appendChild(list);
      (ms.evidence || []).forEach((e) => box.appendChild(el("p", { class: "evidence" }, e)));
      body.appendChild(box);
    });

    const extra = el("div");
    extra.appendChild(el("p", { class: "chart-title" }, "Platform mix"));
    const mix = el("div", { class: "kv" });
    Object.entries(r.platforms).sort((a, b) => b[1] - a[1]).forEach(([p, c]) => {
      const line = el("div");
      line.innerHTML = `${escapeHtml(p)}: <b>${c}</b>`;
      mix.appendChild(line);
    });
    extra.appendChild(mix);
    extra.appendChild(el("p", { class: "chart-title", style: "margin-top:12px" }, "Recurring terms"));
    const terms = el("div", { class: "terms" });
    (r.top_terms || []).forEach(([t, c]) => terms.appendChild(el("span", { class: "term" }, `${t} ${c}`)));
    extra.appendChild(terms);
    body.appendChild(extra);

    d.appendChild(body);
    host.appendChild(d);
  });
}

function renderLog(run) {
  const tally = { ok: 0, skipped: 0, error: 0 };
  run.actor_reports.forEach((r) => { tally[r.status] = (tally[r.status] || 0) + 1; });
  const dormant = new Set(run.actor_reports.filter((r) => r.status === "skipped").map((r) => r.actor));
  $("logSummary").textContent =
    `${run.actor_reports.length} calls — ${tally.ok} returned data, ` +
    `${tally.skipped} skipped (no credential), ${tally.error} failed` +
    (dormant.size ? ` · dormant actors: ${[...dormant].join(", ")}` : "");

  const table = $("logTable");
  table.innerHTML = "";
  const head = el("tr");
  ["Actor", "Platform", "Subject", "Status", "Items", "Detail", "ms"].forEach((h, i) =>
    head.appendChild(el("th", { class: i >= 4 && i !== 5 ? "num" : "" }, h)));
  table.appendChild(head);

  [...run.actor_reports]
    .sort((a, b) => (a.status === b.status ? 0 : a.status === "ok" ? -1 : 1))
    .forEach((rep) => {
      const tr = el("tr");
      tr.appendChild(el("td", {}, rep.actor));
      tr.appendChild(el("td", {}, rep.platform));
      tr.appendChild(el("td", {}, rep.subject));
      const st = el("td");
      st.appendChild(el("span", {
        class: `badge ${rep.status === "ok" ? (rep.simulated ? "warn" : "good") : rep.status === "error" ? "crit" : ""}`,
      }, rep.simulated && rep.status === "ok" ? "simulated" : rep.status));
      tr.appendChild(st);
      tr.appendChild(el("td", { class: "num" }, String(rep.items)));
      tr.appendChild(el("td", {}, rep.detail || "—"));
      tr.appendChild(el("td", { class: "num" }, String(rep.elapsed_ms)));
      table.appendChild(tr);
    });
}

let METRIC_LABELS = {};
const metricLabel = (id) => METRIC_LABELS[id] || id;

function renderWarnings(run) {
  const host = $("warnings");
  host.innerHTML = "";
  (run.warnings || []).forEach((w) => host.appendChild(el("div", { class: "notice" }, w)));
  if (run.data_quality === 0) {
    host.appendChild(el("div", { class: "notice error" },
      "Every figure in this run is simulated. Add API credentials to .env and re-launch before quoting any number."));
  }
}

function renderRun(run) {
  state.run = run;
  state.subjectIndex = new Map(
    [...run.results].sort((a, b) => a.subject.localeCompare(b.subject))
      .map((r, i) => [r.subject, i]));

  $("queryEcho").textContent =
    `${run.results.length} subjects · ${run.total_mentions} items · ` +
    `${run.query.lookback_days}-day window · ${run.query.region} · ` +
    `${Math.round(run.data_quality * 100)}% live data`;
  $("summary").textContent = run.summary;

  const links = $("exportLinks");
  links.innerHTML = "";
  const scores = el("a", { href: `/api/runs/${run.job_id}/scores.csv` }, "Download scores CSV");
  const items = el("a", { href: `/api/runs/${run.job_id}/mentions.csv` }, "Download sample items CSV");
  const json = el("a", { href: `/api/runs/${run.job_id}`, target: "_blank" }, "Raw JSON");
  links.append(scores, items, json, el("span", { class: "muted" }, `job ${run.job_id}`));

  renderWarnings(run);
  renderLegend(run);
  renderOverall(run);
  renderMetrics(run);
  renderHeat(run);
  renderTimelines(run);
  renderDetails(run);
  renderLog(run);

  ["summaryCard", "overallCard", "metricCard", "heatCard", "volumeCard", "detailCard", "logCard"]
    .forEach((id) => $(id).classList.remove("hidden"));
}

/* --------------------------------------------------------------- plumbing */

async function launch() {
  const prompt = $("prompt").value.trim() || $("prompt").placeholder;
  const btn = $("launch");
  btn.disabled = true;
  $("status").innerHTML = '<span class="spinner"></span> scraping…';
  $("warnings").innerHTML = "";

  try {
    const res = await fetch("/api/launch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        region: $("region").value,
        lookback_days: Number($("lookback").value) || 90,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Run failed");
    }
    const run = await res.json();
    renderRun(run);
    $("status").textContent = `done in ${((new Date(run.finished_at) - new Date(run.started_at)) / 1000).toFixed(1)}s`;
  } catch (e) {
    $("warnings").appendChild(el("div", { class: "notice error" }, e.message));
    $("status").textContent = "";
  } finally {
    btn.disabled = false;
  }
}

async function loadCapabilities() {
  const [actorsRes, metricsRes] = await Promise.all([
    fetch("/api/actors").then((r) => r.json()),
    fetch("/api/metrics").then((r) => r.json()),
  ]);
  METRIC_LABELS = Object.fromEntries(metricsRes.metrics.map((m) => [m.id, m.label]));

  const badges = $("capabilities");
  badges.innerHTML = "";
  const live = actorsRes.available, total = actorsRes.actors.length;
  badges.appendChild(el("span", { class: `badge ${live ? "good" : "warn"}` },
    `${live}/${total} actors ready`));
  if (actorsRes.demo_mode) badges.appendChild(el("span", { class: "badge warn" }, "demo mode — simulated output"));

  const table = $("actorTable");
  table.innerHTML = "";
  const head = el("tr");
  ["Actor", "Platform", "Needs", "State", "What it does"].forEach((h) => head.appendChild(el("th", {}, h)));
  table.appendChild(head);
  actorsRes.actors.forEach((a) => {
    const tr = el("tr");
    tr.appendChild(el("td", {}, a.name));
    tr.appendChild(el("td", {}, a.platform));
    tr.appendChild(el("td", {}, a.requires.join(", ") || "—"));
    const st = el("td");
    st.appendChild(el("span", { class: `badge ${a.available ? "good" : ""}` },
      a.available ? "ready" : "dormant"));
    tr.appendChild(st);
    const what = el("td", {}, a.available ? a.description : `${a.description} (${a.reason})`);
    what.style.whiteSpace = "normal";
    tr.appendChild(what);
    table.appendChild(tr);
  });
}

function initExamples() {
  const host = $("examples");
  EXAMPLES.forEach((text) => {
    const chip = el("button", { class: "chip", type: "button" },
      text.length > 78 ? text.slice(0, 76) + "…" : text);
    chip.title = text;
    chip.addEventListener("click", () => { $("prompt").value = text; $("prompt").focus(); });
    host.appendChild(chip);
  });
}

$("themeToggle").addEventListener("click", () => {
  const root = document.documentElement;
  const dark = root.dataset.theme
    ? root.dataset.theme === "dark"
    : window.matchMedia("(prefers-color-scheme: dark)").matches;
  root.dataset.theme = dark ? "light" : "dark";
  if (state.run) { renderHeat(state.run); renderTimelines(state.run); }
});

$("launch").addEventListener("click", launch);
$("prompt").addEventListener("keydown", (e) => {
  if ((e.metaKey || e.ctrlKey) && e.key === "Enter") launch();
});

initExamples();
loadCapabilities();
