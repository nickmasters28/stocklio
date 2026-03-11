"""
pages/cookies.py -- Stocklio Cookie Policy (accessible at /cookies)
"""

import streamlit as st
from auth.propelauth import login_url, signup_url

_login_url  = login_url()
_signup_url = signup_url()

st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Darker Grotesque:wght@700;800;900&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
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
.lp-nav {{ display:flex; align-items:center; justify-content:space-between; padding:20px 0 16px 0; border-bottom:1px solid #e2e8f0; }}
.lp-logo {{ font-family:'Darker Grotesque',sans-serif; font-size:5rem; font-weight:800; color:#1a202c !important; letter-spacing:-0.01em; line-height:1; text-decoration:none !important; }}
.lp-logo-dot {{ color:#00c896; }}
.lp-nav-links {{ display:flex; gap:12px; align-items:center; }}
.lp-btn {{ display:inline-block; padding:8px 20px; border-radius:8px; font-family:'Inter',sans-serif; font-size:0.85rem; font-weight:600; text-decoration:none !important; cursor:pointer; }}
.lp-btn-outline {{ border:1px solid #cbd5e0; color:#1a202c; background:#ffffff; }}
.lp-btn-primary {{ background:#00c896; color:#ffffff !important; border:1px solid #00c896; }}
.legal-wrap {{ max-width:800px; margin:48px auto 0 auto; font-family:'Inter',sans-serif; color:#1a202c; }}
.legal-eyebrow {{ font-size:0.78rem; font-weight:600; color:#00a878; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:10px; }}
.legal-h1 {{ font-family:'Darker Grotesque',sans-serif; font-size:2.6rem; font-weight:900; color:#1a202c; letter-spacing:-0.02em; margin:0 0 8px 0; line-height:1.1; }}
.legal-meta {{ font-size:0.82rem; color:#6b7280; margin-bottom:36px; border-bottom:1px solid #e2e8f0; padding-bottom:24px; }}
.legal-h2 {{ font-family:'Darker Grotesque',sans-serif; font-size:1.4rem; font-weight:800; color:#1a202c; margin:36px 0 10px 0; letter-spacing:-0.01em; }}
.legal-body {{ font-size:0.92rem; color:#4a5568; line-height:1.75; margin-bottom:0; }}
.legal-body ul {{ padding-left:20px; margin:10px 0; }}
.legal-body li {{ margin-bottom:6px; }}
.legal-body a {{ color:#00a878; text-decoration:none; }}
.legal-body a:hover {{ text-decoration:underline; }}
.cookie-table {{ width:100%; border-collapse:collapse; font-family:'Inter',sans-serif; font-size:0.85rem; margin:16px 0 0 0; }}
.cookie-table th {{ background:#f0f4f8; color:#4a5568; font-weight:600; padding:10px 14px; text-align:left; border-bottom:2px solid #e2e8f0; }}
.cookie-table td {{ padding:10px 14px; border-bottom:1px solid #e2e8f0; color:#4a5568; vertical-align:top; }}
.cookie-table tr:last-child td {{ border-bottom:none; }}
.cookie-table td:first-child {{ font-weight:600; color:#1a202c; white-space:nowrap; }}
.ck-badge {{ display:inline-block; padding:2px 8px; border-radius:4px; font-size:0.72rem; font-weight:600; }}
.ck-essential {{ background:#e6faf5; color:#00a878; }}
.ck-analytics {{ background:#ebf4ff; color:#3182ce; }}
.lp-footer {{ padding:32px 0 36px 0; font-family:'Inter',sans-serif; font-size:0.8rem; color:#a0aec0; border-top:1px solid #e2e8f0; margin-top:56px; display:flex; justify-content:space-between; align-items:flex-start; }}
.lp-footer-copy {{ color:#a0aec0; }}
.lp-footer-section-title {{ font-family:'Inter',sans-serif; font-size:0.72rem; font-weight:600; color:#6b7280; text-transform:uppercase; letter-spacing:0.06em; margin-bottom:8px; }}
.lp-footer-link {{ display:block; font-family:'Inter',sans-serif; font-size:0.82rem; color:#a0aec0; text-decoration:none !important; margin-bottom:4px; }}
.lp-footer-link:hover {{ color:#4a5568; }}
</style>
<div class="lp-nav">
<a href="/" class="lp-logo" target="_self">stocklio<span class="lp-logo-dot">.</span></a>
<div class="lp-nav-links">
<a href="/blog" class="lp-btn lp-btn-outline">Blog</a>
<a href="{_login_url}" class="lp-btn lp-btn-outline">Log in</a>
<a href="{_signup_url}" class="lp-btn lp-btn-primary">Sign up free</a>
</div>
</div>
<div class="legal-wrap">
<div class="legal-eyebrow">Legal</div>
<h1 class="legal-h1">Cookie Policy</h1>
<div class="legal-meta">Effective date: March 1, 2025 &nbsp;·&nbsp; Last updated: March 1, 2025 &nbsp;·&nbsp; Operated by Stocklio (Boston, Massachusetts, USA)</div>
<div class="legal-h2">1. What Are Cookies?</div>
<div class="legal-body">Cookies are small text files placed on your device when you visit a website. They are widely used to make websites work more efficiently, remember your preferences, and provide reporting information to site operators.<br><br>Cookies may be "session cookies" (deleted when you close your browser) or "persistent cookies" (remain on your device for a set period). Cookies set by the website you are visiting are called "first-party cookies." Cookies set by other organizations are called "third-party cookies."</div>
<div class="legal-h2">2. How Stocklio Uses Cookies</div>
<div class="legal-body">We use cookies to:
<ul>
<li>Keep you securely logged in to your account</li>
<li>Remember your session preferences and recent searches</li>
<li>Measure how users navigate and interact with the platform (analytics)</li>
<li>Support future advertising features (see Section 5)</li>
</ul>
We do not use cookies to build advertising profiles, sell your data, or track you across unrelated third-party websites beyond the services described below.</div>
<div class="legal-h2">3. Cookies We Use</div>
<div class="legal-body">The table below describes the specific cookies currently set on Stocklio:
<table class="cookie-table">
<thead>
<tr><th>Cookie Name</th><th>Provider</th><th>Type</th><th>Purpose</th><th>Duration</th></tr>
</thead>
<tbody>
<tr>
<td>__pa_session</td>
<td>PropelAuth</td>
<td><span class="ck-badge ck-essential">Essential</span></td>
<td>Maintains your authenticated session so you remain logged in while navigating the site.</td>
<td>Session / 30 days</td>
</tr>
<tr>
<td>__pa_refresh</td>
<td>PropelAuth</td>
<td><span class="ck-badge ck-essential">Essential</span></td>
<td>Refresh token used to renew your session without requiring you to log in again.</td>
<td>30 days</td>
</tr>
<tr>
<td>_ga</td>
<td>Google Analytics</td>
<td><span class="ck-badge ck-analytics">Analytics</span></td>
<td>Registers a unique ID to generate statistical data on how you use the site.</td>
<td>2 years</td>
</tr>
<tr>
<td>_ga_*</td>
<td>Google Analytics</td>
<td><span class="ck-badge ck-analytics">Analytics</span></td>
<td>Used to persist session state for Google Analytics 4 (GA4) measurement.</td>
<td>2 years</td>
</tr>
<tr>
<td>_gid</td>
<td>Google Analytics</td>
<td><span class="ck-badge ck-analytics">Analytics</span></td>
<td>Registers a unique ID to generate statistical data on how you use the site. Expires quickly.</td>
<td>24 hours</td>
</tr>
</tbody>
</table>
</div>
<div class="legal-h2">4. Essential Cookies</div>
<div class="legal-body">Essential (or "strictly necessary") cookies are required for the basic functioning of Stocklio. These include cookies that enable secure login, session management, and fraud prevention. You cannot opt out of essential cookies if you wish to use the Service. They do not store personally identifiable information beyond what is necessary for authentication.</div>
<div class="legal-h2">5. Analytics Cookies</div>
<div class="legal-body">We use Google Analytics 4 to understand how visitors interact with Stocklio — for example, which pages are most visited, how long users spend on each feature, and where users come from. This helps us improve the platform.<br><br>Google Analytics places cookies (<code>_ga</code>, <code>_ga_*</code>, <code>_gid</code>) on your device. The data collected is anonymized before being sent to Google's servers and does not directly identify you. We have configured Google Analytics with IP anonymization enabled.<br><br>You can opt out of Google Analytics tracking at any time by:
<ul>
<li>Installing the <a href="https://tools.google.com/dlpage/gaoptout" target="_blank">Google Analytics Opt-out Browser Add-on</a></li>
<li>Using your browser's built-in privacy or incognito mode</li>
<li>Adjusting your browser settings to block third-party cookies</li>
</ul></div>
<div class="legal-h2">6. Future Advertising Cookies (Google AdSense)</div>
<div class="legal-body">We currently do not serve advertising on Stocklio. We intend to enable Google AdSense display advertising in the future. When advertising is enabled, Google may use additional cookies to serve relevant ads, limit ad frequency, and measure campaign effectiveness.<br><br><strong>We will update this Cookie Policy and provide an opt-out mechanism before enabling any advertising cookies.</strong><br><br>When advertising is active, you will be able to opt out of personalized ads via <a href="https://adssettings.google.com" target="_blank">Google Ad Settings</a> or the <a href="http://optout.aboutads.info/" target="_blank">Digital Advertising Alliance opt-out tool</a>.</div>
<div class="legal-h2">7. Local Storage and Session Storage</div>
<div class="legal-body">In addition to cookies, Stocklio may use your browser's local storage or session storage to save lightweight preferences (such as sidebar state during a session). This data is stored entirely on your device and is not transmitted to our servers. Session storage is cleared automatically when you close your browser tab.</div>
<div class="legal-h2">8. Managing and Deleting Cookies</div>
<div class="legal-body">You can control and manage cookies in your browser settings. Most browsers allow you to view and delete existing cookies, block all cookies, or block only third-party cookies. Instructions for popular browsers:
<ul>
<li><a href="https://support.google.com/chrome/answer/95647" target="_blank">Google Chrome</a></li>
<li><a href="https://support.mozilla.org/en-US/kb/cookies-information-websites-store-on-your-computer" target="_blank">Mozilla Firefox</a></li>
<li><a href="https://support.apple.com/guide/safari/manage-cookies-sfri11471/mac" target="_blank">Apple Safari</a></li>
<li><a href="https://support.microsoft.com/en-us/microsoft-edge/delete-cookies-in-microsoft-edge-63947406-40ac-c3b8-57b9-2a946a29ae09" target="_blank">Microsoft Edge</a></li>
</ul>
Please be aware that blocking essential cookies will prevent you from logging into your Stocklio account.</div>
<div class="legal-h2">9. Do Not Track</div>
<div class="legal-body">Some browsers include a "Do Not Track" (DNT) feature. Because there is no consistent industry standard for responding to DNT signals, Stocklio does not currently alter its data collection practices based on DNT signals.</div>
<div class="legal-h2">10. Changes to This Policy</div>
<div class="legal-body">We may update this Cookie Policy from time to time, particularly before enabling any advertising cookies. The "Last updated" date at the top of this page reflects the most recent revision.</div>
<div class="legal-h2">11. Governing Law</div>
<div class="legal-body">This Cookie Policy is governed by the laws of the Commonwealth of Massachusetts, USA.</div>
<div class="legal-h2">Contact</div>
<div class="legal-body" style="margin-bottom:48px;"><strong>Stocklio</strong><br>Boston, Massachusetts, USA<br><a href="mailto:hello@stocklio.ai">hello@stocklio.ai</a><br><br>See also: <a href="/privacy" target="_self">Privacy Policy</a> &nbsp;·&nbsp; <a href="/terms" target="_self">Terms of Service</a></div>
</div>
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
