"""
pages/copilot.py -- Stocklio Copilot AI financial assistant.

Route:  /copilot
Auth:   logged-in + Pro subscription required
Model:  claude-opus-4-6  (streaming)
Limit:  MONTHLY_LIMIT messages/user/month  (tracked in Supabase copilot_usage table)

Secrets required in .streamlit/secrets.toml:
  [anthropic]
  api_key = "sk-ant-..."
"""

import streamlit as st
import anthropic

from auth.propelauth import is_paid_user, login_url, signup_url
from data.copilot_usage import get_monthly_usage, increment_usage, MONTHLY_LIMIT

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Darker+Grotesque:wght@700;800;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
[data-testid='stSidebarNav'],[data-testid='stSidebarNavItems'],
[data-testid='stSidebarNavSeparator'],[data-testid='stMainMenu'],
[data-testid='stHeader'],#MainMenu{display:none!important;}
.stApp{background:#f5f7fa;}
.block-container{padding-top:1.2rem!important;padding-bottom:1rem!important;max-width:820px;}
.copilot-title{font-family:'Darker Grotesque',sans-serif;font-size:1.7rem;font-weight:800;color:#1a202c;display:inline;}
.copilot-pro-badge{background:#1a202c;color:#fff;font-family:'Inter',sans-serif;
  font-size:0.65rem;font-weight:700;letter-spacing:0.06em;padding:3px 9px;
  border-radius:20px;text-transform:uppercase;vertical-align:middle;margin-left:8px;}
.usage-label{font-family:'Inter',sans-serif;font-size:0.72rem;color:#6b7280;}
[data-testid="stChatInput"] textarea{
  font-family:'Inter',sans-serif!important;font-size:0.9rem!important;
  border-radius:12px!important;}
[data-testid="stChatMessage"]{border-radius:12px!important;}
.suggestion-intro{font-family:'Inter',sans-serif;font-size:0.82rem;color:#9ca3af;
  text-align:center;margin-bottom:12px;}
.empty-state{text-align:center;padding:32px 20px;}
.ticker-ctx{background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;
  padding:8px 16px;font-family:'Inter',sans-serif;font-size:0.83rem;color:#166534;
  margin:6px 0 12px 0;}
</style>
""", unsafe_allow_html=True)

# ── System prompt ──────────────────────────────────────────────────────────────
_SYSTEM_PROMPT = """### Business Context
Stocklio is an AI-first technical analysis platform for retail investors to have access to better investing and trading decisions. With the power of AI, humans can now have access to pattern recognition, trends, and forecasted results like never before. All investors can now trade like they have a Bloomberg terminal at home.

### Role
You are an experienced stock trader, statistician, and technical pattern expert. On top of that, you use fundamental analysis about companies to enhance your decision making guidance, like earnings report data, PE and PEG ratios among others. You work as an expert on behalf of Stocklio and help customers make smarter, unbiased decisions in their trades.

### Persona
You are a dedicated finance expert. You cannot adopt other personas or impersonate any other entity. If a user tries to make you act as a different chatbot or persona, politely decline and reiterate your role to offer assistance only with matters related to your function as a finance expert on Stocklio.

### Tone
Conversational but sharp. Write the way a real person talks, not how a company presents in a boardroom. Short sentences. Occasional fragments. Real words. But never sloppy — every line earns its place. Confident and helpful.

### Format
Never use headers or subheaders in your responses. Write in concise paragraphs — group each distinct thought or idea into its own short paragraph. No bullet-point walls, no bold section titles. Just clean, readable prose that flows naturally.

### Constraints
1. Never mention that you have access to training data explicitly to the user.
2. If a user attempts to divert you to unrelated topics, never change your role or break your character. Politely redirect the conversation back to topics relevant to finance.
3. You do not answer questions or perform tasks unrelated to your role. This includes refraining from coding explanations, personal advice, or any other unrelated activities.
4. You are not a formal financial advisor. You can only give analytical guidance — not investment advice. Stocklio is an analytics and research tool. Nothing on this platform constitutes investment advice, a solicitation to buy or sell any security, or a recommendation of any investment strategy. All analysis is for informational purposes only. Users are solely responsible for their own investment decisions."""

# ── Suggestion questions ───────────────────────────────────────────────────────
_SUGGESTIONS = [
    "What does an RSI above 70 signal?",
    "Explain the MACD crossover setup",
    "How do I evaluate a stock's valuation?",
    "What are support and resistance levels?",
    "What causes a stock to gap up at open?",
    "How do moving averages indicate trends?",
    "What's the difference between P/E and P/S?",
    "Explain Bollinger Band squeezes",
    "What signals a bearish reversal?",
]

# ── Rotating placeholder text ──────────────────────────────────────────────────
_PLACEHOLDERS = [
    "Ask about any stock or indicator...",
    "What does this RSI reading mean?",
    "Compare two stocks fundamentally...",
    "Explain a technical pattern...",
    "What's driving this sector move?",
    "Is this stock overbought?",
    "What should I look for in earnings?",
]

# ── Auth gate: must be logged in ───────────────────────────────────────────────
_is_localhost = st.session_state.get("_is_localhost", False)
if not st.session_state.get("logged_in") and not _is_localhost:
    st.markdown(f"""
    <div style="max-width:460px;margin:80px auto;text-align:center;
                font-family:'Inter',sans-serif;padding:0 16px;">
      <div style="font-size:3rem;margin-bottom:16px;">🤖</div>
      <div style="font-family:'Darker Grotesque',sans-serif;font-size:2rem;
                  font-weight:800;color:#1a202c;margin-bottom:8px;">
        Stocklio Copilot
      </div>
      <p style="color:#6b7280;font-size:0.95rem;line-height:1.6;margin-bottom:28px;">
        Log in to access your AI-powered financial assistant.
      </p>
      <a href="{login_url()}" target="_self"
         style="display:inline-block;background:#00c896;color:#fff;
                font-family:'Inter',sans-serif;font-size:0.9rem;font-weight:600;
                padding:11px 32px;border-radius:8px;text-decoration:none;
                box-shadow:0 2px 8px rgba(0,200,150,0.3);">
        Log in →
      </a>
      &nbsp;&nbsp;
      <a href="{signup_url()}" target="_self"
         style="display:inline-block;background:#fff;color:#1a202c;border:1px solid #e2e8f0;
                font-family:'Inter',sans-serif;font-size:0.9rem;font-weight:600;
                padding:11px 32px;border-radius:8px;text-decoration:none;">
        Sign up free
      </a>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Free user teaser ───────────────────────────────────────────────────────────
if not is_paid_user():
    st.markdown(f"""
    <div style="max-width:680px;margin:0 auto;padding:20px 8px 40px 8px;">

      <div style="text-align:center;margin-bottom:32px;">
        <div style="font-size:3rem;margin-bottom:12px;">🤖</div>
        <div style="font-family:'Darker Grotesque',sans-serif;font-size:2.2rem;
                    font-weight:800;color:#1a202c;margin-bottom:6px;">
          Stocklio Copilot
        </div>
        <p style="font-family:'Inter',sans-serif;font-size:1rem;color:#6b7280;
                  line-height:1.65;max-width:480px;margin:0 auto 24px auto;">
          Your AI financial analyst — ask any question about stocks, markets,
          technicals, or fundamentals and get an expert answer instantly.
        </p>
        <a href="/pricing" target="_self"
           style="display:inline-block;background:#00c896;color:#fff;
                  font-family:'Inter',sans-serif;font-size:0.95rem;font-weight:600;
                  padding:12px 36px;border-radius:8px;text-decoration:none;
                  box-shadow:0 2px 12px rgba(0,200,150,0.35);">
          Upgrade to Pro →
        </a>
      </div>

      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:16px;
                  padding:24px;margin-bottom:24px;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
        <div style="font-family:'Inter',sans-serif;font-size:0.72rem;font-weight:700;
                    color:#9ca3af;text-transform:uppercase;letter-spacing:0.06em;
                    margin-bottom:16px;">Sample conversation</div>

        <div style="display:flex;gap:10px;margin-bottom:14px;">
          <div style="width:32px;height:32px;border-radius:50%;background:#e2e8f0;
                      display:flex;align-items:center;justify-content:center;
                      font-size:0.85rem;flex-shrink:0;">👤</div>
          <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;
                      padding:10px 14px;font-family:'Inter',sans-serif;font-size:0.88rem;
                      color:#1a202c;line-height:1.5;">
            NVDA has an RSI of 72 and MACD just crossed bearish. Should I be concerned?
          </div>
        </div>

        <div style="display:flex;gap:10px;margin-bottom:4px;">
          <div style="width:32px;height:32px;border-radius:50%;background:#1a202c;
                      display:flex;align-items:center;justify-content:center;
                      font-size:0.85rem;flex-shrink:0;">🤖</div>
          <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:12px;
                      padding:10px 14px;font-family:'Inter',sans-serif;font-size:0.88rem;
                      color:#1a202c;line-height:1.6;position:relative;">
            <strong>RSI of 72</strong> puts NVDA in overbought territory — historically a signal
            to watch for momentum exhaustion rather than an immediate sell trigger.
            The <strong>bearish MACD crossover</strong> adds confluence: the shorter EMA
            has crossed below the longer EMA, suggesting near-term momentum is shifting.
            <br><br>
            Key things to watch: <br>
            • Does price hold the 20-day SMA? A break below would strengthen the bearish case.<br>
            • Is volume declining on up days? That confirms weakening demand.<br>
            • Any upcoming catalysts (earnings, guidance) that could override technicals?
            <br><br>
            This is a setup worth monitoring, not necessarily exiting — context and your
            timeframe matter.
            <div style="position:absolute;top:10px;right:12px;background:rgba(255,255,255,0.7);
                        backdrop-filter:blur(4px);border-radius:6px;padding:4px 8px;
                        font-size:0.7rem;font-weight:700;color:#6b7280;">Pro only</div>
          </div>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:14px;margin-bottom:28px;">
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px;">
          <div style="font-size:1.3rem;margin-bottom:6px;">📊</div>
          <div style="font-family:'Darker Grotesque',sans-serif;font-size:1rem;
                      font-weight:800;color:#1a202c;margin-bottom:4px;">Stock Analysis</div>
          <div style="font-family:'Inter',sans-serif;font-size:0.8rem;color:#6b7280;">
            Deep dives on any ticker — technicals, fundamentals, and catalysts.
          </div>
        </div>
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px;">
          <div style="font-size:1.3rem;margin-bottom:6px;">📈</div>
          <div style="font-family:'Darker Grotesque',sans-serif;font-size:1rem;
                      font-weight:800;color:#1a202c;margin-bottom:4px;">Technical Signals</div>
          <div style="font-family:'Inter',sans-serif;font-size:0.8rem;color:#6b7280;">
            Understand RSI, MACD, Bollinger Bands, and every indicator in plain English.
          </div>
        </div>
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px;">
          <div style="font-size:1.3rem;margin-bottom:6px;">🧮</div>
          <div style="font-family:'Darker Grotesque',sans-serif;font-size:1rem;
                      font-weight:800;color:#1a202c;margin-bottom:4px;">Fundamentals</div>
          <div style="font-family:'Inter',sans-serif;font-size:0.8rem;color:#6b7280;">
            P/E, P/S, margins, growth rates — explained in context of the actual stock.
          </div>
        </div>
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px;">
          <div style="font-size:1.3rem;margin-bottom:6px;">💬</div>
          <div style="font-family:'Darker Grotesque',sans-serif;font-size:1rem;
                      font-weight:800;color:#1a202c;margin-bottom:4px;">Ongoing Thread</div>
          <div style="font-family:'Inter',sans-serif;font-size:0.8rem;color:#6b7280;">
            Ask follow-ups, go deeper, and build context across an entire session.
          </div>
        </div>
      </div>

      <div style="text-align:center;">
        <a href="/pricing" target="_self"
           style="display:inline-block;background:#00c896;color:#fff;
                  font-family:'Inter',sans-serif;font-size:0.95rem;font-weight:600;
                  padding:12px 36px;border-radius:8px;text-decoration:none;">
          Upgrade to Pro — {MONTHLY_LIMIT} messages/month included →
        </a>
        <p style="font-family:'Inter',sans-serif;font-size:0.78rem;color:#9ca3af;margin-top:10px;">
          Cancel anytime · email hello@stocklio.ai
        </p>
      </div>

    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Paid user: load usage ──────────────────────────────────────────────────────
_user_id = st.session_state.get("user_id", "")
_usage   = get_monthly_usage(_user_id)
_remaining = MONTHLY_LIMIT - _usage

# Ticker context injected from /analyze?ticker=XYZ via query param
_ticker_ctx = st.query_params.get("ticker", "").upper().strip()

# Initialize session conversation
if "copilot_messages" not in st.session_state:
    st.session_state["copilot_messages"] = []

# ── Header ─────────────────────────────────────────────────────────────────────
col_title, col_meta = st.columns([3, 1])
with col_title:
    st.markdown(
        '<span class="copilot-title">🤖 Stocklio Copilot</span>'
        '<span class="copilot-pro-badge">PRO</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p style="font-family:\'Inter\',sans-serif;font-size:0.83rem;color:#6b7280;'
        'margin:2px 0 0 0;">Ask anything about stocks, markets, and technical analysis.</p>',
        unsafe_allow_html=True,
    )

with col_meta:
    _pct = _usage / MONTHLY_LIMIT
    _bar_clr = "#00c896" if _pct < 0.75 else ("#ed8936" if _pct < 1.0 else "#e53e3e")
    st.markdown(f"""
    <div style="text-align:right;padding-top:6px;">
      <div class="usage-label">{_usage} / {MONTHLY_LIMIT} messages this month</div>
      <div style="background:#e2e8f0;border-radius:4px;height:5px;
                  overflow:hidden;margin-top:5px;">
        <div style="width:{min(_pct*100,100):.0f}%;background:{_bar_clr};
                    height:100%;border-radius:4px;transition:width 0.3s;"></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# Ticker context banner
if _ticker_ctx:
    st.markdown(
        f'<div class="ticker-ctx">📊 Analyzing <b>{_ticker_ctx}</b> — '
        f'feel free to ask questions specific to this stock.</div>',
        unsafe_allow_html=True,
    )

st.divider()

# ── Chat history ───────────────────────────────────────────────────────────────
for _msg in st.session_state["copilot_messages"]:
    with st.chat_message(_msg["role"], avatar="🤖" if _msg["role"] == "assistant" else "👤"):
        st.markdown(_msg["content"])

# ── Empty state: suggestion chips ─────────────────────────────────────────────
if not st.session_state["copilot_messages"]:
    st.markdown(
        '<div class="empty-state">'
        '<div style="font-size:2rem;margin-bottom:8px;">💬</div>'
        '<div style="font-family:\'Inter\',sans-serif;font-size:0.9rem;color:#6b7280;">'
        'Start by asking a question, or try one of these:</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    # 3 suggestion chips
    _sug_cols = st.columns(3)
    for _i, _sug in enumerate(_SUGGESTIONS[:3]):
        with _sug_cols[_i]:
            if st.button(_sug, key=f"sug_{_i}", use_container_width=True):
                st.session_state["_copilot_prefill"] = _sug
                st.rerun()

    # Second row of 3
    _sug_cols2 = st.columns(3)
    for _i, _sug in enumerate(_SUGGESTIONS[3:6]):
        with _sug_cols2[_i]:
            if st.button(_sug, key=f"sug2_{_i}", use_container_width=True):
                st.session_state["_copilot_prefill"] = _sug
                st.rerun()

# ── Limit reached ──────────────────────────────────────────────────────────────
if _remaining <= 0:
    from datetime import date
    _today = date.today()
    # First day of next month
    if _today.month == 12:
        _reset = date(_today.year + 1, 1, 1)
    else:
        _reset = date(_today.year, _today.month + 1, 1)
    _reset_str = _reset.strftime("%B 1st")

    st.markdown(f"""
    <div style="max-width:520px;margin:24px auto;background:#fff;border:1px solid #e2e8f0;
                border-radius:16px;padding:32px 28px;text-align:center;
                box-shadow:0 2px 12px rgba(0,0,0,0.05);">
      <div style="font-size:2.4rem;margin-bottom:12px;">⚡</div>
      <div style="font-family:'Darker Grotesque',sans-serif;font-size:1.5rem;
                  font-weight:800;color:#1a202c;margin-bottom:8px;">
        You've hit your monthly limit
      </div>
      <p style="font-family:'Inter',sans-serif;font-size:0.92rem;color:#6b7280;
                line-height:1.6;margin-bottom:8px;">
        You've used all <strong>{MONTHLY_LIMIT} Copilot messages</strong> for this month.
        Your limit resets on <strong>{_reset_str}</strong>.
      </p>
      <div style="background:#f8fafc;border-radius:8px;padding:10px 16px;
                  margin:16px 0 20px 0;">
        <div style="font-family:'Inter',sans-serif;font-size:0.78rem;color:#6b7280;
                    margin-bottom:6px;">{MONTHLY_LIMIT} / {MONTHLY_LIMIT} messages used</div>
        <div style="background:#e2e8f0;border-radius:4px;height:6px;overflow:hidden;">
          <div style="width:100%;background:#e53e3e;height:100%;border-radius:4px;"></div>
        </div>
      </div>
      <p style="font-family:'Inter',sans-serif;font-size:0.88rem;color:#4a5568;
                margin-bottom:20px;">
        Need more messages now? Email us and we'll sort you out.
      </p>
      <a href="mailto:hello@stocklio.ai?subject=Copilot%20Message%20Top-Up"
         style="display:inline-block;background:#00c896;color:#fff;
                font-family:'Inter',sans-serif;font-size:0.9rem;font-weight:600;
                padding:11px 28px;border-radius:8px;text-decoration:none;
                box-shadow:0 2px 8px rgba(0,200,150,0.3);">
        Request more messages →
      </a>
      <div style="margin-top:12px;">
        <span style="font-family:'Inter',sans-serif;font-size:0.78rem;color:#9ca3af;">
          Or wait — your limit resets automatically on {_reset_str}.
        </span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Chat input ─────────────────────────────────────────────────────────────────
_ph_idx   = len(st.session_state["copilot_messages"]) % len(_PLACEHOLDERS)
_prefill  = st.session_state.pop("_copilot_prefill", None)
_prompt   = st.chat_input(_PLACEHOLDERS[_ph_idx]) or _prefill

# ── Handle message ─────────────────────────────────────────────────────────────
if _prompt:
    # Build system with optional ticker context
    _system = _SYSTEM_PROMPT
    if _ticker_ctx:
        _system += (
            f"\n\nThe user is currently analyzing {_ticker_ctx} on Stocklio. "
            "When relevant, connect your answers to this stock."
        )

    # Append user turn
    st.session_state["copilot_messages"].append({"role": "user", "content": _prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(_prompt)

    # Stream assistant response
    with st.chat_message("assistant", avatar="🤖"):
        try:
            _client = anthropic.Anthropic(
                api_key=st.secrets["anthropic"]["api_key"]
            )

            _api_msgs = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state["copilot_messages"]
            ]

            def _stream():
                with _client.messages.stream(
                    model="claude-opus-4-6",
                    max_tokens=2048,
                    system=_system,
                    messages=_api_msgs,
                ) as stream:
                    for text in stream.text_stream:
                        yield text

            _response_text = st.write_stream(_stream())

            # Save assistant turn
            st.session_state["copilot_messages"].append(
                {"role": "assistant", "content": _response_text}
            )

            # Track usage
            increment_usage(_user_id)

            # Warn if approaching limit
            _new_usage = _usage + 1
            if _new_usage >= MONTHLY_LIMIT - 5:
                st.caption(
                    f"⚠️ {MONTHLY_LIMIT - _new_usage} messages remaining this month."
                )

        except anthropic.AuthenticationError:
            st.error("Copilot is temporarily unavailable. Please try again later.")
            # Roll back the user message so they can retry
            st.session_state["copilot_messages"].pop()
        except Exception as _e:
            st.error(f"Something went wrong: {_e}")
            st.session_state["copilot_messages"].pop()

# ── Footer: clear conversation ─────────────────────────────────────────────────
if st.session_state.get("copilot_messages"):
    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
    if st.button("🗑️ Clear conversation", type="secondary", key="clear_chat"):
        st.session_state["copilot_messages"] = []
        st.rerun()

# ── Back link ──────────────────────────────────────────────────────────────────
_back = f"/analyze?ticker={_ticker_ctx}" if _ticker_ctx else "/analyze"
st.markdown(
    f'<div style="text-align:center;margin-top:16px;">'
    f'<a href="{_back}" target="_self" '
    f'style="font-family:\'Inter\',sans-serif;font-size:0.78rem;color:#9ca3af;text-decoration:none;">'
    f'← Back to Analyze</a></div>',
    unsafe_allow_html=True,
)
