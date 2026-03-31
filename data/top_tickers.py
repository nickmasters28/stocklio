"""
Top tickers for the daily batch builder.
Ordered roughly by trading volume / retail interest.
Expand or trim this list as needed.
"""

TOP_TICKERS = [
    # Mega-cap tech
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "GOOG", "META", "TSLA", "AVGO", "AMD",
    # Financials
    "JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW", "AXP", "V", "MA", "PYPL",
    # Healthcare
    "UNH", "JNJ", "LLY", "ABBV", "MRK", "PFE", "TMO", "ABT", "DHR", "BMY",
    # Consumer
    "AMZN", "COST", "WMT", "HD", "MCD", "SBUX", "NKE", "TGT", "LOW", "TJX",
    # Energy
    "XOM", "CVX", "COP", "SLB", "EOG", "PSX", "VLO", "MPC", "OXY", "HAL",
    # Industrials
    "CAT", "DE", "HON", "GE", "RTX", "BA", "LMT", "UPS", "FDX", "MMM",
    # Communication
    "NFLX", "DIS", "T", "VZ", "CMCSA", "TMUS", "ATVI", "EA", "TTWO",
    # Semis & hardware
    "INTC", "QCOM", "MU", "TXN", "AMAT", "LRCX", "KLAC", "MRVL", "ON", "NXPI",
    # Cloud & software
    "CRM", "ORCL", "SAP", "NOW", "SNOW", "PLTR", "DDOG", "NET", "ZS", "CRWD",
    "PANW", "FTNT", "OKTA", "MDB", "GTLB", "HCP", "HUBS", "WDAY", "VEEV",
    # EV & clean energy
    "RIVN", "LCID", "NIO", "XPEV", "LI", "PLUG", "FCEL", "BE", "ENPH", "SEDG",
    # Biotech
    "MRNA", "BNTX", "REGN", "VRTX", "BIIB", "GILD", "AMGN", "ILMN", "SGEN",
    # ETFs (high retail volume)
    "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "ARKK", "SQQQ", "TQQQ", "SPXU",
    "GLD", "SLV", "TLT", "HYG", "XLF", "XLK", "XLE", "XLV", "XLI", "XLY",
    # High retail interest
    "GME", "AMC", "BBBY", "HOOD", "SOFI", "UPST", "AFRM", "OPEN", "COIN",
    "MSTR", "RIOT", "MARA", "HUT", "CLSK", "CIFR",
    # Mid-cap growth
    "UBER", "LYFT", "ABNB", "DASH", "SNAP", "PINS", "RDDT", "RBLX",
    "SPOT", "DKNG", "PENN", "MGM", "WYNN", "LVS",
    # International ADRs
    "BABA", "JD", "PDD", "BIDU", "TCEHY", "TSM", "ASML", "SAP", "TM", "SONY",
    "ARM", "SHOP", "SE", "GRAB", "VALE", "PBR", "BBD",
    # S&P 500 staples
    "PG", "KO", "PEP", "PM", "MO", "CL", "KMB", "CHD", "CLX", "GIS",
    "K", "CPB", "SJM", "HRL", "CAG", "MKC", "TSN", "HRL",
    # REITs
    "AMT", "PLD", "EQIX", "CCI", "SPG", "O", "VICI", "WPC", "PSA", "EXR",
    # Utilities
    "NEE", "DUK", "SO", "D", "EXC", "AEP", "SRE", "PCG", "ED", "WEC",
    # Additional high-volume names
    "F", "GM", "RIVN", "STLA", "TM", "HMC", "RACE",
    "ZM", "DOCU", "BOX", "TWLO", "FSLY", "U", "RDFN",
    "LULU", "RH", "W", "ETSY", "EBAY", "OSTK",
    "CHWY", "PTON", "NKE", "UAA", "COLM", "VF",
    "SQ", "AFRM", "UPST", "LC", "ENVA", "PFSI",
    "WBD", "PARA", "FOXA", "NYT", "IAC",
    "RDFN", "Z", "OPEN", "EXPI", "HOUS",
    "DAL", "UAL", "AAL", "LUV", "ALK", "JBLU", "HA",
    "CCL", "NCLH", "RCL", "MAR", "HLT", "H", "IHG",
]

# Deduplicate while preserving order
_seen = set()
TOP_TICKERS = [t for t in TOP_TICKERS if not (_seen.add(t) or t in _seen)]
