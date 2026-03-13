"""
data/analyst.py -- Finnhub analyst intelligence endpoints.

Three endpoints used:
  - Recommendation trends  (/stock/recommendation)
  - Price targets          (/stock/price-target)
  - Upgrades/downgrades    (/stock/upgrade-downgrade)

All functions are @st.cache_data with a 1-hour TTL — analyst data changes slowly.
All functions return an empty dict/list on any failure so the UI degrades gracefully.
"""

import requests
import streamlit as st
from typing import Optional


def _token() -> Optional[str]:
    try:
        return st.secrets["finnhub"]["api_key"]
    except Exception:
        return None


def _get(endpoint: str, params: dict):
    token = _token()
    if not token:
        return None
    try:
        resp = requests.get(
            f"https://finnhub.io/api/v1{endpoint}",
            params={**params, "token": token},
            timeout=8,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_recommendations(ticker: str) -> list:
    """
    Returns analyst recommendation counts for the most recent period.
    Each entry: {period, strongBuy, buy, hold, sell, strongSell}
    Returns the single most recent period (index 0), or empty list.
    """
    data = _get("/stock/recommendation", {"symbol": ticker})
    if not isinstance(data, list) or not data:
        return []
    return data[:1]  # most recent period only


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_price_target(ticker: str) -> dict:
    """
    Returns analyst consensus price target.
    Keys: targetHigh, targetLow, targetMean, targetMedian, lastUpdated
    """
    data = _get("/stock/price-target", {"symbol": ticker})
    if not isinstance(data, dict):
        return {}
    return data


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_upgrades_downgrades(ticker: str) -> list:
    """
    Returns the 6 most recent analyst rating changes.
    Each entry: {company, fromGrade, toGrade, action, gradeTime}
    """
    data = _get("/stock/upgrade-downgrade", {"symbol": ticker})
    if not isinstance(data, list) or not data:
        return []
    return data[:6]
