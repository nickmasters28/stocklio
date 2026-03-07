"""
data/votes.py -- Community prediction votes stored in Supabase.

Table schema (run once in the Supabase SQL editor):

  create table votes (
    id        bigint generated always as identity primary key,
    ticker    text        not null,
    ts        timestamptz not null default now(),
    vote      text        not null,   -- 'bullish' | 'bearish'
    price     numeric     not null,
    tech      text        not null,   -- app forecast rating at vote time
    outcome   text,                   -- null | 'correct' | 'incorrect'
    price_out numeric                 -- price when outcome was resolved
  );

  create index on votes (ticker, ts);
"""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

import streamlit as st


@st.cache_resource
def _client():
    from supabase import create_client
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"],
    )


def cast_vote(ticker: str, direction: str, price: float, tech_rating: str):
    """Insert a new vote row. direction must be 'bullish' or 'bearish'."""
    _client().table("votes").insert({
        "ticker": ticker,
        "vote":   direction.lower(),
        "price":  round(float(price), 4),
        "tech":   tech_rating,
    }).execute()


def resolve_outcomes(ticker: str, current_price: float):
    """
    For votes on this ticker that are older than 30 days and still unresolved,
    compare the stored entry price to current_price and write 'correct' or
    'incorrect' back to Supabase.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    client = _client()
    rows = (
        client.table("votes")
        .select("id, vote, price")
        .eq("ticker", ticker)
        .is_("outcome", "null")
        .lt("ts", cutoff)
        .execute()
    ).data
    for row in rows:
        went_up = float(current_price) > float(row["price"])
        correct = (
            (row["vote"] == "bullish" and went_up) or
            (row["vote"] == "bearish" and not went_up)
        )
        client.table("votes").update({
            "outcome":   "correct" if correct else "incorrect",
            "price_out": round(float(current_price), 4),
        }).eq("id", row["id"]).execute()


def sentiment_summary(ticker: str) -> dict:
    """Bull/bear counts and percentages for all votes on a ticker."""
    votes = (
        _client().table("votes")
        .select("vote")
        .eq("ticker", ticker)
        .execute()
    ).data
    bull  = sum(1 for v in votes if v["vote"] == "bullish")
    total = len(votes)
    bear  = total - bull
    return {
        "total":    total,
        "bull":     bull,
        "bear":     bear,
        "bull_pct": round(bull / total * 100, 1) if total else 0.0,
        "bear_pct": round(bear / total * 100, 1) if total else 0.0,
    }


def sentiment_over_time(ticker: str) -> list:
    """Daily % bullish for this ticker over the last 30 days."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    votes = (
        _client().table("votes")
        .select("ts, vote")
        .eq("ticker", ticker)
        .gte("ts", cutoff)
        .order("ts")
        .execute()
    ).data
    if not votes:
        return []
    daily = defaultdict(list)
    for v in votes:
        try:
            ts = v["ts"].replace("Z", "+00:00")
            d  = datetime.fromisoformat(ts).date().isoformat()
            daily[d].append(v["vote"])
        except Exception:
            pass
    results = []
    for date in sorted(daily.keys()):
        day_votes = daily[date]
        bull = sum(1 for v in day_votes if v == "bullish")
        results.append({
            "date":     date,
            "bull_pct": round(bull / len(day_votes) * 100, 1),
        })
    return results


def accuracy_stats() -> dict:
    """
    Global community accuracy across all resolved votes in the last 90 days.
    Used to power the 'Stocklio community: X% accurate' banner.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    rows = (
        _client().table("votes")
        .select("outcome")
        .not_.is_("outcome", "null")
        .gte("ts", cutoff)
        .execute()
    ).data
    total_r = len(rows)
    correct = sum(1 for r in rows if r["outcome"] == "correct")
    return {
        "resolved": total_r,
        "correct":  correct,
        "accuracy": round(correct / total_r * 100, 1) if total_r else None,
    }
