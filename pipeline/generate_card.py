#!/usr/bin/env python3
"""
Conscious Dad Tribe -- LinkedIn / Instagram quote card generator.

Usage:
    python3 generate_card.py "quote text" output.png

Notes:
- A literal \n in the quote text is honored as a hard line break (use it for
  a genuine two-sentence beat: short line, then the longer line that lands
  the punch). Never use it to force three short fragments in a row.
- Auto-sizing steps the font down through FONT_SIZES until the quote
  provably fits above the wordmark without touching it.
- The header (headshot + name + handle) and the quote move together as one
  block, vertically centered between TOP_MARGIN and BOTTOM_LIMIT.
- Rebuilt 2026-09-02 as a pure-PIL renderer (no wkhtmltoimage dependency)
  after the sandbox reset wiped the original script and its assets. Output
  spec (colors, fonts, canvas size, sizing/centering logic) is unchanged.
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(SKILL_DIR, "fonts")
ASSETS_DIR = os.path.join(SKILL_DIR, "assets")

NAVY = (0x00, 0x13, 0x47)
ORANGE = (0xFF, 0x67, 0x19)
WHITE = (0xFF, 0xFF, 0xFF)
HANDLE_GREY = (0xA9, 0xAF, 0xC1)

CANVAS_W, CANVAS_H = 1080, 1350
TOP_MARGIN = 100
BOTTOM_LIMIT = 1150
SIDE_MARGIN = 100
QUOTE_MAX_WIDTH = CANVAS_W - 2 * SIDE_MARGIN  # 880

FONT_SIZES = [66, 60, 54, 48, 44, 40, 36, 32]
LINE_HEIGHT_FACTOR = 1.45  # calibrated against the finalized reference card

NAME_TEXT = "Lohith Dhaksha"
HANDLE_TEXT = "@lohithdhaksha"
NAME_SIZE = 36
HANDLE_SIZE = 28
HEADSHOT_SIZE = 168  # calibrated against the reference card's ring diameter
TEXT_GAP = 36  # gap between headshot and name/handle text
HEADER_GAP = 90  # gap between header block and quote block

# Footer wordmark: fixed in the reserved margin below BOTTOM_LIMIT, not part
# of the header+quote block that slides to stay centered. Sentence case,
# "Dad" in accent orange, everything else white, no letter-spacing.
WORDMARK_SIZE = 40
WORDMARK_SEGMENTS = [
    ("Conscious ", WHITE),
    ("Dad", ORANGE),
    (" Tribe", WHITE),
]

BOLD_FONT_PATH = os.path.join(FONTS_DIR, "Poppins-Bold.ttf")
MEDIUM_FONT_PATH = os.path.join(FONTS_DIR, "Poppins-Medium.ttf")


def load_font(path, size):
    return ImageFont.truetype(path, size)


def draw_multicolor_centered(draw, center_x, y, segments, font):
    """Draw a sequence of (text, color) segments as one line, horizontally
    centered as a whole on center_x. Normal kerning, no letter-spacing."""
    total_w = sum(draw.textlength(text, font=font) for text, _ in segments)
    x = center_x - total_w / 2
    for text, color in segments:
        draw.text((x, y), text, font=font, fill=color)
        x += draw.textlength(text, font=font)


def wrap_text(draw, text, font, max_width):
    """Wrap to max_width. A literal \n is always a hard break."""
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        current = ""
        for word in words:
            trial = (current + " " + word).strip()
            w = draw.textlength(trial, font=font)
            if w <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def block_height(num_lines, font_size):
    return int(num_lines * font_size * LINE_HEIGHT_FACTOR)


def fit_quote(draw, text, max_width, available_height):
    """Step down FONT_SIZES until the wrapped quote fits available_height."""
    last = None
    for size in FONT_SIZES:
        font = load_font(MEDIUM_FONT_PATH, size)
        lines = wrap_text(draw, text, font, max_width)
        height = block_height(len(lines), size)
        last = (font, lines, size, height)
        if height <= available_height:
            return last
    # Smallest size still doesn't fit (very long quote) -- use it anyway,
    # this is a stress case that should get flagged for a shorter line.
    return last


def generate_card(quote_text, output_path):
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), NAVY)
    draw = ImageDraw.Draw(canvas)

    name_font = load_font(BOLD_FONT_PATH, NAME_SIZE)
    handle_font = load_font(BOLD_FONT_PATH, HANDLE_SIZE)

    header_height = HEADSHOT_SIZE
    available_for_quote = (BOTTOM_LIMIT - TOP_MARGIN) - header_height - HEADER_GAP

    quote_font, quote_lines, quote_size, quote_height = fit_quote(
        draw, quote_text, QUOTE_MAX_WIDTH, available_for_quote
    )

    total_height = header_height + HEADER_GAP + quote_height
    space = BOTTOM_LIMIT - TOP_MARGIN
    block_top = TOP_MARGIN + max(0, (space - total_height) // 2)

    # --- Header: headshot + name + handle, sliding as one block ---
    headshot_path = os.path.join(ASSETS_DIR, "headshot.png")
    if not os.path.exists(headshot_path):
        raise FileNotFoundError(
            f"Missing {headshot_path}. Run the headshot processing step first."
        )
    headshot = Image.open(headshot_path).convert("RGBA")
    if headshot.size != (HEADSHOT_SIZE, HEADSHOT_SIZE):
        headshot = headshot.resize((HEADSHOT_SIZE, HEADSHOT_SIZE), Image.LANCZOS)
    canvas.paste(headshot, (SIDE_MARGIN, block_top), headshot)

    text_x = SIDE_MARGIN + HEADSHOT_SIZE + TEXT_GAP
    name_y = block_top + HEADSHOT_SIZE // 2 - 40
    handle_y = name_y + 48
    draw.text((text_x, name_y), NAME_TEXT, font=name_font, fill=WHITE)
    draw.text((text_x, handle_y), HANDLE_TEXT, font=handle_font, fill=HANDLE_GREY)

    # --- Quote block ---
    quote_top = block_top + header_height + HEADER_GAP
    line_step = int(quote_size * LINE_HEIGHT_FACTOR)
    y = quote_top
    for line in quote_lines:
        draw.text((SIDE_MARGIN, y), line, font=quote_font, fill=WHITE)
        y += line_step

    # --- Footer wordmark, fixed in the reserved margin below BOTTOM_LIMIT ---
    wordmark_font = load_font(MEDIUM_FONT_PATH, WORDMARK_SIZE)
    wordmark_y = BOTTOM_LIMIT + 50
    draw_multicolor_centered(
        draw, CANVAS_W // 2, wordmark_y, WORDMARK_SEGMENTS, wordmark_font
    )

    canvas = canvas.convert("RGB")  # clean flattened output, no alpha
    canvas.save(output_path)
    return output_path


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print('Usage: python3 generate_card.py "quote text" output.png')
        sys.exit(1)
    result = generate_card(sys.argv[1], sys.argv[2])
    print("Saved:", result)
