"""
pages/logged_out.py -- Post-logout landing page.
"""

import streamlit as st
from auth.propelauth import login_url

# Clear any auth session state.
for _k in ("logged_in", "user_email", "user_id", "pa_token"):
    st.session_state.pop(_k, None)
if st.query_params.get("pa_token"):
    st.query_params.clear()

# Arm localStorage clear on first render.
if not st.session_state.get("_lo_armed"):
    st.session_state["_lo_armed"] = True
    st.session_state["_pa_just_logged_out"] = True
    st.session_state["_pa_skip_auth"] = True
    st.rerun()

# Clean logged-out UI.
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Darker+Grotesque:wght@800;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  .stApp { background-color: #f5f7fa; }
  .block-container { padding-top: 0 !important; }
  [data-testid="stSidebar"] { display: none !important; }
  header[data-testid="stHeader"] { display: none !important; }
</style>
<div style="
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 80vh;
  font-family: 'Inter', sans-serif;
  text-align: center;
  gap: 0;
">
  <div style="font-family:'Darker Grotesque',sans-serif;font-size:3rem;font-weight:900;color:#1a202c;letter-spacing:-0.02em;margin-bottom:4px;">
    stocklio<span style="color:#00c896;">.</span>
  </div>
  <div style="font-size:1.15rem;font-weight:600;color:#1a202c;margin-bottom:8px;margin-top:24px;">
    You've been signed out.
  </div>
  <div style="font-size:0.95rem;color:#6b7280;margin-bottom:36px;">
    Thanks for using Stocklio. See you next time.
  </div>
  <div style="display:flex;gap:12px;flex-wrap:wrap;justify-content:center;">
    <a href="{login_url}" style="
      display:inline-flex;align-items:center;
      background:#00c896;color:#ffffff;
      padding:11px 28px;border-radius:24px;
      font-family:'Inter',sans-serif;font-size:0.9rem;font-weight:600;
      text-decoration:none;
      box-shadow:0 2px 8px rgba(0,200,150,0.35);
    ">Log in</a>
    <a href="https://www.stocklio.ai" style="
      display:inline-flex;align-items:center;
      background:#ffffff;color:#1a202c;
      padding:11px 28px;border-radius:24px;
      font-family:'Inter',sans-serif;font-size:0.9rem;font-weight:600;
      text-decoration:none;
      border:1px solid #e2e8f0;
      box-shadow:0 1px 4px rgba(0,0,0,0.06);
    ">Go home</a>
  </div>
</div>
""".replace("{login_url}", login_url()), unsafe_allow_html=True)

st.stop()
