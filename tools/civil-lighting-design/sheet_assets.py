"""
Rasterized sheet furniture for Civil Lighting Design: masthead+STA banner,
matchline dividers, and the title block.

Why rasterize instead of styling live HTML text: Buttondown/email clients
do not reliably load custom @font-face fonts, so any font-family set in
inline CSS silently falls back to a web-safe font (Arial/Helvetica/Courier
New) on almost every recipient's screen. That's fine for body copy, but it
means the elements that are supposed to carry the "civil engineering plan
sheet" identity -- the title block, the STA line, the matchline dividers --
were never actually rendering in the drafting-style lettering they were
designed with. Baking these three elements to PNG (same technique already
used for the wordmark) guarantees the real typeface, exact tracking, and
correct lineweight hierarchy render identically in every mail client,
because they're pixels, not text.

Typeface: Overpass (bold, for the wordmark) and Overpass Mono (for all
tracked-caps technical lettering: STA line, matchline labels, title block
labels/values). Both are dual OFL/LGPL licensed (see fonts/LICENSE-OVERPASS.md)
and were chosen deliberately -- Overpass was originally commissioned by
Red Hat as a redraw of U.S. highway signage lettering (Highway Gothic), so
using it site-wide (instead of the previous mix of Overpass/Courier
New/Work Sans) actually has the right lineage for a DOT-style plan sheet,
and keeps one consistent lettering family across the whole sheet the way a
real drawing set does.
"""

import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
FONTS = HERE / "fonts"
FONT_BOLD = FONTS / "overpass-bold.otf"
FONT_VAR = FONTS / "overpass-variable.ttf"
FONT_ITALIC_VAR = FONTS / "overpass-italic-variable.ttf"
FONT_MONO_VAR = FONTS / "overpassmono-variable.ttf"

STATIC_DIR = HERE.parent.parent / "static" / "images" / "civil-lighting-design"
BASE_URL = "https://photometrics.ai/images/civil-lighting-design"

INK = (26, 26, 46, 255)            # #1a1a2e
ACCENT_TEXT = (42, 111, 155, 255)  # #2A6F9B
BODY_TEXT = (74, 85, 104, 255)     # #4a5568
MUTED_TEXT = (113, 128, 150, 255)  # #718096
HAIRLINE = (201, 208, 216, 255)    # #c9d0d8
WHITE = (255, 255, 255, 255)

SCALE = 2  # 2x canvas for retina email rendering

# Two display widths: the wordmark is a centered element narrower than the
# content column; the title block and matchlines span the full content
# column (the sheet's inner white area, after its 40px padding each side).
MASTHEAD_DISPLAY_W = 480
CONTENT_DISPLAY_W = 560
MASTHEAD_CANVAS_W = MASTHEAD_DISPLAY_W * SCALE
CONTENT_CANVAS_W = CONTENT_DISPLAY_W * SCALE


def _font(path, size, weight=None):
    f = ImageFont.truetype(str(path), size)
    if weight is not None:
        try:
            f.set_variation_by_axes([weight])
        except OSError:
            pass
    return f


def overpass(size, weight=400):
    return _font(FONT_VAR, size, weight)


def overpass_bold_static(size):
    return ImageFont.truetype(str(FONT_BOLD), size)


def overpass_mono(size, weight=500):
    return _font(FONT_MONO_VAR, size, weight)


_scratch_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))


def tracked_width(text, font, tracking):
    if not text:
        return 0.0
    width = sum(font.getlength(ch) + tracking for ch in text)
    return width - tracking


def draw_tracked(draw, xy, text, font, tracking, fill):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + tracking


def line_height(font):
    ascent, descent = font.getmetrics()
    return ascent + descent


def _save(img, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


def generate_masthead_sta(issue_number, publish_date):
    """Wordmark + STA line, combined into one image (STA changes per issue)."""
    issue_str = f"{issue_number:02d}"
    title_text = "CIVIL LIGHTING DESIGN"
    sta_text = f"STA {issue_str}+00   ·   {publish_date.strftime('%B %Y').upper()}"

    side_margin = 28
    target_w = MASTHEAD_CANVAS_W - 2 * side_margin
    size = 300
    title_font, title_tracking = None, None
    while size > 10:
        f = overpass_bold_static(size)
        tracking = size * 0.12
        if tracked_width(title_text, f, tracking) <= target_w:
            title_font, title_tracking = f, tracking
            break
        size -= 2
    if title_font is None:
        raise RuntimeError("Could not fit masthead title")

    title_w = tracked_width(title_text, title_font, title_tracking)
    title_h = line_height(title_font)

    sta_size = 42
    sta_font = overpass_mono(sta_size, weight=600)
    sta_tracking = sta_size * 0.22
    sta_w = tracked_width(sta_text, sta_font, sta_tracking)
    sta_h = line_height(sta_font)

    top_pad, gap, bottom_pad = 16, 26, 16
    canvas_h = top_pad + title_h + gap + sta_h + bottom_pad

    img = Image.new("RGBA", (MASTHEAD_CANVAS_W, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_tracked(draw, ((MASTHEAD_CANVAS_W - title_w) / 2, top_pad), title_text, title_font, title_tracking, INK)
    draw_tracked(draw, ((MASTHEAD_CANVAS_W - sta_w) / 2, top_pad + title_h + gap), sta_text, sta_font, sta_tracking, ACCENT_TEXT)

    path = STATIC_DIR / f"masthead-{issue_str}.png"
    _save(img, path)
    return {
        "url": f"{BASE_URL}/masthead-{issue_str}.png",
        "canvas_w": target_w,
        "canvas_h": canvas_h,
        "display_w": MASTHEAD_DISPLAY_W,
        "display_h": round(canvas_h / SCALE),
    }


def generate_matchline(section_name):
    """One static image per fixed section name (section taxonomy doesn't
    change per issue, so these are generated once, not per-issue)."""
    slug = re.sub(r"[^a-z0-9]+", "-", section_name.lower()).strip("-")
    label = f"MATCH LINE — {section_name.upper()}"

    font_size = 24
    font = overpass_mono(font_size, weight=600)
    tracking = font_size * 0.30
    text_w = tracked_width(label, font, tracking)
    text_h = line_height(font)

    rule_y = 22
    tick_half = 8
    gap_below_rule = 16
    bottom_pad = 4
    canvas_h = rule_y + tick_half + gap_below_rule + text_h + bottom_pad

    img = Image.new("RGBA", (CONTENT_CANVAS_W, canvas_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    margin = 0
    rule_w = 4  # bolder than a decorative hairline -- this is a drafted line, not a rule
    dash_len, gap_len = 20, 12
    x = margin
    right = CONTENT_CANVAS_W - margin
    while x < right:
        x_end = min(x + dash_len, right)
        draw.line([(x, rule_y), (x_end, rule_y)], fill=BODY_TEXT, width=rule_w)
        x = x_end + gap_len

    for tx in (margin, right):
        draw.line([(tx, rule_y - tick_half), (tx, rule_y + tick_half)], fill=INK, width=rule_w)

    tx = (CONTENT_CANVAS_W - text_w) / 2
    ty = rule_y + tick_half + gap_below_rule
    draw_tracked(draw, (tx, ty), label, font, tracking, BODY_TEXT)

    path = STATIC_DIR / f"matchline-{slug}.png"
    _save(img, path)
    return {
        "url": f"{BASE_URL}/matchline-{slug}.png",
        "slug": slug,
        "canvas_w": CONTENT_CANVAS_W,
        "canvas_h": canvas_h,
        "display_w": CONTENT_DISPLAY_W,
        "display_h": round(canvas_h / SCALE),
    }


def generate_north_arrow():
    """Static compass icon -- matches the rotation/north icon in the top
    corner of the DelDOT reference sheet. Purely a drafting convention
    marker (no real-world orientation claim, same as a title block corner
    ornament), unlike a scale bar -- see generate_titleblock() for why a
    scale bar is deliberately NOT included."""
    size = 120
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = size / 2
    shaft_top = 34
    shaft_bottom = size - 22
    draw.line([(cx, shaft_bottom), (cx, shaft_top)], fill=INK, width=4)
    ah = 14
    draw.polygon([(cx - ah * 0.6, shaft_top), (cx + ah * 0.6, shaft_top), (cx, shaft_top - 16)], fill=INK)

    r = 5
    draw.ellipse([cx - r, shaft_bottom - r, cx + r, shaft_bottom + r], outline=INK, width=3)

    font = overpass_bold_static(22)
    w = font.getlength("N")
    draw.text((cx - w / 2, 2), "N", font=font, fill=INK)

    path = STATIC_DIR / "north-arrow.png"
    _save(img, path)
    return {
        "url": f"{BASE_URL}/north-arrow.png",
        "canvas_w": size,
        "canvas_h": size,
        "display_w": size // 2,
        "display_h": size // 2,
    }


def generate_corridor_schematic():
    """A thin plan-view stand-in: a corridor centerline with evenly spaced
    fixture nodes and station ticks. This is the one piece of the
    reference sheet's dominant content -- an actual plan-view drawing --
    that has an honest analog here (Photometrics.ai's real subject is
    networked fixtures along a corridor), so it's a legitimate thematic
    borrow rather than fabricated geographic/utility data. It carries no
    real station values or coordinates -- it's schematic, and labeled as
    such, the same way STA 01+00 is an issue marker, not a real chainage."""
    width = CONTENT_CANVAS_W
    n_nodes = 7
    margin = 20
    line_y = 34
    r = 7

    label_font = overpass_mono(18, weight=600)
    label = "TARGET LIGHTING LAYER — CORRIDOR SCHEMATIC"
    tracking = 18 * 0.16
    label_w = tracked_width(label, label_font, tracking)
    label_h = line_height(label_font)

    height = line_y + r + 14 + label_h + 6

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw.line([(margin, line_y), (width - margin, line_y)], fill=HAIRLINE, width=3)
    for i in range(n_nodes):
        x = margin + i * (width - 2 * margin) / (n_nodes - 1)
        draw.ellipse([x - r, line_y - r, x + r, line_y + r], outline=INK, width=3, fill=WHITE)
        draw.line([(x, line_y + r + 3), (x, line_y + r + 10)], fill=BODY_TEXT, width=2)

    draw_tracked(draw, ((width - label_w) / 2, line_y + r + 14), label, label_font, tracking, MUTED_TEXT)

    path = STATIC_DIR / "corridor-schematic.png"
    _save(img, path)
    return {
        "url": f"{BASE_URL}/corridor-schematic.png",
        "canvas_w": width,
        "canvas_h": height,
        "display_w": CONTENT_DISPLAY_W,
        "display_h": round(height / SCALE),
    }


def generate_titleblock(issue_number, publish_date):
    issue_str = f"{issue_number:02d}"
    tb_date = publish_date.strftime("%m/%d/%y")

    col_w = [round(CONTENT_CANVAS_W * 0.36), 0, 0]
    remaining = CONTENT_CANVAS_W - col_w[0]
    col_w[1] = remaining // 2
    col_w[2] = remaining - col_w[1]

    pad_x = 22
    pad_y = 28
    label_size = 20
    value_size = 22
    title_size = 24
    sub_size = 18
    row_h = 42

    height = pad_y * 2 + row_h * 3

    img = Image.new("RGBA", (CONTENT_CANVAS_W, height), WHITE)
    draw = ImageDraw.Draw(img)

    # Lineweight hierarchy: outer border as heavy as the sheet's own
    # neatline (this box is meant to read as a solid, definitive block,
    # not a faint one) -- internal grid lines much thinner, matching how
    # DOT title blocks are actually drawn.
    border_w = 6   # == the 3px-at-display-scale neatline weight
    divider_w = 2  # thin internal grid

    x0 = col_w[0]
    x1 = col_w[0] + col_w[1]

    draw.line([(x0, 0), (x0, height)], fill=HAIRLINE, width=divider_w)
    draw.line([(x1, 0), (x1, height)], fill=HAIRLINE, width=divider_w)
    draw.rectangle([0, 0, CONTENT_CANVAS_W - 1, height - 1], outline=INK, width=border_w)

    # Column 1: wordmark + attribution (attribution is plain text here --
    # linking lives outside the image, in the footer, since a link baked
    # into a raster has no real hyperlink underneath it)
    title_font = overpass_bold_static(title_size)
    sub_font = overpass_mono(sub_size, weight=500)
    sub_tracking = sub_size * 0.14
    title_h = line_height(title_font)
    sub_h = line_height(sub_font)
    block_h = title_h + 8 + sub_h
    ty = (height - block_h) / 2
    draw.text((pad_x, ty), "CIVIL LIGHTING DESIGN", font=title_font, fill=INK)
    draw_tracked(draw, (pad_x, ty + title_h + 8), "PUBLISHED BY EVARILABS", sub_font, sub_tracking, BODY_TEXT)

    def draw_rows(x_start, width, rows):
        label_font = overpass_mono(label_size, weight=500)
        value_font = overpass_mono(value_size, weight=700)
        label_tracking = label_size * 0.12
        for i, (label, value) in enumerate(rows):
            ry = pad_y + i * row_h
            if i > 0:
                draw.line([(x_start, ry), (x_start + width, ry)], fill=HAIRLINE, width=divider_w)
            label_y = ry + (row_h - line_height(label_font)) / 2
            draw_tracked(draw, (x_start + pad_x, label_y), label, label_font, label_tracking, BODY_TEXT)
            value_w = value_font.getlength(value)
            value_y = ry + (row_h - line_height(value_font)) / 2
            draw.text((x_start + width - pad_x - value_w, value_y), value, font=value_font, fill=INK)

    draw_rows(x0, col_w[1], [("ISSUE", issue_str), ("DATE", tb_date), ("SHEET", "1 OF 1")])
    draw_rows(x1, col_w[2], [("DRAWN", "AI"), ("CHECKED", "AI"), ("SCALE", "NTS")])

    path = STATIC_DIR / f"titleblock-{issue_str}.png"
    _save(img, path)
    return {
        "url": f"{BASE_URL}/titleblock-{issue_str}.png",
        "canvas_w": CONTENT_CANVAS_W,
        "canvas_h": height,
        "display_w": CONTENT_DISPLAY_W,
        "display_h": round(height / SCALE),
    }


SECTION_NAMES = ["From Photometrics.ai", "Around the Industry", "Standards and Committees"]


def generate_all_matchlines():
    return {name: generate_matchline(name) for name in SECTION_NAMES}


if __name__ == "__main__":
    from datetime import date

    m = generate_masthead_sta(1, date(2026, 8, 19))
    print("masthead:", m["url"])
    t = generate_titleblock(1, date(2026, 8, 19))
    print("titleblock:", t["url"])
    for name, info in generate_all_matchlines().items():
        print("matchline:", name, "->", info["url"])
