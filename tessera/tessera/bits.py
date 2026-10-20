"""Rung 0: mark and gap.  Glyph names ↔ a string of bits.

Each glyph is 8 bits, 1xxxxxxx.  Because every byte starts with a 1, sixteen zeros
never occur inside the message, so the frame mark is 24 zeros followed by a 1.
Repetition (every page three times, majority vote) is the durability layer a
stranger can see without being told; Hamming(7,4) is an optional inner code for
our own archives, where the reader already knows it.
"""
from __future__ import annotations

from typing import List, Sequence

from .glyphs import NAMES, code, name_of

FRAME = "0" * 24 + "1"


def encode(tokens: Sequence[str]) -> str:
    return "".join(format(code(t), "08b") for t in tokens)


def decode(bitstring: str) -> List[str]:
    if len(bitstring) % 8:
        raise ValueError("bit length is not a multiple of 8")
    out = []
    for i in range(0, len(bitstring), 8):
        b = int(bitstring[i:i + 8], 2)
        if not b & 0x80 or (b & 0x7F) >= len(NAMES):
            raise ValueError(f"not a glyph code at bit {i}: {bitstring[i:i + 8]}")
        out.append(name_of(b))
    return out


def frame(bitstring: str) -> str:
    return FRAME + bitstring + FRAME


def unframe(stream: str) -> str:
    first = stream.find(FRAME)
    last = stream.rfind(FRAME)
    if first < 0 or last <= first:
        raise ValueError("no frame marks found")
    return stream[first + len(FRAME):last]


# ---- repetition ------------------------------------------------------------------

def repeat(bitstring: str, k: int = 3) -> str:
    return bitstring * k


def vote(stream: str, k: int = 3) -> str:
    n = len(stream) // k
    copies = [stream[i * n:(i + 1) * n] for i in range(k)]
    return "".join("1" if sum(c[i] == "1" for c in copies) * 2 > k else "0" for i in range(n))


# ---- Hamming(7,4) ----------------------------------------------------------------------

def hamming_encode(bitstring: str) -> str:
    pad = (-len(bitstring)) % 4
    bitstring += "0" * pad
    out = []
    for i in range(0, len(bitstring), 4):
        d1, d2, d3, d4 = (int(c) for c in bitstring[i:i + 4])
        p1 = d1 ^ d2 ^ d4
        p2 = d1 ^ d3 ^ d4
        p3 = d2 ^ d3 ^ d4
        out.append(f"{p1}{p2}{d1}{p3}{d2}{d3}{d4}")
    return "".join(out)


def hamming_decode(stream: str) -> str:
    out = []
    for i in range(0, len(stream) - len(stream) % 7, 7):
        b = [int(c) for c in stream[i:i + 7]]
        p1, p2, d1, p3, d2, d3, d4 = b
        s1 = p1 ^ d1 ^ d2 ^ d4
        s2 = p2 ^ d1 ^ d3 ^ d4
        s3 = p3 ^ d2 ^ d3 ^ d4
        pos = s1 * 1 + s2 * 2 + s3 * 4
        if pos:
            b[pos - 1] ^= 1
        out.append(f"{b[2]}{b[4]}{b[5]}{b[6]}")
    return "".join(out)


def corrupt(stream: str, fraction: float, seed: int = 1) -> str:
    """Flip a fraction of the bits (a test helper for the durability layers)."""
    import random
    rng = random.Random(seed)
    bits = list(stream)
    for i in range(len(bits)):
        if rng.random() < fraction:
            bits[i] = "0" if bits[i] == "1" else "1"
    return "".join(bits)
