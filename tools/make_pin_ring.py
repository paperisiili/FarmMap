"""Generates the ring around the herb and fish icons on the world map, and the
disc that cuts those icons to fit inside it.

Like make_frame_textures.py, no drawing and no image model is involved: each
pixel comes from geometry alone - how much of it lies inside a circle. Run it
again and you get the same files, byte for byte.

pin-ring.tga  a WHITE band with a dark outline outside it. The game tints the
              band with SetVertexColor (green for herbs, blue for fish); the
              outline stays dark whatever the tint, so the ring reads on light
              and dark ground alike.
pin-disc.tga  a white disc, used as a mask: the icon shows only inside it. It
              runs half a pixel under the band, so no gap shows between the
              two.

Both fill the whole pin. The band's inner edge sits at 24/32 of its width, so
FarmMap draws a ringed pin 32/24 = 4/3 as big as a plain one: the icon keeps
its size, the ring goes around it. Change the sizes below and that factor
(ItemPins.FACTOR in FarmMap.lua) changes with them.

32 px wide: the pins show at 20 px or so, and a texture not much bigger than
its display needs no mipmaps to shrink cleanly.

Written with AI assistance, like the rest of FarmMap's code.

Usage:  python tools/make_pin_ring.py
Output: Textures/pin-ring.tga, Textures/pin-disc.tga
        (32-bit, uncompressed - the TGA flavour WoW reads)
Only the Python standard library is needed.
"""

import math
import os
import struct

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "Textures")

SIZE = 32
# Sub-pixel samples per axis: 8 x 8 = 64 per pixel, for thin curved edges.
SAMPLES = 8

# Radii from the centre, in pixels of the texture. Half a pixel of margin at
# the edge keeps the smoothing inside the texture.
R_OUTER = 15.5            # outside of the dark outline
OUTLINE = 1.5             # dark outline thickness
BAND = 2.0                # coloured band thickness
R_INNER = R_OUTER - OUTLINE - BAND   # 12.0: inside of the band
R_DISC = R_INNER + 0.5    # the icon tucks under the band
OUTLINE_ALPHA = 0.9       # the outline's opacity: dark, not a hard black line


def radii(px, py):
    """Distance from the centre of each sub-pixel sample of pixel (px, py)."""
    c = SIZE / 2
    for sy in range(SAMPLES):
        for sx in range(SAMPLES):
            x = px + (sx + 0.5) / SAMPLES
            y = py + (sy + 0.5) / SAMPLES
            yield math.hypot(x - c, y - c)


def ring_pixel(px, py):
    """(grey, alpha) of a ring pixel, 0-255: white where the band covers it,
    black where the outline does, blended where both share the pixel."""
    band = outline = 0
    for r in radii(px, py):
        if R_INNER < r <= R_OUTER - OUTLINE:
            band += 1
        elif R_OUTER - OUTLINE < r <= R_OUTER:
            outline += 1
    n = SAMPLES * SAMPLES
    alpha = (band + outline * OUTLINE_ALPHA) / n
    if alpha == 0:
        # Fully transparent, but the game blends neighbouring pixels' colours
        # when it scales: white inside the band, black outside the outline,
        # or a grey fringe shows at both edges.
        inside = math.hypot(px + 0.5 - SIZE / 2, py + 0.5 - SIZE / 2) < R_INNER
        return (255 if inside else 0), 0
    grey = band / (band + outline * OUTLINE_ALPHA)
    return round(grey * 255), round(alpha * 255)


def disc_pixel(px, py):
    hits = sum(1 for r in radii(px, py) if r <= R_DISC)
    return 255, round(hits / (SAMPLES * SAMPLES) * 255)


def write_tga(path, pixels):
    """Uncompressed 32-bit TGA, top-left origin, grey pixels: (grey, alpha)
    pairs, 0-255, row by row from the top."""
    header = struct.pack(
        "<BBBHHBHHHHBB",
        0,      # no image ID
        0,      # no colour map
        2,      # uncompressed true-colour
        0, 0, 0,                # colour map spec (unused)
        0, 0,                   # x / y origin
        SIZE, SIZE,             # width, height
        32,                     # bits per pixel
        0x28,                   # 8 alpha bits, top-left origin
    )
    with open(path, "wb") as f:
        f.write(header)
        for grey, a in pixels:
            f.write(bytes((grey, grey, grey, a)))   # B, G, R, A


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for name, pixel in (("pin-ring", ring_pixel), ("pin-disc", disc_pixel)):
        pixels = [pixel(px, py) for py in range(SIZE) for px in range(SIZE)]
        path = os.path.join(OUT_DIR, name + ".tga")
        write_tga(path, pixels)
        print("wrote", os.path.normpath(path))


if __name__ == "__main__":
    main()
