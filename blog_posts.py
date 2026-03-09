"""
blog/__init__.py -- Blog post data for Stocklio.

To add a new post, append a dict to POSTS with these fields:
  slug     - URL-safe identifier (used in ?post=slug)
  title    - Post title
  date     - ISO date string YYYY-MM-DD
  author   - Author name
  excerpt  - 1-2 sentence summary shown on the index card
  content  - Full post body in Markdown
  tags     - List of tag strings
"""

POSTS = [
    {
        "slug": "ride-the-nine-strategy",
        "title": "Ride the Nine: The 9 EMA Strategy Professional Traders Swear By",
        "date": "2025-03-05",
        "author": "Stocklio Team",
        "excerpt": "The 9 EMA is one of the most powerful — and most misunderstood — tools in a trader's toolkit. Here's how professional traders use it to find low-risk entries and early exit signals.",
        "tags": ["EMA", "Strategy", "Technical Analysis"],
        "content": """
The **9-period Exponential Moving Average** (9 EMA) is deceptively simple. It's just a fast-moving average that tracks the last nine candles. But in the hands of an experienced trader, it becomes a precision instrument for timing entries and exits.

## What Is the 9 EMA?

The 9 EMA is a trend-following indicator that gives more weight to recent price action than a simple moving average. Because it reacts quickly to price changes, it's especially useful in trending markets where momentum matters.

The core principle behind **Ride the Nine** is straightforward:

- **Prices above the 9 EMA** signal bullish momentum — the trend is your friend.
- **Prices below the 9 EMA** signal bearish momentum — shorts have the edge.
- **A touch of the 9 EMA** in a trending market is often a low-risk entry point.

## The Setup

The Ride the Nine strategy works best when:

1. The stock is in a clear trend (not choppy or range-bound)
2. Price has pulled back to touch or briefly dip below the 9 EMA
3. Volume confirms the move (higher volume on up days, lower on pullbacks)

When these three conditions align, a bounce off the 9 EMA can offer a high-probability trade with a well-defined stop-loss just below the average.

## Entry and Exit Rules

**Entry:** Buy when price closes back above the 9 EMA after a brief pullback to it. For more confirmation, wait for the candle to show a strong close (body in the upper half of the range).

**Stop-loss:** Place your stop below the most recent swing low or a fixed percentage below the 9 EMA, depending on your risk tolerance.

**Exit:** Consider scaling out when price extends significantly above the 9 EMA (more than 3–5% in a normal-volatility stock). A close back below the 9 EMA is often a signal to exit the remainder of the position.

## What to Watch Out For

The 9 EMA breaks down in sideways, low-volume markets. If a stock is trading in a tight range with no clear direction, the EMA will whipsaw and generate false signals. Always confirm the trend before applying this strategy.

Stocklio's chart analysis tab highlights 9 EMA crossovers and pullback signals automatically, so you can spot these setups at a glance rather than hunting through charts manually.

## Combining the 9 EMA with Other Signals

The Ride the Nine strategy is most powerful when paired with:

- **RSI** — An RSI near 50 during a pullback suggests the trend is intact, not reversing.
- **MACD** — A bullish MACD histogram while price touches the 9 EMA adds conviction.
- **Volume** — Declining volume on the pullback to the 9 EMA is a healthy sign. Surging volume on a pullback is a red flag.

Stocklio's composite score factors all of these in automatically, giving you a single signal to evaluate rather than manually cross-referencing three separate charts.
""",
    },
    {
        "slug": "how-to-read-rsi",
        "title": "How to Read RSI Like a Pro (And Stop Making the Most Common Mistakes)",
        "date": "2025-02-20",
        "author": "Stocklio Team",
        "excerpt": "RSI above 70 means sell, right? Not exactly. Most traders misuse the Relative Strength Index. Here's how to read it correctly — and how to use it alongside other signals.",
        "tags": ["RSI", "Indicators", "Technical Analysis"],
        "content": """
The **Relative Strength Index (RSI)** is one of the most widely cited indicators in technical analysis — and one of the most frequently misread. The classic rule of thumb ("above 70 = overbought, sell; below 30 = oversold, buy") is a simplification that causes more losses than it prevents.

## What RSI Actually Measures

RSI compares the average size of recent up-moves to the average size of recent down-moves over a specified period (typically 14 periods). The result is a number between 0 and 100.

The key insight most traders miss: **RSI measures momentum, not direction.** A stock can stay "overbought" (RSI > 70) for weeks during a strong uptrend. Selling just because RSI crossed 70 means selling into strength — the opposite of what you want.

## The Right Way to Use RSI

**1. Trend confirmation, not reversal signals**

In a strong uptrend, RSI tends to oscillate between 40 and 80, rarely dipping below 40. In a downtrend, it oscillates between 20 and 60. If you know which regime you're in, RSI becomes a much better tool:

- Uptrend: treat RSI dips to 40–50 as potential buy zones, not RSI spikes above 70.
- Downtrend: treat RSI bounces to 50–60 as potential short opportunities.

**2. Divergence**

RSI divergence is one of the more reliable signals in technical analysis:

- **Bearish divergence:** Price makes a higher high, but RSI makes a lower high. Momentum is weakening even as price climbs — a warning sign.
- **Bullish divergence:** Price makes a lower low, but RSI makes a higher low. Selling pressure is drying up — a potential reversal signal.

Divergence works best at key support/resistance levels, not in isolation.

**3. RSI midline (50) as a trend filter**

The 50 level on RSI acts as a rough trend divider. RSI consistently above 50 suggests bullish bias; consistently below 50 suggests bearish bias. Use this to filter out trades that go against the prevailing momentum.

## What Stocklio Shows You

Stocklio calculates RSI on your chosen timeframe and flags divergence patterns automatically. The composite score weights RSI alongside MACD, Bollinger Bands, and volume so you're never making a decision based on one indicator alone.

The best traders don't follow any single indicator. They look for confluence — multiple signals pointing in the same direction at the same time. That's exactly what Stocklio is built to surface.
""",
    },
    {
        "slug": "market-sentiment-explained",
        "title": "Why Market Sentiment Matters More Than You Think",
        "date": "2025-02-05",
        "author": "Stocklio Team",
        "excerpt": "Price doesn't move on fundamentals alone — it moves on what investors believe, fear, and expect. Understanding market sentiment can give you an edge that pure technical analysis misses.",
        "tags": ["Sentiment", "Psychology", "Strategy"],
        "content": """
Markets are not perfectly rational machines. They're driven by millions of people making decisions under uncertainty, shaped by hope, fear, greed, and overconfidence. This is why **market sentiment** — the collective mood of investors toward a stock or the broader market — is a signal worth tracking alongside technical indicators.

## The Gap Between Price and Reality

Consider two stocks with identical fundamentals: same revenue growth, same margins, same debt levels. One trades at 30x earnings, the other at 12x. Why? Sentiment. One has captured the imagination of the investing public; the other hasn't.

This sentiment premium is real, persistent, and tradeable — if you know how to measure it.

## How Sentiment Moves Price

When a stock has strong bullish sentiment:
- More buyers are waiting to add on dips, creating support
- Short sellers are hesitant to fight the crowd, reducing downward pressure
- Momentum traders pile in as the trend becomes self-reinforcing

The reverse is equally true. A stock with strongly bearish sentiment can stay depressed longer than fundamentals justify, because fear and negative momentum suppress buying interest.

## Measuring Sentiment

There's no single perfect sentiment indicator, but some of the most useful proxies include:

**Put/Call ratio** — A high ratio of puts to calls signals fear and potential pessimism about a stock. Extreme readings can be contrarian indicators.

**Short interest** — High short interest means a lot of investors are betting against a stock. If the stock starts moving up, forced short-covering can amplify the move (a "short squeeze").

**Social and news sentiment** — Retail investor chatter on forums and social media has proven capable of moving individual stocks dramatically, as meme stock episodes have demonstrated.

**Prediction markets** — When a large group of informed individuals put skin in the game on a directional call, the aggregate signal tends to be more accurate than any individual forecast.

## Stocklio's Prediction Market

Stocklio's community prediction market lets real investors vote on where a stock is headed over the next 30 days. The platform tracks the accuracy of past predictions so you can see whether the crowd has been right or wrong on a given stock.

Used alone, crowd sentiment is noisy. But when the community sentiment aligns with the AI composite score and key technical levels, the confluence is a meaningful signal — not a guarantee, but a genuine edge.

The best trades combine multiple independent data sources pointing in the same direction. Sentiment is one layer. Technical analysis is another. Together, they build a more complete picture than either could alone.
""",
    },
]


def get_all_posts():
    return sorted(POSTS, key=lambda p: p["date"], reverse=True)


def get_post_by_slug(slug: str):
    for post in POSTS:
        if post["slug"] == slug:
            return post
    return None
