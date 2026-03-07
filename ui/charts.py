"""
ui/charts.py -- All Plotly chart generation for the dashboard.

Charts are built with a consistent dark theme and returned as Plotly Figure
objects so the caller can pass them to st.plotly_chart().
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Optional

# -- Colour palette ------------------------------------------------------------
COLOURS = {
    "bull":      "#00a878",
    "bear":      "#e53e3e",
    "neutral":   "#dd6b20",
    "volume":    "#4a90e2",
    "sma50":     "#dd6b20",
    "sma200":    "#9b59b6",
    "ema12":     "#2196f3",
    "ema26":     "#e91e8c",
    "macd":      "#00a878",
    "signal":    "#e53e3e",
    "hist_pos":  "#00a878",
    "hist_neg":  "#e53e3e",
    "bb_fill":   "rgba(74,144,226,0.07)",
    "bb_line":   "rgba(74,144,226,0.40)",
    "bg":        "#f5f7fa",
    "paper":     "#ffffff",
    "grid":      "#e2e8f0",
    "text":      "#1a202c",
}

def _base_layout(title: str = "") -> dict:
    """Shared dark-theme layout properties."""
    return dict(
        title=dict(text=title, font=dict(color=COLOURS["text"], size=16)),
        paper_bgcolor=COLOURS["paper"],
        plot_bgcolor=COLOURS["bg"],
        font=dict(color=COLOURS["text"], size=12),
        xaxis=dict(
            gridcolor=COLOURS["grid"],
            showgrid=True,
            rangeslider=dict(visible=False),
            type="date",
        ),
        yaxis=dict(gridcolor=COLOURS["grid"], showgrid=True),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=COLOURS["text"], size=11),
        ),
        margin=dict(l=50, r=20, t=50, b=40),
        hovermode="x unified",
    )


# -- Full stock analysis chart (candlestick + indicators) ----------------------

def build_stock_chart(
    df: pd.DataFrame,
    ticker: str,
    support: list,
    resistance: list,
    show_bb: bool = True,
    show_volume: bool = True,
    regression: Optional[dict] = None,
) -> go.Figure:
    """
    Multi-panel chart:
      Row 1 (60%): Candlestick + MAs + Bollinger Bands + S/R levels
      Row 2 (15%): Volume bars
      Row 3 (13%): MACD
      Row 4 (12%): RSI
    """
    row_heights = [0.55, 0.15, 0.15, 0.15] if show_volume else [0.65, 0.20, 0.15]
    n_rows      = 4 if show_volume else 3

    fig = make_subplots(
        rows=n_rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
    )

    # 1. Candlesticks
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color=COLOURS["bull"],
        decreasing_line_color=COLOURS["bear"],
        name=ticker,
    ), row=1, col=1)

    # 2. Moving averages
    for col, colour, name in [
        ("SMA_50",  COLOURS["sma50"],  "SMA 50"),
        ("SMA_200", COLOURS["sma200"], "SMA 200"),
    ]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col],
                line=dict(color=colour, width=1.5, dash="solid"),
                name=name, opacity=0.85,
            ), row=1, col=1)

    # 3. Bollinger Bands
    if show_bb and all(c in df.columns for c in ["BB_upper", "BB_lower", "BB_mid"]):
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_upper"],
            line=dict(color=COLOURS["bb_line"], width=1, dash="dot"),
            name="BB Upper", showlegend=True,
        ), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["BB_lower"],
            fill="tonexty", fillcolor=COLOURS["bb_fill"],
            line=dict(color=COLOURS["bb_line"], width=1, dash="dot"),
            name="BB Lower",
        ), row=1, col=1)

    # 4. Support / Resistance
    last_date  = df.index[-1]
    first_date = df.index[max(0, len(df)-60)]

    for r in resistance:
        fig.add_shape(type="line",
            x0=first_date, x1=last_date, y0=r, y1=r,
            line=dict(color=COLOURS["bear"], width=1.2, dash="dash"),
            row=1, col=1)
        fig.add_annotation(x=last_date, y=r, text=f"R ${r:.2f}",
            font=dict(color=COLOURS["bear"], size=10),
            showarrow=False, xanchor="left", row=1, col=1)

    for s in support:
        fig.add_shape(type="line",
            x0=first_date, x1=last_date, y0=s, y1=s,
            line=dict(color=COLOURS["bull"], width=1.2, dash="dash"),
            row=1, col=1)
        fig.add_annotation(x=last_date, y=s, text=f"S ${s:.2f}",
            font=dict(color=COLOURS["bull"], size=10),
            showarrow=False, xanchor="left", row=1, col=1)

    # 5. Linear regression projection
    if regression and regression.get("projected"):
        last_close   = float(df["Close"].iloc[-1])
        future_dates = pd.bdate_range(start=df.index[-1], periods=len(regression["projected"])+1)[1:]
        proj_y = [last_close] + regression["projected"]
        proj_x = [df.index[-1]] + list(future_dates)
        colour = COLOURS["bull"] if regression["trend_label"] == "Uptrend" else COLOURS["bear"]
        fig.add_trace(go.Scatter(
            x=proj_x, y=proj_y,
            line=dict(color=colour, width=2, dash="dot"),
            name=f"LR Projection ({regression['trend_label']})",
            opacity=0.7,
        ), row=1, col=1)

    # 6. Volume
    if show_volume and "Volume" in df.columns:
        colours_vol = [
            COLOURS["bull"] if df["Close"].iloc[i] >= df["Open"].iloc[i]
            else COLOURS["bear"]
            for i in range(len(df))
        ]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"],
            marker_color=colours_vol, name="Volume", opacity=0.65,
        ), row=2, col=1)
        if "VOL_SMA20" in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df["VOL_SMA20"],
                line=dict(color=COLOURS["neutral"], width=1.2),
                name="Vol SMA20",
            ), row=2, col=1)

    # 7. MACD
    macd_row = 3 if show_volume else 2
    if all(c in df.columns for c in ["MACD", "MACD_sig", "MACD_hist"]):
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MACD"],
            line=dict(color=COLOURS["macd"], width=1.5),
            name="MACD",
        ), row=macd_row, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["MACD_sig"],
            line=dict(color=COLOURS["signal"], width=1.5),
            name="Signal",
        ), row=macd_row, col=1)
        hist_colours = [
            COLOURS["hist_pos"] if v >= 0 else COLOURS["hist_neg"]
            for v in df["MACD_hist"].fillna(0)
        ]
        fig.add_trace(go.Bar(
            x=df.index, y=df["MACD_hist"],
            marker_color=hist_colours, name="MACD Hist", opacity=0.7,
        ), row=macd_row, col=1)

    # 8. RSI
    rsi_row = 4 if show_volume else 3
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["RSI"],
            line=dict(color=COLOURS["neutral"], width=1.5),
            name="RSI",
        ), row=rsi_row, col=1)
        for level, colour in [(70, COLOURS["bear"]), (30, COLOURS["bull"])]:
            fig.add_hline(y=level, line_dash="dot",
                line_color=colour, line_width=1,
                row=rsi_row, col=1)
        fig.add_hrect(y0=70, y1=100,
            fillcolor=COLOURS["bear"], opacity=0.06,
            row=rsi_row, col=1)
        fig.add_hrect(y0=0, y1=30,
            fillcolor=COLOURS["bull"], opacity=0.06,
            row=rsi_row, col=1)

    # Final layout
    layout = _base_layout(f"{ticker} -- Technical Analysis")
    layout.update(height=750)
    fig.update_layout(**layout)

    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    if show_volume:
        fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="MACD", row=macd_row, col=1)
    fig.update_yaxes(title_text="RSI", row=rsi_row, col=1, range=[0, 100])

    for i in range(1, n_rows + 1):
        fig.update_xaxes(gridcolor=COLOURS["grid"], row=i, col=1)
        fig.update_yaxes(gridcolor=COLOURS["grid"], row=i, col=1)

    return fig


# -- Mini sparkline for the market overview index cards -----------------------

def build_mini_chart(df: pd.DataFrame, name: str, is_bullish: bool) -> go.Figure:
    """
    Compact line chart used in the market overview index cards.
    Shows last 60 days of Close price with SMA50 overlay.
    """
    recent = df.tail(60)
    colour = COLOURS["bull"] if is_bullish else COLOURS["bear"]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=recent.index, y=recent["Close"],
        line=dict(color=colour, width=2),
        fill="tozeroy",
        fillcolor="rgba({},{},{},0.10)".format(
            *[int(colour.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)]
        ),
        name=name,
    ))
    if "SMA_50" in recent.columns:
        fig.add_trace(go.Scatter(
            x=recent.index, y=recent["SMA_50"],
            line=dict(color=COLOURS["sma50"], width=1.2, dash="dot"),
            name="SMA50",
        ))

    fig.update_layout(
        height=160,
        paper_bgcolor=COLOURS["paper"],
        plot_bgcolor=COLOURS["bg"],
        margin=dict(l=5, r=5, t=5, b=5),
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(gridcolor=COLOURS["grid"], showgrid=True, tickfont=dict(size=9)),
        hovermode="x",
    )
    return fig


# -- Ride the Nine chart (9 EMA strategy) -------------------------------------

def build_ride_the_nine_chart(df: pd.DataFrame, ticker: str, rtn: dict) -> go.Figure:
    """
    Candlestick chart focused on the 9 EMA ('Ride the Nine' strategy).
    Shows last 90 bars with:
      - 9 EMA (bold, colour-coded to current signal)
      - 20 SMA (secondary dashed reference)
      - Price/EMA fill: green above, red below
      - Crossover markers
    """
    recent = df.tail(90).copy()
    signal = rtn.get("signal", "Neutral")
    ema_colour = (
        COLOURS["bull"]    if signal == "Above" else
        COLOURS["bear"]    if signal == "Below" else
        COLOURS["neutral"]
    )

    fig = go.Figure()

    # -- Green/red fill between close line and 9 EMA --------------------------
    if "EMA_9" in recent.columns:
        close_vals = recent["Close"].values
        ema9_vals  = recent["EMA_9"].values
        idx        = recent.index

        # Build masked arrays: NaN where the fill doesn't apply
        above = np.where(close_vals >= ema9_vals, close_vals, np.nan)
        below = np.where(close_vals <  ema9_vals, close_vals, np.nan)

        # Green fill (price above EMA)
        fig.add_trace(go.Scatter(
            x=idx, y=ema9_vals,
            line=dict(color="rgba(0,0,0,0)", width=0),
            showlegend=False, hoverinfo="skip", name="_ema_base_up",
        ))
        fig.add_trace(go.Scatter(
            x=idx, y=above,
            fill="tonexty", fillcolor="rgba(0,212,164,0.12)",
            line=dict(color="rgba(0,0,0,0)", width=0),
            showlegend=False, hoverinfo="skip", name="_fill_above",
        ))

        # Red fill (price below EMA)
        fig.add_trace(go.Scatter(
            x=idx, y=ema9_vals,
            line=dict(color="rgba(0,0,0,0)", width=0),
            showlegend=False, hoverinfo="skip", name="_ema_base_dn",
        ))
        fig.add_trace(go.Scatter(
            x=idx, y=below,
            fill="tonexty", fillcolor="rgba(255,75,110,0.12)",
            line=dict(color="rgba(0,0,0,0)", width=0),
            showlegend=False, hoverinfo="skip", name="_fill_below",
        ))

    # -- Candlesticks ----------------------------------------------------------
    fig.add_trace(go.Candlestick(
        x=recent.index, open=recent["Open"], high=recent["High"],
        low=recent["Low"],  close=recent["Close"],
        increasing_line_color=COLOURS["bull"],
        decreasing_line_color=COLOURS["bear"],
        name=ticker,
    ))

    # -- 9 EMA — the star of the show -----------------------------------------
    if "EMA_9" in recent.columns:
        fig.add_trace(go.Scatter(
            x=recent.index, y=recent["EMA_9"],
            line=dict(color=ema_colour, width=2.5),
            name="9 EMA",
        ))

    # -- 20 SMA — secondary reference -----------------------------------------
    if "SMA_20" in recent.columns:
        fig.add_trace(go.Scatter(
            x=recent.index, y=recent["SMA_20"],
            line=dict(color=COLOURS["sma50"], width=1.2, dash="dot"),
            name="20 SMA", opacity=0.7,
        ))

    # -- Crossover markers -----------------------------------------------------
    if "EMA_9" in recent.columns:
        up_x, up_y, dn_x, dn_y = [], [], [], []
        for i in range(1, len(recent)):
            prev_above = float(recent["Close"].iloc[i-1]) > float(recent["EMA_9"].iloc[i-1])
            curr_above = float(recent["Close"].iloc[i])   > float(recent["EMA_9"].iloc[i])
            ema_val    = float(recent["EMA_9"].iloc[i])
            if curr_above and not prev_above:
                up_x.append(recent.index[i]); up_y.append(ema_val)
            elif not curr_above and prev_above:
                dn_x.append(recent.index[i]); dn_y.append(ema_val)

        if up_x:
            fig.add_trace(go.Scatter(
                x=up_x, y=up_y, mode="markers",
                marker=dict(symbol="triangle-up", size=13, color=COLOURS["bull"],
                            line=dict(color="#ffffff", width=1)),
                name="Cross Up",
            ))
        if dn_x:
            fig.add_trace(go.Scatter(
                x=dn_x, y=dn_y, mode="markers",
                marker=dict(symbol="triangle-down", size=13, color=COLOURS["bear"],
                            line=dict(color="#ffffff", width=1)),
                name="Cross Down",
            ))

    layout = _base_layout(f"{ticker} \u2014 Ride the Nine (9 EMA)")
    layout.update(height=420)
    fig.update_layout(**layout)
    fig.update_yaxes(title_text="Price ($)")
    fig.update_xaxes(rangeslider=dict(visible=False), type="date")
    return fig


# -- Gauge / score meter for forecast confidence ------------------------------

def build_score_gauge(score: float, rating: str) -> go.Figure:
    """Renders a half-circle gauge showing the composite score from -1 to +1."""
    colour = {
        "Bullish": COLOURS["bull"],
        "Bearish": COLOURS["bear"],
        "Neutral": COLOURS["neutral"],
    }.get(rating, COLOURS["neutral"])

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=round(score * 100, 1),
        number=dict(suffix="", valueformat="+.1f", font=dict(color=colour, size=28)),
        delta=dict(reference=0, valueformat="+.1f"),
        title=dict(text=f"<b>{rating}</b>", font=dict(color=colour, size=18)),
        gauge=dict(
            axis=dict(
                range=[-100, 100], tickmode="array",
                tickvals=[-100, -50, 0, 50, 100],
                ticktext=["Bear -1", "-0.5", "Neutral", "+0.5", "Bull +1"],
                tickfont=dict(color=COLOURS["text"], size=9),
            ),
            bar=dict(color=colour, thickness=0.25),
            bgcolor=COLOURS["bg"],
            bordercolor=COLOURS["grid"],
            steps=[
                dict(range=[-100, -30], color="rgba(255,75,110,0.15)"),
                dict(range=[-30,   30], color="rgba(245,166,35,0.10)"),
                dict(range=[  30, 100], color="rgba(0,212,164,0.15)"),
            ],
            threshold=dict(
                line=dict(color=colour, width=3),
                thickness=0.8,
                value=round(score * 100, 1),
            ),
        ),
    ))

    fig.update_layout(
        height=220,
        paper_bgcolor=COLOURS["paper"],
        plot_bgcolor=COLOURS["bg"],
        margin=dict(l=30, r=30, t=40, b=10),
        font=dict(color=COLOURS["text"]),
    )
    return fig


# -- Community sentiment over time chart --------------------------------------

def build_sentiment_chart(sentiment_history: list) -> go.Figure:
    """Line chart of 7-day rolling % bullish community sentiment."""
    dates    = [item["date"] for item in sentiment_history]
    bull_pct = [item["bull_pct"] for item in sentiment_history]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates, y=bull_pct,
        mode="lines",
        line=dict(color="#00d4a4", width=2),
        fill="tozeroy",
        fillcolor="rgba(0,212,164,0.10)",
        name="% Bullish",
    ))
    fig.add_hline(y=50, line_dash="dot", line_color=COLOURS["grid"], line_width=1.5)

    layout = _base_layout("Community Sentiment Over Time (7-day rolling)")
    layout.update(height=200, margin=dict(l=50, r=20, t=40, b=30))
    fig.update_layout(**layout)
    fig.update_yaxes(range=[0, 100], title_text="% Bullish", ticksuffix="%")
    fig.update_xaxes(type="date")
    return fig
