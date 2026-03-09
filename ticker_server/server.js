"use strict";

// Load .env for local development. In production (Render etc.) the env var
// is set directly on the host — dotenv is a no-op when the var is already set.
require("dotenv").config();

const express  = require("express");
const cors     = require("cors");
const fetch    = require("node-fetch");

const app = express();

// ── Config ────────────────────────────────────────────────────────────────────

// Set this environment variable on your host (Render, Railway, etc.):
//   ALPHA_VANTAGE_API_KEY=your_key_here
const AV_API_KEY = process.env.ALPHA_VANTAGE_API_KEY;

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

// ── Health check ──────────────────────────────────────────────────────────────

app.get("/health", (_req, res) => res.json({ ok: true }));

// ── Start ─────────────────────────────────────────────────────────────────────

app.listen(PORT, () => {
  console.log(`[ticker-server] Listening on port ${PORT}`);
  if (!AV_API_KEY) {
    console.warn("[ticker-server] WARNING: ALPHA_VANTAGE_API_KEY is not set.");
  }
});
