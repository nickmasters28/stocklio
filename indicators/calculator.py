"""
indicators/calculator.py -- Computes all technical indicators used by the app.

Uses the `ta` library where available, with manual fallbacks so the app
still works even if ta isn't installed.

Indicator reference:
  - SMA / EMA       : trend direction & crossovers
  - RSI (14)        : momentum, overbought/oversold
  - MACD (12/26/9)  : trend momentum, signal crossovers
  - Bollinger Bands : volatility, squeeze/breakout
  - ATR (14)        : volatility / position-sizing reference
  - Stochastic      : short-term momentum, overbought/oversold
  - OBV             : volume-weighted trend confirmation
  - Support/Resistance: derived from recent highs/lows
"""

import numpy as np
import pandas as pd
import streamlit as st

# -- Try importing `ta`; fall back to manual calculations if unavailable ------
try:
    import ta
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False


# -- Core helpers --------------------------------------------------------------

def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()

def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window).mean()

def _rsi_manual(close: pd.Series, period: int = 14) -> pd.Series:
    delta  = close.diff()
    gain   = delta.clip(lower=0)
    loss   = (-delta).clip(lower=0)
    avg_g  = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_l  = loss.ewm(alpha=1/period, adjust=False).mean()
    rs     = avg_g / avg_l.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def _atr_manual(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high, low, close = df["High"], df["Low"], df["Close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()


# -- Main computation function -------------------------------------------------

@st.cache_data(ttl=300, show_spinner=False)
def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Attach all technical indicators to the OHLCV DataFrame.

    Returns the same DataFrame with additional columns appended in-place
    (a copy is returned so the original is unchanged).
    """
    d = df.copy()
    close, high, low, vol = d["Close"], d["High"], d["Low"], d["Volume"]

    # -- Moving Averages -------------------------------------------------------
    d["SMA_20"]  = _sma(close, 20)
    d["SMA_50"]  = _sma(close, 50)
    d["SMA_200"] = _sma(close, 200)
    d["EMA_9"]   = _ema(close, 9)
    d["EMA_12"]  = _ema(close, 12)
    d["EMA_26"]  = _ema(close, 26)

    # -- MACD (12/26 EMAs, 9-period signal) ------------------------------------
    if TA_AVAILABLE:
        macd_ind      = ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9)
        d["MACD"]     = macd_ind.macd()
        d["MACD_sig"] = macd_ind.macd_signal()
        d["MACD_hist"]= macd_ind.macd_diff()
    else:
        d["MACD"]     = d["EMA_12"] - d["EMA_26"]
        d["MACD_sig"] = _ema(d["MACD"], 9)
        d["MACD_hist"]= d["MACD"] - d["MACD_sig"]

    # -- RSI (14-period) -------------------------------------------------------
    if TA_AVAILABLE:
        d["RSI"] = ta.momentum.RSIIndicator(close, window=14).rsi()
    else:
        d["RSI"] = _rsi_manual(close, 14)

    # -- Bollinger Bands (20-period, 2 sigma) ----------------------------------
    if TA_AVAILABLE:
        bb = ta.volatility.BollingerBands(close, window=20, window_dev=2)
        d["BB_upper"] = bb.bollinger_hband()
        d["BB_mid"]   = bb.bollinger_mavg()
        d["BB_lower"] = bb.bollinger_lband()
        d["BB_width"] = bb.bollinger_wband()
    else:
        sma20         = _sma(close, 20)
        std20         = close.rolling(20).std()
        d["BB_upper"] = sma20 + 2 * std20
        d["BB_mid"]   = sma20
        d["BB_lower"] = sma20 - 2 * std20
        d["BB_width"] = (d["BB_upper"] - d["BB_lower"]) / sma20

    # -- ATR (14-period) -------------------------------------------------------
    if TA_AVAILABLE:
        d["ATR"] = ta.volatility.AverageTrueRange(high, low, close, window=14).average_true_range()
    else:
        d["ATR"] = _atr_manual(d, 14)

    # -- Stochastic Oscillator (%K 14, %D 3) ----------------------------------
    if TA_AVAILABLE:
        stoch       = ta.momentum.StochasticOscillator(high, low, close, window=14, smooth_window=3)
        d["STOCH_K"]= stoch.stoch()
        d["STOCH_D"]= stoch.stoch_signal()
    else:
        low14  = low.rolling(14).min()
        high14 = high.rolling(14).max()
        d["STOCH_K"] = 100 * (close - low14) / (high14 - low14).replace(0, np.nan)
        d["STOCH_D"] = _sma(d["STOCH_K"], 3)

    # -- On-Balance Volume (OBV) -----------------------------------------------
    if TA_AVAILABLE:
        d["OBV"] = ta.volume.OnBalanceVolumeIndicator(close, vol).on_balance_volume()
    else:
        direction = np.sign(close.diff()).fillna(0)
        d["OBV"]  = (direction * vol).cumsum()

    # -- Volume SMA (20-day) ---------------------------------------------------
    d["VOL_SMA20"] = _sma(vol, 20)

    return d


# -- Support & Resistance levels -----------------------------------------------

@st.cache_data(ttl=300, show_spinner=False)
def find_support_resistance(df: pd.DataFrame, lookback: int = 60, n_levels: int = 3):
    """
    Identify support and resistance levels from recent local highs/lows.

    Strategy: uses a rolling window to find local max/min points,
    then clusters nearby levels using a 1% price proximity threshold.

    Returns:
        support_levels    : list of float (ascending)
        resistance_levels : list of float (ascending)
    """
    window  = max(5, lookback // 12)
    recent  = df.tail(lookback).copy()
    highs   = recent["High"]
    lows    = recent["Low"]

    local_max = highs[
        (highs == highs.rolling(window, center=True).max())
    ].dropna().values

    local_min = lows[
        (lows == lows.rolling(window, center=True).min())
    ].dropna().values

    def cluster(prices, threshold=0.01):
        """Merge price levels within threshold % of each other."""
        if len(prices) == 0:
            return []
        prices = sorted(prices)
        clusters, group = [], [prices[0]]
        for p in prices[1:]:
            if abs(p - group[-1]) / group[-1] < threshold:
                group.append(p)
            else:
                clusters.append(np.mean(group))
                group = [p]
        clusters.append(np.mean(group))
        return sorted(clusters)

    current_price = float(df["Close"].iloc[-1])

    resistance = [r for r in cluster(local_max) if r > current_price][:n_levels]
    support    = [s for s in cluster(local_min) if s < current_price][-n_levels:]

    return support, resistance


# -- Linear Regression Trend Projection ----------------------------------------

@st.cache_data(ttl=300, show_spinner=False)
def linear_regression_projection(
    close: pd.Series,
    lookback: int = 30,
    forecast_days: int = 10,
) -> dict:
    """
    Fit a simple OLS linear regression on the last `lookback` closes and
    project `forecast_days` forward.

    Returns:
        {
          slope       : daily price change implied by the fit,
          r_squared   : goodness-of-fit (0-1),
          projected   : list of projected prices,
          trend_label : "Uptrend" | "Downtrend" | "Flat",
        }
    """
    y = close.tail(lookback).values.astype(float)
    x = np.arange(len(y))

    coeffs = np.polyfit(x, y, 1)  # [slope, intercept]
    slope, intercept = coeffs

    y_hat  = np.polyval(coeffs, x)
    ss_res = np.sum((y - y_hat) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2     = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    future_x  = np.arange(len(y), len(y) + forecast_days)
    projected = [round(float(np.polyval(coeffs, xi)), 2) for xi in future_x]

    pct_slope = slope / float(y[-1]) * 100

    if pct_slope > 0.1:
        trend_label = "Uptrend"
    elif pct_slope < -0.1:
        trend_label = "Downtrend"
    else:
        trend_label = "Flat"

    return {
        "slope":       round(slope, 4),
        "pct_per_day": round(pct_slope, 4),
        "r_squared":   round(r2, 3),
        "projected":   projected,
        "trend_label": trend_label,
    }
