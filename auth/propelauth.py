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
    Inject the PropelAuth JS client into the page via components.html().

    st.markdown() strips <script> tags (React dangerouslySetInnerHTML does not
    execute scripts set via innerHTML). components.html() runs inside a sandboxed
    iframe where scripts do execute.  We target window.parent to modify the
    Streamlit app's URL, then reload.  A try/catch silently handles the rare
    cross-origin case (badly-configured reverse proxy).

    On every page load this checks for a valid PropelAuth session (stored in
    cookies by the hosted login page).  If one exists it appends ?pa_token=...
    to the parent URL so handle_auth_callback() can read it.
    """
    import streamlit.components.v1 as components
    auth_url = _auth_url()
    components.html(
        f"""<script src="https://cdn.jsdelivr.net/npm/@propelauth/javascript@2/dist/propelauth.js"></script>
<script>
(function(){{
  if(window.__paInit)return;
  window.__paInit=true;
  var win=(window.parent&&window.parent!==window)?window.parent:window;
  PropelAuth.createClient({{
    authUrl:"{auth_url}",
    enableBackgroundTokenRefresh:true
  }}).getAuthenticationInfoOrNull().then(function(info){{
    try{{
      var cur=new URLSearchParams(win.location.search);
      if(info&&info.accessToken){{
        if(!cur.has('pa_token')){{
          cur.set('pa_token',info.accessToken);
          win.history.replaceState(null,'',win.location.pathname+'?'+cur.toString());
          win.location.reload();
        }}
      }}else if(cur.has('pa_token')){{
        cur.delete('pa_token');
        win.history.replaceState(null,'',win.location.pathname+'?'+cur.toString());
      }}
    }}catch(e){{/* cross-origin — silently skip */}}
  }});
}})();
</script>""",
        height=0,
    )


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
