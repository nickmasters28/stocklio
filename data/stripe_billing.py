"""
data/stripe_billing.py -- Stripe checkout verification and subscription state via Supabase.

Table schema (run once in Supabase SQL editor):

  create table subscriptions (
    user_id            text primary key,
    email              text not null,
    subscription_tier  text not null default 'free',
    stripe_customer_id text,
    updated_at         timestamptz not null default now()
  );

Secrets required in .streamlit/secrets.toml:
  [stripe]
  secret_key = "sk_live_..."

  [supabase]
  url = "..."
  key = "..."
"""

import streamlit as st


# ---------------------------------------------------------------------------
# Supabase client (shared with recents.py / votes.py)
# ---------------------------------------------------------------------------

@st.cache_resource
def _client():
    from supabase import create_client
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"],
    )


# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------

def _stripe_key() -> str:
    s = st.secrets["stripe"]
    return s.get("STRIPE_SECRET_KEY") or s.get("secret_key") or s.get("STRIPE_SECRET")


def verify_checkout_session(session_id: str) -> dict | None:
    """
    Retrieve a Stripe Checkout Session and return it if payment is complete.
    Returns None on failure or if payment_status != 'paid'.
    """
    import stripe
    stripe.api_key = _stripe_key()
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.get("payment_status") == "paid":
            return session
        return None
    except Exception as e:
        import sys
        print(f"[stripe_billing] session retrieval failed: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Subscription state — Supabase
# ---------------------------------------------------------------------------

def get_subscription_tier(user_id: str) -> str:
    """Return the subscription tier for a user, defaulting to 'free'."""
    try:
        resp = (
            _client()
            .table("subscriptions")
            .select("subscription_tier")
            .eq("user_id", user_id)
            .maybe_single()
            .execute()
        )
        if resp.data:
            return resp.data.get("subscription_tier", "free")
    except Exception as e:
        import sys
        print(f"[stripe_billing] get_subscription_tier failed: {e}", file=sys.stderr)
    return "free"


def set_user_pro(user_id: str, email: str, stripe_customer_id: str) -> bool:
    """Upsert the user's subscription tier to 'pro' in Supabase."""
    try:
        _client().table("subscriptions").upsert({
            "user_id":            user_id,
            "email":              email,
            "subscription_tier":  "pro",
            "stripe_customer_id": stripe_customer_id,
            "updated_at":         "now()",
        }).execute()
        return True
    except Exception as e:
        import sys
        print(f"[stripe_billing] set_user_pro failed: {e}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Full activation flow
# ---------------------------------------------------------------------------

def activate_pro_from_session(session_id: str, user_id: str, user_email: str) -> tuple[bool, str]:
    """
    Verify Stripe session → write pro tier to Supabase.
    Returns (success: bool, message: str).

    Requires the user to already be logged in so we have their user_id.
    """
    session = verify_checkout_session(session_id)
    if not session:
        return False, "Payment not found or not completed."

    stripe_customer_id = session.get("customer", "")
    ok = set_user_pro(user_id, user_email, stripe_customer_id)
    if ok:
        return True, user_email
    return False, "Failed to activate Pro — please contact hello@stocklio.ai."
