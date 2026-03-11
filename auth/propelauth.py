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

def inject_auth_js() -> None:
    """
    Inject the PropelAuth JS client into the page via components.html().

    Two-path approach:
    1. Fast path: check localStorage for a previously-validated token. If found
       and not expired, inject it into the URL immediately — no network round-trip.
    2. Slow path: ask PropelAuth's JS client (cross-domain cookie/session check).
       If a session exists, store the token in localStorage for future fast-path
       use, then inject into the URL.

    On logout (_pa_just_logged_out session flag), a different iframe is rendered
    that clears localStorage and calls PropelAuth.logout() before exiting.
    """
    import streamlit.components.v1 as components
    auth_url = _auth_url()

    # On logout: clear localStorage + PropelAuth cookies, then stop.
    # Different JS content forces Streamlit to recreate the iframe.
    if st.session_state.pop("_pa_just_logged_out", False):
        components.html(
            f"""<script src="https://cdn.jsdelivr.net/npm/@propelauth/javascript@2/dist/propelauth.js"></script>
<script>
(function(){{
  try{{localStorage.removeItem('pa_token');localStorage.removeItem('pa_expiry');}}catch(e){{}}
  try{{
    PropelAuth.createClient({{authUrl:"{auth_url}",enableBackgroundTokenRefresh:false}}).logout(false);
  }}catch(e){{}}
}})();
</script>""",
            height=0,
        )
        return

    components.html(
        f"""<script src="https://cdn.jsdelivr.net/npm/@propelauth/javascript@2/dist/propelauth.js"></script>
<script>
(function(){{
  if(window.__paInit)return;
  window.__paInit=true;
  var win=(window.parent&&window.parent!==window)?window.parent:window;

  function injectToken(token){{
    try{{
      var cur=new URLSearchParams(win.location.search);
      if(!cur.has('pa_token')){{
        cur.set('pa_token',token);
        win.history.replaceState(null,'',win.location.pathname+'?'+cur.toString());
        win.location.reload();
      }}
    }}catch(e){{/* cross-origin — silently skip */}}
  }}

  // Fast path: use token cached in localStorage (instant, no network)
  try{{
    var stored=localStorage.getItem('pa_token');
    var expiry=parseInt(localStorage.getItem('pa_expiry')||'0');
    var now=Math.floor(Date.now()/1000);
    if(stored&&expiry>now){{
      injectToken(stored);
      return;
    }}
  }}catch(e){{}}

  // Slow path: ask PropelAuth (cross-domain cookie check, async)
  PropelAuth.createClient({{
    authUrl:"{auth_url}",
    enableBackgroundTokenRefresh:true
  }}).getAuthenticationInfoOrNull().then(function(info){{
    try{{
      var cur=new URLSearchParams(win.location.search);
      if(info&&info.accessToken){{
        try{{
          localStorage.setItem('pa_token',info.accessToken);
          if(info.expiresAtSeconds){{
            localStorage.setItem('pa_expiry',String(info.expiresAtSeconds));
          }}
        }}catch(e){{}}
        if(!cur.has('pa_token')){{
          cur.set('pa_token',info.accessToken);
          win.history.replaceState(null,'',win.location.pathname+'?'+cur.toString());
          win.location.reload();
        }}
      }}else{{
        try{{localStorage.removeItem('pa_token');localStorage.removeItem('pa_expiry');}}catch(e){{}}
        if(cur.has('pa_token')){{
          cur.delete('pa_token');
          win.history.replaceState(null,'',win.location.pathname+'?'+cur.toString());
        }}
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
