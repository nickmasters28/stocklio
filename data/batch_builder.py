"""
Daily batch builder for ticker_snapshots.
Runs as a Render Cron Job (or locally) — no Streamlit dependency.

Usage:
  python data/batch_builder.py              # process all TOP_TICKERS
  python data/batch_builder.py AAPL MSFT   # process specific tickers

Required env vars:
  SUPABASE_URL
  SUPABASE_KEY
"""

import os
import sys
import time
import logging
import numpy as np
import pandas as pd
import yfinance as yf
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

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

RATE_DELAY = 0.5  # yfinance has no strict rate limit, but be polite

# ── Data fetching ─────────────────────────────────────────────────────────────

def fetch_ticker_data(ticker: str) -> tuple[pd.DataFrame | None, dict]:
    """Returns (ohlcv_df, info_dict) using yfinance."""
    try:
        t    = yf.Ticker(ticker)
        hist = t.history(period="2y")
        info = t.info or {}
        if hist.empty:
            return None, {}
        hist = hist.reset_index()
        df = pd.DataFrame({
            "open":   hist["Open"].values,
            "high":   hist["High"].values,
            "low":    hist["Low"].values,
            "close":  hist["Close"].values,
            "volume": hist["Volume"].values,
        })
        return df, info
    except Exception as e:
        log.warning("yfinance failed for %s: %s", ticker, e)
        return None, {}


# ── Indicator calculations ────────────────────────────────────────────────────

def calc_rsi(closes: np.ndarray, period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    deltas = np.diff(closes)
    gains  = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_g = gains[:period].mean()
    avg_l = losses[:period].mean()
    for i in range(period, len(deltas)):
        avg_g = (avg_g * (period - 1) + gains[i])  / period
        avg_l = (avg_l * (period - 1) + losses[i]) / period
    if avg_l == 0:
        return 100.0
    return round(100 - 100 / (1 + avg_g / avg_l), 2)


def calc_macd(closes: np.ndarray, fast=12, slow=26, signal=9) -> dict:
    s           = pd.Series(closes)
    macd_line   = s.ewm(span=fast, adjust=False).mean() - s.ewm(span=slow, adjust=False).mean()
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist        = macd_line - signal_line
    return {
        "macd":   round(float(macd_line.iloc[-1]),   4),
        "signal": round(float(signal_line.iloc[-1]), 4),
        "hist":   round(float(hist.iloc[-1]),         4),
    }


def calc_bb(closes: np.ndarray, period=20, std_dev=2) -> dict:
    if len(closes) < period:
        return {"upper": 0, "mid": 0, "lower": 0, "pct_b": 0.5}
    s     = pd.Series(closes)
    mid   = s.rolling(period).mean().iloc[-1]
    sigma = s.rolling(period).std().iloc[-1]
    upper = mid + std_dev * sigma
    lower = mid - std_dev * sigma
    pct_b = (closes[-1] - lower) / (upper - lower) if (upper - lower) > 0 else 0.5
    return {"upper": round(float(upper), 4), "mid": round(float(mid), 4),
            "lower": round(float(lower), 4), "pct_b": round(float(pct_b), 4)}


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
    if hist > 0: return "Bullish"
    if hist < 0: return "Bearish"
    return "Neutral"

def bb_label(pct_b: float) -> str:
    if pct_b >= 1.0: return "Above Upper"
    if pct_b >= 0.8: return "Near Upper"
    if pct_b <= 0.0: return "Below Lower"
    if pct_b <= 0.2: return "Near Lower"
    return "Mid-Band"


# ── Composite score ───────────────────────────────────────────────────────────

def composite_score(rsi: float, macd: dict, bb: dict, closes: np.ndarray) -> float:
    rsi_sig   = (rsi - 50) / 50
    hist_norm = np.tanh(macd["hist"] / max(abs(macd["hist"]) + 1e-9, 0.01))
    bb_sig    = (bb["pct_b"] - 0.5) * 2
    sma50     = calc_sma(closes, 50)
    sma200    = calc_sma(closes, 200)
    trend_sig = (1.0 if sma50 > sma200 else -1.0) if (sma50 and sma200) else 0.0
    score = 0.25 * rsi_sig + 0.35 * hist_norm + 0.20 * bb_sig + 0.20 * trend_sig
    return round(float(np.clip(score, -1.0, 1.0)), 4)

def score_label(score: float) -> str:
    if score >= 0.22:  return "Bullish"
    if score <= -0.22: return "Bearish"
    return "Neutral"


# ── Per-ticker pipeline ───────────────────────────────────────────────────────

def process_ticker(ticker: str, supabase: Client) -> bool:
    df, info = fetch_ticker_data(ticker)
    if df is None or len(df) < 30:
        log.warning("%-6s  insufficient data", ticker)
        return False

    closes = df["close"].to_numpy(dtype=float)
    rsi    = calc_rsi(closes)
    macd   = calc_macd(closes)
    bb     = calc_bb(closes)
    score  = composite_score(rsi, macd, bb, closes)

    price      = closes[-1]
    prev_close = closes[-2]
    change_amt = round(price - prev_close, 4)
    change_pct = round((change_amt / prev_close * 100) if prev_close else 0, 2)

    row = {
        "ticker":         ticker,
        "company_name":   info.get("longName") or info.get("shortName") or "",
        "sector":         info.get("sector") or "",
        "exchange":       info.get("exchange") or "",
        "market_cap":     float(info.get("marketCap") or 0) / 1e6,  # store in millions like Finnhub
        "price":          round(float(price), 4),
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

    supabase.from_("ticker_snapshots").upsert(row, on_conflict="ticker").execute()
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
        if success: ok += 1
        else:       fail += 1
        if i < len(tickers) - 1:
            time.sleep(RATE_DELAY)

    log.info("Done. ok=%d  fail=%d", ok, fail)


if __name__ == "__main__":
    main()
