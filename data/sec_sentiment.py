"""
data/sec_sentiment.py -- SEC filing sentiment for Stocklio Pro.

Sources (free, no API key required):
  - SEC EDGAR company_tickers.json  → ticker → CIK lookup
  - SEC EDGAR submissions API       → recent filings metadata
  - SEC EDGAR document fetch        → 8-K text for sentiment scoring

Sentiment is scored using a subset of the Loughran-McDonald financial
word list — the standard in academic finance NLP research.

All functions are cached at 6 hours since filings don't change intraday.
"""

import re
import requests
import streamlit as st
from datetime import date, timedelta
from typing import Optional


# ── Loughran-McDonald keyword lists (subset) ──────────────────────────────────

_POSITIVE = {
    "agreement", "growth", "improve", "improved", "improving", "strong", "stronger",
    "record", "increase", "increased", "exceed", "exceeded", "successful", "success",
    "profit", "profitable", "gain", "gains", "advantage", "opportunity", "positive",
    "higher", "upgrade", "upgraded", "confident", "momentum", "expand", "expanded",
    "expansion", "robust", "solid", "efficient", "innovation", "innovate", "leading",
    "outperform", "beat", "beats", "exceeded", "favorable", "accelerate", "grow",
}

_NEGATIVE = {
    "loss", "losses", "decline", "declined", "risk", "risks", "uncertainty",
    "volatile", "volatility", "decrease", "decreased", "lawsuit", "litigation",
    "default", "investigation", "restate", "restated", "restatement", "write-down",
    "writedown", "impair", "impairment", "adverse", "negative", "lower", "downgrade",
    "downgraded", "concern", "concerns", "weak", "weaker", "debt", "deficit",
    "shortfall", "miss", "missed", "below", "penalty", "penalties", "failure",
    "breach", "noncompliance", "terminated", "termination", "delayed", "delay",
}

# 8-K item numbers → plain English descriptions
_8K_ITEMS = {
    "1.01": "Material Agreement",
    "1.02": "Termination of Agreement",
    "1.03": "Bankruptcy / Receivership",
    "2.01": "Acquisition / Disposal of Assets",
    "2.02": "Results of Operations (Earnings)",
    "2.03": "Financial Obligations",
    "2.04": "Triggering Events",
    "2.05": "Cost Associated with Exit",
    "2.06": "Material Impairment",
    "3.01": "Delisting Notice",
    "3.02": "Unregistered Sales",
    "3.03": "Rights of Security Holders",
    "4.01": "Auditor Change",
    "4.02": "Non-Reliance on Prior Financials",
    "5.01": "Change in Control",
    "5.02": "Officers / Directors Change",
    "5.03": "Amendments to Governing Documents",
    "5.07": "Shareholder Vote Results",
    "5.08": "Shareholder Rights Plan",
    "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events",
    "9.01": "Financial Statements",
}


def _headers() -> dict:
    return {"User-Agent": "Stocklio info@stocklio.ai", "Accept-Encoding": "gzip, deflate"}


@st.cache_data(ttl=86400, show_spinner=False)
def _ticker_to_cik(ticker: str) -> Optional[str]:
    """Returns zero-padded 10-digit CIK for a ticker, or None if not found."""
    try:
        r = requests.get(
            "https://www.sec.gov/files/company_tickers.json",
            headers=_headers(), timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        ticker_upper = ticker.upper()
        for entry in data.values():
            if entry.get("ticker", "").upper() == ticker_upper:
                return str(entry["cik_str"]).zfill(10)
    except Exception:
        pass
    return None


@st.cache_data(ttl=21600, show_spinner=False)
def _fetch_submissions(cik: str) -> dict:
    try:
        r = requests.get(
            f"https://data.sec.gov/submissions/CIK{cik}.json",
            headers=_headers(), timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}


@st.cache_data(ttl=21600, show_spinner=False)
def _fetch_filing_text(cik: str, accession: str, primary_doc: str) -> str:
    """Fetch first 8000 chars of a filing document for sentiment scoring."""
    acc_nodash = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/full-index/{cik}/{acc_nodash}/{primary_doc}"
    # Try the direct Archives path
    try:
        r = requests.get(url, headers=_headers(), timeout=10)
        if r.status_code == 200:
            return r.text[:8000]
    except Exception:
        pass
    # Fallback: filing index path
    try:
        url2 = f"https://www.sec.gov/Archives/edgar/full-index/{acc_nodash}/{primary_doc}"
        r2 = requests.get(url2, headers=_headers(), timeout=10)
        if r2.status_code == 200:
            return r2.text[:8000]
    except Exception:
        pass
    return ""


def _score_text(text: str) -> tuple[int, int]:
    """Returns (positive_count, negative_count) keyword hits."""
    words = set(re.findall(r"[a-z]+", text.lower()))
    return len(words & _POSITIVE), len(words & _NEGATIVE)


def _sentiment_label(pos: int, neg: int) -> tuple[str, str]:
    """Returns (label, color) based on pos/neg counts."""
    total = pos + neg
    if total == 0:
        return "Neutral", "#a0aec0"
    ratio = pos / total
    if ratio >= 0.65:
        return "Bullish", "#00a878"
    elif ratio >= 0.50:
        return "Somewhat Bullish", "#38b2ac"
    elif ratio >= 0.40:
        return "Neutral", "#a0aec0"
    elif ratio >= 0.25:
        return "Somewhat Bearish", "#ed8936"
    else:
        return "Bearish", "#e53e3e"


@st.cache_data(ttl=21600, show_spinner=False)
def fetch_sec_sentiment(ticker: str, limit: int = 6) -> dict:
    """
    Returns a dict with:
      filings     - list of recent filing dicts
      sentiment   - overall label ("Bullish", "Neutral", etc.)
      color       - hex color for sentiment label
      pos_hits    - total positive keyword count
      neg_hits    - total negative keyword count
      cik         - company CIK (for building EDGAR links)
    """
    cik = _ticker_to_cik(ticker)
    if not cik:
        return {}

    subs = _fetch_submissions(cik)
    recent = subs.get("filings", {}).get("recent", {})
    if not recent:
        return {}

    forms        = recent.get("form", [])
    dates        = recent.get("filingDate", [])
    accessions   = recent.get("accessionNumber", [])
    descriptions = recent.get("primaryDocDescription", [])
    primary_docs = recent.get("primaryDocument", [])
    items_list   = recent.get("items", [])

    cutoff = (date.today() - timedelta(days=365)).isoformat()
    target_forms = {"10-K", "10-Q", "8-K"}

    filings = []
    total_pos = total_neg = 0

    for i, form in enumerate(forms):
        if form not in target_forms:
            continue
        filing_date = dates[i] if i < len(dates) else ""
        if filing_date < cutoff:
            continue

        accession  = accessions[i] if i < len(accessions) else ""
        primary    = primary_docs[i] if i < len(primary_docs) else ""
        items_raw  = items_list[i] if i < len(items_list) else ""
        desc       = descriptions[i] if i < len(descriptions) else ""

        # Parse 8-K items into readable labels
        item_labels = []
        if form == "8-K" and items_raw:
            for item_num in re.findall(r"\d+\.\d+", str(items_raw)):
                label = _8K_ITEMS.get(item_num)
                if label:
                    item_labels.append(f"Item {item_num}: {label}")

        # Score 8-K text — skip large annual reports to stay fast
        pos = neg = 0
        if form == "8-K" and primary and accession:
            text = _fetch_filing_text(cik, accession, primary)
            if text:
                pos, neg = _score_text(text)
                total_pos += pos
                total_neg += neg

        acc_link = accession.replace("-", "")
        edgar_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type={form}&dateb=&owner=include&count=10"

        filings.append({
            "form":       form,
            "date":       filing_date,
            "accession":  accession,
            "items":      item_labels,
            "desc":       desc,
            "pos":        pos,
            "neg":        neg,
            "url":        edgar_url,
        })

        if len(filings) >= limit:
            break

    label, color = _sentiment_label(total_pos, total_neg)
    return {
        "filings":   filings,
        "sentiment": label,
        "color":     color,
        "pos_hits":  total_pos,
        "neg_hits":  total_neg,
        "cik":       cik,
    }
