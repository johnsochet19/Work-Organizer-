"""Messari replacement: asset profiles and screener built on CoinGecko's free plan.

Messari's API is now enterprise-only. This produces the fundamentals most people used it for:
supply/dilution, valuation vs. all-time high, returns, liquidity, developer & community stats,
and a screener across the top N coins.
"""
from __future__ import annotations

import pandas as pd

from .free_apis import CoinGecko


def profile(coin_id: str, cg: CoinGecko | None = None) -> dict:
    cg = cg or CoinGecko()
    c = cg.coin(coin_id)
    m = c["market_data"]
    usd = lambda k: (m.get(k) or {}).get("usd")  # noqa: E731
    circ, total, mx = m.get("circulating_supply"), m.get("total_supply"), m.get("max_supply")
    mcap, fdv, vol = usd("market_cap"), usd("fully_diluted_valuation"), usd("total_volume")
    dev = c.get("developer_data") or {}
    return {
        "id": c["id"], "symbol": c["symbol"].upper(), "name": c["name"],
        "categories": c.get("categories", []),
        "genesis_date": c.get("genesis_date"),
        "hashing_algorithm": c.get("hashing_algorithm"),
        "homepage": (c.get("links", {}).get("homepage") or [None])[0],
        "price_usd": usd("current_price"),
        "market_cap_usd": mcap, "market_cap_rank": c.get("market_cap_rank"),
        "fdv_usd": fdv,
        "mcap_to_fdv": round(mcap / fdv, 3) if mcap and fdv else None,
        "circulating_supply": circ, "total_supply": total, "max_supply": mx,
        "pct_supply_issued": round(circ / mx * 100, 2) if circ and mx else None,
        "volume_24h_usd": vol,
        "volume_to_mcap": round(vol / mcap, 4) if vol and mcap else None,
        "ath_usd": usd("ath"), "ath_date": (m.get("ath_date") or {}).get("usd"),
        "pct_from_ath": (m.get("ath_change_percentage") or {}).get("usd"),
        "return_7d_pct": m.get("price_change_percentage_7d"),
        "return_30d_pct": m.get("price_change_percentage_30d"),
        "return_1y_pct": m.get("price_change_percentage_1y"),
        "github_stars": dev.get("stars"), "github_commits_4w": dev.get("commit_count_4_weeks"),
        "description": (c.get("description", {}).get("en") or "")[:600],
    }


def screener(top: int = 100, cg: CoinGecko | None = None) -> pd.DataFrame:
    """Top-N coins with derived ratios; sort/filter it like a Messari screener."""
    cg = cg or CoinGecko()
    frames, page = [], 1
    while sum(len(f) for f in frames) < top:
        frames.append(cg.markets(per_page=min(250, top), page=page))
        page += 1
    df = pd.concat(frames).head(top)
    df["mcap_to_fdv"] = df["market_cap"] / df["fully_diluted_valuation"]
    df["volume_to_mcap"] = df["total_volume"] / df["market_cap"]
    df["pct_supply_issued"] = df["circulating_supply"] / df["max_supply"] * 100
    cols = ["market_cap_rank", "symbol", "name", "current_price", "market_cap",
            "fully_diluted_valuation", "mcap_to_fdv", "total_volume", "volume_to_mcap",
            "pct_supply_issued", "ath_change_percentage",
            "price_change_percentage_24h_in_currency", "price_change_percentage_7d_in_currency",
            "price_change_percentage_30d_in_currency"]
    return df[[c for c in cols if c in df.columns]].reset_index(drop=True)


def compare(coin_ids: list[str]) -> pd.DataFrame:
    cg = CoinGecko()
    return pd.DataFrame([profile(c, cg) for c in coin_ids]).drop(columns=["description"]).set_index("symbol").T
