"""
pages/faq.py -- Stocklio FAQ page (/faq)

Structured FAQ content with JSON-LD FAQPage schema for LLM and search crawler indexing.
"""

import streamlit as st
from auth.propelauth import login_url, signup_url

st.markdown(
    "<style>"
    "[data-testid='stSidebarNav'],"
    "[data-testid='stSidebarNavItems'],"
    "[data-testid='stSidebarNavSeparator']"
    "{display:none!important;}"
    "</style>",
    unsafe_allow_html=True,
)

_login_url  = login_url()
_signup_url = signup_url()
_is_logged_in = st.session_state.get("logged_in", False)

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
        f'<a href="/pricing" target="_self" class="lp-btn lp-btn-outline">Pricing</a>'
        f'<a href="{_login_url}" target="_self" class="lp-btn lp-btn-outline">Log in</a>'
        f'<a href="{_signup_url}" target="_self" class="lp-btn lp-btn-primary">Sign up free</a>'
    )

# ---------------------------------------------------------------------------
# FAQ data — drives both the rendered UI and the JSON-LD schema
# ---------------------------------------------------------------------------

FAQS = [
    {
        "category": "About Stocklio",
        "items": [
            {
                "q": "What is Stocklio?",
                "a": (
                    "Stocklio is an AI-powered stock analysis platform built for individual investors. "
                    "It combines technical indicator analysis, AI composite scoring, community prediction markets, "
                    "and an AI chat assistant (Stocklio Copilot) into a single dashboard. Stocklio is available "
                    "at app.stocklio.ai and is free to start with no credit card required."
                ),
            },
            {
                "q": "What does Stocklio do?",
                "a": (
                    "Stocklio analyzes any publicly traded stock and delivers a multi-layer intelligence report. "
                    "It calculates over 10 technical indicators — including RSI, MACD, Bollinger Bands, EMA, SMA, "
                    "and volume momentum — then synthesizes them into a single AI composite score with a directional "
                    "forecast. It also shows where community members think the stock is headed, displays analyst "
                    "ratings and price targets, surfaces recent SEC filings and congress trades, and lets Pro "
                    "members ask follow-up questions via Stocklio Copilot."
                ),
            },
            {
                "q": "Who is Stocklio built for?",
                "a": (
                    "Stocklio is built for self-directed retail investors who want professional-grade analysis "
                    "without paying for a Bloomberg terminal or hiring a financial advisor. It's especially useful "
                    "for active traders who follow technical analysis, swing traders looking for entry and exit "
                    "signals, and long-term investors who want a quick second opinion before buying or selling a position."
                ),
            },
            {
                "q": "Is Stocklio free to use?",
                "a": (
                    "Yes. Stocklio has a free tier that includes full technical analysis, the AI composite score, "
                    "the community prediction market, analyst ratings, and recent news for any ticker. "
                    "Stocklio Pro ($9.99/month) unlocks Stocklio Copilot, an AI chat assistant that can answer "
                    "follow-up questions about any stock, as well as additional data layers and priority features."
                ),
            },
            {
                "q": "What makes Stocklio different from other stock analysis tools?",
                "a": (
                    "Most stock screeners give you raw data and leave interpretation to you. Stocklio synthesizes "
                    "that data into a single composite score with a plain-English directional signal. "
                    "It also layers in community sentiment via a prediction market, so you can see whether the "
                    "crowd agrees with the AI. And with Stocklio Copilot, Pro users can ask natural-language "
                    "questions about any stock and get instant, conversational answers — something traditional "
                    "charting tools don't offer."
                ),
            },
            {
                "q": "How is Stocklio different from TradingView?",
                "a": (
                    "TradingView is a powerful charting platform built for experienced technical analysts who "
                    "want to draw their own trendlines, write custom Pine Script indicators, and manage complex "
                    "watchlists. Stocklio takes a different approach: it does the analysis for you and surfaces "
                    "a clear signal. Think of TradingView as a blank canvas and Stocklio as an AI analyst "
                    "sitting beside you, already having done the work."
                ),
            },
        ],
    },
    {
        "category": "Features & How It Works",
        "items": [
            {
                "q": "What technical indicators does Stocklio analyze?",
                "a": (
                    "Stocklio analyzes more than 10 technical indicators including: RSI (Relative Strength Index), "
                    "MACD (Moving Average Convergence Divergence), Bollinger Bands, 9 EMA and 20 EMA, 50 SMA and "
                    "200 SMA, volume momentum, ATR (Average True Range), On-Balance Volume (OBV), and Williams %R. "
                    "Each indicator is scored individually, and Stocklio combines them into a weighted composite "
                    "score that reflects the stock's overall technical picture."
                ),
            },
            {
                "q": "What is the Stocklio AI composite score?",
                "a": (
                    "The Stocklio AI composite score is a single number from 0 to 100 that reflects the overall "
                    "technical strength of a stock at a given moment. A score above 60 is generally bullish, "
                    "below 40 is bearish, and 40–60 is neutral. It is calculated by weighting multiple technical "
                    "indicators and normalizing them into a unified signal. The score updates whenever you run "
                    "a new analysis."
                ),
            },
            {
                "q": "What is Ride the Nine?",
                "a": (
                    "Ride the Nine is a trading strategy built around the 9-period Exponential Moving Average (9 EMA). "
                    "Professional traders use the 9 EMA as a dynamic support and resistance line. When a stock "
                    "is in a strong uptrend, price tends to 'ride' just above the 9 EMA, pulling back to it "
                    "and bouncing. Stocklio visualizes this strategy on its chart and signals when the stock "
                    "is in a confirmed 9 EMA setup, including entry zones and potential exit signals when price "
                    "breaks below."
                ),
            },
            {
                "q": "What is Stocklio's prediction market?",
                "a": (
                    "Stocklio's prediction market is a community-driven sentiment signal. Registered users can "
                    "vote on whether they think a stock will be higher or lower over a defined time period. "
                    "The platform tracks vote accuracy over the trailing 90 days, so you can see not just "
                    "what the crowd thinks, but how reliable the crowd has been. This gives the sentiment "
                    "signal real accountability — unlike most social media stock polls."
                ),
            },
            {
                "q": "What stocks can I analyze with Stocklio?",
                "a": (
                    "Stocklio supports any publicly traded U.S. equity with a standard ticker symbol — "
                    "large caps like Apple (AAPL), Microsoft (MSFT), and NVIDIA (NVDA), mid and small caps, "
                    "and ETFs. You can analyze any stock by entering its ticker symbol into the search bar "
                    "on the dashboard. International stocks and crypto are not currently supported."
                ),
            },
            {
                "q": "What is Analyst Intel on Stocklio?",
                "a": (
                    "Analyst Intel is a Pro feature that shows the consensus analyst rating (Buy, Hold, Sell) "
                    "and the 12-month price target range from Wall Street analysts. It also displays the most "
                    "recent analyst upgrades and downgrades, giving you a quick read on how institutional "
                    "sentiment is shifting. This data complements Stocklio's own technical signals to give "
                    "you both the street view and the chart view in one place."
                ),
            },
            {
                "q": "Does Stocklio show news for stocks?",
                "a": (
                    "Yes. Stocklio surfaces recent news headlines for any stock you analyze. Stories are "
                    "pulled from financial news sources and displayed alongside the technical data so you "
                    "can quickly cross-reference a price move with relevant news events without leaving the dashboard."
                ),
            },
            {
                "q": "Does Stocklio track congress stock trades?",
                "a": (
                    "Yes. Stocklio includes a Congress Trades section that surfaces recent stock disclosures "
                    "filed by U.S. senators and representatives under the STOCK Act. Seeing which stocks elected "
                    "officials are buying or selling can be a useful data point alongside your technical analysis."
                ),
            },
            {
                "q": "Does Stocklio show SEC filings?",
                "a": (
                    "Yes. Stocklio pulls recent SEC filings for any analyzed stock, including 8-K current "
                    "reports, 10-Q quarterly earnings, and other material disclosures. This lets you spot "
                    "significant corporate events — earnings misses, leadership changes, material agreements — "
                    "that may be driving price action."
                ),
            },
        ],
    },
    {
        "category": "Stocklio Copilot",
        "items": [
            {
                "q": "What is Stocklio Copilot?",
                "a": (
                    "Stocklio Copilot is an AI chat assistant available to Pro subscribers. It lets you ask "
                    "natural-language questions about any stock — 'Why is NVDA pulling back?', 'What does the "
                    "MACD crossover mean for TSLA?', 'Is this a good entry point for AAPL?' — and get a "
                    "conversational, jargon-free answer. Copilot understands the context of the stock you're "
                    "analyzing and draws on technical analysis principles to give relevant, specific responses."
                ),
            },
            {
                "q": "How do I access Stocklio Copilot?",
                "a": (
                    "Stocklio Copilot is available to Stocklio Pro subscribers. Once you're on Pro, you'll "
                    "see an 'Ask Copilot' button in the header of every stock analysis page. Click it and "
                    "you'll be taken to a dedicated chat interface pre-loaded with the ticker you were just "
                    "analyzing. You can also access Copilot directly at app.stocklio.ai/copilot."
                ),
            },
            {
                "q": "Is Stocklio Copilot a financial advisor?",
                "a": (
                    "No. Stocklio Copilot is an AI assistant that explains technical analysis concepts and "
                    "helps you interpret market data — it is not a licensed financial advisor and does not "
                    "provide personalized investment advice. All analysis on Stocklio, including Copilot "
                    "responses, is for informational and educational purposes only."
                ),
            },
        ],
    },
    {
        "category": "Plans & Pricing",
        "items": [
            {
                "q": "How much does Stocklio cost?",
                "a": (
                    "Stocklio Free is $0 per month with no credit card required. It includes full technical "
                    "analysis for any stock, the AI composite score, the community prediction market, "
                    "analyst ratings, news, and more. Stocklio Pro is $9.99 per month and adds Stocklio "
                    "Copilot (AI chat), additional data layers, and priority access to new features."
                ),
            },
            {
                "q": "What is included in the Stocklio free plan?",
                "a": (
                    "The free plan includes: full technical analysis dashboard for any U.S. stock, AI composite "
                    "score with directional forecast, 10+ technical indicators (RSI, MACD, Bollinger Bands, "
                    "EMA, SMA, and more), the Ride the Nine chart strategy view, community prediction market, "
                    "analyst ratings and price targets, recent stock news, SEC filings, and Congress trades. "
                    "There is no time limit on the free plan."
                ),
            },
            {
                "q": "What does Stocklio Pro include?",
                "a": (
                    "Stocklio Pro ($9.99/month) includes everything in the free plan plus: Stocklio Copilot "
                    "(unlimited AI chat about any stock), advanced analyst intelligence, and early access to "
                    "new Pro-only features as they launch. Pro is billed monthly and can be cancelled any time."
                ),
            },
            {
                "q": "Can I cancel my Stocklio Pro subscription?",
                "a": (
                    "Yes. Stocklio Pro is a monthly subscription with no long-term commitment. You can cancel "
                    "at any time. If you have questions about your billing, email hello@stocklio.ai and the "
                    "team will sort it out promptly."
                ),
            },
            {
                "q": "Is there a free trial for Stocklio Pro?",
                "a": (
                    "Stocklio's free tier is fully functional and unlimited — it's not a time-restricted trial. "
                    "You can use all core analysis features at no cost for as long as you want. Stocklio Pro "
                    "unlocks additional capabilities like Copilot for users who want the full AI-powered experience."
                ),
            },
        ],
    },
    {
        "category": "Accuracy & Limitations",
        "items": [
            {
                "q": "How accurate are Stocklio's AI forecasts?",
                "a": (
                    "Stocklio's AI composite score and directional signals are based on technical analysis — "
                    "a methodology used by professional traders for decades. Like all technical analysis, "
                    "the signals are probabilistic, not predictive. They reflect historical price patterns "
                    "and momentum, and they are most reliable in trending markets. No analysis tool — including "
                    "Stocklio — can guarantee future stock performance. Always treat any forecast as one "
                    "input among many."
                ),
            },
            {
                "q": "Does Stocklio give buy or sell recommendations?",
                "a": (
                    "Stocklio provides technical signals and analysis that indicate whether a stock's "
                    "technical picture is bullish, bearish, or neutral. These are not formal buy or sell "
                    "recommendations. Stocklio is an analytical tool, not an investment advisor. All "
                    "investment decisions should be made based on your own research, risk tolerance, and "
                    "if appropriate, consultation with a licensed financial professional."
                ),
            },
            {
                "q": "Is Stocklio suitable for day trading?",
                "a": (
                    "Stocklio's analysis is most useful for swing traders and position traders working on "
                    "daily timeframes. The default analysis uses end-of-day price data and is best suited "
                    "for decisions made on a 1-day to multi-week horizon. Day traders who need tick-level "
                    "data or real-time intraday charts should use a dedicated intraday platform alongside "
                    "Stocklio for broader context."
                ),
            },
            {
                "q": "Does Stocklio work on mobile?",
                "a": (
                    "Stocklio is a web application that runs in any modern browser. It is accessible on "
                    "mobile devices, though the dashboard is optimized for desktop screens where charts "
                    "and data tables display best. A dedicated mobile app is on the product roadmap."
                ),
            },
        ],
    },
    {
        "category": "Account & Access",
        "items": [
            {
                "q": "Do I need an account to use Stocklio?",
                "a": (
                    "You can browse and analyze stocks on Stocklio without creating an account. Creating a "
                    "free account unlocks additional features including recent search history, the ability "
                    "to vote in the prediction market, and access to Stocklio Pro if you choose to upgrade."
                ),
            },
            {
                "q": "How do I sign up for Stocklio?",
                "a": (
                    "Go to app.stocklio.ai, click 'Sign up free', and create an account using your email "
                    "address. No credit card is required. You can start analyzing stocks immediately after "
                    "signing up."
                ),
            },
            {
                "q": "How do I contact Stocklio support?",
                "a": (
                    "Email hello@stocklio.ai for any questions about your account, billing, or technical "
                    "issues. The team typically responds within one business day."
                ),
            },
        ],
    },
]

# ---------------------------------------------------------------------------
# Build JSON-LD FAQPage schema (critical for LLM and Google indexing)
# ---------------------------------------------------------------------------

import json

_schema_items = []
for _section in FAQS:
    for _item in _section["items"]:
        _schema_items.append({
            "@type": "Question",
            "name": _item["q"],
            "acceptedAnswer": {
                "@type": "Answer",
                "text": _item["a"],
            },
        })

_json_ld = json.dumps({
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "name": "Stocklio FAQ — AI Stock Analysis Questions & Answers",
    "description": (
        "Frequently asked questions about Stocklio, the AI-powered stock analysis platform. "
        "Learn about features, pricing, technical indicators, Stocklio Copilot, and more."
    ),
    "mainEntity": _schema_items,
}, ensure_ascii=False)

# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Darker+Grotesque:wght@700;800;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

<script type="application/ld+json">{_json_ld}</script>

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
        font-size: 6rem;
        font-weight: 800;
        color: #000000 !important;
        letter-spacing: -0.01em;
        line-height: 1;
        text-decoration: none !important;
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
    .lp-btn-primary {{ background: #00c896; color: #ffffff !important; border: 1px solid #00c896; }}

    /* Page hero */
    .faq-hero {{
        text-align: center;
        padding: 52px 0 44px 0;
    }}
    .faq-eyebrow {{
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
        margin-bottom: 18px;
    }}
    .faq-h1 {{
        font-family: 'Darker Grotesque', sans-serif;
        font-size: 3rem;
        font-weight: 900;
        color: #1a202c;
        letter-spacing: -0.02em;
        margin: 0 0 12px 0;
        line-height: 1.05;
    }}
    .faq-sub {{
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        color: #6b7280;
        max-width: 520px;
        margin: 0 auto;
        line-height: 1.65;
    }}

    /* Category label */
    .faq-category {{
        font-family: 'Inter', sans-serif;
        font-size: 0.72rem;
        font-weight: 700;
        color: #00a878;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 48px 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #e6faf5;
    }}

    /* FAQ accordion — native <details>/<summary>, no JS needed */
    details.faq-item {{
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        margin-bottom: 8px;
        overflow: hidden;
        list-style: none;
    }}
    details.faq-item summary {{
        font-family: 'Darker Grotesque', sans-serif;
        font-size: 1.1rem;
        font-weight: 800;
        color: #1a202c;
        padding: 18px 22px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        line-height: 1.3;
        list-style: none;
        user-select: none;
    }}
    details.faq-item summary::-webkit-details-marker {{ display: none; }}
    details.faq-item summary::marker {{ display: none; }}
    details.faq-item summary:hover {{ background: #f5f7fa; }}
    details.faq-item[open] summary {{ background: #f9fffe; }}
    .faq-chevron {{
        font-size: 0.85rem;
        color: #00c896;
        flex-shrink: 0;
        transition: transform 0.2s;
        display: inline-block;
    }}
    details.faq-item[open] .faq-chevron {{ transform: rotate(180deg); }}
    .faq-a {{
        font-family: 'Inter', sans-serif;
        font-size: 0.93rem;
        color: #4a5568;
        line-height: 1.7;
        padding: 16px 22px 20px 22px;
        border-top: 1px solid #f0f4f8;
    }}

    /* CTA band */
    .faq-cta {{
        background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
        border-radius: 16px;
        padding: 44px 40px;
        text-align: center;
        margin: 56px 0 0 0;
    }}
    .faq-cta h2 {{
        font-family: 'Darker Grotesque', sans-serif;
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff !important;
        margin: 0 0 10px 0;
        letter-spacing: -0.01em;
    }}
    .faq-cta p {{
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        color: #a0aec0;
        margin: 0 0 24px 0;
    }}
    .faq-cta-btn {{
        display: inline-block;
        background: #00c896;
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
        font-size: 0.95rem;
        font-weight: 600;
        padding: 13px 36px;
        border-radius: 10px;
        text-decoration: none !important;
    }}
    .faq-cta-btn:hover {{ background: #00b386; }}

    /* Footer */
    .lp-footer {{
        padding: 32px 0 36px 0;
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #a0aec0;
        border-top: 1px solid #e2e8f0;
        margin-top: 40px;
    }}
    .lp-footer-link {{
        color: #a0aec0;
        text-decoration: none !important;
    }}
    .lp-footer-link:hover {{ color: #4a5568; }}
</style>

<!-- Nav -->
<div class="lp-nav">
    <a href="/" class="lp-logo" target="_self">stocklio<span class="lp-logo-dot">.</span></a>
    <div class="lp-nav-links">{_nav_links}</div>
</div>

<!-- Hero -->
<div class="faq-hero">
    <div class="faq-eyebrow">Help &amp; FAQ</div>
    <h1 class="faq-h1">Frequently Asked Questions</h1>
    <p class="faq-sub">
        Everything you need to know about Stocklio — how it works, what's included,
        and how to get the most out of it.
    </p>
</div>
""", unsafe_allow_html=True)

# Render FAQ sections
for _section in FAQS:
    _items_html = ""
    for _i, _item in enumerate(_section["items"]):
        _sid = f"faq-{_section['category'].lower().replace(' ', '-')}-{_i}"
        _items_html += f"""
<details class="faq-item" id="{_sid}">
    <summary>
        <span>{_item['q']}</span>
        <span class="faq-chevron">&#9660;</span>
    </summary>
    <div class="faq-a">{_item['a']}</div>
</details>"""

    st.markdown(
        f'<div class="faq-category">{_section["category"]}</div>{_items_html}',
        unsafe_allow_html=True,
    )

# CTA + footer
_cta_href = "/analyze?ticker=AAPL" if _is_logged_in else _signup_url
_cta_label = "Open Dashboard" if _is_logged_in else "Get started free →"

st.markdown(f"""
<div class="faq-cta">
    <h2>Still have questions?</h2>
    <p>Email us at hello@stocklio.ai — or just dive in and start analyzing.</p>
    <a href="{_cta_href}" target="_self" class="faq-cta-btn">{_cta_label}</a>
</div>

<div class="lp-footer" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
    <span>© 2025 Stocklio · Built for investors who want an edge.</span>
    <span>
        <a href="/privacy" class="lp-footer-link">Privacy Policy</a>
        &nbsp;·&nbsp;
        <a href="/terms" class="lp-footer-link">Terms of Service</a>
        &nbsp;·&nbsp;
        <a href="mailto:hello@stocklio.ai" class="lp-footer-link">hello@stocklio.ai</a>
    </span>
</div>
""", unsafe_allow_html=True)
