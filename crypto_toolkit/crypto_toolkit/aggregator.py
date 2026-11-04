"""CryptoCompare replacement (its free tier was retired; it now needs a paid key).

CryptoCompare's main value was an aggregated, volume-weighted price across exchanges
(the "CCCAGG" index) plus historical candles. This rebuilds both from free exchange APIs:

    agg_price("BTC")           -> volume-weighted price across Coinbase, Kraken, Binance.US
    agg_ohlcv("BTC", "1d")     -> merged daily candles (volume-weighted close, summed volume)
    price_multi(["BTC","ETH"]) -> {"BTC": ..., "ETH": ...}
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from .free_apis import BinanceUS, Coinbase, Kraken

# Kraken uses legacy names for a few assets.
_KRAKEN_ALIAS = {"BTC": "XBT", "DOGE": "XDG"}


def _sources(base: str, quote: str = "USD"):
    kb = _KRAKEN_ALIAS.get(base, base)
    bq = "USDT" if quote == "USD" else quote
    return {
        "coinbase": (lambda: Coinbase().ticker(f"{base}-{quote}"),
                     lambda t: (float(t["price"]), float(t["volume"]))),
        "kraken": (lambda: Kraken().ticker(f"{kb}{quote}"),
                   lambda t: (float(t["c"][0]), float(t["v"][1]))),
        "binance_us": (lambda: BinanceUS().ticker_24h(f"{base}{bq}"),
                       lambda t: (float(t["lastPrice"]), float(t["volume"]))),
    }


def exchange_prices(base: str, quote: str = "USD") -> pd.DataFrame:
    """Last price and 24h base-volume from each exchange (skips ones that don't list it)."""
    rows = []

    def fetch(item):
        name, (call, parse) = item
        try:
            price, vol = parse(call())
            return {"exchange": name, "price": price, "volume_24h": vol}
        except Exception as e:  # pair not listed, outage, etc.
            return {"exchange": name, "price": None, "volume_24h": None, "error": str(e)[:80]}

    with ThreadPoolExecutor(max_workers=3) as ex:
        rows = list(ex.map(fetch, _sources(base.upper(), quote.upper()).items()))
    return pd.DataFrame(rows)


def agg_price(base: str, quote: str = "USD") -> dict:
    df = exchange_prices(base, quote).dropna(subset=["price"])
    if df.empty:
        raise RuntimeError(f"No exchange returned a price for {base}/{quote}")
    w = df["volume_24h"].clip(lower=0)
    vwap = (df["price"] * w).sum() / w.sum() if w.sum() > 0 else df["price"].mean()
    spread = (df["price"].max() - df["price"].min()) / vwap * 100
    return {"symbol": f"{base}/{quote}", "price": round(vwap, 8),
            "sources": len(df), "spread_pct": round(spread, 4),
            "by_exchange": df.to_dict("records")}


def price_multi(bases: list[str], quote: str = "USD") -> dict:
    return {b: agg_price(b, quote)["price"] for b in bases}


def agg_ohlcv(base: str, interval: str = "1d", quote: str = "USD") -> pd.DataFrame:
    """Merge candles from several exchanges into one series.

    open/high/low/close are volume-weighted across exchanges; volume is summed.
    """
    base, quote = base.upper(), quote.upper()
    kb = _KRAKEN_ALIAS.get(base, base)
    bq = "USDT" if quote == "USD" else quote
    calls = {
        "coinbase": lambda: Coinbase().candles(f"{base}-{quote}", interval),
        "kraken": lambda: Kraken().ohlc(f"{kb}{quote}", interval),
        "binance_us": lambda: BinanceUS().klines(f"{base}{bq}", interval),
    }
    frames = []
    for name, call in calls.items():
        try:
            df = call()
            df["exchange"] = name
            frames.append(df)
        except Exception:
            pass
    if not frames:
        raise RuntimeError(f"No candles for {base}/{quote}")
    allc = pd.concat(frames)
    allc["w"] = allc["volume"].clip(lower=1e-12)

    def merge(g):
        w = g["w"]
        return pd.Series({
            "open": (g["open"] * w).sum() / w.sum(),
            "high": (g["high"] * w).sum() / w.sum(),
            "low": (g["low"] * w).sum() / w.sum(),
            "close": (g["close"] * w).sum() / w.sum(),
            "volume": g["volume"].sum(),
            "sources": g["exchange"].nunique(),
        })

    out = allc.groupby("time")[["open", "high", "low", "close", "volume", "w", "exchange"]] \
              .apply(merge).reset_index()
    return out.sort_values("time").reset_index(drop=True)
