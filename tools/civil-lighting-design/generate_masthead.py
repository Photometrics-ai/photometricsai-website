"""
Generates the Civil Lighting Design email masthead PNG from Overpass Bold.

Buttondown's email template can't load web fonts, so the masthead headline
is shipped as a raster image instead. Re-run this whenever the wordmark,
color, or size needs to change.

Usage: python generate_masthead.py
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
FONT_PATH = HERE / "fonts" / "overpass-bold.otf"
OUTPUT_PATH = HERE.parent.parent / "static" / "images" / "civil-lighting-design" / "masthead.png"

TEXT = "CIVIL LIGHTING DESIGN"
INK_COLOR = (26, 26, 46, 255)  # #1a1a2e

CANVAS_WIDTH = 1280  # 2x the 640px email display width
SIDE_MARGIN = 90
TOP_BOTTOM_PADDING = 40
TRACKING_RATIO = 0.12  # extra space between glyphs, as a fraction of font size


def tracked_text_width(draw, text, font, tracking):
    width = 0.0
    for ch in text:
        bbox = draw.textbbox((0, 0), ch, font=font)
        width += (bbox[2] - bbox[0]) if ch != " " else font.getlength(" ")
        width += tracking
    return width - tracking  # no trailing tracking after the last glyph


def find_font_size(draw, text, target_width, max_size=400):
    size = max_size
    while size > 10:
        font = ImageFont.truetype(str(FONT_PATH), size)
        tracking = size * TRACKING_RATIO
        if tracked_text_width(draw, text, font, tracking) <= target_width:
            return font, tracking
        size -= 2
    raise RuntimeError("Could not fit masthead text at any reasonable size")


def draw_tracked_text(draw, xy, text, font, tracking, fill):
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        bbox = draw.textbbox((0, 0), ch, font=font)
        advance = (bbox[2] - bbox[0]) if ch != " " else font.getlength(" ")
        x += advance + tracking


def main():
    scratch = Image.new("RGBA", (1, 1))
    scratch_draw = ImageDraw.Draw(scratch)

    target_width = CANVAS_WIDTH - 2 * SIDE_MARGIN
    font, tracking = find_font_size(scratch_draw, TEXT, target_width)

    ascent, descent = font.getmetrics()
    text_height = ascent + descent
    canvas_height = text_height + 2 * TOP_BOTTOM_PADDING

    img = Image.new("RGBA", (CANVAS_WIDTH, canvas_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    text_width = tracked_text_width(draw, TEXT, font, tracking)
    x = (CANVAS_WIDTH - text_width) / 2
    y = TOP_BOTTOM_PADDING

    draw_tracked_text(draw, (x, y), TEXT, font, tracking, INK_COLOR)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUTPUT_PATH)
    print(f"Wrote {OUTPUT_PATH} ({CANVAS_WIDTH}x{canvas_height}, font size {font.size}px)")


if __name__ == "__main__":
    main()
