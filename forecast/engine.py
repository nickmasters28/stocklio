"""
forecast/engine.py -- Rules-based scoring system that synthesises indicator
signals into a directional forecast (Bullish / Neutral / Bearish).

SCORING SYSTEM OVERVIEW
-----------------------
Each indicator contributes a score in the range [-1, +1]:
    +1  = strongly bullish signal
     0  = neutral
    -1  = strongly bearish signal

Fractional values represent intermediate signal strength.

Each indicator is weighted by importance. Weights can be tuned in the
WEIGHTS dict below. They are normalised so they always sum to 1.0.

Final score range: [-1.0, +1.0]
  >= 0.22  -> Bullish
  <= -0.22 -> Bearish
  between  -> Neutral

Signals (10 total):
  1. Trend (MA)        — price vs SMA50 / SMA200
  2. MA Crossover      — golden / death cross
  3. MACD              — momentum & histogram direction
  4. RSI               — overbought / oversold
  5. Stochastic        — %K/%D crossovers and zones
  6. Bollinger Bands   — price position in band
  7. Volume            — OBV + volume confirmation
  8. Price Momentum    — multi-timeframe rate of change (5d/20d/60d) [NEW]
  9. EMA Alignment     — short EMAs stacked above longer ones [NEW]
  10. 52-Week Range    — position in the 52-week high/low range [NEW]
"""

import pandas as pd
import numpy as np
import streamlit as st
from dataclasses import dataclass, field
from typing import Optional, List

# -- TUNABLE: indicator weights (relative importance) -------------------------
WEIGHTS = {
    "trend_ma":        0.18,
    "ma_crossover":    0.10,
    "macd":            0.15,
    "rsi":             0.10,
    "stochastic":      0.07,
    "bollinger":       0.07,
    "volume":          0.06,
    "price_momentum":  0.15,   # NEW — multi-timeframe ROC
    "ema_alignment":   0.07,   # NEW — MA stack order
    "52w_range":       0.05,   # NEW — 52-week position
}

# -- Thresholds ----------------------------------------------------------------
RSI_OVERSOLD      = 30
RSI_OVERBOUGHT    = 70
STOCH_OVERSOLD    = 20
STOCH_OVERBOUGHT  = 80
BULLISH_THRESHOLD =  0.22
BEARISH_THRESHOLD = -0.22


# -- Data structures -----------------------------------------------------------

@dataclass
class SignalResult:
    """Container for a single indicator's scored signal."""
    name:        str
    score:       float        # [-1, +1]
    weight:      float
    description: str
    direction:   str = "neutral"  # "bullish" | "bearish" | "neutral"

    def __post_init__(self):
        if self.score > 0.10:
            self.direction = "bullish"
        elif self.score < -0.10:
            self.direction = "bearish"
        else:
            self.direction = "neutral"


@dataclass
class HistoricalPattern:
    """Return/context at a similar signal level in the past."""
    label:       str
    occurrences: int
    median_fwd:  float    # median 10-day forward return (%)
    win_rate:    float    # % of occurrences with positive 10-day return


@dataclass
class ForecastResult:
    """Full forecast output for a symbol."""
    symbol:           str
    rating:           str          # "Bullish" | "Neutral" | "Bearish"
    confidence:       str          # "High" | "Medium" | "Low"
    composite_score:  float        # [-1, +1]
    signals:          list = field(default_factory=list)
    setups:           list = field(default_factory=list)
    summary:          str  = ""
    rsi_value:        Optional[float] = None
    macd_value:       Optional[float] = None
    trend_label:      str  = ""
    historical_returns: dict = field(default_factory=dict)   # {5d, 20d, 60d, 252d}
    historical_patterns: List[HistoricalPattern] = field(default_factory=list)


# -- Individual signal scorers -------------------------------------------------

def _score_trend_ma(row: pd.Series) -> SignalResult:
    """Price vs SMA50 and SMA200."""
    close  = row["Close"]
    sma50  = row.get("SMA_50")
    sma200 = row.get("SMA_200")

    if pd.isna(sma50) or pd.isna(sma200):
        return SignalResult("Trend (MA)", 0, WEIGHTS["trend_ma"], "Insufficient data")

    above_50  = close > sma50
    above_200 = close > sma200
    pct_50    = (close - sma50)  / sma50  * 100
    pct_200   = (close - sma200) / sma200 * 100

    if above_50 and above_200:
        score = min(1.0, 0.5 + min(abs(pct_50), abs(pct_200)) / 8)
        desc  = f"Price {pct_50:+.1f}% above SMA50, {pct_200:+.1f}% above SMA200"
    elif not above_50 and not above_200:
        score = max(-1.0, -0.5 - min(abs(pct_50), abs(pct_200)) / 8)
        desc  = f"Price {pct_50:+.1f}% below SMA50, {pct_200:+.1f}% below SMA200"
    else:
        score = 0.15 if above_200 else -0.15
        desc  = (
            "Price above SMA200 but below SMA50 -- mixed signal"
            if above_200
            else "Price above SMA50 but below SMA200 -- caution"
        )

    return SignalResult("Trend (MA)", score, WEIGHTS["trend_ma"], desc)


def _score_ma_crossover(df: pd.DataFrame) -> SignalResult:
    """Golden Cross (SMA50 > SMA200) / Death Cross, with recency bonus."""
    if len(df) < 201 or df["SMA_50"].isna().any() or df["SMA_200"].isna().any():
        return SignalResult("MA Crossover", 0, WEIGHTS["ma_crossover"], "Insufficient history")

    sma50  = df["SMA_50"].iloc[-1]
    sma200 = df["SMA_200"].iloc[-1]
    recent = df.tail(10)

    cross_up   = any(
        recent["SMA_50"].iloc[i] > recent["SMA_200"].iloc[i]
        and recent["SMA_50"].iloc[i-1] <= recent["SMA_200"].iloc[i-1]
        for i in range(1, len(recent))
    )
    cross_down = any(
        recent["SMA_50"].iloc[i] < recent["SMA_200"].iloc[i]
        and recent["SMA_50"].iloc[i-1] >= recent["SMA_200"].iloc[i-1]
        for i in range(1, len(recent))
    )

    golden = sma50 > sma200
    # How far apart are the MAs? Wider gap = more entrenched trend
    gap_pct = abs(sma50 - sma200) / sma200 * 100

    if cross_up:
        score, desc = 1.0, "\U0001f7e2 Fresh Golden Cross — SMA50 just crossed above SMA200"
    elif cross_down:
        score, desc = -1.0, "\U0001f534 Fresh Death Cross — SMA50 just crossed below SMA200"
    elif golden:
        score = min(0.8, 0.4 + gap_pct / 10)
        desc  = f"Golden Cross formation (SMA50 {sma50:.2f} > SMA200 {sma200:.2f}, gap {gap_pct:.1f}%)"
    else:
        score = max(-0.8, -0.4 - gap_pct / 10)
        desc  = f"Death Cross formation (SMA50 {sma50:.2f} < SMA200 {sma200:.2f}, gap {gap_pct:.1f}%)"

    return SignalResult("MA Crossover", score, WEIGHTS["ma_crossover"], desc)


def _score_macd(row: pd.Series) -> SignalResult:
    """MACD line vs signal line, histogram direction, and zero-line position."""
    macd   = row.get("MACD")
    signal = row.get("MACD_sig")
    hist   = row.get("MACD_hist")

    if pd.isna(macd) or pd.isna(signal):
        return SignalResult("MACD", 0, WEIGHTS["macd"], "Insufficient data")

    if macd > signal:
        score = 0.6
        desc  = f"MACD ({macd:.3f}) above signal ({signal:.3f}) — bullish momentum"
    else:
        score = -0.6
        desc  = f"MACD ({macd:.3f}) below signal ({signal:.3f}) — bearish momentum"

    if not pd.isna(hist):
        if hist > 0:
            score = min(1.0, score + 0.25)
            desc += "; histogram positive & expanding" if score > 0 else "; histogram positive"
        else:
            score = max(-1.0, score - 0.25)
            desc += "; histogram negative & contracting" if score < 0 else "; histogram negative"

        if macd > 0:
            desc += " (above zero line — sustained momentum)"
        else:
            desc += " (below zero line — yet to confirm recovery)"

    return SignalResult("MACD", score, WEIGHTS["macd"], desc)


def _score_rsi(row: pd.Series) -> SignalResult:
    """RSI — more sensitive scoring across the full range."""
    rsi = row.get("RSI")
    if pd.isna(rsi):
        return SignalResult("RSI", 0, WEIGHTS["rsi"], "Insufficient data")

    rsi = float(rsi)
    if rsi >= 80:
        score, desc = -1.0, f"RSI {rsi:.1f} — extremely overbought, high reversal risk"
    elif rsi >= RSI_OVERBOUGHT:
        score, desc = -0.55, f"RSI {rsi:.1f} — overbought; momentum strong but overextended"
    elif rsi >= 60:
        score, desc = 0.40, f"RSI {rsi:.1f} — bullish momentum building (60–70 zone)"
    elif rsi >= 55:
        score, desc = 0.25, f"RSI {rsi:.1f} — mild bullish bias (above midline)"
    elif rsi >= 45:
        score, desc = 0.00, f"RSI {rsi:.1f} — neutral equilibrium"
    elif rsi >= 40:
        score, desc = -0.25, f"RSI {rsi:.1f} — mild bearish bias (below midline)"
    elif rsi >= RSI_OVERSOLD:
        score, desc = -0.40, f"RSI {rsi:.1f} — bearish momentum (30–40 zone)"
    elif rsi <= 20:
        score, desc = 1.0,  f"RSI {rsi:.1f} — extremely oversold, high bounce potential"
    else:
        score, desc = 0.55,  f"RSI {rsi:.1f} — oversold; watch for reversal"

    return SignalResult("RSI", score, WEIGHTS["rsi"], desc)


def _score_stochastic(row: pd.Series) -> SignalResult:
    """Stochastic %K vs %D crossovers and overbought/oversold zones."""
    k = row.get("STOCH_K")
    d = row.get("STOCH_D")

    if pd.isna(k) or pd.isna(d):
        return SignalResult("Stochastic", 0, WEIGHTS["stochastic"], "Insufficient data")

    k, d = float(k), float(d)

    if k < STOCH_OVERSOLD and k > d:
        score, desc = 0.9, f"Stoch %K {k:.1f} oversold & crossing above %D — buy signal"
    elif k > STOCH_OVERBOUGHT and k < d:
        score, desc = -0.9, f"Stoch %K {k:.1f} overbought & crossing below %D — sell signal"
    elif k < STOCH_OVERSOLD:
        score, desc = 0.55, f"Stoch %K {k:.1f} in oversold territory"
    elif k > STOCH_OVERBOUGHT:
        score, desc = -0.55, f"Stoch %K {k:.1f} in overbought territory"
    elif k > 60 and k > d:
        score, desc = 0.35, f"Stoch %K ({k:.1f}) bullish — above 60 & crossing %D"
    elif k < 40 and k < d:
        score, desc = -0.35, f"Stoch %K ({k:.1f}) bearish — below 40 & crossing %D"
    elif k > d:
        score, desc = 0.20, f"Stoch %K ({k:.1f}) above %D ({d:.1f}) — mild bullish"
    else:
        score, desc = -0.20, f"Stoch %K ({k:.1f}) below %D ({d:.1f}) — mild bearish"

    return SignalResult("Stochastic", score, WEIGHTS["stochastic"], desc)


def _score_bollinger(row: pd.Series) -> SignalResult:
    """Price position within Bollinger Bands — more nuanced scoring."""
    close = row["Close"]
    upper = row.get("BB_upper")
    lower = row.get("BB_lower")
    mid   = row.get("BB_mid")

    if pd.isna(upper) or pd.isna(lower) or pd.isna(mid):
        return SignalResult("Bollinger Bands", 0, WEIGHTS["bollinger"], "Insufficient data")

    band_range = upper - lower
    if band_range == 0:
        return SignalResult("Bollinger Bands", 0, WEIGHTS["bollinger"], "Band range is zero")

    position = (close - lower) / band_range   # 0 = at lower band, 1 = at upper band

    if close > upper:
        score, desc = -0.5, "Price above upper BB — breakout or overbought"
    elif close < lower:
        score, desc = 0.5, "Price below lower BB — breakdown or oversold bounce"
    elif position >= 0.80:
        score, desc = 0.55, f"Price in top 20% of BB ({position*100:.0f}%) — strong upward momentum"
    elif position >= 0.60:
        score, desc = 0.30, f"Price in upper half of BB ({position*100:.0f}%) — bullish bias"
    elif position <= 0.20:
        score, desc = -0.55, f"Price in bottom 20% of BB ({position*100:.0f}%) — bearish pressure"
    elif position <= 0.40:
        score, desc = -0.30, f"Price in lower half of BB ({position*100:.0f}%) — bearish bias"
    else:
        score, desc = 0.0, f"Price mid-band ({position*100:.0f}%) — consolidating"

    return SignalResult("Bollinger Bands", score, WEIGHTS["bollinger"], desc)


def _score_volume(df: pd.DataFrame) -> SignalResult:
    """Volume confirmation: rising OBV + above-average volume = confirms trend."""
    if len(df) < 5:
        return SignalResult("Volume", 0, WEIGHTS["volume"], "Insufficient data")

    obv      = df["OBV"].iloc[-1]
    obv_prev = df["OBV"].iloc[-5]
    vol      = df["Volume"].iloc[-1]
    vol_avg  = df["VOL_SMA20"].iloc[-1]

    obv_rising = obv > obv_prev
    high_vol   = vol > vol_avg if not pd.isna(vol_avg) else False

    if obv_rising and high_vol:
        score, desc = 0.8, "OBV rising + above-average volume — strong trend confirmation"
    elif obv_rising:
        score, desc = 0.35, "OBV rising — accumulation signal"
    elif not obv_rising and high_vol:
        score, desc = -0.6, "OBV falling + high volume — distribution / selling pressure"
    else:
        score, desc = -0.25, "OBV declining — mild distribution"

    return SignalResult("Volume", score, WEIGHTS["volume"], desc)


# -- NEW SIGNALS ---------------------------------------------------------------

def _score_price_momentum(df: pd.DataFrame) -> SignalResult:
    """
    Multi-timeframe price Rate of Change (ROC).
    Captures raw price momentum that MAs and oscillators can miss.
    Timeframes: 5-day (short), 20-day (medium), 60-day (longer)
    """
    if len(df) < 20:
        return SignalResult("Price Momentum", 0, WEIGHTS["price_momentum"], "Insufficient history")

    close = df["Close"]
    roc5  = (close.iloc[-1] - close.iloc[-5])  / close.iloc[-5]  * 100
    roc20 = (close.iloc[-1] - close.iloc[-20]) / close.iloc[-20] * 100
    roc60 = (close.iloc[-1] - close.iloc[-min(60, len(df))]) / close.iloc[-min(60, len(df))] * 100 if len(df) >= 60 else roc20

    # Short-term momentum weighted highest
    momentum = roc5 * 0.45 + roc20 * 0.35 + roc60 * 0.20

    # Normalize: 15% composite move → ±1.0
    score = float(np.clip(momentum / 15.0, -1, 1))

    parts = [f"5d {roc5:+.1f}%", f"20d {roc20:+.1f}%", f"60d {roc60:+.1f}%"]
    desc  = "Multi-timeframe momentum: " + ", ".join(parts)

    return SignalResult("Price Momentum", round(score, 3), WEIGHTS["price_momentum"], desc)


def _score_ema_alignment(row: pd.Series) -> SignalResult:
    """
    EMA/SMA stack alignment.
    Bullish: EMA9 > SMA20 > SMA50 > SMA200 (shorter EMAs above longer)
    Bearish: inverse order
    """
    ema9   = row.get("EMA_9")
    sma20  = row.get("SMA_20")
    sma50  = row.get("SMA_50")
    sma200 = row.get("SMA_200")

    available = [(v, n) for v, n in [
        (ema9, "EMA9"), (sma20, "SMA20"), (sma50, "SMA50"), (sma200, "SMA200")
    ] if v is not None and not pd.isna(v)]

    if len(available) < 3:
        return SignalResult("EMA Alignment", 0, WEIGHTS["ema_alignment"], "Insufficient MA data")

    values      = [v for v, _ in available]
    names       = [n for _, n in available]
    total_pairs = len(values) - 1

    aligned_up   = sum(1 for i in range(total_pairs) if values[i] > values[i + 1])
    aligned_down = sum(1 for i in range(total_pairs) if values[i] < values[i + 1])

    up_ratio   = aligned_up   / total_pairs
    down_ratio = aligned_down / total_pairs

    if up_ratio == 1.0:
        score = 0.85
        desc  = f"Full bullish MA stack: {' > '.join(names)}"
    elif up_ratio >= 0.67:
        score = 0.45
        desc  = f"Mostly bullish MA stack ({aligned_up}/{total_pairs} aligned)"
    elif down_ratio == 1.0:
        score = -0.85
        desc  = f"Full bearish MA stack: {' < '.join(reversed(names))}"
    elif down_ratio >= 0.67:
        score = -0.45
        desc  = f"Mostly bearish MA stack ({aligned_down}/{total_pairs} aligned)"
    else:
        score = 0.0
        desc  = "Mixed MA alignment — no clear stack direction"

    return SignalResult("EMA Alignment", round(score, 3), WEIGHTS["ema_alignment"], desc)


def _score_52w_range(df: pd.DataFrame) -> SignalResult:
    """
    Position within the 52-week high/low range.
    Stocks near 52-week highs are in strong momentum; near lows indicate weakness.
    """
    if len(df) < 50:
        return SignalResult("52-Week Range", 0, WEIGHTS["52w_range"], "Insufficient history")

    lookback = min(252, len(df))
    high52   = float(df["High"].tail(lookback).max())
    low52    = float(df["Low"].tail(lookback).min())
    close    = float(df["Close"].iloc[-1])
    rng      = high52 - low52

    if rng == 0:
        return SignalResult("52-Week Range", 0, WEIGHTS["52w_range"], "No range data")

    position = (close - low52) / rng   # 0.0 = at 52w low, 1.0 = at 52w high

    pct_from_high = (close - high52) / high52 * 100
    pct_from_low  = (close - low52)  / low52  * 100

    if position >= 0.92:
        score, desc = 0.95, f"Near 52-week high ({pct_from_high:+.1f}% from high) — strong momentum"
    elif position >= 0.75:
        score, desc = 0.60, f"Upper 52-week range ({position*100:.0f}% of range, {pct_from_high:+.1f}% from high)"
    elif position >= 0.55:
        score, desc = 0.25, f"Above mid-range ({position*100:.0f}% of 52-week range)"
    elif position >= 0.45:
        score, desc = 0.0,  f"Mid 52-week range ({position*100:.0f}%)"
    elif position >= 0.25:
        score, desc = -0.25, f"Below mid-range ({position*100:.0f}% of 52-week range)"
    elif position >= 0.08:
        score, desc = -0.60, f"Lower 52-week range ({position*100:.0f}%, {pct_from_low:+.1f}% from low)"
    else:
        score, desc = -0.95, f"Near 52-week low ({pct_from_low:+.1f}% from low) — continued weakness"

    return SignalResult("52-Week Range", round(score, 3), WEIGHTS["52w_range"], desc)


# -- Setup detection -----------------------------------------------------------

def detect_setups(df: pd.DataFrame, support: list, resistance: list) -> list:
    """Identify notable technical patterns / setups."""
    setups = []
    if len(df) < 10:
        return setups

    last  = df.iloc[-1]
    prev  = df.iloc[-2]
    close = float(last["Close"])

    # Golden / Death Cross
    if not pd.isna(last.get("SMA_50")) and not pd.isna(last.get("SMA_200")):
        if last["SMA_50"] > last["SMA_200"] and df["SMA_50"].iloc[-2] <= df["SMA_200"].iloc[-2]:
            setups.append("\U0001f7e2 Golden Cross — SMA50 crossed above SMA200")
        elif last["SMA_50"] < last["SMA_200"] and df["SMA_50"].iloc[-2] >= df["SMA_200"].iloc[-2]:
            setups.append("\U0001f534 Death Cross — SMA50 crossed below SMA200")

    # MACD crossover
    if (not pd.isna(last.get("MACD")) and not pd.isna(last.get("MACD_sig")) and
            not pd.isna(prev.get("MACD")) and not pd.isna(prev.get("MACD_sig"))):
        if last["MACD"] > last["MACD_sig"] and prev["MACD"] <= prev["MACD_sig"]:
            setups.append("\U0001f4c8 MACD Bullish Crossover — MACD crossed above signal line")
        elif last["MACD"] < last["MACD_sig"] and prev["MACD"] >= prev["MACD_sig"]:
            setups.append("\U0001f4c9 MACD Bearish Crossover — MACD crossed below signal line")

    # RSI reversals
    if not pd.isna(last.get("RSI")):
        if float(prev.get("RSI", 50)) <= RSI_OVERSOLD and float(last["RSI"]) > RSI_OVERSOLD:
            setups.append("\U0001f504 Oversold Bounce — RSI recovering from oversold territory")
        elif float(prev.get("RSI", 50)) >= RSI_OVERBOUGHT and float(last["RSI"]) < RSI_OVERBOUGHT:
            setups.append("\u26a0\ufe0f Overbought Pullback — RSI dropping from overbought territory")

    # Breakout / Breakdown vs S&R
    for r in resistance:
        if float(prev["Close"]) < r <= close:
            setups.append(f"\U0001f680 Breakout above resistance at ${r:.2f}")
    for s in support:
        if float(prev["Close"]) > s >= close:
            setups.append(f"\U0001f4c9 Breakdown below support at ${s:.2f}")

    # Bollinger Squeeze
    if not pd.isna(last.get("BB_width")):
        avg_width = df["BB_width"].tail(20).mean()
        if float(last["BB_width"]) < avg_width * 0.65:
            setups.append("\u26a1 Bollinger Squeeze — volatility compression, breakout likely")

    # Volume spike
    if not pd.isna(last.get("VOL_SMA20")) and last["VOL_SMA20"] > 0:
        vol_ratio = last["Volume"] / last["VOL_SMA20"]
        if vol_ratio > 2.0:
            setups.append(f"\U0001f4ca Volume Spike — {vol_ratio:.1f}x average volume")

    # 52-week high new breakout
    if len(df) >= 50:
        high52 = df["High"].tail(min(252, len(df)-1)).iloc[:-1].max()
        if float(last["High"]) > high52:
            setups.append(f"\U0001f3c6 New 52-week high — ${float(last['High']):.2f}")

    # EMA stack fully aligned (bullish)
    if ("EMA_9" in df.columns and not pd.isna(last.get("EMA_9"))
            and not pd.isna(last.get("SMA_50")) and not pd.isna(last.get("SMA_200"))):
        if last["EMA_9"] > last["SMA_50"] > last["SMA_200"] and float(last["Close"]) > last["EMA_9"]:
            setups.append("\u2728 Full EMA Stack alignment — price above all moving averages in bullish order")

    return setups


# -- Historical analysis -------------------------------------------------------

def _compute_historical_returns(df: pd.DataFrame) -> dict:
    """Compute actual rolling returns at key lookback periods."""
    if len(df) < 5:
        return {}

    close = df["Close"]
    result = {}
    for label, n in [("5d", 5), ("20d", 20), ("60d", 60), ("252d", 252)]:
        if len(df) > n:
            ret = (float(close.iloc[-1]) - float(close.iloc[-n - 1])) / float(close.iloc[-n - 1]) * 100
            result[label] = round(ret, 2)

    return result


def _build_historical_patterns(df: pd.DataFrame) -> list:
    """
    For the 3 most actionable signals (RSI zone, MACD alignment, price above/below SMA50),
    look back 252 sessions to find similar conditions and compute the median 10-day
    forward return. Gives users historical base-rate context.
    """
    patterns = []
    if len(df) < 60:
        return patterns

    close = df["Close"].values
    n = len(close)

    # -- RSI zone pattern
    if "RSI" in df.columns:
        rsi_vals = df["RSI"].values
        cur_rsi = float(rsi_vals[-1]) if not pd.isna(rsi_vals[-1]) else None
        if cur_rsi is not None:
            if cur_rsi >= RSI_OVERBOUGHT:
                zone_lo, zone_hi, zone_label = RSI_OVERBOUGHT, 100, "RSI overbought (≥70)"
            elif cur_rsi <= RSI_OVERSOLD:
                zone_lo, zone_hi, zone_label = 0, RSI_OVERSOLD, "RSI oversold (≤30)"
            elif cur_rsi >= 55:
                zone_lo, zone_hi, zone_label = 55, RSI_OVERBOUGHT, "RSI bullish zone (55–70)"
            elif cur_rsi <= 45:
                zone_lo, zone_hi, zone_label = RSI_OVERSOLD, 45, "RSI bearish zone (30–45)"
            else:
                zone_lo, zone_hi, zone_label = None, None, None

            if zone_lo is not None:
                lookback = min(252, n - 11)
                fwd_returns = []
                for i in range(lookback):
                    rsi_i = rsi_vals[i]
                    if not pd.isna(rsi_i) and zone_lo <= float(rsi_i) <= zone_hi:
                        fwd = (close[i + 10] - close[i]) / close[i] * 100
                        fwd_returns.append(fwd)
                if len(fwd_returns) >= 5:
                    median_fwd = float(np.median(fwd_returns))
                    win_rate   = float(np.mean([r > 0 for r in fwd_returns])) * 100
                    patterns.append(HistoricalPattern(
                        label       = zone_label,
                        occurrences = len(fwd_returns),
                        median_fwd  = round(median_fwd, 2),
                        win_rate    = round(win_rate, 1),
                    ))

    # -- Price vs SMA50 pattern
    if "SMA_50" in df.columns:
        sma50_vals = df["SMA_50"].values
        cur_above  = (not pd.isna(sma50_vals[-1])) and (close[-1] > sma50_vals[-1])
        label_str  = "Price above SMA50" if cur_above else "Price below SMA50"
        lookback   = min(252, n - 11)
        fwd_returns = []
        for i in range(lookback):
            s = sma50_vals[i]
            if not pd.isna(s):
                above_i = close[i] > s
                if above_i == cur_above:
                    fwd = (close[i + 10] - close[i]) / close[i] * 100
                    fwd_returns.append(fwd)
        if len(fwd_returns) >= 5:
            median_fwd = float(np.median(fwd_returns))
            win_rate   = float(np.mean([r > 0 for r in fwd_returns])) * 100
            patterns.append(HistoricalPattern(
                label       = label_str,
                occurrences = len(fwd_returns),
                median_fwd  = round(median_fwd, 2),
                win_rate    = round(win_rate, 1),
            ))

    # -- MACD alignment pattern
    if "MACD" in df.columns and "MACD_sig" in df.columns:
        macd_vals = df["MACD"].values
        sig_vals  = df["MACD_sig"].values
        cur_bull  = (not pd.isna(macd_vals[-1]) and not pd.isna(sig_vals[-1])
                     and macd_vals[-1] > sig_vals[-1])
        label_str = "MACD above signal (bullish)" if cur_bull else "MACD below signal (bearish)"
        lookback  = min(252, n - 11)
        fwd_returns = []
        for i in range(lookback):
            if not pd.isna(macd_vals[i]) and not pd.isna(sig_vals[i]):
                bull_i = macd_vals[i] > sig_vals[i]
                if bull_i == cur_bull:
                    fwd = (close[i + 10] - close[i]) / close[i] * 100
                    fwd_returns.append(fwd)
        if len(fwd_returns) >= 5:
            median_fwd = float(np.median(fwd_returns))
            win_rate   = float(np.mean([r > 0 for r in fwd_returns])) * 100
            patterns.append(HistoricalPattern(
                label       = label_str,
                occurrences = len(fwd_returns),
                median_fwd  = round(median_fwd, 2),
                win_rate    = round(win_rate, 1),
            ))

    return patterns


# -- Composite scoring ---------------------------------------------------------

def _normalise_weights(weights: dict) -> dict:
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}


@st.cache_data(ttl=1800, show_spinner=False)
def score_symbol(df: pd.DataFrame, symbol: str, support: list, resistance: list) -> ForecastResult:
    """Run all signal scorers and aggregate into a ForecastResult."""
    if df.empty or len(df) < 20:
        return ForecastResult(
            symbol=symbol, rating="Neutral", confidence="Low",
            composite_score=0.0, summary="Insufficient data to generate forecast."
        )

    last   = df.iloc[-1]
    norm_w = _normalise_weights(WEIGHTS)

    signals = [
        _score_trend_ma(last),
        _score_ma_crossover(df),
        _score_macd(last),
        _score_rsi(last),
        _score_stochastic(last),
        _score_bollinger(last),
        _score_volume(df),
        _score_price_momentum(df),
        _score_ema_alignment(last),
        _score_52w_range(df),
    ]

    name_to_key = {
        "Trend (MA)":      "trend_ma",
        "MA Crossover":    "ma_crossover",
        "MACD":            "macd",
        "RSI":             "rsi",
        "Stochastic":      "stochastic",
        "Bollinger Bands": "bollinger",
        "Volume":          "volume",
        "Price Momentum":  "price_momentum",
        "EMA Alignment":   "ema_alignment",
        "52-Week Range":   "52w_range",
    }
    for sig in signals:
        sig.weight = norm_w[name_to_key[sig.name]]

    composite = sum(s.score * s.weight for s in signals)
    composite = round(float(np.clip(composite, -1, 1)), 4)

    if composite >= BULLISH_THRESHOLD:
        rating = "Bullish"
    elif composite <= BEARISH_THRESHOLD:
        rating = "Bearish"
    else:
        rating = "Neutral"

    same_dir  = sum(1 for s in signals if s.direction == rating.lower())
    agreement = same_dir / len(signals)
    magnitude = abs(composite)

    if magnitude > 0.50 and agreement > 0.60:
        confidence = "High"
    elif magnitude > 0.25 or agreement > 0.50:
        confidence = "Medium"
    else:
        confidence = "Low"

    setups              = detect_setups(df, support, resistance)
    historical_returns  = _compute_historical_returns(df)
    historical_patterns = _build_historical_patterns(df)

    rsi_val  = round(float(last.get("RSI", 50)), 1)
    macd_val = round(float(last.get("MACD",  0)), 4)
    summary  = _generate_summary(symbol, rating, confidence, composite, rsi_val, signals, setups, historical_returns)

    return ForecastResult(
        symbol              = symbol,
        rating              = rating,
        confidence          = confidence,
        composite_score     = composite,
        signals             = signals,
        setups              = setups,
        summary             = summary,
        rsi_value           = rsi_val,
        macd_value          = macd_val,
        historical_returns  = historical_returns,
        historical_patterns = historical_patterns,
    )


def _generate_summary(
    symbol: str,
    rating: str,
    confidence: str,
    score: float,
    rsi: float,
    signals: list,
    setups: list,
    historical_returns: dict,
) -> str:
    """Compose a plain-English paragraph that reads like analyst commentary."""
    direction_phrase = {
        "Bullish": "showing bullish characteristics",
        "Bearish": "under bearish pressure",
        "Neutral": "in a consolidation / neutral phase",
    }[rating]

    if rsi >= RSI_OVERBOUGHT:
        rsi_comment = f" RSI at {rsi} is overbought — consider waiting for a pullback."
    elif rsi <= RSI_OVERSOLD:
        rsi_comment = f" RSI at {rsi} is oversold — watch for a potential reversal or bounce."
    elif rsi >= 60:
        rsi_comment = f" RSI at {rsi} reflects building bullish momentum."
    elif rsi <= 40:
        rsi_comment = f" RSI at {rsi} reflects bearish pressure below midline."
    else:
        rsi_comment = f" RSI at {rsi} is in a neutral range."

    trend_sig    = next((s for s in signals if s.name == "Trend (MA)"), None)
    trend_phrase = f" {trend_sig.description}." if trend_sig else ""

    mom_sig = next((s for s in signals if s.name == "Price Momentum"), None)
    mom_phrase = f" {mom_sig.description}." if mom_sig and abs(mom_sig.score) > 0.15 else ""

    setup_phrase = ""
    if setups:
        setup_phrase = f" Notable setups: {'; '.join(setups[:2])}."

    ret_phrase = ""
    if historical_returns:
        r20 = historical_returns.get("20d")
        r60 = historical_returns.get("60d")
        if r20 is not None and r60 is not None:
            ret_phrase = (
                f" Recent performance: {r20:+.1f}% over 20 days, {r60:+.1f}% over 60 days."
            )

    return (
        f"{symbol} is currently {direction_phrase} (composite score: {score:+.2f}, "
        f"{confidence.lower()} confidence).{trend_phrase}{mom_phrase}{rsi_comment}"
        f"{setup_phrase}{ret_phrase}"
    )


# -- Ride the Nine (9 EMA) analysis --------------------------------------------

def analyze_ride_the_nine(df: pd.DataFrame) -> dict:
    """
    Analyse the 'Ride the Nine' strategy using the 9 EMA.

    Returns a dict with:
        signal          : "Above" | "Below" | "At"
        pct_from_ema    : % distance of close from 9 EMA
        streak          : consecutive sessions above/below
        just_crossed    : True if a crossover occurred in the last 3 bars
        cross_direction : "up" | "down" | None
        ema9_vs_sma20   : True if 9 EMA > 20 SMA (short-term confirmation)
        gap_widening    : True if gap between price and 9 EMA is growing
        bias            : "Bullish" | "Bearish" | "Neutral"
        narrative       : plain-English explanation
    """
    if "EMA_9" not in df.columns or len(df) < 10:
        return {"bias": "Neutral", "narrative": "Insufficient data for Ride the Nine analysis."}

    close = df["Close"]
    ema9  = df["EMA_9"]

    last_close   = float(close.iloc[-1])
    last_ema9    = float(ema9.iloc[-1])
    pct_from_ema = (last_close - last_ema9) / last_ema9 * 100

    if abs(pct_from_ema) < 0.3:
        signal = "At"
    elif last_close > last_ema9:
        signal = "Above"
    else:
        signal = "Below"

    above_now = last_close > last_ema9
    streak = 0
    for i in range(len(df) - 1, max(0, len(df) - 60) - 1, -1):
        c = float(close.iloc[i])
        e = float(ema9.iloc[i])
        if pd.isna(e):
            break
        if (c > e) == above_now:
            streak += 1
        else:
            break

    just_crossed    = False
    cross_direction = None
    recent4 = df.tail(4)
    for i in range(1, len(recent4)):
        prev_above = float(recent4["Close"].iloc[i-1]) > float(recent4["EMA_9"].iloc[i-1])
        curr_above = float(recent4["Close"].iloc[i])   > float(recent4["EMA_9"].iloc[i])
        if curr_above and not prev_above:
            just_crossed    = True
            cross_direction = "up"
        elif not curr_above and prev_above:
            just_crossed    = True
            cross_direction = "down"

    ema9_vs_sma20 = None
    if "SMA_20" in df.columns and not pd.isna(df["SMA_20"].iloc[-1]):
        ema9_vs_sma20 = last_ema9 > float(df["SMA_20"].iloc[-1])

    recent5 = df.tail(5)
    gaps = [
        abs(float(recent5["Close"].iloc[i]) - float(recent5["EMA_9"].iloc[i]))
        for i in range(len(recent5))
        if not pd.isna(recent5["EMA_9"].iloc[i])
    ]
    gap_widening = (gaps[-1] > gaps[0]) if len(gaps) >= 2 else False

    bias = "Bullish" if signal == "Above" else "Bearish" if signal == "Below" else "Neutral"

    narrative = _ride_the_nine_narrative(
        signal, pct_from_ema, streak, just_crossed,
        cross_direction, ema9_vs_sma20, gap_widening,
    )

    return {
        "signal":          signal,
        "pct_from_ema":    round(pct_from_ema, 2),
        "streak":          streak,
        "just_crossed":    just_crossed,
        "cross_direction": cross_direction,
        "ema9_vs_sma20":   ema9_vs_sma20,
        "gap_widening":    gap_widening,
        "bias":            bias,
        "narrative":       narrative,
    }


def _ride_the_nine_narrative(
    signal: str,
    pct: float,
    streak: int,
    just_crossed: bool,
    cross_dir,
    ema9_vs_sma20,
    gap_widening: bool,
) -> str:
    sessions = f"{streak} consecutive session{'s' if streak != 1 else ''}"

    if just_crossed and cross_dir == "up":
        body = (
            f"Price just crossed above the 9 EMA — a fresh bullish signal. "
            f"This is the ideal Ride the Nine entry: the stock is close to the 9 EMA ({pct:+.2f}%), "
            f"keeping risk tight. Traders look to hold as long as price stays above the line."
        )
    elif just_crossed and cross_dir == "down":
        body = (
            f"Price just crossed below the 9 EMA — a bearish crossover. "
            f"Ride the Nine traders treat this as a caution or exit signal ({pct:+.2f}% from EMA). "
            f"Watch whether the 20 SMA acts as the next support, or whether selling accelerates."
        )
    elif signal == "Above":
        body = f"Price is {pct:+.2f}% above the 9 EMA, riding it higher for {sessions}. "
        if gap_widening:
            body += (
                "The gap between price and the 9 EMA is widening, signalling strong momentum — "
                "the trend is healthy. Ride the Nine strategy says to stay long."
            )
        else:
            body += (
                "The gap is narrowing, suggesting momentum may be fading. "
                "A pullback toward the 9 EMA is possible and would represent a re-entry opportunity "
                "rather than a reversal, as long as price holds above the line."
            )
    elif signal == "Below":
        body = f"Price is {pct:+.2f}% below the 9 EMA, in a bearish position for {sessions}. "
        if gap_widening:
            body += (
                "The gap is widening, confirming continued selling pressure. "
                "Ride the Nine strategy favours the short side or staying out until a reclaim."
            )
        else:
            body += (
                "The gap is narrowing — watch for a potential recovery toward the 9 EMA. "
                "A reclaim of the 9 EMA with follow-through would flip the short-term bias bullish."
            )
    else:
        body = (
            f"Price is trading right at the 9 EMA ({pct:+.2f}%), a key decision point. "
            "A daily close above confirms bullish intent; a close below signals bearish pressure. "
            "Ride the Nine traders wait for a decisive close off this line before entering."
        )

    if ema9_vs_sma20 is True:
        body += " The 9 EMA is above the 20 SMA, confirming short-term trend alignment."
    elif ema9_vs_sma20 is False:
        body += " Note: the 9 EMA is below the 20 SMA — broader short-term trend remains under pressure."

    return body


# -- Market-level phase detection ----------------------------------------------

def detect_market_phase(df: pd.DataFrame) -> dict:
    """Determine whether the broader market is Bullish, Bearish, or Consolidating."""
    if df.empty or len(df) < 50:
        return {"phase": "Unknown", "description": "Insufficient data", "score": 0}

    last  = df.iloc[-1]
    votes = []

    if not pd.isna(last.get("SMA_50")) and not pd.isna(last.get("SMA_200")):
        if last["Close"] > last["SMA_50"] and last["Close"] > last["SMA_200"]:
            votes.append(1)
        elif last["Close"] < last["SMA_50"] and last["Close"] < last["SMA_200"]:
            votes.append(-1)
        else:
            votes.append(0)

    if not pd.isna(last.get("MACD")) and not pd.isna(last.get("MACD_sig")):
        votes.append(1 if last["MACD"] > last["MACD_sig"] else -1)

    if not pd.isna(last.get("RSI")):
        rsi = float(last["RSI"])
        if rsi > 55:   votes.append(1)
        elif rsi < 45: votes.append(-1)
        else:          votes.append(0)

    avg = float(np.mean(votes)) if votes else 0

    if avg > 0.3:
        phase = "Bullish"
        desc  = "Market is trending upward across primary indicators."
    elif avg < -0.3:
        phase = "Bearish"
        desc  = "Market is in a downtrend; risk-off posture warranted."
    else:
        phase = "Consolidation"
        desc  = "Market is rangebound — no clear directional bias."

    return {"phase": phase, "description": desc, "score": round(avg, 3)}
