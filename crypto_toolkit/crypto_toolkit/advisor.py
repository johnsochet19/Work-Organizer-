"""Plain-English crypto mentor for beginners.

It reads the market data the rest of this toolkit collects and answers one question each
week: "What should I do?" The approach is the one an honest human mentor would give a
beginner:

  1. Only put in money you can afford to lose. Emergency fund and high-interest debt come first.
  2. Buy a fixed amount on a schedule (dollar-cost averaging). No guessing tops and bottoms.
  3. Buy a bit MORE when the market is on sale, LESS when it's overheated, nothing when it's euphoric.
  4. Never panic-sell in a crash. Never chase hype. Never use leverage.
  5. Keep the coin mix close to your plan by steering new purchases, not by trading.

    python -m crypto_toolkit advise --setup     # answer 6 questions once
    python -m crypto_toolkit advise             # this week's briefing
    python -m crypto_toolkit advise --send      # also push it to your phone/email (see alerts.py)
    python -m crypto_toolkit advise --backtest  # how these rules did vs. plain weekly buying

This is a rules-based planning aid, not personalized financial advice. Nothing can predict prices.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

import pandas as pd

from . import indicators as ta
from .free_apis import Kraken, fear_greed
from .http import get_json

PROFILE = "profile.json"

MIXES = {
    "low": {"BTC": 1.0},
    "medium": {"BTC": 0.7, "ETH": 0.3},
    "high": {"BTC": 0.6, "ETH": 0.3, "SOL": 0.1},
}

# Market "temperature" -> how much of your normal weekly amount to buy.
LEVELS = [
    (-1.0, "ON SALE", 1.5, "Prices are low compared to their history and people are scared. "
                           "Historically this has been a good time for patient buyers."),
    (-0.3, "CHEAPER THAN USUAL", 1.25, "Prices are below their usual range and the mood is nervous."),
    (0.5, "NORMAL", 1.0, "Nothing unusual. Stick to the plan."),
    (1.2, "PRICEY", 0.5, "Prices are stretched and people are getting greedy. Buy less."),
    (99, "OVERHEATED", 0.0, "Prices and excitement are extreme. This is when beginners buy the top. "
                            "Pause buying."),
]


# --------------------------------------------------------------------------- profile
def setup(path: str = PROFILE) -> dict:
    print("A few questions so the advice fits you. Press Enter to accept the [default].\n")

    def ask(q, default, cast=str):
        a = input(f"{q} [{default}]: ").strip()
        return cast(a) if a else cast(default)

    yes = lambda s: s.lower().startswith("y")  # noqa: E731
    p = {
        "emergency_fund": yes(ask("Do you have 3-6 months of living expenses saved in cash? (y/n)", "y")),
        "high_interest_debt": yes(ask("Do you carry credit-card or other high-interest debt? (y/n)", "n")),
        "weekly_usd": ask("How much could you invest each WEEK without it hurting? ($)", "50", float),
        "max_total_usd": ask("The most you'd EVER put in total, knowing you could lose it? ($)", "5000", float),
        "years": ask("How many years can you leave it alone?", "4", float),
        "risk": ask("Risk level: low / medium / high", "medium").lower(),
        "trades_csv": ask("Path to your trades CSV (leave blank if none yet)", ""),
    }
    if p["risk"] not in MIXES:
        p["risk"] = "medium"
    json.dump(p, open(path, "w"), indent=2)
    print(f"\nSaved to {path}. Run `python -m crypto_toolkit advise` any time.")
    return p


def load_profile(path: str = PROFILE) -> dict:
    if os.path.exists(path):
        return json.load(open(path))
    return {"emergency_fund": True, "high_interest_debt": False, "weekly_usd": 50,
            "max_total_usd": 5000, "years": 4, "risk": "medium", "trades_csv": "", "_default": True}


# ---------------------------------------------------------------------- market read
def _score(name, value, bands):
    """bands: list of (upper_bound, score, plain-English reading)."""
    for upper, s, text in bands:
        if value < upper:
            return {"signal": name, "value": value, "score": s, "reading": text}
    return {"signal": name, "value": value, "score": bands[-1][1], "reading": bands[-1][2]}


def read_signals(btc: pd.DataFrame | None = None, fg_value: int | None = None,
                 funding_apr: float | None = None) -> list[dict]:
    btc = btc if btc is not None else Kraken().ohlc("XBTUSD", "1d")
    c = btc["close"]
    price = float(c.iloc[-1])
    mayer = price / float(c.rolling(200).mean().iloc[-1])
    rsi = float(ta.rsi(c).iloc[-1])
    ath = float(btc["high"].max())
    drawdown = (price / ath - 1) * 100
    if fg_value is None:
        fg_value = int(fear_greed(1)["value"].iloc[-1])
    if funding_apr is None:
        try:
            t = Kraken().futures_tickers()
            funding_apr = float(t.loc[t["symbol"] == "PF_XBTUSD", "relativeFundingRate"].iloc[0]) * 24 * 365 * 100
        except Exception:
            funding_apr = 0.0

    return [
        _score("Price vs. its 200-day average (Mayer Multiple)", round(mayer, 2), [
            (0.8, -2, "far below its long-run average: historically very cheap"),
            (1.0, -1, "below its long-run average: cheaper than usual"),
            (1.5, 0, "around its long-run average: fair"),
            (2.4, 1, "well above its long-run average: getting expensive"),
            (99, 2, "extremely far above average: past bubble territory"),
        ]),
        _score("Crowd mood (Fear & Greed, 0-100)", fg_value, [
            (20, -2, "extreme fear: people are panic-selling"),
            (40, -1, "fear: people are nervous"),
            (60, 0, "neutral"),
            (80, 1, "greed: people are excited"),
            (101, 2, "extreme greed: euphoria"),
        ]),
        _score("Short-term momentum (RSI, 0-100)", round(rsi, 1), [
            (30, -1, "sold off hard recently"),
            (75, 0, "normal"),
            (101, 1, "ran up fast recently"),
        ]),
        _score("Distance from all-time high", round(drawdown, 1), [
            (-50, -1, "more than half off its peak"),
            (-10, 0, "a fair way below its peak"),
            (1, 1, "near its all-time high"),
        ]),
        _score("Traders' borrowing (futures funding, % per year)", round(funding_apr, 1), [
            (-5, -1, "traders are betting on falls"),
            (30, 0, "normal"),
            (9999, 1, "traders are borrowing heavily to bet on rises (fragile)"),
        ]),
    ]


def temperature(signals: list[dict]) -> tuple[float, str, float, str]:
    weights = [2.0, 1.5, 0.75, 0.75, 0.5]  # long-run valuation and crowd mood matter most
    avg = sum(s["score"] * w for s, w in zip(signals, weights)) / sum(weights)
    for upper, label, mult, why in LEVELS:
        if avg <= upper:
            return round(avg, 2), label, mult, why
    return round(avg, 2), *LEVELS[-1][1:]


# ------------------------------------------------------------------------ portfolio
def _holdings(profile):
    path = profile.get("trades_csv")
    if not path or not os.path.exists(path):
        return None
    from . import portfolio as pf
    lots, _, _ = pf.compute(pf.load_trades(path))
    return pf.holdings(lots)


# ------------------------------------------------------------------------- briefing
def briefing(profile: dict | None = None, signals: list[dict] | None = None) -> str:
    p = profile or load_profile()
    out = []
    w = out.append
    w(f"YOUR CRYPTO BRIEFING · {datetime.now():%A %b %d, %Y}")
    w("=" * 60)
    if p.get("_default"):
        w("(Using starter settings. Run `advise --setup` so this fits your situation.)\n")

    # Step 0: the things a real advisor checks before anything else.
    if p.get("high_interest_debt"):
        w("WHAT TO DO THIS WEEK: Don't buy crypto. Put that money toward your high-interest debt.\n")
        w("Why: paying off a credit card charging 20%+ is a guaranteed 20%+ return. No investment")
        w("reliably beats that. Come back once it's paid off.")
        return "\n".join(out)
    if not p.get("emergency_fund"):
        w("WHAT TO DO THIS WEEK: Build your emergency fund first (3-6 months of expenses in savings).\n")
        w("Why: without a cushion, a surprise bill could force you to sell crypto at a bad time.")
        w("If you still want to start, keep it to a token amount (e.g. $10/week).")
        return "\n".join(out)

    sig = signals or read_signals()
    score, label, mult, why = temperature(sig)
    mix = MIXES[p["risk"]]
    hold = _holdings(p)
    invested = float(hold["cost_basis"].sum()) if hold is not None and not hold.empty else 0.0
    room = max(0.0, p["max_total_usd"] - invested)
    amount = round(min(p["weekly_usd"] * mult, room), 2)

    # Steer new money toward whatever is under its target share (rebalancing without selling).
    split = dict(mix)
    if hold is not None and not hold.empty and len(mix) > 1:
        cur = {a: 0.0 for a in mix}
        for r in hold.itertuples():
            if r.asset in cur:
                cur[r.asset] = r.allocation_pct / 100
        gaps = {a: max(0.0, mix[a] - cur[a]) for a in mix}
        if sum(gaps.values()) > 0.05:
            split = {a: g / sum(gaps.values()) for a, g in gaps.items()}

    w(f"MARKET RIGHT NOW: {label}")
    w(f"  {why}\n")
    w("WHAT TO DO THIS WEEK:")
    if room <= 0:
        w(f"  Nothing new. You've reached the ${p['max_total_usd']:,.0f} total you said you'd put in.")
        w("  That limit protects you. Raise it only if your finances have genuinely changed.")
    elif amount == 0:
        w("  Buy nothing this week. Keep your usual amount in savings; it'll be used when prices cool off.")
    else:
        parts = [f"${amount * s:,.2f} of {a}" for a, s in split.items() if amount * s >= 1]
        w(f"  Buy ${amount:,.2f} in total: " + ", ".join(parts) + ".")
        if mult > 1:
            w(f"  That's more than your usual ${p['weekly_usd']:,.0f} because prices are lower than normal.")
        elif mult < 1:
            w(f"  That's less than your usual ${p['weekly_usd']:,.0f} because prices are stretched.")
        w("  Use a regular exchange (Coinbase, Kraken). Choose a plain 'buy', not futures or 'leverage'.")
    w("")

    w("WHY (what the data says):")
    for s in sig:
        arrow = {-2: "cheap ++", -1: "cheap +", 0: "neutral", 1: "pricey +", 2: "pricey ++"}[s["score"]]
        w(f"  • {s['signal']}: {s['value']} → {s['reading']} [{arrow}]")
    w(f"  Overall score {score:+.2f} (−2 = very cheap, +2 = very expensive)\n")

    if hold is not None and not hold.empty:
        val = float(hold["value"].sum())
        pnl = val - invested
        w("YOUR PORTFOLIO:")
        w(f"  Put in ${invested:,.2f} · worth ${val:,.2f} · {'up' if pnl >= 0 else 'down'} ${abs(pnl):,.2f} "
          f"({pnl / invested * 100:+.1f}%)" if invested else "  (empty)")
        for r in hold.itertuples():
            w(f"  {r.asset}: {r.allocation_pct:.0f}% of portfolio (plan: {mix.get(r.asset, 0) * 100:.0f}%)")
        if label == "OVERHEATED" and invested and pnl / invested > 1.0:
            w("  You've more than doubled your money and the market is overheated. Consider selling")
            w("  10-20% to lock in some profit. Taxes apply to the gain; check the portfolio tax report.")
        if pnl < 0 and label in ("ON SALE", "CHEAPER THAN USUAL"):
            w("  Being down is normal in crypto and is exactly when steady buying pays off. Don't sell.")
        w("")

    w("WATCH OUT FOR:")
    w("  • Anyone promising guaranteed returns, 'signals' groups, or DMs offering help: these are scams.")
    w("  • Coins that are suddenly everywhere on social media. By the time you hear, insiders are selling.")
    w("  • Leverage, futures, or 'earn 20% APY' offers. These are how beginners lose everything.")
    w("  • Crypto can fall 50-80% and take years to recover. Only use money you can leave alone for "
      f"{p['years']:.0f}+ years.")
    w("")
    w("Not financial advice. This is a rules-based plan using public data; it cannot predict prices.")
    return "\n".join(out)


# ------------------------------------------------------------------------- backtest
def backtest(weekly: float = 50.0) -> dict:
    """Plain weekly buying vs. this advisor's adjusted buying, same dates, same data."""
    btc = Kraken().ohlc("XBTUSD", "1d")
    fg_all = get_json("https://api.alternative.me/fng/", {"limit": 0})["data"]
    fg = {pd.to_datetime(int(d["timestamp"]), unit="s", utc=True).normalize(): int(d["value"]) for d in fg_all}
    plain_usd = plain_btc = adv_usd = adv_btc = 0.0
    weeks = 0
    for i in range(200, len(btc), 7):
        window = btc.iloc[: i + 1]
        day = window["time"].iloc[-1].normalize()
        f = fg.get(day, 50)
        _, _, mult, _ = temperature(read_signals(window, f, 0.0))
        px = float(window["close"].iloc[-1])
        plain_usd += weekly
        plain_btc += weekly / px
        adv_usd += weekly * mult
        adv_btc += weekly * mult / px
        weeks += 1
    last = float(btc["close"].iloc[-1])
    res = lambda usd, q: {"spent": round(usd, 2), "worth_now": round(q * last, 2),  # noqa: E731
                          "avg_price_paid": round(usd / q, 2), "return_pct": round((q * last / usd - 1) * 100, 2)}
    return {"period": f"{btc['time'].iloc[200].date()} to {btc['time'].iloc[-1].date()} ({weeks} weeks)",
            "plain_weekly_buying": res(plain_usd, plain_btc),
            "advisor_rules": res(adv_usd, adv_btc)}
