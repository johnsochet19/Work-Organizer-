"""CoinTracking / Koinly replacement: portfolio tracking and capital-gains lots.

Input: a CSV of your trades (see trades.example.csv):
    date,type,asset,quantity,price_usd,fee_usd,exchange,notes
    type = buy | sell | income | gift_in | spend | transfer   (transfer = moved, not taxable)

    python -m crypto_toolkit portfolio trades.csv --method FIFO --year 2026

Outputs holdings with live value + unrealized P&L, realized gains split short/long term
(held > 365 days), and an IRS Form 8949-style CSV. Methods: FIFO, LIFO, HIFO.
This is a calculator, not tax advice — have a CPA review before filing.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .free_apis import Coinbase


@dataclass
class Lot:
    asset: str
    qty: float
    cost_per_unit: float
    acquired: pd.Timestamp


def load_trades(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df["type"] = df["type"].str.lower().str.strip()
    df["asset"] = df["asset"].str.upper().str.strip()
    for c in ("quantity", "price_usd", "fee_usd"):
        df[c] = pd.to_numeric(df.get(c, 0), errors="coerce").fillna(0.0)
    return df.sort_values("date", kind="stable").reset_index(drop=True)


def compute(trades: pd.DataFrame, method: str = "FIFO"):
    method = method.upper()
    lots: dict[str, list[Lot]] = {}
    realized, income = [], []

    for t in trades.itertuples():
        a, q, px, fee = t.asset, t.quantity, t.price_usd, t.fee_usd
        book = lots.setdefault(a, [])
        if t.type in ("buy", "income", "gift_in"):
            book.append(Lot(a, q, (q * px + fee) / q if q else 0, t.date))
            if t.type == "income":
                income.append({"date": t.date, "asset": a, "quantity": q, "usd_value": q * px})
        elif t.type in ("sell", "spend"):
            remaining, proceeds_unit = q, (q * px - fee) / q if q else 0
            while remaining > 1e-12:
                if not book:
                    raise ValueError(f"{t.date.date()}: selling {q} {a} but holdings run out "
                                     f"(missing buy or transfer-in rows?)")
                if method == "FIFO":
                    idx = 0
                elif method == "LIFO":
                    idx = len(book) - 1
                elif method == "HIFO":
                    idx = max(range(len(book)), key=lambda i: book[i].cost_per_unit)
                else:
                    raise ValueError("method must be FIFO, LIFO or HIFO")
                lot = book[idx]
                take = min(lot.qty, remaining)
                held = (t.date - lot.acquired).days
                realized.append({
                    "description": f"{take:.8f} {a}",
                    "date_acquired": lot.acquired.date(), "date_sold": t.date.date(),
                    "proceeds": round(take * proceeds_unit, 2),
                    "cost_basis": round(take * lot.cost_per_unit, 2),
                    "gain_loss": round(take * (proceeds_unit - lot.cost_per_unit), 2),
                    "term": "long" if held > 365 else "short", "asset": a,
                })
                lot.qty -= take
                remaining -= take
                if lot.qty <= 1e-12:
                    book.pop(idx)
        elif t.type == "transfer":
            continue  # wallet-to-wallet move; basis carries over
        else:
            raise ValueError(f"Unknown type '{t.type}' on {t.date.date()}")
    return lots, pd.DataFrame(realized), pd.DataFrame(income)


def live_prices(assets) -> dict:
    out, cb = {}, Coinbase()
    for a in assets:
        if a in ("USD", "USDC", "USDT"):
            out[a] = 1.0
            continue
        try:
            out[a] = cb.price(f"{a}-USD")
        except Exception:
            out[a] = float("nan")
    return out


def holdings(lots: dict[str, list[Lot]], prices: dict | None = None) -> pd.DataFrame:
    rows = []
    for a, book in lots.items():
        qty = sum(l.qty for l in book)
        if qty <= 1e-12:
            continue
        rows.append({"asset": a, "quantity": qty, "cost_basis": sum(l.qty * l.cost_per_unit for l in book)})
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    prices = prices if prices is not None else live_prices(df["asset"])
    df["price"] = df["asset"].map(prices)
    df["value"] = df["quantity"] * df["price"]
    df["unrealized_pnl"] = df["value"] - df["cost_basis"]
    df["unrealized_pct"] = df["unrealized_pnl"] / df["cost_basis"] * 100
    df["allocation_pct"] = df["value"] / df["value"].sum() * 100
    return df.sort_values("value", ascending=False).round(4).reset_index(drop=True)


def tax_summary(realized: pd.DataFrame, income: pd.DataFrame, year: int | None = None) -> dict:
    r = realized.copy()
    if year and not r.empty:
        r = r[pd.to_datetime(r["date_sold"]).dt.year == year]
    i = income.copy()
    if year and not i.empty:
        i = i[i["date"].dt.year == year]
    g = lambda term: float(r.loc[r["term"] == term, "gain_loss"].sum()) if not r.empty else 0.0  # noqa: E731
    return {"year": year or "all", "short_term_gain": round(g("short"), 2),
            "long_term_gain": round(g("long"), 2),
            "total_realized": round(g("short") + g("long"), 2),
            "income_usd": round(float(i["usd_value"].sum()) if not i.empty else 0.0, 2),
            "disposals": len(r)}


def form_8949(realized: pd.DataFrame, path: str, year: int | None = None) -> str:
    r = realized
    if year and not r.empty:
        r = r[pd.to_datetime(r["date_sold"]).dt.year == year]
    r[["description", "date_acquired", "date_sold", "proceeds", "cost_basis", "gain_loss", "term"]] \
        .to_csv(path, index=False)
    return path
