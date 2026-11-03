# Mintline — Crypto Tracker

Live crypto prices, price alerts and portfolio tracking. It's an installable web app (PWA) with no build step and no dependencies.

## Features

- **Markets**: the top 100 coins by market cap, with price, 1h/24h/7d change, market cap and a 7-day sparkline. Search, sort, and global market stats. Prices refresh every 60 s and flash when they change.
- **Coin detail**: an interactive price chart (24H / 7D / 30D / 90D / 1Y) with a hover crosshair, plus market cap, volume, 24h range, supply and all-time high.
- **Watchlist**: star any coin to pin it.
- **Portfolio**: record buy and sell transactions. Shows total value, 24h change, profit/loss (realized and unrealized, average-cost method), cost basis and an allocation donut. Data can be exported and imported as JSON.
- **Price alerts**: "above" or "below" a target price. When an alert fires you get an in-app toast and, if you allow it, a system notification. Alerts can be re-armed.
- **Currencies**: USD, EUR, GBP, CAD, AUD, JPY and BTC. Transactions and alerts keep the currency they were entered in and are converted using CoinGecko exchange rates.
- **Offline**: a service worker caches the app shell and the last API responses. If CoinGecko can't be reached, the app shows cached prices. With no cache, it shows clearly labelled demo prices, and alerts never fire on demo data.

All user data (watchlist, transactions, alerts) is kept in `localStorage` in your browser.

## Run locally

Any static file server works, for example:

```bash
cd mintline && python3 -m http.server 8080
```

Open http://localhost:8080 and choose **Install** in Chrome's address bar to get the desktop or app shortcut.

## Data

Prices come from the free public [CoinGecko API](https://www.coingecko.com/en/api). It has rate limits, so the app polls once a minute.
