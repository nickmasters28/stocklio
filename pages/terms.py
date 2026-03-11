"""
pages/terms.py -- Stocklio Terms of Service (accessible at /terms)
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
<h1 class="legal-h1">Terms of Service</h1>
<div class="legal-meta">Effective date: March 1, 2025 &nbsp;·&nbsp; Last updated: March 1, 2025 &nbsp;·&nbsp; Operated by Stocklio (Boston, Massachusetts, USA)</div>
<div class="legal-disclaimer"><strong>Not Investment Advice.</strong> Stocklio provides analytical tools for informational and educational purposes only. Nothing on this platform constitutes investment advice, a recommendation to buy or sell any security, or a solicitation of any investment. You are solely responsible for all investment decisions you make. Past performance of any analysis or signal does not guarantee future results.</div>
<div class="legal-h2">1. Acceptance of Terms</div>
<div class="legal-body">By accessing or using Stocklio ("<strong>Service</strong>"), you agree to be bound by these Terms of Service ("<strong>Terms</strong>"). If you do not agree to all of these Terms, do not use the Service. These Terms constitute a legally binding agreement between you and Stocklio, operated by an individual in Boston, Massachusetts, USA ("<strong>we</strong>", "<strong>us</strong>", or "<strong>our</strong>").<br><br>We reserve the right to update these Terms at any time. Your continued use of the Service after any changes constitutes your acceptance of the updated Terms.</div>
<div class="legal-h2">2. Description of Service</div>
<div class="legal-body">Stocklio is an investment analytics platform that provides:
<ul>
<li>AI-powered composite scoring and directional forecasting for publicly traded equities</li>
<li>Technical indicator analysis including RSI, MACD, Bollinger Bands, EMA, and SMA</li>
<li>Community prediction markets and sentiment aggregation</li>
<li>Support and resistance level identification</li>
<li>Linear regression trend projections</li>
<li>Historical price charts and raw market data</li>
</ul>
Stocklio does not execute trades, connect to brokerage accounts, manage portfolios, or provide personalized investment advice. All data is sourced from publicly available third-party providers and is provided "as is."</div>
<div class="legal-h2">3. Eligibility and Account Registration</div>
<div class="legal-body">The Service is available to users globally. To create an account, you must provide a valid email address and create a secure password. You are responsible for maintaining the confidentiality of your account credentials and for all activity that occurs under your account.<br><br>You agree to provide accurate, complete, and current registration information. You may not transfer your account to another person without our prior written consent. We reserve the right to suspend or terminate accounts that violate these Terms.</div>
<div class="legal-h2">4. No Investment Advice</div>
<div class="legal-body"><strong>This is the most important section of these Terms. Please read it carefully.</strong><br><br>All content on Stocklio — including AI forecasts, technical scores, composite ratings, community sentiment data, signals, charts, projections, and editorial content — is provided solely for <strong>informational and educational purposes</strong>. It does not constitute:
<ul>
<li>Investment advice or a personalized recommendation</li>
<li>A solicitation or offer to buy or sell any security</li>
<li>Legal, tax, or accounting advice</li>
<li>A guarantee of any particular investment outcome</li>
</ul>
Stocklio is not a registered investment advisor, broker-dealer, or financial planner. You should consult a qualified financial professional before making any investment decision. Investing involves risk, including the potential loss of principal. You acknowledge that you are solely responsible for any investment decisions you make based on information obtained through Stocklio.</div>
<div class="legal-h2">5. Accuracy of Data</div>
<div class="legal-body">Stocklio sources market data from third-party providers including Alpha Vantage and Yahoo Finance. While we make reasonable efforts to ensure accuracy and timeliness, we make no warranties as to the accuracy, completeness, or timeliness of any data, analysis, or content on the platform. Market data may be delayed, adjusted, or subject to errors. Do not rely solely on Stocklio data for trading decisions.</div>
<div class="legal-h2">6. Acceptable Use</div>
<div class="legal-body">You agree to use Stocklio only for lawful purposes and in accordance with these Terms. You must not:
<ul>
<li>Scrape, crawl, or systematically extract data from the platform without our written permission</li>
<li>Use automated tools (bots, scripts, spiders) to access or interact with the Service</li>
<li>Attempt to probe, scan, or test the vulnerability of our systems or networks</li>
<li>Reverse engineer, decompile, or disassemble any portion of the Service</li>
<li>Distribute, sublicense, or commercially exploit any data or content from the Service without authorization</li>
<li>Impersonate another person or entity, or misrepresent your affiliation with any person or entity</li>
<li>Use the Service in a manner that violates any applicable law or regulation</li>
</ul>
We reserve the right to suspend or terminate access for any user who violates these terms.</div>
<div class="legal-h2">7. Intellectual Property</div>
<div class="legal-body">All content on Stocklio — including the forecasting algorithms, scoring models, UI design, branding, editorial content, and code — is owned by Stocklio or its licensors and protected by applicable intellectual property laws. You may use data and analysis from Stocklio for personal, non-commercial purposes only, provided you attribute Stocklio as the source.</div>
<div class="legal-h2">8. Community Predictions and User Content</div>
<div class="legal-body">Stocklio includes a community prediction market where users can submit bullish or bearish votes on individual stocks. By submitting a vote or any other content, you grant us a non-exclusive, royalty-free, worldwide license to use, display, and aggregate that content in connection with the Service.<br><br>Community votes and sentiment data are aggregated and displayed anonymously. They represent community opinion only and do not constitute investment advice.</div>
<div class="legal-h2">9. Disclaimer of Warranties</div>
<div class="legal-body">THE SERVICE IS PROVIDED ON AN "<strong>AS IS</strong>" AND "<strong>AS AVAILABLE</strong>" BASIS WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED. TO THE FULLEST EXTENT PERMITTED BY LAW, STOCKLIO EXPRESSLY DISCLAIMS ALL WARRANTIES, INCLUDING BUT NOT LIMITED TO:
<ul>
<li>WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND NON-INFRINGEMENT</li>
<li>WARRANTIES THAT THE SERVICE WILL BE UNINTERRUPTED, ERROR-FREE, OR FREE OF VIRUSES</li>
<li>WARRANTIES AS TO THE ACCURACY, TIMELINESS, OR COMPLETENESS OF ANY DATA OR CONTENT</li>
</ul></div>
<div class="legal-h2">10. Limitation of Liability</div>
<div class="legal-body">TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, STOCKLIO SHALL NOT BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING BUT NOT LIMITED TO LOSS OF PROFITS, LOSS OF DATA, OR INVESTMENT LOSSES, ARISING OUT OF OR IN CONNECTION WITH YOUR USE OF THE SERVICE.<br><br>IN NO EVENT SHALL STOCKLIO'S TOTAL LIABILITY TO YOU FOR ALL CLAIMS EXCEED THE GREATER OF (A) THE AMOUNT YOU PAID STOCKLIO IN THE 12 MONTHS PRECEDING THE CLAIM OR (B) $100 USD.</div>
<div class="legal-h2">11. Indemnification</div>
<div class="legal-body">You agree to indemnify, defend, and hold harmless Stocklio and its operators from and against any claims, liabilities, damages, losses, and expenses (including reasonable attorneys' fees) arising out of or relating to: (a) your use of the Service; (b) your violation of these Terms; (c) your violation of any third-party right; or (d) any investment decisions you make based on information from the Service.</div>
<div class="legal-h2">12. Termination</div>
<div class="legal-body">We may suspend or terminate your access to the Service at any time, with or without cause or notice. You may also delete your account at any time by contacting us at <a href="mailto:hello@stocklio.ai">hello@stocklio.ai</a>.<br><br>Sections 4, 7, 9, 10, 11, and 13 survive termination.</div>
<div class="legal-h2">13. Governing Law and Dispute Resolution</div>
<div class="legal-body">These Terms are governed by the laws of the Commonwealth of Massachusetts, USA, without regard to its conflict of law provisions. Any dispute arising under or relating to these Terms shall be resolved exclusively in the state or federal courts located in Suffolk County, Massachusetts, and you consent to personal jurisdiction in those courts.<br><br>You and Stocklio agree to resolve any disputes on an individual basis. You waive any right to bring or participate in class action or class-wide arbitration proceedings.</div>
<div class="legal-h2">14. Third-Party Links and Services</div>
<div class="legal-body">The Service may contain links to third-party websites or services. These links are provided for convenience only. Stocklio does not endorse, control, or assume responsibility for the content, privacy practices, or terms of any third-party sites. Your use of third-party services is at your own risk.</div>
<div class="legal-h2">15. Entire Agreement</div>
<div class="legal-body" style="margin-bottom:48px;">These Terms, together with our <a href="/privacy" target="_self">Privacy Policy</a> and <a href="/cookies" target="_self">Cookie Policy</a>, constitute the entire agreement between you and Stocklio with respect to the Service.<br><br>If any provision of these Terms is held to be invalid or unenforceable, that provision will be modified to the minimum extent necessary and the remaining provisions will continue in full force and effect.<br><br>For questions about these Terms, contact us at <a href="mailto:hello@stocklio.ai">hello@stocklio.ai</a>.</div>
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
