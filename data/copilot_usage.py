"""
data/copilot_usage.py -- Stocklio Copilot monthly message usage tracking.

Supabase table (run once in your Supabase SQL editor):

  create table copilot_usage (
    user_id  text    not null,
    month    text    not null,   -- "YYYY-MM"  e.g. "2026-03"
    count    integer not null default 0,
    primary key (user_id, month)
  );

Usage is tracked per user per calendar month.
The limit is MONTHLY_LIMIT messages — callers must check before calling increment_usage().
"""

import sys
import streamlit as st
from datetime import date

MONTHLY_LIMIT = 50  # Pro messages per user per calendar month


def _db():
    """Return the shared Supabase client (cached resource from stripe_billing)."""
    from data.stripe_billing import _client
    return _client()


def get_monthly_usage(user_id: str) -> int:
    """Return how many Copilot messages this user has sent this calendar month."""
    month = date.today().strftime("%Y-%m")
    try:
        res = (
            _db()
            .table("copilot_usage")
            .select("count")
            .eq("user_id", user_id)
            .eq("month", month)
            .maybe_single()
            .execute()
        )
        return res.data["count"] if res.data else 0
    except Exception as e:
        print(f"[copilot_usage] get_monthly_usage({user_id}): {e}", file=sys.stderr)
        return 0


def increment_usage(user_id: str) -> int:
    """
    Increment the message count for the current month.
    Returns the new count, or -1 on error.
    Callers must verify usage < MONTHLY_LIMIT before calling this.
    """
    month = date.today().strftime("%Y-%m")
    try:
        db = _db()
        res = (
            db.table("copilot_usage")
            .select("count")
            .eq("user_id", user_id)
            .eq("month", month)
            .maybe_single()
            .execute()
        )
        if res.data:
            new_count = res.data["count"] + 1
            db.table("copilot_usage").update(
                {"count": new_count}
            ).eq("user_id", user_id).eq("month", month).execute()
        else:
            new_count = 1
            db.table("copilot_usage").insert(
                {"user_id": user_id, "month": month, "count": 1}
            ).execute()
        return new_count
    except Exception as e:
        print(f"[copilot_usage] increment_usage({user_id}): {e}", file=sys.stderr)
        return -1
