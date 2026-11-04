"""Glassnode / CryptoQuant replacement built on free data.

Glassnode has no free API; CryptoQuant's on-chain API sits on paid plans. This module
computes the commonly used Bitcoin on-chain and derivatives metrics from free sources:

  blockchain.info charts API   tx count, active addresses, hash rate, miner revenue, tx volume
  mempool.space                fees, mempool backlog, difficulty adjustment, hashrate
  Kraken Futures               perpetual funding rates and open interest
  CoinGecko                    market cap / price history

Metrics that need the full UTXO set (MVRV, SOPR, realized cap, exchange flows) can't be
computed from these APIs; for those you'd run your own Bitcoin node — see README.
"""
from __future__ import annotations

import pandas as pd

from .free_apis import Kraken
from .http import get_json

BCI = "https://api.blockchain.info/charts"
MEMPOOL = "https://mempool.space/api"

CHARTS = {
    "transactions": "n-transactions",
    "active_addresses": "n-unique-addresses",
    "hash_rate_ths": "hash-rate",
    "miner_revenue_usd": "miners-revenue",
    "tx_volume_usd": "estimated-transaction-volume-usd",
    "market_price_usd": "market-price",
    "market_cap_usd": "market-cap",
    "fees_usd": "transaction-fees-usd",
    "difficulty": "difficulty",
}


def chart(name: str, timespan: str = "1year") -> pd.Series:
    """Any blockchain.info chart, e.g. chart('hash_rate_ths', '2years')."""
    slug = CHARTS.get(name, name)
    d = get_json(f"{BCI}/{slug}", {"timespan": timespan, "format": "json", "sampled": "false"})
    s = pd.Series({pd.to_datetime(v["x"], unit="s", utc=True): v["y"] for v in d["values"]},
                  name=name)
    return s.sort_index()


def network_snapshot() -> dict:
    """Live Bitcoin network state from mempool.space."""
    fees = get_json(f"{MEMPOOL}/v1/fees/recommended")
    mp = get_json(f"{MEMPOOL}/mempool")
    diff = get_json(f"{MEMPOOL}/v1/difficulty-adjustment")
    hr = get_json(f"{MEMPOOL}/v1/mining/hashrate/3d")
    return {
        "block_height": int(get_json(f"{MEMPOOL}/blocks/tip/height")),
        "fees_sat_vb": fees,
        "mempool_tx_count": mp["count"],
        "mempool_vsize_mb": round(mp["vsize"] / 1e6, 2),
        "hashrate_ehs": round(hr["currentHashrate"] / 1e18, 1),
        "difficulty_change_pct": round(diff["difficultyChange"], 2),
        "blocks_to_retarget": diff["remainingBlocks"],
    }


def valuation_metrics(timespan: str = "2years") -> pd.DataFrame:
    """Daily valuation ratios Glassnode charges for, computed from free series.

      mayer_multiple   price / 200-day SMA (>2.4 historically overheated, <1 cheap)
      nvt_ratio        market cap / 90d-avg on-chain USD volume (high = price outpacing usage)
      puell_multiple   daily miner revenue / its 365-day average (miner-profit cycle)
      hash_ribbon      30d vs 60d hash-rate SMA ("capitulation" when 30d < 60d)
    """
    price = chart("market_price_usd", timespan)
    mcap = chart("market_cap_usd", timespan)
    vol = chart("tx_volume_usd", timespan)
    rev = chart("miner_revenue_usd", timespan)
    hr = chart("hash_rate_ths", timespan)
    df = pd.concat([price, mcap, vol, rev, hr], axis=1).resample("1D").last().ffill()
    df["mayer_multiple"] = df["market_price_usd"] / df["market_price_usd"].rolling(200).mean()
    df["nvt_ratio"] = df["market_cap_usd"] / df["tx_volume_usd"].rolling(90).mean()
    df["puell_multiple"] = df["miner_revenue_usd"] / df["miner_revenue_usd"].rolling(365, min_periods=180).mean()
    df["hash_sma30"] = df["hash_rate_ths"].rolling(30).mean()
    df["hash_sma60"] = df["hash_rate_ths"].rolling(60).mean()
    df["hash_ribbon_capitulation"] = df["hash_sma30"] < df["hash_sma60"]
    return df


def derivatives(symbols=("PF_XBTUSD", "PF_ETHUSD", "PF_SOLUSD")) -> pd.DataFrame:
    """Perp funding & open interest (CryptoQuant 'market data' equivalent), from Kraken Futures.

    funding_apr_pct: relative hourly funding annualised. Positive = longs pay shorts.
    """
    t = Kraken().futures_tickers()
    t = t[t["symbol"].isin(symbols)].copy()
    t["funding_hourly_pct"] = t["relativeFundingRate"] * 100
    t["funding_apr_pct"] = t["relativeFundingRate"] * 24 * 365 * 100
    t["open_interest_usd"] = t["openInterest"] * t["markPrice"]
    t["basis_pct"] = (t["markPrice"] / t["indexPrice"] - 1) * 100
    return t[["symbol", "markPrice", "indexPrice", "basis_pct", "funding_hourly_pct",
              "funding_apr_pct", "openInterest", "open_interest_usd", "vol24h"]].reset_index(drop=True)


def dashboard() -> dict:
    """One-call summary of everything above (latest values)."""
    v = valuation_metrics("2years").iloc[-1]
    return {
        "network": network_snapshot(),
        "valuation": {k: round(float(v[k]), 3) for k in
                      ("market_price_usd", "mayer_multiple", "nvt_ratio", "puell_multiple")}
                     | {"hash_ribbon_capitulation": bool(v["hash_ribbon_capitulation"])},
        "derivatives": derivatives().round(4).to_dict("records"),
    }
