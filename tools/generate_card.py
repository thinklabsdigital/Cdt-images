#!/usr/bin/env python3
"""
Conscious Dad Tribe quote card generator.
Recreated in this session from a real exported card (measured pixel positions),
since /home/claude does not persist between sessions. Layout constants below
were sampled directly from whatever-you-make-of-it-100.png.
"""
import sys
import os
from PIL import Image, ImageDraw, ImageFont

CANVAS_W, CANVAS_H = 1080, 1350
BG = (0x00, 0x13, 0x47)
ORANGE = (0xFF, 0x67, 0x19)
WHITE = (255, 255, 255)
HANDLE_COLOR = (0xA9, 0xAF, 0xC1)

LEFT_MARGIN = 100
RIGHT_MARGIN = 100
TEXT_WIDTH = CANVAS_W - LEFT_MARGIN - RIGHT_MARGIN

TOP_MARGIN = 100
BOTTOM_LIMIT = 1150

HEADSHOT_SIZE = 176
HEADER_TEXT_GAP = 32
NAME_SIZE = 36
HANDLE_SIZE = 30
NAME_HANDLE_GAP = 8

HEADER_QUOTE_GAP = 100

FONT_SIZES = [66, 60, 54, 48, 44, 40, 36, 32]
LINE_HEIGHT_RATIO = 1.45

WORDMARK_SIZE = 40
WORDMARK_Y_CENTER = 1216

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
BOLD_FONT_PATH = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
MEDIUM_FONT_PATH = "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf"
HEADSHOT_PATH = os.path.join(ASSETS_DIR, "headshot.png")

NAME_TEXT = "Lohith Dhaksha"
HANDLE_TEXT = "@lohithdhaksha"


def wrap_paragraph(text, font, max_width, draw):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = (current + " " + word).strip()
        if draw.textlength(candidate, font=font) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def wrap_quote(text, font, max_width, draw):
    paragraphs = text.split("\n")
    all_lines = []
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        all_lines.extend(wrap_paragraph(p, font, max_width, draw))
    return all_lines


def pick_font_size_and_lines(text, draw):
    for size in FONT_SIZES:
        font = ImageFont.truetype(MEDIUM_FONT_PATH, size)
        lines = wrap_quote(text, font, TEXT_WIDTH, draw)
        quote_height = len(lines) * size * LINE_HEIGHT_RATIO
        total_block = HEADSHOT_SIZE + HEADER_QUOTE_GAP + quote_height
        if total_block <= (BOTTOM_LIMIT - TOP_MARGIN):
            return size, lines, quote_height
    # floor: smallest size, accept overflow rather than crash
    size = FONT_SIZES[-1]
    font = ImageFont.truetype(MEDIUM_FONT_PATH, size)
    lines = wrap_quote(text, font, TEXT_WIDTH, draw)
    quote_height = len(lines) * size * LINE_HEIGHT_RATIO
    return size, lines, quote_height


def generate_card(quote_text, output_path):
    img = Image.new("RGB", (CANVAS_W, CANVAS_H), BG)
    draw = ImageDraw.Draw(img)

    quote_size, quote_lines, quote_height = pick_font_size_and_lines(quote_text, draw)
    quote_font = ImageFont.truetype(MEDIUM_FONT_PATH, quote_size)

    total_block = HEADSHOT_SIZE + HEADER_QUOTE_GAP + quote_height
    available = BOTTOM_LIMIT - TOP_MARGIN
    block_top = TOP_MARGIN + max(0, (available - total_block) / 2)

    header_top = block_top
    quote_top = header_top + HEADSHOT_SIZE + HEADER_QUOTE_GAP

    # Headshot
    headshot = Image.open(HEADSHOT_PATH).convert("RGBA")
    if headshot.size != (HEADSHOT_SIZE, HEADSHOT_SIZE):
        headshot = headshot.resize((HEADSHOT_SIZE, HEADSHOT_SIZE), Image.LANCZOS)
    img.paste(headshot, (LEFT_MARGIN, int(header_top)), headshot)

    # Name / handle, vertically centered against the headshot
    name_font = ImageFont.truetype(BOLD_FONT_PATH, NAME_SIZE)
    handle_font = ImageFont.truetype(BOLD_FONT_PATH, HANDLE_SIZE)
    name_bbox = draw.textbbox((0, 0), NAME_TEXT, font=name_font)
    handle_bbox = draw.textbbox((0, 0), HANDLE_TEXT, font=handle_font)
    name_h = name_bbox[3] - name_bbox[1]
    handle_h = handle_bbox[3] - handle_bbox[1]
    text_block_h = name_h + NAME_HANDLE_GAP + handle_h
    text_block_top = header_top + (HEADSHOT_SIZE - text_block_h) / 2
    text_x = LEFT_MARGIN + HEADSHOT_SIZE + HEADER_TEXT_GAP

    draw.text((text_x, text_block_top - name_bbox[1]), NAME_TEXT, font=name_font, fill=WHITE)
    handle_y = text_block_top + name_h + NAME_HANDLE_GAP
    draw.text((text_x, handle_y - handle_bbox[1]), HANDLE_TEXT, font=handle_font, fill=HANDLE_COLOR)

    # Quote
    y = quote_top
    for line in quote_lines:
        draw.text((LEFT_MARGIN, y), line, font=quote_font, fill=WHITE)
        y += quote_size * LINE_HEIGHT_RATIO

    # Wordmark: "Conscious " + "Dad" (orange) + " Tribe"
    wm_font = ImageFont.truetype(MEDIUM_FONT_PATH, WORDMARK_SIZE)
    part1, part2, part3 = "Conscious ", "Dad", " Tribe"
    w1 = draw.textlength(part1, font=wm_font)
    w2 = draw.textlength(part2, font=wm_font)
    w3 = draw.textlength(part3, font=wm_font)
    total_w = w1 + w2 + w3
    start_x = (CANVAS_W - total_w) / 2
    wm_bbox = draw.textbbox((0, 0), "Conscious Dad Tribe", font=wm_font)
    wm_h = wm_bbox[3] - wm_bbox[1]
    wm_y = WORDMARK_Y_CENTER - wm_h / 2 - wm_bbox[1]

    draw.text((start_x, wm_y), part1, font=wm_font, fill=WHITE)
    draw.text((start_x + w1, wm_y), part2, font=wm_font, fill=ORANGE)
    draw.text((start_x + w1 + w2, wm_y), part3, font=wm_font, fill=WHITE)

    img.save(output_path, "PNG")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 generate_card.py \"quote text\" output.png")
        sys.exit(1)
    quote = sys.argv[1]
    out = sys.argv[2]
    generate_card(quote, out)
    print(f"Saved: {out}")
