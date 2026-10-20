"""Bitmap pages for a reader with eyes (or any 2-D sense).

A page is 211 × 223 pixels — both prime, so a reader who receives the bits as a
single string can only unfold them one way (and its mirror).  Glyphs sit in a
35 × 27 grid of 6 × 8 cells.  The last pixel column holds each row's parity and
the last pixel row each column's, a rule a reader can discover at Rung 2 and use
to spot damage.

Also here: the hydrogen page (the one drawing the physics rests on), the glyph
sheet, and PBM/PNG writers that need nothing beyond the standard library.
"""
from __future__ import annotations

import math
import struct
import zlib
from typing import List, Sequence, Tuple

from .glyphs import NAMES, bitmap

W, H = 211, 223                     # both prime
CELL_W, CELL_H = 6, 8
COLS, ROWS = 35, 27                 # 35 * 6 = 210 columns of cells, 27 * 8 = 216 rows
PER_PAGE = COLS * ROWS

Bitmap = List[List[int]]


def blank() -> Bitmap:
    return [[0] * W for _ in range(H)]


def stamp_glyph(page: Bitmap, name: str, col: int, row: int) -> None:
    g = bitmap(name)
    x0, y0 = col * CELL_W, row * CELL_H
    for dy, grow in enumerate(g):
        for dx, v in enumerate(grow):
            if v:
                page[y0 + dy][x0 + dx] = 1


def add_parity(page: Bitmap) -> None:
    for y in range(H - 1):
        page[y][W - 1] = sum(page[y][:W - 1]) % 2
    for x in range(W):
        page[H - 1][x] = sum(page[y][x] for y in range(H - 1)) % 2


def check_parity(page: Bitmap) -> Tuple[List[int], List[int]]:
    """Rows and columns whose parity fails (empty lists for a clean page)."""
    bad_rows = [y for y in range(H - 1) if sum(page[y]) % 2]
    bad_cols = [x for x in range(W) if sum(page[y][x] for y in range(H)) % 2]
    return bad_rows, bad_cols


def paginate(tokens: Sequence[str]) -> List[Bitmap]:
    pages = []
    for start in range(0, len(tokens), PER_PAGE):
        page = blank()
        for i, name in enumerate(tokens[start:start + PER_PAGE]):
            stamp_glyph(page, name, i % COLS, i // COLS)
        add_parity(page)
        pages.append(page)
    return pages


# ---- drawing helpers for the hydrogen page ---------------------------------------------

def disc(page: Bitmap, cx: int, cy: int, r: float, fill: bool = True) -> None:
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if 0 <= x < W - 1 and 0 <= y < H - 1:
                d = math.hypot(x - cx, y - cy)
                if (fill and d <= r) or (not fill and abs(d - r) < 0.7):
                    page[y][x] = 1


def line(page: Bitmap, x0: int, y0: int, x1: int, y1: int) -> None:
    n = max(abs(x1 - x0), abs(y1 - y0), 1)
    for i in range(n + 1):
        x = round(x0 + (x1 - x0) * i / n)
        y = round(y0 + (y1 - y0) * i / n)
        if 0 <= x < W - 1 and 0 <= y < H - 1:
            page[y][x] = 1


def arrow(page: Bitmap, x0: int, y0: int, x1: int, y1: int) -> None:
    line(page, x0, y0, x1, y1)
    ang = math.atan2(y1 - y0, x1 - x0)
    for s in (+1, -1):
        a = ang + s * 2.6
        line(page, x1, y1, round(x1 + 5 * math.cos(a)), round(y1 + 5 * math.sin(a)))


def glyph_at(page: Bitmap, name: str, x: int, y: int) -> None:
    for dy, grow in enumerate(bitmap(name)):
        for dx, v in enumerate(grow):
            if v and 0 <= x + dx < W - 1 and 0 <= y + dy < H - 1:
                page[y + dy][x + dx] = 1


def hydrogen_page() -> Bitmap:
    """Proton, electron, the spin flip, its wave and its period: the anchor, drawn."""
    p = blank()
    # the atom, twice: spins parallel, then antiparallel, with the transition arrow between
    for k, (cx, flip) in enumerate(((50, False), (150, True))):
        cy = 50
        disc(p, cx, cy, 6.0, fill=True)                    # proton
        disc(p, cx, cy, 24.0, fill=False)                  # orbit
        ex, ey = cx + 24, cy
        disc(p, ex, ey, 2.5, fill=True)                    # electron
        arrow(p, cx, cy - 12, cx, cy - 22)                 # proton spin: up
        if flip:
            arrow(p, ex + 8, ey - 10, ex + 8, ey)          # electron spin: down
        else:
            arrow(p, ex + 8, ey, ex + 8, ey - 10)          # electron spin: up
    arrow(p, 82, 50, 118, 50)
    glyph_at(p, "H", 97, 30)
    # the wave: one wavelength, bracketed, labelled WAVE = 1
    y0 = 120
    for x in range(20, 190):
        y = round(y0 - 14 * math.sin(2 * math.pi * (x - 20) / 170))
        p[y][x] = 1
    line(p, 20, y0 + 26, 190, y0 + 26)
    line(p, 20, y0 + 22, 20, y0 + 30)
    line(p, 190, y0 + 22, 190, y0 + 30)
    glyph_at(p, "WAVE", 96, y0 + 32)
    glyph_at(p, "EQ", 103, y0 + 32)
    glyph_at(p, "O", 110, y0 + 32)
    # the period: ticks of the same transition in time, labelled TICK = 1
    y1 = 180
    for i in range(9):
        x = 20 + i * 21
        line(p, x, y1 - 8, x, y1 + 8)
    line(p, 20, y1 + 14, 41, y1 + 14)
    line(p, 20, y1 + 11, 20, y1 + 17)
    line(p, 41, y1 + 11, 41, y1 + 17)
    glyph_at(p, "TICK", 60, y1 + 10)
    glyph_at(p, "EQ", 67, y1 + 10)
    glyph_at(p, "O", 74, y1 + 10)
    add_parity(p)
    return p


def glyph_sheet() -> Bitmap:
    """Every glyph with its id in binary beside it — the key, for us."""
    p = blank()
    from .message import number
    for i, name in enumerate(NAMES):
        col = (i // ROWS) * 12
        row = i % ROWS
        stamp_glyph(p, name, col, row)
        for j, d in enumerate(number(i)):
            if col + 2 + j < COLS:
                stamp_glyph(p, d, col + 2 + j, row)
    add_parity(p)
    return p


# ---- writers ------------------------------------------------------------------------------

def to_bits(page: Bitmap) -> str:
    return "".join(str(v) for row in page for v in row)


def from_bits(bits: str, w: int = W, h: int = H) -> Bitmap:
    return [[int(bits[y * w + x]) for x in range(w)] for y in range(h)]


def write_pbm(page: Bitmap, path: str) -> None:
    with open(path, "w") as f:
        f.write(f"P1\n{W} {H}\n")
        for row in page:
            f.write(" ".join(str(v) for v in row) + "\n")


def write_png(page: Bitmap, path: str, scale: int = 3, invert: bool = False) -> None:
    """A minimal grayscale PNG writer (no PIL needed)."""
    h, w = len(page), len(page[0])
    raw = bytearray()
    for row in page:
        line_bytes = bytearray()
        for v in row:
            on = v ^ (1 if invert else 0)
            line_bytes += bytes([0 if on else 255]) * scale
        for _ in range(scale):
            raw += b"\x00" + line_bytes

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w * scale, h * scale, 8, 0, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)
