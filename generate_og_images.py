"""
generate_og_images.py
Auto-discovers all HTML pages under www/ and generates 1200x630 OG images.

Run manually:       python3 generate_og_images.py
Specific file:      python3 generate_og_images.py www/blog/my-post.html
Regenerate all:     python3 generate_og_images.py --force
"""

import os, sys, re, glob, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WWW_DIR = "www"
OUT_DIR  = "www/og"
os.makedirs(OUT_DIR, exist_ok=True)

FORCE  = "--force" in sys.argv
TARGET = next((a for a in sys.argv[1:] if not a.startswith("--")), None)

F_BOLD    = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
F_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"

def font(path, size):
    return ImageFont.truetype(path, size)

# ── Short subtitles ────────────────────────────────────────────────────────
SHORT_SUBS = {
    "default":                          "All your signals. One dashboard.",
    "pricing":                          "Free to start. Upgrade anytime.",
    "faq":                              "Everything you need to know.",
    "demo":                             "See every signal. Live.",
    "blog":                             "Strategy. Signals. Edge.",
    "how-to-read-rsi":                  "Stop guessing. Start reading.",
    "ride-the-nine-strategy":           "Low risk. High conviction.",
    "how-to-read-technical-indicators": "See what professionals see.",
    "why-traders-fight-the-trend":      "The trend is always right.",
    "stock-prediction-markets":         "The crowd knows more than you think.",
}

# ── Palette ────────────────────────────────────────────────────────────────
BG        = (240, 242, 245)   # very light gray
DARK      = (15,  22,  40)    # near-black navy
GREEN     = (0,  168, 120)    # brand green (pill)
GRAY      = (107, 114, 128)   # subtitle
UP_C      = (38, 198, 160)    # teal-green candle
DN_C      = (235, 100, 100)   # soft coral-red candle
GLOW_C    = (120, 220, 185)   # soft mint for glow
WHITE     = (255, 255, 255)

W, H = 1200, 630

CANDLES = [
    (20, 28, 36, 12, True),
    (26, 21, 33, 15, False),
    (21, 37, 44, 17, True),
    (35, 47, 54, 28, True),
    (45, 38, 52, 32, False),
    (38, 57, 64, 33, True),
    (55, 70, 78, 49, True),
    (68, 61, 75, 54, False),
    (61, 79, 88, 56, True),
    (77, 91, 97, 72, True),
]

# ── HTML parsing ────────────────────────────────────────────────────────────
def parse_html(path):
    try:
        html = open(path, encoding="utf-8").read()
    except FileNotFoundError:
        return None
    tm = re.search(r"<title>([^<]+)</title>", html, re.I)
    dm = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.I)
    if not tm:
        return None
    title = re.sub(r'\s*[\|—–]\s*Stocklio.*$', '', tm.group(1)).strip()
    desc  = dm.group(1).strip() if dm else ""
    return {"title": title, "desc": desc}

def derive_label(html_path):
    rel  = html_path.replace("\\", "/")
    name = os.path.basename(rel).replace(".html", "")
    if "blog/" in rel and name == "index": return "BLOG"
    if "blog/" in rel:
        short = re.sub(r'\b(How To|The|A|An|And|Or|Of|In|For|With|That|This|Your)\b',
                       '', name.replace("-", " ").title(), flags=re.I)
        return "BLOG · " + " ".join(short.split())[:22].upper()
    if name == "pricing": return "PRICING"
    if name == "faq":     return "FAQ"
    if name == "demo":    return "LIVE DEMO"
    return None

def og_filename(html_path):
    rel   = os.path.relpath(html_path, WWW_DIR).replace("\\", "/")
    parts = rel.split("/")
    name  = parts[-1].replace(".html", "")
    if name == "index":
        return os.path.join(OUT_DIR,
            ("blog" if len(parts) > 1 and parts[-2] == "blog" else "default") + ".png")
    return os.path.join(OUT_DIR, name + ".png")

def wrap_title(text, max_chars=26):
    if len(text) <= max_chars:
        return [text]
    words = text.split()
    l1, l2 = [], []
    for w in words:
        if len(" ".join(l1 + [w])) <= max_chars: l1.append(w)
        else: l2.append(w)
    return [" ".join(l1), " ".join(l2)] if l2 else [" ".join(l1)]

def draw_rounded_rect(draw, x0, y0, x1, y1, r, fill):
    draw.rectangle([x0+r, y0, x1-r, y1], fill=fill)
    draw.rectangle([x0, y0+r, x1, y1-r], fill=fill)
    for cx, cy in [(x0, y0), (x1-2*r, y0), (x0, y1-2*r), (x1-2*r, y1-2*r)]:
        draw.ellipse([cx, cy, cx+2*r, cy+2*r], fill=fill)

# ── Render ──────────────────────────────────────────────────────────────────
def generate(html_path, out_path, label, title_lines, sub_text):
    img = Image.new("RGBA", (W, H), (*BG, 255))

    # ── 1. Large soft background glow (top-right origin) ──────────────────
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    gcx, gcy = W - 80, 60   # glow center: top-right
    for i in range(28, 0, -1):
        frac  = i / 28
        alpha = int(52 * frac**1.6)
        rx, ry = int(580 * frac), int(500 * frac)
        gd.ellipse([gcx-rx, gcy-ry, gcx+rx, gcy+ry], fill=(*GLOW_C, alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    img  = Image.alpha_composite(img, glow)

    # ── 2. Secondary glow bloom along the trend path (center-left) ────────
    glow2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd2   = ImageDraw.Draw(glow2)
    for i in range(16, 0, -1):
        frac  = i / 16
        alpha = int(28 * frac**2)
        rx, ry = int(260 * frac), int(220 * frac)
        gd2.ellipse([620-rx, 380-ry, 620+rx, 380+ry], fill=(*GLOW_C, alpha))
    glow2 = glow2.filter(ImageFilter.GaussianBlur(30))
    img   = Image.alpha_composite(img, glow2)

    draw = ImageDraw.Draw(img)

    # ── 3. Subtle arc ring (top-right decorative) ──────────────────────────
    draw.arc([W-460, -160, W+120, 420], start=140, end=200,
             fill=(*GLOW_C, 35), width=2)

    # ── 4. Smooth bezier trend line ────────────────────────────────────────
    bp0 = (180,  H + 10)      # start: bottom-left (off-image)
    bp1 = (560,  H - 60)      # control 1: gentle horizontal start
    bp2 = (940,  140)          # control 2: steep pull toward top-right
    bp3 = (W + 20, 20)        # end: top-right (slightly off-image)

    def bezier(t, p0, p1, p2, p3):
        u = 1 - t
        return (
            int(u**3*p0[0] + 3*u**2*t*p1[0] + 3*u*t**2*p2[0] + t**3*p3[0]),
            int(u**3*p0[1] + 3*u**2*t*p1[1] + 3*u*t**2*p2[1] + t**3*p3[1]),
        )

    curve    = [bezier(i/140, bp0, bp1, bp2, bp3) for i in range(141)]
    dot_ts   = [i/140 for i in range(14, 141, 18)]   # evenly-spaced dots

    tl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tl)

    # Green glow passes (soft, airy)
    for width, alpha in [(70, 6), (45, 12), (25, 22), (12, 40)]:
        for i in range(len(curve)-1):
            td.line([curve[i], curve[i+1]], fill=(*GLOW_C, alpha), width=width)

    # White line on top
    for width, alpha in [(5, 160), (2, 255)]:
        for i in range(len(curve)-1):
            td.line([curve[i], curve[i+1]], fill=(*WHITE, alpha), width=width)

    # Dots: green bloom + white center
    for t in dot_ts:
        pt = bezier(t, bp0, bp1, bp2, bp3)
        r  = 11
        td.ellipse([pt[0]-r,   pt[1]-r,   pt[0]+r,   pt[1]+r],   fill=(*GLOW_C, 120))
        td.ellipse([pt[0]-5,   pt[1]-5,   pt[0]+5,   pt[1]+5],   fill=(*WHITE,  220))
        td.ellipse([pt[0]-2,   pt[1]-2,   pt[0]+2,   pt[1]+2],   fill=(*WHITE,  255))

    tl  = tl.filter(ImageFilter.GaussianBlur(0.8))
    img = Image.alpha_composite(img, tl)

    # ── 5. Candlesticks (right half only, fading left → right) ────────────
    draw = ImageDraw.Draw(img)
    cx0, cx1 = 680, 1220    # candles start mid-right, end off-screen
    cy0, cy1 = 50,  580
    n    = len(CANDLES)
    slot = (cx1 - cx0) / n
    cw   = int(slot * 0.42)

    def sy(v):
        return int(cy1 - (v/100) * (cy1 - cy0))

    # Glow pass for candles
    cg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cgd = ImageDraw.Draw(cg)
    for i, (o, c, h, l, up) in enumerate(CANDLES):
        fade = 0.15 + 0.85 * (i / (n-1))
        xc   = int(cx0 + i * slot + slot/2)
        base = UP_C if up else DN_C
        col  = tuple(int(b * fade) for b in base)
        yo, yc_px = sy(o), sy(c)
        tb, bb = min(yo, yc_px), max(yo, yc_px)
        if bb - tb < 3: bb = tb + 3
        cgd.rectangle([xc-cw, tb-4, xc+cw, bb+4], fill=(*col, 45))
    cg  = cg.filter(ImageFilter.GaussianBlur(10))
    img = Image.alpha_composite(img, cg)

    draw = ImageDraw.Draw(img)
    for i, (o, c, h, l, up) in enumerate(CANDLES):
        fade = 0.15 + 0.85 * (i / (n-1))
        xc   = int(cx0 + i * slot + slot/2)
        base = UP_C if up else DN_C
        col  = tuple(int(b * fade) for b in base)
        yo, yc_px, yh, yl = sy(o), sy(c), sy(h), sy(l)
        draw.line([(xc, yh), (xc, yl)], fill=col, width=2)
        tb, bb = min(yo, yc_px), max(yo, yc_px)
        if bb - tb < 3: bb = tb + 3
        draw.rectangle([xc - cw//2, tb, xc + cw//2, bb], fill=col)

    # ── 6. Text ────────────────────────────────────────────────────────────
    # Label pill
    if label:
        f_lbl = font(F_BOLD, 19)
        tw    = int(draw.textlength(label, font=f_lbl))
        px0, py0, pad_x, pad_y = 52, 52, 18, 9
        draw_rounded_rect(draw, px0, py0, px0+tw+pad_x*2, py0+38, 10, GREEN)
        draw.text((px0+pad_x, py0+pad_y+1), label, font=f_lbl, fill=WHITE)
        title_y = 136
    else:
        title_y = 100

    # Title
    f_title = font(F_BOLD, 78)
    for i, line in enumerate(title_lines):
        draw.text((52, title_y + i*90), line, font=f_title, fill=DARK)

    # Subtitle
    f_sub = font(F_REGULAR, 30)
    sub_y = title_y + len(title_lines)*90 + 20
    draw.text((52, sub_y), sub_text, font=f_sub, fill=GRAY)

    # Logo
    f_logo = font(F_BOLD, 34)
    draw.text((52, H - 62), "stocklio", font=f_logo, fill=DARK, anchor="lm")
    dot_x = 52 + int(draw.textlength("stocklio", font=f_logo))
    draw.text((dot_x, H - 62), ".", font=f_logo, fill=GREEN, anchor="lm")

    # ── 7. Save ────────────────────────────────────────────────────────────
    out = Image.new("RGB", (W, H), BG)
    out.paste(img.convert("RGB"))
    out.save(out_path, "PNG", optimize=True)

# ── Entry point ─────────────────────────────────────────────────────────────
def process(html_path):
    out_path = og_filename(html_path)
    if not FORCE and os.path.exists(out_path):
        return False
    parsed = parse_html(html_path)
    if not parsed:
        print(f"  ⚠ skipped (no <title>): {html_path}")
        return False
    label       = derive_label(html_path)
    title_lines = wrap_title(parsed["title"])
    slug        = os.path.basename(out_path).replace(".png", "")
    sub_text    = SHORT_SUBS.get(slug, parsed["desc"][:60])
    generate(html_path, out_path, label, title_lines, sub_text)
    print(f"  ✓ {out_path}")
    return True

if TARGET:
    process(TARGET)
else:
    files     = sorted(set(glob.glob(f"{WWW_DIR}/**/*.html", recursive=True) +
                           glob.glob(f"{WWW_DIR}/*.html")))
    generated = sum(process(p) for p in files)
    skipped   = len(files) - generated
    print(f"\nDone — {generated} generated, {skipped} skipped (use --force to regenerate all)")
