"""
data/fetcher.py -- Handles all market data retrieval.

Primary source:  Finnhub REST API  (~200-500ms per call, direct REST API)
Fallback source: yfinance          (~1-3s per call, unofficial scraper)

Both public functions maintain the same signatures and return types so the
rest of the codebase is unaffected by which source is actually used.

Secrets required in .streamlit/secrets.toml:
    [finnhub]
    api_key = "YOUR_FINNHUB_API_KEY"

If the [finnhub] key is absent, both functions fall back to yfinance silently.
"""

import time as _time

import requests
import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Optional


# Period string → approximate calendar days (used to compute Finnhub from/to timestamps)
_PERIOD_DAYS: dict[str, int] = {
    "1mo":  30,
    "3mo":  90,
    "6mo":  180,
    "1y":   365,
    "2y":   730,
}


def _finnhub_token() -> Optional[str]:
    """Return the Finnhub API key from secrets, or None if not configured."""
    try:
        return st.secrets["finnhub"]["api_key"]
    except Exception:
        return None


# ── OHLCV ─────────────────────────────────────────────────────────────────────

def _fetch_ohlcv_finnhub(ticker: str, period: str) -> pd.DataFrame:
    """Fetch OHLCV daily bars from Finnhub /stock/candle."""
    token = _finnhub_token()
    if not token:
        raise RuntimeError("Finnhub API key not configured")

    days    = _PERIOD_DAYS.get(period, 365)
    to_ts   = int(_time.time())
    from_ts = to_ts - days * 86400

    resp = requests.get(
        "https://finnhub.io/api/v1/stock/candle",
        params={
            "symbol":     ticker,
            "resolution": "D",
            "from":       from_ts,
            "to":         to_ts,
            "token":      token,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    if data.get("s") != "ok" or not data.get("t"):
        raise ValueError(
            f"No data returned for ticker '{ticker}'. Check the symbol and try again."
        )

    df = pd.DataFrame(
        {
            "Open":   data["o"],
            "High":   data["h"],
            "Low":    data["l"],
            "Close":  data["c"],
            "Volume": data["v"],
        },
        index=pd.to_datetime(data["t"], unit="s"),
    )
    df.index.name = None
    df.index = df.index.tz_localize(None)
    df.dropna(subset=["Close"], inplace=True)
    return df


def _fetch_ohlcv_yfinance(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """Fetch OHLCV data from yfinance (fallback)."""
    raw = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    if raw.empty:
        raise ValueError(
            f"No data returned for ticker '{ticker}'. Check the symbol and try again."
        )
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)
    df = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.dropna(subset=["Close"], inplace=True)
    return df


# Cache data for 30 minutes — daily bars are stable intraday for this analysis app
@st.cache_data(ttl=1800)
def fetch_ohlcv(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch OHLCV data for a given ticker.

    Tries Finnhub first (~200-500ms); falls back to yfinance on any non-ticker
    error (rate limit, network issue, key not configured).

    Args:
        ticker:   Stock symbol, e.g. "AAPL" or "^GSPC".
        period:   Period string -- "1mo", "3mo", "6mo", "1y", "2y".
        interval: Bar interval (yfinance fallback only) -- "1d", "1wk", "1mo".

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume.
        Index is a DatetimeIndex (timezone-naive).

    Raises:
        ValueError: if the ticker is invalid / returns no data from either source.
    """
    try:
        return _fetch_ohlcv_finnhub(ticker, period)
    except ValueError:
        raise  # invalid ticker — propagate immediately, no point trying yfinance
    except Exception:
        return _fetch_ohlcv_yfinance(ticker, period, interval)


# ── Company metadata ──────────────────────────────────────────────────────────

def _fetch_info_finnhub(ticker: str) -> dict:
    """Fetch company metadata from Finnhub /stock/profile2."""
    token = _finnhub_token()
    if not token:
        raise RuntimeError("Finnhub API key not configured")

    resp = requests.get(
        "https://finnhub.io/api/v1/stock/profile2",
        params={"symbol": ticker, "token": token},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()

    if not data or not data.get("name"):
        raise ValueError("Empty profile from Finnhub")

    # Normalise to the field names that ui/layout.py expects
    info: dict = {}
    if data.get("name"):
        info["longName"] = data["name"]
    if data.get("finnhubIndustry"):
        info["sector"] = data["finnhubIndustry"]
    if data.get("marketCapitalization"):
        # Finnhub returns market cap in millions USD; convert to absolute dollars
        info["marketCap"] = float(data["marketCapitalization"]) * 1_000_000
    if data.get("weburl"):
        info["website"] = data["weburl"]
    return info


def _fetch_info_yfinance(ticker: str) -> dict:
    """Fetch company metadata from yfinance (fallback)."""
    t = yf.Ticker(ticker)
    try:
        info = t.info or {}
    except Exception:
        info = {}
    # history_metadata is a lighter endpoint that reliably carries longName/shortName
    # for ETFs/funds when .info is empty or rate-limited.
    if not info.get("longName") and not info.get("shortName"):
        try:
            meta = t.history_metadata or {}
            if meta.get("longName"):
                info["longName"] = meta["longName"]
            elif meta.get("shortName"):
                info["shortName"] = meta["shortName"]
        except Exception:
            pass
    return info


@st.cache_data(ttl=3600)  # company metadata rarely changes — 1-hour TTL is safe
def fetch_info(ticker: str) -> dict:
    """
    Fetch company/index metadata (name, sector, market cap, website, etc.).

    Tries Finnhub first (~100-300ms); falls back to yfinance on any error.

    Returns:
        dict with keys: longName, sector, marketCap, website (where available).
        Empty dict on total failure.
    """
    try:
        return _fetch_info_finnhub(ticker)
    except Exception:
        return _fetch_info_yfinance(ticker)
