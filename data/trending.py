"""
data/trending.py -- Alpha Vantage most-actively-traded tickers.

Fetched server-side in Python and cached for 5 minutes so the AV free-tier
limit (25 calls/day) is never exceeded in normal use.
"""

import json
import urllib.request

import streamlit as st

# Number of tickers to show in the bar. Adjust here.
MAX_TICKERS = 15


@st.cache_data(ttl=3600)  # 1-hour cache — keeps daily calls well within AV free tier (25/day)
def get_trending_tickers() -> list[dict]:
    """
    Returns a list of dicts with keys: ticker, price, change_pct.
    Returns an empty list on any error so the bar degrades gracefully.
    """
    try:
        api_key = st.secrets["alphavantage"]["api_key"]
    except KeyError:
        return []

    url = (
        "https://www.alphavantage.co/query"
        f"?function=TOP_GAINERS_LOSERS&apikey={api_key}"
    )

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "stocklio/1.0"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception:
        return []

    # AV returns a plain-text "Note" or "Information" key when rate-limited
    if "Note" in data or "Information" in data:
        return []

    raw = data.get("most_actively_traded", [])[:MAX_TICKERS]

    tickers = []
    for item in raw:
        pct_str = str(item.get("change_percentage", "0")).replace("%", "")
        try:
            pct = round(float(pct_str), 2)
        except ValueError:
            pct = 0.0

        try:
            price = f"{float(item.get('price', 0)):.2f}"
        except ValueError:
            price = "—"

        tickers.append({
            "ticker": item.get("ticker", ""),
            "price":  price,
            "change_pct": pct,
        })

    return tickers
