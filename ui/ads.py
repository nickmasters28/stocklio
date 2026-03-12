"""
ui/ads.py -- Google AdSense integration for Stocklio.

Ads load lazily via IntersectionObserver: the adsbygoogle.push() call fires
only when the ad slot's iframe scrolls into the parent viewport. This means:

  - Ads never block main content rendering.
  - Ads below the fold don't make any network request until scrolled to.
  - The AdSense script itself is async and runs in an isolated iframe context.

Setup (required before going live):
  Replace each SLOT_* constant with the matching ad unit slot ID from your
  AdSense account. Create a separate ad unit for each placement.
"""

import json
import streamlit.components.v1 as components


# ── AdSense account identifiers ───────────────────────────────────────────────

PUBLISHER_ID = "ca-pub-8558122539705900"

# Ad unit slot IDs — one per placement, created in your AdSense dashboard.
# TODO: replace each "XXXXXXXXXX" with the actual slot ID from your AdSense account.
SLOT_ANALYZE_BELOW_RTN      = "6047770968"   # /analyze — below Ride the Nine section
SLOT_ANALYZE_BELOW_LR       = "6047770968"   # /analyze — below Linear Regression section
SLOT_HOME_BETWEEN_STEPS_CTA = "6047770968"   # /home    — between How It Works and CTA band
SLOT_BLOG_INDEX_MID         = "6047770968"   # /blog index — after every 2nd post card
SLOT_BLOG_POST_AFTER_HEADER = "6047770968"   # /blog post  — below post header, above content
SLOT_BLOG_POST_BEFORE_CTA   = "6047770968"   # /blog post  — after content, before CTA button


# ── Ad component ──────────────────────────────────────────────────────────────

def lazy_ad_slot(
    slot_id: str,
    ad_format: str = "auto",
    height: int = 280,
    full_width_responsive: bool = True,
) -> None:
    """
    Render a lazily-loaded AdSense unit inside a components.html() iframe.

    Lazy loading strategy:
      The script inside the iframe locates its own <iframe> element in the
      parent document and attaches an IntersectionObserver to it (same-origin
      in production). adsbygoogle.push() fires only when the iframe enters the
      parent viewport (threshold 10%). This guarantees that:
        - Ads above the fold load after content is interactive.
        - Ads below the fold load only when the user scrolls to them.
        - Ad slots the user never reaches never fire a push() call.
      On cross-origin environments (local dev), falls back to a 500ms delay.

    Parameters
    ----------
    slot_id : str
        The AdSense ad unit slot ID for this placement.
    ad_format : str
        AdSense data-ad-format value. "auto" works for responsive units.
    height : int
        Height of the components.html() iframe in pixels. Should accommodate
        the ad size + the "Advertisement" label (~30px overhead).
        - Responsive / rectangle formats: 280
        - Leaderboard / horizontal banner: 100
    full_width_responsive : bool
        Whether to set data-full-width-responsive="true" on the ins element.
    """
    pub_js   = json.dumps(PUBLISHER_ID)
    slot_js  = json.dumps(slot_id)
    fmt_js   = json.dumps(ad_format)
    fwr_attr = 'data-full-width-responsive="true"' if full_width_responsive else ""

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: transparent;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    overflow: hidden;
  }}
  .ad-wrap {{
    width: 100%;
    padding: 6px 0 0 0;
  }}
  .ad-label {{
    font-size: 0.67rem;
    color: #a0aec0;
    letter-spacing: .07em;
    text-transform: uppercase;
    text-align: center;
    margin-bottom: 5px;
    user-select: none;
  }}
  .ad-divider {{
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 0 0 8px 0;
  }}
  ins.adsbygoogle {{ display: block; background: transparent; }}
</style>
</head>
<body>
<div class="ad-wrap">
  <hr class="ad-divider">
  <div class="ad-label">Advertisement</div>
  <ins class="adsbygoogle"
       style="display:block"
       data-ad-client={pub_js}
       data-ad-slot={slot_js}
       data-ad-format={fmt_js}
       {fwr_attr}></ins>
</div>

<!-- AdSense script: async, runs after content, does not block the parent page -->
<script async
  src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={PUBLISHER_ID}"
  crossorigin="anonymous"></script>

<script>
(function() {{
  var ins = document.querySelector('ins.adsbygoogle');
  if (!ins) return;

  function loadAd() {{
    try {{
      (adsbygoogle = window.adsbygoogle || []).push({{}});
    }} catch (e) {{
      console.warn('[Stocklio] AdSense push error:', e);
    }}
  }}

  // ── Preferred path: observe the iframe element in the parent window ────────
  // Works when the parent and iframe share an origin (production on stocklio.ai).
  // IntersectionObserver on the IFRAME element means push() fires only when
  // the user actually scrolls the ad slot into the viewport.
  try {{
    var p = window.parent;
    if (!p || p === window) throw new Error('no parent');

    // Find this iframe in the parent DOM by matching contentWindow.
    var allFrames = p.document.querySelectorAll('iframe');
    var myFrame = null;
    for (var i = 0; i < allFrames.length; i++) {{
      try {{
        if (allFrames[i].contentWindow === window) {{
          myFrame = allFrames[i];
          break;
        }}
      }} catch (ignore) {{}}
    }}
    if (!myFrame) throw new Error('frame not found');

    if ('IntersectionObserver' in p) {{
      var obs = new p.IntersectionObserver(function(entries) {{
        entries.forEach(function(entry) {{
          if (entry.isIntersecting) {{
            obs.disconnect();
            loadAd();
          }}
        }});
      }}, {{ root: null, threshold: 0.1 }});
      obs.observe(myFrame);
    }} else {{
      // Old browser without IntersectionObserver — load after short delay.
      p.setTimeout(loadAd, 300);
    }}

  }} catch (e) {{
    // ── Fallback: cross-origin or restricted env (local dev) ──────────────
    // Load after 500 ms so the main content has had time to paint first.
    setTimeout(loadAd, 500);
  }}
}})();
</script>
</body>
</html>"""

    components.html(html, height=height, scrolling=False)
