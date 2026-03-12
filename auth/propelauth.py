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
import json
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

def inject_auth_js(current_params: dict = None) -> None:
    """
    Detect the PropelAuth session and inject ?pa_token= into the main page URL.

    Loads the PropelAuth SDK in the components.html() iframe (same-origin in
    production per the GA injection comment in app.py).  After getting the
    access token, navigates via window.parent.location.href — a write-only
    navigation that is always allowed even cross-origin — using a URL built
    entirely from Python-side values so we never need to read window.parent.location.

    current_params should be dict(st.query_params) from the caller (app.py).
    This lets JS reconstruct the current page URL without cross-origin reads.
    """
    import streamlit.components.v1 as components
    import urllib.parse

    auth_url    = _auth_url()
    auth_url_js = json.dumps(auth_url)

    # Build the redirect base URL from Python so JS needs no location reads.
    # Strip any stale pa_token; detect page path from params heuristic.
    safe = {k: v for k, v in (current_params or {}).items() if k != "pa_token"}
    page_path   = "/analyze" if "ticker" in safe else "/"
    redirect_base = _base_url() + page_path
    if safe:
        redirect_base += "?" + urllib.parse.urlencode(safe)
    redirect_base_js = json.dumps(redirect_base)

    # ── Logout path ─────────────────────────────────────────────────────────
    if st.session_state.pop("_pa_just_logged_out", False):
        components.html(
            f"""<script type="module">
import {{ createClient }} from 'https://cdn.jsdelivr.net/npm/@propelauth/javascript@2/+esm';
try{{localStorage.removeItem('pa_token');localStorage.removeItem('pa_expiry');}}catch(e){{}}
try{{
  createClient({{authUrl:{auth_url_js},enableBackgroundTokenRefresh:false}}).logout(false);
}}catch(e){{}}
</script>""",
            height=0,
        )
        return

    components.html(
        f"""<script type="module">
import {{ createClient }} from 'https://cdn.jsdelivr.net/npm/@propelauth/javascript@2/+esm';
(function(){{
  if(window.__paInit)return;
  window.__paInit=true;

  var redirectBase={redirect_base_js};

  function applyToken(token){{
    try{{localStorage.setItem('pa_token',token);}}catch(e){{}}
    // Primary: same-origin URL manipulation (preserves exact current URL)
    try{{
      var p=window.parent;
      var cur=new URLSearchParams(p.location.search);
      if(!cur.has('pa_token')){{
        cur.set('pa_token',token);
        p.history.replaceState(null,'',p.location.pathname+'?'+cur.toString());
        p.location.reload();
        return;
      }}
    }}catch(e){{}}
    // Fallback: cross-origin navigate to Python-constructed URL (write-only, always allowed)
    var sep=redirectBase.indexOf('?')>=0?'&':'?';
    window.parent.location.href=redirectBase+sep+'pa_token='+encodeURIComponent(token);
  }}

  // Fast path: valid token cached in localStorage
  try{{
    var stored=localStorage.getItem('pa_token');
    var expiry=parseInt(localStorage.getItem('pa_expiry')||'0');
    if(stored&&expiry>Math.floor(Date.now()/1000)){{applyToken(stored);return;}}
  }}catch(e){{}}

  // pa_token already in parent URL — handle_auth_callback() will process it
  try{{if(new URLSearchParams(window.parent.location.search).has('pa_token'))return;}}catch(e){{}}

  // Slow path: ask PropelAuth whether this user has an active session
  createClient({{
    authUrl:{auth_url_js},
    enableBackgroundTokenRefresh:true
  }}).getAuthenticationInfoOrNull().then(function(info){{
    if(info&&info.accessToken){{
      try{{
        localStorage.setItem('pa_token',info.accessToken);
        if(info.expiresAtSeconds){{localStorage.setItem('pa_expiry',String(info.expiresAtSeconds));}}
      }}catch(e){{}}
      applyToken(info.accessToken);
    }}else{{
      try{{localStorage.removeItem('pa_token');localStorage.removeItem('pa_expiry');}}catch(e){{}}
    }}
  }}).catch(function(e){{
    console.error('[Stocklio] PropelAuth session check failed:',e);
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
    On success, also caches the token in localStorage so inject_auth_js can
    recover the session instantly on future page loads without a network round-trip.
    """
    import streamlit.components.v1 as components

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
        # Cache in localStorage for instant cross-session recovery
        exp = payload.get("exp", 0)
        components.html(
            f"<script>try{{localStorage.setItem('pa_token',{json.dumps(token)});"
            f"localStorage.setItem('pa_expiry','{exp}');}}catch(e){{}}</script>",
            height=0,
        )
    else:
        for key in ("logged_in", "user_email", "user_id", "pa_token"):
            st.session_state.pop(key, None)


def logout() -> None:
    """Clear local session and signal inject_auth_js to clear localStorage + PropelAuth cookies."""
    for key in ("logged_in", "user_email", "user_id", "pa_token"):
        st.session_state.pop(key, None)
    st.query_params.clear()
    st.session_state["_pa_just_logged_out"] = True
