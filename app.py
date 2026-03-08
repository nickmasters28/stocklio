"""
app.py -- Stocklio landing page.
Fast-loading static page. Analysis lives at /Analyze.
"""

import streamlit as st
from auth.propelauth import inject_auth_js, handle_auth_callback, login_url, signup_url

st.set_page_config(
    page_title="Stocklio — AI-Powered Stock Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_auth_js()
handle_auth_callback()

_login_url  = login_url()
_signup_url = signup_url()

st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Darker+Grotesque:wght@700;800;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    .stApp {{ background-color: #f5f7fa; }}
    .block-container {{ padding-top: 2rem !important; padding-bottom: 0 !important; max-width: 1100px; }}
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
        font-size: 5rem;
        font-weight: 800;
        color: #1a202c;
        letter-spacing: -0.01em;
        line-height: 1;
    }}
    .lp-logo-dot {{ color: #00c896; }}
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
    .lp-btn-primary {{ background: #00c896; color: #ffffff; border: 1px solid #00c896; }}

    /* Hero */
    .lp-hero {{
        text-align: center;
        padding: 36px 20px 48px 20px;
    }}
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
        font-size: 3.5rem !important;
        font-weight: 900;
        color: #1a202c;
        line-height: 1.05;
        letter-spacing: -0.02em;
        margin: 0 0 4px 0;
    }}
    .lp-h1 span {{ color: #00c896; }}
    .lp-sub {{
        font-family: 'Inter', sans-serif;
        font-size: 1.1rem;
        color: #4a5568;
        max-width: 640px;
        margin: 0 auto 36px auto;
        line-height: 1.7;
        text-align: center;
    }}
    .lp-hero-cta {{ display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }}
    .lp-btn-lg {{ padding: 13px 32px; font-size: 0.95rem; border-radius: 10px; }}

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
        padding: 52px 40px;
        text-align: center;
        margin: 56px 0 40px 0;
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
        margin: 0 0 28px 0;
    }}

    /* Footer */
    .lp-footer {{
        text-align: center;
        padding: 24px 0 32px 0;
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #a0aec0;
        border-top: 1px solid #e2e8f0;
    }}
</style>

<!-- Nav -->
<div class="lp-nav">
    <div class="lp-logo">stocklio<span class="lp-logo-dot">.</span></div>
    <div class="lp-nav-links">
        <form onsubmit="event.preventDefault();var t=this.ticker.value.trim().toUpperCase();if(t){{window.location.href='/Analyze?ticker='+encodeURIComponent(t);}}" style="display:inline-flex;gap:0;border:1px solid #cbd5e0;border-radius:8px;overflow:hidden;background:#fff;">
            <input name="ticker" placeholder="Get a stock forecast, e.g. AAPL" style="border:none;outline:none;padding:7px 14px;font-family:'Inter',sans-serif;font-size:0.85rem;width:220px;background:transparent;color:#1a202c;">
            <button type="submit" style="border:none;background:#00c896;color:#fff;padding:7px 14px;font-family:'Inter',sans-serif;font-size:0.85rem;font-weight:600;cursor:pointer;">→</button>
        </form>
        <a href="{_login_url}" class="lp-btn lp-btn-outline">Log in</a>
        <a href="{_signup_url}" class="lp-btn lp-btn-primary">Sign up free</a>
    </div>
</div>

<!-- Hero -->
<div class="lp-hero">
    <div class="lp-eyebrow">AI Forecast · Prediction Market · Technical Analysis</div>
    <h1 class="lp-h1">Know where the market is headed<br><span style="display:block;margin-top:-0.15em;">before it moves.</span></h1>
    <div style="display:flex;justify-content:center;width:100%;">
        <p class="lp-sub" style="text-align:center;max-width:640px;margin:4px auto 24px auto;">
            Stocklio combines AI analysis, technical signals, and market sentiment to help individual investors spot opportunities and make smarter trades.
        </p>
    </div>
    <div class="lp-hero-cta">
        <a href="/Analyze" class="lp-btn lp-btn-primary lp-btn-lg">Try Stocklio free</a>
        <a href="{_signup_url}" class="lp-btn lp-btn-outline lp-btn-lg">Create an account</a>
    </div>
</div>

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

<!-- CTA Band -->
<div class="lp-cta-band">
    <h2>Stop guessing. Start analyzing.</h2>
    <p>Free to use. No credit card required.</p>
    <form onsubmit="event.preventDefault();var t=this.ticker.value.trim().toUpperCase();if(t){{window.location.href='/Analyze?ticker='+encodeURIComponent(t);}}" style="display:inline-flex;gap:0;border:1px solid #4a5568;border-radius:10px;overflow:hidden;background:#2d3748;margin-bottom:12px;">
        <input name="ticker" placeholder="Enter a ticker to get your forecast, e.g. NVDA" style="border:none;outline:none;padding:13px 20px;font-family:'Inter',sans-serif;font-size:0.95rem;width:320px;background:transparent;color:#ffffff;">
        <button type="submit" style="border:none;background:#00c896;color:#fff;padding:13px 24px;font-family:'Inter',sans-serif;font-size:0.95rem;font-weight:600;cursor:pointer;white-space:nowrap;">Get Forecast →</button>
    </form>
    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
        <a href="{_signup_url}" class="lp-btn lp-btn-outline lp-btn-lg">Create an account</a>
    </div>
</div>

<!-- Footer -->
<div class="lp-footer">
    © 2025 Stocklio · Built for investors who want an edge.
</div>
""", unsafe_allow_html=True)
