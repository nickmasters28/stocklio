"""
data/congress.py -- Congressional trading data for Stocklio Pro.

Sources (free, no API key required):
  - House Stock Watcher: https://housestockwatcher.com
  - Senate Stock Watcher: https://senatestockwatcher.com

Both datasets are public disclosures filed under the STOCK Act.
Data is cached for 6 hours since disclosures only update a few times per day.
"""

import requests
import streamlit as st
from datetime import datetime


_HOUSE_URL  = "https://house-stock-watcher-data.s3-us-west-2.amazonaws.com/data/all_transactions.json"
_SENATE_URL = "https://senate-stock-watcher-data.s3-us-west-2.amazonaws.com/aggregate/all_transactions.json"


@st.cache_data(ttl=21600, show_spinner=False)
def _fetch_house_all() -> list:
    try:
        r = requests.get(_HOUSE_URL, timeout=12)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


@st.cache_data(ttl=21600, show_spinner=False)
def _fetch_senate_all() -> list:
    try:
        r = requests.get(_SENATE_URL, timeout=12)
        r.raise_for_status()
        return r.json()
    except Exception:
        return []


@st.cache_data(ttl=21600, show_spinner=False)
def fetch_congress_trades(ticker: str, limit: int = 10) -> list:
    """
    Returns the most recent congressional trades for a given ticker.

    Each result dict has:
      chamber      - "House" or "Senate"
      name         - representative / senator name
      trade_type   - "Purchase" or "Sale"
      amount       - disclosure amount range string
      date         - transaction date string (YYYY-MM-DD)
      asset        - asset description
    """
    ticker_upper = ticker.upper()
    trades = []

    # House
    for row in _fetch_house_all():
        t = (row.get("ticker") or "").upper().strip()
        if t != ticker_upper:
            continue
        date_str = row.get("transaction_date") or row.get("disclosure_date") or ""
        trades.append({
            "chamber":    "House",
            "name":       row.get("representative", "—"),
            "trade_type": row.get("type", "—").capitalize(),
            "amount":     row.get("amount", "—"),
            "date":       date_str[:10] if date_str else "—",
            "asset":      row.get("asset_description", ticker),
        })

    # Senate
    for row in _fetch_senate_all():
        t = (row.get("ticker") or "").upper().strip()
        if t != ticker_upper:
            continue
        date_str = row.get("transaction_date") or ""
        trades.append({
            "chamber":    "Senate",
            "name":       row.get("senator", "—"),
            "trade_type": row.get("type", "—").capitalize(),
            "amount":     row.get("amount", "—"),
            "date":       date_str[:10] if date_str else "—",
            "asset":      row.get("asset_name", ticker),
        })

    # Sort by date descending, most recent first
    def _sort_key(x):
        try:
            return datetime.strptime(x["date"], "%Y-%m-%d")
        except Exception:
            return datetime.min

    trades.sort(key=_sort_key, reverse=True)
    return trades[:limit]
