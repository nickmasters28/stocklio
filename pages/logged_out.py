"""
pages/logged_out.py -- Post-logout landing page.

PropelAuth (and our own logout flow) can redirect here after sign-out.
This page delegates to inject_auth_js's proven logout mechanism, which
clears localStorage, invalidates the PropelAuth session cookie, and
navigates the browser to https://www.stocklio.ai.
"""

import streamlit as st

# Clear any auth session state (in case handle_auth_callback ran before us).
for _k in ("logged_in", "user_email", "user_id", "pa_token"):
    st.session_state.pop(_k, None)

if st.query_params.get("pa_token"):
    st.query_params.clear()

# On the first load of this page, arm the inject_auth_js logout path and
# rerun so app.py fires the logout JS (clears localStorage + navigates to
# www.stocklio.ai).  A guard flag prevents this from looping on the second
# render while the JS redirect is in flight.
if not st.session_state.get("_lo_armed"):
    st.session_state["_lo_armed"] = True
    st.session_state["_pa_just_logged_out"] = True
    st.session_state["_pa_skip_auth"] = True
    st.rerun()

# Second render — inject_auth_js has fired its logout JS.
# Show a brief message while the browser navigates away.
st.markdown(
    "<p style='font-family:sans-serif;color:#6b7280;margin-top:40px;text-align:center;'>"
    "Signing out…</p>",
    unsafe_allow_html=True,
)
st.stop()
