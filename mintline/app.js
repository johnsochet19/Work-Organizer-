/* Mintline — Crypto Tracker
 * Live prices, price alerts and portfolio tracking.
 * Data from the public CoinGecko API; falls back to cached data, then demo data.
 */
(() => {
  'use strict';

  const API = 'https://api.coingecko.com/api/v3';
  const REFRESH_MS = 60_000;
  const STORE_KEY = 'mintline:v1';
  const CACHE_KEY = 'mintline:cache:v1';

  // ---------- State ----------
  const defaults = {
    currency: 'usd',
    sort: 'rank',
    watchlist: ['bitcoin', 'ethereum'],
    txs: [],     // {id, coinId, type:'buy'|'sell', amount, price, cur, ts}
    alerts: [],  // {id, coinId, dir:'above'|'below', price, cur, createdAt, triggeredAt, lastPrice}
  };
  const saved = load(STORE_KEY) || {};
  const state = {
    ...defaults,
    ...saved,
    coins: [],          // market rows
    coinMap: new Map(), // id -> row
    rates: null,        // exchange rates relative to BTC
    global: null,
    mode: 'loading',    // live | cached | demo | loading
    updatedAt: null,
    tab: 'markets',
    detail: { id: null, days: 7 },
  };

  function persist() {
    const { currency, sort, watchlist, txs, alerts } = state;
    save(STORE_KEY, { currency, sort, watchlist, txs, alerts });
  }
  function load(k) { try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } }
  function save(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* storage unavailable */ } }

  // ---------- Helpers ----------
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const uid = () => Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  function fmtMoney(v, cur = state.currency, opts = {}) {
    if (v == null || !isFinite(v)) return '—';
    const abs = Math.abs(v);
    if (cur === 'btc') {
      const d = abs >= 1 ? 4 : abs >= 0.0001 ? 6 : 8;
      return `₿${v.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d })}`;
    }
    let max = abs >= 1000 ? 2 : abs >= 1 ? 2 : abs >= 0.01 ? 4 : abs >= 0.0001 ? 6 : 8;
    if (cur === 'jpy' && abs >= 1) max = 0;
    try {
      return new Intl.NumberFormat(undefined, {
        style: 'currency', currency: cur.toUpperCase(),
        minimumFractionDigits: Math.min(opts.min ?? 2, max), maximumFractionDigits: max,
        ...(opts.compact ? { notation: 'compact', maximumFractionDigits: 2, minimumFractionDigits: 0 } : {}),
      }).format(v);
    } catch {
      return `${v.toFixed(max)} ${cur.toUpperCase()}`;
    }
  }
  const fmtCompact = (v) => fmtMoney(v, state.currency, { compact: true });
  function fmtPct(v) {
    if (v == null || !isFinite(v)) return '<span class="muted">—</span>';
    const cls = v >= 0 ? 'up' : 'down';
    const sign = v >= 0 ? '▲' : '▼';
    return `<span class="${cls}">${sign} ${Math.abs(v).toFixed(2)}%</span>`;
  }
  function fmtNum(v, max = 8) {
    if (v == null || !isFinite(v)) return '—';
    return v.toLocaleString(undefined, { maximumFractionDigits: max });
  }
  function coinIcon(c, size = 24) {
    if (c?.image) return `<img src="${esc(c.image)}" alt="" width="${size}" height="${size}" loading="lazy">`;
    return `<span class="coin-icon" style="width:${size}px;height:${size}px">${esc((c?.symbol || '?').slice(0, 3).toUpperCase())}</span>`;
  }

  /** Convert an amount between vs-currencies using BTC-relative rates. */
  function convert(amount, from, to) {
    if (from === to || amount == null) return amount;
    const r = state.rates;
    if (!r || !r[from] || !r[to]) return null;
    return amount * (r[to].value / r[from].value);
  }

  // ---------- Data ----------
  async function getJSON(url, timeoutMs = 12_000) {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), timeoutMs);
    try {
      const res = await fetch(url, { signal: ctrl.signal, headers: { accept: 'application/json' } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } finally {
      clearTimeout(t);
    }
  }

  function trackedIds() {
    return new Set([
      ...state.watchlist,
      ...state.txs.map((t) => t.coinId),
      ...state.alerts.map((a) => a.coinId),
    ]);
  }

  async function fetchLive() {
    const cur = state.currency;
    const q = `vs_currency=${cur}&sparkline=true&price_change_percentage=1h,24h,7d`;
    const top = await getJSON(`${API}/coins/markets?${q}&order=market_cap_desc&per_page=100&page=1`);
    const have = new Set(top.map((c) => c.id));
    const missing = [...trackedIds()].filter((id) => !have.has(id));
    let extra = [];
    if (missing.length) {
      try { extra = await getJSON(`${API}/coins/markets?${q}&ids=${missing.map(encodeURIComponent).join(',')}`); } catch { /* optional */ }
    }
    const [rates, global] = await Promise.all([
      getJSON(`${API}/exchange_rates`).then((r) => r.rates).catch(() => state.rates),
      getJSON(`${API}/global`).then((g) => g.data).catch(() => state.global),
    ]);
    return { coins: [...top, ...extra], rates, global };
  }

  async function refresh({ manual = false } = {}) {
    const btn = $('#refresh');
    btn.classList.add('spin');
    try {
      const data = await fetchLive();
      applyData(data, 'live');
      save(CACHE_KEY, { currency: state.currency, at: Date.now(), ...data });
      if (manual) toast('Prices updated');
    } catch (err) {
      const cache = load(CACHE_KEY);
      if (cache && cache.currency === state.currency && cache.coins?.length) {
        applyData(cache, 'cached', cache.at);
        if (manual) toast('Could not reach CoinGecko — showing cached prices', 'warn');
      } else if (state.mode !== 'live') {
        const wasDemo = state.mode === 'demo';
        applyData(Demo.data(state.currency), 'demo');
        if (manual || !wasDemo) toast('Live data unavailable — showing demo prices', 'warn');
      }
    } finally {
      btn.classList.remove('spin');
    }
  }

  function applyData({ coins, rates, global }, mode, at = Date.now()) {
    const prev = state.coinMap;
    state.coins = coins;
    state.coinMap = new Map(coins.map((c) => [c.id, c]));
    if (rates) state.rates = rates;
    if (global) state.global = global;
    state.mode = mode;
    state.updatedAt = at;
    renderAll(prev);
    checkAlerts();
  }

  // ---------- Demo data (used only when the API is unreachable) ----------
  const Demo = (() => {
    const seed = [
      ['bitcoin', 'Bitcoin', 'btc', 68000, 1.34e12],
      ['ethereum', 'Ethereum', 'eth', 3500, 4.2e11],
      ['tether', 'Tether', 'usdt', 1, 1.1e11],
      ['binancecoin', 'BNB', 'bnb', 590, 8.7e10],
      ['solana', 'Solana', 'sol', 165, 7.6e10],
      ['usd-coin', 'USDC', 'usdc', 1, 3.3e10],
      ['ripple', 'XRP', 'xrp', 0.55, 3.1e10],
      ['dogecoin', 'Dogecoin', 'doge', 0.15, 2.2e10],
      ['the-open-network', 'Toncoin', 'ton', 6.8, 1.7e10],
      ['cardano', 'Cardano', 'ada', 0.45, 1.6e10],
      ['avalanche-2', 'Avalanche', 'avax', 36, 1.4e10],
      ['shiba-inu', 'Shiba Inu', 'shib', 0.000024, 1.4e10],
      ['tron', 'TRON', 'trx', 0.12, 1.05e10],
      ['polkadot', 'Polkadot', 'dot', 7.1, 1.0e10],
      ['chainlink', 'Chainlink', 'link', 15.5, 9.1e9],
      ['bitcoin-cash', 'Bitcoin Cash', 'bch', 470, 9.2e9],
      ['near', 'NEAR Protocol', 'near', 6.9, 7.4e9],
      ['litecoin', 'Litecoin', 'ltc', 82, 6.1e9],
      ['uniswap', 'Uniswap', 'uni', 9.8, 5.9e9],
      ['polygon-ecosystem-token', 'POL', 'pol', 0.62, 5.0e9],
    ];
    const fx = { usd: 1, eur: 0.92, gbp: 0.79, cad: 1.37, aud: 1.51, jpy: 151, btc: 1 / 68000 };
    // Deterministic PRNG so demo charts are stable within a session.
    function rng(s) { return () => ((s = Math.imul(s ^ (s >>> 15), 1 | s) + 0x6d2b79f5 | 0), ((s >>> 0) % 1e6) / 1e6); }
    function walk(id, n, end, vol) {
      const r = rng([...id].reduce((a, ch) => a * 31 + ch.charCodeAt(0), 7) + Math.floor(Date.now() / 3.6e6));
      const pts = [end];
      for (let i = 1; i < n; i++) pts.push(pts[i - 1] * (1 + (r() - 0.5) * vol));
      return pts.reverse();
    }
    function data(cur) {
      const k = fx[cur] ?? 1;
      const jitter = () => 1 + (Math.random() - 0.5) * 0.004;
      const coins = seed.map(([id, name, symbol, usd, mcap], i) => {
        const stable = symbol === 'usdt' || symbol === 'usdc';
        const vol = stable ? 0.0005 : 0.008;
        const price = usd * k * (stable ? 1 : jitter());
        const spark = walk(id, 168, price, vol);
        const pct = (a, b) => ((b - a) / a) * 100;
        return {
          id, name, symbol, image: null,
          current_price: price,
          market_cap: mcap * k, market_cap_rank: i + 1,
          total_volume: mcap * k * 0.04,
          high_24h: Math.max(...spark.slice(-24)), low_24h: Math.min(...spark.slice(-24)),
          circulating_supply: mcap / usd, total_supply: null, max_supply: symbol === 'btc' ? 21e6 : null,
          ath: price * 1.4, ath_change_percentage: -28.6,
          price_change_percentage_1h_in_currency: pct(spark[166], spark[167]),
          price_change_percentage_24h_in_currency: pct(spark[143], spark[167]),
          price_change_percentage_7d_in_currency: pct(spark[0], spark[167]),
          sparkline_in_7d: { price: spark },
        };
      });
      const rates = Object.fromEntries(Object.entries(fx).map(([c, v]) => [c, { value: v / fx.btc }]));
      const total = coins.reduce((a, c) => a + c.market_cap, 0);
      const global = {
        total_market_cap: { [cur]: total / 0.82 },
        total_volume: { [cur]: total * 0.035 },
        market_cap_percentage: { btc: 54.1, eth: 17.2 },
        market_cap_change_percentage_24h_usd: 1.2,
        active_cryptocurrencies: 14000,
      };
      return { coins, rates, global };
    }
    function chart(coin, days) {
      const n = days <= 1 ? 288 : days <= 90 ? Math.min(days * 24, 720) : days;
      const vol = (coin.symbol === 'usdt' || coin.symbol === 'usdc') ? 0.0005 : 0.008;
      const pts = walk(coin.id + days, n, coin.current_price, vol);
      const step = (days * 864e5) / pts.length;
      const now = Date.now();
      return pts.map((p, i) => [now - (pts.length - 1 - i) * step, p]);
    }
    return { data, chart };
  })();

  // ---------- Rendering ----------
  function renderAll(prevMap) {
    renderStatus();
    renderGlobal();
    renderMarkets(prevMap);
    renderWatchlist(prevMap);
    renderPortfolio();
    renderAlerts();
    if ($('#detail').open && state.detail.id) renderDetailHeader();
  }

  function renderStatus() {
    const el = $('#status');
    const labels = { live: 'Live', cached: 'Cached', demo: 'Demo data', loading: 'Loading…' };
    el.className = `status ${state.mode === 'live' ? 'live' : state.mode === 'demo' ? 'demo' : state.mode === 'cached' ? 'offline' : ''}`;
    el.innerHTML = `<span>${labels[state.mode]}</span>`;
    $('#updated').textContent = state.updatedAt ? `Updated ${new Date(state.updatedAt).toLocaleTimeString()}` : '';
  }

  function renderGlobal() {
    const g = state.global;
    if (!g) { $('#global').innerHTML = ''; return; }
    const cur = state.currency;
    const chg = g.market_cap_change_percentage_24h_usd;
    $('#global').innerHTML = `
      <span>Market cap <b>${fmtCompact(g.total_market_cap?.[cur])}</b> ${fmtPct(chg)}</span>
      <span>24h volume <b>${fmtCompact(g.total_volume?.[cur])}</b></span>
      <span>BTC dominance <b>${(g.market_cap_percentage?.btc ?? 0).toFixed(1)}%</b></span>
      <span>ETH dominance <b>${(g.market_cap_percentage?.eth ?? 0).toFixed(1)}%</b></span>`;
  }

  function sparkSVG(prices, w = 120, h = 36) {
    if (!prices?.length) return '';
    const step = Math.max(1, Math.floor(prices.length / 60));
    const pts = prices.filter((_, i) => i % step === 0 || i === prices.length - 1);
    const min = Math.min(...pts), max = Math.max(...pts), span = max - min || 1;
    const d = pts.map((p, i) => `${((i / (pts.length - 1)) * w).toFixed(1)},${(h - 2 - ((p - min) / span) * (h - 4)).toFixed(1)}`).join(' ');
    const color = pts[pts.length - 1] >= pts[0] ? 'var(--up)' : 'var(--down)';
    return `<svg class="spark" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><polyline fill="none" stroke="${color}" stroke-width="1.5" points="${d}"/></svg>`;
  }

  function coinRow(c, prevMap) {
    const on = state.watchlist.includes(c.id);
    const prev = prevMap?.get(c.id)?.current_price;
    const flash = prev != null && prev !== c.current_price ? (c.current_price > prev ? 'flash-up' : 'flash-down') : '';
    return `<tr data-id="${esc(c.id)}">
      <td><button class="star ${on ? 'on' : ''}" data-star="${esc(c.id)}" aria-label="${on ? 'Remove from' : 'Add to'} watchlist">${on ? '★' : '☆'}</button></td>
      <td class="muted num-col">${c.market_cap_rank ?? '—'}</td>
      <td><div class="coin-cell">${coinIcon(c)}<span class="coin-name">${esc(c.name)}</span><span class="coin-sym">${esc(c.symbol)}</span></div></td>
      <td class="r ${flash}">${fmtMoney(c.current_price)}</td>
      <td class="r hide-sm">${fmtPct(c.price_change_percentage_1h_in_currency)}</td>
      <td class="r">${fmtPct(c.price_change_percentage_24h_in_currency ?? c.price_change_percentage_24h)}</td>
      <td class="r hide-sm">${fmtPct(c.price_change_percentage_7d_in_currency)}</td>
      <td class="r hide-md">${fmtCompact(c.market_cap)}</td>
      <td class="r hide-md">${sparkSVG(c.sparkline_in_7d?.price)}</td>
    </tr>`;
  }

  function sortedCoins(list) {
    const key = {
      rank: (c) => c.market_cap_rank ?? 1e9,
      price: (c) => -(c.current_price ?? 0),
      change24: (c) => -(c.price_change_percentage_24h_in_currency ?? -1e9),
      change7d: (c) => -(c.price_change_percentage_7d_in_currency ?? -1e9),
      volume: (c) => -(c.total_volume ?? 0),
    }[state.sort] || ((c) => c.market_cap_rank);
    return [...list].sort((a, b) => key(a) - key(b));
  }

  function renderMarkets(prevMap) {
    const q = $('#search').value.trim().toLowerCase();
    let list = state.coins;
    if (q) list = list.filter((c) => c.name.toLowerCase().includes(q) || c.symbol.toLowerCase().includes(q));
    const body = $('#markets-body');
    if (!list.length) {
      body.innerHTML = `<tr><td colspan="9" class="empty">${state.mode === 'loading' ? 'Loading prices…' : 'No coins match your search.'}</td></tr>`;
      return;
    }
    body.innerHTML = sortedCoins(list).map((c) => coinRow(c, prevMap)).join('');
  }

  function renderWatchlist(prevMap) {
    const list = state.watchlist.map((id) => state.coinMap.get(id)).filter(Boolean);
    $('#watchlist-body').innerHTML = sortedCoins(list).map((c) => coinRow(c, prevMap)).join('');
    $('#watchlist-empty').hidden = list.length > 0;
  }

  // Portfolio
  function computeHoldings() {
    const cur = state.currency;
    const byCoin = new Map();
    // Process in chronological order so average-cost accounting is correct.
    for (const t of [...state.txs].sort((a, b) => a.ts - b.ts)) {
      const h = byCoin.get(t.coinId) || { coinId: t.coinId, amount: 0, cost: 0, realized: 0, txs: [] };
      const price = convert(t.price, t.cur, cur);
      h.txs.push(t);
      if (price == null) { h.unconvertible = true; }
      if (t.type === 'buy') {
        h.amount += t.amount;
        h.cost += (price ?? 0) * t.amount;
      } else {
        const avg = h.amount > 0 ? h.cost / h.amount : 0;
        const qty = Math.min(t.amount, h.amount);
        h.realized += ((price ?? 0) - avg) * qty;
        h.cost -= avg * qty;
        h.amount -= qty;
      }
      byCoin.set(t.coinId, h);
    }
    const rows = [];
    for (const h of byCoin.values()) {
      const c = state.coinMap.get(h.coinId);
      const price = c?.current_price ?? null;
      const value = price != null ? price * h.amount : null;
      const ch24 = c?.price_change_percentage_24h_in_currency ?? c?.price_change_percentage_24h ?? 0;
      const value24ago = value != null ? value / (1 + ch24 / 100) : null;
      const unreal = value != null ? value - h.cost : null;
      rows.push({ ...h, coin: c, price, value, value24ago, avg: h.amount > 0 ? h.cost / h.amount : 0, pl: unreal != null ? unreal + h.realized : null });
    }
    rows.sort((a, b) => (b.value ?? 0) - (a.value ?? 0));
    return rows;
  }

  const PALETTE = ['#3ee6a8', '#5aa9ff', '#ffc857', '#ff6b7a', '#b48cff', '#4dd6e8', '#ff9f5a', '#9fe36b', '#f78fd0', '#8aa39b'];

  function renderPortfolio() {
    const rows = computeHoldings();
    const active = rows.filter((r) => r.amount > 1e-12);
    const total = active.reduce((a, r) => a + (r.value ?? 0), 0);
    const total24 = active.reduce((a, r) => a + (r.value24ago ?? 0), 0);
    const cost = active.reduce((a, r) => a + r.cost, 0);
    const pl = rows.reduce((a, r) => a + (r.pl ?? 0), 0);
    const plBase = cost || rows.reduce((a, r) => a + r.txs.filter((t) => t.type === 'buy').reduce((s, t) => s + (convert(t.price, t.cur, state.currency) ?? 0) * t.amount, 0), 0);

    $('#pf-value').textContent = rows.length ? fmtMoney(total) : '—';
    const d24 = total - total24;
    $('#pf-24h').innerHTML = rows.length ? `<span class="${d24 >= 0 ? 'up' : 'down'}">${d24 >= 0 ? '+' : ''}${fmtMoney(d24)}</span> <div class="sub">${fmtPct(total24 ? (d24 / total24) * 100 : 0)}</div>` : '—';
    $('#pf-pl').innerHTML = rows.length ? `<span class="${pl >= 0 ? 'up' : 'down'}">${pl >= 0 ? '+' : ''}${fmtMoney(pl)}</span> <div class="sub">${fmtPct(plBase ? (pl / plBase) * 100 : 0)}</div>` : '—';
    $('#pf-cost').textContent = rows.length ? fmtMoney(cost) : '—';

    $('#holdings-body').innerHTML = rows.map((r) => {
      const c = r.coin || { id: r.coinId, name: r.coinId, symbol: '' };
      const plPct = r.cost > 0 && r.pl != null ? (r.pl / r.cost) * 100 : null;
      return `<tr>
        <td><div class="coin-cell">${coinIcon(c)}<div><div class="coin-name">${esc(c.name)}</div><div class="sub">${r.txs.length} transaction${r.txs.length === 1 ? '' : 's'}</div></div></div></td>
        <td class="r">${fmtMoney(r.price)}<div class="sub">${fmtPct(c.price_change_percentage_24h_in_currency)}</div></td>
        <td class="r">${fmtMoney(r.value)}<div class="sub">${fmtNum(r.amount)} ${esc((c.symbol || '').toUpperCase())}</div></td>
        <td class="r hide-sm">${r.amount > 0 ? fmtMoney(r.avg) : '—'}</td>
        <td class="r"><span class="${(r.pl ?? 0) >= 0 ? 'up' : 'down'}">${r.pl != null ? (r.pl >= 0 ? '+' : '') + fmtMoney(r.pl) : '—'}</span><div class="sub">${plPct != null ? fmtPct(plPct) : ''}</div></td>
        <td class="r"><button class="del" data-del-holding="${esc(r.coinId)}" title="Remove all transactions for this coin" aria-label="Remove">✕</button></td>
      </tr>`;
    }).join('');
    $('#holdings-empty').hidden = rows.length > 0;

    // Allocation donut
    const alloc = $('#allocation');
    if (!active.length || total <= 0) { alloc.innerHTML = '<p class="empty">Nothing to show yet.</p>'; return; }
    let slices = active.map((r) => ({ name: r.coin?.name || r.coinId, sym: r.coin?.symbol || '', v: r.value ?? 0 }));
    if (slices.length > 8) {
      const rest = slices.slice(7).reduce((a, s) => a + s.v, 0);
      slices = [...slices.slice(0, 7), { name: 'Other', sym: '', v: rest }];
    }
    const R = 70, r0 = 46, cx = 80, cy = 80;
    let a0 = -Math.PI / 2;
    const arcs = slices.map((s, i) => {
      const frac = s.v / total;
      const a1 = a0 + frac * Math.PI * 2;
      const large = a1 - a0 > Math.PI ? 1 : 0;
      const p = (rad, a) => `${(cx + rad * Math.cos(a)).toFixed(2)} ${(cy + rad * Math.sin(a)).toFixed(2)}`;
      const path = frac >= 0.9999
        ? `M ${cx - R} ${cy} A ${R} ${R} 0 1 1 ${cx + R} ${cy} A ${R} ${R} 0 1 1 ${cx - R} ${cy} M ${cx - r0} ${cy} A ${r0} ${r0} 0 1 0 ${cx + r0} ${cy} A ${r0} ${r0} 0 1 0 ${cx - r0} ${cy} Z`
        : `M ${p(R, a0)} A ${R} ${R} 0 ${large} 1 ${p(R, a1)} L ${p(r0, a1)} A ${r0} ${r0} 0 ${large} 0 ${p(r0, a0)} Z`;
      a0 = a1;
      return `<path d="${path}" fill="${PALETTE[i % PALETTE.length]}" fill-rule="evenodd"><title>${esc(s.name)} ${(frac * 100).toFixed(1)}%</title></path>`;
    }).join('');
    alloc.innerHTML = `
      <svg class="alloc-donut" width="160" height="160" viewBox="0 0 160 160">${arcs}</svg>
      <ul class="alloc-legend">${slices.map((s, i) => `<li><span class="sw" style="background:${PALETTE[i % PALETTE.length]}"></span>${esc(s.name)} <span class="coin-sym">${esc(s.sym)}</span><span class="pct">${((s.v / total) * 100).toFixed(1)}%</span></li>`).join('')}</ul>`;
  }

  // Alerts
  function renderAlerts() {
    const list = $('#alerts-list');
    const items = [...state.alerts].sort((a, b) => (!!a.triggeredAt - !!b.triggeredAt) || b.createdAt - a.createdAt);
    list.innerHTML = items.map((a) => {
      const c = state.coinMap.get(a.coinId) || { name: a.coinId, symbol: '' };
      const target = convert(a.price, a.cur, state.currency);
      const now = c.current_price;
      const dist = now && target ? ((target - now) / now) * 100 : null;
      return `<li class="${a.triggeredAt ? 'triggered' : ''}">
        ${coinIcon(c, 28)}
        <div class="info">
          <div class="cond">${esc(c.name)} ${a.dir === 'above' ? '≥' : '≤'} ${fmtMoney(a.price, a.cur)}</div>
          <div class="meta">${a.triggeredAt
            ? `Triggered ${new Date(a.triggeredAt).toLocaleString()} at ${fmtMoney(a.lastPrice, a.cur)}`
            : `Now ${fmtMoney(now)}${dist != null ? ` · ${Math.abs(dist).toFixed(2)}% ${dist >= 0 ? 'below' : 'above'} target` : ''}`}</div>
        </div>
        ${a.triggeredAt ? '<span class="pill hit">Triggered</span>' : '<span class="pill on">Active</span>'}
        ${a.triggeredAt ? `<button class="btn ghost" data-rearm="${esc(a.id)}">Re-arm</button>` : ''}
        <button class="del" data-del-alert="${esc(a.id)}" aria-label="Delete alert">✕</button>
      </li>`;
    }).join('');
    $('#alerts-empty').hidden = items.length > 0;
    const active = state.alerts.filter((a) => !a.triggeredAt).length;
    const badge = $('#alert-badge');
    badge.hidden = !active;
    badge.textContent = active;
    const btn = $('#enable-notif');
    if (!('Notification' in window)) btn.hidden = true;
    else if (Notification.permission === 'granted') { btn.textContent = 'Notifications on'; btn.disabled = true; }
    else if (Notification.permission === 'denied') { btn.textContent = 'Notifications blocked'; btn.disabled = true; }
  }

  function checkAlerts() {
    // Alerts only fire against real prices, never demo data.
    if (state.mode !== 'live') return;
    let changed = false;
    for (const a of state.alerts) {
      if (a.triggeredAt) continue;
      const c = state.coinMap.get(a.coinId);
      if (!c) continue;
      const price = convert(c.current_price, state.currency, a.cur);
      if (price == null) continue;
      const hit = a.dir === 'above' ? price >= a.price : price <= a.price;
      if (hit) {
        a.triggeredAt = Date.now();
        a.lastPrice = price;
        changed = true;
        const msg = `${c.name} is ${a.dir} ${fmtMoney(a.price, a.cur)} — now ${fmtMoney(price, a.cur)}`;
        toast(`🔔 ${msg}`);
        notify('Mintline price alert', msg, c.image);
      }
    }
    if (changed) { persist(); renderAlerts(); }
  }

  async function notify(title, body, icon) {
    if (!('Notification' in window) || Notification.permission !== 'granted') return;
    const opts = { body, icon: icon || 'icons/icon-192.png', badge: 'icons/icon-192.png', tag: `mintline-${Date.now()}` };
    try {
      const reg = await navigator.serviceWorker?.getRegistration();
      if (reg) reg.showNotification(title, opts);
      else new Notification(title, opts);
    } catch { /* ignore */ }
  }

  // ---------- Coin detail ----------
  function openDetail(id) {
    state.detail.id = id;
    renderDetailHeader();
    $('#detail').showModal();
    loadChart();
  }

  function renderDetailHeader() {
    const c = state.coinMap.get(state.detail.id);
    if (!c) return;
    $('#detail-title').innerHTML = `${coinIcon(c, 32)}<span>${esc(c.name)}</span><span class="coin-sym">${esc(c.symbol)}</span><span class="pill">#${c.market_cap_rank ?? '—'}</span>`;
    $('#detail-price').innerHTML = `${fmtMoney(c.current_price)}<span class="chg">${fmtPct(c.price_change_percentage_24h_in_currency ?? c.price_change_percentage_24h)}</span>`;
    const stat = (l, v) => `<div><div class="label">${l}</div><div class="val">${v}</div></div>`;
    $('#detail-stats').innerHTML = [
      stat('Market cap', fmtCompact(c.market_cap)),
      stat('24h volume', fmtCompact(c.total_volume)),
      stat('24h range', `${fmtMoney(c.low_24h)} – ${fmtMoney(c.high_24h)}`),
      stat('Circulating', `${fmtNum(c.circulating_supply, 0)} ${esc(c.symbol.toUpperCase())}`),
      stat('Max supply', c.max_supply ? fmtNum(c.max_supply, 0) : '∞'),
      stat('All-time high', `${fmtMoney(c.ath)} ${c.ath_change_percentage != null ? fmtPct(c.ath_change_percentage) : ''}`),
    ].join('');
    const on = state.watchlist.includes(c.id);
    $('#detail-star').textContent = on ? '★ Watching' : '☆ Watch';
  }

  const chartCache = new Map();
  async function loadChart() {
    const { id, days } = state.detail;
    const c = state.coinMap.get(id);
    const el = $('#chart');
    $$('#ranges button').forEach((b) => b.classList.toggle('active', +b.dataset.days === days));
    const key = `${id}:${days}:${state.currency}`;
    let pts = chartCache.get(key)?.pts;
    if (!pts) {
      el.innerHTML = '<div class="loading">Loading chart…</div>';
      try {
        if (state.mode === 'demo') throw new Error('demo');
        const data = await getJSON(`${API}/coins/${encodeURIComponent(id)}/market_chart?vs_currency=${state.currency}&days=${days}`);
        pts = data.prices;
        chartCache.set(key, { pts, at: Date.now() });
      } catch {
        pts = c ? Demo.chart(c, days) : [];
        if (state.mode !== 'demo' && c?.sparkline_in_7d?.price && days === 7) {
          const s = c.sparkline_in_7d.price, step = 7 * 864e5 / s.length, now = Date.now();
          pts = s.map((p, i) => [now - (s.length - 1 - i) * step, p]);
        }
      }
    }
    // Ignore if the user switched coin/range meanwhile.
    if (state.detail.id !== id || state.detail.days !== days) return;
    drawChart(el, pts, days);
  }

  function drawChart(el, pts, days) {
    if (!pts?.length) { el.innerHTML = '<div class="loading">No chart data</div>'; return; }
    const W = el.clientWidth || 640, H = el.clientHeight || 260, padL = 8, padR = 64, padT = 10, padB = 24;
    const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1]);
    const x0 = xs[0], x1 = xs[xs.length - 1];
    let y0 = Math.min(...ys), y1 = Math.max(...ys);
    const padY = (y1 - y0) * 0.08 || y1 * 0.01 || 1; y0 -= padY; y1 += padY;
    const X = (x) => padL + ((x - x0) / (x1 - x0 || 1)) * (W - padL - padR);
    const Y = (y) => padT + (1 - (y - y0) / (y1 - y0)) * (H - padT - padB);
    const up = ys[ys.length - 1] >= ys[0];
    const color = up ? 'var(--up)' : 'var(--down)';
    const line = pts.map((p, i) => `${i ? 'L' : 'M'}${X(p[0]).toFixed(1)},${Y(p[1]).toFixed(1)}`).join('');
    const area = `${line}L${X(x1).toFixed(1)},${H - padB}L${X(x0).toFixed(1)},${H - padB}Z`;
    const ticks = 4;
    let grid = '';
    for (let i = 0; i <= ticks; i++) {
      const v = y0 + ((y1 - y0) * i) / ticks, y = Y(v);
      grid += `<line x1="${padL}" x2="${W - padR}" y1="${y}" y2="${y}" stroke="var(--line)" stroke-dasharray="2 4"/>`;
      grid += `<text x="${W - padR + 6}" y="${y + 4}" fill="var(--muted)" font-size="11">${esc(fmtMoney(v, state.currency, { compact: v >= 1e5 }))}</text>`;
    }
    const tfmt = (t) => days <= 1
      ? new Date(t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : new Date(t).toLocaleDateString([], days > 180 ? { month: 'short', year: '2-digit' } : { month: 'short', day: 'numeric' });
    for (let i = 0; i <= 4; i++) {
      const t = x0 + ((x1 - x0) * i) / 4;
      grid += `<text x="${X(t)}" y="${H - 6}" fill="var(--muted)" font-size="11" text-anchor="${i === 0 ? 'start' : i === 4 ? 'end' : 'middle'}">${esc(tfmt(t))}</text>`;
    }
    el.innerHTML = `
      <svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
        <defs><linearGradient id="g" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stop-color="${color}" stop-opacity=".28"/><stop offset="1" stop-color="${color}" stop-opacity="0"/>
        </linearGradient></defs>
        ${grid}
        <path d="${area}" fill="url(#g)"/>
        <path d="${line}" fill="none" stroke="${color}" stroke-width="2" vector-effect="non-scaling-stroke"/>
        <line id="cx" y1="${padT}" y2="${H - padB}" stroke="var(--muted)" stroke-dasharray="3 3" visibility="hidden"/>
        <circle id="cd" r="4" fill="${color}" stroke="var(--panel)" stroke-width="2" visibility="hidden"/>
        <rect x="${padL}" y="0" width="${W - padL - padR}" height="${H}" fill="transparent" id="hit"/>
      </svg>
      <div class="tip" hidden></div>`;
    const svg = $('svg', el), tip = $('.tip', el), cxl = $('#cx', el), cd = $('#cd', el);
    const move = (ev) => {
      const rect = svg.getBoundingClientRect();
      const clientX = ev.touches ? ev.touches[0].clientX : ev.clientX;
      const px = ((clientX - rect.left) / rect.width) * W;
      const t = x0 + ((px - padL) / (W - padL - padR)) * (x1 - x0);
      let lo = 0, hi = pts.length - 1;
      while (hi - lo > 1) { const m = (lo + hi) >> 1; if (pts[m][0] < t) lo = m; else hi = m; }
      const p = Math.abs(pts[lo][0] - t) < Math.abs(pts[hi][0] - t) ? pts[lo] : pts[hi];
      const x = X(p[0]), y = Y(p[1]);
      cxl.setAttribute('x1', x); cxl.setAttribute('x2', x); cxl.setAttribute('visibility', 'visible');
      cd.setAttribute('cx', x); cd.setAttribute('cy', y); cd.setAttribute('visibility', 'visible');
      tip.hidden = false;
      tip.style.left = `${(x / W) * rect.width}px`;
      tip.style.top = `${(y / H) * rect.height}px`;
      tip.innerHTML = `<b>${fmtMoney(p[1])}</b><br><span class="muted">${new Date(p[0]).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</span>`;
    };
    const leave = () => { tip.hidden = true; cxl.setAttribute('visibility', 'hidden'); cd.setAttribute('visibility', 'hidden'); };
    svg.addEventListener('mousemove', move);
    svg.addEventListener('touchmove', move, { passive: true });
    svg.addEventListener('mouseleave', leave);
    svg.addEventListener('touchend', leave);
  }

  // ---------- Forms ----------
  function fillCoinSelect(sel, selected) {
    const ids = new Set();
    const opts = [];
    const add = (c) => { if (c && !ids.has(c.id)) { ids.add(c.id); opts.push(c); } };
    trackedIds().forEach((id) => add(state.coinMap.get(id)));
    sortedCoins(state.coins).forEach(add);
    sel.innerHTML = opts.map((c) => `<option value="${esc(c.id)}" ${c.id === selected ? 'selected' : ''}>${esc(c.name)} (${esc(c.symbol.toUpperCase())})</option>`).join('');
  }

  function openHoldingForm(coinId) {
    const f = $('#holding-form');
    f.reset();
    fillCoinSelect(f.coin, coinId || state.coins[0]?.id);
    const setPrice = () => { const c = state.coinMap.get(f.coin.value); f.price.value = c ? +c.current_price.toPrecision(8) : ''; updateTotal(); };
    f.coin.onchange = setPrice;
    setPrice();
    $$('.cur-label').forEach((e) => (e.textContent = state.currency.toUpperCase()));
    $('#holding-dialog').showModal();
    f.amount.focus();
  }
  function updateTotal() {
    const f = $('#holding-form');
    const t = parseFloat(f.amount.value) * parseFloat(f.price.value);
    $('#tx-total').textContent = isFinite(t) ? fmtMoney(t) : '—';
  }

  function openAlertForm(coinId) {
    const f = $('#alert-form');
    f.reset();
    fillCoinSelect(f.coin, coinId || state.coins[0]?.id);
    const hint = () => {
      const c = state.coinMap.get(f.coin.value);
      $('#alert-hint').textContent = c ? `Current price: ${fmtMoney(c.current_price)}` : '';
      if (c && !f.price.value) f.price.value = +(c.current_price * (f.dir.value === 'above' ? 1.05 : 0.95)).toPrecision(6);
    };
    f.coin.onchange = () => { f.price.value = ''; hint(); };
    $$('input[name="dir"]', f).forEach((r) => (r.onchange = () => { f.price.value = ''; hint(); }));
    hint();
    $$('.cur-label').forEach((e) => (e.textContent = state.currency.toUpperCase()));
    $('#alert-dialog').showModal();
    f.price.focus();
  }

  // ---------- Toasts ----------
  function toast(msg, kind = '', action = null) {
    const el = document.createElement('div');
    el.className = `toast ${kind}`;
    const span = document.createElement('span');
    span.textContent = msg;
    el.appendChild(span);
    if (action) {
      const b = document.createElement('button');
      b.className = 'toast-action';
      b.textContent = action.label;
      b.onclick = () => { action.run(); el.remove(); };
      el.appendChild(b);
    }
    const box = $('#toasts');
    box.appendChild(el);
    while (box.children.length > 3) box.firstElementChild.remove();
    setTimeout(() => el.remove(), 5000);
  }

  // ---------- Events ----------
  function toggleStar(id) {
    const i = state.watchlist.indexOf(id);
    if (i >= 0) state.watchlist.splice(i, 1); else state.watchlist.push(id);
    persist();
    renderMarkets(); renderWatchlist();
    if ($('#detail').open) renderDetailHeader();
  }

  function switchTab(tab) {
    state.tab = tab;
    $$('.tabs button').forEach((b) => b.classList.toggle('active', b.dataset.tab === tab));
    $$('.panel').forEach((p) => p.classList.toggle('active', p.id === `tab-${tab}`));
    history.replaceState(null, '', `#${tab}`);
  }

  function bind() {
    $('.tabs').addEventListener('click', (e) => { const b = e.target.closest('button[data-tab]'); if (b) switchTab(b.dataset.tab); });

    const onTable = (e) => {
      const star = e.target.closest('[data-star]');
      if (star) { e.stopPropagation(); toggleStar(star.dataset.star); return; }
      const tr = e.target.closest('tr[data-id]');
      if (tr) openDetail(tr.dataset.id);
    };
    $('#markets-body').addEventListener('click', onTable);
    $('#watchlist-body').addEventListener('click', onTable);

    $('#search').addEventListener('input', () => renderMarkets());
    const sortSel = $('#sort');
    sortSel.value = state.sort;
    sortSel.addEventListener('change', () => { state.sort = sortSel.value; persist(); renderMarkets(); renderWatchlist(); });

    const curSel = $('#currency');
    curSel.value = state.currency;
    curSel.addEventListener('change', () => {
      state.currency = curSel.value;
      persist();
      chartCache.clear();
      // Re-render immediately with converted values where possible, then fetch.
      if (state.mode === 'demo') applyData(Demo.data(state.currency), 'demo');
      else { state.mode = 'loading'; renderStatus(); }
      refresh();
    });
    $('#refresh').addEventListener('click', () => refresh({ manual: true }));

    // Dialog close buttons + click outside
    $$('dialog').forEach((d) => {
      d.addEventListener('click', (e) => {
        if (e.target.closest('[data-close]') || e.target === d) d.close();
      });
    });
    $('#detail').addEventListener('close', () => { state.detail.id = null; });
    $('#ranges').addEventListener('click', (e) => {
      const b = e.target.closest('button[data-days]');
      if (!b) return;
      state.detail.days = +b.dataset.days;
      loadChart();
    });
    $('#detail-star').addEventListener('click', () => toggleStar(state.detail.id));
    $('#detail-alert').addEventListener('click', () => { const id = state.detail.id; $('#detail').close(); openAlertForm(id); });
    $('#detail-hold').addEventListener('click', () => { const id = state.detail.id; $('#detail').close(); openHoldingForm(id); });

    // Holdings
    $('#add-holding').addEventListener('click', () => openHoldingForm());
    const hf = $('#holding-form');
    hf.amount.addEventListener('input', updateTotal);
    hf.price.addEventListener('input', updateTotal);
    hf.addEventListener('submit', (e) => {
      e.preventDefault();
      const amount = parseFloat(hf.amount.value), price = parseFloat(hf.price.value);
      if (!(amount > 0) || !(price >= 0)) return;
      const type = hf.type.value;
      if (type === 'sell') {
        const held = computeHoldings().find((h) => h.coinId === hf.coin.value)?.amount ?? 0;
        if (amount > held + 1e-12) { toast(`You only hold ${fmtNum(held)} of this coin`, 'err'); return; }
      }
      state.txs.push({ id: uid(), coinId: hf.coin.value, type, amount, price, cur: state.currency, ts: Date.now() });
      if (!state.watchlist.includes(hf.coin.value)) state.watchlist.push(hf.coin.value);
      persist();
      $('#holding-dialog').close();
      renderPortfolio(); renderWatchlist(); renderMarkets();
      switchTab('portfolio');
      toast('Transaction saved');
    });
    $('#holdings-body').addEventListener('click', (e) => {
      const b = e.target.closest('[data-del-holding]');
      if (!b) return;
      const id = b.dataset.delHolding;
      const name = state.coinMap.get(id)?.name || id;
      const removed = state.txs.filter((t) => t.coinId === id);
      state.txs = state.txs.filter((t) => t.coinId !== id);
      persist(); renderPortfolio();
      toast(`Removed ${name} from your portfolio`, '', {
        label: 'Undo',
        run: () => { state.txs.push(...removed); persist(); renderPortfolio(); },
      });
    });

    // Alerts
    $('#add-alert').addEventListener('click', () => openAlertForm());
    const af = $('#alert-form');
    af.addEventListener('submit', (e) => {
      e.preventDefault();
      const price = parseFloat(af.price.value);
      if (!(price > 0)) return;
      state.alerts.push({ id: uid(), coinId: af.coin.value, dir: af.dir.value, price, cur: state.currency, createdAt: Date.now(), triggeredAt: null });
      persist();
      $('#alert-dialog').close();
      renderAlerts();
      switchTab('alerts');
      toast('Alert created');
      checkAlerts();
      if ('Notification' in window && Notification.permission === 'default') requestNotif();
    });
    $('#alerts-list').addEventListener('click', (e) => {
      const del = e.target.closest('[data-del-alert]');
      const re = e.target.closest('[data-rearm]');
      if (del) state.alerts = state.alerts.filter((a) => a.id !== del.dataset.delAlert);
      else if (re) { const a = state.alerts.find((x) => x.id === re.dataset.rearm); if (a) { a.triggeredAt = null; a.lastPrice = null; } }
      else return;
      persist(); renderAlerts(); checkAlerts();
    });
    $('#enable-notif').addEventListener('click', requestNotif);

    // Export / import
    $('#export').addEventListener('click', () => {
      const { watchlist, txs, alerts, currency } = state;
      const blob = new Blob([JSON.stringify({ app: 'mintline', version: 1, exportedAt: new Date().toISOString(), currency, watchlist, txs, alerts }, null, 2)], { type: 'application/json' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `mintline-backup-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 1000);
    });
    $('#import').addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      try {
        const data = JSON.parse(await file.text());
        if (data.app !== 'mintline') throw new Error('Not a Mintline backup');
        state.watchlist = Array.isArray(data.watchlist) ? data.watchlist.map(String) : state.watchlist;
        state.txs = Array.isArray(data.txs) ? data.txs.filter((t) => t && t.coinId && isFinite(t.amount) && isFinite(t.price)) : state.txs;
        state.alerts = Array.isArray(data.alerts) ? data.alerts.filter((a) => a && a.coinId && isFinite(a.price)) : state.alerts;
        persist();
        toast('Backup imported');
        refresh();
      } catch (err) {
        toast(`Import failed: ${err.message}`, 'err');
      }
      e.target.value = '';
    });

    // Keyboard: "/" focuses search
    document.addEventListener('keydown', (e) => {
      if (e.key === '/' && !e.target.closest('input, select, textarea, dialog')) {
        e.preventDefault(); switchTab('markets'); $('#search').focus();
      }
    });

    // Refresh when coming back to the app
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && Date.now() - (state.updatedAt || 0) > REFRESH_MS / 2) refresh();
    });
    window.addEventListener('online', () => refresh());
    window.addEventListener('resize', () => { if ($('#detail').open) loadChart(); });
  }

  async function requestNotif() {
    if (!('Notification' in window)) return;
    const p = await Notification.requestPermission();
    if (p === 'granted') toast('Notifications enabled');
    renderAlerts();
  }

  // ---------- Boot ----------
  function boot() {
    bind();
    const initial = (location.hash || '').slice(1);
    if (['markets', 'watchlist', 'portfolio', 'alerts'].includes(initial)) switchTab(initial);
    // Paint cached data instantly, then go to the network.
    const cache = load(CACHE_KEY);
    if (cache && cache.currency === state.currency && cache.coins?.length) applyData(cache, 'cached', cache.at);
    else renderAll();
    refresh();
    setInterval(() => { if (!document.hidden) refresh(); }, REFRESH_MS);
    if ('serviceWorker' in navigator && /^https?:$/.test(location.protocol)) {
      navigator.serviceWorker.register('sw.js').catch(() => {});
    }
  }

  // Exposed for tests/debugging
  window.Mintline = { state, convert, computeHoldings, checkAlerts, Demo };

  boot();
})();
