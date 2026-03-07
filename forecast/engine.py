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
  >= 0.30  -> Bullish
  <= -0.30 -> Bearish
  between  -> Neutral

Confidence is derived from |score|: higher magnitude = higher confidence.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Optional

# -- TUNABLE: indicator weights (relative importance) -------------------------
WEIGHTS = {
    "trend_ma":      0.25,
    "ma_crossover":  0.15,
    "macd":          0.20,
    "rsi":           0.15,
    "stochastic":    0.10,
    "bollinger":     0.10,
    "volume":        0.05,
}

# -- Thresholds ----------------------------------------------------------------
RSI_OVERSOLD     = 30
RSI_OVERBOUGHT   = 70
STOCH_OVERSOLD   = 20
STOCH_OVERBOUGHT = 80
BULLISH_THRESHOLD = 0.30
BEARISH_THRESHOLD = -0.30


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
        if self.score > 0.15:
            self.direction = "bullish"
        elif self.score < -0.15:
            self.direction = "bearish"
        else:
            self.direction = "neutral"


@dataclass
class ForecastResult:
    """Full forecast output for a symbol."""
    symbol:          str
    rating:          str          # "Bullish" | "Neutral" | "Bearish"
    confidence:      str          # "High" | "Medium" | "Low"
    composite_score: float        # [-1, +1]
    signals:         list = field(default_factory=list)
    setups:          list = field(default_factory=list)
    summary:         str  = ""
    rsi_value:       Optional[float] = None
    macd_value:      Optional[float] = None
    trend_label:     str  = ""


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
        score = min(1.0, 0.5 + min(abs(pct_50), abs(pct_200)) / 10)
        desc  = f"Price {pct_50:+.1f}% above SMA50, {pct_200:+.1f}% above SMA200"
    elif not above_50 and not above_200:
        score = max(-1.0, -0.5 - min(abs(pct_50), abs(pct_200)) / 10)
        desc  = f"Price {pct_50:+.1f}% below SMA50, {pct_200:+.1f}% below SMA200"
    else:
        score = 0.1 if above_200 else -0.1
        desc  = (
            "Price above SMA200 but below SMA50 -- mixed signal"
            if above_200
            else "Price above SMA50 but below SMA200 -- caution"
        )

    return SignalResult("Trend (MA)", score, WEIGHTS["trend_ma"], desc)


def _score_ma_crossover(df: pd.DataFrame) -> SignalResult:
    """Golden Cross (SMA50 > SMA200) / Death Cross (SMA50 < SMA200)."""
    if len(df) < 201 or df["SMA_50"].isna().any() or df["SMA_200"].isna().any():
        return SignalResult("MA Crossover", 0, WEIGHTS["ma_crossover"], "Insufficient history")

    sma50  = df["SMA_50"].iloc[-1]
    sma200 = df["SMA_200"].iloc[-1]
    recent = df.tail(10)

    golden     = (sma50 > sma200)
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

    if cross_up:
        score, desc = 1.0, "\U0001f7e2 Fresh Golden Cross -- SMA50 just crossed above SMA200"
    elif cross_down:
        score, desc = -1.0, "\U0001f534 Fresh Death Cross -- SMA50 just crossed below SMA200"
    elif golden:
        score, desc = 0.5, f"Golden Cross formation (SMA50 {sma50:.2f} > SMA200 {sma200:.2f})"
    else:
        score, desc = -0.5, f"Death Cross formation (SMA50 {sma50:.2f} < SMA200 {sma200:.2f})"

    return SignalResult("MA Crossover", score, WEIGHTS["ma_crossover"], desc)


def _score_macd(row: pd.Series) -> SignalResult:
    """MACD line vs signal line and histogram direction."""
    macd   = row.get("MACD")
    signal = row.get("MACD_sig")
    hist   = row.get("MACD_hist")

    if pd.isna(macd) or pd.isna(signal):
        return SignalResult("MACD", 0, WEIGHTS["macd"], "Insufficient data")

    if macd > signal:
        score = 0.6
        desc  = f"MACD ({macd:.3f}) above signal ({signal:.3f}) -- bullish momentum"
    else:
        score = -0.6
        desc  = f"MACD ({macd:.3f}) below signal ({signal:.3f}) -- bearish momentum"

    if not pd.isna(hist):
        if hist > 0:
            score = min(1.0, score + 0.2)
            desc += "; histogram positive"
        else:
            score = max(-1.0, score - 0.2)
            desc += "; histogram negative"

        if macd > 0:
            desc += " (MACD in positive territory)"
        else:
            desc += " (MACD in negative territory)"

    return SignalResult("MACD", score, WEIGHTS["macd"], desc)


def _score_rsi(row: pd.Series) -> SignalResult:
    """RSI interpretation: >70 overbought, <30 oversold."""
    rsi = row.get("RSI")
    if pd.isna(rsi):
        return SignalResult("RSI", 0, WEIGHTS["rsi"], "Insufficient data")

    rsi = float(rsi)
    if rsi >= 80:
        score, desc = -0.9, f"RSI {rsi:.1f} -- extremely overbought, high reversal risk"
    elif rsi >= RSI_OVERBOUGHT:
        score, desc = -0.5, f"RSI {rsi:.1f} -- overbought; momentum strong but overextended"
    elif rsi <= 20:
        score, desc = 0.9, f"RSI {rsi:.1f} -- extremely oversold, potential bounce"
    elif rsi <= RSI_OVERSOLD:
        score, desc = 0.5, f"RSI {rsi:.1f} -- oversold; watch for reversal"
    elif rsi > 55:
        score, desc = 0.3, f"RSI {rsi:.1f} -- bullish momentum (above mid-range)"
    elif rsi < 45:
        score, desc = -0.3, f"RSI {rsi:.1f} -- bearish momentum (below mid-range)"
    else:
        score, desc = 0.0, f"RSI {rsi:.1f} -- neutral range"

    return SignalResult("RSI", score, WEIGHTS["rsi"], desc)


def _score_stochastic(row: pd.Series) -> SignalResult:
    """Stochastic %K vs %D crossovers and overbought/oversold zones."""
    k = row.get("STOCH_K")
    d = row.get("STOCH_D")

    if pd.isna(k) or pd.isna(d):
        return SignalResult("Stochastic", 0, WEIGHTS["stochastic"], "Insufficient data")

    k, d = float(k), float(d)

    if k < STOCH_OVERSOLD and k > d:
        score, desc = 0.8, f"Stoch %K {k:.1f} oversold & crossing above %D -- buy signal"
    elif k > STOCH_OVERBOUGHT and k < d:
        score, desc = -0.8, f"Stoch %K {k:.1f} overbought & crossing below %D -- sell signal"
    elif k < STOCH_OVERSOLD:
        score, desc = 0.5, f"Stoch %K {k:.1f} in oversold territory"
    elif k > STOCH_OVERBOUGHT:
        score, desc = -0.5, f"Stoch %K {k:.1f} in overbought territory"
    elif k > d:
        score, desc = 0.2, f"Stoch %K ({k:.1f}) above %D ({d:.1f}) -- mild bullish"
    else:
        score, desc = -0.2, f"Stoch %K ({k:.1f}) below %D ({d:.1f}) -- mild bearish"

    return SignalResult("Stochastic", score, WEIGHTS["stochastic"], desc)


def _score_bollinger(row: pd.Series) -> SignalResult:
    """Price position relative to Bollinger Bands."""
    close = row["Close"]
    upper = row.get("BB_upper")
    lower = row.get("BB_lower")
    mid   = row.get("BB_mid")

    if pd.isna(upper) or pd.isna(lower) or pd.isna(mid):
        return SignalResult("Bollinger Bands", 0, WEIGHTS["bollinger"], "Insufficient data")

    band_range = upper - lower
    if band_range == 0:
        return SignalResult("Bollinger Bands", 0, WEIGHTS["bollinger"], "Band range is zero")

    position = (close - lower) / band_range

    if close > upper:
        score, desc = -0.6, "Price above upper BB -- potential overbought/breakout"
    elif close < lower:
        score, desc = 0.6, "Price below lower BB -- potential oversold/breakdown"
    elif position > 0.75:
        score, desc = 0.3, f"Price in upper quartile of BB ({position*100:.0f}% of band)"
    elif position < 0.25:
        score, desc = -0.3, f"Price in lower quartile of BB ({position*100:.0f}% of band)"
    else:
        score, desc = 0.0, f"Price mid-band ({position*100:.0f}%) -- consolidating"

    return SignalResult("Bollinger Bands", score, WEIGHTS["bollinger"], desc)


def _score_volume(df: pd.DataFrame) -> SignalResult:
    """Volume confirmation: rising OBV + above-average volume = confirms trend."""
    if len(df) < 5:
        return SignalResult("Volume", 0, WEIGHTS["volume"], "Insufficient data")

    obv       = df["OBV"].iloc[-1]
    obv_prev  = df["OBV"].iloc[-5]
    vol       = df["Volume"].iloc[-1]
    vol_avg   = df["VOL_SMA20"].iloc[-1]

    obv_rising = obv > obv_prev
    high_vol   = vol > vol_avg if not pd.isna(vol_avg) else False

    if obv_rising and high_vol:
        score, desc = 0.7, "OBV rising + above-average volume -- strong trend confirmation"
    elif obv_rising:
        score, desc = 0.3, "OBV rising -- accumulation signal (volume below average)"
    elif not obv_rising and high_vol:
        score, desc = -0.5, "OBV falling + high volume -- distribution / selling pressure"
    else:
        score, desc = -0.2, "OBV declining -- mild distribution signal"

    return SignalResult("Volume", score, WEIGHTS["volume"], desc)


# -- Setup detection -----------------------------------------------------------

def detect_setups(df: pd.DataFrame, support: list, resistance: list) -> list:
    """
    Identify notable technical patterns / setups.
    Returns a list of human-readable setup descriptions.
    """
    setups = []
    if len(df) < 10:
        return setups

    last  = df.iloc[-1]
    prev  = df.iloc[-2]
    close = float(last["Close"])

    # Golden / Death Cross
    if not pd.isna(last.get("SMA_50")) and not pd.isna(last.get("SMA_200")):
        if last["SMA_50"] > last["SMA_200"] and df["SMA_50"].iloc[-2] <= df["SMA_200"].iloc[-2]:
            setups.append("\U0001f7e2 Golden Cross -- SMA50 crossed above SMA200")
        elif last["SMA_50"] < last["SMA_200"] and df["SMA_50"].iloc[-2] >= df["SMA_200"].iloc[-2]:
            setups.append("\U0001f534 Death Cross -- SMA50 crossed below SMA200")

    # MACD crossover
    if (not pd.isna(last.get("MACD")) and not pd.isna(last.get("MACD_sig")) and
            not pd.isna(prev.get("MACD")) and not pd.isna(prev.get("MACD_sig"))):
        if last["MACD"] > last["MACD_sig"] and prev["MACD"] <= prev["MACD_sig"]:
            setups.append("\U0001f4c8 MACD Bullish Crossover -- MACD crossed above signal line")
        elif last["MACD"] < last["MACD_sig"] and prev["MACD"] >= prev["MACD_sig"]:
            setups.append("\U0001f4c9 MACD Bearish Crossover -- MACD crossed below signal line")

    # Oversold bounce
    if not pd.isna(last.get("RSI")):
        if float(prev.get("RSI", 50)) <= RSI_OVERSOLD and float(last["RSI"]) > RSI_OVERSOLD:
            setups.append("\U0001f504 Oversold Bounce -- RSI recovering from oversold territory")
        elif float(prev.get("RSI", 50)) >= RSI_OVERBOUGHT and float(last["RSI"]) < RSI_OVERBOUGHT:
            setups.append("\u26a0\ufe0f Overbought Pullback -- RSI dropping from overbought territory")

    # Breakout above resistance
    for r in resistance:
        if float(prev["Close"]) < r <= close:
            setups.append(f"\U0001f680 Breakout above resistance at ${r:.2f}")

    # Breakdown below support
    for s in support:
        if float(prev["Close"]) > s >= close:
            setups.append(f"\U0001f4c9 Breakdown below support at ${s:.2f}")

    # Bollinger Squeeze
    if not pd.isna(last.get("BB_width")):
        avg_width = df["BB_width"].tail(20).mean()
        if float(last["BB_width"]) < avg_width * 0.7:
            setups.append("\u26a1 Bollinger Squeeze -- low volatility, potential breakout imminent")

    # Volume spike
    if not pd.isna(last.get("VOL_SMA20")) and last["VOL_SMA20"] > 0:
        vol_ratio = last["Volume"] / last["VOL_SMA20"]
        if vol_ratio > 2.0:
            setups.append(f"\U0001f4ca Volume Spike -- {vol_ratio:.1f}x average volume")

    return setups


# -- Composite scoring ---------------------------------------------------------

def _normalise_weights(weights: dict) -> dict:
    """Ensure weights sum to 1.0."""
    total = sum(weights.values())
    return {k: v / total for k, v in weights.items()}


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
    ]

    name_to_key = {
        "Trend (MA)":      "trend_ma",
        "MA Crossover":    "ma_crossover",
        "MACD":            "macd",
        "RSI":             "rsi",
        "Stochastic":      "stochastic",
        "Bollinger Bands": "bollinger",
        "Volume":          "volume",
    }
    for sig in signals:
        sig.weight = norm_w[name_to_key[sig.name]]

    composite = sum(s.score * s.weight for s in signals)
    composite = round(np.clip(composite, -1, 1), 4)

    if composite >= BULLISH_THRESHOLD:
        rating = "Bullish"
    elif composite <= BEARISH_THRESHOLD:
        rating = "Bearish"
    else:
        rating = "Neutral"

    same_dir   = sum(1 for s in signals if s.direction == rating.lower())
    agreement  = same_dir / len(signals)
    magnitude  = abs(composite)

    if magnitude > 0.55 and agreement > 0.65:
        confidence = "High"
    elif magnitude > 0.30 or agreement > 0.50:
        confidence = "Medium"
    else:
        confidence = "Low"

    setups = detect_setups(df, support, resistance)

    rsi_val  = round(float(last.get("RSI", 50)), 1)
    macd_val = round(float(last.get("MACD", 0)), 4)
    summary  = _generate_summary(symbol, rating, confidence, composite, rsi_val, signals, setups)

    return ForecastResult(
        symbol=symbol,
        rating=rating,
        confidence=confidence,
        composite_score=composite,
        signals=signals,
        setups=setups,
        summary=summary,
        rsi_value=rsi_val,
        macd_value=macd_val,
    )


def _generate_summary(
    symbol: str,
    rating: str,
    confidence: str,
    score: float,
    rsi: float,
    signals: list,
    setups: list,
) -> str:
    """Compose a plain-English paragraph that reads like analyst commentary."""
    direction_phrase = {
        "Bullish": "showing bullish characteristics",
        "Bearish": "under bearish pressure",
        "Neutral": "in a consolidation / neutral phase",
    }[rating]

    if rsi >= RSI_OVERBOUGHT:
        rsi_comment = f" RSI at {rsi} is overbought -- consider waiting for a pullback before entering."
    elif rsi <= RSI_OVERSOLD:
        rsi_comment = f" RSI at {rsi} is oversold -- watch for a potential reversal or bounce."
    else:
        rsi_comment = f" RSI at {rsi} is in a healthy range."

    trend_sig    = next((s for s in signals if s.name == "Trend (MA)"), None)
    trend_phrase = f" {trend_sig.description}." if trend_sig else ""

    setup_phrase = ""
    if setups:
        setup_phrase = f" Notable setups: {'; '.join(setups[:2])}."

    return (
        f"{symbol} is currently {direction_phrase} (composite score: {score:+.2f}, "
        f"{confidence.lower()} confidence).{trend_phrase}{rsi_comment}{setup_phrase}"
    )


# -- Ride the Nine (9 EMA) analysis -------------------------------------------

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

    last_close = float(close.iloc[-1])
    last_ema9  = float(ema9.iloc[-1])
    pct_from_ema = (last_close - last_ema9) / last_ema9 * 100

    # Signal
    if abs(pct_from_ema) < 0.3:
        signal = "At"
    elif last_close > last_ema9:
        signal = "Above"
    else:
        signal = "Below"

    # Streak: consecutive sessions above/below
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

    # Crossover detection (last 3 bars)
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

    # 9 EMA vs 20 SMA confirmation
    ema9_vs_sma20 = None
    if "SMA_20" in df.columns and not pd.isna(df["SMA_20"].iloc[-1]):
        ema9_vs_sma20 = last_ema9 > float(df["SMA_20"].iloc[-1])

    # Gap widening: is the distance between price and 9 EMA growing?
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
        body = (
            f"Price is {pct:+.2f}% above the 9 EMA, riding it higher for {sessions}. "
        )
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
        body = (
            f"Price is {pct:+.2f}% below the 9 EMA, in a bearish position for {sessions}. "
        )
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

    # Append trend confirmation
    if ema9_vs_sma20 is True:
        body += " The 9 EMA is above the 20 SMA, confirming short-term trend alignment."
    elif ema9_vs_sma20 is False:
        body += " Note: the 9 EMA is below the 20 SMA, indicating the broader short-term trend remains under pressure."

    return body


# -- Market-level phase detection ----------------------------------------------

def detect_market_phase(df: pd.DataFrame) -> dict:
    """
    Determine whether the broader market is Bullish, Bearish, or Consolidating.

    Returns dict with keys: phase, description, score.
    """
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

    avg = np.mean(votes) if votes else 0

    if avg > 0.3:
        phase = "Bullish"
        desc  = "Market is trending upward across primary indicators."
    elif avg < -0.3:
        phase = "Bearish"
        desc  = "Market is in a downtrend; risk-off posture warranted."
    else:
        phase = "Consolidation"
        desc  = "Market is rangebound -- no clear directional bias."

    return {"phase": phase, "description": desc, "score": round(avg, 3)}
