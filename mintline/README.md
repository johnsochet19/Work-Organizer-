# Mintline: Crypto Tracker

Live crypto prices, alerts, portfolio and tax tracking, research, Bitcoin on-chain data and strategy backtests. Mintline runs in the browser, as a desktop shortcut, or as a Chrome extension. It has no build step and no dependencies.

It's the browser version of the Python toolkit in [`../crypto_toolkit`](../crypto_toolkit). The calculations are ported line for line and tested against the Python code, so both tools give the same numbers for the same data.

## What's in it

| Tab | What it does | Python equivalent |
|---|---|---|
| **Markets** | Top 100 coins with prices, 1h/24h/7d change and sparklines. **Screener** view adds market cap ÷ FDV, volume ÷ market cap, % of supply issued, distance from all-time high and 30-day returns, all sortable. **Compare** shows up to 4 coins side by side. | `market`, `screener`, `research a b c` |
| **Coin detail** | Chart from 24H to 1Y with SMA 50/200, Bollinger bands, RSI and MACD. A plain-English daily read (overbought/oversold, above/below the 200-day average, golden/death cross, MACD). Prices on Coinbase, Kraken and Binance.US with the volume-weighted price and spread. Research: FDV, dilution, supply, returns, GitHub activity. | `chart`, `ta`, `price`, `research` |
| **Watchlist** | Starred coins. | |
| **Portfolio** | Buys, sells, income (staking or airdrops), gifts, spending and wallet transfers, with fees. Cost basis by **FIFO, LIFO or HIFO**. Unrealized and realized profit and loss. **Taxes**: short- and long-term gains by year, income, and a **Form 8949 CSV** download. Import and export use the toolkit's `trades.csv` format. | `portfolio trades.csv --method FIFO --year 2026 --export-8949` |
| **Alerts** | All toolkit rule types: price above/below, 24h change, RSI, moving-average crosses, Fear & Greed, futures funding. Each has a cooldown. **Import/export `alerts.json`** in the same format as the toolkit. Alerts arrive in the app, as system notifications, on your phone through **ntfy**, or in **Slack/Discord**. | `alerts --watch` |
| **Mentor** | Six questions about you, then a weekly plan: how much to buy (0× to 1.5× your usual amount), split by coin, with the five market signals explained. Includes a backtest of these rules against plain weekly buying. | `advise`, `advise --backtest` |
| **Bitcoin data** | Network (fees, mempool, hash rate, difficulty). Valuation: Mayer Multiple, NVT, Puell Multiple, hash ribbons. Kraken perpetuals: funding, basis, open interest. Fear & Greed history. | `onchain` |
| **Backtest** | DCA with dip buys, spot grid, and SMA cross, on Kraken daily candles (or CoinGecko closes as a fallback). Shows an equity curve and the list of trades. Plus a **paper DCA bot** that buys with a pretend balance while the app is open. | `backtest dca/grid/sma`, `bot dca` |

**Kept in the Python toolkit only:**
- **Live trading**, which needs exchange API keys. Those shouldn't live in a browser.
- **Email alerts**, which need a mail server.
- The **CoinMarketCap** client, which needs a key and only duplicates CoinGecko data.

Settings (the ⚙ button) take an optional free CoinGecko demo key, an ntfy topic and a webhook URL. Everything is stored only in your browser's `localStorage`.

## Run it

- **Quick look:** open `index.html` in a browser.
- **Windows:** in the downloaded `Mintline.zip`, double-click **Open Mintline.bat**. It opens Mintline in its own Chrome window.
- **Chrome extension:** extract `Mintline-extension.zip`, go to `chrome://extensions`, turn on Developer mode and click **Load unpacked**. The extension can reach every data source. A plain web page may be blocked by some exchanges.
- **Installable app:** serve the folder (`python3 -m http.server 8080`) and use Chrome's **Install** button.

Build both ZIPs with:

```bash
./packaging/build.sh
```

The ZIPs are written to `dist/`.

## Data sources

All of these are free and need no account:
- CoinGecko: prices, history, research. Polled once a minute, and requests are spaced about 2 seconds apart, as in the toolkit.
- alternative.me: Fear & Greed.
- Kraken and Kraken Futures: candles, funding.
- Coinbase and Binance.US: exchange prices.
- mempool.space and blockchain.info: on-chain data.

If live data can't be reached, Mintline shows saved prices first, then clearly labelled sample prices. Alerts and the paper bot never act on sample data.

## Files

| File | Contents |
|---|---|
| `indicators.js` | SMA, EMA, RSI, MACD, Bollinger, resampling (port of `indicators.py`) |
| `engine.js` | Tax lots, backtests and the advisor (ports of `portfolio.py`, `bot.py`, `advisor.py`) |
| `app.js` | Data loading, markets, coin detail, portfolio, alerts, settings |
| `tools.js` | Mentor, Bitcoin data, Backtest and paper bot tabs |
| `packaging/` | Chrome extension manifest, Windows launcher, build script |

Not financial advice. The mentor is a rules-based plan and can't predict prices. The tax figures come from a calculator, so have a CPA review them before you file.
