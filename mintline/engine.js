/* Mintline engine — JavaScript ports of the Python crypto_toolkit:
 *   tax       portfolio.py  (FIFO/LIFO/HIFO lots, realized gains, Form 8949 CSV)
 *   backtest  bot.py        (paper broker, DCA with dip buys, grid, SMA cross)
 *   advisor   advisor.py    (five market signals -> weekly buying plan)
 * Pure functions with no network or DOM access, so they can be tested in Node.
 */
(function (root) {
  'use strict';
  const TA = typeof module !== 'undefined' && module.exports ? require('./indicators.js') : root.MintTA;
  const DAY = 864e5;
  const r2 = (x) => Math.round((x + Number.EPSILON) * 100) / 100;

  // ------------------------------------------------------------------ portfolio / tax
  const ACQUIRE = ['buy', 'income', 'gift_in'];
  const DISPOSE = ['sell', 'spend'];
  const TYPES = [...ACQUIRE, ...DISPOSE, 'transfer'];

  /**
   * trades: [{date (ms), type, asset, quantity, price, fee}] in one currency.
   * Returns {lots: {asset: [{qty, costPerUnit, acquired}]}, realized: [...], income: [...]}.
   */
  function computeLots(trades, method = 'FIFO') {
    method = String(method).toUpperCase();
    if (!['FIFO', 'LIFO', 'HIFO'].includes(method)) throw new Error('method must be FIFO, LIFO or HIFO');
    const sorted = trades.map((t, i) => ({ ...t, _i: i })).sort((a, b) => a.date - b.date || a._i - b._i);
    const lots = {}, realized = [], income = [];
    for (const t of sorted) {
      const a = t.asset, q = +t.quantity || 0, px = +t.price || 0, fee = +t.fee || 0;
      const book = (lots[a] ||= []);
      if (ACQUIRE.includes(t.type)) {
        book.push({ qty: q, costPerUnit: q ? (q * px + fee) / q : 0, acquired: t.date });
        if (t.type === 'income') income.push({ date: t.date, asset: a, quantity: q, value: q * px });
      } else if (DISPOSE.includes(t.type)) {
        let remaining = q;
        const proceedsUnit = q ? (q * px - fee) / q : 0;
        while (remaining > 1e-12) {
          if (!book.length) {
            const err = new Error(`${new Date(t.date).toISOString().slice(0, 10)}: selling ${q} ${a} but holdings run out (missing buy or transfer-in rows?)`);
            err.code = 'oversold';
            throw err;
          }
          let idx = 0;
          if (method === 'LIFO') idx = book.length - 1;
          else if (method === 'HIFO') idx = book.reduce((best, l, i) => (l.costPerUnit > book[best].costPerUnit ? i : best), 0);
          const lot = book[idx];
          const take = Math.min(lot.qty, remaining);
          const held = Math.floor((t.date - lot.acquired) / DAY);
          realized.push({
            asset: a, quantity: take,
            dateAcquired: lot.acquired, dateSold: t.date,
            proceeds: r2(take * proceedsUnit),
            costBasis: r2(take * lot.costPerUnit),
            gainLoss: r2(take * (proceedsUnit - lot.costPerUnit)),
            term: held > 365 ? 'long' : 'short',
          });
          lot.qty -= take;
          remaining -= take;
          if (lot.qty <= 1e-12) book.splice(idx, 1);
        }
      } else if (t.type === 'transfer') {
        continue; // wallet-to-wallet move; basis carries over
      } else {
        throw new Error(`Unknown type '${t.type}'`);
      }
    }
    return { lots, realized, income };
  }

  function holdings(lots, prices = {}) {
    const rows = [];
    for (const [asset, book] of Object.entries(lots)) {
      const qty = book.reduce((s, l) => s + l.qty, 0);
      if (qty <= 1e-12) continue;
      const costBasis = book.reduce((s, l) => s + l.qty * l.costPerUnit, 0);
      const price = prices[asset] ?? null;
      const value = price != null ? qty * price : null;
      rows.push({ asset, quantity: qty, costBasis, price, value,
        unrealized: value != null ? value - costBasis : null,
        unrealizedPct: value != null && costBasis ? ((value - costBasis) / costBasis) * 100 : null });
    }
    const total = rows.reduce((s, r) => s + (r.value || 0), 0);
    rows.forEach((r) => { r.allocationPct = total ? ((r.value || 0) / total) * 100 : 0; });
    return rows.sort((a, b) => (b.value || 0) - (a.value || 0));
  }

  const yearOf = (ms) => new Date(ms).getUTCFullYear();

  function taxSummary(realized, income, year = null) {
    const r = year ? realized.filter((x) => yearOf(x.dateSold) === year) : realized;
    const i = year ? income.filter((x) => yearOf(x.date) === year) : income;
    const g = (term) => r.filter((x) => x.term === term).reduce((s, x) => s + x.gainLoss, 0);
    return {
      year: year || 'all',
      shortTermGain: r2(g('short')), longTermGain: r2(g('long')),
      totalRealized: r2(g('short') + g('long')),
      income: r2(i.reduce((s, x) => s + x.value, 0)),
      disposals: r.length,
    };
  }

  const iso = (ms) => new Date(ms).toISOString().slice(0, 10);
  function csvCell(v) {
    const s = String(v ?? '');
    return /[",\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  }

  /** Form 8949-style CSV, same columns as the toolkit's form_8949(). */
  function form8949Csv(realized, year = null, symbolOf = (a) => a) {
    const r = year ? realized.filter((x) => yearOf(x.dateSold) === year) : realized;
    const rows = [['description', 'date_acquired', 'date_sold', 'proceeds', 'cost_basis', 'gain_loss', 'term']];
    for (const x of r) rows.push([`${x.quantity.toFixed(8)} ${symbolOf(x.asset)}`, iso(x.dateAcquired), iso(x.dateSold), x.proceeds, x.costBasis, x.gainLoss, x.term]);
    return rows.map((row) => row.map(csvCell).join(',')).join('\n') + '\n';
  }

  /** Minimal RFC 4180 CSV parser (quotes, escaped quotes, CRLF). */
  function parseCsv(text) {
    const rows = [];
    let row = [], cell = '', q = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (q) {
        if (c === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else q = false; }
        else cell += c;
      } else if (c === '"') q = true;
      else if (c === ',') { row.push(cell); cell = ''; }
      else if (c === '\n' || c === '\r') {
        if (c === '\r' && text[i + 1] === '\n') i++;
        row.push(cell); rows.push(row); row = []; cell = '';
      } else cell += c;
    }
    if (cell !== '' || row.length) { row.push(cell); rows.push(row); }
    return rows.filter((r) => r.some((v) => v.trim() !== ''));
  }

  /** Toolkit trades CSV: date,type,asset,quantity,price_usd,fee_usd,exchange,notes */
  function parseTradesCsv(text) {
    const rows = parseCsv(text);
    if (!rows.length) return { trades: [], errors: ['The file is empty.'] };
    const head = rows[0].map((h) => h.trim().toLowerCase());
    const col = (name) => head.indexOf(name);
    const need = ['date', 'type', 'asset', 'quantity'];
    const missing = need.filter((n) => col(n) < 0);
    if (missing.length) return { trades: [], errors: [`Missing column(s): ${missing.join(', ')}`] };
    const priceCol = col('price_usd') >= 0 ? col('price_usd') : col('price');
    const feeCol = col('fee_usd') >= 0 ? col('fee_usd') : col('fee');
    const trades = [], errors = [];
    rows.slice(1).forEach((r, n) => {
      const line = n + 2;
      const date = Date.parse(r[col('date')]?.trim());
      const type = (r[col('type')] || '').trim().toLowerCase();
      const asset = (r[col('asset')] || '').trim().toUpperCase();
      const num = (i) => { const v = parseFloat(i >= 0 ? r[i] : ''); return Number.isFinite(v) ? v : 0; };
      if (!Number.isFinite(date)) { errors.push(`Line ${line}: unreadable date`); return; }
      if (!TYPES.includes(type)) { errors.push(`Line ${line}: unknown type "${type}"`); return; }
      if (!asset) { errors.push(`Line ${line}: missing asset`); return; }
      trades.push({ date, type, asset, quantity: num(col('quantity')), price: num(priceCol), fee: num(feeCol),
        exchange: col('exchange') >= 0 ? (r[col('exchange')] || '').trim() : '',
        notes: col('notes') >= 0 ? (r[col('notes')] || '').trim() : '' });
    });
    return { trades, errors };
  }

  function tradesCsv(trades) {
    const rows = [['date', 'type', 'asset', 'quantity', 'price_usd', 'fee_usd', 'exchange', 'notes']];
    for (const t of trades) rows.push([iso(t.date), t.type, t.asset, t.quantity, t.price, t.fee || 0, t.exchange || '', t.notes || '']);
    return rows.map((row) => row.map(csvCell).join(',')).join('\n') + '\n';
  }

  // ------------------------------------------------------------------------ backtests
  const FEE = 0.006; // 0.6% taker, same default as the toolkit

  class PaperBroker {
    constructor(cash = 10000, fee = FEE) { this.cash = cash; this.qty = 0; this.fee = fee; this.trades = []; }
    buyUsd(usd, price, time) {
      usd = Math.min(usd, this.cash);
      if (usd <= 0) return;
      const q = (usd * (1 - this.fee)) / price;
      this.cash -= usd; this.qty += q;
      this.trades.push({ time, side: 'buy', price, qty: q, usd });
    }
    sellQty(q, price, time) {
      q = Math.min(q, this.qty);
      if (q <= 0) return;
      const usd = q * price * (1 - this.fee);
      this.qty -= q; this.cash += usd;
      this.trades.push({ time, side: 'sell', price, qty: q, usd });
    }
    equity(price) { return this.cash + this.qty * price; }
  }

  function report(name, b, startCash, curve, lastPrice) {
    const eq = b.equity(lastPrice);
    const invested = b.trades.filter((t) => t.side === 'buy').reduce((s, t) => s + t.usd, 0);
    let peak = -Infinity, dd = 0;
    for (const v of curve) { peak = Math.max(peak, v); dd = Math.min(dd, v / peak - 1); }
    return { strategy: name, startCash, finalEquity: r2(eq), returnPct: r2((eq / startCash - 1) * 100),
      totalBuyVolume: r2(invested), trades: b.trades.length, maxDrawdownPct: r2(dd * 100),
      endQty: Math.round(b.qty * 1e8) / 1e8, endCash: r2(b.cash), curve, fills: b.trades };
  }

  /** bars: [{time, high, low, close}] oldest first (daily). */
  function backtestDca(bars, { amount = 100, every = 7, dipPct = 0, dipMultiplier = 2, startCash = null, fee = FEE } = {}) {
    const nBuys = Math.floor(bars.length / every) + 1;
    startCash = startCash || amount * nBuys * (dipPct ? dipMultiplier : 1);
    const b = new PaperBroker(startCash, fee);
    const curve = [];
    bars.forEach((r, i) => {
      if (i % every === 0) {
        let size = amount;
        let hi30 = -Infinity;
        for (let j = Math.max(0, i - 29); j <= i; j++) hi30 = Math.max(hi30, bars[j].high);
        if (dipPct && r.close <= hi30 * (1 - dipPct / 100)) size *= dipMultiplier;
        b.buyUsd(size, r.close, r.time);
      }
      curve.push(b.equity(r.close));
    });
    const rep = report(`DCA ${amount} every ${every} days` + (dipPct ? ` + dip buys at -${dipPct}%` : ''), b, startCash, curve, bars[bars.length - 1].close);
    const deployed = rep.totalBuyVolume;
    rep.returnOnInvestedPct = deployed ? r2(((b.qty * bars[bars.length - 1].close) / deployed - 1) * 100) : 0;
    return rep;
  }

  function backtestGrid(bars, { low, high, levels = 20, capital = 5000, fee = FEE } = {}) {
    const grid = Array.from({ length: levels + 1 }, (_, i) => low + ((high - low) * i) / levels);
    const per = capital / levels;
    const b = new PaperBroker(capital, fee);
    const holding = new Map();
    const p0 = bars[0].close;
    for (let i = 0; i < levels; i++) {
      if (grid[i] > p0) { const before = b.qty; b.buyUsd(per, p0, bars[0].time); holding.set(i, b.qty - before); }
    }
    const curve = [];
    for (const r of bars) {
      for (let i = 0; i < levels; i++) {
        const buyPx = grid[i], sellPx = grid[i + 1];
        if (!holding.has(i) && r.low <= buyPx && b.cash >= per * 0.99) {
          const before = b.qty; b.buyUsd(per, buyPx, r.time); holding.set(i, b.qty - before);
        } else if (holding.has(i) && r.high >= sellPx) {
          b.sellQty(holding.get(i), sellPx, r.time); holding.delete(i);
        }
      }
      curve.push(b.equity(r.close));
    }
    return report(`Grid ${Math.round(low).toLocaleString('en-US')}–${Math.round(high).toLocaleString('en-US')} × ${levels}`, b, capital, curve, bars[bars.length - 1].close);
  }

  function backtestSma(bars, { fast = 50, slow = 200, capital = 10000, fee = FEE } = {}) {
    const closes = bars.map((r) => r.close);
    const f = TA.sma(closes, fast), s = TA.sma(closes, slow);
    const b = new PaperBroker(capital, fee);
    const curve = [];
    bars.forEach((r, i) => {
      if (s[i] != null) {
        if (f[i] > s[i] && b.cash > 1) b.buyUsd(b.cash, r.close, r.time);
        else if (f[i] < s[i] && b.qty > 0) b.sellQty(b.qty, r.close, r.time);
      }
      curve.push(b.equity(r.close));
    });
    const rep = report(`SMA ${fast}/${slow} cross`, b, capital, curve, bars[bars.length - 1].close);
    rep.buyAndHoldPct = r2((closes[closes.length - 1] / closes[0] - 1) * 100);
    return rep;
  }

  // -------------------------------------------------------------------------- advisor
  const MIXES = {
    low: { BTC: 1.0 },
    medium: { BTC: 0.7, ETH: 0.3 },
    high: { BTC: 0.6, ETH: 0.3, SOL: 0.1 },
  };
  const LEVELS = [
    [-1.0, 'ON SALE', 1.5, 'Prices are low compared to their history and people are scared. Historically this has been a good time for patient buyers.'],
    [-0.3, 'CHEAPER THAN USUAL', 1.25, 'Prices are below their usual range and the mood is nervous.'],
    [0.5, 'NORMAL', 1.0, 'Nothing unusual. Stick to the plan.'],
    [1.2, 'PRICEY', 0.5, 'Prices are stretched and people are getting greedy. Buy less.'],
    [99, 'OVERHEATED', 0.0, 'Prices and excitement are extreme. This is when beginners buy the top. Pause buying.'],
  ];
  const ARROWS = { '-2': 'cheap ++', '-1': 'cheap +', 0: 'neutral', 1: 'pricey +', 2: 'pricey ++' };
  const round = (x, d) => Math.round(x * 10 ** d) / 10 ** d;

  function score(name, value, bands) {
    for (const [upper, s, text] of bands) if (value < upper) return { signal: name, value, score: s, reading: text };
    const lastBand = bands[bands.length - 1];
    return { signal: name, value, score: lastBand[1], reading: lastBand[2] };
  }

  /** closes: daily BTC closes (>= 200); ath: all-time high in the same currency. */
  function readSignals({ closes, ath, fearGreed, fundingApr = 0 }) {
    const price = closes[closes.length - 1];
    const mayer = price / TA.last(TA.sma(closes, 200));
    const rsi = TA.last(TA.rsi(closes));
    const drawdown = (price / Math.max(ath, ...closes) - 1) * 100;
    return [
      score('Price vs. its 200-day average (Mayer Multiple)', round(mayer, 2), [
        [0.8, -2, 'far below its long-run average: historically very cheap'],
        [1.0, -1, 'below its long-run average: cheaper than usual'],
        [1.5, 0, 'around its long-run average: fair'],
        [2.4, 1, 'well above its long-run average: getting expensive'],
        [99, 2, 'extremely far above average: past bubble territory'],
      ]),
      score('Crowd mood (Fear & Greed, 0-100)', fearGreed, [
        [20, -2, 'extreme fear: people are panic-selling'],
        [40, -1, 'fear: people are nervous'],
        [60, 0, 'neutral'],
        [80, 1, 'greed: people are excited'],
        [101, 2, 'extreme greed: euphoria'],
      ]),
      score('Short-term momentum (RSI, 0-100)', round(rsi, 1), [
        [30, -1, 'sold off hard recently'],
        [75, 0, 'normal'],
        [101, 1, 'ran up fast recently'],
      ]),
      score('Distance from all-time high', round(drawdown, 1), [
        [-50, -1, 'more than half off its peak'],
        [-10, 0, 'a fair way below its peak'],
        [1, 1, 'near its all-time high'],
      ]),
      score("Traders' borrowing (futures funding, % per year)", round(fundingApr, 1), [
        [-5, -1, 'traders are betting on falls'],
        [30, 0, 'normal'],
        [9999, 1, 'traders are borrowing heavily to bet on rises (fragile)'],
      ]),
    ].map((s) => ({ ...s, arrow: ARROWS[s.score] }));
  }

  function temperature(signals) {
    const weights = [2.0, 1.5, 0.75, 0.75, 0.5];
    const avg = signals.reduce((s, x, i) => s + x.score * weights[i], 0) / weights.reduce((a, b) => a + b, 0);
    for (const [upper, label, mult, why] of LEVELS) if (avg <= upper) return { score: round(avg, 2), label, mult, why };
    const l = LEVELS[LEVELS.length - 1];
    return { score: round(avg, 2), label: l[1], mult: l[2], why: l[3] };
  }

  /**
   * profile: {emergencyFund, highInterestDebt, weeklyUsd, maxTotalUsd, years, risk}
   * hold: [{symbol, costBasis (USD), value (USD), allocationPct}] or null
   * Returns the briefing as data; the app renders it.
   */
  function plan(profile, signals, hold = null) {
    const p = profile;
    if (p.highInterestDebt) return { blocked: 'debt' };
    if (!p.emergencyFund) return { blocked: 'emergency' };
    const t = temperature(signals);
    const mix = MIXES[p.risk] || MIXES.medium;
    const has = hold && hold.length;
    const invested = has ? hold.reduce((s, h) => s + h.costBasis, 0) : 0;
    const room = Math.max(0, p.maxTotalUsd - invested);
    const amount = r2(Math.min(p.weeklyUsd * t.mult, room));
    let split = { ...mix };
    if (has && Object.keys(mix).length > 1) {
      const cur = Object.fromEntries(Object.keys(mix).map((a) => [a, 0]));
      for (const h of hold) if (h.symbol in cur) cur[h.symbol] = h.allocationPct / 100;
      const gaps = Object.fromEntries(Object.keys(mix).map((a) => [a, Math.max(0, mix[a] - cur[a])]));
      const total = Object.values(gaps).reduce((a, b) => a + b, 0);
      if (total > 0.05) split = Object.fromEntries(Object.entries(gaps).map(([a, g]) => [a, g / total]));
    }
    const buys = Object.entries(split).map(([symbol, s]) => ({ symbol, usd: r2(amount * s) })).filter((b) => b.usd >= 1);
    const value = has ? hold.reduce((s, h) => s + (h.value || 0), 0) : 0;
    const pnl = value - invested;
    return {
      blocked: null, ...t, mix, room, amount, buys, signals,
      portfolio: has ? {
        invested, value, pnl, pnlPct: invested ? (pnl / invested) * 100 : 0,
        rows: hold.map((h) => ({ symbol: h.symbol, allocationPct: h.allocationPct, planPct: (mix[h.symbol] || 0) * 100 })),
        takeProfit: t.label === 'OVERHEATED' && invested && pnl / invested > 1.0,
        dontSell: pnl < 0 && (t.label === 'ON SALE' || t.label === 'CHEAPER THAN USUAL'),
      } : null,
    };
  }

  /** Plain weekly buying vs. the advisor's adjusted buying over daily history. */
  function advisorBacktest(days, fearGreedByDay, weekly = 50) {
    // days: [{time, close, high?}] daily; fearGreedByDay: {YYYY-MM-DD: value}
    let plainUsd = 0, plainQty = 0, advUsd = 0, advQty = 0, weeks = 0;
    for (let i = 200; i < days.length; i += 7) {
      const win = days.slice(0, i + 1);
      const day = iso(win[win.length - 1].time);
      const fg = fearGreedByDay[day] ?? 50;
      const closes = win.map((d) => d.close);
      const ath = Math.max(...win.map((d) => d.high ?? d.close));
      const { mult } = temperature(readSignals({ closes, ath, fearGreed: fg, fundingApr: 0 }));
      const px = closes[closes.length - 1];
      plainUsd += weekly; plainQty += weekly / px;
      advUsd += weekly * mult; advQty += (weekly * mult) / px;
      weeks++;
    }
    const lastPx = days[days.length - 1].close;
    const res = (usd, q) => ({ spent: r2(usd), worthNow: r2(q * lastPx), avgPricePaid: q ? r2(usd / q) : null, returnPct: usd ? r2(((q * lastPx) / usd - 1) * 100) : 0 });
    return { from: days[Math.min(200, days.length - 1)].time, to: days[days.length - 1].time, weeks,
      plain: res(plainUsd, plainQty), advisor: res(advUsd, advQty) };
  }

  const api = {
    TYPES, ACQUIRE, DISPOSE, computeLots, holdings, taxSummary, form8949Csv, parseCsv, parseTradesCsv, tradesCsv,
    PaperBroker, backtestDca, backtestGrid, backtestSma, FEE,
    MIXES, LEVELS, readSignals, temperature, plan, advisorBacktest,
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.MintEngine = api;
})(typeof window !== 'undefined' ? window : globalThis);
