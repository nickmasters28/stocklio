"use strict";

// Load .env for local development. In production (Render etc.) the env var
// is set directly on the host — dotenv is a no-op when the var is already set.
require("dotenv").config();

const express     = require("express");
const cors        = require("cors");
const fetch       = require("node-fetch");
const { createClient } = require("@supabase/supabase-js");

const app = express();

// ── Config ────────────────────────────────────────────────────────────────────

const AV_API_KEY    = process.env.ALPHA_VANTAGE_API_KEY;
const FINNHUB_KEY   = process.env.FINNHUB_API_KEY;
const SUPABASE_URL  = process.env.SUPABASE_URL;
const SUPABASE_KEY  = process.env.SUPABASE_KEY;

// Port the server listens on. Override with the PORT env var (Render sets this).
const PORT = process.env.PORT || 3001;

// Number of tickers to return from the most_actively_traded list.
// Adjust this to show more or fewer tickers in the bar.
const MAX_TICKERS = 15;

// How long (ms) to cache the Alpha Vantage response server-side.
// AV's free tier allows 25 calls/day, so 5 min = safe for production.
const CACHE_TTL_MS = 5 * 60 * 1000;

// Origins allowed to call /api/trending-tickers.
// Tighten this in production to your exact domain, e.g. "https://stocklio.ai".
const ALLOWED_ORIGINS = process.env.ALLOWED_ORIGINS
  ? process.env.ALLOWED_ORIGINS.split(",")
  : ["http://localhost:8501", "https://stocklio.ai"];

// ── Cache ─────────────────────────────────────────────────────────────────────

let _cache = null; // { data: [...], expiresAt: number }

function getCached() {
  if (_cache && Date.now() < _cache.expiresAt) return _cache.data;
  return null;
}

function setCache(data) {
  _cache = { data, expiresAt: Date.now() + CACHE_TTL_MS };
}

// ── Middleware ────────────────────────────────────────────────────────────────

app.use(cors({ origin: ALLOWED_ORIGINS }));
app.use(express.json());

// ── Route: GET /api/trending-tickers ─────────────────────────────────────────

app.get("/api/trending-tickers", async (req, res) => {
  if (!AV_API_KEY) {
    return res.status(500).json({
      error: "ALPHA_VANTAGE_API_KEY is not configured on the server.",
    });
  }

  // Serve from cache if still fresh
  const cached = getCached();
  if (cached) {
    return res.json({ tickers: cached, cached: true });
  }

  try {
    const avRes = await fetch(
      `https://www.alphavantage.co/query?function=TOP_GAINERS_LOSERS&apikey=${AV_API_KEY}`,
      { headers: { "User-Agent": "stocklio-ticker-server/1.0" } }
    );

    if (!avRes.ok) {
      throw new Error(`Alpha Vantage responded with ${avRes.status}`);
    }

    const json = await avRes.json();

    // Alpha Vantage returns a note string when the key is invalid or rate-limited
    if (json.Note || json.Information) {
      console.warn("[ticker-server] Alpha Vantage warning:", json.Note || json.Information);
      return res.status(429).json({
        error: "Alpha Vantage rate limit reached. Try again shortly.",
      });
    }

    const raw = json.most_actively_traded || [];

    // Shape the data — strip everything the frontend doesn't need
    const tickers = raw.slice(0, MAX_TICKERS).map((item) => {
      // change_percentage from AV looks like "2.05%" — strip the % sign
      const pctRaw = String(item.change_percentage || "0").replace("%", "");
      const pct    = parseFloat(pctRaw);
      const price  = parseFloat(item.price || 0);

      return {
        ticker:      item.ticker,
        price:       isNaN(price) ? "—"  : price.toFixed(2),
        change_pct:  isNaN(pct)   ? 0    : parseFloat(pct.toFixed(2)),
        change_amt:  item.change_amount || "0",
      };
    });

    setCache(tickers);
    return res.json({ tickers, cached: false });

  } catch (err) {
    console.error("[ticker-server] fetch error:", err.message);
    return res.status(502).json({ error: "Failed to fetch market data." });
  }
});

// ── Supabase client ───────────────────────────────────────────────────────────

const supabase = (SUPABASE_URL && SUPABASE_KEY)
  ? createClient(SUPABASE_URL, SUPABASE_KEY)
  : null;

// ── Finnhub on-demand fetch ───────────────────────────────────────────────────

async function finnhubGet(path, params = {}) {
  if (!FINNHUB_KEY) return null;
  const url = new URL(`https://finnhub.io/api/v1${path}`);
  url.searchParams.set("token", FINNHUB_KEY);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  try {
    const r = await fetch(url.toString(), { headers: { "User-Agent": "stocklio/1.0" }, timeout: 8000 });
    if (!r.ok) return null;
    return r.json();
  } catch { return null; }
}

async function fetchOnDemandSnapshot(ticker) {
  const [quote, profile] = await Promise.all([
    finnhubGet("/quote",         { symbol: ticker }),
    finnhubGet("/stock/profile2", { symbol: ticker }),
  ]);

  if (!quote || !quote.c) return null;

  const price    = quote.c  || 0;
  const prevClose = quote.pc || price;
  const changePct = prevClose ? ((price - prevClose) / prevClose * 100) : 0;
  const changeAmt = price - prevClose;

  const row = {
    ticker,
    company_name:   (profile && profile.name)                 || ticker,
    sector:         (profile && profile.finnhubIndustry)       || "",
    exchange:       (profile && profile.exchange)              || "",
    market_cap:     (profile && profile.marketCapitalization)  || 0,
    price:          parseFloat(price.toFixed(2)),
    change_pct:     parseFloat(changePct.toFixed(2)),
    change_amt:     parseFloat(changeAmt.toFixed(4)),
    ai_score_label: "Neutral",
    ai_score_value: 0,
    rsi_value:      50,
    rsi_label:      "Neutral",
    macd_label:     "Neutral",
    bb_label:       "Mid-Band",
    on_demand:      true,
    updated_at:     new Date().toISOString(),
  };

  // Store so future requests hit Supabase instead of Finnhub
  if (supabase) {
    await supabase.table("ticker_snapshots").upsert(row, { onConflict: "ticker" });
  }

  return row;
}

// ── HTML renderer ─────────────────────────────────────────────────────────────

function scoreColor(label) {
  if (label === "Bullish") return "#00c896";
  if (label === "Bearish") return "#f56565";
  return "#a0aec0";
}

function signClass(v) {
  return v > 0 ? "pos" : v < 0 ? "neg" : "neu";
}

function renderTickerPage(snap) {
  const {
    ticker, company_name, sector, exchange, market_cap,
    price, change_pct, change_amt,
    ai_score_label, ai_score_value,
    rsi_value, rsi_label, macd_label, bb_label,
    updated_at,
  } = snap;

  const changeSign  = change_pct >= 0 ? "+" : "";
  const scColor     = scoreColor(ai_score_label);
  const priceFmt    = price      ? `$${Number(price).toFixed(2)}` : "—";
  const capFmt      = market_cap ? `$${(market_cap / 1000).toFixed(1)}B` : "—";
  const updFmt      = updated_at ? new Date(updated_at).toLocaleDateString("en-US",
    { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" }) : "—";

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${ticker} Stock Analysis — RSI, MACD, AI Score | Stocklio</title>
  <meta name="description" content="Free technical analysis for ${ticker} (${company_name || ticker}). View RSI, MACD, Bollinger Bands, and AI composite score updated daily.">
  <link rel="canonical" href="https://www.stocklio.ai/stocks/${ticker}">
  <meta property="og:type"        content="website">
  <meta property="og:url"         content="https://www.stocklio.ai/stocks/${ticker}">
  <meta property="og:title"       content="${ticker} Stock Analysis | Stocklio">
  <meta property="og:description" content="RSI, MACD, Bollinger Bands &amp; AI score for ${ticker}. Updated daily. Free on Stocklio.">
  <meta property="og:image"       content="https://www.stocklio.ai/og/Stocklio_General.png">
  <meta name="twitter:card"       content="summary_large_image">
  <meta name="twitter:image"      content="https://www.stocklio.ai/og/Stocklio_General.png">
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "WebPage",
    "name": "${ticker} Stock Technical Analysis",
    "url": "https://www.stocklio.ai/stocks/${ticker}",
    "description": "Daily RSI, MACD, Bollinger Bands and AI composite score for ${ticker}.",
    "publisher": { "@type": "Organization", "name": "Stocklio", "url": "https://www.stocklio.ai" }
  }
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="/style.css">
  <style>
    .ticker-hero   { padding: 40px 0 32px; border-bottom: 1px solid var(--border); margin-bottom: 36px; }
    .ticker-name   { font-family: 'Darker Grotesque', sans-serif; font-size: 2.6rem; font-weight: 900; color: var(--dark); letter-spacing: -0.02em; line-height: 1.1; margin: 0 0 4px; }
    .ticker-meta   { font-size: 0.85rem; color: var(--gray-light); margin-bottom: 20px; }
    .price-row     { display: flex; align-items: baseline; gap: 14px; flex-wrap: wrap; margin-bottom: 8px; }
    .price-val     { font-family: 'Darker Grotesque', sans-serif; font-size: 2.8rem; font-weight: 900; color: var(--dark); line-height: 1; }
    .change        { font-size: 1.1rem; font-weight: 600; }
    .pos           { color: #00c896; }
    .neg           { color: #f56565; }
    .neu           { color: var(--gray-light); }
    .snapshot-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin: 36px 0; }
    @media (max-width: 768px) { .snapshot-grid { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 420px) { .snapshot-grid { grid-template-columns: 1fr; } }
    .snap-card     { background: var(--white); border: 1px solid var(--border); border-radius: 14px; padding: 22px 20px; }
    .snap-label    { font-size: 0.72rem; font-weight: 700; color: var(--gray-light); text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }
    .snap-value    { font-family: 'Darker Grotesque', sans-serif; font-size: 2rem; font-weight: 900; line-height: 1; margin-bottom: 4px; }
    .snap-sub      { font-size: 0.78rem; color: var(--gray-light); }
    .info-row      { display: flex; gap: 32px; flex-wrap: wrap; margin-bottom: 36px; }
    .info-item     { font-size: 0.88rem; color: var(--gray); }
    .info-item strong { color: var(--dark); font-weight: 600; }
    .freshness     { font-size: 0.78rem; color: var(--gray-light); margin-top: 12px; }
    .cta-section   { margin: 48px 0; }
  </style>
</head>
<body>
<div class="container">

  <nav class="nav">
    <a href="/" class="logo">stocklio<span class="logo-dot">.</span></a>
    <div class="nav-links">
      <a href="/blog/" class="btn btn-outline">Blog</a>
      <a href="/pricing.html" class="btn btn-outline">Pricing</a>
      <a href="/faq.html" class="btn btn-outline">FAQ</a>
      <a href="https://auth.stocklio.ai/en/login?redirect_to=https%3A%2F%2Fapp.stocklio.ai%2Fanalyze%3Fticker%3D${ticker}" class="btn btn-outline">Log in</a>
      <a href="https://auth.stocklio.ai/en/signup?redirect_to=https%3A%2F%2Fapp.stocklio.ai%2Fanalyze%3Fticker%3D${ticker}" class="btn btn-primary">Sign up free</a>
    </div>
  </nav>

  <div class="ticker-hero">
    <div class="section-label" style="text-align:left;">${exchange || "Stock"} &middot; ${sector || "Equity"}</div>
    <h1 class="ticker-name">${ticker} &mdash; ${company_name || ticker}</h1>
    <div class="price-row">
      <span class="price-val">${priceFmt}</span>
      <span class="change ${signClass(change_pct)}">${changeSign}${Number(change_pct).toFixed(2)}% (${changeSign}${Number(change_amt).toFixed(2)})</span>
    </div>
    <div class="ticker-meta">Market cap: ${capFmt} &nbsp;&middot;&nbsp; Data updated ${updFmt}</div>
  </div>

  <!-- Snapshot cards -->
  <div class="snapshot-grid">

    <div class="snap-card">
      <div class="snap-label">AI Score</div>
      <div class="snap-value" style="color:${scColor};">${ai_score_label}</div>
      <div class="snap-sub">Score: ${Number(ai_score_value).toFixed(2)}</div>
    </div>

    <div class="snap-card">
      <div class="snap-label">RSI (14)</div>
      <div class="snap-value" style="color:${scoreColor(rsi_label === 'Overbought' ? 'Bearish' : rsi_label === 'Oversold' ? 'Bullish' : 'Neutral')};">${Number(rsi_value).toFixed(1)}</div>
      <div class="snap-sub">${rsi_label}</div>
    </div>

    <div class="snap-card">
      <div class="snap-label">MACD</div>
      <div class="snap-value" style="color:${scoreColor(macd_label)};">${macd_label}</div>
      <div class="snap-sub">Histogram signal</div>
    </div>

    <div class="snap-card">
      <div class="snap-label">Bollinger Bands</div>
      <div class="snap-value" style="font-size:1.4rem;color:var(--dark);">${bb_label}</div>
      <div class="snap-sub">Band position</div>
    </div>

  </div>

  <!-- Info row -->
  <div class="info-row">
    <div class="info-item"><strong>Ticker</strong><br>${ticker}</div>
    <div class="info-item"><strong>Company</strong><br>${company_name || "—"}</div>
    <div class="info-item"><strong>Sector</strong><br>${sector || "—"}</div>
    <div class="info-item"><strong>Exchange</strong><br>${exchange || "—"}</div>
    <div class="info-item"><strong>Market Cap</strong><br>${capFmt}</div>
  </div>

  <!-- Deeper analysis CTA -->
  <div class="cta-section">
    <div class="cta-band">
      <h2>Get the full picture for ${ticker}</h2>
      <p>Live charts, 9 EMA, SMA 50/200, volume analysis, and real-time alerts — free on Stocklio.</p>
      <a href="https://auth.stocklio.ai/en/signup?redirect_to=https%3A%2F%2Fapp.stocklio.ai%2Fanalyze%3Fticker%3D${ticker}" class="btn btn-primary btn-lg">
        Analyze ${ticker} free &rarr;
      </a>
    </div>
  </div>

  <p class="freshness">
    Indicators are calculated from daily closing prices and updated once per trading day.
    Data is provided for informational purposes only and does not constitute investment advice.
  </p>

  <footer class="footer">
    <div>
      <div class="logo" style="font-size:2rem;">stocklio<span class="logo-dot">.</span></div>
      <div style="font-size:0.8rem;color:#a0aec0;margin-top:6px;">Built for investors who want an edge.</div>
    </div>
    <div style="display:flex;gap:48px;flex-wrap:wrap;">
      <div>
        <div class="footer-col-title">Product</div>
        <a href="https://app.stocklio.ai/analyze?ticker=AAPL" class="footer-link">Open Dashboard</a>
        <a href="/pricing.html" class="footer-link">Pricing</a>
        <a href="/faq.html" class="footer-link">FAQ</a>
      </div>
      <div>
        <div class="footer-col-title">Resources</div>
        <a href="/blog/" class="footer-link">Blog</a>
        <a href="mailto:hello@stocklio.ai" class="footer-link">hello@stocklio.ai</a>
      </div>
      <div>
        <div class="footer-col-title">Legal</div>
        <a href="https://app.stocklio.ai/privacy" class="footer-link">Privacy Policy</a>
        <a href="https://app.stocklio.ai/terms" class="footer-link">Terms of Service</a>
      </div>
    </div>
    <div style="width:100%;border-top:1px solid var(--border);padding-top:20px;" class="footer-copy">
      &copy; 2025 Stocklio &nbsp;&middot;&nbsp;
      <a href="https://app.stocklio.ai/privacy">Privacy Policy</a> &nbsp;&middot;&nbsp;
      <a href="https://app.stocklio.ai/terms">Terms of Service</a>
    </div>
  </footer>

</div>
</body>
</html>`;
}

// ── Route: GET /stocks/:ticker ────────────────────────────────────────────────

app.get("/stocks/:ticker", async (req, res) => {
  const ticker = req.params.ticker.toUpperCase().trim();

  // Basic sanity check
  if (!/^[A-Z]{1,6}$/.test(ticker)) {
    return res.status(400).send("Invalid ticker symbol.");
  }

  if (!supabase) {
    return res.status(503).send("Data store not configured.");
  }

  try {
    // 1. Try Supabase first
    const { data, error } = await supabase
      .from("ticker_snapshots")
      .select("*")
      .eq("ticker", ticker)
      .maybeSingle();

    if (error) throw error;

    if (data) {
      res.setHeader("Cache-Control", "public, max-age=3600"); // 1h browser cache
      return res.send(renderTickerPage(data));
    }

    // 2. Not in batch list — fetch on-demand from Finnhub
    console.log(`[ticker-server] on-demand fetch for ${ticker}`);
    const snap = await fetchOnDemandSnapshot(ticker);

    if (!snap) {
      return res.status(404).send(`
        <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
        <title>Not Found | Stocklio</title>
        <link rel="stylesheet" href="/style.css">
        </head><body><div class="container" style="padding-top:60px;text-align:center;">
        <div class="logo" style="margin-bottom:16px;"><a href="/">stocklio<span class="logo-dot">.</span></a></div>
        <h1 style="font-family:'Darker Grotesque',sans-serif;font-size:2rem;font-weight:800;">Ticker not found</h1>
        <p style="color:var(--gray-light);margin:12px 0 24px;">We couldn't find data for <strong>${ticker}</strong>. It may be delisted or misspelled.</p>
        <a href="/" class="btn btn-primary">Back to Stocklio</a>
        </div></body></html>
      `);
    }

    res.setHeader("Cache-Control", "public, max-age=3600");
    return res.send(renderTickerPage(snap));

  } catch (err) {
    console.error(`[ticker-server] /stocks/${ticker} error:`, err.message);
    return res.status(500).send("Internal server error.");
  }
});

// ── Health check ──────────────────────────────────────────────────────────────

app.get("/health", (_req, res) => res.json({ ok: true }));

// ── Start ─────────────────────────────────────────────────────────────────────

app.listen(PORT, () => {
  console.log(`[ticker-server] Listening on port ${PORT}`);
  if (!AV_API_KEY) console.warn("[ticker-server] WARNING: ALPHA_VANTAGE_API_KEY is not set.");
  if (!FINNHUB_KEY)  console.warn("[ticker-server] WARNING: FINNHUB_API_KEY is not set.");
  if (!SUPABASE_URL || !SUPABASE_KEY) console.warn("[ticker-server] WARNING: Supabase env vars not set — /stocks routes disabled.");
});
