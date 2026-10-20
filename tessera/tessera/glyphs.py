"""The alphabet: every glyph is a small program, and its 5 × 7 bitmap is what the program draws.

A glyph program is a list of primitives — PT(x, y), ROW(y, x, n), COL(x, y, n),
RECT(x, y, w, h) — in a grid 5 wide and 7 tall, x to the right, y downward.  The
same primitives are rules in the rung-4 machine, so the message can state every
glyph's shape as a definition (`≝ (shape g) ⇒ …`) and a reader who runs the rules
gets the typeface back.  The alphabet describes itself.

Families carry role in their frame: machine words have a bar above and below,
physics words a column either side, dialogue words four corner points.  Numbers,
operators and logic are bare.  Codes are 1xxxxxxx; ids are the order of NAMES
(append, never reorder).  `tessera glyphs --export` writes the programs to
glyphs.txt; edit and the package reads them back with `load_overrides`.
"""
from __future__ import annotations

import os
import random
from typing import Dict, List, Sequence, Tuple

NAMES: List[str] = [
    "DOT", "Z", "O", "END",
    "EQ", "PLUS", "MINUS", "TIMES", "DIV", "LT", "GT",
    "TRUE", "FALSE", "NOT", "AND", "OR", "IMP",
    "LP", "RP", "ARROW", "DEF",
    "VA", "VB", "VC", "VD",
    "N", "S", "ADD", "MUL", "DOUBLE",
    "TICK", "WAVE", "H", "LIGHT",
    "CLOCK_A", "CLOCK_B", "HEIGHT", "G", "RATE", "PER",
    "PULSAR", "PERIOD", "DRIFT", "STAMP",
    "SHIP", "DISTANCE", "TIME_SHIP", "TIME_HOME", "SPEED",
    "AGENT", "TARGET", "DANGER", "STEP", "GOOD", "BAD",
    # v0.2 — pictures
    "CONS", "PT", "ROW", "COL", "RECT", "CAT", "SHAPE", "PICTURE",
    # v0.2 — dialogue
    "HA", "HB", "SAY", "ASK", "KNOW", "WANT", "HELP", "WE", "YOU",
    # v0.2 — the separator between adjacent numerals inside a term
    "SEP",
]
ID: Dict[str, int] = {n: i for i, n in enumerate(NAMES)}

PRETTY: Dict[str, str] = {
    "DOT": "·", "Z": "0", "O": "1", "END": "⏎", "EQ": "=", "PLUS": "+", "MINUS": "−", "TIMES": "×",
    "DIV": "÷", "LT": "<", "GT": ">", "TRUE": "⊤", "FALSE": "⊥", "NOT": "¬", "AND": "∧", "OR": "∨",
    "IMP": "⊃", "LP": "(", "RP": ")", "ARROW": "⇒", "DEF": "≝", "VA": "a", "VB": "b", "VC": "c", "VD": "d",
    "N": "∅", "S": "S", "ADD": "add", "MUL": "mul", "DOUBLE": "double", "TICK": "tick", "WAVE": "wave",
    "H": "H", "LIGHT": "light", "CLOCK_A": "clockA", "CLOCK_B": "clockB", "HEIGHT": "height", "G": "g",
    "RATE": "rate", "PER": "per", "PULSAR": "pulsar", "PERIOD": "period", "DRIFT": "drift", "STAMP": "now",
    "SHIP": "ship", "DISTANCE": "distance", "TIME_SHIP": "shiptime", "TIME_HOME": "hometime", "SPEED": "speed",
    "AGENT": "agent", "TARGET": "target", "DANGER": "danger", "STEP": "step", "GOOD": "good", "BAD": "bad",
    "CONS": "cons", "PT": "pt", "ROW": "row", "COL": "col", "RECT": "rect", "CAT": "cat", "SHAPE": "shape",
    "PICTURE": "picture", "HA": "Ha", "HB": "Hb", "SAY": "say", "ASK": "?", "KNOW": "know", "WANT": "want",
    "HELP": "help", "WE": "we", "YOU": "you", "SEP": ",",
}

W, H = 5, 7
Prim = Tuple           # ("PT", x, y) | ("ROW", y, x, n) | ("COL", x, y, n) | ("RECT", x, y, w, h)

# ---- the hand-drawn programs ---------------------------------------------------------------------
HAND: Dict[str, List[Prim]] = {
    "DOT":   [("PT", 2, 3)],
    "Z":     [("ROW", 0, 0, 5), ("ROW", 6, 0, 5), ("COL", 0, 1, 5), ("COL", 4, 1, 5)],
    "O":     [("COL", 2, 0, 7)],
    "END":   [("COL", 0, 0, 7), ("ROW", 6, 1, 4)],
    "EQ":    [("ROW", 2, 0, 5), ("ROW", 4, 0, 5)],
    "PLUS":  [("ROW", 3, 0, 5), ("COL", 2, 1, 2), ("COL", 2, 4, 2)],
    "MINUS": [("ROW", 2, 0, 5), ("ROW", 3, 0, 5)],
    "TIMES": [("PT", 0, 1), ("PT", 4, 1), ("PT", 1, 2), ("PT", 3, 2), ("PT", 2, 3), ("PT", 1, 4), ("PT", 3, 4), ("PT", 0, 5), ("PT", 4, 5)],
    "DIV":   [("ROW", 3, 0, 5), ("PT", 1, 1), ("PT", 3, 1), ("PT", 1, 5), ("PT", 3, 5)],
    "LT":    [("PT", 3, 1), ("PT", 2, 2), ("PT", 1, 3), ("PT", 2, 4), ("PT", 3, 5)],
    "GT":    [("PT", 1, 1), ("PT", 2, 2), ("PT", 3, 3), ("PT", 2, 4), ("PT", 1, 5)],
    "TRUE":  [("PT", 2, 3), ("ROW", 4, 1, 3), ("ROW", 5, 0, 5)],
    "FALSE": [("ROW", 1, 0, 5), ("ROW", 2, 1, 3), ("PT", 2, 3)],
    "NOT":   [("ROW", 2, 0, 5), ("COL", 4, 3, 3)],
    "AND":   [("PT", 2, 2), ("PT", 1, 3), ("PT", 3, 3), ("PT", 0, 4), ("PT", 4, 4), ("PT", 0, 5), ("PT", 4, 5)],
    "OR":    [("PT", 0, 1), ("PT", 4, 1), ("PT", 0, 2), ("PT", 4, 2), ("PT", 1, 3), ("PT", 3, 3), ("PT", 2, 4)],
    "IMP":   [("ROW", 1, 0, 4), ("COL", 4, 2, 3), ("ROW", 5, 0, 4)],
    "LP":    [("PT", 3, 0), ("PT", 2, 1), ("COL", 1, 2, 3), ("PT", 2, 5), ("PT", 3, 6)],
    "RP":    [("PT", 1, 0), ("PT", 2, 1), ("COL", 3, 2, 3), ("PT", 2, 5), ("PT", 1, 6)],
    "ARROW": [("ROW", 4, 0, 5), ("PT", 3, 3), ("PT", 3, 5)],
    "DEF":   [("ROW", 1, 0, 5), ("ROW", 3, 0, 5), ("ROW", 5, 0, 5)],
    "VA":    [("RECT", 0, 5, 3, 2)],
    "VB":    [("RECT", 2, 5, 3, 2)],
    "VC":    [("RECT", 0, 0, 3, 2)],
    "VD":    [("RECT", 2, 0, 3, 2)],
    "N":     [("ROW", 2, 1, 3), ("ROW", 4, 1, 3), ("PT", 1, 3), ("PT", 3, 3)],
    "S":     [("PT", 2, 0), ("PT", 1, 1), ("PT", 3, 1), ("PT", 0, 2), ("PT", 4, 2)],
    "SEP":   [("PT", 0, 1), ("PT", 4, 1), ("PT", 0, 3), ("PT", 4, 3), ("PT", 0, 5), ("PT", 4, 5)],
    # machine words: a bar above
    "ADD":   [("ROW", 0, 0, 5), ("COL", 2, 2, 5), ("ROW", 4, 0, 5)],
    "MUL":   [("ROW", 0, 0, 5), ("PT", 1, 2), ("PT", 3, 2), ("PT", 2, 3), ("PT", 1, 4), ("PT", 3, 4)],
    "PT":    [("ROW", 0, 0, 5), ("PT", 2, 4)],
    "ROW":   [("ROW", 0, 0, 5), ("ROW", 3, 0, 5), ("ROW", 4, 0, 5)],
    "COL":   [("ROW", 0, 0, 5), ("COL", 1, 2, 5), ("COL", 3, 2, 5)],
    "RECT":  [("ROW", 0, 0, 5), ("RECT", 1, 2, 3, 2), ("RECT", 1, 5, 3, 2)],
    # physics words: a column either side
    "TICK":  [("COL", 0, 0, 7), ("COL", 4, 0, 7), ("COL", 2, 0, 7)],
    "WAVE":  [("COL", 0, 0, 7), ("COL", 4, 0, 7), ("PT", 1, 1), ("PT", 2, 2), ("PT", 3, 3), ("PT", 2, 4), ("PT", 1, 5)],
    "H":     [("COL", 0, 0, 7), ("COL", 4, 0, 7), ("ROW", 3, 1, 3)],
    "LIGHT": [("COL", 0, 0, 7), ("COL", 4, 0, 7), ("PT", 2, 0), ("PT", 2, 6), ("PT", 1, 2), ("PT", 3, 2), ("PT", 1, 4), ("PT", 3, 4)],
    "CLOCK_A": [("COL", 0, 0, 7), ("COL", 4, 0, 7), ("RECT", 1, 1, 3, 2)],
    "CLOCK_B": [("COL", 0, 0, 7), ("COL", 4, 0, 7), ("RECT", 1, 4, 3, 2)],
    "SHIP":  [("COL", 0, 0, 7), ("COL", 4, 0, 7), ("PT", 2, 0), ("ROW", 2, 1, 3), ("ROW", 5, 1, 3)],
    # dialogue words: four corner points
    "HA":    [("PT", 0, 0), ("PT", 4, 0), ("PT", 0, 6), ("PT", 4, 6), ("RECT", 1, 1, 3, 2)],
    "HB":    [("PT", 0, 0), ("PT", 4, 0), ("PT", 0, 6), ("PT", 4, 6), ("RECT", 1, 4, 3, 2)],
    "WE":    [("PT", 0, 0), ("PT", 4, 0), ("PT", 0, 6), ("PT", 4, 6), ("ROW", 3, 1, 3), ("COL", 2, 1, 5)],
    "YOU":   [("PT", 0, 0), ("PT", 4, 0), ("PT", 0, 6), ("PT", 4, 6), ("PT", 1, 2), ("PT", 3, 2), ("PT", 2, 3), ("COL", 2, 4, 2)],
    "GOOD":  [("PT", 0, 0), ("PT", 4, 0), ("PT", 0, 6), ("PT", 4, 6), ("PT", 2, 1), ("ROW", 2, 1, 3), ("ROW", 3, 0, 5)],
    "BAD":   [("PT", 0, 0), ("PT", 4, 0), ("PT", 0, 6), ("PT", 4, 6), ("ROW", 3, 0, 5), ("ROW", 4, 1, 3), ("PT", 2, 5)],
}

FAMILY: Dict[str, List[Prim]] = {
    "machine": [("ROW", 0, 0, 5)],
    "physics": [("COL", 0, 0, 7), ("COL", 4, 0, 7)],
    "dialogue": [("PT", 0, 0), ("PT", 4, 0), ("PT", 0, 6), ("PT", 4, 6)],
}
ROLE: Dict[str, str] = {}
for _n in ("ADD", "MUL", "DOUBLE", "CONS", "PT", "ROW", "COL", "RECT", "CAT", "SHAPE", "PICTURE"):
    ROLE[_n] = "machine"
for _n in ("TICK", "WAVE", "H", "LIGHT", "CLOCK_A", "CLOCK_B", "HEIGHT", "G", "RATE", "PER", "PULSAR", "PERIOD",
           "DRIFT", "STAMP", "SHIP", "DISTANCE", "TIME_SHIP", "TIME_HOME", "SPEED"):
    ROLE[_n] = "physics"
for _n in ("AGENT", "TARGET", "DANGER", "STEP", "GOOD", "BAD", "HA", "HB", "SAY", "ASK", "KNOW", "WANT", "HELP", "WE", "YOU"):
    ROLE[_n] = "dialogue"


# ---- rendering ----------------------------------------------------------------------------------------

def points(program: Sequence[Prim]) -> set:
    out = set()
    for p in program:
        if p[0] == "PT":
            out.add((p[1], p[2]))
        elif p[0] == "ROW":
            _, y, x, n = p
            out.update((x + i, y) for i in range(n))
        elif p[0] == "COL":
            _, x, y, n = p
            out.update((x, y + i) for i in range(n))
        elif p[0] == "RECT":
            _, x, y, w, h = p
            out.update((x + i, y + j) for i in range(w) for j in range(h))
        else:
            raise ValueError(p)
    return out


def render(program: Sequence[Prim], w: int = W, h: int = H) -> List[List[int]]:
    pts = points(program)
    return [[1 if (x, y) in pts else 0 for x in range(w)] for y in range(h)]


def _distance(a: List[List[int]], b: List[List[int]]) -> int:
    return sum(x != y for ra, rb in zip(a, b) for x, y in zip(ra, rb))


INTERIOR = {                      # (x0, x1, y0, y1) inclusive, where a family's inner mark may go
    "machine": (0, 4, 2, 6),
    "physics": (1, 3, 0, 6),
    "dialogue": (0, 4, 1, 5),
}


def _inner_candidates(rng: random.Random, role: str) -> List[Prim]:
    """Two or three small primitives inside the family's interior."""
    x0, x1, y0, y1 = INTERIOR[role]
    out: List[Prim] = []
    for _ in range(rng.randint(2, 3)):
        kind = rng.choice(["PT", "ROW", "COL", "RECT"])
        if kind == "PT":
            out.append(("PT", rng.randint(x0, x1), rng.randint(y0, y1)))
        elif kind == "ROW":
            n = rng.randint(2, min(3, x1 - x0 + 1))
            out.append(("ROW", rng.randint(y0, y1), rng.randint(x0, x1 - n + 1), n))
        elif kind == "COL":
            n = rng.randint(2, 4)
            out.append(("COL", rng.randint(x0, x1), rng.randint(y0, y1 - n + 1), n))
        else:
            out.append(("RECT", rng.randint(x0, x1 - 1), rng.randint(y0, y1 - 1), 2, 2))
    return out


def build() -> Dict[str, List[Prim]]:
    progs: Dict[str, List[Prim]] = {n: list(p) for n, p in HAND.items()}
    bitmaps: Dict[str, List[List[int]]] = {n: render(p) for n, p in progs.items()}
    clashes = [(a, b) for i, a in enumerate(HAND) for b in list(HAND)[i + 1:] if _distance(bitmaps[a], bitmaps[b]) < 6]
    if clashes:
        raise RuntimeError(f"hand glyphs too alike: {clashes}")
    for name in NAMES:
        if name in progs:
            continue
        rng = random.Random(f"tessera:{name}")
        frame = FAMILY[ROLE[name]]
        for _ in range(60000):
            cand = frame + _inner_candidates(rng, ROLE[name])
            bm = render(cand)
            if sum(map(sum, bm)) < len(points(frame)) + 3:
                continue
            if all(_distance(bm, other) >= 6 for other in bitmaps.values()):
                progs[name] = cand
                bitmaps[name] = bm
                break
        else:
            raise RuntimeError(f"no distinct shape found for {name}")
    return progs


PROGRAMS: Dict[str, List[Prim]] = build()


def code(name: str) -> int:
    return 0x80 | ID[name]


def name_of(code_byte: int) -> str:
    return NAMES[code_byte & 0x7F]


def bitmap(name: str) -> List[List[int]]:
    return render(PROGRAMS[name])


def art(name: str) -> List[str]:
    return ["".join("#" if v else "." for v in row) for row in bitmap(name)]


def pretty(name: str) -> str:
    return PRETTY.get(name, name.lower())


# ---- glyphs.txt -----------------------------------------------------------------------------------------

def export(path: str) -> None:
    with open(path, "w") as f:
        f.write("# tessera glyphs — each glyph is a program: PT x y | ROW y x n | COL x y n | RECT x y w h\n")
        f.write("# (x right, y down, 5 wide, 7 tall). The art below each is what the program draws.\n")
        f.write("# Edit the program lines; keep the names. Art lines are ignored on reading.\n\n")
        for name in NAMES:
            f.write(name + "\n")
            for p in PROGRAMS[name]:
                f.write("  " + " ".join(str(v) for v in p) + "\n")
            for row in art(name):
                f.write("  | " + row + "\n")
            f.write("\n")


def load_overrides(path: str) -> int:
    """Read glyphs.txt: NAME then primitive lines; returns how many glyphs were replaced."""
    if not os.path.exists(path):
        return 0
    n = 0
    cur = None
    prog: List[Prim] = []

    def flush():
        nonlocal n
        if cur in ID and prog:
            PROGRAMS[cur] = list(prog)
            n += 1

    with open(path) as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#") or line.lstrip().startswith("|"):
                continue
            if not line.startswith(" ") and line.strip() in ID:
                flush()
                cur, prog = line.strip(), []
                continue
            parts = line.split()
            if parts and parts[0] in ("PT", "ROW", "COL", "RECT"):
                prog.append(tuple([parts[0]] + [int(v) for v in parts[1:]]))
    flush()
    return n
