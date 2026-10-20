"""The ladder: every lesson defines new glyphs only from glyphs already taught.

Rung 1  counting      · ·· ··· beside their binary names
Rung 2  arithmetic    + − × ÷ < > and = by example triples
Rung 3  truth         ⊤ ⊥ ¬ ∧ ∨ ⊃ by statements the reader can check
Rung 4  the machine   ∅ S, rewrite rules, worked reductions, a new definition
Rung 5  anchors       hydrogen tick and wave (c = 1); the pulsar stamp
Rung 6  payload       the Greylock ledger, or the ship
Rung 7  words         agent / target / danger / good / bad by a short walk

A Message is a list of glyph names.  `transcript()` prints it for humans.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence

from . import machine, stamp, units
from .glyphs import NAMES, pretty


class Message:
    def __init__(self) -> None:
        self.tokens: List[str] = []
        self.sections: List[tuple] = []      # (name, start index)

    # ---- building ----------------------------------------------------------------
    def section(self, name: str) -> None:
        self.sections.append((name, len(self.tokens)))

    def add(self, *names: str) -> None:
        for n in names:
            if n not in NAMES:
                raise KeyError(n)
            self.tokens.append(n)

    def line(self, *parts) -> None:
        """A statement: glyph names, ints (binary numbers) and lists, ended with END."""
        for p in parts:
            if isinstance(p, int):
                self.tokens += number(p)
            elif isinstance(p, (list, tuple)):
                self.line_parts(p)
            else:
                self.add(p)
        self.add("END")

    def line_parts(self, parts) -> None:
        for p in parts:
            if isinstance(p, int):
                self.tokens += number(p)
            elif isinstance(p, (list, tuple)):
                self.line_parts(p)
            else:
                self.add(p)

    def dots(self, n: int) -> None:
        self.tokens += ["DOT"] * n

    # ---- reading ---------------------------------------------------------------------
    def lines(self) -> List[List[str]]:
        out, cur = [], []
        for t in self.tokens:
            if t == "END":
                out.append(cur)
                cur = []
            else:
                cur.append(t)
        if cur:
            out.append(cur)
        return out

    def transcript(self) -> str:
        """Human-readable: numbers collapsed to binary, glyphs to their pretty forms."""
        out = []
        sec = {start: name for name, start in self.sections}
        i = 0
        cur: List[str] = []
        for t in self.tokens:
            if i in sec:
                out.append(f"\n— {sec[i]} —")
            i += 1
            if t == "END":
                out.append(_fmt(cur))
                cur = []
            else:
                cur.append(t)
        if cur:
            out.append(_fmt(cur))
        return "\n".join(out)

    def __len__(self) -> int:
        return len(self.tokens)


def _fmt(line: Sequence[str]) -> str:
    parts: List[str] = []
    i = 0
    while i < len(line):
        t = line[i]
        if t in ("Z", "O"):
            j = i
            while j < len(line) and line[j] in ("Z", "O"):
                j += 1
            parts.append("".join("1" if x == "O" else "0" for x in line[i:j]))
            i = j
            continue
        if t == "DOT":
            j = i
            while j < len(line) and line[j] == "DOT":
                j += 1
            parts.append("·" * (j - i))
            i = j
            continue
        parts.append(pretty(t))
        i += 1
    return " ".join(parts)


def number(n: int) -> List[str]:
    """A non-negative integer as Z/O glyphs, most significant first."""
    if n < 0:
        raise ValueError("the message has no negative numbers; write a − b")
    return ["O" if ch == "1" else "Z" for ch in bin(n)[2:]]


def value(toks: Sequence[str]) -> int:
    return int("".join("1" if t == "O" else "0" for t in toks), 2)


# ----------------------------------------------------------------------------------
# the rungs
# ----------------------------------------------------------------------------------

def rung1_counting(m: Message) -> None:
    m.section("rung 1 · counting")
    for n in list(range(1, 17)) + [20, 25, 32, 50, 64, 100]:
        m.dots(n)
        m.line(n)


def rung2_arithmetic(m: Message) -> None:
    m.section("rung 2 · arithmetic")
    # the first lines keep the dots so + and = are anchored to counting
    m.dots(1); m.add("PLUS"); m.dots(1); m.add("EQ"); m.dots(2); m.add("END")
    m.dots(2); m.add("PLUS"); m.dots(1); m.add("EQ"); m.dots(3); m.add("END")
    m.dots(2); m.add("PLUS"); m.dots(3); m.add("EQ"); m.dots(5); m.add("END")
    for a, b in [(1, 1), (2, 1), (2, 3), (3, 4), (5, 7), (8, 8), (12, 13), (100, 1)]:
        m.line(a, "PLUS", b, "EQ", a + b)
    for a, b in [(2, 1), (5, 3), (10, 4), (100, 1), (7, 7)]:
        m.line(a, "MINUS", b, "EQ", a - b)
    for a, b in [(1, 1), (2, 3), (3, 3), (4, 5), (6, 7), (12, 12)]:
        m.line(a, "TIMES", b, "EQ", a * b)
    for a, b in [(6, 3), (6, 2), (12, 4), (100, 10), (49, 7)]:
        m.line(a, "DIV", b, "EQ", a // b)
    for a, b in [(1, 2), (3, 5), (10, 100)]:
        m.line(a, "LT", b)
        m.line(b, "GT", a)
    m.line(2, "PLUS", 3, "EQ", 3, "PLUS", 2)
    m.line(2, "TIMES", 3, "EQ", 3, "TIMES", 2)
    m.line(2, "TIMES", "LP", 3, "PLUS", 4, "RP", "EQ", 14)
    m.line("LP", 2, "TIMES", 3, "RP", "PLUS", 4, "EQ", 10)


def rung3_truth(m: Message) -> None:
    m.section("rung 3 · truth")
    truths = [(1, "PLUS", 1, "EQ", 2), (2, "TIMES", 3, "EQ", 6), (5, "GT", 2), (7, "MINUS", 3, "EQ", 4)]
    lies = [(1, "PLUS", 1, "EQ", 3), (2, "TIMES", 3, "EQ", 5), (5, "LT", 2), (7, "MINUS", 3, "EQ", 5)]
    for t, l in zip(truths, lies):
        m.line("LP", *t, "RP", "TRUE")
        m.line("LP", *l, "RP", "FALSE")
    m.line("NOT", "LP", 1, "PLUS", 1, "EQ", 3, "RP", "TRUE")
    m.line("NOT", "LP", 1, "PLUS", 1, "EQ", 2, "RP", "FALSE")
    m.line("NOT", "TRUE", "EQ", "FALSE")
    m.line("NOT", "FALSE", "EQ", "TRUE")
    for a, b, r in [("TRUE", "TRUE", "TRUE"), ("TRUE", "FALSE", "FALSE"), ("FALSE", "TRUE", "FALSE"), ("FALSE", "FALSE", "FALSE")]:
        m.line("LP", a, "AND", b, "RP", "EQ", r)
    for a, b, r in [("TRUE", "TRUE", "TRUE"), ("TRUE", "FALSE", "TRUE"), ("FALSE", "TRUE", "TRUE"), ("FALSE", "FALSE", "FALSE")]:
        m.line("LP", a, "OR", b, "RP", "EQ", r)
    for a, b, r in [("TRUE", "TRUE", "TRUE"), ("TRUE", "FALSE", "FALSE"), ("FALSE", "TRUE", "TRUE"), ("FALSE", "FALSE", "TRUE")]:
        m.line("LP", a, "IMP", b, "RP", "EQ", r)
    m.line("LP", "LP", 2, "GT", 1, "RP", "AND", "LP", 1, "PLUS", 1, "EQ", 2, "RP", "RP", "TRUE")
    m.line("LP", "LP", "VA", "GT", "VB", "RP", "IMP", "LP", "VA", "PLUS", 1, "GT", "VB", "RP", "RP", "TRUE")
    m.line("LP", "VA", "PLUS", "VB", "EQ", "VB", "PLUS", "VA", "RP", "TRUE")


def rung4_machine(m: Message) -> None:
    m.section("rung 4 · the machine")
    for n in range(0, 5):
        m.line(machine.tokens(machine.peano(n)), "EQ", n)
    for pat, rep in machine.RULES:
        m.line("DEF", machine.tokens(pat), "ARROW", machine.tokens(rep))
    # worked reductions, then the cross-check against rung 2
    for a, b, head in [(1, 2, "ADD"), (2, 2, "MUL"), (3, None, "DOUBLE")]:
        term = (head, machine.peano(a), machine.peano(b)) if b is not None else (head, machine.peano(a))
        trace = machine.reduce(term)
        parts: List = []
        for i, t in enumerate(trace):
            if i:
                parts.append("ARROW")
            parts.append(machine.tokens(t))
        m.line(parts)
        result = machine.unpeano(trace[-1])
        m.line(machine.tokens(term), "EQ", result)


def rung5_anchors(m: Message, pulsars: Optional[Sequence[stamp.Pulsar]] = None) -> None:
    m.section("rung 5 · anchors")
    # the hydrogen page (drawn) carries the physics; here are its equations
    m.line("H", "TICK", "EQ", 1, "TICK")                       # the period of the drawn transition is one tick
    m.line("H", "WAVE", "EQ", 1, "WAVE")                       # its wavelength is one wave
    m.line("LIGHT", "SPEED", "EQ", 1, "WAVE", "DIV", 1, "TICK")     # c = 1
    m.line(1, "WAVE", "EQ", "LIGHT", "SPEED", "TIMES", 1, "TICK")
    m.section("rung 5 · the stamp")
    for i, (p_milli, inv_pdot) in enumerate(stamp.encode(pulsars or stamp.CATALOGUE), start=1):
        m.line("PULSAR", i, "PERIOD", "STAMP", "EQ", p_milli, "DIV", 1000, "TICK")
        m.line("PULSAR", i, "DRIFT", "EQ", 1, "DIV", inv_pdot)


def payload_greylock(m: Message) -> None:
    u = units
    m.section("rung 6 · the Greylock ledger")
    m.line("CLOCK_B", "HEIGHT", "EQ", 0, "WAVE")
    m.line("CLOCK_A", "HEIGHT", "EQ", u.GREYLOCK_HEIGHT_WAVES, "WAVE")
    m.line("G", "TIMES", u.G_DENOMINATOR, "EQ", 1, "WAVE", "DIV", "LP", 1, "TICK", "TIMES", 1, "TICK", "RP")
    m.line("RATE", "EQ", "G", "TIMES", "CLOCK_A", "HEIGHT", "DIV", "LP", "LIGHT", "SPEED", "TIMES", "LIGHT", "SPEED", "RP")
    m.line("LP", "CLOCK_A", "MINUS", "CLOCK_B", "RP", "PER", u.DAY_TICKS, "TICK", "EQ", "RATE", "TIMES", u.DAY_TICKS, "TICK")
    m.line("LP", "CLOCK_A", "MINUS", "CLOCK_B", "RP", "TIMES", 100, "PER", u.DAY_TICKS, "TICK", "EQ", u.LEAD_PER_DAY_CENTITICKS, "TICK")
    m.line("LP", "CLOCK_A", "GT", "CLOCK_B", "RP", "TRUE")


def payload_ship(m: Message) -> None:
    u = units
    m.section("rung 6 · the ship")
    m.line("SHIP", "DISTANCE", "EQ", u.PROXIMA_WAVES, "WAVE")
    m.line("SHIP", "SPEED", "TIMES", 1_000_000, "LT", u.PEAK_BETA_PER_MILLION + 1, "TIMES", "LIGHT", "SPEED")
    m.line("SHIP", "TIME_SHIP", "EQ", u.SHIP_TICKS, "TICK")
    m.line("SHIP", "TIME_HOME", "EQ", u.EARTH_TICKS, "TICK")
    m.line("SHIP", "TIME_HOME", "MINUS", "SHIP", "TIME_SHIP", "EQ", u.LEAD_TICKS, "TICK")
    m.line("LP", "SHIP", "TIME_HOME", "GT", "SHIP", "TIME_SHIP", "RP", "TRUE")


def rung7_words(m: Message) -> None:
    """A walk on the number line: toward the target is good, onto the danger is bad."""
    m.section("rung 7 · words")
    m.line("TARGET", "EQ", 7)
    m.line("DANGER", "EQ", 2)
    for pos, nxt, word in [(4, 5, "GOOD"), (5, 6, "GOOD"), (6, 7, "GOOD"), (4, 3, "BAD"), (3, 2, "BAD")]:
        m.line("AGENT", "EQ", pos, "STEP", "AGENT", "EQ", nxt, word)
    m.line("LP", "AGENT", "EQ", "TARGET", "RP", "GOOD")
    m.line("LP", "AGENT", "EQ", "DANGER", "RP", "BAD")
    m.line("LP", "LP", "AGENT", "GT", "VA", "RP", "AND", "LP", "TARGET", "GT", "AGENT", "RP", "AND",
           "LP", "AGENT", "STEP", "AGENT", "PLUS", 1, "RP", "RP", "GOOD")


def build(payload: str = "greylock", pulsars: Optional[Sequence[stamp.Pulsar]] = None) -> Message:
    m = Message()
    rung1_counting(m)
    rung2_arithmetic(m)
    rung3_truth(m)
    rung4_machine(m)
    rung5_anchors(m, pulsars)
    if payload == "greylock":
        payload_greylock(m)
    elif payload == "ship":
        payload_ship(m)
    elif payload == "both":
        payload_greylock(m)
        payload_ship(m)
    else:
        raise ValueError(payload)
    rung7_words(m)
    return m
