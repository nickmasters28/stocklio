"""
pages/logged_out.py -- Post-logout landing page.

PropelAuth (and our own logout flow) can redirect here after sign-out.
This page clears all remaining auth state and sends the browser to
https://www.stocklio.ai with no auth query params remaining.
"""

import streamlit as st
import streamlit.components.v1 as components

# Clear any session state that may have been set by handle_auth_callback
# running in app.py before this page executes (e.g. if pa_token was in URL).
for _k in ("logged_in", "user_email", "user_id", "pa_token"):
    st.session_state.pop(_k, None)

# Strip pa_token (and any other auth params) from the URL.
if st.query_params.get("pa_token"):
    st.query_params.clear()

components.html(
    "<script>"
    "try{localStorage.removeItem('pa_token');localStorage.removeItem('pa_expiry');}catch(e){}"
    "window.location.replace('https://www.stocklio.ai');"
    "</script>",
    height=0,
)
st.stop()
