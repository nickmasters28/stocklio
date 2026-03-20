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

def inject_auth_js(current_params: dict = None, base_url_override: str = None) -> None:
    """
    Detect the PropelAuth session and inject ?pa_token= into the main page URL.

    Loads the PropelAuth SDK in the components.html() iframe (same-origin in
    production per the GA injection comment in app.py).  After getting the
    access token, navigates via window.parent.location.href — a write-only
    navigation that is always allowed even cross-origin — using a URL built
    entirely from Python-side values so we never need to read window.parent.location.

    current_params should be dict(st.query_params) from the caller (app.py).
    base_url_override should be the actual request host (e.g. "https://app.stocklio.ai")
    so redirects stay on the correct subdomain.
    """
    import streamlit.components.v1 as components
    import urllib.parse

    auth_url    = _auth_url()
    auth_url_js = json.dumps(auth_url)

    # Build the redirect base URL from the actual request host so that tokens
    # are injected on the correct subdomain (app. vs www.).
    base = (base_url_override or _base_url()).rstrip("/")
    safe = {k: v for k, v in (current_params or {}).items() if k != "pa_token"}
    page_path   = "/analyze" if "ticker" in safe else "/"
    redirect_base = base + page_path
    if safe:
        redirect_base += "?" + urllib.parse.urlencode(safe)
    redirect_base_js = json.dumps(redirect_base)

    # ── Logout path ─────────────────────────────────────────────────────────
    if st.session_state.pop("_pa_just_logged_out", False):
        components.html(
            # Clear localStorage only — no PropelAuth redirect to avoid 404.
            # The JWT token is removed, so /analyze will require re-authentication.
            """<script>
try{localStorage.removeItem('pa_token');localStorage.removeItem('pa_expiry');}catch(e){}
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

  // If we're on the logout landing page, clear cached tokens and bail out
  // immediately — never re-inject a token on /logged-out.
  try{{
    if(window.parent.location.pathname==='/logged-out'){{
      try{{localStorage.removeItem('pa_token');localStorage.removeItem('pa_expiry');}}catch(e){{}}
      return;
    }}
  }}catch(e){{}}

  function applyToken(token){{
    try{{localStorage.setItem('pa_token',token);}}catch(e){{}}
    // Primary: same-origin URL manipulation (preserves exact current URL)
    try{{
      var p=window.parent;
      var cur=new URLSearchParams(p.location.search);
      if(cur.has('pa_token'))return;  // already in URL — server-side callback handles it
      cur.set('pa_token',token);
      p.history.replaceState(null,'',p.location.pathname+'?'+cur.toString());
      p.location.reload();
      return;
    }}catch(e){{}}
    // Fallback: cross-origin navigate. Prefer reading the actual origin from the
    // parent frame (same-origin write is always allowed). Use Python-embedded
    // redirectBase only if the origin read somehow fails.
    try{{
      var _origin=window.parent.location.origin;
      var _path=window.parent.location.pathname;
      var _search=window.parent.location.search;
      var _cur2=new URLSearchParams(_search);
      _cur2.set('pa_token',token);
      window.parent.location.href=_origin+_path+'?'+_cur2.toString();
      return;
    }}catch(e){{}}
    var sep=redirectBase.indexOf('?')>=0?'&':'?';
    window.parent.location.href=redirectBase+sep+'pa_token='+encodeURIComponent(token);
  }}

  // pa_token already in parent URL — handle_auth_callback() will process it
  // Must come BEFORE fast path so localStorage token never triggers applyToken when URL already has token
  try{{if(new URLSearchParams(window.parent.location.search).has('pa_token'))return;}}catch(e){{}}

  // Fast path: valid token cached in localStorage
  try{{
    var stored=localStorage.getItem('pa_token');
    var expiry=parseInt(localStorage.getItem('pa_expiry')||'0');
    if(stored&&expiry>Math.floor(Date.now()/1000)){{applyToken(stored);return;}}
  }}catch(e){{}}

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
        import sys; print("[propelauth] token expired", file=sys.stderr)
        return None
    except jwt.InvalidTokenError as e:
        import sys; print(f"[propelauth] invalid token: {e}", file=sys.stderr)
        return None


def handle_auth_callback() -> None:
    """
    Read ?pa_token from the URL, validate it, and populate session state.
    Call this once at the top of every page render (before rendering content).
    On success, also caches the token in localStorage so inject_auth_js can
    recover the session instantly on future page loads without a network round-trip.
    """
    import streamlit.components.v1 as components

    # Skip token processing entirely during the logout flow so a stale or
    # PropelAuth-issued pa_token in the URL cannot re-authenticate the user.
    if st.session_state.pop("_pa_skip_auth", False):
        st.query_params.pop("pa_token", None)
        return

    token = st.query_params.get("pa_token")
    if not token:
        return

    # Already validated this exact token — skip
    if st.session_state.get("pa_token") == token:
        return

    payload = _validate_token(token)
    if payload:
        user_id = payload.get("user_id", "")
        st.session_state["logged_in"]   = True
        st.session_state["user_email"]  = payload.get("email", "")
        st.session_state["user_id"]     = user_id
        st.session_state["pa_token"]    = token

        # Fetch subscription tier from Supabase. Falls back to "free" on any error.
        try:
            from data.stripe_billing import get_subscription_tier
            tier = get_subscription_tier(user_id)
        except Exception:
            tier = "free"
        st.session_state["subscription_tier"] = tier
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


def is_paid_user() -> bool:
    """
    Returns True if the current session has an active paid subscription.
    On localhost, defaults to True for easier local development unless
    session state has 'dev_force_free' set to True.
    """
    # Allow overriding paid status on localhost for testing free UX
    if st.session_state.get("dev_force_free", False):
        return False
    try:
        _host = st.context.headers.get("host", "")
        if _host.startswith("localhost") or _host.startswith("127.0.0.1"):
            return True
    except Exception:
        pass
    tier = st.session_state.get("subscription_tier", "free")
    return tier in ("pro", "premium", "enterprise")


def logout() -> None:
    """Clear local session and signal inject_auth_js to clear localStorage + PropelAuth cookies."""
    for key in ("logged_in", "user_email", "user_id", "pa_token"):
        st.session_state.pop(key, None)
    st.query_params.clear()
    st.session_state["_pa_just_logged_out"] = True
    st.session_state["_pa_skip_auth"] = True  # block handle_auth_callback on the next render
