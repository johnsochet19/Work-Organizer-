/* Mintline technical indicators — a JavaScript port of crypto_toolkit/indicators.py.
 * Every function takes an array of closing prices (oldest first) and returns arrays of
 * the same length, with null where there isn't enough history yet. The formulas match
 * the Python toolkit exactly (pandas ewm adjust=False, population std-dev), so both
 * tools report the same RSI/MACD/Bollinger values for the same data.
 */
(function (root) {
  'use strict';

  function sma(values, n) {
    const out = new Array(values.length).fill(null);
    let sum = 0, count = 0;
    for (let i = 0; i < values.length; i++) {
      sum += values[i]; count++;
      if (count > n) { sum -= values[i - n]; count--; }
      if (count === n) out[i] = sum / n;
    }
    return out;
  }

  // pandas: s.ewm(span=n, adjust=False).mean() — seeded with the first value.
  function ema(values, n) {
    const out = new Array(values.length).fill(null);
    const k = 2 / (n + 1);
    let prev = null;
    for (let i = 0; i < values.length; i++) {
      const v = values[i];
      if (v == null) continue;
      prev = prev == null ? v : v * k + prev * (1 - k);
      out[i] = prev;
    }
    return out;
  }

  function bollinger(values, n = 20, mult = 2) {
    const mid = sma(values, n);
    const upper = new Array(values.length).fill(null);
    const lower = new Array(values.length).fill(null);
    for (let i = n - 1; i < values.length; i++) {
      let s = 0;
      for (let j = i - n + 1; j <= i; j++) s += (values[j] - mid[i]) ** 2;
      const sd = Math.sqrt(s / n);
      upper[i] = mid[i] + mult * sd;
      lower[i] = mid[i] - mult * sd;
    }
    return { mid, upper, lower };
  }

  // Same as the toolkit: ewm(alpha=1/n, adjust=False, min_periods=n) of gains and losses.
  function rsi(values, n = 14) {
    const out = new Array(values.length).fill(null);
    const a = 1 / n;
    let up = null, dn = null, seen = 0;
    for (let i = 1; i < values.length; i++) {
      const d = values[i] - values[i - 1];
      const g = Math.max(d, 0), l = Math.max(-d, 0);
      up = up == null ? g : a * g + (1 - a) * up;
      dn = dn == null ? l : a * l + (1 - a) * dn;
      seen++;
      if (seen >= n) out[i] = dn === 0 ? 100 : 100 - 100 / (1 + up / dn);
    }
    return out;
  }

  function macd(values, fast = 12, slow = 26, signalN = 9) {
    const ef = ema(values, fast), es = ema(values, slow);
    const line = values.map((_, i) => (ef[i] != null && es[i] != null ? ef[i] - es[i] : null));
    const signal = ema(line, signalN);
    const hist = line.map((v, i) => (v != null && signal[i] != null ? v - signal[i] : null));
    return { macd: line, signal, hist };
  }

  /** Group [timestamp, price] points into candles of `ms` length; returns [[t, close], ...]. */
  function resample(points, ms) {
    const out = [];
    let bucket = null;
    for (const [t, p] of points) {
      const b = Math.floor(t / ms);
      if (b !== bucket) { out.push([t, p]); bucket = b; } else out[out.length - 1] = [t, p];
    }
    return out;
  }

  const last = (arr) => { for (let i = arr.length - 1; i >= 0; i--) if (arr[i] != null) return arr[i]; return null; };

  const api = { sma, ema, bollinger, rsi, macd, resample, last };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.MintTA = api;
})(typeof window !== 'undefined' ? window : globalThis);
