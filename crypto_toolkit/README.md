# Crypto Toolkit

Python clients for the crypto APIs that are free, plus code I wrote to replace the paid ones.
I tested every module against the live APIs on Nov 3, 2026.

> No tool here can reliably tell you when to buy or sell. Use these for research and alerts.
> The bot module runs in **paper mode** (simulated trades) unless you turn on live trading on purpose.

## Start here if you're new: the mentor

```bash
python -m crypto_toolkit advise --setup   # 6 questions, once
python -m crypto_toolkit advise           # each week: what to buy, how much, and why
python -m crypto_toolkit advise --send    # same, pushed to your phone/email
```
It checks your safety basics (emergency fund, debt), reads five market signals, and tells you
how much to buy this week (0x to 1.5x your normal amount), split by coin, with plain-English reasons.
It never tells you to panic-sell, and it stops at the total you said you could afford to lose.

## Setup (5 minutes)

```bash
pip install -r requirements.txt
cp .env.example .env              # optional: add free keys / alert settings
python -m crypto_toolkit price BTC ETH SOL
```

## What each link is, and what's in this folder

### FREE: clients are in `free_apis.py`

| Service | Cost | Key? | Base URL | Notes |
|---|---|---|---|---|
| **CoinGecko** | Free "Demo" plan, 10k calls/mo | Free key (works keyless at lower limits) | `https://api.coingecko.com/api/v3` | Header `x-cg-demo-api-key`. Get a key at coingecko.com/en/developers/dashboard. Up to 365 days of history. Attribution required. |
| **CoinMarketCap** | Free "Basic" plan | **Required** (free signup) | `https://pro-api.coinmarketcap.com` | Header `X-CMC_PRO_API_KEY`. Sign up at pro.coinmarketcap.com/signup. Latest data only: no history on free. |
| **Binance** | Free public data | No | `https://api.binance.us` | ⚠️ **binance.com blocks US locations** (tested: "restricted location"). Use Binance.US. |
| **Coinbase** | Free public data | No | `https://api.exchange.coinbase.com` | Tickers, order book, candles (300 per call). WebSocket: `wss://ws-feed.exchange.coinbase.com` |
| **Kraken** | Free public data | No | `https://api.kraken.com/0/public` | ~720 daily candles per call. Futures (funding, open interest): `https://futures.kraken.com/derivatives/api/v3/tickers` |
| **Fear & Greed** (alternative.me) | Free | No | `https://api.alternative.me/fng/?limit=30` | Daily 0–100 sentiment index |
| **CCXT** | Free, open source | n/a | `pip install ccxt` | One library for 100+ exchanges. Used here for live trading. |
| **TA-Lib / pandas-ta** | Free, open source | n/a | n/a | Not needed: `indicators.py` implements RSI, MACD, Bollinger, ATR, Stochastic, VWAP, OBV, SMA/EMA in plain pandas. |

### PAID (or no longer free): replacements I built

| Service | Why it's not usable for free | Replacement | What it does |
|---|---|---|---|
| **CryptoCompare** | Free tier retired May 2026; API now returns "API key required" (tested) | `aggregator.py` | Volume-weighted price across Coinbase + Kraken + Binance.US, merged OHLCV candles, multi-coin prices |
| **Glassnode** | No free API; API access needs paid plans | `onchain.py` | BTC network snapshot (fees, mempool, hashrate, difficulty), **Mayer Multiple, NVT, Puell Multiple, Hash Ribbons**, any blockchain.info chart |
| **CryptoQuant** | On-chain API is on paid tiers | `onchain.derivatives()` | Perp **funding rates, open interest, basis** from Kraken Futures |
| **Messari** | API is now enterprise/custom pricing | `research.py` | Asset profiles (supply, FDV, dilution, ATH drawdown, returns, GitHub activity), top-N screener, side-by-side compare |
| **TradingView** | Charts are free but there's no data/alert API | `charts.py` + `alerts.py` | Interactive candlestick HTML charts (SMA 50/200, Bollinger, RSI, MACD). Alerts on price, % move, RSI, SMA crosses, Fear & Greed, funding. Sent to phone (ntfy), Slack/Discord, or email |
| **CoinTracking / Koinly** | Paid for real tax reports | `portfolio.py` | Holdings with live P&L, FIFO/LIFO/HIFO lots, short- vs long-term gains, staking income, **Form 8949-style CSV** |
| **3Commas / Cryptohopper** | Subscription bots | `bot.py` | DCA bot (with buy-the-dip "safety orders"), grid bot, SMA-cross strategy. Backtests on 2 years of data, paper trading, guarded live mode via CCXT |

**Not replicable from free data:** MVRV, SOPR, realized cap, and exchange inflow/outflow need the full
Bitcoin UTXO set. To get those yourself, run a Bitcoin Core full node (~700 GB) and index it with an
open-source indexer. Otherwise those specific metrics need Glassnode/CryptoQuant.

## Commands

```bash
python -m crypto_toolkit price BTC ETH            # aggregated price + per-exchange spread
python -m crypto_toolkit market                   # top 25 by market cap
python -m crypto_toolkit feargreed                # last 14 days of sentiment
python -m crypto_toolkit ta BTC                   # RSI / MACD / SMA read
python -m crypto_toolkit chart BTC                # writes btc_1d.html, open in a browser
python -m crypto_toolkit onchain                  # network + valuation + derivatives dashboard
python -m crypto_toolkit research bitcoin         # Messari-style profile (CoinGecko ids)
python -m crypto_toolkit research bitcoin ethereum solana   # side-by-side
python -m crypto_toolkit screener --top 100

cp alerts.example.json alerts.json                # edit your rules
python -m crypto_toolkit alerts --once            # check now
python -m crypto_toolkit alerts --watch --every 60

python -m crypto_toolkit portfolio trades.csv --method FIFO --year 2026 --export-8949 8949.csv

python -m crypto_toolkit backtest dca  BTC --amount 100 --every 7 --dip 10
python -m crypto_toolkit backtest grid BTC --low 60000 --high 90000 --levels 20 --capital 5000
python -m crypto_toolkit backtest sma  BTC --fast 50 --slow 200
python -m crypto_toolkit bot dca BTC --amount 25 --every-hours 24          # paper mode
```

## Use it from Python

```python
from crypto_toolkit import CoinGecko, Kraken, fear_greed
from crypto_toolkit.aggregator import agg_price, agg_ohlcv
from crypto_toolkit import indicators as ta, onchain, research

df = Kraken().ohlc("XBTUSD", "1d")
df = ta.add_all(df)                       # adds sma_50, rsi_14, macd, bb_*, atr_14 ...
print(agg_price("ETH"))
print(onchain.valuation_metrics().tail())
print(research.screener(50).sort_values("mcap_to_fdv").head(10))
```

## Phone alerts in 2 minutes
1. Install the free **ntfy** app (iOS/Android) and subscribe to a long random topic, e.g. `john-crypto-8f3k2q`.
2. Put `NTFY_TOPIC=john-crypto-8f3k2q` in `.env`.
3. Run `python -m crypto_toolkit alerts --watch`. To keep it running 24/7, use a $5/mo VPS or a scheduled task running `alerts --once`.

## Portfolio CSV format
```
date,type,asset,quantity,price_usd,fee_usd,exchange,notes
2024-01-10,buy,BTC,0.10,46000,15,coinbase,
2025-02-15,sell,BTC,0.08,96000,20,coinbase,
2025-04-01,income,ETH,0.05,1800,0,kraken,staking reward
```
`type`: buy, sell, income (staking/airdrop/mining), gift_in, spend, transfer (wallet move, not taxable).
Export your history from each exchange and map the columns. This is a calculator, not tax advice;
have a CPA review before you file.

## Live trading (read first)
Live orders require **all three**: `LIVE_TRADING=yes` in `.env`, exchange API keys, and the `--live`
flag plus typing `YES`. Each order is capped by `MAX_ORDER_USD` (default $50). Create **trade-only**
keys with withdrawals disabled. Backtest, then paper-trade for weeks first. The included 2-year backtests
show DCA and SMA strategies **losing money** over the current window, which is a good reminder.

## Rate limits built in
`http.py` spaces calls per host (CoinGecko ~2s, CMC ~1.3s) and retries 429/5xx with backoff.
