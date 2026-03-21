"""
generate_og_images.py
Auto-discovers all HTML pages under www/ and generates a 1200x630 OG image
for any page that doesn't already have one in www/og/.

Run manually:          python3 generate_og_images.py
Run for one file:      python3 generate_og_images.py www/blog/my-post.html
Regenerate all:        python3 generate_og_images.py --force
"""

import os, sys, re, glob
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ── Config ────────────────────────────────────────────────────────────────────
WWW_DIR = "www"
OUT_DIR  = "www/og"
os.makedirs(OUT_DIR, exist_ok=True)

FORCE = "--force" in sys.argv
TARGET = next((a for a in sys.argv[1:] if not a.startswith("--")), None)

FONT_DIR = "/System/Library/Fonts/Supplemental"
SYS_FONT  = "/System/Library/Fonts"
F_BOLD    = f"{FONT_DIR}/Arial Bold.ttf"
F_REGULAR = f"{FONT_DIR}/Arial.ttf"

BG      = (238, 240, 243)
DARK    = (15,  20,  35)
GREEN   = (0,  168, 120)
RED     = (239, 83,  80)
WHITE   = (255, 255, 255)
GRAY    = (100, 110, 125)
GRID_C  = (200, 205, 212)
W, H    = 1200, 630

CANDLES = [
    (20, 28, 34, 12, True),
    (26, 22, 32, 16, False),
    (22, 36, 42, 18, True),
    (34, 46, 52, 28, True),
    (44, 38, 50, 32, False),
    (38, 56, 63, 34, True),
    (54, 68, 76, 48, True),
    (66, 60, 73, 54, False),
    (60, 78, 86, 56, True),
    (76, 90, 96, 72, True),
]

# ── HTML parsing ──────────────────────────────────────────────────────────────
def parse_html(path):
    try:
        with open(path, encoding="utf-8") as f:
            html = f.read()
    except FileNotFoundError:
        return None

    title_m = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
    desc_m  = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
    if not title_m:
        return None

    title = title_m.group(1).strip()
    desc  = desc_m.group(1).strip() if desc_m else ""

    # Strip trailing " | Stocklio" or " — Stocklio" from title
    title = re.sub(r'\s*[\|—–]\s*Stocklio.*$', '', title).strip()

    return {"title": title, "desc": desc}

def derive_label(html_path):
    """Infer the label pill text from the file path."""
    rel = html_path.replace("\\", "/")
    name = os.path.basename(rel).replace(".html", "")

    if "blog/" in rel and name == "index":
        return "BLOG"
    if "blog/" in rel:
        # Derive short topic from filename slug
        slug_words = name.replace("-", " ").title()
        # Keep it short — strip common filler words
        short = re.sub(r'\b(How To|The|A|An|And|Or|Of|In|For|With|That|This|Your)\b', '', slug_words, flags=re.I)
        short = ' '.join(short.split())[:28]
        return f"BLOG · {short.upper()}"
    if name == "pricing":   return "PRICING"
    if name == "faq":       return "FAQ"
    if name == "demo":      return "LIVE DEMO"
    return None  # homepage — no label

def og_filename(html_path):
    """Map www/blog/foo-bar.html → www/og/foo-bar.png"""
    rel  = os.path.relpath(html_path, WWW_DIR).replace("\\", "/")
    base = rel.replace("/", "-").replace(".html", "")
    # blog-index.html → blog.png, index.html → default.png
    if base == "blog-index":  base = "blog"
    if base == "index":       base = "default"
    return os.path.join(OUT_DIR, base + ".png")

# ── Drawing helpers ───────────────────────────────────────────────────────────
def font(path, size):
    return ImageFont.truetype(path, size)

def draw_rounded_rect(draw, x0, y0, x1, y1, r, fill):
    draw.rectangle([x0+r, y0, x1-r, y1], fill=fill)
    draw.rectangle([x0, y0+r, x1, y1-r], fill=fill)
    for cx, cy in [(x0, y0), (x1-2*r, y0), (x0, y1-2*r), (x1-2*r, y1-2*r)]:
        draw.ellipse([cx, cy, cx+2*r, cy+2*r], fill=fill)

def make_glow_layer(cx, cy, rx, ry, color_rgb, steps=22):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i in range(steps, 0, -1):
        frac  = i / steps
        alpha = int(55 * frac * frac)
        ex, ey = int(rx * frac), int(ry * frac)
        d.ellipse([cx-ex, cy-ey, cx+ex, cy+ey], fill=(*color_rgb, alpha))
    return layer.filter(ImageFilter.GaussianBlur(24))

def wrap_title(title, max_chars=28):
    """Split title into at most 2 lines at a word boundary."""
    if len(title) <= max_chars:
        return [title]
    words = title.split()
    line1, line2 = [], []
    for w in words:
        if len(" ".join(line1 + [w])) <= max_chars:
            line1.append(w)
        else:
            line2.append(w)
    return [" ".join(line1), " ".join(line2)] if line2 else [" ".join(line1)]

def wrap_sub(sub, max_chars=52):
    """Split subtitle into at most 2 lines."""
    if len(sub) <= max_chars:
        return [sub]
    words = sub.split()
    line1, line2 = [], []
    for w in words:
        if len(" ".join(line1 + [w])) <= max_chars:
            line1.append(w)
        else:
            line2.append(w)
    return [" ".join(line1), " ".join(line2)] if line2 else [" ".join(line1)]

# ── Render ────────────────────────────────────────────────────────────────────
def generate(html_path, out_path, label, title_lines, sub_lines):
    img  = Image.new("RGBA", (W, H), (*BG, 255))
    glow = make_glow_layer(cx=1010, cy=160, rx=480, ry=340, color_rgb=(0, 200, 140))
    img  = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # Subtle grid (right half)
    for gx in range(530, W, 72):
        draw.line([(gx, 0), (gx, H)], fill=(*GRID_C, 55), width=1)
    for gy in range(0, H, 72):
        draw.line([(530, gy), (W, gy)], fill=(*GRID_C, 55), width=1)

    # Candlesticks
    cx0, cx1 = 560, 1155
    cy0, cy1 = 60,  560
    n    = len(CANDLES)
    slot = (cx1 - cx0) / n
    cw   = int(slot * 0.48)

    def sy(v):
        return int(cy1 - (v / 100) * (cy1 - cy0))

    trend_pts = []
    for i, (o, c, h, l, up) in enumerate(CANDLES):
        fade  = 0.35 + 0.65 * (i / (n - 1))
        xctr  = int(cx0 + i * slot + slot / 2)
        base  = (38, 210, 160) if up else (239, 83, 80)
        color = tuple(int(255 - (255 - ch) * fade) for ch in base)
        yo, yc, yh, yl = sy(o), sy(c), sy(h), sy(l)
        draw.line([(xctr, yh), (xctr, yl)], fill=color, width=2)
        top_b, bot_b = min(yo, yc), max(yo, yc)
        if bot_b - top_b < 4: bot_b = top_b + 4
        draw.rectangle([xctr - cw//2, top_b, xctr + cw//2, bot_b], fill=color)
        trend_pts.append((xctr, yc))

    # Trend line
    tl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tl)
    for width, alpha in [(28, 18), (16, 40), (8, 100), (4, 200), (2, 255)]:
        for i in range(len(trend_pts) - 1):
            td.line([trend_pts[i], trend_pts[i+1]], fill=(255, 255, 255, alpha), width=width)
    for pt in trend_pts:
        r = 7
        td.ellipse([pt[0]-r, pt[1]-r, pt[0]+r, pt[1]+r], fill=(255,255,255,220))
        td.ellipse([pt[0]-3, pt[1]-3, pt[0]+3, pt[1]+3], fill=(200,255,235,255))
    tl  = tl.filter(ImageFilter.GaussianBlur(1))
    img = Image.alpha_composite(img, tl)
    draw = ImageDraw.Draw(img)

    # Label pill
    if label:
        f_lbl = font(F_BOLD, 19)
        tw    = int(draw.textlength(label, font=f_lbl))
        px0, py0, pad_x, pad_y = 58, 62, 16, 9
        draw_rounded_rect(draw, px0, py0, px0 + tw + pad_x*2, py0 + 38, 10, GREEN)
        draw.text((px0 + pad_x, py0 + pad_y), label, font=f_lbl, fill=WHITE)
        title_y = 148
    else:
        title_y = 110

    # Title
    f_title = font(F_BOLD, 68)
    for i, line in enumerate(title_lines):
        draw.text((58, title_y + i * 80), line, font=f_title, fill=DARK)

    # Subtitle
    f_sub = font(F_REGULAR, 28)
    sub_y = title_y + len(title_lines) * 80 + 24
    for i, line in enumerate(sub_lines):
        draw.text((58, sub_y + i * 40), line, font=f_sub, fill=GRAY)

    # Logo
    f_logo = font(F_BOLD, 30)
    logo_y = H - 58
    draw.text((58, logo_y), "stocklio", font=f_logo, fill=DARK, anchor="lm")
    dot_x = 58 + int(draw.textlength("stocklio", font=f_logo))
    draw.text((dot_x, logo_y), ".", font=f_logo, fill=GREEN, anchor="lm")

    out = Image.new("RGB", (W, H), BG)
    out.paste(img.convert("RGB"))
    out.save(out_path, "PNG", optimize=True)

# ── Main ──────────────────────────────────────────────────────────────────────
def process(html_path):
    out_path = og_filename(html_path)

    if not FORCE and os.path.exists(out_path):
        return False  # already exists, skip

    parsed = parse_html(html_path)
    if not parsed:
        print(f"  ⚠ skipped (no <title>): {html_path}")
        return False

    label       = derive_label(html_path)
    title_lines = wrap_title(parsed["title"])
    sub_lines   = wrap_sub(parsed["desc"]) if parsed["desc"] else [""]

    generate(html_path, out_path, label, title_lines, sub_lines)
    print(f"  ✓ {out_path}")
    return True

if TARGET:
    process(TARGET)
else:
    html_files = sorted(
        glob.glob(f"{WWW_DIR}/**/*.html", recursive=True) +
        glob.glob(f"{WWW_DIR}/*.html")
    )
    generated = sum(process(p) for p in html_files)
    skipped   = len(html_files) - generated
    print(f"\nDone — {generated} generated, {skipped} already existed (use --force to regenerate all)")
