"""tessera — a message that teaches itself, for readers who share nothing with us.

    glyphs    the alphabet (placeholder 5×7 shapes; draw your own in glyphs.txt)
    message   the ladder of lessons, rung by rung, and the payloads
    machine   the rewriting machine of rung 4
    units     hydrogen units (c = 1) and the Greylock/ship numbers in them
    stamp     the pulsar time stamp and its inverse
    bits      glyphs ↔ bits, frame marks, repetition, Hamming
    pages     prime-size bitmap pages with parity; the hydrogen page; PNG/PBM
    listen    the stranger's decoder — no key
    harness   the blind-test packet and scorer

Pure standard library.  `python -m tessera --help`.
"""
from . import bits, glyphs, harness, listen, machine, message, pages, stamp, units  # noqa: F401

__version__ = "0.1.0"
