"""
pages/blog.py -- Stocklio blog (accessible at /blog)

Index:    /blog
Post:     /blog?post=slug
"""

import streamlit as st
from datetime import date as _date
from blog_posts import get_all_posts, get_post_by_slug
from auth.propelauth import login_url, signup_url

# st.set_page_config, inject_auth_js, handle_auth_callback are handled by app.py shell

_login_url  = login_url()
_signup_url = signup_url()

_post_slug = st.query_params.get("post", "")

# ── Shared CSS + Nav ─────────────────────────────────────────────────────────

st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Darker+Grotesque:wght@700;800;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    .stApp {{ background-color: #f5f7fa; }}
    .block-container {{ padding-top: 1rem !important; padding-bottom: 0 !important; max-width: 1100px; }}
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarHeader"] > button,
    button[aria-label*="keyboard" i],
    button[title*="keyboard" i],
    [data-testid="stToolbar"],
    [data-testid="stHeaderActionElements"] {{ display: none !important; }}

    .lp-nav {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 20px 0 16px 0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 0;
    }}
    .lp-logo {{
        font-family: 'Darker Grotesque', sans-serif;
        font-size: 5rem;
        font-weight: 800;
        color: #1a202c;
        letter-spacing: -0.01em;
        line-height: 1;
        text-decoration: none !important;
    }}
    .lp-logo-dot {{ color: #00c896; }}
    .lp-nav-links {{ display: flex; gap: 12px; align-items: center; }}
    .lp-btn {{
        display: inline-block;
        padding: 8px 20px;
        border-radius: 8px;
        font-family: 'Inter', sans-serif;
        font-size: 0.85rem;
        font-weight: 600;
        text-decoration: none !important;
        cursor: pointer;
    }}
    .lp-btn-outline {{ border: 1px solid #cbd5e0; color: #1a202c; background: #ffffff; }}
    .lp-btn-primary {{ background: #00c896; color: #ffffff !important; border: 1px solid #00c896; }}

    /* Blog index cards */
    .blog-card {{
        background: #ffffff;
        border-radius: 14px;
        padding: 28px 28px 24px 28px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }}
    .blog-card-tags {{
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
        margin-bottom: 10px;
    }}
    .blog-tag {{
        display: inline-block;
        background: #e6faf5;
        color: #00a878;
        border-radius: 6px;
        padding: 2px 10px;
        font-family: 'Inter', sans-serif;
        font-size: 0.72rem;
        font-weight: 600;
    }}
    .blog-card-title {{
        font-family: 'Darker Grotesque', sans-serif;
        font-size: 1.5rem;
        font-weight: 800;
        color: #1a202c;
        margin: 0 0 6px 0;
        letter-spacing: -0.01em;
        line-height: 1.2;
    }}
    .blog-card-meta {{
        font-family: 'Inter', sans-serif;
        font-size: 0.78rem;
        color: #6b7280;
        margin-bottom: 10px;
    }}
    .blog-card-excerpt {{
        font-family: 'Inter', sans-serif;
        font-size: 0.92rem;
        color: #4a5568;
        line-height: 1.65;
        margin-bottom: 0;
    }}

    /* Post view */
    .blog-post-header {{
        padding: 40px 0 32px 0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 36px;
    }}
    .blog-post-title {{
        font-family: 'Darker Grotesque', sans-serif;
        font-size: 2.8rem;
        font-weight: 900;
        color: #1a202c;
        letter-spacing: -0.02em;
        line-height: 1.1;
        margin: 12px 0 14px 0;
    }}
    .blog-post-meta {{
        font-family: 'Inter', sans-serif;
        font-size: 0.82rem;
        color: #6b7280;
    }}

    /* Footer */
    .lp-footer {{
        padding: 32px 0 36px 0;
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #a0aec0;
        border-top: 1px solid #e2e8f0;
        margin-top: 56px;
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
    }}
    .lp-footer-copy {{ color: #a0aec0; }}
    .lp-footer-section-title {{
        font-family: 'Inter', sans-serif;
        font-size: 0.72rem;
        font-weight: 600;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 8px;
    }}
    .lp-footer-link {{
        display: block;
        font-family: 'Inter', sans-serif;
        font-size: 0.8rem;
        color: #a0aec0;
        text-decoration: none !important;
        margin-bottom: 4px;
    }}
    .lp-footer-link:hover {{ color: #4a5568; }}
</style>

<!-- Nav -->
<div class="lp-nav">
    <a href="/" class="lp-logo" style="text-decoration:none;color:#1a202c;">stocklio<span class="lp-logo-dot">.</span></a>
    <div class="lp-nav-links">
        <a href="{_login_url}" class="lp-btn lp-btn-outline">Log in</a>
        <a href="{_signup_url}" class="lp-btn lp-btn-primary">Sign up free</a>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Router ───────────────────────────────────────────────────────────────────

def _fmt_date(iso: str) -> str:
    return _date.fromisoformat(iso).strftime("%B %-d, %Y")


if _post_slug:
    # ── Individual post view ─────────────────────────────────────────────────
    post = get_post_by_slug(_post_slug)

    if post is None:
        st.error("Post not found.")
        if st.button("← Back to Blog"):
            st.query_params.clear()
            st.rerun()
    else:
        tags_html = "".join(f'<span class="blog-tag">{t}</span>' for t in post["tags"])

        st.markdown(f"""
        <div class="blog-post-header">
            <div class="blog-card-tags">{tags_html}</div>
            <div class="blog-post-title">{post["title"]}</div>
            <div class="blog-post-meta">{_fmt_date(post["date"])} &nbsp;·&nbsp; {post["author"]}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("← Back to Blog"):
            st.query_params.clear()
            st.rerun()

        st.markdown(post["content"])

        st.markdown("""
<hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0 20px 0;">
<p style='font-family:Inter,sans-serif;font-size:0.9rem;color:#4a5568;margin-bottom:14px;'>
    Ready to apply these insights? Analyze any stock on Stocklio.
</p>
<a href="/analyze?ticker=NVDA" target="_self"
   style="display:inline-block;background:#00c896;color:#ffffff;text-decoration:none;
          font-family:'Inter',sans-serif;font-size:0.9rem;font-weight:600;
          padding:10px 22px;border-radius:8px;">
    Open Stock Analyzer →
</a>
""", unsafe_allow_html=True)

else:
    # ── Blog index ───────────────────────────────────────────────────────────
    st.markdown("""
    <div style="padding:40px 0 32px 0;">
        <div style="font-family:'Inter',sans-serif;font-size:0.78rem;font-weight:600;color:#00a878;
                    text-transform:uppercase;letter-spacing:0.06em;margin-bottom:8px;">
            Stocklio Blog
        </div>
        <h1 style="font-family:'Darker Grotesque',sans-serif;font-size:2.8rem;font-weight:900;
                   color:#1a202c;letter-spacing:-0.02em;margin:0 0 10px 0;">
            Insights for smarter trading.
        </h1>
        <p style="font-family:'Inter',sans-serif;font-size:1rem;color:#6b7280;max-width:540px;line-height:1.6;margin:0;">
            Strategy breakdowns, indicator guides, and market psychology — written for
            individual investors who want a real edge.
        </p>
    </div>
    """, unsafe_allow_html=True)

    for post in get_all_posts():
        tags_html = "".join(f'<span class="blog-tag">{t}</span>' for t in post["tags"])

        st.markdown(f"""
        <div class="blog-card">
            <div class="blog-card-tags">{tags_html}</div>
            <div class="blog-card-title">{post["title"]}</div>
            <div class="blog-card-meta">{_fmt_date(post["date"])} &nbsp;·&nbsp; {post["author"]}</div>
            <div class="blog-card-excerpt">{post["excerpt"]}</div>
        </div>
        """, unsafe_allow_html=True)

        # Native Streamlit button so navigation is guaranteed to work
        if st.button(f"Read article →", key=f"read_{post['slug']}"):
            st.query_params["post"] = post["slug"]
            st.rerun()

        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

st.markdown(f"""
<div class="lp-footer" style="flex-direction:column;gap:16px;">
    <div style="display:flex;justify-content:flex-end;width:100%;">
        <div>
            <div class="lp-footer-section-title">Resources</div>
            <a href="/blog" class="lp-footer-link">Blog</a>
            <a href="{_signup_url}" class="lp-footer-link">Create an account</a>
            <a href="{_login_url}" class="lp-footer-link">Log in</a>
            <a href="mailto:hello@stocklio.ai" class="lp-footer-link">hello@stocklio.ai</a>
        </div>
    </div>
    <div class="lp-footer-copy">© 2025 Stocklio · Built for investors who want an edge.</div>
</div>
""", unsafe_allow_html=True)
