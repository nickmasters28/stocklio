"""
pages/blog.py -- Stocklio blog (accessible at /blog)

Index:    /blog
Post:     /blog?post=slug
"""

import streamlit as st
from datetime import date as _date
from blog_posts import get_all_posts, get_post_by_slug
from auth.propelauth import login_url, signup_url
from ui.ads import (
    lazy_ad_slot,
    blog_sidebar_ads,
    SLOT_BLOG_INDEX_MID,
    SLOT_BLOG_POST_AFTER_HEADER,
    SLOT_BLOG_POST_BEFORE_CTA,
    SLOT_BLOG_LEFT_SIDEBAR,
    SLOT_BLOG_RIGHT_SIDEBAR,
)

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
    section[data-testid="stSidebar"] {{ display: none !important; }}
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

    /* ── Article components ─────────────────────────────────────── */
    .bl-callout {{
        background: #f5f0e8;
        border-left: 3px solid #00a878;
        border-radius: 0 8px 8px 0;
        padding: 18px 22px;
        margin: 28px 0;
        font-style: italic;
        font-size: 1.05rem;
        line-height: 1.6;
        color: #1a202c;
        font-family: 'Georgia', serif;
    }}
    .bl-concept {{
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-top: 3px solid #00a878;
        border-radius: 0 0 8px 8px;
        padding: 20px 24px;
        margin: 28px 0;
    }}
    .bl-concept-label {{
        font-size: 0.68rem; font-weight: 700; letter-spacing: 0.1em;
        text-transform: uppercase; color: #00a878;
        margin-bottom: 8px; font-family: 'Inter', sans-serif;
    }}
    .bl-concept h3 {{ font-size: 1rem; font-weight: 600; margin: 0 0 8px; color: #1a202c; }}
    .bl-concept p {{ font-size: 0.92rem; color: #4a5568; margin: 0; line-height: 1.6; }}
    .bl-stats {{
        display: grid; grid-template-columns: repeat(3, 1fr);
        gap: 14px; margin: 28px 0;
    }}
    .bl-stat {{
        background: #ffffff; border: 1px solid #e2e8f0;
        border-radius: 8px; padding: 18px 14px; text-align: center;
    }}
    .bl-stat-num {{
        display: block; font-family: 'Georgia', serif;
        font-size: 2rem; font-weight: 700; color: #00a878;
        line-height: 1.1; margin-bottom: 6px;
    }}
    .bl-stat-lbl {{ font-size: 0.78rem; color: #6b7280; line-height: 1.4; font-family: 'Inter', sans-serif; }}
    .bl-ind-list {{ list-style: none; padding: 0; margin: 14px 0 22px; }}
    .bl-ind-item {{
        display: flex; gap: 14px; padding: 14px 0;
        border-bottom: 1px solid #e2e8f0;
    }}
    .bl-ind-item:last-child {{ border-bottom: none; }}
    .bl-ind-icon {{
        width: 30px; height: 30px; background: #e6faf5; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        flex-shrink: 0; font-size: 0.68rem; font-weight: 700;
        color: #00a878; font-family: 'Inter', sans-serif; margin-top: 2px;
        min-width: 30px;
    }}
    .bl-ind-name {{ font-weight: 600; display: block; margin-bottom: 4px; font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #1a202c; }}
    .bl-ind-desc {{ font-size: 0.87rem; color: #4a5568; line-height: 1.55; font-family: 'Inter', sans-serif; }}
    .bl-cta {{
        background: #1a6b3a; border-radius: 12px;
        padding: 32px 28px; margin: 40px 0 0;
    }}
    .bl-cta h3 {{
        font-family: 'Georgia', serif; font-size: 1.4rem;
        font-weight: 700; color: #ffffff; margin: 0 0 10px;
    }}
    .bl-cta p {{ font-size: 0.93rem; color: rgba(255,255,255,0.82); margin: 0 0 20px; line-height: 1.6; }}
    .bl-cta-btn {{
        display: inline-block; background: #ffffff; color: #1a6b3a;
        font-size: 0.88rem; font-weight: 600; padding: 9px 22px;
        border-radius: 6px; text-decoration: none; font-family: 'Inter', sans-serif;
    }}
    .bl-faq {{ margin-top: 48px; border-top: 2px solid #e2e8f0; padding-top: 36px; }}
    .bl-faq h2 {{
        font-family: 'Georgia', serif; font-size: 1.6rem;
        font-weight: 700; margin-bottom: 24px; color: #1a202c;
    }}
    .bl-faq-item {{ border-bottom: 1px solid #e2e8f0; padding: 18px 0; }}
    .bl-faq-q {{ font-weight: 600; font-size: 0.97rem; color: #1a202c; margin-bottom: 8px; font-family: 'Inter', sans-serif; }}
    .bl-faq-a {{ font-size: 0.92rem; color: #4a5568; line-height: 1.65; margin: 0; font-family: 'Inter', sans-serif; }}
    .bl-sidebar-card {{
        background: #ffffff; border: 1px solid #e2e8f0;
        border-radius: 10px; padding: 20px 18px; margin-bottom: 20px;
    }}
    .bl-sidebar-card h4 {{
        font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em;
        text-transform: uppercase; color: #6b7280;
        margin-bottom: 14px; font-family: 'Inter', sans-serif;
    }}
    .bl-toc-link {{
        display: block; font-size: 0.85rem; color: #4a5568;
        text-decoration: none; padding: 5px 0 5px 10px;
        border-left: 2px solid transparent; line-height: 1.4;
        font-family: 'Inter', sans-serif;
    }}
    .bl-toc-link:hover {{ color: #00a878; border-left-color: #00a878; }}
    .bl-related-item {{ padding: 6px 0; border-bottom: 1px solid #e2e8f0; }}
    .bl-related-item:last-child {{ border-bottom: none; }}
    .bl-related-link {{ font-size: 0.85rem; color: #00a878; text-decoration: none; font-family: 'Inter', sans-serif; line-height: 1.4; display: block; }}
    .bl-about-card {{
        background: #e6faf5; border: 1px solid #00a878;
        border-radius: 10px; padding: 20px 18px; margin-bottom: 20px;
    }}
    .bl-about-card h4 {{ color: #00a878 !important; }}
    .bl-about-card p {{ font-size: 0.85rem; color: #4a5568; line-height: 1.55; margin-bottom: 12px; font-family: 'Inter', sans-serif; }}
    .bl-about-link {{ font-size: 0.85rem; font-weight: 600; color: #00a878; text-decoration: none; font-family: 'Inter', sans-serif; }}
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


# ── Fixed left/right skyscraper ads (visible on viewports ≥ 1440px) ─────────
blog_sidebar_ads(SLOT_BLOG_LEFT_SIDEBAR, SLOT_BLOG_RIGHT_SIDEBAR)

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

        # Ad below post header — loads lazily when scrolled into view
        lazy_ad_slot(SLOT_BLOG_POST_AFTER_HEADER, height=280)

        # 2-column layout: article + sidebar
        _col_art, _col_side = st.columns([2.2, 1], gap="large")

        with _col_art:
            st.markdown(post["content"], unsafe_allow_html=True)
            lazy_ad_slot(SLOT_BLOG_POST_BEFORE_CTA, height=280)

        with _col_side:
            _toc = post.get("toc", [])
            _related = post.get("related", [])

            if _toc:
                _toc_links = "".join(
                    f'<a class="bl-toc-link" href="#">{item["text"]}</a>'
                    for item in _toc
                )
                st.markdown(
                    f'<div class="bl-sidebar-card"><h4>In This Article</h4>{_toc_links}</div>',
                    unsafe_allow_html=True,
                )

            if _related:
                _rel_items = "".join(
                    f'<div class="bl-related-item"><a class="bl-related-link" href="{item["url"]}" target="_self">{item["text"]}</a></div>'
                    for item in _related
                )
                st.markdown(
                    f'<div class="bl-sidebar-card"><h4>Related Reading</h4>{_rel_items}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("""
<div class="bl-about-card">
  <h4 class="bl-sidebar-card" style="font-size:0.68rem;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#00a878;margin-bottom:10px;font-family:Inter,sans-serif;">About Stocklio.ai</h4>
  <p>AI-powered pattern recognition for self-directed traders. Surface trend setups. Remove the bias. Act on data, not instinct.</p>
  <a class="bl-about-link" href="https://www.stocklio.ai" target="_self">Visit Stocklio.ai &rarr;</a>
</div>
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

    for _idx, post in enumerate(get_all_posts()):
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

        # Ad after every 2nd post card (0-indexed: after index 1, 3, 5, …)
        if _idx % 2 == 1:
            lazy_ad_slot(SLOT_BLOG_INDEX_MID, ad_format="auto", height=120)

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
    <div class="lp-footer-copy">
        © 2025 Stocklio · Built for investors who want an edge.
        &nbsp;·&nbsp;<a href="/privacy" style="color:#a0aec0;text-decoration:none;" onmouseover="this.style.color='#4a5568'" onmouseout="this.style.color='#a0aec0'">Privacy Policy</a>
        &nbsp;·&nbsp;<a href="/terms" style="color:#a0aec0;text-decoration:none;" onmouseover="this.style.color='#4a5568'" onmouseout="this.style.color='#a0aec0'">Terms of Service</a>
        &nbsp;·&nbsp;<a href="/cookies" style="color:#a0aec0;text-decoration:none;" onmouseover="this.style.color='#4a5568'" onmouseout="this.style.color='#a0aec0'">Cookie Policy</a>
    </div>
</div>
""", unsafe_allow_html=True)
