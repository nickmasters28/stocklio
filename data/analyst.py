"""
data/analyst.py -- Analyst intelligence via yfinance (free, no API key required).

Three data points:
  - Recommendation trends  (ticker.recommendations)
  - Price targets          (ticker.analyst_price_targets)
  - Upgrades/downgrades    (ticker.upgrades_downgrades)

All functions are @st.cache_data with a 1-hour TTL.
All functions return an empty dict/list on any failure so the UI degrades gracefully.
"""

import sys
import streamlit as st


def _ticker(symbol: str):
    import yfinance as yf
    return yf.Ticker(symbol)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_recommendations(ticker: str) -> list:
    """
    Returns analyst recommendation counts for the most recent period.
    Each entry: {period, strongBuy, buy, hold, sell, strongSell}
    """
    try:
        df = _ticker(ticker).recommendations
        if df is None or df.empty:
            return []
        # yfinance returns columns: strongBuy, buy, hold, sell, strongSell, period
        latest = df.iloc[-1]
        return [{
            "period":     str(latest.name)[:7] if hasattr(latest, "name") else "",
            "strongBuy":  int(latest.get("strongBuy", 0)),
            "buy":        int(latest.get("buy", 0)),
            "hold":       int(latest.get("hold", 0)),
            "sell":       int(latest.get("sell", 0)),
            "strongSell": int(latest.get("strongSell", 0)),
        }]
    except Exception as e:
        print(f"[analyst] fetch_recommendations({ticker}): {e}", file=sys.stderr)
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_price_target(ticker: str) -> dict:
    """
    Returns analyst consensus price target.
    Keys: targetHigh, targetLow, targetMean, targetMedian, numberOfAnalysts
    """
    try:
        pt = _ticker(ticker).analyst_price_targets
        if pt is None:
            return {}
        return {
            "targetMean":        float(pt.get("mean", 0) or 0),
            "targetHigh":        float(pt.get("high", 0) or 0),
            "targetLow":         float(pt.get("low", 0) or 0),
            "targetMedian":      float(pt.get("median", 0) or 0),
            "numberOfAnalysts":  int(pt.get("numberOfAnalysts", 0) or 0),
            "lastUpdated":       "",
        }
    except Exception as e:
        print(f"[analyst] fetch_price_target({ticker}): {e}", file=sys.stderr)
        return {}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_upgrades_downgrades(ticker: str) -> list:
    """
    Returns the 6 most recent analyst rating changes.
    Each entry: {company, fromGrade, toGrade, action, gradeTime}
    """
    try:
        df = _ticker(ticker).upgrades_downgrades
        if df is None or df.empty:
            return []
        # Most recent first
        df = df.sort_index(ascending=False).head(6)
        results = []
        for ts, row in df.iterrows():
            action = str(row.get("Action", "")).lower()
            if action == "up":
                action_key = "up"
            elif action == "down":
                action_key = "down"
            else:
                action_key = "init"
            results.append({
                "company":   str(row.get("Firm", "—")),
                "fromGrade": str(row.get("FromGrade", "—")),
                "toGrade":   str(row.get("ToGrade", "—")),
                "action":    action_key,
                "gradeTime": int(ts.timestamp()) if hasattr(ts, "timestamp") else 0,
            })
        return results
    except Exception as e:
        print(f"[analyst] fetch_upgrades_downgrades({ticker}): {e}", file=sys.stderr)
        return []
