/* Mintline — Crypto Tracker
 * Live prices, alerts, portfolio and tax tracking, research and charts.
 * Browser version of the Python crypto_toolkit (see ../crypto_toolkit).
 * Market data comes from free public APIs; falls back to cached data, then demo data.
 */
(() => {
  'use strict';

  const TA = window.MintTA, E = window.MintEngine;
  const API = 'https://api.coingecko.com/api/v3';
  const REFRESH_MS = 60_000;
  const DAY = 864e5;
  const STORE_KEY = 'mintline:v1';
  const CACHE_KEY = 'mintline:cache:v1';

  // Canonical CoinGecko ids for common tickers, so "BTC" never resolves to a look-alike token.
  const SYMBOL_IDS = {
    BTC: 'bitcoin', ETH: 'ethereum', SOL: 'solana', XRP: 'ripple', DOGE: 'dogecoin', ADA: 'cardano',
    BNB: 'binancecoin', LTC: 'litecoin', DOT: 'polkadot', LINK: 'chainlink', AVAX: 'avalanche-2',
    TRX: 'tron', TON: 'the-open-network', USDT: 'tether', USDC: 'usd-coin', BCH: 'bitcoin-cash',
    XLM: 'stellar', ATOM: 'cosmos', UNI: 'uniswap', NEAR: 'near', POL: 'polygon-ecosystem-token',
    MATIC: 'matic-network', SHIB: 'shiba-inu', XMR: 'monero', ETC: 'ethereum-classic', ARB: 'arbitrum',
    OP: 'optimism', SUI: 'sui', APT: 'aptos', DAI: 'dai', AAVE: 'aave', FIL: 'filecoin', HBAR: 'hedera-hashgraph',
  };
  const ID_SYMBOLS = Object.fromEntries(Object.entries(SYMBOL_IDS).map(([s, id]) => [id, s]));

  // ---------- State ----------
  const defaults = {
    currency: 'usd',
    sort: 'rank',
    watchlist: ['bitcoin', 'ethereum'],
    txs: [],      // {id, coinId, type, amount, price, fee, cur, date, exchange, notes}
    alerts: [],   // {id, name, type, coinId, contract, value, period, interval, cooldown, cur, enabled, lastFired, ...}
    settings: { cgKey: '', ntfyTopic: '', webhook: '', taxMethod: 'FIFO' },
    indicators: ['sma50', 'sma200'],
    marketsView: 'prices',
    screenerSort: { key: 'rank', dir: 1 },
    profile: null,
    paperBot: null,
  };
  const saved = load(STORE_KEY) || {};
  const state = {
    ...defaults,
    ...saved,
    settings: { ...defaults.settings, ...(saved.settings || {}) },
    coins: [],
    coinMap: new Map(),
    rates: null,
    global: null,
    mode: 'loading',    // live | cached | demo | loading
    updatedAt: null,
    tab: 'markets',
    detail: { id: null, days: 7 },
    taxYear: null,
  };
  migrate();

  function migrate() {
    state.txs = (state.txs || []).filter((t) => t && t.coinId).map((t) => ({
      exchange: '', notes: '', fee: 0, ...t,
      type: E.TYPES.includes(t.type) ? t.type : 'buy',
      date: t.date ?? t.ts ?? Date.now(),
      amount: +t.amount || 0, price: +t.price || 0, fee: +t.fee || 0,
    }));
    state.alerts = (state.alerts || []).filter(Boolean).map((a) => {
      if (a.type) return { enabled: true, cooldown: 60, cur: 'usd', ...a };
      // Pre-2.0 alerts: {coinId, dir, price, cur, triggeredAt}
      return { id: a.id || uid(), name: '', type: a.dir === 'below' ? 'price_below' : 'price_above', coinId: a.coinId,
        value: a.price, cur: a.cur || 'usd', cooldown: 60, enabled: !a.triggeredAt, lastFired: a.triggeredAt || null, createdAt: a.createdAt || Date.now() };
    });
  }

  const PERSIST_KEYS = ['currency', 'sort', 'watchlist', 'txs', 'alerts', 'settings', 'indicators', 'marketsView', 'screenerSort', 'profile', 'paperBot'];
  function persist() { save(STORE_KEY, Object.fromEntries(PERSIST_KEYS.map((k) => [k, state[k]]))); }
  function load(k) { try { return JSON.parse(localStorage.getItem(k)); } catch { return null; } }
  function save(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* storage unavailable */ } }

  // ---------- Helpers ----------
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const uid = () => Math.random().toString(36).slice(2, 10) + Date.now().toString(36);
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const isoDay = (ms) => new Date(ms).toISOString().slice(0, 10);
  const todayIso = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; };
  const parseIsoDay = (s) => { const [y, m, d] = s.split('-').map(Number); return Date.UTC(y, m - 1, d); };

  function fmtMoney(v, cur = state.currency, opts = {}) {
    if (v == null || !isFinite(v)) return '—';
    const abs = Math.abs(v);
    if (cur === 'btc') {
      const d = abs >= 1 ? 4 : abs >= 0.0001 ? 6 : 8;
      return `₿${v.toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d })}`;
    }
    let max = abs >= 1 ? 2 : abs >= 0.01 ? 4 : abs >= 0.0001 ? 6 : 8;
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
  const fmtCompact = (v, cur = state.currency) => fmtMoney(v, cur, { compact: true });
  const fmtUsd = (v, opts) => fmtMoney(v, 'usd', opts);
  function fmtPct(v, digits = 2) {
    if (v == null || !isFinite(v)) return '<span class="muted">—</span>';
    const cls = v >= 0 ? 'up' : 'down';
    const sign = v >= 0 ? '▲' : '▼';
    return `<span class="${cls}">${sign} ${Math.abs(v).toFixed(digits)}%</span>`;
  }
  function fmtNum(v, max = 8) {
    if (v == null || !isFinite(v)) return '—';
    return v.toLocaleString(undefined, { maximumFractionDigits: max });
  }
  const fmtBig = (v) => (v == null || !isFinite(v) ? '—' : new Intl.NumberFormat(undefined, { notation: 'compact', maximumFractionDigits: 2 }).format(v));
  const signed = (v, f = fmtMoney) => (v == null || !isFinite(v) ? '—' : `<span class="${v >= 0 ? 'up' : 'down'}">${v >= 0 ? '+' : '−'}${f(Math.abs(v))}</span>`);
  function coinIcon(c, size = 24) {
    if (c?.image) return `<img src="${esc(c.image)}" alt="" width="${size}" height="${size}" loading="lazy">`;
    return `<span class="coin-icon" style="width:${size}px;height:${size}px">${esc((c?.symbol || '?').slice(0, 3).toUpperCase())}</span>`;
  }
  function stripHtml(html) {
    const d = new DOMParser().parseFromString(String(html || ''), 'text/html');
    return d.body.textContent || '';
  }

  /** Convert an amount between vs-currencies using BTC-relative rates. */
  function convert(amount, from, to) {
    if (from === to || amount == null) return amount;
    const r = state.rates;
    if (!r || !r[from] || !r[to]) return null;
    return amount * (r[to].value / r[from].value);
  }
  const symbolOf = (id) => (state.coinMap.get(id)?.symbol || ID_SYMBOLS[id] || id || '').toUpperCase();
  const nameOf = (id) => state.coinMap.get(id)?.name || id;

  function downloadFile(name, text, type = 'text/plain') {
    const blob = new Blob([text], { type });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  }

  // ---------- Network: per-host spacing, retries and a small cache ----------
  // Same spacing as the toolkit's http.py, to stay inside free-tier limits.
  const HOST_GAP = { 'api.coingecko.com': 2100, 'api.blockchain.info': 1000, 'mempool.space': 500 };
  const nextAt = {};
  async function gate(host) {
    const gap = HOST_GAP[host];
    if (!gap) return;
    const now = Date.now();
    const at = Math.max(now, nextAt[host] || 0);
    nextAt[host] = at + gap;
    if (at > now) await sleep(at - now);
  }

  async function getJSON(url, { headers = {}, timeout = 15_000, retries = 2 } = {}) {
    const host = new URL(url).host;
    for (let attempt = 0; ; attempt++) {
      await gate(host);
      const ctrl = new AbortController();
      const t = setTimeout(() => ctrl.abort(), timeout);
      let res;
      try {
        res = await fetch(url, { signal: ctrl.signal, headers: { accept: 'application/json', ...headers } });
      } finally {
        clearTimeout(t);
      }
      if (res.ok) return res.json();
      if ((res.status === 429 || res.status >= 500) && attempt < retries) {
        const ra = parseFloat(res.headers.get('retry-after'));
        await sleep(Math.min(30_000, Number.isFinite(ra) ? ra * 1000 : 3000 * 2 ** attempt));
        continue;
      }
      const err = new Error(res.status === 429 ? 'Too many requests (rate limited). Try again in a minute, or add a free CoinGecko key in Settings.' : `HTTP ${res.status} from ${host}`);
      err.status = res.status;
      throw err;
    }
  }

  function cg(path) {
    const key = state.settings.cgKey?.trim();
    return getJSON(API + path, { headers: key ? { 'x-cg-demo-api-key': key } : {} });
  }

  const memo = new Map();
  function cached(key, ttl, fn) {
    const hit = memo.get(key);
    if (hit && (hit.pending || Date.now() - hit.at < ttl)) return hit.pending || Promise.resolve(hit.value);
    const pending = Promise.resolve().then(fn).then(
      (value) => { memo.set(key, { at: Date.now(), value }); return value; },
      (err) => { memo.delete(key); throw err; },
    );
    memo.set(key, { pending });
    return pending;
  }

  // ---------- Data sources ----------
  /** CoinGecko price history [[ms, price], ...]. Granularity: days 1 = 5 min, 2–90 = hourly, more = daily. */
  function priceHistory(coinId, days, vs = state.currency) {
    const ttl = days <= 1 ? 5 * 60e3 : days <= 90 ? 15 * 60e3 : 60 * 60e3;
    return cached(`hist:${coinId}:${days}:${vs}`, ttl, async () => {
      if (state.mode === 'demo') {
        const c = state.coinMap.get(coinId);
        if (!c) throw new Error('No data for this coin');
        const k = convert(1, state.currency, vs) ?? 1;
        return Demo.chart(c, days).map(([t, p]) => [t, p * k]);
      }
      const d = await cg(`/coins/${encodeURIComponent(coinId)}/market_chart?vs_currency=${vs}&days=${days}`);
      return d.prices;
    });
  }

  const INTERVAL_MS = { '5m': 5 * 60e3, '15m': 15 * 60e3, '1h': 3600e3, '4h': 4 * 3600e3, '6h': 6 * 3600e3, '1d': DAY };
  const INTERVAL_DAYS = { '5m': 1, '15m': 1, '1h': 7, '4h': 30, '6h': 30, '1d': 365 };
  /** Closing prices at the given candle size (USD), built from CoinGecko history. */
  async function closes(coinId, interval = '1h') {
    const pts = await priceHistory(coinId, INTERVAL_DAYS[interval] || 7, 'usd');
    return TA.resample(pts, INTERVAL_MS[interval] || 3600e3).map((p) => p[1]);
  }

  const KRAKEN_ALIAS = { BTC: 'XBT', DOGE: 'XDG' };
  /** Daily OHLC bars [{time, open, high, low, close}] in USD: Kraken (~720 days), else CoinGecko closes (365 days). */
  function dailyBars(coinId) {
    return cached(`bars:${coinId}`, 60 * 60e3, async () => {
      const sym = symbolOf(coinId);
      if (state.mode !== 'demo') {
        try {
          const pair = `${KRAKEN_ALIAS[sym] || sym}USD`;
          const d = await getJSON(`https://api.kraken.com/0/public/OHLC?pair=${pair}&interval=1440`, { retries: 0 });
          if (d.error?.length) throw new Error(d.error.join(', '));
          const rows = Object.entries(d.result).find(([k]) => k !== 'last')[1];
          const bars = rows.map((r) => ({ time: r[0] * 1000, open: +r[1], high: +r[2], low: +r[3], close: +r[4] }));
          if (bars.length > 30) return { bars, source: 'Kraken daily candles' };
        } catch { /* fall back to CoinGecko */ }
      }
      const pts = TA.resample(await priceHistory(coinId, 365, 'usd'), DAY);
      const bars = pts.map(([time, close]) => ({ time, open: close, high: close, low: close, close }));
      return { bars, source: state.mode === 'demo' ? 'demo prices' : 'CoinGecko daily closes (no intraday highs/lows)', closeOnly: true };
    });
  }

  function fearGreed(limit = 30) {
    return cached(`fng:${limit}`, 30 * 60e3, async () => {
      const d = await getJSON(`https://api.alternative.me/fng/?limit=${limit}&format=json`);
      return d.data.map((x) => ({ time: +x.timestamp * 1000, value: +x.value, label: x.value_classification })).sort((a, b) => a.time - b.time);
    });
  }

  function krakenFutures() {
    return cached('kfut', 5 * 60e3, async () => (await getJSON('https://futures.kraken.com/derivatives/api/v3/tickers')).tickers);
  }

  function coinProfile(id) {
    return cached(`profile:${id}`, 60 * 60e3, async () => {
      const c = await cg(`/coins/${encodeURIComponent(id)}?localization=false&tickers=false&community_data=true&developer_data=true`);
      const m = c.market_data || {};
      const usd = (k) => (m[k] || {}).usd ?? null;
      const circ = m.circulating_supply, total = m.total_supply, mx = m.max_supply;
      const mcap = usd('market_cap'), fdv = usd('fully_diluted_valuation'), vol = usd('total_volume');
      const dev = c.developer_data || {};
      return {
        id: c.id, symbol: (c.symbol || '').toUpperCase(), name: c.name,
        categories: c.categories || [], genesisDate: c.genesis_date, algorithm: c.hashing_algorithm,
        homepage: (c.links?.homepage || []).find(Boolean) || null,
        price: usd('current_price'), marketCap: mcap, rank: c.market_cap_rank, fdv,
        mcapToFdv: mcap && fdv ? mcap / fdv : null,
        circulating: circ, totalSupply: total, maxSupply: mx,
        pctIssued: circ && mx ? (circ / mx) * 100 : null,
        volume: vol, volToMcap: vol && mcap ? vol / mcap : null,
        ath: usd('ath'), athDate: (m.ath_date || {}).usd, fromAth: (m.ath_change_percentage || {}).usd,
        r7d: m.price_change_percentage_7d, r30d: m.price_change_percentage_30d, r1y: m.price_change_percentage_1y,
        githubStars: dev.stars ?? null, commits4w: dev.commit_count_4_weeks ?? null,
        description: stripHtml(c.description?.en || '').slice(0, 600),
      };
    });
  }

  /** Volume-weighted price across Coinbase, Kraken and Binance.US (port of aggregator.agg_price). */
  function exchangePrices(sym) {
    return cached(`agg:${sym}`, 60e3, async () => {
      const kb = KRAKEN_ALIAS[sym] || sym;
      const sources = [
        ['Coinbase', () => getJSON(`https://api.exchange.coinbase.com/products/${sym}-USD/ticker`, { retries: 0 }), (t) => [+t.price, +t.volume]],
        ['Kraken', async () => { const d = await getJSON(`https://api.kraken.com/0/public/Ticker?pair=${kb}USD`, { retries: 0 }); if (d.error?.length) throw new Error(d.error[0]); return Object.values(d.result)[0]; }, (t) => [+t.c[0], +t.v[1]]],
        ['Binance.US', () => getJSON(`https://api.binance.us/api/v3/ticker/24hr?symbol=${sym}USDT`, { retries: 0 }), (t) => [+t.lastPrice, +t.volume]],
      ];
      const rows = await Promise.all(sources.map(async ([exchange, call, parse]) => {
        try { const [price, volume] = parse(await call()); if (!(price > 0)) throw new Error('no price'); return { exchange, price, volume }; } catch (e) { return { exchange, error: e.message }; }
      }));
      const ok = rows.filter((r) => r.price);
      if (!ok.length) return { rows, vwap: null, spread: null };
      const w = ok.reduce((s, r) => s + Math.max(0, r.volume || 0), 0);
      const vwap = w > 0 ? ok.reduce((s, r) => s + r.price * Math.max(0, r.volume || 0), 0) / w : ok.reduce((s, r) => s + r.price, 0) / ok.length;
      const spread = ((Math.max(...ok.map((r) => r.price)) - Math.min(...ok.map((r) => r.price))) / vwap) * 100;
      return { rows, vwap, spread, sources: ok.length };
    });
  }

  /** Ticker -> CoinGecko id. Common tickers first, then loaded coins, then CoinGecko search. */
  async function resolveSymbol(sym) {
    const S = String(sym || '').trim().toUpperCase();
    if (!S) return null;
    if (SYMBOL_IDS[S]) return SYMBOL_IDS[S];
    const local = state.coins.filter((c) => c.symbol.toUpperCase() === S).sort((a, b) => (a.market_cap_rank ?? 1e9) - (b.market_cap_rank ?? 1e9))[0];
    if (local) return local.id;
    try {
      const r = await cached(`search:${S}`, DAY, () => cg(`/search?query=${encodeURIComponent(S)}`));
      const hit = (r.coins || []).filter((c) => c.symbol?.toUpperCase() === S).sort((a, b) => (a.market_cap_rank ?? 1e9) - (b.market_cap_rank ?? 1e9))[0];
      return hit?.id || null;
    } catch { return null; }
  }

  function trackedIds() {
    const ids = new Set([...state.watchlist, ...state.txs.map((t) => t.coinId), ...state.alerts.map((a) => a.coinId), 'bitcoin', 'ethereum', 'solana']);
    if (state.paperBot?.coinId) ids.add(state.paperBot.coinId);
    ids.delete(undefined); ids.delete(null);
    return ids;
  }

  async function fetchLive() {
    const cur = state.currency;
    const q = `vs_currency=${cur}&sparkline=true&price_change_percentage=1h,24h,7d,30d`;
    const top = await cg(`/coins/markets?${q}&order=market_cap_desc&per_page=100&page=1`);
    const have = new Set(top.map((c) => c.id));
    const missing = [...trackedIds()].filter((id) => !have.has(id));
    let extra = [];
    if (missing.length) {
      try { extra = await cg(`/coins/markets?${q}&ids=${missing.map(encodeURIComponent).join(',')}`); } catch { /* optional */ }
    }
    const rates = await cg('/exchange_rates').then((r) => r.rates).catch(() => state.rates);
    const global = await cg('/global').then((g) => g.data).catch(() => state.global);
    return { coins: [...top, ...extra], rates, global };
  }

  let refreshing = false;
  async function refresh({ manual = false } = {}) {
    if (refreshing) return;
    refreshing = true;
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
        if (manual) toast(`Couldn't reach CoinGecko (${err.message}). Showing saved prices.`, 'warn');
      } else if (state.mode !== 'live') {
        const wasDemo = state.mode === 'demo';
        applyData(Demo.data(state.currency), 'demo');
        if (manual || !wasDemo) toast('Live prices unavailable, so Mintline is showing sample prices', 'warn');
      }
    } finally {
      btn.classList.remove('spin');
      refreshing = false;
    }
  }

  const refreshHooks = [];
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
    refreshHooks.forEach((fn) => { try { fn(); } catch (e) { console.error(e); } });
  }

  // ---------- Demo data (used only when the API is unreachable) ----------
  const Demo = (() => {
    const seed = [
      ['bitcoin', 'Bitcoin', 'btc', 68000, 1.34e12, 21e6],
      ['ethereum', 'Ethereum', 'eth', 3500, 4.2e11, null],
      ['tether', 'Tether', 'usdt', 1, 1.1e11, null],
      ['binancecoin', 'BNB', 'bnb', 590, 8.7e10, 2e8],
      ['solana', 'Solana', 'sol', 165, 7.6e10, null],
      ['usd-coin', 'USDC', 'usdc', 1, 3.3e10, null],
      ['ripple', 'XRP', 'xrp', 0.55, 3.1e10, 1e11],
      ['dogecoin', 'Dogecoin', 'doge', 0.15, 2.2e10, null],
      ['the-open-network', 'Toncoin', 'ton', 6.8, 1.7e10, null],
      ['cardano', 'Cardano', 'ada', 0.45, 1.6e10, 4.5e10],
      ['avalanche-2', 'Avalanche', 'avax', 36, 1.4e10, 7.2e8],
      ['shiba-inu', 'Shiba Inu', 'shib', 0.000024, 1.4e10, null],
      ['tron', 'TRON', 'trx', 0.12, 1.05e10, null],
      ['polkadot', 'Polkadot', 'dot', 7.1, 1.0e10, null],
      ['chainlink', 'Chainlink', 'link', 15.5, 9.1e9, 1e9],
      ['bitcoin-cash', 'Bitcoin Cash', 'bch', 470, 9.2e9, 21e6],
      ['near', 'NEAR Protocol', 'near', 6.9, 7.4e9, null],
      ['litecoin', 'Litecoin', 'ltc', 82, 6.1e9, 8.4e7],
      ['uniswap', 'Uniswap', 'uni', 9.8, 5.9e9, 1e9],
      ['polygon-ecosystem-token', 'POL', 'pol', 0.62, 5.0e9, null],
    ];
    const fx = { usd: 1, eur: 0.92, gbp: 0.79, cad: 1.37, aud: 1.51, jpy: 151, btc: 1 / 68000 };
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
      const coins = seed.map(([id, name, symbol, usd, mcap, maxSupply], i) => {
        const stable = symbol === 'usdt' || symbol === 'usdc';
        const vol = stable ? 0.0005 : 0.008;
        const price = usd * k * (stable ? 1 : jitter());
        const spark = walk(id, 168, price, vol);
        const pct = (a, b) => ((b - a) / a) * 100;
        const circ = mcap / usd;
        return {
          id, name, symbol, image: null,
          current_price: price,
          market_cap: mcap * k, market_cap_rank: i + 1,
          fully_diluted_valuation: maxSupply ? maxSupply * price : mcap * k,
          total_volume: mcap * k * (0.02 + (i % 5) * 0.015),
          high_24h: Math.max(...spark.slice(-24)), low_24h: Math.min(...spark.slice(-24)),
          circulating_supply: circ, total_supply: null, max_supply: maxSupply,
          ath: price * 1.4, ath_change_percentage: -28.6,
          price_change_percentage_1h_in_currency: pct(spark[166], spark[167]),
          price_change_percentage_24h_in_currency: pct(spark[143], spark[167]),
          price_change_percentage_7d_in_currency: pct(spark[0], spark[167]),
          price_change_percentage_30d_in_currency: pct(spark[0], spark[167]) * 2.1,
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
      };
      return { coins, rates, global };
    }
    function chart(coin, days) {
      const n = days <= 1 ? 288 : days <= 90 ? Math.min(days * 24, 2160) : days;
      const vol = (coin.symbol === 'usdt' || coin.symbol === 'usdc') ? 0.0005 : days > 90 ? 0.03 : 0.008;
      const pts = walk(coin.id + days, n, coin.current_price, vol);
      const step = (days * DAY) / pts.length;
      const now = Date.now();
      return pts.map((p, i) => [now - (pts.length - 1 - i) * step, p]);
    }
    return { data, chart };
  })();

  // ---------- Rendering: markets ----------
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
    const labels = { live: 'Live', cached: 'Saved prices', demo: 'Sample data', loading: 'Loading…' };
    el.className = `status ${state.mode === 'live' ? 'live' : state.mode === 'demo' ? 'demo' : state.mode === 'cached' ? 'offline' : ''}`;
    el.innerHTML = `<span>${labels[state.mode]}</span>`;
    $('#updated').textContent = state.updatedAt ? `Updated ${new Date(state.updatedAt).toLocaleTimeString()}` : '';
  }

  function renderGlobal() {
    const g = state.global;
    if (!g) { $('#global').innerHTML = ''; return; }
    const cur = state.currency;
    $('#global').innerHTML = `
      <span>Market cap <b>${fmtCompact(g.total_market_cap?.[cur])}</b> ${fmtPct(g.market_cap_change_percentage_24h_usd)}</span>
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

  function searchFilter(list) {
    const q = $('#search').value.trim().toLowerCase();
    return q ? list.filter((c) => c.name.toLowerCase().includes(q) || c.symbol.toLowerCase().includes(q)) : list;
  }

  function renderMarkets(prevMap) {
    const screener = state.marketsView === 'screener';
    $('#prices-wrap').hidden = screener;
    $('#screener-wrap').hidden = !screener;
    $('#sort').hidden = screener;
    $('#open-compare').hidden = !screener;
    if (screener) { renderScreener(); return; }
    const list = searchFilter(state.coins);
    const body = $('#markets-body');
    if (!list.length) {
      body.innerHTML = `<tr><td colspan="9" class="empty">${state.mode === 'loading' ? 'Loading prices…' : 'No coins match your search.'}</td></tr>`;
      return;
    }
    body.innerHTML = sortedCoins(list).map((c) => coinRow(c, prevMap)).join('');
  }

  // Screener: Messari-style derived ratios (port of research.screener).
  const SCREENER_COLS = [
    { key: 'rank', label: '#', get: (c) => c.market_cap_rank, fmt: (v) => v ?? '—', cls: 'num-col' },
    { key: 'name', label: 'Coin', get: (c) => c.name.toLowerCase(), cell: (c) => `<div class="coin-cell">${coinIcon(c, 20)}<span class="coin-name">${esc(c.name)}</span><span class="coin-sym">${esc(c.symbol)}</span></div>` },
    { key: 'price', label: 'Price', get: (c) => c.current_price, fmt: (v) => fmtMoney(v), r: true },
    { key: 'mcap', label: 'Market cap', get: (c) => c.market_cap, fmt: (v) => fmtCompact(v), r: true },
    { key: 'fdv', label: 'FDV', get: (c) => c.fully_diluted_valuation, fmt: (v) => fmtCompact(v), r: true, hide: 'hide-sm' },
    { key: 'mcapFdv', label: 'Mcap ÷ FDV', get: (c) => (c.market_cap && c.fully_diluted_valuation ? c.market_cap / c.fully_diluted_valuation : null), fmt: (v) => (v == null ? '—' : v.toFixed(2)), r: true },
    { key: 'volMcap', label: 'Vol ÷ Mcap', get: (c) => (c.total_volume && c.market_cap ? c.total_volume / c.market_cap : null), fmt: (v) => (v == null ? '—' : v.toFixed(3)), r: true, hide: 'hide-sm' },
    { key: 'issued', label: 'Supply issued', get: (c) => (c.circulating_supply && c.max_supply ? (c.circulating_supply / c.max_supply) * 100 : null), fmt: (v) => (v == null ? '—' : `${v.toFixed(1)}%`), r: true, hide: 'hide-md' },
    { key: 'ath', label: 'From ATH', get: (c) => c.ath_change_percentage, fmt: (v) => fmtPct(v, 1), r: true, hide: 'hide-md' },
    { key: 'c24', label: '24h', get: (c) => c.price_change_percentage_24h_in_currency, fmt: (v) => fmtPct(v, 1), r: true },
    { key: 'c7', label: '7d', get: (c) => c.price_change_percentage_7d_in_currency, fmt: (v) => fmtPct(v, 1), r: true, hide: 'hide-sm' },
    { key: 'c30', label: '30d', get: (c) => c.price_change_percentage_30d_in_currency, fmt: (v) => fmtPct(v, 1), r: true, hide: 'hide-md' },
  ];
  function renderScreener() {
    const { key, dir } = state.screenerSort;
    const col = SCREENER_COLS.find((c) => c.key === key) || SCREENER_COLS[0];
    $('#screener-head').innerHTML = `<tr>${SCREENER_COLS.map((c) => `<th class="${c.r ? 'r ' : ''}${c.hide || ''} ${c.cls || ''} sortable" data-sort="${c.key}" aria-sort="${c.key === key ? (dir > 0 ? 'ascending' : 'descending') : 'none'}">${esc(c.label)}${c.key === key ? (dir > 0 ? ' ▲' : ' ▼') : ''}</th>`).join('')}</tr>`;
    const list = searchFilter(state.coins).slice().sort((a, b) => {
      const va = col.get(a), vb = col.get(b);
      if (va == null && vb == null) return 0;
      if (va == null) return 1;
      if (vb == null) return -1;
      return (va > vb ? 1 : va < vb ? -1 : 0) * dir;
    });
    $('#screener-body').innerHTML = list.map((c) => `<tr data-id="${esc(c.id)}">${SCREENER_COLS.map((k) => `<td class="${k.r ? 'r ' : ''}${k.hide || ''} ${k.cls || ''}">${k.cell ? k.cell(c) : k.fmt(k.get(c))}</td>`).join('')}</tr>`).join('')
      || `<tr><td colspan="${SCREENER_COLS.length}" class="empty">No coins match your search.</td></tr>`;
  }

  function renderWatchlist(prevMap) {
    const list = state.watchlist.map((id) => state.coinMap.get(id)).filter(Boolean);
    $('#watchlist-body').innerHTML = sortedCoins(list).map((c) => coinRow(c, prevMap)).join('');
    $('#watchlist-empty').hidden = list.length > 0;
  }

  // ---------- Portfolio & taxes (lot accounting from engine.js) ----------
  function tradesIn(cur, txs = state.txs) {
    let approx = false;
    const trades = txs.map((t) => {
      const price = convert(t.price, t.cur, cur), fee = convert(t.fee || 0, t.cur, cur);
      if (t.cur !== cur) approx = true;
      return { date: t.date, type: t.type, asset: t.coinId, quantity: t.amount, price: price ?? 0, fee: fee ?? 0 };
    });
    return { trades, approx };
  }

  /** Holdings and realized gains in `cur`, priced at live prices. */
  function portfolioIn(cur = state.currency, method = state.settings.taxMethod, txs = state.txs) {
    const { trades, approx } = tradesIn(cur, txs);
    let res;
    try { res = E.computeLots(trades, method); } catch (err) {
      const msg = err.message.replace(/^(\S+): selling (\S+) (\S+) but holdings run out.*$/, (_, d, q, id) => `on ${d} you'd be selling ${fmtNum(+q)} ${symbolOf(id)}, more than you held then`);
      return { error: msg, rows: [], realized: [], income: [], approx };
    }
    const prices = {};
    for (const id of Object.keys(res.lots)) {
      const c = state.coinMap.get(id);
      if (c) prices[id] = convert(c.current_price, state.currency, cur);
    }
    const rows = E.holdings(res.lots, prices).map((r) => ({ ...r, coinId: r.asset, symbol: symbolOf(r.asset), coin: state.coinMap.get(r.asset) }));
    return { ...res, rows, approx };
  }

  const PALETTE = ['#3ee6a8', '#5aa9ff', '#ffc857', '#ff6b7a', '#b48cff', '#4dd6e8', '#ff9f5a', '#9fe36b', '#f78fd0', '#8aa39b'];

  function renderPortfolio() {
    const pf = portfolioIn();
    const errEl = $('#pf-error');
    errEl.hidden = !pf.error;
    if (pf.error) errEl.textContent = `Your transactions don't add up: ${pf.error}. Add the missing buy, or remove the sale.`;
    const rows = pf.rows;
    const total = rows.reduce((a, r) => a + (r.value ?? 0), 0);
    const total24 = rows.reduce((a, r) => {
      const ch = r.coin?.price_change_percentage_24h_in_currency ?? 0;
      return a + (r.value != null ? r.value / (1 + ch / 100) : 0);
    }, 0);
    const cost = rows.reduce((a, r) => a + r.costBasis, 0);
    const realized = pf.realized.reduce((a, r) => a + r.gainLoss, 0);
    const pl = total - cost + realized;
    const everInvested = cost + pf.realized.reduce((a, r) => a + r.costBasis, 0);
    const any = state.txs.length > 0;

    $('#pf-value').textContent = any ? fmtMoney(total) : '—';
    const d24 = total - total24;
    $('#pf-24h').innerHTML = any ? `${signed(d24)} <div class="sub">${fmtPct(total24 ? (d24 / total24) * 100 : 0)}</div>` : '—';
    $('#pf-pl').innerHTML = any ? `${signed(pl)} <div class="sub">${fmtPct(everInvested ? (pl / everInvested) * 100 : 0)} · realized ${signed(realized)}</div>` : '—';
    $('#pf-cost').textContent = any ? fmtMoney(cost) : '—';

    $('#holdings-body').innerHTML = rows.map((r) => {
      const c = r.coin || { id: r.coinId, name: nameOf(r.coinId), symbol: r.symbol };
      return `<tr data-id="${esc(r.coinId)}" class="clickable">
        <td><div class="coin-cell">${coinIcon(c)}<div><div class="coin-name">${esc(c.name)}</div><div class="sub">${r.allocationPct.toFixed(1)}% of portfolio</div></div></div></td>
        <td class="r">${fmtMoney(r.price)}<div class="sub">${fmtPct(c.price_change_percentage_24h_in_currency)}</div></td>
        <td class="r">${fmtMoney(r.value)}<div class="sub">${fmtNum(r.quantity)} ${esc(r.symbol)}</div></td>
        <td class="r hide-sm">${fmtMoney(r.costBasis / r.quantity)}</td>
        <td class="r">${signed(r.unrealized)}<div class="sub">${r.unrealizedPct != null ? fmtPct(r.unrealizedPct) : ''}</div></td>
      </tr>`;
    }).join('');
    $('#holdings-empty').hidden = rows.length > 0;
    $('#tax-method').value = state.settings.taxMethod;

    renderAllocation(rows, total);
    renderTax();
    renderTxs();
  }

  function renderAllocation(rows, total) {
    const alloc = $('#allocation');
    if (!rows.length || total <= 0) { alloc.innerHTML = '<p class="empty">Nothing to show yet.</p>'; return; }
    let slices = rows.map((r) => ({ name: r.coin?.name || nameOf(r.coinId), sym: r.symbol, v: r.value ?? 0 }));
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

  function taxData() {
    // Tax figures are always in USD, as on Form 8949.
    const pf = portfolioIn('usd');
    const years = new Set([new Date().getUTCFullYear(), ...pf.realized.map((r) => new Date(r.dateSold).getUTCFullYear()), ...pf.income.map((r) => new Date(r.date).getUTCFullYear())]);
    return { pf, years: [...years].sort((a, b) => b - a) };
  }

  function renderTax() {
    const { pf, years } = taxData();
    const sel = $('#tax-year');
    if (!state.taxYear || !years.includes(state.taxYear)) {
      const withSales = years.find((y) => pf.realized.some((r) => new Date(r.dateSold).getUTCFullYear() === y));
      state.taxYear = withSales || years[0];
    }
    sel.innerHTML = years.map((y) => `<option value="${y}" ${y === state.taxYear ? 'selected' : ''}>${y}</option>`).join('');
    if (pf.error) { $('#tax-summary').innerHTML = '<p class="muted small">Fix the transaction problem above to see your tax figures.</p>'; $('#realized-body').innerHTML = ''; $('#realized-empty').hidden = true; return; }
    const s = E.taxSummary(pf.realized, pf.income, state.taxYear);
    const stat = (l, v) => `<div><div class="label">${l}</div><div class="val">${v}</div></div>`;
    $('#tax-summary').innerHTML = [
      stat('Short-term gain', signed(s.shortTermGain, fmtUsd)),
      stat('Long-term gain', signed(s.longTermGain, fmtUsd)),
      stat('Total realized', signed(s.totalRealized, fmtUsd)),
      stat('Income (staking, airdrops)', fmtUsd(s.income)),
      stat('Sales', s.disposals),
    ].join('');
    const rows = pf.realized.filter((r) => new Date(r.dateSold).getUTCFullYear() === state.taxYear);
    $('#realized-body').innerHTML = rows.map((r) => `<tr>
      <td>${isoDay(r.dateSold)}</td><td>${esc(symbolOf(r.asset))}</td><td class="r">${fmtNum(r.quantity)}</td><td class="hide-sm">${isoDay(r.dateAcquired)}</td>
      <td class="r">${fmtUsd(r.proceeds)}</td><td class="r">${fmtUsd(r.costBasis)}</td><td class="r">${signed(r.gainLoss, fmtUsd)}</td>
      <td><span class="pill ${r.term === 'long' ? 'on' : ''}">${r.term === 'long' ? 'Long' : 'Short'}</span></td></tr>`).join('');
    $('#realized-empty').hidden = rows.length > 0;
    $('#tax-note').textContent = `Method: ${state.settings.taxMethod}. Held more than 365 days counts as long term.${pf.approx ? ' Some transactions were entered in another currency and are converted to USD at today\'s rate, so check those figures.' : ''} This is a calculator, not tax advice. Have a CPA review it before you file.`;
  }

  const TYPE_LABELS = { buy: 'Buy', sell: 'Sell', income: 'Income', gift_in: 'Gift in', spend: 'Spend', transfer: 'Transfer' };
  function renderTxs() {
    const list = [...state.txs].sort((a, b) => b.date - a.date);
    $('#tx-body').innerHTML = list.map((t) => `<tr>
      <td>${isoDay(t.date)}</td>
      <td><span class="pill tx-${t.type}">${TYPE_LABELS[t.type] || t.type}</span></td>
      <td>${esc(symbolOf(t.coinId))}</td>
      <td class="r">${fmtNum(t.amount)}</td>
      <td class="r">${t.type === 'transfer' ? '—' : fmtMoney(t.price, t.cur)}</td>
      <td class="r hide-sm">${t.fee ? fmtMoney(t.fee, t.cur) : '—'}</td>
      <td class="hide-md muted small">${esc([t.exchange, t.notes].filter(Boolean).join(' · '))}</td>
      <td class="r"><button class="del" data-del-tx="${esc(t.id)}" aria-label="Delete transaction" title="Delete">✕</button></td>
    </tr>`).join('');
    $('#tx-empty').hidden = list.length > 0;
  }

  /** USD holdings for the mentor: [{symbol, costBasis, value, allocationPct}]. */
  function portfolioUsd() {
    const pf = portfolioIn('usd', 'FIFO');
    return pf.error ? null : pf.rows.map((r) => ({ symbol: r.symbol, costBasis: r.costBasis, value: r.value || 0, allocationPct: r.allocationPct }));
  }

  // ---------- Alerts (port of alerts.py) ----------
  const RULES = {
    price_above: { coin: true, value: 'price' }, price_below: { coin: true, value: 'price' },
    change_24h_above: { coin: true, value: '%' }, change_24h_below: { coin: true, value: '%' },
    rsi_above: { coin: true, value: 'rsi', ind: true, period: 14, interval: '1h' },
    rsi_below: { coin: true, value: 'rsi', ind: true, period: 14, interval: '1h' },
    cross_above_sma: { coin: true, ind: true, period: 200, interval: '1d' },
    cross_below_sma: { coin: true, ind: true, period: 200, interval: '1d' },
    fear_greed_above: { value: 'index' }, fear_greed_below: { value: 'index' },
    funding_apr_above: { value: '%', contract: true },
  };

  function describeRule(a) {
    const sym = symbolOf(a.coinId);
    const p = a.period ?? RULES[a.type]?.period, iv = a.interval ?? RULES[a.type]?.interval;
    switch (a.type) {
      case 'price_above': return `${sym} price above ${fmtMoney(a.value, a.cur)}`;
      case 'price_below': return `${sym} price below ${fmtMoney(a.value, a.cur)}`;
      case 'change_24h_above': return `${sym} 24h change above ${a.value}%`;
      case 'change_24h_below': return `${sym} 24h change below ${a.value}%`;
      case 'rsi_above': return `${sym} RSI(${p}, ${iv}) above ${a.value}`;
      case 'rsi_below': return `${sym} RSI(${p}, ${iv}) below ${a.value}`;
      case 'cross_above_sma': return `${sym} crosses above its ${p}-candle average (${iv})`;
      case 'cross_below_sma': return `${sym} crosses below its ${p}-candle average (${iv})`;
      case 'fear_greed_above': return `Fear & Greed above ${a.value}`;
      case 'fear_greed_below': return `Fear & Greed below ${a.value}`;
      case 'funding_apr_above': return `${a.contract || 'PF_XBTUSD'} funding above ${a.value}% a year`;
      default: return a.type;
    }
  }

  /** Returns {hit, msg}. Same conditions as the toolkit's evaluate(). */
  async function evaluate(a) {
    const sym = symbolOf(a.coinId), v = a.value, t = a.type;
    if (t.startsWith('price_') || t.startsWith('change_24h')) {
      const c = state.coinMap.get(a.coinId);
      if (!c) throw new Error('no price for this coin yet');
      if (t.startsWith('price_')) {
        const px = convert(c.current_price, state.currency, a.cur);
        if (px == null) throw new Error('exchange rates unavailable');
        const hit = t === 'price_above' ? px > v : px < v;
        return { hit, msg: `${sym} price ${fmtMoney(px, a.cur)} (trigger: ${t === 'price_above' ? 'above' : 'below'} ${fmtMoney(v, a.cur)})` };
      }
      const ch = c.price_change_percentage_24h_in_currency ?? c.price_change_percentage_24h;
      if (ch == null) throw new Error('no 24h change available');
      const hit = t === 'change_24h_above' ? ch > v : ch < v;
      return { hit, msg: `${sym} 24h change ${ch >= 0 ? '+' : ''}${ch.toFixed(2)}% (trigger: ${t === 'change_24h_above' ? 'above' : 'below'} ${v}%)` };
    }
    if (t.startsWith('rsi_')) {
      const period = a.period || 14, iv = a.interval || '1h';
      const r = TA.last(TA.rsi(await closes(a.coinId, iv), period));
      if (r == null) throw new Error('not enough price history');
      const hit = t === 'rsi_above' ? r > v : r < v;
      return { hit, msg: `${sym} RSI(${period}, ${iv}) = ${r.toFixed(1)} (trigger: ${t === 'rsi_above' ? 'above' : 'below'} ${v})` };
    }
    if (t.startsWith('cross_')) {
      const n = a.period || 200, iv = a.interval || '1d';
      const c = await closes(a.coinId, iv);
      const s = TA.sma(c, n);
      const L = c.length;
      if (L < 2 || s[L - 2] == null) throw new Error(`needs more than ${n} candles of history`);
      const prevAbove = c[L - 2] > s[L - 2], nowAbove = c[L - 1] > s[L - 1];
      const hit = t === 'cross_above_sma' ? !prevAbove && nowAbove : prevAbove && !nowAbove;
      return { hit, msg: `${sym} close ${fmtUsd(c[L - 1])} vs SMA${n} ${fmtUsd(s[L - 1])} (trigger: fresh cross ${t === 'cross_above_sma' ? 'above' : 'below'})` };
    }
    if (t.startsWith('fear_greed_')) {
      const fg = (await fearGreed(1)).at(-1);
      const hit = t === 'fear_greed_below' ? fg.value < v : fg.value > v;
      return { hit, msg: `Fear & Greed = ${fg.value} (${fg.label}) (trigger: ${t === 'fear_greed_below' ? 'below' : 'above'} ${v})` };
    }
    if (t === 'funding_apr_above') {
      const contract = a.contract || 'PF_XBTUSD';
      const row = (await krakenFutures()).find((x) => x.symbol === contract);
      if (!row) throw new Error(`Kraken has no contract called ${contract}`);
      const apr = row.relativeFundingRate * 24 * 365 * 100;
      return { hit: apr > v, msg: `${contract} funding ${apr.toFixed(1)}% APR (trigger: above ${v}%)` };
    }
    throw new Error(`Unknown rule type: ${t}`);
  }

  let checking = false;
  async function checkAlerts({ manual = false } = {}) {
    // Alerts only fire against real prices, never sample data.
    if (state.mode !== 'live') {
      if (manual) toast('Alerts need live prices. Mintline will check as soon as it is back online.', 'warn');
      return;
    }
    if (checking) return;
    checking = true;
    try {
      for (const a of state.alerts) {
        if (!a.enabled) continue;
        try {
          const { hit, msg } = await evaluate(a);
          a.lastMsg = msg; a.error = null; a.lastCheck = Date.now(); a.lastHit = hit;
          const cooldown = (a.cooldown ?? 60) * 60e3;
          if (hit && Date.now() - (a.lastFired || 0) >= cooldown) {
            a.lastFired = Date.now();
            notifyAll(`Crypto alert: ${a.name || describeRule(a)}`, msg, state.coinMap.get(a.coinId)?.image);
          }
        } catch (err) {
          a.error = err.message; a.lastCheck = Date.now();
        }
      }
      persist();
    } finally {
      checking = false;
      renderAlerts();
    }
  }

  const ago = (ms) => {
    const m = Math.round((Date.now() - ms) / 60e3);
    return m < 1 ? 'just now' : m < 60 ? `${m} min ago` : m < 1440 ? `${Math.round(m / 60)} h ago` : `${Math.round(m / 1440)} d ago`;
  };

  function renderAlerts() {
    const list = $('#alerts-list');
    const items = [...state.alerts].sort((a, b) => (b.enabled - a.enabled) || (b.createdAt || 0) - (a.createdAt || 0));
    list.innerHTML = items.map((a) => {
      const c = state.coinMap.get(a.coinId) || { symbol: a.type.startsWith('fear') ? 'F&G' : a.type.startsWith('funding') ? 'FUT' : symbolOf(a.coinId) };
      const quietFor = a.lastFired ? (a.cooldown ?? 60) * 60e3 - (Date.now() - a.lastFired) : 0;
      let pill = '<span class="pill on">Watching</span>';
      if (!a.enabled) pill = '<span class="pill">Paused</span>';
      else if (a.error) pill = '<span class="pill warn">Can\'t check</span>';
      else if (quietFor > 0) pill = `<span class="pill hit">Fired ${ago(a.lastFired)}</span>`;
      const meta = a.error ? `Couldn't check: ${esc(a.error)}` : a.lastMsg ? esc(a.lastMsg) : state.mode === 'live' ? 'Checking…' : 'Waiting for live prices';
      return `<li class="${a.enabled ? '' : 'paused'}">
        ${coinIcon(c, 28)}
        <div class="info">
          <div class="cond">${esc(a.name || describeRule(a))}</div>
          <div class="meta">${a.name ? `${esc(describeRule(a))} · ` : ''}${meta}${quietFor > 0 && a.enabled ? ` · quiet for ${Math.ceil(quietFor / 60e3)} more min` : ''}</div>
        </div>
        ${pill}
        <button class="btn ghost small-btn" data-toggle-alert="${esc(a.id)}">${a.enabled ? 'Pause' : 'Resume'}</button>
        <button class="del" data-del-alert="${esc(a.id)}" aria-label="Delete alert">✕</button>
      </li>`;
    }).join('');
    $('#alerts-empty').hidden = items.length > 0;
    const active = state.alerts.filter((a) => a.enabled).length;
    const badge = $('#alert-badge');
    badge.hidden = !active;
    badge.textContent = active;
    const btn = $('#enable-notif');
    if (!('Notification' in window)) btn.hidden = true;
    else if (Notification.permission === 'granted') { btn.textContent = 'Notifications on'; btn.disabled = true; }
    else if (Notification.permission === 'denied') { btn.textContent = 'Notifications blocked'; btn.disabled = true; }
  }

  async function importRules(json) {
    const rules = Array.isArray(json) ? json : json?.alerts;
    if (!Array.isArray(rules)) throw new Error('expected {"alerts": [...]}');
    let added = 0;
    const skipped = [];
    for (const r of rules) {
      const meta = RULES[r.type];
      if (!meta) { skipped.push(`${r.name || r.type} (unknown type)`); continue; }
      let coinId = null;
      if (meta.coin) {
        coinId = await resolveSymbol(r.symbol || 'BTC');
        if (!coinId) { skipped.push(`${r.name || r.type} (unknown coin ${r.symbol})`); continue; }
      }
      const rule = { id: uid(), name: r.name || '', type: r.type, coinId, contract: meta.contract ? r.symbol || 'PF_XBTUSD' : undefined,
        value: r.value != null ? +r.value : null, period: r.period != null ? +r.period : meta.period, interval: r.interval || meta.interval,
        cooldown: r.cooldown_minutes != null ? +r.cooldown_minutes : 60, cur: 'usd', enabled: true, createdAt: Date.now() };
      const i = rule.name ? state.alerts.findIndex((a) => a.name === rule.name) : -1;
      if (i >= 0) state.alerts[i] = rule; else state.alerts.push(rule);
      added++;
    }
    persist();
    refresh();
    return { added, skipped };
  }

  function exportRules() {
    const alerts = state.alerts.map((a) => {
      const meta = RULES[a.type] || {};
      const o = { name: a.name || describeRule(a), type: a.type };
      if (meta.coin) o.symbol = symbolOf(a.coinId);
      if (meta.contract) o.symbol = a.contract || 'PF_XBTUSD';
      if (meta.value) o.value = meta.value === 'price' ? +(convert(a.value, a.cur, 'usd') ?? a.value).toPrecision(8) : a.value;
      if (meta.ind) { o.period = a.period ?? meta.period; o.interval = a.interval ?? meta.interval; }
      if ((a.cooldown ?? 60) !== 60) o.cooldown_minutes = a.cooldown;
      return o;
    });
    return JSON.stringify({ alerts }, null, 2) + '\n';
  }

  // ---------- Notifications: in-app, system, ntfy phone push, Slack/Discord ----------
  async function notifyAll(title, body, icon) {
    toast(`🔔 ${title}: ${body}`);
    if ('Notification' in window && Notification.permission === 'granted') {
      const opts = { body, icon: icon || 'icons/icon-192.png', badge: 'icons/icon-192.png', tag: `mintline-${Date.now()}` };
      try {
        const reg = await navigator.serviceWorker?.getRegistration();
        if (reg) reg.showNotification(title, opts); else new Notification(title, opts);
      } catch { /* ignore */ }
    }
    const topic = state.settings.ntfyTopic?.trim();
    if (topic) {
      // Title as a query parameter keeps this a simple CORS request.
      fetch(`https://ntfy.sh/${encodeURIComponent(topic)}?title=${encodeURIComponent(title)}`, { method: 'POST', body }).catch(() => toast('Couldn\'t send the phone alert through ntfy', 'warn'));
    }
    const hook = state.settings.webhook?.trim();
    if (hook) {
      // Webhooks don't allow browser CORS, so send a form post the services accept without reading the reply.
      const isDiscord = /discord(app)?\.com\/api\/webhooks/.test(hook);
      const form = new URLSearchParams(isDiscord ? { content: `**${title}**\n${body}` } : { payload: JSON.stringify({ text: `*${title}*\n${body}` }) });
      fetch(hook, { method: 'POST', mode: 'no-cors', body: form }).catch(() => {});
    }
  }

  // ---------- Coin detail ----------
  function openDetail(id) {
    state.detail.id = id;
    renderDetailHeader();
    $('#detail-exchanges-wrap').open = false;
    $('#detail-research-wrap').open = false;
    $('#detail-exchanges').innerHTML = '';
    $('#detail-research').innerHTML = '';
    $('#detail-ta').innerHTML = '';
    $('#detail').showModal();
    loadChart();
    loadTaNotes(id);
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
    $('#detail-star').textContent = state.watchlist.includes(c.id) ? '★ Watching' : '☆ Watch';
    $$('#ind-toggles button').forEach((b) => b.classList.toggle('active', state.indicators.includes(b.dataset.ind)));
  }

  // Extra history before the visible range so long averages are warmed up.
  const FETCH_DAYS = { 1: 1, 7: 30, 30: 90, 90: 90, 365: 365 };
  async function loadChart() {
    const { id, days } = state.detail;
    const el = $('#chart');
    $$('#ranges button').forEach((b) => b.classList.toggle('active', +b.dataset.days === days));
    el.innerHTML = '<div class="loading">Loading chart…</div>';
    let pts;
    try {
      pts = await priceHistory(id, FETCH_DAYS[days] || days);
    } catch (err) {
      const c = state.coinMap.get(id);
      pts = c?.sparkline_in_7d?.price && days === 7
        ? (() => { const s = c.sparkline_in_7d.price, step = (7 * DAY) / s.length, now = Date.now(); return s.map((p, i) => [now - (s.length - 1 - i) * step, p]); })()
        : null;
      if (!pts) { if (state.detail.id === id) el.innerHTML = `<div class="loading">Couldn't load the chart: ${esc(err.message)}</div>`; return; }
    }
    if (state.detail.id !== id || state.detail.days !== days) return;
    drawChart(el, pts, days);
  }

  const IND_COLORS = { sma50: 'var(--ind-1)', sma200: 'var(--ind-2)', bb: 'var(--ind-3)', macd: 'var(--ind-1)', signal: 'var(--ind-4)', rsi: 'var(--ind-3)' };

  function drawChart(el, allPts, days) {
    if (!allPts?.length) { el.innerHTML = '<div class="loading">No chart data</div>'; return; }
    const on = new Set(state.indicators);
    const values = allPts.map((p) => p[1]);
    const ind = {
      sma50: on.has('sma50') ? TA.sma(values, 50) : null,
      sma200: on.has('sma200') ? TA.sma(values, 200) : null,
      bb: on.has('bb') ? TA.bollinger(values, 20, 2) : null,
      rsi: on.has('rsi') ? TA.rsi(values, 14) : null,
      macd: on.has('macd') ? TA.macd(values) : null,
    };
    const tEnd = allPts[allPts.length - 1][0];
    let start = allPts.findIndex((p) => p[0] >= tEnd - days * DAY);
    if (start < 0 || allPts.length - start < 2) start = 0;
    const idx = [];
    for (let i = start; i < allPts.length; i++) idx.push(i);
    const pts = idx.map((i) => allPts[i]);
    const candle = days <= 1 ? '5-minute' : FETCH_DAYS[days] <= 90 ? 'hourly' : 'daily';
    const legend = [];
    if (ind.sma50) legend.push(['SMA 50', IND_COLORS.sma50]);
    if (ind.sma200) legend.push(['SMA 200', IND_COLORS.sma200]);
    if (ind.bb) legend.push(['Bollinger 20, 2σ', IND_COLORS.bb]);
    $('#chart-legend').innerHTML = (legend.length || ind.rsi || ind.macd)
      ? `${legend.map(([l, c]) => `<span><i style="background:${c}"></i>${l}</span>`).join('')}<span class="muted">Indicators use ${candle} prices</span>`
      : '';

    const panels = [{ key: 'main', h: 240 }];
    if (ind.rsi) panels.push({ key: 'rsi', h: 80 });
    if (ind.macd) panels.push({ key: 'macd', h: 90 });
    const gap = 16, padL = 8, padR = 64, padT = 10, padB = 24;
    const W = el.clientWidth || 640;
    const H = padT + panels.reduce((s, p) => s + p.h, 0) + gap * (panels.length - 1) + padB;
    el.style.height = `${H}px`;
    let yOff = padT;
    for (const p of panels) { p.y0 = yOff; yOff += p.h + gap; }

    const x0 = pts[0][0], x1 = pts[pts.length - 1][0];
    const X = (x) => padL + ((x - x0) / (x1 - x0 || 1)) * (W - padL - padR);
    const pathOf = (series, Y) => {
      let d = '', pen = false;
      idx.forEach((i) => {
        const v = series[i];
        if (v == null) { pen = false; return; }
        d += `${pen ? 'L' : 'M'}${X(allPts[i][0]).toFixed(1)},${Y(v).toFixed(1)}`;
        pen = true;
      });
      return d;
    };
    let svg = '';

    // Main price panel
    const main = panels[0];
    const visible = (s) => idx.map((i) => s[i]).filter((v) => v != null);
    const yVals = [...pts.map((p) => p[1])];
    if (ind.sma50) yVals.push(...visible(ind.sma50));
    if (ind.sma200) yVals.push(...visible(ind.sma200));
    if (ind.bb) yVals.push(...visible(ind.bb.upper), ...visible(ind.bb.lower));
    let y0 = Math.min(...yVals), y1 = Math.max(...yVals);
    const padY = (y1 - y0) * 0.08 || y1 * 0.01 || 1; y0 -= padY; y1 += padY;
    const Y = (y) => main.y0 + (1 - (y - y0) / (y1 - y0)) * main.h;
    const up = pts[pts.length - 1][1] >= pts[0][1];
    const color = up ? 'var(--up)' : 'var(--down)';
    for (let i = 0; i <= 4; i++) {
      const v = y0 + ((y1 - y0) * i) / 4, y = Y(v);
      svg += `<line x1="${padL}" x2="${W - padR}" y1="${y}" y2="${y}" stroke="var(--line)" stroke-dasharray="2 4"/>`;
      svg += `<text x="${W - padR + 6}" y="${y + 4}" fill="var(--muted)" font-size="11">${esc(fmtMoney(v, state.currency, { compact: Math.abs(v) >= 1e5 }))}</text>`;
    }
    if (ind.bb) {
      const up2 = pathOf(ind.bb.upper, Y), lo2 = pathOf(ind.bb.lower, Y);
      svg += `<path d="${up2}" fill="none" stroke="${IND_COLORS.bb}" stroke-width="1" stroke-dasharray="3 3"/><path d="${lo2}" fill="none" stroke="${IND_COLORS.bb}" stroke-width="1" stroke-dasharray="3 3"/>`;
    }
    const line = pts.map((p, i) => `${i ? 'L' : 'M'}${X(p[0]).toFixed(1)},${Y(p[1]).toFixed(1)}`).join('');
    const area = `${line}L${X(x1).toFixed(1)},${main.y0 + main.h}L${X(x0).toFixed(1)},${main.y0 + main.h}Z`;
    svg += `<defs><linearGradient id="g" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="${color}" stop-opacity=".25"/><stop offset="1" stop-color="${color}" stop-opacity="0"/></linearGradient></defs>`;
    svg += `<path d="${area}" fill="url(#g)"/><path d="${line}" fill="none" stroke="${color}" stroke-width="2"/>`;
    if (ind.sma50) svg += `<path d="${pathOf(ind.sma50, Y)}" fill="none" stroke="${IND_COLORS.sma50}" stroke-width="1.5"/>`;
    if (ind.sma200) svg += `<path d="${pathOf(ind.sma200, Y)}" fill="none" stroke="${IND_COLORS.sma200}" stroke-width="1.5"/>`;

    // RSI panel
    const rp = panels.find((p) => p.key === 'rsi');
    let YR = null;
    if (rp) {
      YR = (v) => rp.y0 + (1 - v / 100) * rp.h;
      svg += `<rect x="${padL}" y="${YR(70)}" width="${W - padL - padR}" height="${YR(30) - YR(70)}" fill="var(--panel-2)"/>`;
      for (const lvl of [30, 70]) svg += `<line x1="${padL}" x2="${W - padR}" y1="${YR(lvl)}" y2="${YR(lvl)}" stroke="var(--line)" stroke-dasharray="3 3"/><text x="${W - padR + 6}" y="${YR(lvl) + 4}" fill="var(--muted)" font-size="11">${lvl}</text>`;
      svg += `<text x="${padL + 4}" y="${rp.y0 + 12}" fill="var(--muted)" font-size="11">RSI 14</text>`;
      svg += `<path d="${pathOf(ind.rsi, YR)}" fill="none" stroke="${IND_COLORS.rsi}" stroke-width="1.5"/>`;
    }
    // MACD panel
    const mp = panels.find((p) => p.key === 'macd');
    let YM = null;
    if (mp) {
      const mv = [...visible(ind.macd.macd), ...visible(ind.macd.signal), ...visible(ind.macd.hist)];
      const m = Math.max(...mv.map(Math.abs), 1e-12);
      YM = (v) => mp.y0 + mp.h / 2 - (v / m) * (mp.h / 2 - 4);
      svg += `<line x1="${padL}" x2="${W - padR}" y1="${YM(0)}" y2="${YM(0)}" stroke="var(--line)"/>`;
      svg += `<text x="${padL + 4}" y="${mp.y0 + 12}" fill="var(--muted)" font-size="11">MACD 12, 26, 9</text>`;
      const bw = Math.max(1, ((W - padL - padR) / idx.length) * 0.7);
      idx.forEach((i) => {
        const h = ind.macd.hist[i];
        if (h == null) return;
        const yA = YM(Math.max(h, 0)), yB = YM(Math.min(h, 0));
        svg += `<rect x="${(X(allPts[i][0]) - bw / 2).toFixed(1)}" y="${yA.toFixed(1)}" width="${bw.toFixed(1)}" height="${Math.max(0.5, yB - yA).toFixed(1)}" fill="${h >= 0 ? 'var(--up)' : 'var(--down)'}" opacity=".55"/>`;
      });
      svg += `<path d="${pathOf(ind.macd.macd, YM)}" fill="none" stroke="${IND_COLORS.macd}" stroke-width="1.3"/>`;
      svg += `<path d="${pathOf(ind.macd.signal, YM)}" fill="none" stroke="${IND_COLORS.signal}" stroke-width="1.3"/>`;
    }

    const tfmt = (t) => days <= 1
      ? new Date(t).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : new Date(t).toLocaleDateString([], days > 180 ? { month: 'short', year: '2-digit' } : { month: 'short', day: 'numeric' });
    for (let i = 0; i <= 4; i++) {
      const t = x0 + ((x1 - x0) * i) / 4;
      svg += `<text x="${X(t)}" y="${H - 6}" fill="var(--muted)" font-size="11" text-anchor="${i === 0 ? 'start' : i === 4 ? 'end' : 'middle'}">${esc(tfmt(t))}</text>`;
    }
    el.innerHTML = `
      <svg viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="Price chart">
        ${svg}
        <line id="cx" y1="${padT}" y2="${H - padB}" stroke="var(--muted)" stroke-dasharray="3 3" visibility="hidden"/>
        <circle id="cd" r="4" fill="${color}" stroke="var(--panel)" stroke-width="2" visibility="hidden"/>
        <rect x="${padL}" y="0" width="${W - padL - padR}" height="${H}" fill="transparent"/>
      </svg>
      <div class="tip" hidden></div>`;
    const svgEl = $('svg', el), tip = $('.tip', el), cxl = $('#cx', el), cd = $('#cd', el);
    const move = (ev) => {
      const rect = svgEl.getBoundingClientRect();
      const clientX = ev.touches ? ev.touches[0].clientX : ev.clientX;
      const px = ((clientX - rect.left) / rect.width) * W;
      const t = x0 + ((px - padL) / (W - padL - padR)) * (x1 - x0);
      let lo = 0, hi = pts.length - 1;
      while (hi - lo > 1) { const m = (lo + hi) >> 1; if (pts[m][0] < t) lo = m; else hi = m; }
      const k = Math.abs(pts[lo][0] - t) < Math.abs(pts[hi][0] - t) ? lo : hi;
      const p = pts[k], gi = idx[k];
      const x = X(p[0]), y = Y(p[1]);
      cxl.setAttribute('x1', x); cxl.setAttribute('x2', x); cxl.setAttribute('visibility', 'visible');
      cd.setAttribute('cx', x); cd.setAttribute('cy', y); cd.setAttribute('visibility', 'visible');
      const extra = [];
      if (ind.sma50?.[gi] != null) extra.push(`SMA 50 ${fmtMoney(ind.sma50[gi])}`);
      if (ind.sma200?.[gi] != null) extra.push(`SMA 200 ${fmtMoney(ind.sma200[gi])}`);
      if (ind.bb?.upper[gi] != null) extra.push(`Bands ${fmtMoney(ind.bb.lower[gi])} – ${fmtMoney(ind.bb.upper[gi])}`);
      if (ind.rsi?.[gi] != null) extra.push(`RSI ${ind.rsi[gi].toFixed(1)}`);
      if (ind.macd?.macd[gi] != null) extra.push(`MACD ${ind.macd.macd[gi].toPrecision(3)} / ${ind.macd.signal[gi].toPrecision(3)}`);
      tip.hidden = false;
      tip.style.left = `${Math.min(Math.max((x / W) * rect.width, 80), rect.width - 80)}px`;
      tip.style.top = `${(y / H) * rect.height}px`;
      tip.innerHTML = `<b>${fmtMoney(p[1])}</b><br><span class="muted">${new Date(p[0]).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}</span>${extra.map((e) => `<br>${esc(e)}`).join('')}`;
    };
    const leave = () => { tip.hidden = true; cxl.setAttribute('visibility', 'hidden'); cd.setAttribute('visibility', 'hidden'); };
    svgEl.addEventListener('mousemove', move);
    svgEl.addEventListener('touchmove', move, { passive: true });
    svgEl.addEventListener('mouseleave', leave);
    svgEl.addEventListener('touchend', leave);
  }

  /** Plain-English read of the latest daily bar (port of indicators.signal_summary). */
  async function loadTaNotes(id) {
    const el = $('#detail-ta');
    try {
      const c = TA.resample(await priceHistory(id, 365, 'usd'), DAY).map((p) => p[1]);
      if (state.detail.id !== id) return;
      const last = c[c.length - 1];
      const r = TA.last(TA.rsi(c)), s50 = TA.last(TA.sma(c, 50)), s200 = TA.sma(c, 200).at(-1), m = TA.macd(c);
      const notes = [];
      if (r != null) notes.push(r > 70 ? ['RSI overbought (above 70)', 'warn'] : r < 30 ? ['RSI oversold (below 30)', 'warn'] : [`RSI neutral (${r.toFixed(0)})`, '']);
      if (s200 != null) notes.push(last > s200 ? ['Price above its 200-day average', 'up'] : ['Price below its 200-day average', 'down']);
      if (s50 != null && s200 != null) notes.push(s50 > s200 ? ['50-day above 200-day (golden-cross regime)', 'up'] : ['50-day below 200-day (death-cross regime)', 'down']);
      notes.push(TA.last(m.macd) > TA.last(m.signal) ? ['MACD above its signal line', 'up'] : ['MACD below its signal line', 'down']);
      el.innerHTML = `<span class="muted small">Daily read:</span> ${notes.map(([t, cls]) => `<span class="chip ${cls}">${esc(t)}</span>`).join('')} <span class="muted small">Describes the chart. It isn't a buy or sell signal.</span>`;
    } catch { el.innerHTML = ''; }
  }

  async function loadExchanges() {
    const id = state.detail.id, el = $('#detail-exchanges');
    const sym = symbolOf(id);
    el.innerHTML = '<p class="muted small">Asking Coinbase, Kraken and Binance.US…</p>';
    if (state.mode === 'demo') { el.innerHTML = '<p class="muted small">Exchange prices need a live connection.</p>'; return; }
    const r = await exchangePrices(sym);
    if (state.detail.id !== id) return;
    el.innerHTML = `
      <table class="holdings compact-table"><thead><tr><th>Exchange</th><th class="r">Price (USD)</th><th class="r">24h volume</th></tr></thead><tbody>
      ${r.rows.map((x) => `<tr><td>${esc(x.exchange)}</td><td class="r">${x.price ? fmtUsd(x.price) : '<span class="muted">not available</span>'}</td><td class="r">${x.price ? `${fmtBig(x.volume)} ${esc(sym)}` : `<span class="muted small">${esc(x.error === 'Failed to fetch' ? "can't reach from this page" : x.error || '')}</span>`}</td></tr>`).join('')}
      </tbody></table>
      ${r.vwap ? `<p class="small">Volume-weighted price <b>${fmtUsd(r.vwap)}</b> from ${r.sources} exchange${r.sources > 1 ? 's' : ''} · spread ${r.spread.toFixed(3)}%</p>` : '<p class="muted small">No exchange answered. Some exchanges block requests from web pages. The Chrome extension version can reach them.</p>'}`;
  }

  async function loadResearch() {
    const id = state.detail.id, el = $('#detail-research');
    el.innerHTML = '<p class="muted small">Loading…</p>';
    if (state.mode === 'demo') { el.innerHTML = '<p class="muted small">Research needs a live connection.</p>'; return; }
    try {
      const p = await coinProfile(id);
      if (state.detail.id !== id) return;
      el.innerHTML = researchHtml(p);
    } catch (err) { el.innerHTML = `<p class="muted small">Couldn't load research: ${esc(err.message)}</p>`; }
  }

  const PROFILE_FIELDS = [
    ['Market cap', (p) => fmtCompact(p.marketCap, 'usd')],
    ['Fully diluted value', (p) => fmtCompact(p.fdv, 'usd')],
    ['Market cap ÷ FDV', (p) => (p.mcapToFdv != null ? p.mcapToFdv.toFixed(3) : '—')],
    ['Supply issued', (p) => (p.pctIssued != null ? `${p.pctIssued.toFixed(1)}%` : 'no max supply')],
    ['24h volume ÷ market cap', (p) => (p.volToMcap != null ? p.volToMcap.toFixed(4) : '—')],
    ['All-time high', (p) => `${fmtUsd(p.ath)}${p.athDate ? ` (${isoDay(Date.parse(p.athDate))})` : ''}`],
    ['From all-time high', (p) => fmtPct(p.fromAth, 1)],
    ['Return 7 days', (p) => fmtPct(p.r7d, 1)],
    ['Return 30 days', (p) => fmtPct(p.r30d, 1)],
    ['Return 1 year', (p) => fmtPct(p.r1y, 1)],
    ['GitHub stars', (p) => fmtNum(p.githubStars, 0)],
    ['Commits, last 4 weeks', (p) => fmtNum(p.commits4w, 0)],
    ['Launched', (p) => esc(p.genesisDate || '—')],
    ['Algorithm', (p) => esc(p.algorithm || '—')],
  ];
  function researchHtml(p) {
    return `<div class="stats">${PROFILE_FIELDS.map(([l, f]) => `<div><div class="label">${l}</div><div class="val">${f(p)}</div></div>`).join('')}</div>
      ${p.categories.length ? `<p class="small">${p.categories.slice(0, 8).map((c) => `<span class="chip">${esc(c)}</span>`).join(' ')}</p>` : ''}
      ${p.description ? `<p class="small muted">${esc(p.description)}${p.description.length >= 600 ? '…' : ''}</p>` : ''}
      ${p.homepage && /^https?:\/\//.test(p.homepage) ? `<p class="small"><a href="${esc(p.homepage)}" target="_blank" rel="noopener">${esc(p.homepage)}</a></p>` : ''}`;
  }

  // ---------- Compare ----------
  function openCompare() {
    const picks = $('#compare-pickers');
    const defaultsIds = ['bitcoin', 'ethereum', 'solana', ''];
    picks.innerHTML = defaultsIds.map((_, i) => `<select data-cmp="${i}" aria-label="Coin ${i + 1}"></select>`).join('');
    $$('select', picks).forEach((s, i) => { fillCoinSelect(s, defaultsIds[i], true); s.onchange = renderCompare; });
    $('#compare-dialog').showModal();
    renderCompare();
  }
  async function renderCompare() {
    const ids = [...new Set($$('#compare-pickers select').map((s) => s.value).filter(Boolean))];
    const tbl = $('#compare-table');
    if (state.mode === 'demo') { tbl.innerHTML = '<tbody><tr><td class="muted">Comparing needs a live connection.</td></tr></tbody>'; return; }
    tbl.innerHTML = '<tbody><tr><td class="muted">Loading…</td></tr></tbody>';
    const profiles = await Promise.all(ids.map((id) => coinProfile(id).catch((e) => ({ id, error: e.message }))));
    tbl.innerHTML = `<thead><tr><th></th>${profiles.map((p) => `<th class="r">${esc(p.symbol || nameOf(p.id))}</th>`).join('')}</tr></thead>
      <tbody>${[['Price', (p) => fmtUsd(p.price)], ['Rank', (p) => p.rank ?? '—'], ...PROFILE_FIELDS].map(([l, f]) => `<tr><td>${l}</td>${profiles.map((p) => `<td class="r">${p.error ? '—' : f(p)}</td>`).join('')}</tr>`).join('')}</tbody>`;
  }

  // ---------- Forms ----------
  function fillCoinSelect(sel, selected, allowNone = false) {
    const ids = new Set();
    const opts = [];
    const add = (c) => { if (c && !ids.has(c.id)) { ids.add(c.id); opts.push(c); } };
    trackedIds().forEach((id) => add(state.coinMap.get(id)));
    sortedCoins(state.coins).forEach(add);
    sel.innerHTML = (allowNone ? '<option value="">—</option>' : '') + opts.map((c) => `<option value="${esc(c.id)}" ${c.id === selected ? 'selected' : ''}>${esc(c.name)} (${esc(c.symbol.toUpperCase())})</option>`).join('');
  }

  function openHoldingForm(coinId) {
    const f = $('#holding-form');
    f.reset();
    $('#tx-error').hidden = true;
    fillCoinSelect(f.coin, coinId || state.coins[0]?.id);
    f.date.value = todayIso();
    f.date.max = todayIso();
    const setPrice = () => { const c = state.coinMap.get(f.coin.value); f.price.value = c ? +c.current_price.toPrecision(8) : ''; updateTotal(); };
    f.coin.onchange = setPrice;
    f.type.onchange = () => { const transfer = f.type.value === 'transfer'; f.price.required = !transfer; if (transfer) f.price.value = 0; else if (!+f.price.value) setPrice(); updateTotal(); };
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
    fillCoinSelect(f.coin, coinId || 'bitcoin');
    const sync = (resetValue) => {
      const meta = RULES[f.type.value];
      $$('[data-show]', f).forEach((el) => {
        const k = el.dataset.show;
        el.hidden = !(k === 'coin' ? meta.coin : k === 'contract' ? meta.contract : k === 'value' ? meta.value : k === 'ind' ? meta.ind : true);
      });
      if (meta.ind && resetValue) { f.period.value = meta.period; f.interval.value = meta.interval; }
      const c = state.coinMap.get(f.coin.value);
      const labels = { price: `Target price (${state.currency.toUpperCase()})`, '%': 'Percent', rsi: 'RSI level (0–100)', index: 'Index level (0–100)' };
      $('#value-label').textContent = labels[meta.value] || 'Value';
      if (resetValue) {
        const t = f.type.value;
        const sug = {
          price_above: c && +(c.current_price * 1.05).toPrecision(6), price_below: c && +(c.current_price * 0.95).toPrecision(6),
          change_24h_above: 5, change_24h_below: -5, rsi_above: 70, rsi_below: 30, fear_greed_above: 75, fear_greed_below: 20, funding_apr_above: 30,
        }[t];
        f.value.value = sug ?? '';
        f.cooldown.value = t.startsWith('fear') ? 1440 : 60;
      }
      const hints = {
        price: c ? `Current price: ${fmtMoney(c.current_price)}` : '',
        '%': meta.contract ? 'Funding is what traders betting on rises pay, per year. Above 30% is unusually high.' : c ? `24h change now: ${(c.price_change_percentage_24h_in_currency ?? 0).toFixed(2)}%` : '',
        rsi: 'RSI above 70 is usually called overbought, below 30 oversold.',
        index: '0 = extreme fear, 100 = extreme greed. Updates once a day.',
      };
      $('#alert-hint').textContent = meta.ind && !meta.value ? 'Fires on the first check after the price closes on the other side of its moving average.' : hints[meta.value] || '';
      f.value.required = !!meta.value;
    };
    f.type.onchange = () => sync(true);
    f.coin.onchange = () => sync(f.type.value.startsWith('price'));
    sync(true);
    $('#alert-dialog').showModal();
  }

  function openSettings() {
    const f = $('#settings-form');
    f.cgKey.value = state.settings.cgKey || '';
    f.ntfyTopic.value = state.settings.ntfyTopic || '';
    f.webhook.value = state.settings.webhook || '';
    $('#settings-dialog').showModal();
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
    setTimeout(() => el.remove(), action ? 8000 : 5000);
  }

  // ---------- Events ----------
  function toggleStar(id) {
    const i = state.watchlist.indexOf(id);
    if (i >= 0) state.watchlist.splice(i, 1); else state.watchlist.push(id);
    persist();
    renderMarkets(); renderWatchlist();
    if ($('#detail').open) renderDetailHeader();
  }

  const tabHooks = {};
  function switchTab(tab) {
    state.tab = tab;
    $$('.tabs button').forEach((b) => b.classList.toggle('active', b.dataset.tab === tab));
    $$('.panel').forEach((p) => p.classList.toggle('active', p.id === `tab-${tab}`));
    try { window.history.replaceState(null, '', `#${tab}`); } catch { /* sandboxed */ }
    tabHooks[tab]?.();
  }

  async function readFile(input) {
    const file = input.files[0];
    input.value = '';
    return file ? file.text() : null;
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
    $('#screener-body').addEventListener('click', onTable);
    $('#holdings-body').addEventListener('click', onTable);
    $('#screener-head').addEventListener('click', (e) => {
      const th = e.target.closest('[data-sort]');
      if (!th) return;
      const key = th.dataset.sort;
      state.screenerSort = { key, dir: state.screenerSort.key === key ? -state.screenerSort.dir : (key === 'rank' || key === 'name' ? 1 : -1) };
      persist(); renderScreener();
    });

    $('#search').addEventListener('input', () => renderMarkets());
    $$('input[name="mview"]').forEach((r) => {
      r.checked = r.value === state.marketsView;
      r.addEventListener('change', () => { state.marketsView = r.value; persist(); renderMarkets(); });
    });
    $('#open-compare').addEventListener('click', openCompare);
    const sortSel = $('#sort');
    sortSel.value = state.sort;
    sortSel.addEventListener('change', () => { state.sort = sortSel.value; persist(); renderMarkets(); renderWatchlist(); });

    const curSel = $('#currency');
    curSel.value = state.currency;
    curSel.addEventListener('change', () => {
      state.currency = curSel.value;
      persist();
      if (state.mode === 'demo') applyData(Demo.data(state.currency), 'demo');
      else { state.mode = 'loading'; renderStatus(); }
      refresh();
    });
    $('#refresh').addEventListener('click', () => refresh({ manual: true }));
    $('#open-settings').addEventListener('click', openSettings);

    $$('dialog').forEach((d) => {
      d.addEventListener('click', (e) => { if (e.target.closest('[data-close]') || e.target === d) d.close(); });
    });
    $('#detail').addEventListener('close', () => { state.detail.id = null; });
    $('#ranges').addEventListener('click', (e) => {
      const b = e.target.closest('button[data-days]');
      if (!b) return;
      state.detail.days = +b.dataset.days;
      loadChart();
    });
    $('#ind-toggles').addEventListener('click', (e) => {
      const b = e.target.closest('button[data-ind]');
      if (!b) return;
      const k = b.dataset.ind, i = state.indicators.indexOf(k);
      if (i >= 0) state.indicators.splice(i, 1); else state.indicators.push(k);
      persist(); renderDetailHeader(); loadChart();
    });
    $('#detail-exchanges-wrap').addEventListener('toggle', (e) => { if (e.target.open) loadExchanges(); });
    $('#detail-research-wrap').addEventListener('toggle', (e) => { if (e.target.open) loadResearch(); });
    $('#detail-star').addEventListener('click', () => toggleStar(state.detail.id));
    $('#detail-alert').addEventListener('click', () => { const id = state.detail.id; $('#detail').close(); openAlertForm(id); });
    $('#detail-hold').addEventListener('click', () => { const id = state.detail.id; $('#detail').close(); openHoldingForm(id); });

    // Transactions
    $('#add-holding').addEventListener('click', () => openHoldingForm());
    const hf = $('#holding-form');
    hf.amount.addEventListener('input', updateTotal);
    hf.price.addEventListener('input', updateTotal);
    hf.addEventListener('submit', (e) => {
      e.preventDefault();
      const amount = parseFloat(hf.amount.value), price = parseFloat(hf.price.value) || 0, fee = parseFloat(hf.fee.value) || 0;
      const errEl = $('#tx-error');
      if (!(amount > 0)) { errEl.textContent = 'Enter a quantity above zero.'; errEl.hidden = false; return; }
      const tx = { id: uid(), coinId: hf.coin.value, type: hf.type.value, amount, price, fee, cur: state.currency,
        date: parseIsoDay(hf.date.value || todayIso()), exchange: hf.exchange.value.trim(), notes: hf.notes.value.trim() };
      const check = portfolioIn(state.currency, state.settings.taxMethod, [...state.txs, tx]);
      if (check.error) { errEl.textContent = `This would sell more than you hold: ${check.error}`; errEl.hidden = false; return; }
      state.txs.push(tx);
      if (!state.watchlist.includes(tx.coinId)) state.watchlist.push(tx.coinId);
      persist();
      $('#holding-dialog').close();
      renderPortfolio(); renderWatchlist(); renderMarkets();
      switchTab('portfolio');
      toast('Transaction saved');
    });
    $('#tx-body').addEventListener('click', (e) => {
      const b = e.target.closest('[data-del-tx]');
      if (!b) return;
      const i = state.txs.findIndex((t) => t.id === b.dataset.delTx);
      if (i < 0) return;
      const [removed] = state.txs.splice(i, 1);
      persist(); renderPortfolio();
      toast(`Deleted ${TYPE_LABELS[removed.type].toLowerCase()} of ${fmtNum(removed.amount)} ${symbolOf(removed.coinId)}`, '', {
        label: 'Undo', run: () => { state.txs.push(removed); persist(); renderPortfolio(); },
      });
    });
    $('#tax-method').addEventListener('change', (e) => { state.settings.taxMethod = e.target.value; persist(); renderPortfolio(); });
    $('#tax-year').addEventListener('change', (e) => { state.taxYear = +e.target.value; renderTax(); });
    $('#export-8949').addEventListener('click', () => {
      const { pf } = taxData();
      if (pf.error) { toast('Fix the transaction problem first', 'err'); return; }
      downloadFile(`form8949-${state.taxYear}-${state.settings.taxMethod}.csv`, E.form8949Csv(pf.realized, state.taxYear, symbolOf), 'text/csv');
    });
    $('#export-trades').addEventListener('click', () => {
      const { trades } = tradesIn('usd');
      const rows = trades.map((t, i) => ({ ...t, asset: symbolOf(t.asset), exchange: state.txs[i].exchange, notes: state.txs[i].notes }));
      downloadFile(`trades-${todayIso()}.csv`, E.tradesCsv(rows), 'text/csv');
    });
    $('#import-trades').addEventListener('change', async (e) => {
      const text = await readFile(e.target);
      if (text == null) return;
      const { trades, errors } = E.parseTradesCsv(text);
      const added = [], unknown = new Set();
      for (const t of trades) {
        const coinId = await resolveSymbol(t.asset);
        if (!coinId) { unknown.add(t.asset); continue; }
        added.push({ id: uid(), coinId, type: t.type, amount: t.quantity, price: t.price, fee: t.fee, cur: 'usd', date: t.date, exchange: t.exchange, notes: t.notes });
      }
      const check = portfolioIn(state.currency, state.settings.taxMethod, [...state.txs, ...added]);
      if (check.error) { toast(`Import stopped: ${check.error}`, 'err'); return; }
      state.txs.push(...added);
      added.forEach((t) => { if (!state.watchlist.includes(t.coinId)) state.watchlist.push(t.coinId); });
      persist();
      const notes = [...errors, ...(unknown.size ? [`unknown coin(s): ${[...unknown].join(', ')}`] : [])];
      toast(`Imported ${added.length} transaction${added.length === 1 ? '' : 's'}${notes.length ? `. Skipped: ${notes.slice(0, 3).join('; ')}` : ''}`, notes.length ? 'warn' : '');
      refresh();
    });

    // Alerts
    $('#add-alert').addEventListener('click', () => openAlertForm());
    $('#check-alerts').addEventListener('click', () => checkAlerts({ manual: true }));
    const af = $('#alert-form');
    af.addEventListener('submit', (e) => {
      e.preventDefault();
      const type = af.type.value, meta = RULES[type];
      const value = meta.value ? parseFloat(af.value.value) : null;
      if (meta.value && !Number.isFinite(value)) return;
      state.alerts.push({ id: uid(), name: af.name.value.trim(), type, coinId: meta.coin ? af.coin.value : null,
        contract: meta.contract ? af.contract.value.trim().toUpperCase() || 'PF_XBTUSD' : undefined, value,
        period: meta.ind ? parseInt(af.period.value, 10) || meta.period : undefined, interval: meta.ind ? af.interval.value : undefined,
        cooldown: Math.max(1, parseInt(af.cooldown.value, 10) || 60), cur: state.currency, enabled: true, createdAt: Date.now() });
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
      const tog = e.target.closest('[data-toggle-alert]');
      if (del) {
        const i = state.alerts.findIndex((a) => a.id === del.dataset.delAlert);
        const [removed] = state.alerts.splice(i, 1);
        toast('Alert deleted', '', { label: 'Undo', run: () => { state.alerts.push(removed); persist(); renderAlerts(); } });
      } else if (tog) {
        const a = state.alerts.find((x) => x.id === tog.dataset.toggleAlert);
        if (a) a.enabled = !a.enabled;
      } else return;
      persist(); renderAlerts();
    });
    $('#enable-notif').addEventListener('click', requestNotif);
    $('#import-rules').addEventListener('change', async (e) => {
      const text = await readFile(e.target);
      if (text == null) return;
      try {
        const { added, skipped } = await importRules(JSON.parse(text));
        toast(`Imported ${added} alert${added === 1 ? '' : 's'}${skipped.length ? `. Skipped: ${skipped.join('; ')}` : ''}`, skipped.length ? 'warn' : '');
        renderAlerts(); switchTab('alerts');
      } catch (err) { toast(`Couldn't import alerts: ${err.message}`, 'err'); }
    });
    $('#export-rules').addEventListener('click', () => downloadFile('alerts.json', exportRules(), 'application/json'));

    // Settings
    $('#settings-form').addEventListener('submit', (e) => {
      e.preventDefault();
      const f = e.target;
      const keyChanged = f.cgKey.value.trim() !== (state.settings.cgKey || '');
      Object.assign(state.settings, { cgKey: f.cgKey.value.trim(), ntfyTopic: f.ntfyTopic.value.trim(), webhook: f.webhook.value.trim() });
      persist();
      $('#settings-dialog').close();
      toast('Settings saved');
      if (keyChanged) { memo.clear(); refresh({ manual: true }); }
    });
    $('#test-notify').addEventListener('click', () => {
      const f = $('#settings-form');
      Object.assign(state.settings, { ntfyTopic: f.ntfyTopic.value.trim(), webhook: f.webhook.value.trim() });
      persist();
      notifyAll('Mintline test alert', 'If you can read this, alerts will reach you here.');
    });

    // Backup
    $('#export').addEventListener('click', () => {
      const { watchlist, txs, alerts, currency, settings, profile } = state;
      const safeSettings = { ...settings, cgKey: '' };
      downloadFile(`mintline-backup-${todayIso()}.json`, JSON.stringify({ app: 'mintline', version: 2, exportedAt: new Date().toISOString(), currency, watchlist, txs, alerts, profile, settings: safeSettings }, null, 2), 'application/json');
    });
    $('#import').addEventListener('change', async (e) => {
      const text = await readFile(e.target);
      if (text == null) return;
      try {
        const data = JSON.parse(text);
        if (data.app !== 'mintline') throw new Error('this isn\'t a Mintline backup');
        if (Array.isArray(data.watchlist)) state.watchlist = data.watchlist.map(String);
        if (Array.isArray(data.txs)) state.txs = data.txs.filter((t) => t && t.coinId && isFinite(t.amount));
        if (Array.isArray(data.alerts)) state.alerts = data.alerts;
        if (data.profile) state.profile = data.profile;
        migrate();
        persist();
        toast('Backup imported');
        refresh();
      } catch (err) {
        toast(`Import failed: ${err.message}`, 'err');
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === '/' && !e.target.closest('input, select, textarea, dialog')) {
        e.preventDefault(); switchTab('markets'); $('#search').focus();
      }
    });
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && Date.now() - (state.updatedAt || 0) > REFRESH_MS / 2) refresh();
    });
    window.addEventListener('online', () => refresh());
    let rt;
    window.addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(() => { if ($('#detail').open) loadChart(); }, 150); });
  }

  async function requestNotif() {
    if (!('Notification' in window)) return;
    const p = await Notification.requestPermission();
    if (p === 'granted') toast('Notifications enabled');
    renderAlerts();
  }

  // ---------- Public API for tools.js and tests ----------
  window.Mintline = {
    state, persist, convert, cg, getJSON, cached, priceHistory, closes, dailyBars, fearGreed, krakenFutures, coinProfile,
    exchangePrices, resolveSymbol, symbolOf, nameOf, portfolioIn, portfolioUsd, evaluate, checkAlerts, importRules,
    exportRules, describeRule, notifyAll, toast, fmtMoney, fmtUsd, fmtPct, fmtNum, fmtBig, fmtCompact, signed, esc,
    coinIcon, fillCoinSelect, sortedCoins, downloadFile, isoDay, Demo, DAY,
    onRefresh: (fn) => refreshHooks.push(fn),
    onTab: (tab, fn) => { tabHooks[tab] = fn; },
    switchTab, openDetail,
  };

  // ---------- Boot ----------
  function boot() {
    bind();
    const cache = load(CACHE_KEY);
    if (cache && cache.currency === state.currency && cache.coins?.length) applyData(cache, 'cached', cache.at);
    else renderAll();
    const initial = (location.hash || '').slice(1);
    if (['markets', 'watchlist', 'portfolio', 'alerts', 'mentor', 'bitcoin', 'backtest'].includes(initial)) switchTab(initial);
    refresh();
    setInterval(() => { if (!document.hidden) refresh(); }, REFRESH_MS);
    if ('serviceWorker' in navigator && /^https?:$/.test(location.protocol)) {
      navigator.serviceWorker.register('sw.js').catch(() => {});
    }
  }
  // Let tools.js register its tabs before the first render.
  window.addEventListener('DOMContentLoaded', boot);
})();
