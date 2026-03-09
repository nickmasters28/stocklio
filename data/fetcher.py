"""
data/fetcher.py -- Handles all market data retrieval via yfinance.

All functions return clean DataFrames with standardised column names.
Errors are surfaced as exceptions and handled gracefully at the UI layer.
"""

import yfinance as yf
import pandas as pd
import streamlit as st
from typing import Optional

# Cache data for 5 minutes to avoid hammering the API on re-renders
@st.cache_data(ttl=300)
def fetch_ohlcv(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch OHLCV data for a given ticker.

    Args:
        ticker:   Stock symbol, e.g. "AAPL" or "^GSPC".
        period:   yfinance period string -- "1mo", "3mo", "6mo", "1y", "2y".
        interval: Bar interval -- "1d" (daily), "1wk", "1mo".

    Returns:
        DataFrame with columns: Open, High, Low, Close, Volume.
        Index is a DatetimeIndex (timezone-naive, UTC).

    Raises:
        ValueError: if the ticker returns empty data (likely invalid symbol).
    """
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

    # Flatten MultiIndex columns produced by yfinance >= 0.2.x
    if isinstance(raw.columns, pd.MultiIndex):
        raw.columns = raw.columns.get_level_values(0)

    df = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
    df.index = pd.to_datetime(df.index).tz_localize(None)  # make tz-naive
    df.dropna(subset=["Close"], inplace=True)
    return df


@st.cache_data(ttl=300)
def fetch_info(ticker: str) -> dict:
    """
    Fetch company/index metadata (name, sector, market cap, etc.).

    Returns:
        dict of yfinance .info fields; empty dict on failure.
        Falls back to history_metadata for ETFs/funds when .info is missing name fields.
    """
    t = yf.Ticker(ticker)
    try:
        info = t.info or {}
    except Exception:
        info = {}

    # .info can return an empty-ish dict for ETFs/funds (rate-limited or unsupported).
    # history_metadata is a lighter endpoint that reliably carries longName/shortName.
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

