"""
ui/layout.py -- Renders the two main pages of the dashboard:
  - render_market_overview()  -> Market Overview tab
  - render_stock_analysis()   -> Individual Stock Analysis tab
"""

import html as _html
import time
from concurrent.futures import ThreadPoolExecutor
import streamlit as st
import pandas as pd
import numpy as np
from typing import Optional

from data.fetcher import fetch_ohlcv, fetch_info
from data.votes import cast_vote, resolve_outcomes, sentiment_summary, sentiment_over_time, accuracy_stats
from indicators.calculator import (
    calculate_indicators, find_support_resistance, linear_regression_projection,
)
from forecast.engine import score_symbol, analyze_ride_the_nine
from ui.charts import build_stock_chart, build_score_gauge, build_ride_the_nine_chart, build_sentiment_chart
from ui.ads import lazy_ad_slot, SLOT_ANALYZE_BELOW_RTN, SLOT_ANALYZE_BELOW_LR, SLOT_BOTTOM_LEADERBOARD


# ── Cached computation pipeline ───────────────────────────────────────────────
# All heavy computation is bundled into one @st.cache_data function keyed on
# (ticker, period).  Cache key is two strings — no DataFrame hashing overhead.
# On a cache hit (same ticker + period within TTL) this returns instantly.

@st.cache_data(ttl=1800, show_spinner=False)
def _compute_analysis(ticker: str, period: str):
    """Run the full indicator + forecast pipeline; result cached for 5 minutes."""
    df                  = fetch_ohlcv(ticker, period=period)   # hits its own cache
    df                  = calculate_indicators(df)
    support, resistance = find_support_resistance(df)
    regression          = linear_regression_projection(df["Close"])
    forecast            = score_symbol(df, ticker, support, resistance)
    rtn                 = analyze_ride_the_nine(df)
    return df, support, resistance, regression, forecast, rtn


# ── Loading experience ─────────────────────────────────────────────────────────

# CSS injected once per page load — prefixed with stkl- to avoid collisions
_LOADING_CSS = """
<style>
@keyframes stkl-scan {
  0%   { transform: translateX(-100%); }
  100% { transform: translateX(500%); }
}
@keyframes stkl-pulse {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.35; }
}
/* Overlay and status-widget rules — re-enable if restoring the loading card animation
[data-testid="stStatusWidget"] { display: none !important; }
*/
/* Full-viewport overlay — kept here for easy restoration */
.stkl-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: #f8fafc;
  z-index: 99999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.stkl-card {
  background: #ffffff; border-radius: 16px; padding: 32px 36px 26px 36px;
  border: 1px solid #e2e8f0; box-shadow: 0 2px 14px rgba(0,0,0,0.05);
  width: 100%; max-width: 480px;
}
.stkl-bar {
  height: 3px; background: #e2e8f0; border-radius: 3px;
  overflow: hidden; margin: 20px 0 24px 0; position: relative;
}
.stkl-bar::after {
  content: ''; position: absolute; top: 0; left: 0;
  height: 100%; width: 22%;
  background: linear-gradient(90deg, transparent, #00c896, transparent);
  animation: stkl-scan 1.5s ease-in-out infinite;
}
.stkl-step {
  display: flex; align-items: center; gap: 10px;
  padding: 6px 0; font-family: 'Inter', sans-serif; font-size: 0.88rem;
}
.stkl-done   { color: #00a878; }
.stkl-active { color: #1a202c; font-weight: 600; }
.stkl-wait   { color: #cbd5e0; }
.stkl-dot {
  width: 9px; height: 9px; background: #00c896; border-radius: 50%;
  display: inline-block; flex-shrink: 0;
  animation: stkl-pulse 1.1s ease-in-out infinite;
}
.stkl-insight {
  font-family: 'Inter', sans-serif; font-size: 0.82rem;
  color: #6b7280; line-height: 1.6;
  border-top: 1px solid #f0f4f8; margin-top: 20px; padding-top: 16px;
}
</style>
"""

_STEPS = [
    "Pulling live market data",
    "Scoring technical indicators",
    "Reading market sentiment",
    "Generating AI forecast",
    "Preparing your dashboard",
]

_INSIGHTS = [
    "Better decisions come from combining multiple signals, not relying on one chart pattern.",
    "Technical analysis is stronger when paired with sentiment data.",
    "Momentum matters more when multiple indicators agree.",
    "Sentiment can confirm or challenge what the chart is already telling you.",
]


def _loading_html(ticker: str, step: int) -> str:
    """Return the branded loading card HTML for the given pipeline step."""
    steps_html = ""
    for i, label in enumerate(_STEPS):
        if i < step:
            steps_html += (
                f'<div class="stkl-step stkl-done">'
                f'<span style="font-size:0.72rem;flex-shrink:0;">✓</span>{label}'
                f'</div>'
            )
        elif i == step:
            steps_html += (
                f'<div class="stkl-step stkl-active">'
                f'<span class="stkl-dot"></span>{label}'
                f'</div>'
            )
        else:
            steps_html += (
                f'<div class="stkl-step stkl-wait">'
                f'<span style="font-size:0.72rem;flex-shrink:0;color:#e2e8f0;">○</span>{label}'
                f'</div>'
            )

    insight = _INSIGHTS[step % len(_INSIGHTS)]

    return (
        f'<div class="stkl-overlay">'
        f'<div class="stkl-card">'
        # Header row: logo left, ticker right
        f'<div style="display:flex;align-items:baseline;justify-content:space-between;margin-bottom:2px;">'
        f'<div style="font-family:\'Darker Grotesque\',sans-serif;font-size:1.55rem;font-weight:800;'
        f'color:#1a202c;letter-spacing:-0.01em;">'
        f'stocklio<span style="color:#00c896;">.</span></div>'
        f'<div style="font-family:\'Inter\',sans-serif;font-size:0.82rem;color:#6b7280;">'
        f'Analyzing&nbsp;<span style="font-weight:700;color:#1a202c;letter-spacing:.04em;">{_html.escape(ticker)}</span>'
        f'</div>'
        f'</div>'
        # Animated scan bar
        f'<div class="stkl-bar"></div>'
        # Step list
        f'{steps_html}'
        # Educational insight
        f'<div class="stkl-insight">💡&nbsp; {insight}</div>'
        f'</div>'
        f'</div>'
    )


# ── Skeleton helpers ──────────────────────────────────────────────────────────

def _sk(h="14px", w="100%", r="5px", mb="9px", d="0s"):
    """Single animated skeleton block."""
    return (
        f'<div style="height:{h};width:{w};background:#edf0f4;border-radius:{r};'
        f'margin-bottom:{mb};animation:stkl-pulse 1.9s ease-in-out {d} infinite;"></div>'
    )

def _skel_header():
    return (
        '<div style="display:flex;align-items:center;padding:4px 0 8px 0;">'
        f'<div style="width:54px;height:54px;border-radius:10px;background:#edf0f4;'
        f'margin-right:16px;flex-shrink:0;animation:stkl-pulse 1.9s ease-in-out infinite;"></div>'
        '<div style="flex:1;">'
        + _sk("26px", "240px", "6px", "10px", "0.06s")
        + _sk("15px", "175px", "4px", "0",    "0.12s")
        + '</div>'
        '</div>'
    )

def _skel_two_col(h="190px", ratio_l=1, ratio_r=2.5):
    """Two-column skeleton mimicking gauge + card layouts."""
    fl = ratio_l / (ratio_l + ratio_r)
    fr = ratio_r / (ratio_l + ratio_r)
    return (
        f'<div style="display:flex;gap:20px;margin-top:6px;">'
        f'<div style="flex:{fl:.3f};height:{h};background:#edf0f4;border-radius:12px;'
        f'animation:stkl-pulse 1.9s ease-in-out 0.1s infinite;"></div>'
        f'<div style="flex:{fr:.3f};height:{h};background:#edf0f4;border-radius:12px;'
        f'animation:stkl-pulse 1.9s ease-in-out 0.22s infinite;"></div>'
        f'</div>'
    )

def _skel_rows(n=4, base_w=92):
    """Generic skeleton row list — simulates a table or list of signals."""
    rows = "".join(
        _sk("13px", f"{base_w - i * 5}%", "4px", "8px", f"{i * 0.09:.2f}s")
        for i in range(n)
    )
    return f'<div style="margin-top:6px;">{rows}</div>'

def _skel_chart():
    return (
        f'<div style="height:400px;background:#edf0f4;border-radius:12px;margin-top:8px;'
        f'animation:stkl-pulse 1.9s ease-in-out 0.3s infinite;"></div>'
    )

def _skel_section(title_w="180px", rows=3):
    """Section skeleton: fake subheader + row list."""
    return (
        _sk("18px", title_w, "5px", "14px")
        + _skel_rows(rows)
    )


# -- Helpers -------------------------------------------------------------------

def _colour_class(rating: str) -> str:
    return {"Bullish": "bullish", "Bearish": "bearish", "Neutral": "neutral"}.get(rating, "neutral")

def _badge(text: str, direction: str) -> str:
    css = {"bullish": "badge-bull", "bearish": "badge-bear", "neutral": "badge-neut"}.get(direction, "badge-neut")
    return f'<span class="signal-badge {css}">{text}</span>'

def _fmt_large(n) -> str:
    """Format large numbers as 1.2B / 345.6M etc."""
    if n is None:
        return "N/A"
    try:
        n = float(n)
        if n >= 1e12: return f"${n/1e12:.2f}T"
        if n >= 1e9:  return f"${n/1e9:.2f}B"
        if n >= 1e6:  return f"${n/1e6:.2f}M"
        return f"${n:,.0f}"
    except Exception:
        return "N/A"


# -- Community voting ----------------------------------------------------------

_BULL_CLR = "#00d4a4"
_BEAR_CLR = "#ff4b6e"


def _render_voting(ticker: str, current_price: float, tech_rating: str):
    """Predicta Vote — community prediction panel."""
    # resolve_outcomes reads/writes st.session_state so must stay on the main thread
    resolve_outcomes(ticker, current_price)

    # Parallelise the three read-only Supabase fetches — each is @st.cache_data
    # so thread-safe; on a warm cache all three return in <1 ms total.
    with ThreadPoolExecutor(max_workers=3) as _vpool:
        _f_acc  = _vpool.submit(accuracy_stats)
        _f_sent = _vpool.submit(sentiment_summary, ticker)
        _f_hist = _vpool.submit(sentiment_over_time, ticker)
        acc     = _f_acc.result()
        sent    = _f_sent.result()
        history = _f_hist.result()

    # -- Accuracy banner (global, last 90 days) --------------------------------
    if acc["resolved"] > 0:
        acc_colour = _BULL_CLR if (acc["accuracy"] or 0) >= 55 else _BEAR_CLR
        st.markdown(
            f'<div style="font-size:0.82rem;color:#4a5568;margin-bottom:8px;">'
            f'Stocklio community: '
            f'<b style="color:{acc_colour}">{acc["accuracy"]}% accurate</b>'
            f' over last 90 days'
            f' &nbsp;<span style="color:#6b7280;">({acc["correct"]} correct of {acc["resolved"]} resolved)</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.subheader("Prediction Market")

    col_l, col_r = st.columns([1, 2])
    sess_key = f"voted_{ticker}"

    with col_l:
        st.markdown(
            f'<p style="font-size:0.9rem;color:#4a5568;margin-bottom:12px;">'
            f'Where is <b>{ticker}</b> headed in the next 30 days?</p>',
            unsafe_allow_html=True,
        )
        if sess_key not in st.session_state:
            bc, rc = st.columns(2)
            with bc:
                if st.button("🟢 Bullish", key=f"vote_bull_{ticker}",
                             use_container_width=True, type="primary"):
                    cast_vote(ticker, "bullish", current_price, tech_rating)
                    sentiment_summary.clear()
                    sentiment_over_time.clear()
                    st.session_state[sess_key] = "bullish"
                    st.rerun()
            with rc:
                if st.button("🔴 Bearish", key=f"vote_bear_{ticker}",
                             use_container_width=True):
                    cast_vote(ticker, "bearish", current_price, tech_rating)
                    sentiment_summary.clear()
                    sentiment_over_time.clear()
                    st.session_state[sess_key] = "bearish"
                    st.rerun()
        else:
            voted  = st.session_state[sess_key]
            colour = _BULL_CLR if voted == "bullish" else _BEAR_CLR
            bg     = "rgba(0,212,164,0.08)" if voted == "bullish" else "rgba(255,75,110,0.08)"
            label  = "🟢 Bullish" if voted == "bullish" else "🔴 Bearish"
            st.markdown(
                f'<div style="background:{bg};border:1px solid {colour};border-radius:8px;'
                f'padding:10px 14px;color:{colour};font-weight:700;font-size:0.95rem;">'
                f'{label} — vote recorded</div>',
                unsafe_allow_html=True,
            )

    with col_r:
        if sent["total"] > 0:
            bull_w = max(1.0, sent["bull_pct"])
            bear_w = max(1.0, sent["bear_pct"])
            st.markdown(f"""
            <div style="margin-bottom:6px;">
                <span style="color:{_BULL_CLR};font-weight:700;">{sent['bull_pct']:.0f}% Bullish</span>
                &nbsp;·&nbsp;
                <span style="color:{_BEAR_CLR};font-weight:700;">{sent['bear_pct']:.0f}% Bearish</span>
                &nbsp;
                <span style="color:#6b7280;font-size:0.82rem;">({sent['total']} vote{'s' if sent['total'] != 1 else ''})</span>
            </div>
            <div style="display:flex;border-radius:6px;overflow:hidden;height:14px;background:#e2e8f0;">
                <div style="width:{bull_w}%;background:{_BULL_CLR};"></div>
                <div style="width:{bear_w}%;background:{_BEAR_CLR};"></div>
            </div>
            """, unsafe_allow_html=True)

            crowd        = "Bullish" if sent["bull_pct"] > 50 else ("Bearish" if sent["bear_pct"] > 50 else "Neutral")
            crowd_colour = _BULL_CLR if crowd == "Bullish" else (_BEAR_CLR if crowd == "Bearish" else "#dd6b20")
            tech_colour  = _BULL_CLR if tech_rating == "Bullish" else (_BEAR_CLR if tech_rating == "Bearish" else "#dd6b20")
            agree        = crowd == tech_rating
            agree_colour = _BULL_CLR if agree else _BEAR_CLR
            agree_label  = "✓ Crowd agrees with forecast" if agree else "✗ Crowd disagrees with forecast"
            st.markdown(
                f'<div style="margin-top:10px;font-size:0.82rem;color:#4a5568;">'
                f'Crowd: <b style="color:{crowd_colour}">{crowd}</b>'
                f'&nbsp;&nbsp;·&nbsp;&nbsp;App: <b style="color:{tech_colour}">{tech_rating}</b>'
                f'&nbsp;&nbsp;·&nbsp;&nbsp;<b style="color:{agree_colour}">{agree_label}</b>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.caption("No votes yet — be the first to predict!")

    if len(history) > 1:
        st.plotly_chart(build_sentiment_chart(history), use_container_width=True)
    else:
        st.markdown(
            '<p style="font-size:0.82rem;color:#a0aec0;margin-top:12px;">'
            'Community Sentiment Chart will appear once enough votes have been cast for this ticker.'
            '</p>',
            unsafe_allow_html=True,
        )


# -- Individual Stock Analysis -------------------------------------------------

def render_stock_analysis(ticker: str, period: str = "1y"):
    """Render the full stock analysis report with staged skeleton loading.

    Render order (core analysis first, community/chart last):
      Header → Forecast → Ride the Nine → Signal Breakdown →
      Support & Resistance → Linear Regression → Prediction Market →
      Technical Chart (deferred — user must click to load)
    """

    if not ticker:
        st.info("Enter a ticker symbol in the sidebar.")
        return

    st.markdown(_LOADING_CSS, unsafe_allow_html=True)

    # ── Create placeholders in display order — core analysis first, voting last.
    # Chart has no placeholder: it is deferred behind a button.
    # _s_load   = st.empty()   # loading card — disabled; re-enable to restore step animation
    _s_header   = st.empty()   # company header
    _s_d1       = st.empty()   # divider
    _s_forecast = st.empty()   # forecast gauge + card
    _s_rtn      = st.empty()   # ride the nine (auto-loaded)
    _s_d2       = st.empty()   # divider
    _s_ad1      = st.empty()   # ad slot 1 (below ride-the-nine, lazy)
    _s_signals  = st.empty()   # signal breakdown
    _s_d3       = st.empty()   # divider
    _s_sr       = st.empty()   # support & resistance
    _s_d4       = st.empty()   # divider
    _s_lr       = st.empty()   # linear regression
    _s_d5       = st.empty()   # divider
    _s_ad2      = st.empty()   # ad slot 2 (below linear regression, lazy)
    _s_voting   = st.empty()   # prediction market (last core section — has Supabase I/O)

    # ── Fill all sections with skeletons immediately ───────────────────────────
    # _s_load.markdown(_loading_html(ticker, 0), unsafe_allow_html=True)  # loading card disabled
    _s_header.markdown(_skel_header(), unsafe_allow_html=True)
    _s_d1.markdown("---")
    _s_forecast.markdown(
        _skel_section("140px", 1) + _skel_two_col("190px"),
        unsafe_allow_html=True,
    )
    _s_rtn.markdown(
        _skel_section("160px", 1) + _skel_two_col("220px"),
        unsafe_allow_html=True,
    )
    _s_d2.markdown("---")
    _s_signals.markdown(_skel_section("150px", 5), unsafe_allow_html=True)
    _s_d3.markdown("---")
    _s_sr.markdown(_skel_section("140px", 3), unsafe_allow_html=True)
    _s_d4.markdown("---")
    _s_lr.markdown(_skel_section("220px", 1), unsafe_allow_html=True)
    _s_d5.markdown("---")
    _s_voting.markdown(_skel_section("160px", 2), unsafe_allow_html=True)

    def _clear_all():
        for s in [_s_header, _s_d1, _s_forecast, _s_rtn, _s_d2, _s_ad1,
                  _s_signals, _s_d3, _s_sr, _s_d4, _s_lr, _s_d5, _s_ad2, _s_voting]:
            s.empty()

    # ── Parallel I/O — _compute_analysis and fetch_info run concurrently.
    # On a cache hit both return in <10 ms.
    with ThreadPoolExecutor(max_workers=2) as _pool:
        _f_compute = _pool.submit(_compute_analysis, ticker, period)
        _f_info    = _pool.submit(fetch_info, ticker)

        # _s_load.markdown(_loading_html(ticker, 1), unsafe_allow_html=True)

        try:
            df, support, resistance, regression, forecast, rtn = _f_compute.result()
        except ValueError as e:
            _clear_all(); st.error(str(e)); return
        except Exception as e:
            _clear_all(); st.error(f"Data fetch failed: {e}"); return

        # _s_load.markdown(_loading_html(ticker, 2), unsafe_allow_html=True)
        info = _f_info.result()

    # _s_load.markdown(_loading_html(ticker, 3), unsafe_allow_html=True)

    # ── Pre-build display values ───────────────────────────────────────────────
    # _s_load.markdown(_loading_html(ticker, 4), unsafe_allow_html=True)

    company_name = _html.escape(info.get("longName") or info.get("shortName") or ticker)
    sector       = _html.escape(info.get("sector", ""))
    market_cap   = _fmt_large(info.get("marketCap") or info.get("totalAssets"))
    last_close   = float(df["Close"].iloc[-1])
    prev_close   = float(df["Close"].iloc[-2]) if len(df) > 1 else last_close
    day_chg      = last_close - prev_close
    day_chg_pct  = day_chg / prev_close * 100 if prev_close else 0
    chg_colour   = "#00a878" if day_chg >= 0 else "#e53e3e"
    chg_arrow    = "\u25b2" if day_chg >= 0 else "\u25bc"

    logo_html = ""
    website = info.get("website", "")
    if website:
        try:
            from urllib.parse import urlparse
            domain   = urlparse(website).netloc.lstrip("www.")
            token    = st.secrets["logo_dev"]["token"]
            logo_url = f"https://img.logo.dev/{domain}?token={token}&size=80&format=png"
            logo_html = (
                f'<img src="{logo_url}" '
                f'style="height:56px;width:56px;border-radius:10px;object-fit:contain;'
                f'background:#ffffff;padding:4px;margin-right:16px;vertical-align:middle;" '
                f'onerror="this.style.display=\'none\'">'
            )
        except Exception:
            pass

    _sector_html = f'&nbsp;&bull;&nbsp;{sector}' if sector else ''
    _header_html = (
        f'<div style="display:flex;align-items:center;margin-bottom:6px;">'
        f'{logo_html}<div>'
        f'<div style="font-size:1.8rem;font-weight:700;color:#1a202c;line-height:1.1;">{company_name}</div>'
        f'<div style="font-size:1rem;color:#4a5568;margin-top:2px;">'
        f'<span style="color:#6b7280;">{ticker}</span>&nbsp;&bull;&nbsp;'
        f'<span style="color:{chg_colour};font-weight:600;">'
        f'${last_close:,.2f}&nbsp;{chg_arrow}&nbsp;{abs(day_chg_pct):.2f}%'
        f'</span>{_sector_html}&nbsp;&bull;&nbsp;{market_cap}'
        f'</div></div></div>'
    )

    # Brief hold — re-enable if restoring loading card animation
    # time.sleep(0.45)

    # ── Reveal: fill each slot in order ───────────────────────────────────────

    # _s_load.empty()  # clear loading card — disabled with animation

    # Header
    _s_header.markdown(_header_html, unsafe_allow_html=True)

    # Forecast
    _s_forecast.empty()
    with _s_forecast.container():
        st.subheader("Stocklio Forecast")
        col_g, col_f = st.columns([1, 2.5])
        with col_g:
            st.plotly_chart(
                build_score_gauge(forecast.composite_score, forecast.rating),
                use_container_width=True,
            )
        with col_f:
            rc = _colour_class(forecast.rating)
            st.markdown(f"""
        <div class="metric-card">
            <div style="font-size:0.9rem; color:#4a5568; margin-bottom:4px;">Composite Rating</div>
            <div class="{rc}" style="font-size:2rem;">{forecast.rating}</div>
            <div style="color:#4a5568; font-size:0.85rem;">Confidence: <b style="color:#1a202c">{forecast.confidence}</b>
             &nbsp;|&nbsp; Score: <b style="color:#1a202c">{forecast.composite_score:+.3f}</b></div>
            <hr style="border-color:#1a202c; margin:10px 0;">
            <p style="color:#1a202c; font-size:0.92rem;">{forecast.summary}</p>
        </div>
            """, unsafe_allow_html=True)
        if forecast.setups:
            st.subheader("\u26a1 Notable Setups")
            for setup in forecast.setups:
                st.success(setup)

    # Ride the Nine — always visible, renders automatically
    _s_rtn.empty()
    with _s_rtn.container():
        st.subheader("Ride the Nine \u2014 9 EMA Strategy")
        signal      = rtn.get("signal", "Neutral")
        bias        = rtn.get("bias", "Neutral")
        bias_colour = "#00a878" if bias == "Bullish" else "#e53e3e" if bias == "Bearish" else "#dd6b20"
        bias_bg     = "#e6faf5" if bias == "Bullish" else "#fff5f5" if bias == "Bearish" else "#fffaf0"
        signal_label = (
            "\u25b2 Riding Up"   if signal == "Above" else
            "\u25bc Riding Down" if signal == "Below" else
            "\u2015 At the Nine"
        )
        streak    = rtn.get("streak", 0)
        pct       = rtn.get("pct_from_ema", 0.0)
        conf_icon = "\u2714\ufe0f" if rtn.get("ema9_vs_sma20") else "\u274c" if rtn.get("ema9_vs_sma20") is False else "\u2014"
        gap_label = "Widening \u2197" if rtn.get("gap_widening") else "Narrowing \u2198"

        col_rtn_l, col_rtn_r = st.columns([1, 2])
        with col_rtn_l:
            st.markdown(f"""
        <div class="metric-card" style="text-align:center;">
            <div style="font-size:0.8rem; color:#4a5568; margin-bottom:6px;">Current Signal</div>
            <div style="display:inline-block;background:{bias_bg};color:{bias_colour};
                border:1px solid {bias_colour};border-radius:8px;padding:8px 18px;
                font-size:1.15rem;font-weight:700;margin-bottom:14px;">{signal_label}</div>
            <table style="width:100%; font-size:0.85rem; color:#1a202c; border-collapse:collapse;">
                <tr><td style="color:#4a5568; padding:4px 0;">Distance from 9 EMA</td>
                    <td style="text-align:right; color:{bias_colour}; font-weight:600;">{pct:+.2f}%</td></tr>
                <tr><td style="color:#4a5568; padding:4px 0;">Streak</td>
                    <td style="text-align:right;">{streak} session{'s' if streak != 1 else ''}</td></tr>
                <tr><td style="color:#4a5568; padding:4px 0;">Momentum gap</td>
                    <td style="text-align:right;">{gap_label}</td></tr>
                <tr><td style="color:#4a5568; padding:4px 0;">9 EMA &gt; 20 SMA</td>
                    <td style="text-align:right;">{conf_icon}</td></tr>
            </table>
        </div>
            """, unsafe_allow_html=True)
            if rtn.get("just_crossed"):
                if rtn.get("cross_direction") == "up":
                    st.success("\U0001f7e2 **Fresh cross above 9 EMA** — potential entry signal")
                else:
                    st.error("\U0001f534 **Fresh cross below 9 EMA** — caution / exit signal")
        with col_rtn_r:
            st.markdown(f"""
        <div class="metric-card" style="height:100%;">
            <div style="font-size:0.8rem; color:#4a5568; margin-bottom:8px;">Strategy Analysis</div>
            <p style="color:#1a202c; font-size:0.92rem; line-height:1.6; margin:0;">{rtn.get("narrative", "")}</p>
            <hr style="border-color:#1a202c; margin:12px 0 8px 0;">
            <div style="font-size:0.78rem; color:#6b7280;">
                <b style="color:#4a5568;">How it works:</b>
                The "Ride the Nine" strategy uses the 9-period EMA as a dynamic trend guide.
                Enter trades when price is <em>close</em> to the 9 EMA (low risk).
                Stay long while price holds above it. Exit or flip short on a decisive close below.
                Combine with the 20 SMA for trend confirmation.
            </div>
        </div>
            """, unsafe_allow_html=True)
        st.plotly_chart(build_ride_the_nine_chart(df, ticker, rtn), use_container_width=True)

    # Signal Breakdown
    _s_signals.empty()
    with _s_signals.container():
        st.subheader("Signal Breakdown")
        sig_data = []
        for s in forecast.signals:
            icon = "\U0001f7e2" if s.direction == "bullish" else "\U0001f534" if s.direction == "bearish" else "\U0001f7e1"
            sig_data.append({
                "Signal":       f"{icon} {s.name}",
                "Score":        f"{s.score:+.2f}",
                "Weight":       f"{s.weight:.0%}",
                "Contribution": f"{s.score * s.weight:+.3f}",
                "Description":  s.description,
            })
        st.dataframe(pd.DataFrame(sig_data), hide_index=True, use_container_width=True)

    # Support & Resistance
    _s_sr.empty()
    with _s_sr.container():
        col_s, col_r = st.columns(2)
        with col_s:
            st.subheader("\U0001f7e2 Support Levels")
            if support:
                for s in reversed(support):
                    pct = (last_close - s) / last_close * 100
                    st.markdown(f"**${s:.2f}** &nbsp; ({pct:.1f}% below price)")
            else:
                st.caption("No clear support levels identified.")
        with col_r:
            st.subheader("\U0001f534 Resistance Levels")
            if resistance:
                for r in resistance:
                    pct = (r - last_close) / last_close * 100
                    st.markdown(f"**${r:.2f}** &nbsp; ({pct:.1f}% above price)")
            else:
                st.caption("No clear resistance levels identified.")

    # Linear Regression
    _s_lr.empty()
    with _s_lr.container():
        st.subheader("Linear Regression Trend Projection (10 days)")
        col_lr1, col_lr2, col_lr3, col_lr4 = st.columns(4)
        col_lr1.metric("Trend",         regression["trend_label"])
        col_lr2.metric("Slope ($/day)", f"{regression['slope']:+.3f}")
        col_lr3.metric("Daily drift",   f"{regression['pct_per_day']:+.3f}%")
        col_lr4.metric("R\u00b2",       f"{regression['r_squared']:.3f}")
        proj_10d = regression["projected"][-1] if regression["projected"] else None
        if proj_10d:
            proj_chg = (proj_10d - last_close) / last_close * 100
            st.caption(
                f"Projected price in ~10 trading days: **${proj_10d:.2f}** ({proj_chg:+.1f}%)"
                " -- based on 30-day regression. *Not a prediction.*"
            )

    # Ad slot 1 — rendered after ride-the-nine content is live.
    # The IntersectionObserver in the iframe fires only when the user scrolls here.
    with _s_ad1.container():
        lazy_ad_slot(SLOT_ANALYZE_BELOW_RTN, height=280)

    # Ad slot 2 — rendered after linear-regression content is live.
    with _s_ad2.container():
        lazy_ad_slot(SLOT_ANALYZE_BELOW_LR, height=280)

    # Prediction Market — rendered after core analysis so Supabase I/O
    # (parallelised internally) does not delay the forecast/signals sections.
    _s_voting.empty()
    with _s_voting.container():
        _render_voting(ticker, last_close, forecast.rating)

    # ── Technical Chart — deferred behind a button. ────────────────────────────
    # The heavy Plotly render is skipped entirely until the user requests it.
    # Session state key is per-ticker so the chart collapses when the ticker changes.
    st.markdown("---")
    _chart_key = f"_chart_{ticker}"
    if not st.session_state.get(_chart_key):
        st.markdown(
            '<p style="font-family:\'Inter\',sans-serif;font-size:0.85rem;'
            'color:#6b7280;margin:0 0 10px 0;">'
            'Full technical chart with overlays (Bollinger Bands, volume, LR projection) '
            'is available on demand.</p>',
            unsafe_allow_html=True,
        )
        if st.button("📊 View Technical Chart", key=f"btn_chart_{ticker}"):
            st.session_state[_chart_key] = True
    if st.session_state.get(_chart_key):
        st.subheader("Chart")
        chart_opts = st.columns(3)
        show_bb  = chart_opts[0].checkbox("Bollinger Bands", value=True)
        show_vol = chart_opts[1].checkbox("Volume Panel",    value=True)
        show_reg = chart_opts[2].checkbox("LR Projection",   value=True)
        fig = build_stock_chart(
            df, ticker,
            support=support, resistance=resistance,
            show_bb=show_bb, show_volume=show_vol,
            regression=regression if show_reg else None,
        )
        st.plotly_chart(fig, use_container_width=True)
        with st.expander("\U0001f4cb Raw Data & Indicators"):
            display_cols = [
                "Open", "High", "Low", "Close", "Volume",
                "SMA_50", "SMA_200", "RSI", "MACD", "MACD_sig",
                "BB_upper", "BB_lower", "ATR", "STOCH_K", "STOCH_D",
            ]
            show_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(
                df[show_cols].tail(50).round(4).sort_index(ascending=False),
                use_container_width=True,
            )

    # Bottom leaderboard — always rendered, loads lazily when scrolled into view
    lazy_ad_slot(SLOT_BOTTOM_LEADERBOARD, ad_format="auto", height=120)
