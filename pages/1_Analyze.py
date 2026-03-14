"""
pages/1_Analyze.py -- Stock analysis dashboard (accessible at /Analyze)
"""

import streamlit as st
from ui.layout import render_stock_analysis
from auth.propelauth import logout, login_url, signup_url
from data.recents import record_search, get_recent_searches

# st.set_page_config, inject_auth_js, handle_auth_callback are handled by app.py shell
# Sidebar is shown via initial_sidebar_state="expanded" in app.py (Streamlit-native,
# works in all environments). JS-based auto-expand was removed because components.html()
# iframes are cross-origin in production (behind a reverse proxy), causing
# window.parent.document access to throw a SecurityError silently.

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Darker+Grotesque:wght@700;800;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    .stApp { background-color: #f5f7fa; }
    .block-container { padding-top: 1rem !important; padding-bottom: 1rem !important; }
    .metric-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 16px 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .bullish  { color: #00a878; font-weight: 700; }
    .bearish  { color: #e53e3e; font-weight: 700; }
    .neutral  { color: #dd6b20; font-weight: 700; }
    .signal-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 2px;
    }
    .badge-bull { background: #e6faf5; color: #00a878; border: 1px solid #00a878; }
    .badge-bear { background: #fff5f5; color: #e53e3e; border: 1px solid #e53e3e; }
    .badge-neut { background: #fffaf0; color: #dd6b20; border: 1px solid #dd6b20; }
    h1, h2, h3 { color: #1a202c !important; }
    .stTabs { margin-top: 24px; }
    .sec-gap { margin-top: 36px; }
    .stTabs [data-baseweb="tab"] { color: #4a5568; font-size: 1.6rem; font-weight: 1000; }
    .stTabs [aria-selected="true"] { color: #00c896 !important; }
    [data-testid="stSidebar"] * { font-family: 'Inter', sans-serif !important; }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stTextInput input,
    [data-testid="stSidebar"] .stSelectbox div,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span:not(.auth-btn):not(.logo-dot),
    [data-testid="stSidebar"] h3 { font-size: 0.78rem !important; }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] { font-size: 0.85rem !important; }
    button[aria-label*="keyboard" i],
    button[title*="keyboard" i] { display: none !important; }
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarHeader"] > button { display: none !important; }
    section[data-testid="stSidebar"] { width: 273px !important; min-width: 273px !important; max-width: 273px !important; }
    section[data-testid="stSidebar"] > div:first-child { width: 273px !important; }
    .sidebar-auth-bar {
        position: fixed;
        bottom: 0;
        left: 0;
        width: 273px;
        background: #ffffff;
        border-top: 1px solid #e2e8f0;
        padding: 10px 16px 14px;
        display: flex;
        flex-direction: column;
        gap: 6px;
        z-index: 999;
    }
    .auth-btn {
        width: 100%;
        text-align: center;
        padding: 5px 8px;
        border-radius: 7px;
        font-size: 0.75rem;
        font-weight: 600;
        cursor: default;
        border: 1px solid #e2e8f0;
        background: #f5f7fa;
        color: #4a5568;
        font-family: 'Inter', sans-serif;
        box-sizing: border-box;
    }
    .auth-btn-primary {
        background: #00c896;
        color: #ffffff;
        border-color: #00c896;
    }
    .auth-avatar {
        width: 28px; height: 28px; border-radius: 50%;
        background: #00c896;
        display: inline-flex; align-items: center; justify-content: center;
        color: #fff; font-weight: 700; font-size: 0.8rem;
        flex-shrink: 0;
    }
    .lp-footer {
        padding: 32px 0 36px 0;
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #a0aec0;
        border-top: 1px solid #e2e8f0;
        margin-top: 48px;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }
    .lp-footer-copy { color: #a0aec0; }
    .lp-footer-section-title {
        font-family: 'Inter', sans-serif;
        font-size: 0.72rem;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 8px;
    }
    .lp-footer-link {
        display: block;
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #a0aec0;
        text-decoration: none !important;
        margin-bottom: 4px;
    }
    .lp-footer-link:hover { color: #4a5568; }
</style>
""", unsafe_allow_html=True)

# -- Auth gate -----------------------------------------------------------------
# Only enforce on app.stocklio.ai. On www.stocklio.ai the analyze page is public.
# inject_auth_js() already ran in app.py — its iframe JS will detect an active
# PropelAuth session and reload with ?pa_token= if the user is logged in.
# Localhost is always bypassed so local development works without a PropelAuth session.
_is_app_host = st.session_state.get("_is_app_host", True)
_is_localhost = st.session_state.get("_is_localhost", False)
if _is_app_host and not _is_localhost and not st.session_state.get("logged_in"):
    _gate_login  = login_url()
    _gate_signup = signup_url()
    st.markdown(
        f"""
        <div style="display:flex;flex-direction:column;align-items:center;
             justify-content:center;min-height:60vh;text-align:center;
             font-family:'Inter',sans-serif;">
          <div style="font-family:'Darker Grotesque',sans-serif;font-size:3rem;
               font-weight:800;color:#1a202c;letter-spacing:-0.01em;margin-bottom:8px;">
            stocklio<span style="color:#00c896;">.</span>
          </div>
          <p style="color:#6b7280;font-size:1rem;margin:0 0 32px 0;">
            Sign in to access AI-powered stock analysis.
          </p>
          <div style="display:flex;gap:12px;justify-content:center;">
            <a href="{_gate_login}" target="_self"
               style="background:#00c896;color:#fff;padding:10px 28px;border-radius:8px;
                      text-decoration:none;font-weight:600;font-size:0.95rem;">
              Log in
            </a>
            <a href="{_gate_signup}" target="_self"
               style="background:#f5f7fa;color:#4a5568;padding:10px 28px;border-radius:8px;
                      text-decoration:none;font-weight:600;font-size:0.95rem;
                      border:1px solid #e2e8f0;">
              Sign up
            </a>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

# -- Sidebar -------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div style="font-family:\'Darker Grotesque\',sans-serif;font-size:3rem;font-weight:800;'
        'color:#1a202c;letter-spacing:-0.01em;margin-top:-60px;padding:4px 0 2px 0;">'
        'stocklio<span class="logo-dot" style="color:#00c896;font-size:3rem;">.</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<a href="https://www.stocklio.ai" target="_self" style="text-decoration:none;font-size:0.9rem;color:#4a5568;">← Home</a>', unsafe_allow_html=True)
    st.markdown("---")

    st.subheader("🔍 Stock Lookup")
    # Seed ticker on first load, or when URL changes externally (trending bar, direct link).
    # Never overwrite what the user is actively typing.
    _url_ticker = st.query_params.get("ticker", "").upper().strip()
    # If home page sent us here via auto_ticker, promote it into the URL so the
    # analysis fires immediately (same as clicking a direct /analyze?ticker=XYZ link).
    _auto = st.session_state.pop("auto_ticker", None)
    if _auto and not _url_ticker:
        st.query_params["ticker"] = _auto.upper().strip()
        st.rerun()
    _last_url   = st.session_state.get("_last_url_ticker", "")
    if "ticker_input" not in st.session_state:
        _seed = _url_ticker or "AAPL"
        st.session_state["ticker_input"]    = _seed
        st.session_state["_last_url_ticker"] = _url_ticker
    elif _url_ticker and _url_ticker != _last_url:
        # URL changed externally — sync the input
        st.session_state["ticker_input"]    = _url_ticker
        st.session_state["_last_url_ticker"] = _url_ticker

    with st.form("ticker_form"):
        ticker_input = st.text_input(
            "Enter Ticker Symbol",
            key="ticker_input",
            placeholder="e.g. NVDA, MSFT, TSLA",
        ).upper().strip()

        period_map = {
            "1 Month":  "1mo",
            "3 Months": "3mo",
            "6 Months": "6mo",
            "1 Year":   "1y",
            "2 Years":  "2y",
        }
        selected_period_label = st.selectbox("Analysis Period", list(period_map.keys()), index=3)
        period = period_map[selected_period_label]

        analyze_btn = st.form_submit_button("🔎 Analyze Stock", use_container_width=True, type="primary")

    # Recent searches — only for logged-in users
    if st.session_state.get("logged_in"):
        _recents = get_recent_searches(st.session_state["user_id"])
        if _recents:
            st.markdown("---")
            st.markdown(
                "<p style='font-size:0.72rem;font-weight:600;color:#6b7280;"
                "text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;'>"
                "Recent Searches</p>",
                unsafe_allow_html=True,
            )
            for _rt in _recents:
                if st.button(_rt, key=f"recent_{_rt}", use_container_width=True):
                    st.session_state["_last_url_ticker"] = _rt
                    st.query_params["ticker"] = _rt
                    st.rerun()

    st.markdown("---")

    if st.session_state.get("logged_in"):
        st.markdown(
            f'<div class="sidebar-auth-bar">'
            f'<a href="https://auth.stocklio.ai/account" class="auth-btn auth-btn-primary" '
            f'style="text-decoration:none;cursor:pointer;color:#fff;">My Account</a>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        _login_url  = login_url()
        _signup_url = signup_url()
        st.markdown(
            f'<div class="sidebar-auth-bar">'
            f'<a href="{_login_url}" target="_self" class="auth-btn auth-btn-primary" '
            f'style="text-decoration:none;cursor:pointer;">Log in</a>'
            f'<a href="{_signup_url}" target="_self" class="auth-btn" '
            f'style="text-decoration:none;cursor:pointer;">Sign up</a>'
            f'</div>',
            unsafe_allow_html=True,
        )

# -- Main content --------------------------------------------------------------
if analyze_btn:
    if ticker_input:
        # Update URL and record the applied value so pre-populate won't fight it
        st.session_state["_last_url_ticker"] = ticker_input
        st.query_params["ticker"] = ticker_input
        st.rerun()
    else:
        st.warning("Please enter a ticker symbol.")

_active_ticker = st.query_params.get("ticker", "").upper().strip()
if _active_ticker:
    if st.session_state.get("logged_in"):
        record_search(st.session_state["user_id"], _active_ticker)
    render_stock_analysis(_active_ticker, period)
else:
    st.info("Enter a ticker in the sidebar and click **Analyze Stock** to get started.")

# -- Footer --------------------------------------------------------------------
_footer_login_url  = login_url()
_footer_signup_url = signup_url()
st.markdown(f"""
<div class="lp-footer" style="flex-direction:column;gap:16px;">
    <div style="display:flex;justify-content:flex-end;width:100%;">
        <div>
            <div class="lp-footer-section-title">Resources</div>
            <a href="/blog" class="lp-footer-link">Blog</a>
            <a href="{_footer_signup_url}" target="_self" class="lp-footer-link">Create an account</a>
            <a href="{_footer_login_url}" target="_self" class="lp-footer-link">Log in</a>
            <a href="mailto:hello@stocklio.ai" class="lp-footer-link">hello@stocklio.ai</a>
        </div>
    </div>
    <div class="lp-footer-copy">© 2025 Stocklio · Built for investors who want an edge.</div>
</div>
""", unsafe_allow_html=True)
