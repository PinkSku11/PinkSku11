"""The blind test: hand the message to someone without the key.

`packet()` writes what a stranger gets — the bits, and the same message with
every glyph replaced by an arbitrary symbol — plus the rubric for scoring what
they recover, rung by rung.  Give the packet to a person, or to a language model
in a fresh conversation with no other context; score their answer with `score()`.
`listen.decode_blind` is the automated stranger and runs in the tests.
"""
from __future__ import annotations

import random
from typing import Dict, Sequence

from . import bits as B
from .glyphs import NAMES, PRETTY, code

SYMBOLS = [chr(c) for c in range(0x13A0, 0x13F4)]     # a syllabary a reader is unlikely to know


def transliterate(tokens: Sequence[str], seed: int = 20261020) -> Dict[str, str]:
    rng = random.Random(seed)
    syms = SYMBOLS[:]
    rng.shuffle(syms)
    return {name: syms[i] for i, name in enumerate(NAMES)}


RUBRIC = """\
You are receiving a message from a sender who shares no language with you.
It is one long string of symbols (and, separately, the same message as bits).
Nothing in it is decoration: every symbol is defined by how it is used.
Work out, in order:
  1. which symbol separates statements, and which symbol is repeated to count;
  2. the two symbols that spell numbers, and which is which;
  3. the symbols for =, +, −, ×, ÷, <, >;
  4. the symbols for TRUE and FALSE, and for NOT, AND, OR, IMPLIES;
  5. the bracket pair and the symbol that means "rewrites to";
  6. what the long numbers near the end measure.
Report a table: symbol → meaning → the evidence (which statements convinced you).
Do not guess beyond the evidence; say what you could not decode.
"""


def packet(tokens: Sequence[str], path_prefix: str, seed: int = 20261020) -> Dict[str, str]:
    tr = transliterate(tokens, seed)
    text = "".join(tr[t] for t in tokens)
    with open(path_prefix + "-symbols.txt", "w") as f:
        f.write(RUBRIC + "\n" + text + "\n")
    with open(path_prefix + "-bits.txt", "w") as f:
        f.write(B.frame(B.encode(tokens)) + "\n")
    with open(path_prefix + "-key.txt", "w") as f:
        f.write("KEY — do not give this to the reader\n")
        for name in NAMES:
            f.write(f"{tr[name]}  0x{code(name):02x}  {name}  {PRETTY.get(name, '')}\n")
    return tr


def score(answer: Dict[str, str], tr: Dict[str, str]) -> Dict[str, object]:
    """answer maps the stranger's symbol → claimed meaning (pretty form); returns hits and misses."""
    truth = {sym: PRETTY.get(name, name.lower()) for name, sym in tr.items()}
    hits = {s: m for s, m in answer.items() if truth.get(s) == m}
    misses = {s: (m, truth.get(s)) for s, m in answer.items() if truth.get(s) != m}
    return {"hits": len(hits), "misses": misses, "of": len(answer)}
