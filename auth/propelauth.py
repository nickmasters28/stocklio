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
    Detect the PropelAuth session and inject ?pa_token= into the main page URL.

    Uses window.parent.document.createElement('script') — the same pattern as the
    GA injection in app.py — so PropelAuth runs in the MAIN PAGE context, not inside
    the iframe. This means:
      - CORS requests to auth.stocklio.ai originate from app.stocklio.ai (correct origin)
      - window.location / history / localStorage all refer to the main page directly
      - No cross-origin URL-reading issues

    Two-path approach:
    1. Fast path (iframe): check main-page localStorage for a cached unexpired token;
       if found, inject into URL immediately without a network round-trip.
    2. Slow path (main page): inject PropelAuth SDK into parent document, call
       getAuthenticationInfoOrNull(), cache token in localStorage, inject into URL.

    Logout: clear localStorage in both contexts, remove injected script element so it
    can be re-injected on next login, call PropelAuth.logout() to clear the session.
    """
    import streamlit.components.v1 as components
    auth_url = _auth_url()
    auth_url_js = json.dumps(auth_url)
    sdk_url_js  = json.dumps(
        "https://cdn.jsdelivr.net/npm/@propelauth/javascript@2/dist/propelauth.js"
    )

    # ── Logout path ─────────────────────────────────────────────────────────
    # Render different JS content to force Streamlit to recreate the iframe.
    if st.session_state.pop("_pa_just_logged_out", False):
        components.html(
            f"""<script src="https://cdn.jsdelivr.net/npm/@propelauth/javascript@2/dist/propelauth.js"></script>
<script>
(function(){{
  // Clear iframe localStorage
  try{{localStorage.removeItem('pa_token');localStorage.removeItem('pa_expiry');}}catch(e){{}}
  // Clear parent localStorage and remove injected SDK script so it re-runs on next login
  try{{
    var p=window.parent;
    p.localStorage.removeItem('pa_token');
    p.localStorage.removeItem('pa_expiry');
    var el=p.document.getElementById('_pa_sdk');
    if(el)el.parentNode.removeChild(el);
  }}catch(e){{}}
  // Invalidate the PropelAuth session server-side
  try{{
    PropelAuth.createClient({{authUrl:{auth_url_js},enableBackgroundTokenRefresh:false}}).logout(false);
  }}catch(e){{}}
}})();
</script>""",
            height=0,
        )
        return

    # ── Build the script that runs in the MAIN PAGE context ─────────────────
    # Plain string concatenation (no f-string) keeps JS braces literal.
    parent_js = (
        "(function(){"
        "var s=document.createElement('script');"
        "s.id='_pa_sdk';"
        "s.src=" + sdk_url_js + ";"
        "s.onload=function(){"
          "PropelAuth.createClient({authUrl:" + auth_url_js + ",enableBackgroundTokenRefresh:true})"
          ".getAuthenticationInfoOrNull().then(function(info){"
            "var cur=new URLSearchParams(window.location.search);"
            "if(info&&info.accessToken){"
              "try{"
                "localStorage.setItem('pa_token',info.accessToken);"
                "if(info.expiresAtSeconds){"
                  "localStorage.setItem('pa_expiry',String(info.expiresAtSeconds));"
                "}"
              "}catch(e){}"
              "if(!cur.has('pa_token')){"
                "cur.set('pa_token',info.accessToken);"
                "window.history.replaceState(null,'',window.location.pathname+'?'+cur.toString());"
                "window.location.reload();"
              "}"
            "}else{"
              "try{localStorage.removeItem('pa_token');localStorage.removeItem('pa_expiry');}catch(e){}"
              "if(cur.has('pa_token')){"
                "cur.delete('pa_token');"
                "window.history.replaceState(null,'',window.location.pathname+'?'+cur.toString());"
              "}"
            "}"
          "});"
        "};"
        "document.head.appendChild(s);"
        "})()"
    )

    components.html(
        f"""<script>
(function(){{
  var p=(window.parent&&window.parent!==window)?window.parent:window;
  try{{
    // Avoid double-init if the SDK script is already in the parent document
    if(p.document.getElementById('_pa_sdk'))return;

    var cur=new URLSearchParams(p.location.search);

    // Fast path A: pa_token already in URL — handle_auth_callback() will process it
    if(cur.has('pa_token'))return;

    // Fast path B: valid token cached in main-page localStorage
    var stored=p.localStorage.getItem('pa_token');
    var expiry=parseInt(p.localStorage.getItem('pa_expiry')||'0');
    if(stored&&expiry>Math.floor(Date.now()/1000)){{
      cur.set('pa_token',stored);
      p.history.replaceState(null,'',p.location.pathname+'?'+cur.toString());
      p.location.reload();
      return;
    }}

    // Slow path: inject PropelAuth SDK into main page document
    var el=p.document.createElement('script');
    el.id='_pa_sdk_init';
    el.textContent={json.dumps(parent_js)};
    p.document.head.appendChild(el);
  }}catch(e){{/* window.parent.document access blocked */}}
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
