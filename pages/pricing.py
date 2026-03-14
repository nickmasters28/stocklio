"""
pages/pricing.py -- Stocklio pricing page (/pricing)
"""

import streamlit as st
from auth.propelauth import login_url, signup_url, is_paid_user

st.markdown(
    "<style>"
    "[data-testid='stSidebarNav'],"
    "[data-testid='stSidebarNavItems'],"
    "[data-testid='stSidebarNavSeparator']"
    "{display:none!important;}"
    "</style>",
    unsafe_allow_html=True,
)

_login_url    = login_url()
_signup_url   = signup_url()
_is_logged_in = st.session_state.get("logged_in", False)
_is_pro       = is_paid_user()

# Pre-compute nav and CTA strings so no expressions inside the f-string
if _is_logged_in:
    _nav_links = (
        '<a href="/blog" class="lp-btn lp-btn-outline">Blog</a>'
        '<a href="/pricing" class="lp-btn lp-btn-outline">Pricing</a>'
        '<a href="https://auth.stocklio.ai/account" class="lp-btn lp-btn-outline">My Account</a>'
        '<a href="/analyze?ticker=AAPL" class="lp-btn lp-btn-primary">Open Dashboard</a>'
    )
else:
    _nav_links = (
        f'<a href="/blog" class="lp-btn lp-btn-outline">Blog</a>'
        f'<a href="/pricing" class="lp-btn lp-btn-outline">Pricing</a>'
        f'<a href="{_login_url}" target="_self" class="lp-btn lp-btn-outline">Log in</a>'
        f'<a href="{_signup_url}" target="_self" class="lp-btn lp-btn-primary">Sign up free</a>'
    )

if _is_logged_in and not _is_pro:
    _free_cta = "<span class='pricing-cta pricing-cta-current'>Your current plan</span>"
else:
    _free_cta = f"<a href='{_signup_url}' target='_self' class='pricing-cta pricing-cta-free'>Get started free</a>"

if _is_pro:
    _pro_cta = "<span class='pricing-cta pricing-cta-current'>&#10003; You're on Pro</span>"
else:
    _pro_cta = "<a href='https://buy.stripe.com/bJe00j3tg8ug65kaIBenS00' target='_blank' class='pricing-cta pricing-cta-pro'>Upgrade to Pro &rarr;</a>"

st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Darker+Grotesque:wght@700;800;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    .stApp {{ background-color: #f5f7fa; }}
    .block-container {{
        padding-top: 1rem !important;
        padding-bottom: 0 !important;
        max-width: 1100px;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }}
    section[data-testid="stSidebar"] {{ display: none !important; }}
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarHeader"] > button,
    button[aria-label*="keyboard" i],
    button[title*="keyboard" i],
    [data-testid="stToolbar"],
    [data-testid="stHeaderActionElements"] {{ display: none !important; }}

    .lp-nav {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 20px 0 16px 0;
        border-bottom: 1px solid #e2e8f0;
    }}
    .lp-logo {{
        font-family: 'Darker Grotesque', sans-serif;
        font-size: 2.4rem;
        font-weight: 800;
        color: #1a202c !important;
        letter-spacing: -0.01em;
        line-height: 1;
        text-decoration: none !important;
    }}
    .lp-logo-dot {{ color: #00c896 !important; }}
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
    .lp-btn-outline {{ border: 1px solid #cbd5e0; color: #1a202c !important; background: #ffffff; }}
    .lp-btn-primary {{ background: #00c896; color: #ffffff !important; border: 1px solid #00c896; }}

    .pricing-hero {{
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        padding: 64px 0 48px 0;
    }}
    .pricing-eyebrow {{
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
    .pricing-h1 {{
        font-family: 'Darker Grotesque', sans-serif;
        font-size: 3.8rem;
        font-weight: 900;
        color: #1a202c;
        line-height: 1.05;
        letter-spacing: -0.02em;
        margin: 0 0 16px 0;
        text-align: center;
        width: 100%;
    }}
    .pricing-sub {{
        font-family: 'Inter', sans-serif;
        font-size: 1.05rem;
        color: #4a5568;
        white-space: nowrap;
        margin: 0 auto;
        line-height: 1.7;
        text-align: center;
    }}
    .pricing-grid {{
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 24px;
        max-width: 860px;
        margin: 0 auto 64px auto;
    }}
    .pricing-card {{
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 36px 32px 32px 32px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        position: relative;
        display: flex;
        flex-direction: column;
    }}
    .pricing-card-pro {{
        border: 2px solid #00c896;
        box-shadow: 0 4px 24px rgba(0,200,150,0.12);
    }}
    .pricing-badge {{
        position: absolute;
        top: -13px;
        left: 50%;
        transform: translateX(-50%);
        background: #00c896;
        color: #ffffff;
        font-family: 'Inter', sans-serif;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        padding: 4px 16px;
        border-radius: 20px;
        white-space: nowrap;
    }}
    .pricing-tier {{
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #6b7280;
        margin-bottom: 8px;
    }}
    .pricing-tier-pro {{ color: #00a878; }}
    .pricing-price {{
        font-family: 'Darker Grotesque', sans-serif;
        font-size: 3.2rem;
        font-weight: 900;
        color: #1a202c;
        line-height: 1;
        margin-bottom: 4px;
    }}
    .pricing-period {{
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        color: #a0aec0;
        margin-bottom: 20px;
    }}
    .pricing-desc {{
        font-family: 'Inter', sans-serif;
        font-size: 0.88rem;
        color: #4a5568;
        line-height: 1.6;
        margin-bottom: 24px;
        padding-bottom: 24px;
        border-bottom: 1px solid #e2e8f0;
    }}
    .pricing-features {{
        list-style: none;
        padding: 0;
        margin: 0 0 32px 0;
        flex: 1;
    }}
    .pricing-features li {{
        font-family: 'Inter', sans-serif;
        font-size: 0.88rem;
        color: #1a202c;
        padding: 7px 0;
        display: flex;
        align-items: flex-start;
        gap: 10px;
        border-bottom: 1px solid #f0f4f8;
    }}
    .pricing-features li:last-child {{ border-bottom: none; }}
    .feat-icon {{ flex-shrink: 0; margin-top: 1px; font-size: 0.95rem; }}
    .feat-label {{ flex: 1; }}
    .feat-muted {{ color: #a0aec0; }}
    .feat-soon {{
        display: inline-block;
        background: #fef3c7;
        color: #92400e;
        font-size: 0.68rem;
        font-weight: 600;
        padding: 1px 7px;
        border-radius: 10px;
        margin-left: 6px;
        vertical-align: middle;
        letter-spacing: 0.02em;
    }}
    .pricing-section-label {{
        font-family: 'Inter', sans-serif;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        color: #a0aec0;
        padding: 12px 0 4px 0;
        border-bottom: none !important;
    }}
    .pricing-cta {{
        display: block;
        width: 100%;
        text-align: center;
        padding: 12px 0;
        border-radius: 10px;
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        text-decoration: none !important;
        box-sizing: border-box;
    }}
    .pricing-cta-free {{
        background: #f5f7fa;
        color: #1a202c !important;
        border: 1px solid #e2e8f0;
    }}
    .pricing-cta-pro {{
        background: #00c896;
        color: #ffffff !important;
        border: 1px solid #00c896;
    }}
    .pricing-cta-current {{
        background: #e6faf5;
        color: #00a878 !important;
        border: 1px solid #00c896;
        cursor: default;
    }}
    .lp-footer {{
        padding: 32px 0 36px 0;
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #a0aec0;
        border-top: 1px solid #e2e8f0;
        margin-top: 48px;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }}
    .lp-footer-copy {{ color: #a0aec0; }}
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
        color: #a0aec0 !important;
        text-decoration: none !important;
        margin-bottom: 4px;
    }}
    .lp-footer-link:hover {{ color: #4a5568 !important; }}
</style>

<div class="lp-nav">
    <a href="/" class="lp-logo" target="_self">stocklio<span class="lp-logo-dot">.</span></a>
    <div class="lp-nav-links">{_nav_links}</div>
</div>

<div class="pricing-hero">
    <div class="pricing-eyebrow">Pricing</div>
    <div class="pricing-h1">Simple, transparent pricing</div>
    <p class="pricing-sub">Start free with powerful technical analysis. Upgrade to Pro for institutional-grade intelligence.</p>
</div>

<div class="pricing-grid">
    <div class="pricing-card">
        <div class="pricing-tier">Free</div>
        <div class="pricing-price">$0</div>
        <div class="pricing-period">forever</div>
        <div class="pricing-desc">Full access to core technical analysis tools. No credit card required.</div>
        <ul class="pricing-features">
            <li><div class="pricing-section-label" style="padding-top:0;">Technical Analysis</div></li>
            <li><span class="feat-icon">&#10003;</span><span class="feat-label">Stocklio Forecast Score</span></li>
            <li><span class="feat-icon">&#10003;</span><span class="feat-label">Ride the Nine &mdash; 9 EMA Strategy</span></li>
            <li><span class="feat-icon">&#10003;</span><span class="feat-label">Signal Breakdown Table</span></li>
            <li><span class="feat-icon">&#10003;</span><span class="feat-label">Support &amp; Resistance Levels</span></li>
            <li><span class="feat-icon">&#10003;</span><span class="feat-label">Linear Regression Trend Projection</span></li>
            <li><span class="feat-icon">&#10003;</span><span class="feat-label">Interactive Technical Chart</span></li>
            <li><div class="pricing-section-label">Community</div></li>
            <li><span class="feat-icon">&#10003;</span><span class="feat-label">Community Prediction Market</span></li>
            <li><div class="pricing-section-label">Pro Intel</div></li>
            <li><span class="feat-icon feat-muted">&mdash;</span><span class="feat-label feat-muted">Analyst Recommendations</span></li>
            <li><span class="feat-icon feat-muted">&mdash;</span><span class="feat-label feat-muted">Price Target</span></li>
            <li><span class="feat-icon feat-muted">&mdash;</span><span class="feat-label feat-muted">Insider Sentiment Score</span></li>
            <li><span class="feat-icon feat-muted">&mdash;</span><span class="feat-label feat-muted">Congressional Trading Alerts</span></li>
            <li><span class="feat-icon feat-muted">&mdash;</span><span class="feat-label feat-muted">SEC Filing Sentiment</span></li>
            <li><span class="feat-icon feat-muted">&mdash;</span><span class="feat-label feat-muted">Stocklio Copilot</span></li>
        </ul>
        {_free_cta}
    </div>
    <div class="pricing-card pricing-card-pro">
        <div class="pricing-badge">Most Popular</div>
        <div class="pricing-tier pricing-tier-pro">Pro</div>
        <div class="pricing-price">$9<span style="font-size:1.4rem;font-weight:600;color:#6b7280;">/mo</span></div>
        <div class="pricing-period">billed monthly</div>
        <div class="pricing-desc">Everything in Free, plus Wall Street-grade intelligence to stay ahead of the market.</div>
        <ul class="pricing-features">
            <li><div class="pricing-section-label" style="padding-top:0;">Technical Analysis</div></li>
            <li><span class="feat-icon">&#10003;</span><span class="feat-label">Everything in Free</span></li>
            <li><div class="pricing-section-label">Pro Intel</div></li>
            <li><span class="feat-icon">&#10003;</span><span class="feat-label">Analyst Recommendations</span></li>
            <li><span class="feat-icon">&#10003;</span><span class="feat-label">Price Target</span></li>
            <li><span class="feat-icon">&#10003;</span><span class="feat-label">Insider Sentiment Score</span></li>
            <li><span class="feat-icon">&#10003;</span><span class="feat-label">Congressional Trading Alerts</span></li>
            <li><span class="feat-icon">&#10003;</span><span class="feat-label">SEC Filing Sentiment</span></li>
            <li><span class="feat-icon">&#10003;</span><span class="feat-label">Stocklio Copilot <span class="feat-soon">Coming Soon</span></span></li>
        </ul>
        {_pro_cta}
    </div>
</div>

<div class="lp-footer" style="flex-direction:column;gap:16px;">
    <div style="display:flex;justify-content:flex-end;width:100%;">
        <div>
            <div class="lp-footer-section-title">Resources</div>
            <a href="/blog" class="lp-footer-link">Blog</a>
            <a href="/pricing" class="lp-footer-link">Pricing</a>
            <a href="{_signup_url}" target="_self" class="lp-footer-link">Create an account</a>
            <a href="{_login_url}" target="_self" class="lp-footer-link">Log in</a>
            <a href="mailto:hello@stocklio.ai" class="lp-footer-link">hello@stocklio.ai</a>
        </div>
    </div>
    <div class="lp-footer-copy">&copy; 2025 Stocklio &middot; Built for investors who want an edge.</div>
</div>
""", unsafe_allow_html=True)
