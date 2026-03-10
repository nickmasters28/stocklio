"""
pages/privacy.py -- Stocklio Privacy Policy (accessible at /privacy)
"""

import streamlit as st
from auth.propelauth import login_url, signup_url

_login_url  = login_url()
_signup_url = signup_url()

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
.legal-disclaimer {{ background:#fff9e6; border:1px solid #f6d860; border-radius:10px; padding:16px 20px; margin-bottom:36px; font-size:0.88rem; color:#7a5c00; line-height:1.6; }}
.legal-h2 {{ font-family:'Darker Grotesque',sans-serif; font-size:1.4rem; font-weight:800; color:#1a202c; margin:36px 0 10px 0; letter-spacing:-0.01em; }}
.legal-body {{ font-size:0.92rem; color:#4a5568; line-height:1.75; margin-bottom:0; }}
.legal-body ul {{ padding-left:20px; margin:10px 0; }}
.legal-body li {{ margin-bottom:6px; }}
.legal-body a {{ color:#00a878; text-decoration:none; }}
.legal-body a:hover {{ text-decoration:underline; }}
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
<h1 class="legal-h1">Privacy Policy</h1>
<div class="legal-meta">Effective date: March 1, 2025 &nbsp;·&nbsp; Last updated: March 1, 2025 &nbsp;·&nbsp; Operated by Stocklio (Boston, Massachusetts, USA)</div>
<div class="legal-disclaimer"><strong>Not Investment Advice.</strong> Stocklio is an analytics and research tool. Nothing on this platform constitutes investment advice, a solicitation to buy or sell any security, or a recommendation of any investment strategy. All analysis is for informational purposes only. You are solely responsible for your own investment decisions.</div>
<div class="legal-h2">1. Who We Are</div>
<div class="legal-body">Stocklio ("<strong>Stocklio</strong>", "<strong>we</strong>", "<strong>us</strong>", or "<strong>our</strong>") is an individual-operated investment analytics platform headquartered in Boston, Massachusetts, USA. We provide retail investors with AI-powered stock forecasting, technical indicator scoring, and community sentiment tools. Our website is accessible at <a href="https://stocklio.ai">stocklio.ai</a>.<br><br>If you have questions about this policy, contact us at <a href="mailto:hello@stocklio.ai">hello@stocklio.ai</a>.</div>
<div class="legal-h2">2. Information We Collect</div>
<div class="legal-body">We collect only the information necessary to provide and improve our service:
<ul>
<li><strong>Account information:</strong> When you register, we collect your email address and name. This data is stored and managed by PropelAuth, our third-party authentication provider.</li>
<li><strong>Authentication activity:</strong> Login history, session tokens, and multi-factor authentication records are maintained by PropelAuth on our behalf.</li>
<li><strong>Usage data:</strong> We collect information about how you interact with Stocklio, including ticker symbols searched and features used. This data is used solely to improve your experience and product quality.</li>
<li><strong>Technical data:</strong> Standard server logs including IP address, browser type, operating system, and referring URL, used for security, debugging, and performance monitoring.</li>
</ul>
We do not collect payment information, Social Security numbers, brokerage credentials, or trading account details. No brokerage integration or trade execution occurs on this platform.</div>
<div class="legal-h2">3. How We Use Your Information</div>
<div class="legal-body">We use the information we collect to:
<ul>
<li>Create and manage your account, including authentication and session management</li>
<li>Provide and personalize the Stocklio analytics experience (e.g., recent searches)</li>
<li>Send transactional emails required for your account, such as email verification and login notifications (via PropelAuth)</li>
<li>Measure and analyze site usage and performance (via Google Analytics)</li>
<li>Detect, investigate, and prevent fraudulent or unauthorized activity</li>
<li>Comply with applicable legal obligations</li>
</ul>
We do not sell your personal data to third parties. We do not use your data to make automated decisions that have legal or similarly significant effects on you.</div>
<div class="legal-h2">4. Third-Party Services</div>
<div class="legal-body">Stocklio uses the following third-party services that may process your data:
<ul>
<li><strong>PropelAuth</strong> — Handles user authentication, session tokens, and transactional email delivery. PropelAuth acts as a data processor on our behalf and processes your email address and name. Review their privacy policy at <a href="https://www.propelauth.com/privacy" target="_blank">propelauth.com/privacy</a>.</li>
<li><strong>Google Analytics</strong> — We use Google Analytics 4 to understand how visitors use Stocklio. Google Analytics uses cookies to collect anonymized usage data including page views, session duration, and device type. You can opt out via the <a href="https://tools.google.com/dlpage/gaoptout" target="_blank">Google Analytics Opt-out Add-on</a>.</li>
<li><strong>Google AdSense (future)</strong> — We may enable Google AdSense display advertising in the future. If activated, Google may use cookies to serve personalized ads. We will update this policy before enabling AdSense.</li>
<li><strong>Alpha Vantage</strong> — We fetch publicly available market data via the Alpha Vantage API. No personal data is transmitted in these requests.</li>
</ul></div>
<div class="legal-h2">5. Cookies</div>
<div class="legal-body">Stocklio uses cookies and similar tracking technologies. Please see our <a href="/cookies" target="_self">Cookie Policy</a> for a full description of the cookies we use, their purpose, and how to manage them.</div>
<div class="legal-h2">6. Data Retention</div>
<div class="legal-body">We retain your account data for as long as your account is active. If you request account deletion, we will delete or anonymize your personal data within 30 days, except where required by law. Search history and usage logs are retained for up to 12 months and then automatically purged.</div>
<div class="legal-h2">7. Your Rights</div>
<div class="legal-body">Depending on your location, you may have the right to:
<ul>
<li>Access the personal data we hold about you</li>
<li>Request correction of inaccurate data</li>
<li>Request deletion of your personal data ("right to be forgotten")</li>
<li>Object to or restrict certain types of processing</li>
<li>Request portability of your data in a machine-readable format</li>
</ul>
To exercise any of these rights, contact us at <a href="mailto:hello@stocklio.ai">hello@stocklio.ai</a>. We will respond within 30 days. If you are a resident of the EEA or United Kingdom, you have additional rights under GDPR. If you are a California resident, you have rights under the CCPA. We honor these rights for all users globally.</div>
<div class="legal-h2">8. Data Security</div>
<div class="legal-body">We take reasonable technical and organizational measures to protect your information, including encrypted data transmission (HTTPS), access controls, and using trusted third-party providers with established security practices. Authentication credentials are managed entirely by PropelAuth and are never stored in plain text.<br><br>No method of transmission over the internet is 100% secure. While we strive to protect your data, we cannot guarantee absolute security.</div>
<div class="legal-h2">9. Children's Privacy</div>
<div class="legal-body">Stocklio is intended for general audiences and does not restrict access by age. However, we do not knowingly collect personal data from children under the age of 13. If you believe a child under 13 has provided us with personal information, please contact us at <a href="mailto:hello@stocklio.ai">hello@stocklio.ai</a> and we will delete it promptly.</div>
<div class="legal-h2">10. International Transfers</div>
<div class="legal-body">Stocklio is operated from the United States. If you access the platform from outside the United States, your information may be transferred to, stored, and processed in the US. By using Stocklio, you consent to this transfer.</div>
<div class="legal-h2">11. Changes to This Policy</div>
<div class="legal-body">We may update this Privacy Policy from time to time. When we make material changes, we will update the "Last updated" date at the top of this page. Your continued use of Stocklio after any changes constitutes acceptance of the updated policy.</div>
<div class="legal-h2">12. Governing Law</div>
<div class="legal-body">This Privacy Policy is governed by the laws of the Commonwealth of Massachusetts, USA, without regard to its conflict of law provisions. Any disputes arising under this policy shall be subject to the exclusive jurisdiction of the courts located in Suffolk County, Massachusetts.</div>
<div class="legal-h2">Contact</div>
<div class="legal-body" style="margin-bottom:48px;"><strong>Stocklio</strong><br>Boston, Massachusetts, USA<br><a href="mailto:hello@stocklio.ai">hello@stocklio.ai</a></div>
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
