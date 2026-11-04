"""TradingView replacement, part 2: price & indicator alerts with push/email/webhook delivery.

Rules live in alerts.json (see alerts.example.json). Run:
    python -m crypto_toolkit alerts --watch          # checks every 60s
    python -m crypto_toolkit alerts --once           # single check (good for cron)

Rule types:
  price_above / price_below           {"value": 80000}
  change_24h_above / change_24h_below {"value": 5}       (percent)
  rsi_above / rsi_below               {"value": 70, "interval": "1h", "period": 14}
  cross_above_sma / cross_below_sma   {"period": 200, "interval": "1d"}
  fear_greed_below / fear_greed_above {"value": 20}
  funding_apr_above                   {"value": 30, "symbol": "PF_XBTUSD"}

Notifiers (set in .env): console always; NTFY_TOPIC (free phone push via ntfy.sh app);
WEBHOOK_URL (Slack/Discord/Teams incoming webhook); SMTP_* for email.
"""
from __future__ import annotations

import json
import os
import smtplib
import time
from email.message import EmailMessage

from . import indicators as ta
from .free_apis import Coinbase, Kraken, fear_greed
from .http import SESSION, env

STATE_FILE = ".alert_state.json"


# ----------------------------------------------------------------------------- data
def _product(symbol: str) -> str:
    return symbol if "-" in symbol else f"{symbol.upper()}-USD"


def _candles(symbol: str, interval: str):
    return Coinbase().candles(_product(symbol), interval)


def evaluate(rule: dict) -> tuple[bool, str]:
    """Return (triggered, message) for one rule."""
    t, sym = rule["type"], rule.get("symbol", "BTC")
    v = rule.get("value")

    if t in ("price_above", "price_below", "change_24h_above", "change_24h_below"):
        tk = Coinbase().ticker(_product(sym))
        px = float(tk["price"])
        if t == "price_above":
            return px > v, f"{sym} price {px:,.2f} (trigger: above {v:,})"
        if t == "price_below":
            return px < v, f"{sym} price {px:,.2f} (trigger: below {v:,})"
        df = _candles(sym, "1h")
        ref = float(df["close"].iloc[-25]) if len(df) > 25 else float(df["close"].iloc[0])
        ch = (px / ref - 1) * 100
        if t == "change_24h_above":
            return ch > v, f"{sym} 24h change {ch:+.2f}% (trigger: above {v}%)"
        return ch < v, f"{sym} 24h change {ch:+.2f}% (trigger: below {v}%)"

    if t in ("rsi_above", "rsi_below"):
        df = _candles(sym, rule.get("interval", "1h"))
        r = float(ta.rsi(df["close"], rule.get("period", 14)).iloc[-1])
        hit = r > v if t == "rsi_above" else r < v
        return hit, f"{sym} RSI({rule.get('period', 14)}, {rule.get('interval', '1h')}) = {r:.1f} (trigger: {'above' if t == 'rsi_above' else 'below'} {v})"

    if t in ("cross_above_sma", "cross_below_sma"):
        df = _candles(sym, rule.get("interval", "1d"))
        n = rule.get("period", 200)
        s = ta.sma(df["close"], n)
        prev_above = df["close"].iloc[-2] > s.iloc[-2]
        now_above = df["close"].iloc[-1] > s.iloc[-1]
        hit = (not prev_above and now_above) if t == "cross_above_sma" else (prev_above and not now_above)
        direction = "above" if t == "cross_above_sma" else "below"
        return hit, f"{sym} close {df['close'].iloc[-1]:,.2f} vs SMA{n} {s.iloc[-1]:,.2f} (trigger: fresh cross {direction})"

    if t in ("fear_greed_below", "fear_greed_above"):
        fg = fear_greed(1).iloc[-1]
        hit = fg["value"] < v if t == "fear_greed_below" else fg["value"] > v
        return hit, f"Fear & Greed = {fg['value']} ({fg['value_classification']}) (trigger: {'below' if t == 'fear_greed_below' else 'above'} {v})"

    if t == "funding_apr_above":
        ft = Kraken().futures_tickers()
        row = ft[ft["symbol"] == rule.get("symbol", "PF_XBTUSD")].iloc[0]
        apr = row["relativeFundingRate"] * 24 * 365 * 100
        return apr > v, f"{row['symbol']} funding {apr:.1f}% APR (trigger: above {v}%)"

    raise ValueError(f"Unknown rule type: {t}")


# ------------------------------------------------------------------------- notifiers
def notify(title: str, body: str) -> None:
    print(f"[ALERT] {title}: {body}")
    topic = env("NTFY_TOPIC")
    if topic:
        try:
            SESSION.post(f"https://ntfy.sh/{topic}", data=body.encode(),
                         headers={"Title": title}, timeout=10)
        except Exception as e:
            print("  ntfy failed:", e)
    hook = env("WEBHOOK_URL")
    if hook:
        try:
            SESSION.post(hook, json={"text": f"*{title}*\n{body}", "content": f"**{title}**\n{body}"},
                         timeout=10)
        except Exception as e:
            print("  webhook failed:", e)
    host = env("SMTP_HOST")
    if host and env("ALERT_EMAIL_TO"):
        try:
            msg = EmailMessage()
            msg["Subject"], msg["From"], msg["To"] = title, env("SMTP_USER"), env("ALERT_EMAIL_TO")
            msg.set_content(body)
            with smtplib.SMTP(host, int(env("SMTP_PORT", "587"))) as s:
                s.starttls()
                s.login(env("SMTP_USER"), env("SMTP_PASS"))
                s.send_message(msg)
        except Exception as e:
            print("  email failed:", e)


# ----------------------------------------------------------------------------- loop
def _load(path):
    with open(path) as f:
        return json.load(f)


def _state():
    return json.load(open(STATE_FILE)) if os.path.exists(STATE_FILE) else {}


def check_all(rules_path: str = "alerts.json") -> list[str]:
    rules = _load(rules_path)["alerts"]
    state, fired, now = _state(), [], time.time()
    for i, rule in enumerate(rules):
        key = rule.get("name") or f"rule{i}"
        cooldown = rule.get("cooldown_minutes", 60) * 60
        try:
            hit, msg = evaluate(rule)
        except Exception as e:
            print(f"  {key}: error {e}")
            continue
        if hit and now - state.get(key, 0) >= cooldown:
            notify(f"Crypto alert: {key}", msg)
            state[key] = now
            fired.append(msg)
        elif not hit:
            print(f"  {key}: not triggered — {msg}")
    json.dump(state, open(STATE_FILE, "w"))
    return fired


def watch(rules_path: str = "alerts.json", every: int = 60) -> None:
    print(f"Watching {rules_path} every {every}s — Ctrl+C to stop")
    while True:
        check_all(rules_path)
        time.sleep(every)
