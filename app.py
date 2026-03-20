"""
app.py -- Stocklio router.

In Streamlit 1.36+, this entrypoint runs on every page load.
It sets page config, handles auth, and registers all routes via st.navigation().
"""

import streamlit as st
import streamlit.components.v1 as components
from auth.propelauth import inject_auth_js, handle_auth_callback
from data.trending import get_trending_tickers

st.set_page_config(
    page_title="Stocklio — AI-Powered Stock Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Critical hide CSS — injected as early as possible to prevent FOUC ────────
# Must come before any network calls (get_trending_tickers, auth, etc.) so the
# browser receives the hide rules before it has a chance to paint the default
# Streamlit sidebar nav, header, or menu.
st.markdown(
    "<style>"
    "[data-testid='stSidebarNav'],"
    "[data-testid='stSidebarNavItems'],"
    "[data-testid='stSidebarNavSeparator'],"
    "[data-testid='stMainMenu'],"
    "[data-testid='stHeader'],"
    "#MainMenu{display:none!important;}"
    "</style>",
    unsafe_allow_html=True,
)

# ── Subdomain detection ───────────────────────────────────────────────────────
# Detect whether we're on app.stocklio.ai (gated) or www.stocklio.ai (public).
# st.context.headers available in Streamlit 1.37+; fall back to gated (safer).
try:
    _host = st.context.headers.get("host", "")
except AttributeError:
    _host = ""
st.session_state["_is_app_host"] = not _host.startswith("www.")
st.session_state["_is_localhost"] = _host.startswith("localhost") or _host.startswith("127.0.0.1")
_actual_base = f"https://{_host}" if _host else None

inject_auth_js(current_params=dict(st.query_params), base_url_override=_actual_base)
handle_auth_callback()

# ── Head injection: hide CSS + Google Analytics ───────────────────────────────
# Inject both the nav-hide CSS and GA script directly into the parent document
# <head> so they apply before React renders the sidebar nav, preventing the
# flash of the default Streamlit page-list sidebar.
components.html(
    '<script>'
    '(function(){'
    '  var p=window.parent;'
    '  if(!p||p===window)return;'
    # Inject hide CSS into <head> immediately — faster than st.markdown() body injection
    '  if(!p.document.getElementById("_stkl_hide")){'
    '    var st=p.document.createElement("style");'
    '    st.id="_stkl_hide";'
    '    st.textContent="[data-testid=\'stSidebarNav\'],[data-testid=\'stSidebarNavItems\'],[data-testid=\'stSidebarNavSeparator\'],[data-testid=\'stMainMenu\'],[data-testid=\'stHeader\'],#MainMenu{display:none!important;}";'
    '    p.document.head.appendChild(st);'
    '  }'
    # GA injection
    '  if(p.document.getElementById("_ga_stkl"))return;'
    '  var s=p.document.createElement("script");'
    '  s.id="_ga_stkl";s.async=true;'
    '  s.src="https://www.googletagmanager.com/gtag/js?id=G-P4BE4NHFLX";'
    '  p.document.head.appendChild(s);'
    '  p.dataLayer=p.dataLayer||[];'
    '  function gtag(){p.dataLayer.push(arguments);}'
    '  gtag("js",new Date());'
    '  gtag("config","G-P4BE4NHFLX");'
    '  p.gtag=gtag;'
    '})();'
    '</script>',
    height=0,
)

# ── Trending ticker bar (server-side, no JS fetch) ───────────────────────────
_trending = get_trending_tickers()

if _trending:
    def _ticker_item(t):
        is_up = t["change_pct"] >= 0
        sign  = "+" if is_up else ""
        cls   = "tkr-up" if is_up else "tkr-dn"
        pct   = abs(t["change_pct"])
        # [TICKER_LINK] — adjust URL pattern here if your route changes
        href  = f"/analyze?ticker={t['ticker']}"
        return (
            f'<a class="tkr-item" href="{href}" target="_self">'
            f'<span class="tkr-sym">{t["ticker"]}</span>'
            f'<span class="tkr-px">${t["price"]}</span>'
            f'<span class="tkr-chg {cls}">{sign}{pct:.2f}%</span>'
            f'</a>'
        )
    _items_html = "".join(_ticker_item(t) for t in _trending)
    _track_html = _items_html + _items_html  # duplicate for seamless loop
else:
    _track_html = '<span class="tkr-msg">Market data unavailable.</span>'

st.markdown(f"""
<style>
  .tkr-bar {{
    width: 100%;
    overflow: hidden;
    border-bottom: 1px solid #e2e8f0;
    position: relative;
    margin-bottom: 0;
  }}
  .tkr-bar::before, .tkr-bar::after {{
    content: "";
    position: absolute;
    top: 0; bottom: 0;
    width: 40px;
    z-index: 2;
    pointer-events: none;
  }}
  .tkr-bar::before {{ left:  0; background: linear-gradient(to right, #f5f7fa, transparent); }}
  .tkr-bar::after  {{ right: 0; background: linear-gradient(to left,  #f5f7fa, transparent); }}
  .tkr-track {{
    display: inline-flex;
    align-items: center;
    white-space: nowrap;
    will-change: transform;
    animation: tkr-scroll 35s linear infinite; /* adjust seconds to change speed */
  }}
  .tkr-bar:hover .tkr-track {{ animation-play-state: paused; }}
  @keyframes tkr-scroll {{
    0%   {{ transform: translateX(0); }}
    100% {{ transform: translateX(-50%); }}
  }}
  .tkr-item {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 7px 18px;
    text-decoration: none !important;
    border-right: 1px solid #e2e8f0;
    transition: background 0.15s;
    cursor: pointer;
  }}
  .tkr-item:hover {{ background: rgba(0,200,150,0.07); }}
  .tkr-sym {{ font-family:'Inter',sans-serif; font-size:.76rem; font-weight:700; color:#1a202c; letter-spacing:.02em; }}
  .tkr-px  {{ font-family:'Inter',sans-serif; font-size:.76rem; font-weight:500; color:#6b7280; }}
  .tkr-chg {{ font-family:'Inter',sans-serif; font-size:.74rem; font-weight:600; min-width:50px; }}
  .tkr-up  {{ color:#00a878; }}
  .tkr-dn  {{ color:#e53e3e; }}
  .tkr-msg {{ font-family:'Inter',sans-serif; font-size:.76rem; color:#a0aec0; padding:7px 24px; }}
  /* Pin ticker tape to top of main content area */
  .tkr-bar {{
    position: fixed !important;
    top: 0;
    left: 273px;
    right: 0;
    z-index: 1002;
    background: #f5f7fa;
  }}
</style>
<div class="tkr-bar">
  <div class="tkr-track">{_track_html}</div>
</div>
""", unsafe_allow_html=True)

pg = st.navigation(
    [
        st.Page("pages/home.py",      title="Home",             url_path="",        default=True),
        st.Page("pages/blog.py",      title="Blog",             url_path="blog"),
        st.Page("pages/1_Analyze.py", title="Analyze",          url_path="analyze"),
        st.Page("pages/pricing.py",   title="Pricing",          url_path="pricing"),
        st.Page("pages/copilot.py",   title="Copilot",          url_path="copilot"),
        st.Page("pages/privacy.py",    title="Privacy Policy",   url_path="privacy"),
        st.Page("pages/terms.py",      title="Terms of Service", url_path="terms"),
        st.Page("pages/cookies.py",    title="Cookie Policy",    url_path="cookies"),
        st.Page("pages/faq.py",             title="FAQ",              url_path="faq"),
        st.Page("pages/logged_out.py",     title="Logged Out",       url_path="logged-out"),
        st.Page("pages/payment_success.py", title="Payment Success",  url_path="payment-success"),
    ],
    position="hidden",  # suppress Streamlit's default sidebar nav
)
pg.run()
