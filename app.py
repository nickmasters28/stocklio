"""
app.py -- Main entry point for the Stock Technical Analysis Dashboard.
Run with: streamlit run app.py
"""

import streamlit as st
from ui.layout import render_stock_analysis

# -- Page config ---------------------------------------------------------------
st.set_page_config(
    page_title="Stocklio",
    page_icon="\U0001f4c8",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -- Theme overrides -----------------------------------------------------------
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Darker+Grotesque:wght@700;800;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    .stApp { background-color: #f5f7fa; }
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
    /* Hide Streamlit's keyboard-shortcut tooltip near the sidebar */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarHeader"] > button,
    button[aria-label*="keyboard" i],
    button[title*="keyboard" i] { display: none !important; }
</style>
""", unsafe_allow_html=True)

# -- Sidebar -------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div style="font-family:\'Darker Grotesque\',sans-serif;font-size:3rem;font-weight:800;color:#1a202c;letter-spacing:-0.01em;margin-top:-60px;padding:4px 0 2px 0;">stocklio<span style="color:#00c896;">.</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    st.subheader("\U0001f50d Stock Lookup")
    ticker_input = st.text_input(
        "Enter Ticker Symbol",
        value="AAPL",
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

    analyze_btn = st.button("\U0001f50e Analyze Stock", use_container_width=True, type="primary")

    st.markdown("---")

    # -- Auth ------------------------------------------------------------------
    if st.session_state.get("logged_in"):
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;">'
            f'<div style="width:32px;height:32px;border-radius:50%;background:#00c896;'
            f'display:flex;align-items:center;justify-content:center;'
            f'color:#fff;font-weight:700;font-size:0.9rem;">'
            f'{st.session_state["user_email"][0].upper()}</div>'
            f'<div style="font-size:0.85rem;color:#1a202c;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
            f'{st.session_state["user_email"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("Log out", use_container_width=True):
            st.session_state.pop("logged_in", None)
            st.session_state.pop("user_email", None)
            st.rerun()
    else:
        with st.popover("Log in", use_container_width=True):
            st.markdown("### Sign in to Stocklio")
            email    = st.text_input("Email", placeholder="you@example.com", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Sign in", use_container_width=True, type="primary", key="login_submit"):
                # Backend auth wired up later
                st.info("Auth backend not configured yet.")

    st.markdown("---")

# -- Main content --------------------------------------------------------------
if analyze_btn or ticker_input:
    render_stock_analysis(ticker_input, period)
else:
    st.info("Enter a ticker in the sidebar and click **Analyze Stock** to get started.")
