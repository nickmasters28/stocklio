"""
data/recents.py -- Per-user recent ticker searches stored in Supabase.

Table schema (run once in the Supabase SQL editor):

  create table recent_searches (
    id       bigint generated always as identity primary key,
    user_id  text        not null,
    ticker   text        not null,
    ts       timestamptz not null default now(),
    constraint recent_searches_user_ticker unique (user_id, ticker)
  );

  create index on recent_searches (user_id, ts desc);

The unique constraint on (user_id, ticker) ensures each ticker appears
only once per user; upserting updates the timestamp so the list stays
sorted by most-recently-searched.
"""

import streamlit as st
from datetime import datetime, timezone


@st.cache_resource
def _client():
    from supabase import create_client
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"],
    )


def record_search(user_id: str, ticker: str) -> None:
    """
    Upsert a search record for this user+ticker.
    If the ticker was already searched, its timestamp is refreshed so it
    floats to the top of the recents list.
    """
    ticker = ticker.upper().strip()
    if not user_id or not ticker:
        return
    try:
        _client().table("recent_searches").upsert(
            {"user_id": user_id, "ticker": ticker, "ts": datetime.now(timezone.utc).isoformat()},
            on_conflict="user_id,ticker",
        ).execute()
    except Exception as e:
        import sys; print(f"[recents] record_search failed: {e}", file=sys.stderr)


def get_recent_searches(user_id: str, limit: int = 10) -> list[str]:
    """
    Return up to `limit` ticker symbols this user has searched,
    ordered by most recent first.
    """
    if not user_id:
        return []
    try:
        rows = (
            _client().table("recent_searches")
            .select("ticker")
            .eq("user_id", user_id)
            .order("ts", desc=True)
            .limit(limit)
            .execute()
        ).data
        return [r["ticker"] for r in rows]
    except Exception as e:
        import sys; print(f"[recents] get_recent_searches failed: {e}", file=sys.stderr)
        return []
