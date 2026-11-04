"""Clients for the crypto APIs that are FREE to use.

  CoinGecko       free Demo key (works keyless at lower limits)   docs.coingecko.com
  CoinMarketCap   free Basic key required                          coinmarketcap.com/api/documentation
  Binance.US      public market data, no key (binance.com blocks US IPs)
  Coinbase        public Exchange market data, no key
  Kraken          public spot + futures market data, no key
  Alternative.me  Fear & Greed Index, no key

Every method returns plain dicts/lists or pandas DataFrames.
"""
from __future__ import annotations

import pandas as pd

from .http import env, get_json


def _ohlcv_frame(rows, cols) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=cols)[["time", "open", "high", "low", "close", "volume"]]
    df = df.astype({c: float for c in ("open", "high", "low", "close", "volume")})
    return df.sort_values("time").reset_index(drop=True)


# --------------------------------------------------------------------------- CoinGecko
class CoinGecko:
    """Free Demo plan: get a key at coingecko.com/en/developers/dashboard (no card)."""
    BASE = "https://api.coingecko.com/api/v3"

    def __init__(self, api_key: str | None = None):
        key = api_key or env("COINGECKO_API_KEY")
        self.headers = {"x-cg-demo-api-key": key} if key else {}

    def _get(self, path, **params):
        return get_json(self.BASE + path, params=params, headers=self.headers)

    def price(self, ids: str | list, vs: str = "usd", **extra) -> dict:
        ids = ",".join(ids) if isinstance(ids, list) else ids
        return self._get("/simple/price", ids=ids, vs_currencies=vs,
                         include_market_cap="true", include_24hr_vol="true",
                         include_24hr_change="true", **extra)

    def markets(self, vs: str = "usd", per_page: int = 100, page: int = 1,
                ids: str | None = None, category: str | None = None) -> pd.DataFrame:
        p = dict(vs_currency=vs, per_page=per_page, page=page,
                 price_change_percentage="1h,24h,7d,30d")
        if ids:
            p["ids"] = ids
        if category:
            p["category"] = category
        return pd.DataFrame(self._get("/coins/markets", **p))

    def coin(self, coin_id: str) -> dict:
        return self._get(f"/coins/{coin_id}", localization="false", tickers="false",
                         community_data="true", developer_data="true")

    def market_chart(self, coin_id: str, days: int | str = 30, vs: str = "usd") -> pd.DataFrame:
        """Price/market-cap/volume history. Demo plan: up to 365 days."""
        d = self._get(f"/coins/{coin_id}/market_chart", vs_currency=vs, days=days)
        df = pd.DataFrame(d["prices"], columns=["time", "price"])
        df["market_cap"] = [x[1] for x in d["market_caps"]]
        df["volume"] = [x[1] for x in d["total_volumes"]]
        df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
        return df

    def ohlc(self, coin_id: str, days: int = 30, vs: str = "usd") -> pd.DataFrame:
        d = self._get(f"/coins/{coin_id}/ohlc", vs_currency=vs, days=days)
        df = pd.DataFrame(d, columns=["time", "open", "high", "low", "close"])
        df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
        df["volume"] = float("nan")
        return df

    def global_data(self) -> dict:
        return self._get("/global")["data"]

    def trending(self) -> dict:
        return self._get("/search/trending")

    def search(self, query: str) -> dict:
        return self._get("/search", query=query)

    def categories(self) -> pd.DataFrame:
        return pd.DataFrame(self._get("/coins/categories"))


# ----------------------------------------------------------------------- CoinMarketCap
class CoinMarketCap:
    """Free Basic plan: sign up at pro.coinmarketcap.com (key required, no history)."""
    BASE = "https://pro-api.coinmarketcap.com"

    def __init__(self, api_key: str | None = None):
        key = api_key or env("CMC_API_KEY")
        if not key:
            raise ValueError("Set CMC_API_KEY (free at pro.coinmarketcap.com/signup)")
        self.headers = {"X-CMC_PRO_API_KEY": key, "Accept": "application/json"}

    def _get(self, path, **params):
        return get_json(self.BASE + path, params=params, headers=self.headers)["data"]

    def listings(self, limit: int = 100, convert: str = "USD") -> pd.DataFrame:
        rows = self._get("/v1/cryptocurrency/listings/latest", limit=limit, convert=convert)
        for r in rows:
            r.update({f"q_{k}": v for k, v in r.pop("quote")[convert].items()})
        return pd.DataFrame(rows)

    def quotes(self, symbols: str, convert: str = "USD") -> dict:
        return self._get("/v2/cryptocurrency/quotes/latest", symbol=symbols, convert=convert)

    def info(self, symbols: str) -> dict:
        return self._get("/v2/cryptocurrency/info", symbol=symbols)

    def global_metrics(self, convert: str = "USD") -> dict:
        return self._get("/v1/global-metrics/quotes/latest", convert=convert)

    def fear_greed(self) -> dict:
        return self._get("/v3/fear-and-greed/latest")


# ------------------------------------------------------------------------ Binance (US)
class BinanceUS:
    """Public market data. binance.com returns 'restricted location' from the US."""
    BASE = "https://api.binance.us"

    def __init__(self, base: str | None = None):
        self.base = base or env("BINANCE_BASE", self.BASE)

    def price(self, symbol: str = "BTCUSDT") -> float:
        return float(get_json(f"{self.base}/api/v3/ticker/price", {"symbol": symbol})["price"])

    def ticker_24h(self, symbol: str = "BTCUSDT") -> dict:
        return get_json(f"{self.base}/api/v3/ticker/24hr", {"symbol": symbol})

    def order_book(self, symbol: str = "BTCUSDT", limit: int = 100) -> dict:
        return get_json(f"{self.base}/api/v3/depth", {"symbol": symbol, "limit": limit})

    def klines(self, symbol: str = "BTCUSDT", interval: str = "1d", limit: int = 500) -> pd.DataFrame:
        rows = get_json(f"{self.base}/api/v3/klines",
                        {"symbol": symbol, "interval": interval, "limit": limit})
        cols = ["time", "open", "high", "low", "close", "volume", "close_time", "qv", "n", "tb", "tq", "x"]
        df = _ohlcv_frame(rows, cols)
        df["time"] = pd.to_datetime(df["time"], unit="ms", utc=True)
        return df

    def stream_url(self, symbol: str = "btcusdt", channel: str = "trade") -> str:
        """WebSocket URL for live data, e.g. use with the `websockets` package."""
        return f"wss://stream.binance.us:9443/ws/{symbol.lower()}@{channel}"


# ---------------------------------------------------------------------------- Coinbase
class Coinbase:
    BASE = "https://api.exchange.coinbase.com"
    GRAN = {"1m": 60, "5m": 300, "15m": 900, "1h": 3600, "6h": 21600, "1d": 86400}

    def ticker(self, product: str = "BTC-USD") -> dict:
        return get_json(f"{self.BASE}/products/{product}/ticker")

    def price(self, product: str = "BTC-USD") -> float:
        return float(self.ticker(product)["price"])

    def order_book(self, product: str = "BTC-USD", level: int = 2) -> dict:
        return get_json(f"{self.BASE}/products/{product}/book", {"level": level})

    def candles(self, product: str = "BTC-USD", interval: str = "1d") -> pd.DataFrame:
        rows = get_json(f"{self.BASE}/products/{product}/candles",
                        {"granularity": self.GRAN[interval]})
        df = _ohlcv_frame(rows, ["time", "low", "high", "open", "close", "volume"])
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        return df

    def products(self) -> list:
        return get_json(f"{self.BASE}/products")

    stream_url = "wss://ws-feed.exchange.coinbase.com"


# ------------------------------------------------------------------------------ Kraken
class Kraken:
    BASE = "https://api.kraken.com/0/public"
    FUTURES = "https://futures.kraken.com/derivatives/api/v3"
    INTERVAL = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440, "1w": 10080}

    def _get(self, path, **params):
        d = get_json(f"{self.BASE}/{path}", params)
        if d.get("error"):
            raise RuntimeError(d["error"])
        return d["result"]

    def ticker(self, pair: str = "XBTUSD") -> dict:
        return next(iter(self._get("Ticker", pair=pair).values()))

    def price(self, pair: str = "XBTUSD") -> float:
        return float(self.ticker(pair)["c"][0])

    def order_book(self, pair: str = "XBTUSD", count: int = 100) -> dict:
        return next(iter(self._get("Depth", pair=pair, count=count).values()))

    def ohlc(self, pair: str = "XBTUSD", interval: str = "1d") -> pd.DataFrame:
        res = self._get("OHLC", pair=pair, interval=self.INTERVAL[interval])
        rows = next(v for k, v in res.items() if k != "last")
        df = _ohlcv_frame(rows, ["time", "open", "high", "low", "close", "vwap", "volume", "count"])
        df["time"] = pd.to_datetime(df["time"].astype(int), unit="s", utc=True)
        return df

    def futures_tickers(self) -> pd.DataFrame:
        """Perpetuals: funding rate, open interest, mark/index price. Free, no key."""
        return pd.DataFrame(get_json(f"{self.FUTURES}/tickers")["tickers"])

    stream_url = "wss://ws.kraken.com/v2"


# ------------------------------------------------------------------- Fear & Greed Index
def fear_greed(limit: int = 30) -> pd.DataFrame:
    """Alternative.me Crypto Fear & Greed Index (0 = extreme fear, 100 = extreme greed)."""
    d = get_json("https://api.alternative.me/fng/", {"limit": limit, "format": "json"})["data"]
    df = pd.DataFrame(d)
    df["value"] = df["value"].astype(int)
    df["time"] = pd.to_datetime(df["timestamp"].astype(int), unit="s", utc=True)
    return df[["time", "value", "value_classification"]].sort_values("time").reset_index(drop=True)
