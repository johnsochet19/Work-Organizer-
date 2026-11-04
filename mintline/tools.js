/* Mintline tools: Mentor (advisor.py), Bitcoin data (onchain.py), Backtest and paper bot (bot.py). */
(() => {
  'use strict';
  const M = window.Mintline, E = window.MintEngine, TA = window.MintTA;
  const { state, esc, fmtUsd, fmtPct, fmtNum, fmtBig, signed, toast } = M;
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const DAY = M.DAY;
  const DEFAULT_PROFILE = { emergencyFund: true, highInterestDebt: false, weeklyUsd: 50, maxTotalUsd: 5000, years: 4, risk: 'medium', _default: true };

  // ---------------------------------------------------------------- small line chart
  /** series: [{pts: [[t, v]], color, label, dash, width}] */
  function drawLines(el, series, { height = 140, yFmt = (v) => fmtBig(v), refs = [], xDays = true } = {}) {
    const all = series.flatMap((s) => s.pts.filter((p) => p[1] != null && isFinite(p[1])));
    if (all.length < 2) { el.innerHTML = '<p class="muted small">Not enough data to draw.</p>'; return; }
    const W = Math.max(el.clientWidth || 320, 240), H = height, padL = 6, padR = 58, padT = 8, padB = 20;
    const xs = all.map((p) => p[0]);
    let y0 = Math.min(...all.map((p) => p[1]), ...refs.map((r) => r.y)), y1 = Math.max(...all.map((p) => p[1]), ...refs.map((r) => r.y));
    const pad = (y1 - y0) * 0.08 || Math.abs(y1) * 0.05 || 1; y0 -= pad; y1 += pad;
    const x0 = Math.min(...xs), x1 = Math.max(...xs);
    const X = (x) => padL + ((x - x0) / (x1 - x0 || 1)) * (W - padL - padR);
    const Y = (y) => padT + (1 - (y - y0) / (y1 - y0)) * (H - padT - padB);
    let svg = '';
    for (let i = 0; i <= 3; i++) {
      const v = y0 + ((y1 - y0) * i) / 3, y = Y(v);
      svg += `<line x1="${padL}" x2="${W - padR}" y1="${y}" y2="${y}" stroke="var(--line)" stroke-dasharray="2 4"/><text x="${W - padR + 5}" y="${y + 4}" fill="var(--muted)" font-size="10">${esc(yFmt(v))}</text>`;
    }
    for (const r of refs) svg += `<line x1="${padL}" x2="${W - padR}" y1="${Y(r.y)}" y2="${Y(r.y)}" stroke="var(--muted)" stroke-dasharray="4 3" opacity=".7"/>${r.label ? `<text x="${padL + 4}" y="${Y(r.y) - 3}" fill="var(--muted)" font-size="10">${esc(r.label)}</text>` : ''}`;
    for (const s of series) {
      let d = '', pen = false;
      for (const [t, v] of s.pts) {
        if (v == null || !isFinite(v)) { pen = false; continue; }
        d += `${pen ? 'L' : 'M'}${X(t).toFixed(1)},${Y(v).toFixed(1)}`; pen = true;
      }
      svg += `<path d="${d}" fill="none" stroke="${s.color}" stroke-width="${s.width || 1.6}" ${s.dash ? `stroke-dasharray="${s.dash}"` : ''}/>`;
    }
    const fx = (t) => new Date(t).toLocaleDateString([], xDays && x1 - x0 > 200 * DAY ? { month: 'short', year: '2-digit' } : { month: 'short', day: 'numeric' });
    svg += `<text x="${padL}" y="${H - 5}" fill="var(--muted)" font-size="10">${esc(fx(x0))}</text><text x="${W - padR}" y="${H - 5}" fill="var(--muted)" font-size="10" text-anchor="end">${esc(fx(x1))}</text>`;
    const legend = series.filter((s) => s.label).map((s) => `<span><i style="background:${s.color}"></i>${esc(s.label)}</span>`).join('');
    el.innerHTML = `${legend ? `<div class="chart-legend">${legend}</div>` : ''}<svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" class="mini-chart" role="img">${svg}</svg>`;
  }

  // ======================================================================== Mentor
  const LABEL_CLASS = { 'ON SALE': 'up', 'CHEAPER THAN USUAL': 'up', NORMAL: '', PRICEY: 'warn', OVERHEATED: 'down' };
  let mentorData = null; // {signals, notes, demo}

  async function mentorSignals() {
    const notes = [];
    const pts = TA.resample(await M.priceHistory('bitcoin', 365, 'usd'), DAY);
    const closes = pts.map((p) => p[1]);
    const btc = state.coinMap.get('bitcoin');
    const ath = btc?.ath ? M.convert(btc.ath, state.currency, 'usd') ?? Math.max(...closes) : Math.max(...closes);
    let fg = 50;
    try { fg = (await M.fearGreed(1)).at(-1).value; } catch { notes.push("Couldn't load Fear & Greed, so it's treated as neutral (50)."); }
    let funding = 0;
    try {
      const row = (await M.krakenFutures()).find((x) => x.symbol === 'PF_XBTUSD');
      funding = row.relativeFundingRate * 24 * 365 * 100;
    } catch { notes.push("Couldn't load futures funding from Kraken, so it's treated as 0."); }
    return { signals: E.readSignals({ closes, ath, fearGreed: fg, fundingApr: funding }), notes, demo: state.mode === 'demo' };
  }

  function briefingText(p, plan) {
    const lines = [`YOUR CRYPTO BRIEFING · ${new Date().toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' })}`];
    if (plan.blocked === 'debt') return [...lines, "WHAT TO DO THIS WEEK: Don't buy crypto. Put that money toward your high-interest debt."].join('\n');
    if (plan.blocked === 'emergency') return [...lines, 'WHAT TO DO THIS WEEK: Build your emergency fund first (3-6 months of expenses in savings).'].join('\n');
    lines.push(`MARKET RIGHT NOW: ${plan.label}`, plan.why, '');
    if (plan.room <= 0) lines.push(`Buy nothing new. You've reached your $${fmtNum(p.maxTotalUsd, 0)} limit.`);
    else if (!plan.amount) lines.push('Buy nothing this week. Keep your usual amount in savings.');
    else lines.push(`Buy ${fmtUsd(plan.amount)} in total: ${plan.buys.map((b) => `${fmtUsd(b.usd)} of ${b.symbol}`).join(', ')}.`);
    lines.push('', ...plan.signals.map((s) => `• ${s.signal}: ${s.value} → ${s.reading} [${s.arrow}]`), `Overall score ${plan.score >= 0 ? '+' : ''}${plan.score.toFixed(2)}`, '', 'Not financial advice.');
    return lines.join('\n');
  }

  async function renderMentor(force = false) {
    const box = $('#mentor-briefing');
    const p = state.profile || DEFAULT_PROFILE;
    fillProfileForm(p);
    if (p.highInterestDebt || !p.emergencyFund) { drawBriefing(p, E.plan(p, [], null)); return; }
    if (state.mode === 'loading') { box.innerHTML = '<p class="empty">Waiting for prices…</p>'; return; }
    if (!mentorData || force) {
      box.innerHTML = '<p class="empty">Reading the market…</p>';
      try { mentorData = await mentorSignals(); } catch (err) {
        box.innerHTML = `<p class="empty">Couldn't load Bitcoin's price history: ${esc(err.message)}</p>`; return;
      }
    }
    drawBriefing(p, E.plan(p, mentorData.signals, M.portfolioUsd()));
  }

  function drawBriefing(p, plan) {
    const box = $('#mentor-briefing');
    const date = new Date().toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
    let html = `<div class="brief-head"><h2>Your crypto briefing</h2><span class="muted small">${esc(date)}</span></div>`;
    if (p._default) html += '<p class="banner">These are starter settings. Fill in "About you" so the advice fits your situation.</p>';
    if (plan.blocked === 'debt') {
      html += `<div class="verdict down"><div class="label">What to do this week</div><div class="big">Don't buy crypto</div></div>
        <p>Put that money toward your high-interest debt. Paying off a credit card that charges 20% or more is a guaranteed 20%+ return, and no investment reliably beats that. Come back once it's paid off.</p>`;
      box.innerHTML = html; return;
    }
    if (plan.blocked === 'emergency') {
      html += `<div class="verdict warn"><div class="label">What to do this week</div><div class="big">Build your emergency fund first</div></div>
        <p>Save 3–6 months of expenses first. Without a cushion, a surprise bill could force you to sell crypto at a bad time. If you still want to start, keep it to a token amount, like $10 a week.</p>`;
      box.innerHTML = html; return;
    }
    if (mentorData?.demo) html += '<p class="banner warn">Live data isn\'t available, so this briefing uses sample prices. Don\'t act on it.</p>';
    html += `<div class="verdict ${LABEL_CLASS[plan.label] || ''}"><div class="label">Market right now</div><div class="big">${esc(plan.label)}</div><p>${esc(plan.why)}</p></div>`;
    html += '<h3>What to do this week</h3>';
    if (plan.room <= 0) html += `<p><b>Nothing new.</b> You've reached the ${fmtUsd(p.maxTotalUsd, { min: 0 })} total you said you'd put in. That limit protects you. Raise it only if your finances have really changed.</p>`;
    else if (!plan.amount) html += '<p><b>Buy nothing this week.</b> Keep your usual amount in savings. It\'ll be used when prices cool off.</p>';
    else {
      html += `<p class="buy-line">Buy <b>${fmtUsd(plan.amount)}</b> in total</p><ul class="buys">${plan.buys.map((b) => `<li><span class="coin-sym">${esc(b.symbol)}</span><b>${fmtUsd(b.usd)}</b></li>`).join('')}</ul>`;
      if (plan.mult > 1) html += `<p class="small">That's more than your usual ${fmtUsd(p.weeklyUsd, { min: 0 })} because prices are lower than normal.</p>`;
      else if (plan.mult < 1) html += `<p class="small">That's less than your usual ${fmtUsd(p.weeklyUsd, { min: 0 })} because prices are stretched.</p>`;
      html += '<p class="small muted">Use a regular exchange like Coinbase or Kraken. Choose a plain "buy", not futures or leverage.</p>';
    }
    html += '<h3>Why: what the data says</h3><ul class="signals">';
    for (const s of plan.signals) {
      const cls = s.score < 0 ? 'up' : s.score > 0 ? 'down' : '';
      html += `<li><div><div class="sig-name">${esc(s.signal)}</div><div class="small muted">${esc(s.reading)}</div></div><div class="sig-val"><b>${esc(s.value)}</b><span class="chip ${cls}">${esc(s.arrow)}</span></div></li>`;
    }
    const pos = ((plan.score + 2) / 4) * 100;
    html += `</ul><div class="gauge" aria-label="Overall score ${plan.score}"><div class="gauge-bar"><span style="left:${Math.min(100, Math.max(0, pos))}%"></span></div><div class="gauge-labels small muted"><span>−2 very cheap</span><b>${plan.score >= 0 ? '+' : ''}${plan.score.toFixed(2)}</b><span>+2 very expensive</span></div></div>`;
    if (mentorData?.notes?.length) html += `<p class="small muted">${mentorData.notes.map(esc).join(' ')}</p>`;
    if (plan.portfolio) {
      const pf = plan.portfolio;
      html += `<h3>Your portfolio</h3><p>Put in <b>${fmtUsd(pf.invested)}</b> · worth <b>${fmtUsd(pf.value)}</b> · ${pf.pnl >= 0 ? 'up' : 'down'} <b class="${pf.pnl >= 0 ? 'up' : 'down'}">${fmtUsd(Math.abs(pf.pnl))}</b> (${fmtPct(pf.pnlPct, 1)})</p>`;
      html += `<ul class="plan-rows">${pf.rows.map((r) => `<li><span class="coin-sym">${esc(r.symbol)}</span> ${r.allocationPct.toFixed(0)}% of portfolio <span class="muted">(plan ${r.planPct.toFixed(0)}%)</span></li>`).join('')}</ul>`;
      if (pf.takeProfit) html += '<p class="banner warn">You\'ve more than doubled your money and the market is overheated. Consider selling 10–20% to lock in some profit. Taxes apply to the gain, so check the tax section on the Portfolio tab.</p>';
      if (pf.dontSell) html += '<p class="banner">Being down is normal in crypto, and it\'s exactly when steady buying pays off. Don\'t sell.</p>';
    }
    html += `<h3>Watch out for</h3><ul class="watch">
      <li>Anyone promising guaranteed returns, "signals" groups, or DMs offering help. These are scams.</li>
      <li>Coins that are suddenly everywhere on social media. By the time you hear about them, insiders are selling.</li>
      <li>Leverage, futures, or "earn 20% APY" offers. These are how beginners lose everything.</li>
      <li>Crypto can fall 50–80% and take years to recover. Only use money you can leave alone for ${fmtNum(p.years, 0)}+ years.</li></ul>
      <div class="row-gap"><button class="btn ghost" id="mentor-send">Send to my phone</button><button class="btn ghost" id="mentor-refresh">Refresh data</button></div>
      <p class="hint">Not financial advice. This is a rules-based plan using public data, and it can't predict prices.</p>`;
    box.innerHTML = html;
    $('#mentor-send').onclick = () => {
      if (!state.settings.ntfyTopic && !state.settings.webhook) { toast('Add an ntfy topic or webhook in Settings first', 'warn'); return; }
      M.notifyAll('Your weekly crypto briefing', briefingText(p, plan));
    };
    $('#mentor-refresh').onclick = () => renderMentor(true);
  }

  function fillProfileForm(p) {
    const f = $('#profile-form');
    if (f.dataset.filled) return;
    f.emergencyFund.checked = !!p.emergencyFund;
    f.highInterestDebt.checked = !!p.highInterestDebt;
    f.weeklyUsd.value = p.weeklyUsd;
    f.maxTotalUsd.value = p.maxTotalUsd;
    f.years.value = p.years;
    f.risk.value = p.risk;
    f.dataset.filled = '1';
  }

  $('#profile-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const f = e.target;
    state.profile = { emergencyFund: f.emergencyFund.checked, highInterestDebt: f.highInterestDebt.checked,
      weeklyUsd: +f.weeklyUsd.value || 0, maxTotalUsd: +f.maxTotalUsd.value || 0, years: +f.years.value || 0,
      risk: E.MIXES[f.risk.value] ? f.risk.value : 'medium' };
    M.persist();
    toast('Saved');
    renderMentor();
  });

  $('#mentor-backtest').addEventListener('click', async () => {
    const el = $('#mentor-bt');
    el.innerHTML = '<p class="muted small">Running…</p>';
    try {
      const { bars, source } = await M.dailyBars('bitcoin');
      if (bars.length < 210) throw new Error('needs more than 200 days of history');
      let fg = {};
      try { for (const d of await M.fearGreed(0)) fg[M.isoDay(d.time)] = d.value; } catch { fg = {}; }
      const weekly = (state.profile || DEFAULT_PROFILE).weeklyUsd || 50;
      const r = E.advisorBacktest(bars, fg, weekly);
      const row = (label, x) => `<tr><td>${label}</td><td class="r">${fmtUsd(x.spent)}</td><td class="r">${fmtUsd(x.worthNow)}</td><td class="r">${fmtUsd(x.avgPricePaid)}</td><td class="r">${fmtPct(x.returnPct, 1)}</td></tr>`;
      el.innerHTML = `<p class="small muted">${M.isoDay(r.from)} to ${M.isoDay(r.to)} · ${r.weeks} weeks · ${fmtUsd(weekly, { min: 0 })} a week · ${esc(source)}${Object.keys(fg).length ? '' : ' · Fear & Greed history unavailable, treated as neutral'}</p>
        <div class="table-wrap"><table class="holdings compact-table"><thead><tr><th></th><th class="r">Spent</th><th class="r">Worth now</th><th class="r">Avg price</th><th class="r">Return</th></tr></thead>
        <tbody>${row('Plain weekly buying', r.plain)}${row('Mentor rules', r.advisor)}</tbody></table></div>
        <p class="hint">Past results don't predict future returns.</p>`;
    } catch (err) { el.innerHTML = `<p class="muted small">Couldn't run the backtest: ${esc(err.message)}</p>`; }
  });

  M.onTab('mentor', () => renderMentor());

  // =================================================================== Bitcoin data
  let onchainLoaded = false;
  const MEMPOOL = 'https://mempool.space/api';
  const BCI = 'https://api.blockchain.info/charts';

  function section(el, fn) {
    el.innerHTML = '<p class="muted small">Loading…</p>';
    return fn().catch((err) => {
      el.innerHTML = `<p class="muted small">Couldn't load this: ${esc(err.message === 'Failed to fetch' ? 'the source blocked the request or is offline' : err.message)}. ${state.mode === 'demo' ? 'Live data is needed.' : 'The Chrome extension version can reach more sources.'}</p>`;
    });
  }

  async function loadNetwork() {
    const el = $('#oc-network');
    await section(el, async () => {
      const get = (p) => M.getJSON(MEMPOOL + p, { retries: 1 });
      const fees = await get('/v1/fees/recommended');
      const mp = await get('/mempool');
      const diff = await get('/v1/difficulty-adjustment');
      const hr = await get('/v1/mining/hashrate/3d');
      const height = await get('/blocks/tip/height');
      const stat = (l, v, sub = '') => `<div><div class="label">${l}</div><div class="val">${v}</div>${sub ? `<div class="small muted">${sub}</div>` : ''}</div>`;
      el.innerHTML = [
        stat('Block height', fmtNum(+height, 0)),
        stat('Fee, next block', `${fees.fastestFee} sat/vB`, `30 min ${fees.halfHourFee} · 1 h ${fees.hourFee} · low ${fees.economyFee}`),
        stat('Waiting transactions', fmtNum(mp.count, 0), `${(mp.vsize / 1e6).toFixed(2)} MB`),
        stat('Hash rate (3 days)', `${(hr.currentHashrate / 1e18).toFixed(1)} EH/s`),
        stat('Next difficulty change', `${diff.difficultyChange >= 0 ? '+' : ''}${diff.difficultyChange.toFixed(2)}%`, `in ${fmtNum(diff.remainingBlocks, 0)} blocks`),
      ].join('');
    });
  }

  async function loadFng() {
    const el = $('#oc-fng');
    await section(el, async () => {
      const d = await M.fearGreed(30);
      const now = d.at(-1);
      const cls = now.value < 25 ? 'down' : now.value > 75 ? 'up' : '';
      el.innerHTML = `<div class="fng-now"><span class="big ${cls}">${now.value}</span><span>${esc(now.label)}</span></div><div class="fng-chart"></div>`;
      drawLines($('.fng-chart', el), [{ pts: d.map((x) => [x.time, x.value]), color: 'var(--ind-3)' }], { height: 110, yFmt: (v) => v.toFixed(0), refs: [{ y: 20, label: 'extreme fear' }, { y: 80, label: 'extreme greed' }] });
    });
  }

  function rollingMean(arr, n, minPeriods = n) {
    const out = new Array(arr.length).fill(null);
    for (let i = 0; i < arr.length; i++) {
      let s = 0, c = 0;
      for (let j = Math.max(0, i - n + 1); j <= i; j++) if (arr[j] != null) { s += arr[j]; c++; }
      if (c >= minPeriods) out[i] = s / c;
    }
    return out;
  }

  async function loadValuation() {
    const el = $('#oc-valuation');
    await section(el, async () => {
      const slugs = { price: 'market-price', mcap: 'market-cap', vol: 'estimated-transaction-volume-usd', rev: 'miners-revenue', hr: 'hash-rate' };
      const series = {};
      for (const [k, slug] of Object.entries(slugs)) {
        const d = await M.cached(`bci:${slug}`, 3 * 3600e3, () => M.getJSON(`${BCI}/${slug}?timespan=2years&format=json&sampled=false&cors=true`, { retries: 1 }));
        series[k] = new Map(d.values.map((v) => [Math.floor((v.x * 1000) / DAY), v.y]));
      }
      // Daily rows from the first to the last day, forward-filled (like pandas resample("1D").last().ffill()).
      const days = [...new Set(Object.values(series).flatMap((m) => [...m.keys()]))].sort((a, b) => a - b);
      const rows = [];
      const lastSeen = {};
      for (let d = days[0]; d <= days[days.length - 1]; d++) {
        for (const k of Object.keys(series)) if (series[k].has(d)) lastSeen[k] = series[k].get(d);
        rows.push({ t: d * DAY, ...lastSeen });
      }
      const col = (k) => rows.map((r) => r[k] ?? null);
      const price = col('price'), mcap = col('mcap'), vol = col('vol'), rev = col('rev'), hrs = col('hr');
      const s200 = rollingMean(price, 200), v90 = rollingMean(vol, 90), r365 = rollingMean(rev, 365, 180);
      const h30 = rollingMean(hrs, 30), h60 = rollingMean(hrs, 60);
      const mayer = price.map((p, i) => (p != null && s200[i] ? p / s200[i] : null));
      const nvt = mcap.map((m, i) => (m != null && v90[i] ? m / v90[i] : null));
      const puell = rev.map((r, i) => (r != null && r365[i] ? r / r365[i] : null));
      const L = rows.length - 1;
      const capit = h30[L] != null && h60[L] != null && h30[L] < h60[L];
      const reading = (v, bands) => bands.find(([u]) => v < u)?.[1] || bands.at(-1)[1];
      el.innerHTML = `
        <div class="metric"><div class="label">Mayer Multiple</div><div class="val">${mayer[L]?.toFixed(2) ?? '—'}</div><div class="small muted">${mayer[L] != null ? reading(mayer[L], [[0.8, 'historically very cheap'], [1, 'cheaper than usual'], [1.5, 'fair'], [2.4, 'getting expensive'], [99, 'overheated']]) : ''}</div><div class="m-chart" data-k="mayer"></div></div>
        <div class="metric"><div class="label">NVT ratio</div><div class="val">${nvt[L] != null ? nvt[L].toFixed(1) : '—'}</div><div class="small muted">High means price is outpacing on-chain use</div><div class="m-chart" data-k="nvt"></div></div>
        <div class="metric"><div class="label">Puell Multiple</div><div class="val">${puell[L]?.toFixed(2) ?? '—'}</div><div class="small muted">Miner revenue vs its yearly average</div><div class="m-chart" data-k="puell"></div></div>
        <div class="metric"><div class="label">Hash ribbon</div><div class="val ${capit ? 'down' : 'up'}">${capit ? 'Capitulation' : 'Healthy'}</div><div class="small muted">30-day vs 60-day hash rate average</div><div class="m-chart" data-k="hash"></div></div>`;
      const pts = (arr) => rows.map((r, i) => [r.t, arr[i]]);
      drawLines($('[data-k="mayer"]', el), [{ pts: pts(mayer), color: 'var(--ind-1)' }], { height: 90, yFmt: (v) => v.toFixed(2), refs: [{ y: 1 }, { y: 2.4 }] });
      drawLines($('[data-k="nvt"]', el), [{ pts: pts(nvt), color: 'var(--ind-2)' }], { height: 90, yFmt: (v) => v.toFixed(0) });
      drawLines($('[data-k="puell"]', el), [{ pts: pts(puell), color: 'var(--ind-3)' }], { height: 90, yFmt: (v) => v.toFixed(2), refs: [{ y: 1 }] });
      drawLines($('[data-k="hash"]', el), [{ pts: pts(h30), color: 'var(--ind-1)', label: '30-day' }, { pts: pts(h60), color: 'var(--ind-4)', label: '60-day' }], { height: 90, yFmt: (v) => `${(v / 1e6).toFixed(0)}M` });
    });
  }

  async function loadDerivatives() {
    const body = $('#oc-deriv');
    body.innerHTML = '<tr><td colspan="8" class="muted small">Loading…</td></tr>';
    try {
      const t = (await M.krakenFutures()).filter((x) => ['PF_XBTUSD', 'PF_ETHUSD', 'PF_SOLUSD'].includes(x.symbol));
      if (!t.length) throw new Error('no perpetual contracts returned');
      body.innerHTML = t.map((x) => {
        const apr = x.relativeFundingRate * 24 * 365 * 100;
        return `<tr><td>${esc(x.symbol)}</td><td class="r">${fmtUsd(x.markPrice)}</td><td class="r hide-sm">${fmtUsd(x.indexPrice)}</td>
          <td class="r">${((x.markPrice / x.indexPrice - 1) * 100).toFixed(3)}%</td><td class="r hide-sm">${(x.relativeFundingRate * 100).toFixed(4)}%</td>
          <td class="r ${apr > 30 ? 'down' : apr < -5 ? 'up' : ''}">${apr.toFixed(1)}%</td><td class="r">${fmtBig(x.openInterest * x.markPrice)} USD</td><td class="r hide-md">${fmtBig(x.vol24h)}</td></tr>`;
      }).join('');
    } catch (err) {
      body.innerHTML = `<tr><td colspan="8" class="muted small">Couldn't load Kraken Futures: ${esc(err.message === 'Failed to fetch' ? 'the request was blocked or the service is offline' : err.message)}.</td></tr>`;
    }
  }

  function loadOnchain() {
    onchainLoaded = true;
    loadNetwork(); loadFng(); loadValuation(); loadDerivatives();
  }
  M.onTab('bitcoin', () => { if (!onchainLoaded) loadOnchain(); });
  $('#reload-onchain').addEventListener('click', loadOnchain);

  // ======================================================================= Backtest
  const btForm = $('#bt-form');
  let btReady = false;
  function initBacktest() {
    if (!btReady) {
      M.fillCoinSelect(btForm.coin, 'bitcoin');
      M.fillCoinSelect($('#bot-form').coin, state.paperBot?.coinId || 'bitcoin');
      btReady = true;
    }
    renderBot();
  }
  btForm.strategy.addEventListener('change', () => $$('.bt-params', btForm).forEach((el) => { el.hidden = el.dataset.for !== btForm.strategy.value; }));

  btForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const out = $('#bt-result');
    out.innerHTML = '<p class="empty">Loading price history…</p>';
    const f = btForm;
    const fee = Math.max(0, +f.fee.value || 0) / 100;
    try {
      const coinId = f.coin.value;
      const { bars, source, closeOnly } = await M.dailyBars(coinId);
      if (bars.length < 30) throw new Error('not enough price history');
      let rep;
      if (f.strategy.value === 'dca') rep = E.backtestDca(bars, { amount: +f.amount.value || 100, every: Math.max(1, parseInt(f.every.value, 10) || 7), dipPct: +f.dip.value || 0, fee });
      else if (f.strategy.value === 'grid') {
        const low = +f.low.value || Math.min(...bars.map((b) => b.low)), high = +f.high.value || Math.max(...bars.map((b) => b.high));
        if (!(high > low)) throw new Error('the highest price must be above the lowest');
        rep = E.backtestGrid(bars, { low, high, levels: Math.max(2, parseInt(f.levels.value, 10) || 20), capital: +f.capital.value || 5000, fee });
      } else {
        const fast = parseInt(f.fast.value, 10) || 50, slow = parseInt(f.slow.value, 10) || 200;
        if (fast >= slow) throw new Error('the fast average must be shorter than the slow one');
        if (bars.length <= slow) throw new Error(`needs more than ${slow} days of history (have ${bars.length})`);
        rep = E.backtestSma(bars, { fast, slow, capital: +f.smacap.value || 10000, fee });
      }
      drawBacktest(rep, bars, { coinId, source, closeOnly, strategy: f.strategy.value });
    } catch (err) { out.innerHTML = `<p class="empty">Couldn't run the backtest: ${esc(err.message)}</p>`; }
  });

  function drawBacktest(rep, bars, { coinId, source, closeOnly, strategy }) {
    const out = $('#bt-result');
    const stat = (l, v) => `<div><div class="label">${l}</div><div class="val">${v}</div></div>`;
    const stats = [
      stat('Final value', fmtUsd(rep.finalEquity)),
      stat('Return on starting cash', fmtPct(rep.returnPct)),
      stat('Worst drop (max drawdown)', fmtPct(rep.maxDrawdownPct)),
      stat('Trades', fmtNum(rep.trades, 0)),
      stat('Total bought', fmtUsd(rep.totalBuyVolume)),
      stat(`Ending ${M.symbolOf(coinId)} / cash`, `${fmtNum(rep.endQty, 6)} / ${fmtUsd(rep.endCash)}`),
    ];
    if (rep.returnOnInvestedPct != null) stats.splice(2, 0, stat('Return on money invested', fmtPct(rep.returnOnInvestedPct)));
    if (rep.buyAndHoldPct != null) stats.splice(2, 0, stat('Buy and hold instead', fmtPct(rep.buyAndHoldPct)));
    const t0 = bars[0].time, t1 = bars[bars.length - 1].time;
    out.innerHTML = `<div class="card-head"><h2>${esc(rep.strategy)}</h2><span class="muted small">${M.isoDay(t0)} to ${M.isoDay(t1)} · ${bars.length} days</span></div>
      <div class="stats">${stats.join('')}</div><div id="bt-chart"></div>
      <p class="hint">Data: ${esc(source)}.${closeOnly && strategy !== 'sma' ? ' Without intraday highs and lows, grid fills and dip buys are only checked against closing prices.' : ''} Trading fees are included. Past results don't predict future returns.</p>
      ${rep.fills.length ? `<details class="more"><summary>Trades (${rep.fills.length})</summary><div class="table-wrap"><table class="holdings compact-table"><thead><tr><th>Date</th><th>Side</th><th class="r">Price</th><th class="r">Quantity</th><th class="r">USD</th></tr></thead><tbody>${rep.fills.slice(-200).reverse().map((x) => `<tr><td>${M.isoDay(x.time)}</td><td>${x.side}</td><td class="r">${fmtUsd(x.price)}</td><td class="r">${fmtNum(x.qty, 8)}</td><td class="r">${fmtUsd(x.usd)}</td></tr>`).join('')}</tbody></table></div></details>` : ''}`;
    const eq = bars.map((b, i) => [b.time, rep.curve[i]]);
    const hold = bars.map((b) => [b.time, rep.startCash * (b.close / bars[0].close)]);
    const series = [{ pts: eq, color: 'var(--mint)', label: 'Strategy value', width: 2 }];
    if (strategy !== 'dca') series.push({ pts: hold, color: 'var(--muted)', label: 'Buy and hold', dash: '4 3' });
    else {
      let spent = 0; const fills = [...rep.fills]; let k = 0;
      series.push({ pts: bars.map((b) => { while (k < fills.length && fills[k].time <= b.time) spent += fills[k++].usd; return [b.time, spent]; }), color: 'var(--muted)', label: 'Money put in', dash: '4 3' });
    }
    drawLines($('#bt-chart'), series, { height: 200, yFmt: (v) => fmtUsd(v, { compact: true }) });
  }

  // ===================================================================== Paper bot
  const botForm = $('#bot-form');
  botForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const amount = +botForm.amount.value, hours = +botForm.hours.value;
    if (!(amount > 0) || !(hours > 0)) return;
    const prev = state.paperBot;
    const same = prev && prev.coinId === botForm.coin.value;
    state.paperBot = { coinId: botForm.coin.value, amount, hours, enabled: true,
      cash: same ? prev.cash : 10000, qty: same ? prev.qty : 0, trades: same ? prev.trades : [], lastBuy: same ? prev.lastBuy : 0, startedAt: same ? prev.startedAt : Date.now() };
    M.persist();
    toast(`Paper bot started: ${fmtUsd(amount)} of ${M.symbolOf(state.paperBot.coinId)} every ${hours} h`);
    runBot();
    renderBot();
  });
  $('#bot-stop').addEventListener('click', () => { if (state.paperBot) { state.paperBot.enabled = false; M.persist(); renderBot(); } });
  $('#bot-reset').addEventListener('click', () => {
    const prev = state.paperBot;
    state.paperBot = null; M.persist(); renderBot();
    if (prev) toast('Paper bot reset', '', { label: 'Undo', run: () => { state.paperBot = prev; M.persist(); renderBot(); } });
  });

  function runBot() {
    const b = state.paperBot;
    if (!b?.enabled || state.mode !== 'live') return;
    if (Date.now() - (b.lastBuy || 0) < b.hours * 3600e3) return;
    const c = state.coinMap.get(b.coinId);
    const px = c && M.convert(c.current_price, state.currency, 'usd');
    if (!px) return;
    const usd = Math.min(b.amount, b.cash);
    if (usd <= 0) { b.enabled = false; M.persist(); toast('Paper bot stopped: the pretend balance is used up', 'warn'); renderBot(); return; }
    const q = (usd * (1 - E.FEE)) / px;
    b.cash -= usd; b.qty += q; b.lastBuy = Date.now();
    b.trades.push({ time: b.lastBuy, price: px, qty: q, usd });
    M.persist();
    toast(`[PAPER] bought ${fmtUsd(usd)} of ${M.symbolOf(b.coinId)} at ${fmtUsd(px)}`);
    renderBot();
  }

  function renderBot() {
    const b = state.paperBot, view = $('#bot-view'), pill = $('#bot-status');
    if (!b) { pill.textContent = 'Off'; pill.className = 'pill'; view.innerHTML = ''; return; }
    if (btReady) { botForm.coin.value = b.coinId; botForm.amount.value = b.amount; botForm.hours.value = b.hours; }
    pill.textContent = b.enabled ? (state.mode === 'live' ? 'Running' : 'Waiting for live prices') : 'Stopped';
    pill.className = `pill ${b.enabled ? 'on' : ''}`;
    const c = state.coinMap.get(b.coinId);
    const px = c ? M.convert(c.current_price, state.currency, 'usd') : null;
    const equity = b.cash + (px ? b.qty * px : 0);
    const spent = b.trades.reduce((s, t) => s + t.usd, 0);
    const next = b.lastBuy ? b.lastBuy + b.hours * 3600e3 : Date.now();
    const stat = (l, v) => `<div><div class="label">${l}</div><div class="val">${v}</div></div>`;
    view.innerHTML = `<div class="stats">${[
      stat('Pretend balance left', fmtUsd(b.cash)),
      stat(`${M.symbolOf(b.coinId)} held`, fmtNum(b.qty, 8)),
      stat('Total value', fmtUsd(equity)),
      stat('Profit / loss on buys', px && spent ? signed(b.qty * px - spent, fmtUsd) : '—'),
      stat('Buys so far', b.trades.length),
      stat('Next buy', b.enabled ? new Date(next).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : '—'),
    ].join('')}</div>
    ${b.trades.length ? `<details class="more"><summary>Paper trades</summary><div class="table-wrap"><table class="holdings compact-table"><thead><tr><th>Time</th><th class="r">Price</th><th class="r">Quantity</th><th class="r">USD</th></tr></thead><tbody>${b.trades.slice().reverse().map((t) => `<tr><td>${new Date(t.time).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}</td><td class="r">${fmtUsd(t.price)}</td><td class="r">${fmtNum(t.qty, 8)}</td><td class="r">${fmtUsd(t.usd)}</td></tr>`).join('')}</tbody></table></div></details>` : ''}`;
  }

  M.onTab('backtest', initBacktest);
  M.onRefresh(() => {
    runBot();
    if (state.tab === 'backtest') renderBot();
    if (state.tab === 'mentor') renderMentor(!mentorData || mentorData.demo !== (state.mode === 'demo'));
  });

  window.MintlineTools = { drawLines, renderMentor, loadOnchain, runBot };
})();
