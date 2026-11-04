"""Technical indicators in plain pandas (no TA-Lib / pandas-ta install needed).

All functions take a DataFrame with open/high/low/close/volume columns (or a Series)
and return a Series or DataFrame aligned to the input index.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def sma(s: pd.Series, n: int = 20) -> pd.Series:
    return s.rolling(n).mean()


def ema(s: pd.Series, n: int = 20) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    """Wilder's RSI, matches TradingView/TA-Lib."""
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(100.0).where(up.notna())


def macd(s: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    line = ema(s, fast) - ema(s, slow)
    sig = ema(line, signal)
    return pd.DataFrame({"macd": line, "signal": sig, "hist": line - sig})


def bollinger(s: pd.Series, n: int = 20, k: float = 2.0) -> pd.DataFrame:
    mid = sma(s, n)
    sd = s.rolling(n).std(ddof=0)
    return pd.DataFrame({"bb_mid": mid, "bb_upper": mid + k * sd, "bb_lower": mid - k * sd,
                         "bb_pctb": (s - (mid - k * sd)) / (2 * k * sd)})


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    pc = df["close"].shift()
    tr = pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()],
                   axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()


def stochastic(df: pd.DataFrame, n: int = 14, d: int = 3) -> pd.DataFrame:
    lo, hi = df["low"].rolling(n).min(), df["high"].rolling(n).max()
    k = 100 * (df["close"] - lo) / (hi - lo)
    return pd.DataFrame({"stoch_k": k, "stoch_d": k.rolling(d).mean()})


def vwap(df: pd.DataFrame) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3
    return (tp * df["volume"]).cumsum() / df["volume"].cumsum()


def obv(df: pd.DataFrame) -> pd.Series:
    return (np.sign(df["close"].diff()).fillna(0) * df["volume"]).cumsum()


def add_all(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of df with the common indicator set attached."""
    out = df.copy()
    c = out["close"]
    out["sma_20"], out["sma_50"], out["sma_200"] = sma(c, 20), sma(c, 50), sma(c, 200)
    out["ema_12"], out["ema_26"] = ema(c, 12), ema(c, 26)
    out["rsi_14"] = rsi(c)
    out = out.join(macd(c)).join(bollinger(c)).join(stochastic(out))
    out["atr_14"] = atr(out)
    if out["volume"].notna().any():
        out["obv"] = obv(out)
    return out


def signal_summary(df: pd.DataFrame) -> dict:
    """Plain-English read of the latest bar. Descriptive only — not a trade signal."""
    x = add_all(df).iloc[-1]
    notes = []
    if pd.notna(x["rsi_14"]):
        notes.append("RSI overbought (>70)" if x["rsi_14"] > 70 else
                     "RSI oversold (<30)" if x["rsi_14"] < 30 else f"RSI neutral ({x['rsi_14']:.0f})")
    if pd.notna(x["sma_200"]):
        notes.append("price above 200-day SMA" if x["close"] > x["sma_200"] else "price below 200-day SMA")
    if pd.notna(x["sma_50"]) and pd.notna(x["sma_200"]):
        notes.append("50 > 200 SMA (golden-cross regime)" if x["sma_50"] > x["sma_200"]
                     else "50 < 200 SMA (death-cross regime)")
    notes.append("MACD above signal" if x["macd"] > x["signal"] else "MACD below signal")
    return {"close": float(x["close"]), "rsi_14": float(x["rsi_14"]),
            "macd_hist": float(x["hist"]), "atr_14": float(x["atr_14"]), "notes": notes}
