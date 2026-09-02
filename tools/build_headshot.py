#!/usr/bin/env python3
"""
Rebuild assets/headshot.png from an original source photo.

Produces the 176x176 circular headshot with the orange brand ring, composited
on the navy card background, matching the live card design exactly.

Measured from the existing live asset:
  - canvas 176x176
  - navy background #001347 fills the corners
  - orange ring #FF6719, ~6px thick, flush to the canvas edge

Rendered at 4x supersampling then downsampled with LANCZOS for clean edges.
"""
from PIL import Image, ImageDraw, ImageEnhance
import sys

SIZE = 176
SS = 4                      # supersample factor
RING = 6                    # ring thickness in final px
NAVY = (0x00, 0x13, 0x47)
ORANGE = (0xFF, 0x67, 0x19)

# Light enhancement, matching what was applied to the original asset
BRIGHTNESS = 1.08
CONTRAST = 1.10
SATURATION = 1.12


def build(src_path, out_path):
    S = SIZE * SS
    ring = RING * SS

    photo = Image.open(src_path).convert("RGB")

    # Square-crop centred, then scale to fill the inner circle
    w, h = photo.size
    side = min(w, h)
    photo = photo.crop(((w - side) // 2, (h - side) // 2,
                        (w - side) // 2 + side, (h - side) // 2 + side))
    photo = photo.resize((S, S), Image.LANCZOS)

    photo = ImageEnhance.Brightness(photo).enhance(BRIGHTNESS)
    photo = ImageEnhance.Contrast(photo).enhance(CONTRAST)
    photo = ImageEnhance.Color(photo).enhance(SATURATION)

    canvas = Image.new("RGB", (S, S), NAVY)

    # Circular mask for the photo, inset by the ring thickness
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse([ring, ring, S - ring - 1, S - ring - 1], fill=255)
    canvas.paste(photo, (0, 0), mask)

    # Orange ring drawn on top, flush to the edge
    d = ImageDraw.Draw(canvas)
    d.ellipse([ring // 2, ring // 2, S - ring // 2 - 1, S - ring // 2 - 1],
              outline=ORANGE, width=ring)

    canvas = canvas.resize((SIZE, SIZE), Image.LANCZOS)
    canvas.save(out_path, "PNG")
    return out_path


if __name__ == "__main__":
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "assets/headshot.png"
    build(src, out)
    print(f"Built: {out}")
