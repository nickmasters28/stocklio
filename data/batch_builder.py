"""
Daily batch builder for ticker_snapshots.
Runs as a Render Cron Job (or locally) — no Streamlit dependency.

Usage:
  python data/batch_builder.py              # process all TOP_TICKERS
  python data/batch_builder.py AAPL MSFT   # process specific tickers

Required env vars:
  FINNHUB_API_KEY
  SUPABASE_URL
  SUPABASE_KEY
"""

import os
import sys
import time
import logging
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from supabase import create_client, Client

# Ensure the script's own directory is on the path so top_tickers.py is found
# regardless of the working directory Render uses.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from top_tickers import TOP_TICKERS

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("batch_builder")

# ── Config ───────────────────────────────────────────────────────────────────

FINNHUB_KEY  = os.environ["FINNHUB_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

FINNHUB_BASE = "https://finnhub.io/api/v1"
RATE_DELAY   = 3.5   # seconds between tickers (3 calls/ticker × 3.5s = ~51 calls/min, under 60 limit)
CANDLE_BARS  = 250   # trading days of history for indicators
TIMEOUT      = 10    # requests timeout

# ── Finnhub helpers ───────────────────────────────────────────────────────────

def _get(path: str, params: dict) -> dict | None:
    params["token"] = FINNHUB_KEY
    try:
        r = requests.get(f"{FINNHUB_BASE}{path}", params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.warning("Finnhub %s failed: %s", path, e)
        return None


def fetch_candles(ticker: str) -> pd.DataFrame | None:
    """Return a DataFrame with OHLCV columns, or None on failure."""
    now   = int(datetime.now(timezone.utc).timestamp())
    start = now - CANDLE_BARS * 2 * 86400  # 2x to account for weekends/holidays
    data  = _get("/stock/candle", {"symbol": ticker, "resolution": "D",
                                   "from": start, "to": now})
    if not data or data.get("s") != "ok":
        return None
    df = pd.DataFrame({
        "open":   data["o"],
        "high":   data["h"],
        "low":    data["l"],
        "close":  data["c"],
        "volume": data["v"],
        "ts":     data["t"],
    })
    df.sort_values("ts", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def fetch_quote(ticker: str) -> dict | None:
    return _get("/quote", {"symbol": ticker})


def fetch_profile(ticker: str) -> dict | None:
    return _get("/stock/profile2", {"symbol": ticker})


# ── Indicator calculations ────────────────────────────────────────────────────

def calc_rsi(closes: np.ndarray, period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    deltas = np.diff(closes)
    gains  = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    # Wilder smoothing
    avg_g = gains[:period].mean()
    avg_l = losses[:period].mean()
    for i in range(period, len(deltas)):
        avg_g = (avg_g * (period - 1) + gains[i])  / period
        avg_l = (avg_l * (period - 1) + losses[i]) / period
    if avg_l == 0:
        return 100.0
    rs = avg_g / avg_l
    return round(100 - 100 / (1 + rs), 2)


def calc_macd(closes: np.ndarray, fast=12, slow=26, signal=9) -> dict:
    """Returns {'macd': float, 'signal': float, 'hist': float}."""
    s = pd.Series(closes)
    ema_fast   = s.ewm(span=fast,   adjust=False).mean()
    ema_slow   = s.ewm(span=slow,   adjust=False).mean()
    macd_line  = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist        = macd_line - signal_line
    return {
        "macd":   round(float(macd_line.iloc[-1]),   4),
        "signal": round(float(signal_line.iloc[-1]), 4),
        "hist":   round(float(hist.iloc[-1]),         4),
    }


def calc_bb(closes: np.ndarray, period=20, std_dev=2) -> dict:
    """Returns {'upper', 'mid', 'lower', 'pct_b'} for latest bar."""
    if len(closes) < period:
        return {"upper": 0, "mid": 0, "lower": 0, "pct_b": 0.5}
    s     = pd.Series(closes)
    mid   = s.rolling(period).mean().iloc[-1]
    sigma = s.rolling(period).std().iloc[-1]
    upper = mid + std_dev * sigma
    lower = mid - std_dev * sigma
    price = closes[-1]
    pct_b = (price - lower) / (upper - lower) if (upper - lower) > 0 else 0.5
    return {
        "upper":  round(float(upper), 4),
        "mid":    round(float(mid),   4),
        "lower":  round(float(lower), 4),
        "pct_b":  round(float(pct_b), 4),
    }


def calc_sma(closes: np.ndarray, period: int) -> float | None:
    if len(closes) < period:
        return None
    return float(np.mean(closes[-period:]))


# ── Label helpers ─────────────────────────────────────────────────────────────

def rsi_label(rsi: float) -> str:
    if rsi >= 70: return "Overbought"
    if rsi <= 30: return "Oversold"
    return "Neutral"


def macd_label(hist: float) -> str:
    if hist > 0:  return "Bullish"
    if hist < 0:  return "Bearish"
    return "Neutral"


def bb_label(pct_b: float) -> str:
    if pct_b >= 1.0: return "Above Upper"
    if pct_b >= 0.8: return "Near Upper"
    if pct_b <= 0.0: return "Below Lower"
    if pct_b <= 0.2: return "Near Lower"
    return "Mid-Band"


# ── Composite score (simplified, no Streamlit dependency) ─────────────────────

def composite_score(rsi: float, macd: dict, bb: dict, closes: np.ndarray) -> float:
    """
    Returns a score in [-1, +1].
    Weights: RSI 25% | MACD 35% | BB 20% | Trend (SMA50 vs SMA200) 20%
    """
    # RSI signal: [-1, +1] linearly mapped from [0, 100], centered at 50
    rsi_sig = (rsi - 50) / 50  # -1 at RSI=0, +1 at RSI=100

    # MACD histogram normalised: tanh to keep in bounds
    hist_norm = np.tanh(macd["hist"] / max(abs(macd["hist"]) + 1e-9, 0.01))

    # BB %B signal: 0=oversold(-1), 0.5=neutral(0), 1=overbought(+1)
    bb_sig = (bb["pct_b"] - 0.5) * 2

    # Trend: SMA50 vs SMA200
    sma50  = calc_sma(closes, 50)
    sma200 = calc_sma(closes, 200)
    if sma50 is not None and sma200 is not None:
        trend_sig = 1.0 if sma50 > sma200 else -1.0
    else:
        trend_sig = 0.0

    score = (0.25 * rsi_sig +
             0.35 * hist_norm +
             0.20 * bb_sig +
             0.20 * trend_sig)
    return round(float(np.clip(score, -1.0, 1.0)), 4)


def score_label(score: float) -> str:
    if score >= 0.22:  return "Bullish"
    if score <= -0.22: return "Bearish"
    return "Neutral"


# ── Per-ticker pipeline ───────────────────────────────────────────────────────

def process_ticker(ticker: str, supabase: Client) -> bool:
    df = fetch_candles(ticker)
    if df is None or len(df) < 30:
        log.warning("%-6s  insufficient candle data", ticker)
        return False

    closes = df["close"].to_numpy(dtype=float)
    rsi    = calc_rsi(closes)
    macd   = calc_macd(closes)
    bb     = calc_bb(closes)
    score  = composite_score(rsi, macd, bb, closes)

    quote   = fetch_quote(ticker)   or {}
    profile = fetch_profile(ticker) or {}

    price      = float(quote.get("c") or closes[-1])
    prev_close = float(quote.get("pc") or closes[-2])
    change_amt = round(price - prev_close, 4)
    change_pct = round((change_amt / prev_close * 100) if prev_close else 0, 2)

    row = {
        "ticker":         ticker,
        "company_name":   profile.get("name", ""),
        "sector":         profile.get("finnhubIndustry", ""),
        "exchange":       profile.get("exchange", ""),
        "market_cap":     float(profile.get("marketCapitalization", 0) or 0),
        "price":          price,
        "change_pct":     change_pct,
        "change_amt":     change_amt,
        "ai_score_label": score_label(score),
        "ai_score_value": score,
        "rsi_value":      rsi,
        "rsi_label":      rsi_label(rsi),
        "macd_label":     macd_label(macd["hist"]),
        "bb_label":       bb_label(bb["pct_b"]),
        "on_demand":      False,
        "updated_at":     datetime.now(timezone.utc).isoformat(),
    }

    supabase.table("ticker_snapshots").upsert(row, on_conflict="ticker").execute()
    log.info("%-6s  price=%-8.2f  RSI=%-5.1f  score=%-6.3f  %s",
             ticker, price, rsi, score, row["ai_score_label"])
    return True


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    tickers = sys.argv[1:] if len(sys.argv) > 1 else TOP_TICKERS
    log.info("Batch builder starting — %d tickers", len(tickers))

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    ok = fail = 0
    for i, ticker in enumerate(tickers):
        success = process_ticker(ticker, supabase)
        if success:
            ok += 1
        else:
            fail += 1
        # Rate-limit: sleep after every ticker except the last
        if i < len(tickers) - 1:
            time.sleep(RATE_DELAY)

    log.info("Done. ok=%d  fail=%d", ok, fail)


if __name__ == "__main__":
    main()
