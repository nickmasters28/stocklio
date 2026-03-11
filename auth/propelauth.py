"""
auth/propelauth.py -- PropelAuth integration for Stocklio.

Flow:
  1. User clicks "Log in" or "Sign up" → redirected to PropelAuth hosted page.
  2. PropelAuth's JS client (injected via inject_auth_js) detects the active
     session from cookies and forwards the access token as a query param.
  3. On the next Streamlit render, handle_auth_callback() reads the token,
     validates it using the RSA public key, and stores the user in session state.

Secrets required in .streamlit/secrets.toml:
  [propelauth]
  auth_url   = "https://YOUR_SUBDOMAIN.propelauthtest.com"
  public_key = \"\"\"-----BEGIN PUBLIC KEY-----
  ...
  -----END PUBLIC KEY-----\"\"\"
"""

import streamlit as st
import jwt
from urllib.parse import quote as _quote


# ---------------------------------------------------------------------------

def _auth_url() -> str:
    return st.secrets["propelauth"]["auth_url"].rstrip("/")


def _public_key() -> str:
    key = st.secrets["propelauth"]["public_key"]
    # Handle \n-escaped single-line format used in env vars
    return key.replace("\\n", "\n")


def _base_url() -> str:
    try:
        return st.secrets["propelauth"]["redirect_url"].rstrip("/")
    except KeyError:
        return "http://localhost:8501"


def login_url() -> str:
    redirect = f"{_base_url()}/analyze?ticker=AAPL"
    return f"{_auth_url()}/en/login?redirect_to={_quote(redirect, safe='')}"


def signup_url() -> str:
    redirect = f"{_base_url()}/analyze?ticker=AAPL"
    return f"{_auth_url()}/en/signup?redirect_to={_quote(redirect, safe='')}"


# ---------------------------------------------------------------------------

def inject_auth_js() -> None:
    """
    Inject the PropelAuth JS client into the page.

    On every page load it checks whether the user already has a valid
    PropelAuth session (stored in cookies by the hosted login page).
    If a session exists it appends the access token as ?pa_token=... so
    Streamlit can read it via st.query_params.
    """
    auth_url = _auth_url()
    st.markdown(f"""
    <script src="https://cdn.jsdelivr.net/npm/@propelauth/javascript@2/dist/propelauth.js"></script>
    <script>
    (function() {{
        if (window.__paChecked) return;
        window.__paChecked = true;
        const client = PropelAuth.createClient({{
            authUrl: "{auth_url}",
            enableBackgroundTokenRefresh: true,
        }});
        client.getAuthenticationInfoOrNull().then(function(info) {{
            const cur = new URLSearchParams(window.location.search);
            if (info && info.accessToken) {{
                if (cur.get('pa_token') !== info.accessToken) {{
                    cur.set('pa_token', info.accessToken);
                    window.history.replaceState(null, '', '?' + cur.toString());
                    window.location.reload();
                }}
            }} else {{
                if (cur.has('pa_token')) {{
                    cur.delete('pa_token');
                    window.history.replaceState(null, '', '?' + cur.toString());
                }}
            }}
        }});
    }})();
    </script>
    """, unsafe_allow_html=True)


def _validate_token(token: str):
    """Verify the JWT signature using PropelAuth's RSA public key."""
    try:
        payload = jwt.decode(
            token,
            _public_key(),
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def handle_auth_callback() -> None:
    """
    Read ?pa_token from the URL, validate it, and populate session state.
    Call this once at the top of every page render (before rendering content).
    """
    token = st.query_params.get("pa_token")
    if not token:
        return

    # Already validated this exact token — skip
    if st.session_state.get("pa_token") == token:
        return

    payload = _validate_token(token)
    if payload:
        st.session_state["logged_in"]  = True
        st.session_state["user_email"] = payload.get("email", "")
        st.session_state["user_id"]    = payload.get("user_id", "")
        st.session_state["pa_token"]   = token
    else:
        for key in ("logged_in", "user_email", "user_id", "pa_token"):
            st.session_state.pop(key, None)


def logout() -> None:
    """Clear local session. PropelAuth JS client will clear its cookies."""
    for key in ("logged_in", "user_email", "user_id", "pa_token"):
        st.session_state.pop(key, None)
    st.query_params.clear()
