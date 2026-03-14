"""
pages/home.py -- Stocklio landing page and embedded analysis dashboard.

Rendered at the root URL (/) by app.py's st.navigation() router.
st.set_page_config and auth init are handled by app.py (the entrypoint shell).
"""

import streamlit as st
from auth.propelauth import login_url, signup_url
from ui.ads import lazy_ad_slot, SLOT_HOME_BETWEEN_STEPS_CTA, SLOT_BOTTOM_LEADERBOARD

# Critical hide CSS — injected first to prevent FOUC of Streamlit's default nav.
# Mirrors the rule in app.py; redundant injection here ensures it's applied
# immediately when the home page renders, before any other content.
st.markdown(
    "<style>"
    "[data-testid='stSidebarNav'],"
    "[data-testid='stSidebarNavItems'],"
    "[data-testid='stSidebarNavSeparator']"
    "{display:none!important;}"
    "</style>",
    unsafe_allow_html=True,
)

# Determine active ticker from URL param or session state
_url_ticker = st.query_params.get("ticker", "").upper().strip()
if _url_ticker:
    st.session_state["current_ticker"] = _url_ticker

# If a ticker is active, show the full analysis dashboard instead of the landing page
if st.session_state.get("current_ticker"):
    from ui.layout import render_stock_analysis
    from auth.propelauth import logout
    from data.recents import record_search, get_recent_searches

    _ticker = st.session_state["current_ticker"]

    # Record this search for the logged-in user
    if st.session_state.get("logged_in"):
        record_search(st.session_state["user_id"], _ticker)

    st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Darker+Grotesque:wght@700;800;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    .stApp { background-color: #f5f7fa; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 1rem !important; }
    .metric-card { background:#ffffff;border-radius:12px;padding:16px 20px;border:1px solid #e2e8f0;box-shadow:0 1px 4px rgba(0,0,0,0.06); }
    .bullish { color:#00a878;font-weight:700; } .bearish { color:#e53e3e;font-weight:700; } .neutral { color:#dd6b20;font-weight:700; }
    .signal-badge { display:inline-block;padding:3px 10px;border-radius:20px;font-size:0.78rem;font-weight:600;margin:2px; }
    .badge-bull { background:#e6faf5;color:#00a878;border:1px solid #00a878; }
    .badge-bear { background:#fff5f5;color:#e53e3e;border:1px solid #e53e3e; }
    .badge-neut { background:#fffaf0;color:#dd6b20;border:1px solid #dd6b20; }
    h1, h2, h3 { color:#1a202c !important; }
    [data-testid="stSidebar"] * { font-family:'Inter',sans-serif !important; }
    [data-testid="stSidebar"] label,[data-testid="stSidebar"] .stTextInput input,
    [data-testid="stSidebar"] .stSelectbox div,[data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span:not(.auth-btn):not(.logo-dot),
    [data-testid="stSidebar"] h3 { font-size:0.78rem !important; }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] { font-size:0.85rem !important; }
    [data-testid="stSidebarCollapseButton"],[data-testid="stSidebarHeader"] > button,
    button[aria-label*="keyboard" i],button[title*="keyboard" i] { display:none !important; }
    section[data-testid="stSidebar"] { width:273px !important;min-width:273px !important;max-width:273px !important; }
    section[data-testid="stSidebar"] > div:first-child { width:273px !important; }
    .sidebar-auth-bar { position:fixed;bottom:0;left:0;width:273px;background:#ffffff;border-top:1px solid #e2e8f0;padding:10px 16px 14px;display:flex;flex-direction:column;gap:6px;z-index:999; }
    .auth-btn { width:100%;text-align:center;padding:5px 8px;border-radius:7px;font-size:0.75rem;font-weight:600;cursor:default;border:1px solid #e2e8f0;background:#f5f7fa;color:#4a5568;font-family:'Inter',sans-serif;box-sizing:border-box; }
    .auth-btn-primary { background:#00c896;color:#ffffff;border-color:#00c896; }
    .auth-avatar { width:28px;height:28px;border-radius:50%;background:#00c896;display:inline-flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:0.8rem;flex-shrink:0; }
</style>
""", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(
            '<div style="font-family:\'Darker Grotesque\',sans-serif;font-size:3rem;font-weight:800;'
            'color:#1a202c;letter-spacing:-0.01em;margin-top:-60px;padding:4px 0 2px 0;">'
            'stocklio<span class="logo-dot" style="color:#00c896;font-size:3rem;">.</span></div>',
            unsafe_allow_html=True,
        )
        if st.button("← Back to home", use_container_width=False):
            del st.session_state["current_ticker"]
            st.rerun()
        st.markdown("---")
        st.subheader("🔍 Stock Lookup")
        ticker_input = st.text_input("Enter Ticker Symbol", value=_ticker, placeholder="e.g. NVDA, MSFT, TSLA").upper().strip()
        period_map = {"1 Month":"1mo","3 Months":"3mo","6 Months":"6mo","1 Year":"1y","2 Years":"2y"}
        period = period_map[st.selectbox("Analysis Period", list(period_map.keys()), index=3)]
        if st.button("🔎 Analyze Stock", use_container_width=True, type="primary"):
            st.session_state["current_ticker"] = ticker_input
            st.rerun()

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
                        st.session_state["current_ticker"] = _rt
                        st.rerun()

        st.markdown("---")
        _lu = login_url(); _su = signup_url()
        if st.session_state.get("logged_in"):
            ei = st.session_state["user_email"][0].upper()
            st.markdown(f'<div class="sidebar-auth-bar"><div class="auth-avatar">{ei}</div><div style="font-size:0.78rem;color:#1a202c;">{st.session_state["user_email"]}</div></div>', unsafe_allow_html=True)
            if st.button("Log out", use_container_width=True):
                logout(); st.rerun()
        else:
            st.markdown(f'<div class="sidebar-auth-bar"><a href="{_lu}" target="_self" class="auth-btn auth-btn-primary" style="text-decoration:none;">Log in</a><a href="{_su}" target="_self" class="auth-btn" style="text-decoration:none;">Sign up</a></div>', unsafe_allow_html=True)

    render_stock_analysis(ticker_input, period)
    st.stop()

# ============================================================
# LANDING PAGE
# ============================================================

_login_url  = login_url()
_signup_url = signup_url()
_is_logged_in = st.session_state.get("logged_in", False)


if _is_logged_in:
    _user_email = st.session_state.get("user_email", "")
    _welcome_banner = (
        f'<div class="lp-welcome-bar">'
        f'<span>Welcome back, <strong>{_user_email}</strong></span>'
        f'<div class="lp-welcome-actions">'
        f'<a href="/analyze?ticker=AAPL" class="lp-btn lp-btn-primary" style="padding:6px 16px;font-size:0.82rem;">Open Dashboard</a>'
        f'<a href="https://auth.stocklio.ai/account" class="lp-btn lp-btn-outline" style="padding:6px 16px;font-size:0.82rem;">My Account</a>'
        f'</div>'
        f'</div>'
    )
    _nav_links = (
        '<a href="/blog" class="lp-btn lp-btn-outline">Blog</a>'
        '<a href="/pricing" target="_self" class="lp-btn lp-btn-outline">Pricing</a>'
        '<a href="https://auth.stocklio.ai/account" class="lp-btn lp-btn-outline">My Account</a>'
        '<a href="/analyze?ticker=AAPL" class="lp-btn lp-btn-primary">Open Dashboard</a>'
    )
else:
    _welcome_banner = ""
    _nav_links = (
        f'<a href="/blog" class="lp-btn lp-btn-outline">Blog</a>'
        f'<a href="/pricing" target="_self" class="lp-btn lp-btn-outline">Pricing</a>'
        f'<a href="{_login_url}" target="_self" class="lp-btn lp-btn-outline">Log in</a>'
        f'<a href="{_signup_url}" target="_self" class="lp-btn lp-btn-primary">Sign up free</a>'
    )

st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Darker+Grotesque:wght@700;800;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    .stApp {{ background-color: #f5f7fa; }}
    .block-container {{ padding-top: 1rem !important; padding-bottom: 0 !important; max-width: 1400px; padding-left: 2rem !important; padding-right: 2rem !important; }}
    section[data-testid="stSidebar"] {{ display: none !important; }}
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarHeader"] > button,
    button[aria-label*="keyboard" i],
    button[title*="keyboard" i],
    [data-testid="stToolbar"],
    [data-testid="stHeaderActionElements"] {{ display: none !important; }}

    /* Nav */
    .lp-nav {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 20px 0 16px 0;
        border-bottom: 1px solid #e2e8f0;
    }}
    .lp-logo {{
        font-family: 'Darker Grotesque', sans-serif;
        font-size: 6rem;
        font-weight: 800;
        color: #1a202c;
        letter-spacing: -0.01em;
        line-height: 1;
    }}
    .lp-logo-dot {{ color: #00c896; }}
    .lp-welcome-bar {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #e6faf5;
        border: 1px solid #b2f0e0;
        border-radius: 10px;
        padding: 10px 20px;
        margin: 14px 0 0 0;
        font-family: 'Inter', sans-serif;
        font-size: 0.88rem;
        color: #1a202c;
        flex-wrap: wrap;
        gap: 10px;
    }}
    .lp-welcome-actions {{ display: flex; gap: 8px; flex-wrap: wrap; }}
    .lp-nav-links {{ display: flex; gap: 12px; align-items: center; }}
    .lp-btn {{
        display: inline-block;
        padding: 8px 20px;
        border-radius: 8px;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 600;
        text-decoration: none !important;
        cursor: pointer;
    }}
    .lp-btn-outline {{ border: 1px solid #cbd5e0; color: #1a202c; background: #ffffff; }}
    .lp-btn-primary {{ background: #00c896; color: #ffffff !important; border: 1px solid #00c896; }}

    /* Hero */
    .lp-eyebrow {{
        display: inline-block;
        background: #e6faf5;
        color: #00a878;
        border: 1px solid #00c896;
        border-radius: 20px;
        padding: 4px 14px;
        font-family: 'Inter', sans-serif;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        margin-bottom: 20px;
    }}
    .lp-h1 {{
        font-family: 'Darker Grotesque', sans-serif !important;
        font-size: 4.5rem !important;
        font-weight: 900;
        color: #1a202c;
        line-height: 1.05;
        letter-spacing: -0.02em;
        margin: 0 0 4px 0;
    }}
    .lp-sub {{
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        color: #4a5568;
        max-width: 640px;
        margin: 0 auto 0 auto;
        line-height: 1.7;
        text-align: center;
    }}

    /* Native Streamlit search form styling */
    div[data-testid="stForm"] {{
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }}
    div[data-testid="stForm"] > div {{
        gap: 8px !important;
    }}
    .lp-search-wrap .stTextInput input {{
        border-radius: 10px !important;
        border: 1.5px solid #cbd5e0 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 1rem !important;
        padding: 12px 16px !important;
        background: #ffffff !important;
        color: #1a202c !important;
    }}
    .lp-search-wrap .stTextInput input:focus {{
        border-color: #00c896 !important;
        box-shadow: 0 0 0 2px rgba(0,200,150,0.15) !important;
    }}
    .lp-search-wrap button[kind="primaryFormSubmit"],
    .lp-search-wrap button[kind="primary"] {{
        background: #00c896 !important;
        border-color: #00c896 !important;
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        border-radius: 10px !important;
        padding: 12px 28px !important;
        width: 100% !important;
    }}

    /* Stats strip */
    .lp-stats {{
        display: flex;
        justify-content: center;
        gap: 48px;
        padding: 32px 0;
        border-top: 1px solid #e2e8f0;
        border-bottom: 1px solid #e2e8f0;
    }}
    .lp-stat-num {{
        font-family: 'Darker Grotesque', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        color: #1a202c;
        line-height: 1;
    }}
    .lp-stat-label {{
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #6b7280;
        margin-top: 4px;
    }}

    /* Features */
    .lp-section {{ padding: 64px 0 0 0; }}
    .lp-section-label {{
        font-family: 'Inter', sans-serif;
        font-size: 0.78rem;
        font-weight: 600;
        color: #00a878;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        text-align: center;
        margin-bottom: 10px;
    }}
    .lp-section-title {{
        font-family: 'Darker Grotesque', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        color: #1a202c;
        text-align: center;
        margin: 0 0 8px 0;
        letter-spacing: -0.01em;
    }}
    .lp-section-sub {{
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        color: #6b7280;
        text-align: center;
        max-width: 540px;
        margin: 0 auto 44px auto;
        line-height: 1.6;
    }}
    .lp-cards {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
    }}
    .lp-card {{
        background: #ffffff;
        border-radius: 14px;
        padding: 28px 24px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }}
    .lp-card-icon {{ font-size: 1.8rem; margin-bottom: 14px; }}
    .lp-card-title {{
        font-family: 'Darker Grotesque', sans-serif;
        font-size: 1.25rem;
        font-weight: 800;
        color: #1a202c;
        margin-bottom: 8px;
    }}
    .lp-card-body {{
        font-family: 'Inter', sans-serif;
        font-size: 0.88rem;
        color: #4a5568;
        line-height: 1.65;
    }}
    .lp-card-tag {{
        display: inline-block;
        margin-top: 14px;
        background: #e6faf5;
        color: #00a878;
        border-radius: 6px;
        padding: 3px 10px;
        font-family: 'Inter', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
    }}

    /* How it works */
    .lp-steps {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
        padding: 16px 0 0 0;
    }}
    .lp-step {{ text-align: center; padding: 20px 16px; }}
    .lp-step-num {{
        width: 40px;
        height: 40px;
        background: #00c896;
        color: #ffffff;
        border-radius: 50%;
        font-family: 'Darker Grotesque', sans-serif;
        font-size: 1.2rem;
        font-weight: 800;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 14px auto;
    }}
    .lp-step-title {{
        font-family: 'Darker Grotesque', sans-serif;
        font-size: 1.1rem;
        font-weight: 800;
        color: #1a202c;
        margin-bottom: 6px;
    }}
    .lp-step-body {{
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: #6b7280;
        line-height: 1.6;
    }}

    /* CTA band */
    .lp-cta-band {{
        background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
        border-radius: 16px;
        padding: 52px 40px 36px 40px;
        text-align: center;
        margin: 56px 0 0 0;
    }}
    .lp-cta-band h2 {{
        font-family: 'Darker Grotesque', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff !important;
        margin: 0 0 10px 0;
        letter-spacing: -0.01em;
    }}
    .lp-cta-band p {{
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        color: #a0aec0;
        margin: 0;
    }}

    /* Footer */
    .lp-footer {{
        padding: 32px 0 36px 0;
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #a0aec0;
        border-top: 1px solid #e2e8f0;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }}
    .lp-footer-copy {{ color: #a0aec0; }}
    .lp-footer-section {{ text-align: left; }}
    .lp-footer-section-title {{
        font-family: 'Inter', sans-serif;
        font-size: 0.72rem;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 8px;
    }}
    .lp-footer-link {{
        display: block;
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #a0aec0;
        text-decoration: none !important;
        margin-bottom: 4px;
    }}
    .lp-footer-link:hover {{ color: #4a5568; }}
</style>

<!-- Nav -->
<div class="lp-nav">
    <div class="lp-logo">stocklio<span class="lp-logo-dot">.</span></div>
    <div class="lp-nav-links">
        {_nav_links}
    </div>
</div>

{_welcome_banner}

<!-- Hero heading & subtext -->
<div style="text-align:center;padding:36px 20px 24px 20px;">
    <div class="lp-eyebrow">AI Forecast · Prediction Market · Technical Analysis</div>
    <h1 class="lp-h1"><span style="color:#1a202c;">Know where the market is headed</span><br>
    <span style="display:block;margin-top:-0.15em;color:#00c896;">before it moves.</span></h1>
    <div style="display:flex;justify-content:center;width:100%;margin-top:12px;">
        <p class="lp-sub" style="text-align:center;max-width:640px;margin:0 auto;">
            Stocklio combines AI analysis, technical signals, and market sentiment to help individual investors spot opportunities and make smarter trades.
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Hero search — native Streamlit (bypasses JS interception entirely) ──
_, _hero_col, _ = st.columns([1, 2, 1])
with _hero_col:
    st.markdown('<div class="lp-search-wrap">', unsafe_allow_html=True)
    with st.form("hero_search", border=False):
        _lp_ticker = st.text_input(
            "ticker",
            placeholder="Get a stock forecast, e.g. AAPL",
            label_visibility="collapsed",
        )
        _hero_submitted = st.form_submit_button("Get Forecast →", use_container_width=True, type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    if _hero_submitted:
        _t = _lp_ticker.strip().upper()
        if _t:
            st.session_state["auto_ticker"] = _t
            st.switch_page("pages/1_Analyze.py")
        else:
            st.warning("Please enter a ticker symbol.")

st.markdown(f"""
<!-- Stats strip -->
<div class="lp-stats">
    <div style="text-align:center;">
        <div class="lp-stat-num">10+</div>
        <div class="lp-stat-label">Technical indicators</div>
    </div>
    <div style="text-align:center;">
        <div class="lp-stat-num">3</div>
        <div class="lp-stat-label">Intelligence layers</div>
    </div>
    <div style="text-align:center;">
        <div class="lp-stat-num">Real-time</div>
        <div class="lp-stat-label">Market data</div>
    </div>
    <div style="text-align:center;">
        <div class="lp-stat-num">1</div>
        <div class="lp-stat-label">Unified dashboard</div>
    </div>
</div>

<!-- Features -->
<div class="lp-section">
    <div class="lp-section-label">What Stocklio does</div>
    <h2 class="lp-section-title">Three layers of intelligence, one dashboard.</h2>
    <div style="display:flex;justify-content:center;width:100%;">
        <p class="lp-section-sub" style="text-align:center;max-width:540px;margin:0 auto 44px auto;">
            Most tools give you one signal. Stocklio layers AI forecasting, community wisdom,
            and proven chart strategies so no angle goes unanalyzed.
        </p>
    </div>
    <div class="lp-cards">
        <div class="lp-card">
            <div class="lp-card-icon">🤖</div>
            <div class="lp-card-title">AI-Powered Analytics</div>
            <div class="lp-card-body">
                Stocklio's composite scoring engine reads RSI, MACD, Bollinger Bands,
                momentum, and more — then synthesizes them into a single directional forecast.
                See the stock's likely trajectory before you commit a dollar.
            </div>
            <span class="lp-card-tag">Composite Score</span>
        </div>
        <div class="lp-card">
            <div class="lp-card-icon">🌐</div>
            <div class="lp-card-title">Community Sentiment</div>
            <div class="lp-card-body">
                Markets move on psychology as much as fundamentals. Stocklio's prediction market
                captures where real investors think a stock is headed — and tracks how accurate
                the crowd has been over the last 90 days.
            </div>
            <span class="lp-card-tag">Prediction Market</span>
        </div>
        <div class="lp-card">
            <div class="lp-card-icon">📊</div>
            <div class="lp-card-title">Technical Chart Analysis</div>
            <div class="lp-card-body">
                Built on time-tested strategies including <strong>Ride the Nine</strong> — a 9 EMA strategy
                used by professional traders to identify low-risk entries, trend confirmation,
                and early exit signals.
            </div>
            <span class="lp-card-tag">Ride the Nine · EMA · SMA</span>
        </div>
    </div>
</div>

<!-- How it works -->
<div class="lp-section">
    <div class="lp-section-label">How it works</div>
    <h2 class="lp-section-title">Analysis in seconds. Not hours.</h2>
    <div class="lp-steps">
        <div class="lp-step">
            <div class="lp-step-num">1</div>
            <div class="lp-step-title">Enter any ticker</div>
            <div class="lp-step-body">Type in any stock symbol — AAPL, NVDA, TSLA, anything publicly traded — and choose your time window.</div>
        </div>
        <div class="lp-step">
            <div class="lp-step-num">2</div>
            <div class="lp-step-title">Stocklio runs the analysis</div>
            <div class="lp-step-body">AI scores the stock, flags notable setups, maps support and resistance, and projects a 10-day price trajectory.</div>
        </div>
        <div class="lp-step">
            <div class="lp-step-num">3</div>
            <div class="lp-step-title">Make a confident decision</div>
            <div class="lp-step-body">See the community vote, compare it to the AI forecast, and use the Ride the Nine chart to time your entry or exit.</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Homepage ad — lazy, between "How it works" and CTA band ──────────────────
lazy_ad_slot(SLOT_HOME_BETWEEN_STEPS_CTA, ad_format="auto", height=100, full_width_responsive=True)

st.markdown(f"""
<!-- CTA Band -->
<div class="lp-cta-band">
    <h2>{"Your edge is ready." if _is_logged_in else "Stop guessing. Start analyzing."}</h2>
    <p>{"Open your dashboard and run your next analysis." if _is_logged_in else "Free to use. No credit card required."}</p>
</div>
""", unsafe_allow_html=True)

# CTA band buttons (native Streamlit, centered below the dark band)
_, _cta_col, _ = st.columns([1, 2, 1])
with _cta_col:
    st.markdown('<div class="lp-search-wrap" style="margin-top:16px;">', unsafe_allow_html=True)
    with st.form("cta_search", border=False):
        _cta_ticker = st.text_input(
            "cta_ticker",
            placeholder="Enter a ticker to get your forecast, e.g. NVDA",
            label_visibility="collapsed",
        )
        _cta_submitted = st.form_submit_button("Get Forecast →", use_container_width=True, type="primary")
    st.markdown('</div>', unsafe_allow_html=True)

    if _cta_submitted:
        _t = _cta_ticker.strip().upper()
        if _t:
            st.session_state["auto_ticker"] = _t
            st.switch_page("pages/1_Analyze.py")
        else:
            st.warning("Please enter a ticker symbol.")

    if _is_logged_in:
        _cta_secondary_html = (
            '<a href="/analyze?ticker=AAPL" class="lp-btn lp-btn-outline lp-btn-lg" '
            'style="font-family:\'Inter\',sans-serif;font-size:0.95rem;padding:13px 32px;border-radius:10px;border:1px solid #4a5568;color:#1a202c;background:#ffffff;">'
            'Open Dashboard</a>'
        )
    else:
        _cta_secondary_html = (
            f'<a href="{_signup_url}" target="_self" class="lp-btn lp-btn-outline lp-btn-lg" '
            f'style="font-family:\'Inter\',sans-serif;font-size:0.95rem;padding:13px 32px;border-radius:10px;border:1px solid #4a5568;color:#1a202c;background:#ffffff;">'
            f'Create an account</a>'
        )
    st.markdown(
        f'<div style="text-align:center;margin-top:8px;">{_cta_secondary_html}</div>',
        unsafe_allow_html=True,
    )

# Bottom leaderboard — above footer, loads lazily when scrolled into view
lazy_ad_slot(SLOT_BOTTOM_LEADERBOARD, ad_format="auto", height=120)

st.markdown(f"""
<!-- Footer -->
<div class="lp-footer" style="margin-top:40px;flex-direction:column;gap:16px;">
    <div style="display:flex;justify-content:flex-end;width:100%;">
        <div class="lp-footer-section">
            <div class="lp-footer-section-title">Resources</div>
            <a href="/blog" class="lp-footer-link">Blog</a>
            <a href="/pricing" class="lp-footer-link">Pricing</a>
            {"<a href='/analyze?ticker=AAPL' class='lp-footer-link'>Open Dashboard</a><a href='https://auth.stocklio.ai/account' target='_self' class='lp-footer-link'>My Account</a>" if _is_logged_in else f"<a href='{_signup_url}' target='_self' class='lp-footer-link'>Create an account</a><a href='{_login_url}' target='_self' class='lp-footer-link'>Log in</a>"}
            <a href="mailto:hello@stocklio.ai" class="lp-footer-link">hello@stocklio.ai</a>
        </div>
    </div>
    <div class="lp-footer-copy">
        © 2025 Stocklio · Built for investors who want an edge.
        &nbsp;·&nbsp;<a href="/privacy" style="color:#a0aec0;text-decoration:none;" onmouseover="this.style.color='#4a5568'" onmouseout="this.style.color='#a0aec0'">Privacy Policy</a>
        &nbsp;·&nbsp;<a href="/terms" style="color:#a0aec0;text-decoration:none;" onmouseover="this.style.color='#4a5568'" onmouseout="this.style.color='#a0aec0'">Terms of Service</a>
        &nbsp;·&nbsp;<a href="/cookies" style="color:#a0aec0;text-decoration:none;" onmouseover="this.style.color='#4a5568'" onmouseout="this.style.color='#a0aec0'">Cookie Policy</a>
    </div>
</div>
""", unsafe_allow_html=True)
