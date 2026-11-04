"""Command line: python -m crypto_toolkit <command> ...   (run with -h for help)"""
from __future__ import annotations

import argparse
import json

import pandas as pd

pd.set_option("display.width", 200, "display.max_columns", 30)


def _p(obj):
    if isinstance(obj, pd.DataFrame):
        print(obj.to_string())
    else:
        print(json.dumps(obj, indent=2, default=str))


def main():
    ap = argparse.ArgumentParser(prog="crypto_toolkit")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("price", help="aggregated price across exchanges (CryptoCompare-style)")
    s.add_argument("symbols", nargs="+")

    sub.add_parser("market", help="top 25 coins from CoinGecko")
    sub.add_parser("feargreed", help="Fear & Greed Index, last 14 days")

    s = sub.add_parser("ta", help="indicator summary for a coin")
    s.add_argument("symbol"); s.add_argument("--interval", default="1d")

    s = sub.add_parser("chart", help="interactive HTML candlestick chart")
    s.add_argument("symbol"); s.add_argument("--interval", default="1d")
    s.add_argument("--source", default="kraken", choices=["kraken", "coinbase", "aggregate"])
    s.add_argument("--out")

    sub.add_parser("onchain", help="BTC network, valuation and derivatives dashboard")

    s = sub.add_parser("research", help="Messari-style profile(s)")
    s.add_argument("coin_ids", nargs="+", help="CoinGecko ids, e.g. bitcoin ethereum solana")

    s = sub.add_parser("screener", help="top-N screener with derived ratios")
    s.add_argument("--top", type=int, default=50)
    s.add_argument("--sort", default="market_cap_rank")

    s = sub.add_parser("alerts", help="run alert rules")
    s.add_argument("--rules", default="alerts.json")
    g = s.add_mutually_exclusive_group(); g.add_argument("--once", action="store_true")
    g.add_argument("--watch", action="store_true"); s.add_argument("--every", type=int, default=60)

    s = sub.add_parser("portfolio", help="holdings + capital gains from a trades CSV")
    s.add_argument("csv"); s.add_argument("--method", default="FIFO")
    s.add_argument("--year", type=int); s.add_argument("--export-8949")

    s = sub.add_parser("backtest", help="backtest a bot strategy")
    s.add_argument("strategy", choices=["dca", "grid", "sma"]); s.add_argument("symbol")
    s.add_argument("--amount", type=float, default=100); s.add_argument("--every", type=int, default=7)
    s.add_argument("--dip", type=float, default=0)
    s.add_argument("--low", type=float); s.add_argument("--high", type=float)
    s.add_argument("--levels", type=int, default=20); s.add_argument("--capital", type=float, default=5000)
    s.add_argument("--fast", type=int, default=50); s.add_argument("--slow", type=int, default=200)

    s = sub.add_parser("advise", help="plain-English weekly briefing: what to do and why")
    s.add_argument("--setup", action="store_true"); s.add_argument("--send", action="store_true")
    s.add_argument("--backtest", action="store_true"); s.add_argument("--profile", default="profile.json")

    s = sub.add_parser("bot", help="run a DCA bot (paper unless --live)")
    s.add_argument("kind", choices=["dca"]); s.add_argument("symbol")
    s.add_argument("--amount", type=float, default=25); s.add_argument("--every-hours", type=float, default=24)
    s.add_argument("--live", action="store_true"); s.add_argument("--exchange", default="coinbase")

    a = ap.parse_args()

    if a.cmd == "price":
        from .aggregator import agg_price
        for sym in a.symbols:
            _p(agg_price(sym))
    elif a.cmd == "market":
        from .free_apis import CoinGecko
        _p(CoinGecko().markets(per_page=25)[["market_cap_rank", "symbol", "current_price", "market_cap",
                                             "price_change_percentage_24h_in_currency",
                                             "price_change_percentage_7d_in_currency"]])
    elif a.cmd == "feargreed":
        from .free_apis import fear_greed
        _p(fear_greed(14))
    elif a.cmd == "ta":
        from .charts import load
        from .indicators import signal_summary
        _p(signal_summary(load(a.symbol, a.interval)))
    elif a.cmd == "chart":
        from .charts import chart
        print("Wrote", chart(a.symbol, a.interval, a.source, a.out))
    elif a.cmd == "onchain":
        from .onchain import dashboard
        _p(dashboard())
    elif a.cmd == "research":
        from .research import compare, profile
        _p(profile(a.coin_ids[0]) if len(a.coin_ids) == 1 else compare(a.coin_ids))
    elif a.cmd == "screener":
        from .research import screener
        _p(screener(a.top).sort_values(a.sort))
    elif a.cmd == "alerts":
        from .alerts import check_all, watch
        watch(a.rules, a.every) if a.watch else check_all(a.rules)
    elif a.cmd == "portfolio":
        from . import portfolio as pf
        lots, realized, income = pf.compute(pf.load_trades(a.csv), a.method)
        print("\nHOLDINGS"); _p(pf.holdings(lots))
        print("\nTAX SUMMARY"); _p(pf.tax_summary(realized, income, a.year))
        if a.export_8949:
            print("Wrote", pf.form_8949(realized, a.export_8949, a.year))
    elif a.cmd == "backtest":
        from . import bot
        df = bot.history(a.symbol)
        print(f"{len(df)} daily bars {df['time'].iloc[0].date()} -> {df['time'].iloc[-1].date()}")
        if a.strategy == "dca":
            rep, _ = bot.backtest_dca(df, a.amount, a.every, a.dip)
        elif a.strategy == "grid":
            lo = a.low or float(df["low"].min()); hi = a.high or float(df["high"].max())
            rep, _ = bot.backtest_grid(df, lo, hi, a.levels, a.capital)
        else:
            rep, _ = bot.backtest_sma(df, a.fast, a.slow, a.capital)
        _p(rep)
    elif a.cmd == "advise":
        from . import advisor
        if a.setup:
            advisor.setup(a.profile)
        elif a.backtest:
            _p(advisor.backtest())
        else:
            text = advisor.briefing(advisor.load_profile(a.profile))
            print(text)
            if a.send:
                from .alerts import notify
                notify("Your weekly crypto briefing", text)
    elif a.cmd == "bot":
        from .bot import run_dca_bot
        if a.live and input("LIVE trading with real money. Type YES to continue: ") != "YES":
            return
        run_dca_bot(a.symbol, a.amount, a.every_hours, a.live, a.exchange)


if __name__ == "__main__":
    main()
