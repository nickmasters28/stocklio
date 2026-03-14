"""
pages/payment_success.py -- Post-payment landing page (/payment-success)

Stripe redirects here after a successful checkout with ?session_id=xxx.
The user must be logged in — we use their session user_id to write the
subscription to Supabase, then prompt them to refresh so the new tier loads.
"""

import streamlit as st
from data.stripe_billing import activate_pro_from_session

st.markdown(
    "<style>"
    "[data-testid='stSidebarNav'],[data-testid='stSidebarNavItems'],"
    "[data-testid='stSidebarNavSeparator']{display:none!important;}"
    "section[data-testid='stSidebar']{display:none!important;}"
    "[data-testid='stToolbar'],[data-testid='stHeaderActionElements'],"
    "[data-testid='stSidebarCollapseButton'],[data-testid='stSidebarHeader']>button,"
    "button[aria-label*='keyboard' i],button[title*='keyboard' i]{display:none!important;}"
    ".stApp{background-color:#f5f7fa;}"
    ".block-container{max-width:600px;padding-top:4rem!important;}"
    "</style>",
    unsafe_allow_html=True,
)

session_id  = st.query_params.get("session_id", "")
user_id     = st.session_state.get("user_id", "")
user_email  = st.session_state.get("user_email", "")

if not session_id:
    st.error("No payment session found. If you completed a payment, please contact hello@stocklio.ai.")
    st.page_link("pages/pricing.py", label="← Back to Pricing")
    st.stop()

if not user_id:
    # User isn't logged in yet — ask them to log in first, then we'll re-process
    st.warning("Please log in to activate your Pro subscription.")
    st.markdown(
        f'<a href="/analyze?ticker=AAPL" target="_self" style="color:#00a878;">Log in →</a>',
        unsafe_allow_html=True,
    )
    st.stop()

# Avoid re-processing on rerun
_cache_key = f"_stripe_activated_{session_id}"

if st.session_state.get(_cache_key) is None:
    with st.spinner("Activating your Pro account..."):
        success, result = activate_pro_from_session(session_id, user_id, user_email)
    st.session_state[_cache_key] = (success, result)
    if success:
        # Immediately reflect the new tier in this session
        st.session_state["subscription_tier"] = "pro"
else:
    success, result = st.session_state[_cache_key]

if success:
    st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Darker+Grotesque:wght@700;800;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<div style="text-align:center;font-family:'Inter',sans-serif;padding:32px 0;">
    <div style="font-size:3.5rem;margin-bottom:16px;">&#127881;</div>
    <div style="font-family:'Darker Grotesque',sans-serif;font-size:2.6rem;font-weight:900;
         color:#1a202c;letter-spacing:-0.01em;margin-bottom:8px;">You're on Pro!</div>
    <p style="color:#4a5568;font-size:1rem;margin-bottom:32px;">
        Pro features are now active for <strong>{result}</strong>.<br>
        Head to the dashboard to start using them.
    </p>
    <a href="/analyze?ticker=AAPL" target="_self"
       style="display:inline-block;background:#00c896;color:#fff;font-family:'Inter',sans-serif;
              font-weight:600;font-size:0.95rem;padding:12px 32px;border-radius:10px;
              text-decoration:none;">
        Go to Dashboard &rarr;
    </a>
    <div style="margin-top:16px;">
        <a href="/" target="_self" style="color:#a0aec0;font-size:0.85rem;text-decoration:none;">
            Back to Home
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

else:
    st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Darker+Grotesque:wght@700;800;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<div style="text-align:center;font-family:'Inter',sans-serif;padding:32px 0;">
    <div style="font-size:3rem;margin-bottom:16px;">&#9888;&#65039;</div>
    <div style="font-family:'Darker Grotesque',sans-serif;font-size:2.2rem;font-weight:900;
         color:#1a202c;margin-bottom:8px;">Something went wrong</div>
    <p style="color:#4a5568;font-size:1rem;margin-bottom:8px;">{result}</p>
    <p style="color:#a0aec0;font-size:0.85rem;margin-bottom:32px;">
        Your payment was received by Stripe — we just couldn't activate automatically.<br>
        Email <a href="mailto:hello@stocklio.ai" style="color:#00a878;">hello@stocklio.ai</a> and we'll sort it out immediately.
    </p>
    <a href="/pricing" target="_self"
       style="display:inline-block;background:#f5f7fa;color:#1a202c;font-family:'Inter',sans-serif;
              font-weight:600;font-size:0.9rem;padding:10px 28px;border-radius:10px;
              text-decoration:none;border:1px solid #e2e8f0;">
        &larr; Back to Pricing
    </a>
</div>
""", unsafe_allow_html=True)
