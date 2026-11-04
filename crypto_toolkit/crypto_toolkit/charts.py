"""TradingView replacement, part 1: interactive candlestick charts with indicators.

Writes a self-contained HTML file (zoom, pan, hover) you open in any browser:
    python -m crypto_toolkit chart BTC --interval 1d --out btc.html
"""
from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import indicators as ta
from .aggregator import agg_ohlcv
from .free_apis import Coinbase, Kraken


def load(symbol: str, interval: str = "1d", source: str = "kraken"):
    if source == "kraken" and interval in Kraken.INTERVAL:
        base = {"BTC": "XBT"}.get(symbol.upper(), symbol.upper())
        return Kraken().ohlc(f"{base}USD", interval)
    if source == "aggregate":
        return agg_ohlcv(symbol, interval)
    return Coinbase().candles(f"{symbol.upper()}-USD", interval)


def chart(symbol: str, interval: str = "1d", source: str = "kraken",
          out: str | None = None) -> str:
    df = ta.add_all(load(symbol, interval, source))
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03,
                        row_heights=[0.6, 0.2, 0.2],
                        subplot_titles=(f"{symbol.upper()}/USD · {interval}", "RSI 14", "MACD"))
    fig.add_trace(go.Candlestick(x=df["time"], open=df["open"], high=df["high"], low=df["low"],
                                 close=df["close"], name="Price"), row=1, col=1)
    for col, color in (("sma_50", "#f2a33a"), ("sma_200", "#7b61ff")):
        if df[col].notna().any():
            fig.add_trace(go.Scatter(x=df["time"], y=df[col], name=col.upper(),
                                     line=dict(width=1.4, color=color)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["time"], y=df["bb_upper"], name="BB upper",
                             line=dict(width=0.8, color="#999", dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["time"], y=df["bb_lower"], name="BB lower",
                             line=dict(width=0.8, color="#999", dash="dot")), row=1, col=1)
    fig.add_trace(go.Scatter(x=df["time"], y=df["rsi_14"], name="RSI",
                             line=dict(color="#2a9d8f")), row=2, col=1)
    for lvl in (30, 70):
        fig.add_hline(y=lvl, line=dict(color="#bbb", dash="dash", width=1), row=2, col=1)
    fig.add_trace(go.Bar(x=df["time"], y=df["hist"], name="MACD hist",
                         marker_color=["#26a69a" if h >= 0 else "#ef5350" for h in df["hist"]]),
                  row=3, col=1)
    fig.add_trace(go.Scatter(x=df["time"], y=df["macd"], name="MACD", line=dict(width=1)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df["time"], y=df["signal"], name="Signal", line=dict(width=1)), row=3, col=1)
    fig.update_layout(height=850, template="plotly_white", xaxis_rangeslider_visible=False,
                      legend=dict(orientation="h", y=1.09), margin=dict(l=40, r=20, t=110, b=30))
    out = out or f"{symbol.lower()}_{interval}.html"
    fig.write_html(out, include_plotlyjs="cdn")
    return out
