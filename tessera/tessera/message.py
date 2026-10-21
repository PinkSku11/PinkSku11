"""The ladder: every lesson defines new glyphs only from glyphs already taught.

Rung 1  counting      · ·· ··· beside their binary names
Rung 2  arithmetic    + − × ÷ < > and = by example triples
Rung 3  truth         ⊤ ⊥ ¬ ∧ ∨ ⊃ by statements the reader can check
Rung 4  the machine   ∅ S, rewrite rules, worked reductions, binary inside terms
Rung 4b pictures      lists, points, row/col/rect/cat; every glyph's shape as a program;
                      the ship drawn as a program
Rung 5  anchors       hydrogen tick and wave (c = 1); the pulsar stamp
Rung 6  payload       the Greylock ledger, or the ship
Rung 7  dialogue      Ha and Hb speak, ask, answer; good and bad are judgments the reader
                      can check; knowing, wanting, help; then we and you, and what we want

A Message is a list of glyph names.  `transcript()` prints it for humans.
"""
from __future__ import annotations

from typing import List, Optional, Sequence

from . import glyphs, machine, stamp, units
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
        """A statement: glyph names, ints (binary numbers) and nested lists, ended with END."""
        self._parts(parts)
        self.add("END")

    def _parts(self, parts) -> None:
        prev_num = False
        for p in parts:
            if isinstance(p, int):
                if prev_num:
                    self.add("SEP")
                self.tokens += number(p)
            elif isinstance(p, (list, tuple)):
                self._parts(p)
            else:
                self.add(p)
            prev_num = isinstance(p, int)

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
        out = []
        sec = {start: name for name, start in self.sections}
        cur: List[str] = []
        for i, t in enumerate(self.tokens):
            if i in sec:
                out.append(f"\n— {sec[i]} —")
            if t == "END":
                out.append(fmt(cur))
                cur = []
            else:
                cur.append(t)
        if cur:
            out.append(fmt(cur))
        return "\n".join(out)

    def __len__(self) -> int:
        return len(self.tokens)


def fmt(line: Sequence[str]) -> str:
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
    if n < 0:
        raise ValueError("the message has no negative numbers; write a − b")
    return ["O" if ch == "1" else "Z" for ch in bin(n)[2:]]


def value(toks: Sequence[str]) -> int:
    return int("".join("1" if t == "O" else "0" for t in toks), 2)


def T(term) -> List[str]:
    """A machine term as glyph names."""
    return machine.tokens(term)


# ----------------------------------------------------------------------------------
# rungs 1–3
# ----------------------------------------------------------------------------------

def rung1_counting(m: Message) -> None:
    m.section("rung 1 · counting")
    for n in list(range(1, 17)) + [20, 25, 32, 50, 64, 100]:
        m.dots(n)
        m.line(n)


def rung2_arithmetic(m: Message) -> None:
    m.section("rung 2 · arithmetic")
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


# ----------------------------------------------------------------------------------
# rung 4: the machine, then pictures
# ----------------------------------------------------------------------------------

def _trace_line(m: Message, term, result_value: Optional[int] = None) -> None:
    trace = machine.reduce(term)
    parts: List = []
    for i, t in enumerate(trace):
        if i:
            parts.append("ARROW")
        parts.append(T(t))
    m.line(parts)
    if result_value is not None:
        m.line(T(term), "EQ", result_value)


def rung4_machine(m: Message) -> None:
    m.section("rung 4 · the machine")
    for n in range(0, 5):
        m.line(T(machine.peano(n)), "EQ", n)
    for pat, rep in machine.ARITH_RULES:
        m.line("DEF", T(pat), "ARROW", T(rep))
    _trace_line(m, ("ADD", machine.peano(1), machine.peano(2)), 3)
    _trace_line(m, ("MUL", machine.peano(2), machine.peano(2)), 4)
    _trace_line(m, ("DOUBLE", machine.peano(3)), 6)
    # binary numerals inside terms: the same machine, shorter to write
    m.line(T(("S", 0)), "EQ", 1)
    m.line(T(("S", 1)), "EQ", 2)
    m.line(T(("S", 2)), "EQ", 3)
    m.line(T(("S", 5)), "EQ", 6)
    _trace_line(m, ("ADD", 2, 3), 5)
    _trace_line(m, ("DOUBLE", 5), 10)


def rung4b_pictures(m: Message, ship_program: Sequence[tuple]) -> None:
    m.section("rung 4b · lists")
    m.line(T(machine.cons_list([1])))
    m.line(T(machine.cons_list([1, 2])))
    m.line(T(machine.cons_list([1, 2, 3])))
    for pat, rep in machine.DRAW_RULES[:2]:
        m.line("DEF", T(pat), "ARROW", T(rep))
    _trace_line(m, ("CAT", machine.cons_list([1]), machine.cons_list([2, 3])))
    m.line(T(("CAT", machine.cons_list([1]), machine.cons_list([2, 3]))), "EQ", T(machine.cons_list([1, 2, 3])))

    m.section("rung 4b · points and pictures")
    for pat, rep in machine.DRAW_RULES[2:]:
        m.line("DEF", T(pat), "ARROW", T(rep))
    _trace_line(m, ("ROW", 0, 0, 3))
    _trace_line(m, ("COL", 1, 0, 2))
    m.line(T(("RECT", 0, 0, 2, 2)), "EQ", T(machine.normal_form(("RECT", 0, 0, 2, 2))))
    # the alphabet describes itself
    m.section("rung 4b · the shapes of the glyphs")
    for name in NAMES:
        if name == "END":
            # the delimiter cannot be named inside a statement; its shape is "the shape of
            # what ends this one": ( shape ) ⇒ …  followed, as always, by the glyph itself
            m.line("DEF", "LP", "SHAPE", "RP", "ARROW", T(machine.program_term(glyphs.PROGRAMS[name])))
        else:
            m.line("DEF", "LP", "SHAPE", name, "RP", "ARROW", T(machine.program_term(glyphs.PROGRAMS[name])))
    m.section("rung 4b · the ship, drawn")
    m.line("DEF", "LP", "PICTURE", "SHIP", "RP", "ARROW", T(machine.program_term(ship_program)))


SHIP_PICTURE: List[tuple] = (
    [("COL", 0, 0, 31), ("COL", 14, 0, 31), ("ROW", 0, 0, 15), ("ROW", 30, 0, 15)]
    + [("ROW", y, 1, 13) for y in (4, 8, 12, 16, 20, 24)]      # the decks: thrust is down, so floors stack
    + [("RECT", 4, 26, 7, 4), ("ROW", 2, 6, 3)]                 # the engine block; the cabin at the prow
)


# ----------------------------------------------------------------------------------
# rung 5 and the payloads
# ----------------------------------------------------------------------------------

def rung5_anchors(m: Message, pulsars: Optional[Sequence[stamp.Pulsar]] = None) -> None:
    m.section("rung 5 · anchors")
    m.line("H", "TICK", "EQ", 1, "TICK")
    m.line("H", "WAVE", "EQ", 1, "WAVE")
    m.line("LIGHT", "SPEED", "EQ", 1, "WAVE", "DIV", 1, "TICK")
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


# ----------------------------------------------------------------------------------
# rung 7: dialogue (after Lincos, chapter III)
# ----------------------------------------------------------------------------------

def rung7_dialogue(m: Message) -> None:
    m.section("rung 7 · speaking")
    m.line("HA", "SAY", "HB", "LP", 1, "PLUS", 1, "EQ", 2, "RP")
    m.line("HB", "SAY", "HA", "LP", 2, "PLUS", 1, "EQ", 3, "RP")
    m.line("HA", "SAY", "HB", "LP", 2, "TIMES", 3, "EQ", 6, "RP")
    m.line("HB", "SAY", "HA", "LP", 6, "DIV", 2, "EQ", 3, "RP")

    m.section("rung 7 · asking, answering, judging")
    # (question, answer, judgment) — every GOOD answer is true, every BAD one false,
    # so a reader can recover GOOD and BAD by checking
    exchanges = [
        ((2, "PLUS", "VA", "EQ", 5), 3, True),
        ((2, "TIMES", "VA", "EQ", 6), 4, False),
        ((2, "TIMES", "VA", "EQ", 6), 3, True),
        (("VA", "TIMES", "VA", "EQ", 9), 3, True),
        ((10, "MINUS", "VA", "EQ", 4), 5, False),
        ((10, "MINUS", "VA", "EQ", 4), 6, True),
        (("VA", "PLUS", 5, "EQ", 8), 3, True),
        ((7, "LT", "VA"), 9, True),
        ((7, "LT", "VA"), 2, False),
    ]
    for i, (q, ans, good) in enumerate(exchanges):
        asker, other = ("HA", "HB") if i % 3 != 2 else ("HB", "HA")
        m.line(asker, "SAY", other, "ASK", "VA", "LP", *q, "RP")
        m.line(other, "SAY", asker, "LP", "VA", "EQ", ans, "RP")
        m.line(asker, "SAY", other, "GOOD" if good else "BAD")

    m.section("rung 7 · knowing")
    m.line("HB", "NOT", "KNOW", "LP", 3, "TIMES", "VA", "EQ", 12, "RP")
    m.line("HB", "SAY", "HA", "ASK", "VA", "LP", 3, "TIMES", "VA", "EQ", 12, "RP")
    m.line("HA", "SAY", "HB", "LP", "VA", "EQ", 4, "RP")
    m.line("HB", "SAY", "HA", "GOOD")
    m.line("HB", "KNOW", "LP", 3, "TIMES", 4, "EQ", 12, "RP")
    m.line("HA", "KNOW", "LP", 3, "TIMES", 4, "EQ", 12, "RP")
    m.line("LP", "LP", "HA", "KNOW", "VB", "RP", "AND", "LP", "HB", "SAY", "HA", "ASK", "VB", "RP", "RP", "IMP", "LP", "HA", "SAY", "HB", "VB", "RP")

    m.section("rung 7 · wanting")
    m.line("HB", "WANT", "LP", "HB", "KNOW", "LP", 5, "TIMES", "VA", "EQ", 35, "RP", "RP")
    m.line("HB", "SAY", "HA", "ASK", "VA", "LP", 5, "TIMES", "VA", "EQ", 35, "RP")
    m.line("HA", "SAY", "HB", "LP", "VA", "EQ", 7, "RP")
    m.line("HB", "SAY", "HA", "GOOD")
    m.line("HB", "KNOW", "LP", 5, "TIMES", 7, "EQ", 35, "RP")
    m.line("LP", "LP", "HB", "WANT", "LP", "HB", "KNOW", "VB", "RP", "RP", "AND", "LP", "HA", "KNOW", "VB", "RP", "RP",
           "IMP", "LP", "HB", "SAY", "HA", "ASK", "VB", "RP")

    m.section("rung 7 · the walk: wanting, danger, help")
    m.line("TARGET", "EQ", 7)
    m.line("DANGER", "EQ", 2)
    m.line("AGENT", "WANT", "LP", "AGENT", "EQ", "TARGET", "RP")
    m.line("AGENT", "NOT", "WANT", "LP", "AGENT", "EQ", "DANGER", "RP")
    for pos, nxt, word in [(4, 5, "GOOD"), (5, 6, "GOOD"), (6, 7, "GOOD"), (4, 3, "BAD"), (3, 2, "BAD")]:
        m.line("AGENT", "EQ", pos, "STEP", "AGENT", "EQ", nxt, word)
    m.line("LP", "AGENT", "EQ", "TARGET", "RP", "GOOD")
    m.line("LP", "AGENT", "EQ", "DANGER", "RP", "BAD")
    m.line("LP", "LP", "AGENT", "WANT", "LP", "AGENT", "EQ", "VA", "RP", "RP", "AND", "LP", "AGENT", "LT", "VA", "RP", "RP",
           "IMP", "LP", "AGENT", "STEP", "AGENT", "PLUS", 1, "RP")
    # help: Hb wants what it cannot do alone; Ha does it
    m.line("HB", "EQ", 3)
    m.line("HB", "WANT", "LP", "HB", "EQ", 7, "RP")
    m.line("HB", "SAY", "HA", "HELP", "LP", "HB", "EQ", 7, "RP")
    m.line("HA", "STEP", "HB", "EQ", 7)
    m.line("HB", "SAY", "HA", "GOOD")
    m.line("LP", "LP", "VA", "SAY", "VB", "HELP", "VC", "RP", "AND", "LP", "VB", "STEP", "VC", "RP", "RP", "IMP", "LP", "VA", "SAY", "VB", "GOOD", "RP")

    m.section("rung 7 · we and you")
    m.line("WE", "SAY", "YOU", "LP", 1, "PLUS", 1, "EQ", 2, "RP")
    m.line("WE", "SAY", "YOU", "LP", "CLOCK_A", "GT", "CLOCK_B", "RP")
    m.line("WE", "WANT", "LP", "YOU", "KNOW", "LP", "CLOCK_A", "GT", "CLOCK_B", "RP", "RP")
    m.line("WE", "NOT", "KNOW", "LP", "PULSAR", 1, "PERIOD", "EQ", "VA", "RP")
    m.line("WE", "WANT", "LP", "WE", "KNOW", "LP", "PULSAR", 1, "PERIOD", "EQ", "VA", "RP", "RP")
    m.line("WE", "SAY", "YOU", "ASK", "VA", "LP", "PULSAR", 1, "PERIOD", "EQ", "VA", "RP")
    m.line("WE", "WANT", "LP", "YOU", "SAY", "WE", "LP", "PULSAR", 1, "PERIOD", "EQ", "VA", "RP", "RP")
    m.line("WE", "WANT", "LP", "YOU", "GOOD", "RP")


def build(payload: str = "greylock", pulsars: Optional[Sequence[stamp.Pulsar]] = None) -> Message:
    m = Message()
    rung1_counting(m)
    rung2_arithmetic(m)
    rung3_truth(m)
    rung4_machine(m)
    rung4b_pictures(m, SHIP_PICTURE)
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
    rung7_dialogue(m)
    return m
