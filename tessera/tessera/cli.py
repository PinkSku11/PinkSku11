"""Command line: python -m tessera <command>

  speak     build the message; write bits, pages (PNG + PBM), the transcript and the key
  listen    decode a bits file with no key and report what a stranger would recover
  stamp     show the pulsar stamp, or date a message from today's periods (demo)
  glyphs    export the glyph set to glyphs.txt (edit it, then every command reads it back)
  packet    write the blind-test packet for a human or a language model
"""
from __future__ import annotations

import argparse
import os
import sys

from . import bits as B
from . import glyphs, harness, listen, message, pages, stamp
from .units import YEAR


def _overrides() -> None:
    n = glyphs.load_overrides(os.path.join(os.getcwd(), "glyphs.txt"))
    if n:
        print(f"(using {n} glyph shapes from glyphs.txt)")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="tessera", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("speak")
    s.add_argument("--payload", choices=["greylock", "ship", "both"], default="greylock")
    s.add_argument("--out", default="out", help="output directory")
    s.add_argument("--repeat", type=int, default=3, help="copies of the bitstream in the durable file")

    l = sub.add_parser("listen")
    l.add_argument("bits", help="a file of 0/1 characters (framed or not)")

    st = sub.add_parser("stamp")
    st.add_argument("--years", type=float, help="simulate a reader this many years later and date the message")

    g = sub.add_parser("glyphs")
    g.add_argument("--export", default="glyphs.txt")
    g.add_argument("--sheet", default=None, help="also write a PNG key sheet here")

    p = sub.add_parser("packet")
    p.add_argument("--payload", choices=["greylock", "ship", "both"], default="greylock")
    p.add_argument("--prefix", default="blind")

    a = ap.parse_args(argv)
    _overrides()

    if a.cmd == "speak":
        m = message.build(a.payload)
        os.makedirs(a.out, exist_ok=True)
        raw = B.encode(m.tokens)
        with open(os.path.join(a.out, "message.bits"), "w") as f:
            f.write(B.frame(raw) + "\n")
        with open(os.path.join(a.out, "message-durable.bits"), "w") as f:
            f.write(B.repeat(B.frame(raw), a.repeat) + "\n")
        with open(os.path.join(a.out, "transcript.txt"), "w") as f:
            f.write(m.transcript() + "\n")
        pgs = pages.paginate(m.tokens)
        specials = [("page-00-hydrogen", pages.hydrogen_page()), ("page-00-pictures", pages.pictures_page(message.SHIP_PICTURE))]
        for name, pg in specials + [(f"page-{i:02d}", pg) for i, pg in enumerate(pgs, start=1)]:
            pages.write_png(pg, os.path.join(a.out, name + ".png"))
            pages.write_pbm(pg, os.path.join(a.out, name + ".pbm"))
        pages.write_png(pages.glyph_sheet(), os.path.join(a.out, "key-glyph-sheet.png"))
        with open(os.path.join(a.out, "key.txt"), "w") as f:
            for n in glyphs.NAMES:
                f.write(f"0x{glyphs.code(n):02x}  {n:10s} {glyphs.pretty(n)}\n")
        print(f"{len(m.tokens)} glyphs, {len(raw)} bits, {len(pgs)} glyph pages + the hydrogen and pictures pages → {a.out}/")
        print(m.transcript())
    elif a.cmd == "listen":
        with open(a.bits) as f:
            stream = "".join(ch for ch in f.read() if ch in "01")
        try:
            stream = B.unframe(stream)
        except ValueError:
            pass
        print(listen.report_text(stream))
    elif a.cmd == "stamp":
        enc = stamp.encode()
        for p, (pm, inv) in zip(stamp.CATALOGUE, enc):
            print(f"{p.name:32s} period {pm / 1000:,.3f} ticks   drift 1/{inv:.3e}   dates to ±{stamp.resolution_years(p):.3g} yr per 10⁻¹² s of period precision")
        if a.years is not None:
            today = stamp.aged(stamp.CATALOGUE, a.years, jitter=0.0)
            r = stamp.decode(enc, today)
            print(f"\nreader {a.years:,.0f} years later recovers Δt = {r['years']:,.2f} yr (spread {r['spread_years']:.2g} yr) from {len(r['matches'])} pulsars")
    elif a.cmd == "glyphs":
        glyphs.export(a.export)
        print(f"wrote {a.export}")
        if a.sheet:
            pages.write_png(pages.glyph_sheet(), a.sheet)
            print(f"wrote {a.sheet}")
    elif a.cmd == "packet":
        m = message.build(a.payload)
        harness.packet(m.tokens, a.prefix)
        print(f"wrote {a.prefix}-symbols.txt (give this to the reader), {a.prefix}-bits.txt, {a.prefix}-key.txt (keep)")


if __name__ == "__main__":
    main()
