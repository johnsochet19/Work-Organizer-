"""3Commas / Cryptohopper replacement: DCA and grid bots, with backtests and paper trading.

SAFETY: everything runs in PAPER mode (simulated fills, fake balance) unless you pass
--live AND set LIVE_TRADING=yes in .env AND supply exchange API keys. Start with a
backtest, then paper-trade for weeks before risking money. Bots can and do lose money.

    python -m crypto_toolkit backtest dca  BTC --amount 100 --every 7 --dip 5
    python -m crypto_toolkit backtest grid BTC --low 60000 --high 90000 --levels 20 --capital 5000
    python -m crypto_toolkit backtest sma  BTC --fast 50 --slow 200
    python -m crypto_toolkit bot dca BTC --amount 25 --every-hours 24          # paper
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import indicators as ta
from .free_apis import Coinbase, Kraken
from .http import env

FEE = 0.006  # 0.6% taker, roughly Coinbase Advanced entry tier; change to your exchange


# ------------------------------------------------------------------------------ brokers
@dataclass
class PaperBroker:
    cash: float = 10_000.0
    qty: float = 0.0
    fee: float = FEE
    trades: list = field(default_factory=list)

    def buy_usd(self, usd: float, price: float, ts=None):
        usd = min(usd, self.cash)
        if usd <= 0:
            return
        q = usd * (1 - self.fee) / price
        self.cash -= usd
        self.qty += q
        self.trades.append({"time": ts, "side": "buy", "price": price, "qty": q, "usd": usd})

    def sell_qty(self, q: float, price: float, ts=None):
        q = min(q, self.qty)
        if q <= 0:
            return
        usd = q * price * (1 - self.fee)
        self.qty -= q
        self.cash += usd
        self.trades.append({"time": ts, "side": "sell", "price": price, "qty": q, "usd": usd})

    def equity(self, price: float) -> float:
        return self.cash + self.qty * price


class LiveBroker:
    """Real orders via CCXT. Guarded by three separate opt-ins."""

    def __init__(self, exchange: str, symbol: str):
        if env("LIVE_TRADING", "no").lower() != "yes":
            raise PermissionError("Refusing live trading: set LIVE_TRADING=yes in .env first")
        import ccxt
        key, secret = env(f"{exchange.upper()}_API_KEY"), env(f"{exchange.upper()}_API_SECRET")
        if not key or not secret:
            raise PermissionError(f"Set {exchange.upper()}_API_KEY and _API_SECRET (trade-only, no withdrawals)")
        self.ex = getattr(ccxt, exchange)({"apiKey": key, "secret": secret, "enableRateLimit": True})
        self.symbol = symbol
        self.max_order = float(env("MAX_ORDER_USD", "50"))

    def buy_usd(self, usd: float, price: float, ts=None):
        usd = min(usd, self.max_order)
        return self.ex.create_order(self.symbol, "market", "buy", usd / price)

    def sell_qty(self, q: float, price: float, ts=None):
        q = min(q, self.max_order / price)
        return self.ex.create_order(self.symbol, "market", "sell", q)


# ---------------------------------------------------------------------------- results
def _report(name, broker: PaperBroker, start_cash, curve: pd.Series, last_price) -> dict:
    eq = broker.equity(last_price)
    invested = sum(t["usd"] for t in broker.trades if t["side"] == "buy")
    dd = (curve / curve.cummax() - 1).min() * 100 if len(curve) else 0
    return {"strategy": name, "start_cash": start_cash, "final_equity": round(eq, 2),
            "return_pct": round((eq / start_cash - 1) * 100, 2),
            "total_buy_volume_usd": round(invested, 2), "trades": len(broker.trades),
            "max_drawdown_pct": round(float(dd), 2), "end_qty": round(broker.qty, 8),
            "end_cash": round(broker.cash, 2)}


def history(symbol: str, interval: str = "1d") -> pd.DataFrame:
    base = {"BTC": "XBT"}.get(symbol.upper(), symbol.upper())
    try:  # Kraken gives ~720 daily bars; Coinbase gives 300
        return Kraken().ohlc(f"{base}USD", interval)
    except Exception:
        return Coinbase().candles(f"{symbol.upper()}-USD", interval)


# ----------------------------------------------------------------------- strategies
def backtest_dca(df: pd.DataFrame, amount: float = 100, every: int = 7,
                 dip_pct: float = 0, dip_multiplier: float = 2.0, start_cash: float | None = None):
    """Buy `amount` every `every` bars; if price is `dip_pct`% below its 30-bar high,
    buy amount * dip_multiplier instead (3Commas-style 'safety order')."""
    n_buys = len(df) // every + 1
    start_cash = start_cash or amount * n_buys * (dip_multiplier if dip_pct else 1)
    b = PaperBroker(cash=start_cash)
    hi30 = df["high"].rolling(30, min_periods=1).max()
    curve = []
    for i, r in df.iterrows():
        if i % every == 0:
            size = amount
            if dip_pct and r["close"] <= hi30[i] * (1 - dip_pct / 100):
                size *= dip_multiplier
            b.buy_usd(size, r["close"], r["time"])
        curve.append(b.equity(r["close"]))
    rep = _report(f"DCA {amount}/{every} bars" + (f" +dip {dip_pct}%" if dip_pct else ""),
                  b, start_cash, pd.Series(curve), df["close"].iloc[-1])
    deployed = rep["total_buy_volume_usd"]
    rep["return_on_money_invested_pct"] = round(((b.qty * df["close"].iloc[-1]) / deployed - 1) * 100, 2) if deployed else 0
    return rep, b


def backtest_grid(df: pd.DataFrame, low: float, high: float, levels: int = 20, capital: float = 5000):
    """Classic spot grid: buy at each level down, sell one level up. Uses intrabar high/low."""
    grid = np.linspace(low, high, levels + 1)
    per = capital / levels
    b = PaperBroker(cash=capital)
    holding = {}  # grid index -> qty bought at grid[i]
    p0 = df["close"].iloc[0]
    for i in range(levels):  # pre-buy levels above the start price, like 3Commas does
        if grid[i] > p0:
            before = b.qty
            b.buy_usd(per, p0, df["time"].iloc[0])
            holding[i] = b.qty - before
    curve = []
    for _, r in df.iterrows():
        for i in range(levels):
            buy_px, sell_px = grid[i], grid[i + 1]
            if i not in holding and r["low"] <= buy_px and b.cash >= per * 0.99:
                before = b.qty
                b.buy_usd(per, buy_px, r["time"])
                holding[i] = b.qty - before
            elif i in holding and r["high"] >= sell_px:
                b.sell_qty(holding.pop(i), sell_px, r["time"])
        curve.append(b.equity(r["close"]))
    return _report(f"Grid {low:,.0f}-{high:,.0f} x{levels}", b, capital,
                   pd.Series(curve), df["close"].iloc[-1]), b


def backtest_sma(df: pd.DataFrame, fast: int = 50, slow: int = 200, capital: float = 10000):
    """All-in when fast SMA > slow SMA, all-out otherwise. Compared to buy & hold."""
    f, s = ta.sma(df["close"], fast), ta.sma(df["close"], slow)
    b, curve = PaperBroker(cash=capital), []
    for i, r in df.iterrows():
        if pd.notna(s[i]):
            if f[i] > s[i] and b.cash > 1:
                b.buy_usd(b.cash, r["close"], r["time"])
            elif f[i] < s[i] and b.qty > 0:
                b.sell_qty(b.qty, r["close"], r["time"])
        curve.append(b.equity(r["close"]))
    rep = _report(f"SMA {fast}/{slow} cross", b, capital, pd.Series(curve), df["close"].iloc[-1])
    rep["buy_and_hold_pct"] = round((df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100, 2)
    return rep, b


# --------------------------------------------------------------------- running a bot
def run_dca_bot(symbol: str, amount: float, every_hours: float, live: bool = False,
                exchange: str = "coinbase", state_file: str = ".bot_state.json"):
    """Recurring buy. Paper by default; state survives restarts."""
    product = f"{symbol.upper()}-USD"
    broker = LiveBroker(exchange, f"{symbol.upper()}/USD") if live else PaperBroker()
    try:
        st = json.load(open(state_file))
    except Exception:
        st = {"last_buy": 0}
    mode = "LIVE" if live else "PAPER"
    print(f"[{mode}] DCA {amount} USD of {symbol} every {every_hours}h. Ctrl+C to stop.")
    while True:
        if time.time() - st["last_buy"] >= every_hours * 3600:
            px = Coinbase().price(product)
            broker.buy_usd(amount, px)
            st["last_buy"] = time.time()
            json.dump(st, open(state_file, "w"))
            msg = f"[{mode}] bought ${amount} {symbol} @ {px:,.2f}"
            if not live:
                msg += f" | paper equity {broker.equity(px):,.2f}"
            print(msg)
        time.sleep(60)
