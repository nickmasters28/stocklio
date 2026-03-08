"""
pages/1_Analyze.py -- Stock analysis dashboard (accessible at /Analyze)
"""

import streamlit as st
from ui.layout import render_stock_analysis
from auth.propelauth import inject_auth_js, handle_auth_callback, logout, login_url, signup_url

st.set_page_config(
    page_title="Analyze — Stocklio",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_auth_js()
handle_auth_callback()

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Darker+Grotesque:wght@700;800;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    .stApp { background-color: #f5f7fa; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 1rem !important; }
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
    .stTabs [data-baseweb="tab"] { color: #4a5568; }
    .stTabs [aria-selected="true"] { color: #00c896 !important; }
    [data-testid="stSidebar"] * { font-family: 'Inter', sans-serif !important; }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stTextInput input,
    [data-testid="stSidebar"] .stSelectbox div,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span:not(.auth-btn):not(.logo-dot),
    [data-testid="stSidebar"] h3 { font-size: 0.78rem !important; }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] { font-size: 0.85rem !important; }
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarHeader"] > button,
    button[aria-label*="keyboard" i],
    button[title*="keyboard" i] { display: none !important; }
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
</style>
""", unsafe_allow_html=True)

# -- Sidebar -------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div style="font-family:\'Darker Grotesque\',sans-serif;font-size:3rem;font-weight:800;'
        'color:#1a202c;letter-spacing:-0.01em;margin-top:-60px;padding:4px 0 2px 0;">'
        'stocklio<span class="logo-dot" style="color:#00c896;font-size:3rem;">.</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    st.subheader("🔍 Stock Lookup")
    # Pre-populate from landing page search (passed via session state)
    if "auto_ticker" in st.session_state and "ticker_input" not in st.session_state:
        st.session_state["ticker_input"] = st.session_state.pop("auto_ticker")
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

    analyze_btn = st.button("🔎 Analyze Stock", use_container_width=True, type="primary")

    st.markdown("---")

    if st.session_state.get("logged_in"):
        email_initial = st.session_state["user_email"][0].upper()
        email_display = st.session_state["user_email"]
        st.markdown(
            f'<div class="sidebar-auth-bar">'
            f'<div class="auth-avatar">{email_initial}</div>'
            f'<div style="font-size:0.78rem;color:#1a202c;flex:1;overflow:hidden;'
            f'text-overflow:ellipsis;white-space:nowrap;">{email_display}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("Log out", use_container_width=True, key="logout_btn"):
            logout()
            st.rerun()
    else:
        _login_url  = login_url()
        _signup_url = signup_url()
        st.markdown(
            f'<div class="sidebar-auth-bar">'
            f'<a href="{_login_url}" class="auth-btn auth-btn-primary" '
            f'style="text-decoration:none;cursor:pointer;">Log in</a>'
            f'<a href="{_signup_url}" class="auth-btn" '
            f'style="text-decoration:none;cursor:pointer;">Sign up</a>'
            f'</div>',
            unsafe_allow_html=True,
        )

# -- Main content --------------------------------------------------------------
if analyze_btn or ticker_input:
    render_stock_analysis(ticker_input, period)
else:
    st.info("Enter a ticker in the sidebar and click **Analyze Stock** to get started.")
