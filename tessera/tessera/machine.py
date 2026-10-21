"""Rung 4: a tiny machine the reader can run by hand — and, in v0.2, draw with.

Terms are nested tuples: ('ADD', ('S', 'N'), 'N').  Numbers may also appear as
Python ints (the message writes them in binary); the pattern 'N' matches 0 and
the pattern ('S', v) matches any k > 0 with v = k − 1, and ('S', k) with k an int
normalises to k + 1 — the equivalences the message teaches in rung 4.  Pattern
variables are VA, VB, VC, VD.  Reduction is leftmost-outermost rewriting.

Lists are ('CONS', head, rest) ending in 'N'.  Pictures are lists of points
('PT', x, y); ROW, COL, RECT and CAT are rules that build them.  So a picture is
a program, a glyph's shape is a program, and `render` is just: run it.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Set, Tuple, Union

Term = Union[str, int, Tuple]
VARS = ("VA", "VB", "VC", "VD")

ARITH_RULES: List[Tuple[Term, Term]] = [
    (("ADD", "VA", "N"), "VA"),
    (("ADD", "VA", ("S", "VB")), ("S", ("ADD", "VA", "VB"))),
    (("MUL", "VA", "N"), "N"),
    (("MUL", "VA", ("S", "VB")), ("ADD", ("MUL", "VA", "VB"), "VA")),
    (("DOUBLE", "VA"), ("ADD", "VA", "VA")),
]

DRAW_RULES: List[Tuple[Term, Term]] = [
    (("CAT", "N", "VB"), "VB"),
    (("CAT", ("CONS", "VA", "VC"), "VB"), ("CONS", "VA", ("CAT", "VC", "VB"))),
    (("ROW", "VA", "VB", "N"), "N"),
    (("ROW", "VA", "VB", ("S", "VC")), ("CONS", ("PT", "VB", "VA"), ("ROW", "VA", ("S", "VB"), "VC"))),
    (("COL", "VA", "VB", "N"), "N"),
    (("COL", "VA", "VB", ("S", "VC")), ("CONS", ("PT", "VA", "VB"), ("COL", "VA", ("S", "VB"), "VC"))),
    (("RECT", "VA", "VB", "VC", "N"), "N"),
    (("RECT", "VA", "VB", "VC", ("S", "VD")), ("CAT", ("ROW", "VB", "VA", "VC"), ("RECT", "VA", ("S", "VB"), "VC", "VD"))),
]

RULES: List[Tuple[Term, Term]] = ARITH_RULES + DRAW_RULES


# ---- numbers ----------------------------------------------------------------------------------------

def peano(n: int) -> Term:
    t: Term = "N"
    for _ in range(n):
        t = ("S", t)
    return t


def unpeano(t: Term) -> Optional[int]:
    if isinstance(t, int):
        return t
    n = 0
    while isinstance(t, tuple) and t[0] == "S" and len(t) == 2:
        n += 1
        t = t[1]
    if isinstance(t, int):
        return n + t
    return n if t == "N" else None


def is_zero(t: Term) -> bool:
    return t == "N" or t == 0


# ---- matching and rewriting ---------------------------------------------------------------------------

def match(pattern: Term, term: Term, env: Dict[str, Term]) -> bool:
    if isinstance(pattern, str):
        if pattern in VARS:
            if pattern in env:
                return env[pattern] == term
            env[pattern] = term
            return True
        if pattern == "N":
            return is_zero(term)
        return pattern == term
    if isinstance(pattern, int):
        return term == pattern or (pattern == 0 and term == "N")
    # tuple pattern
    if pattern[0] == "S" and len(pattern) == 2 and isinstance(term, int):
        return term > 0 and match(pattern[1], term - 1, env)
    if not isinstance(term, tuple) or len(term) != len(pattern):
        return False
    return all(match(p, t, env) for p, t in zip(pattern, term))


def substitute(term: Term, env: Dict[str, Term]) -> Term:
    if isinstance(term, str):
        return env.get(term, term)
    if isinstance(term, int):
        return term
    return tuple(substitute(t, env) for t in term)


def step(term: Term, rules: Sequence[Tuple[Term, Term]] = RULES) -> Optional[Term]:
    """One leftmost-outermost rewrite, or None if the term is in normal form."""
    if isinstance(term, tuple) and term[0] == "S" and len(term) == 2 and isinstance(term[1], int):
        return term[1] + 1                                   # the binary successor, taught by example
    for pat, rep in rules:
        env: Dict[str, Term] = {}
        if match(pat, term, env):
            return substitute(rep, env)
    if isinstance(term, tuple):
        for i, sub in enumerate(term):
            new = step(sub, rules)
            if new is not None:
                return term[:i] + (new,) + term[i + 1:]
    return None


def reduce(term: Term, rules: Sequence[Tuple[Term, Term]] = RULES, limit: int = 200_000) -> List[Term]:
    """The whole reduction as a list of terms, first to last."""
    trace = [term]
    for _ in range(limit):
        new = step(trace[-1], rules)
        if new is None:
            return trace
        trace.append(new)
    raise RuntimeError("reduction did not terminate")


def normal_form(term: Term, rules: Sequence[Tuple[Term, Term]] = RULES, limit: int = 2_000_000) -> Term:
    """The result without keeping the trace (pictures take thousands of steps)."""
    for _ in range(limit):
        new = step(term, rules)
        if new is None:
            return term
        term = new
    raise RuntimeError("reduction did not terminate")


# ---- lists and pictures -----------------------------------------------------------------------------------

def cons_list(items: Sequence[Term]) -> Term:
    t: Term = "N"
    for it in reversed(items):
        t = ("CONS", it, t)
    return t


def list_items(t: Term) -> List[Term]:
    out = []
    while isinstance(t, tuple) and t[0] == "CONS":
        out.append(t[1])
        t = t[2]
    if not is_zero(t):
        raise ValueError(f"not a proper list: {t!r}")
    return out


def points(term: Term) -> Set[Tuple[int, int]]:
    """Run a picture program and collect its points."""
    pts = set()
    for it in list_items(normal_form(term)):
        if not (isinstance(it, tuple) and it[0] == "PT" and len(it) == 3):
            raise ValueError(f"not a point: {it!r}")
        pts.add((unpeano(it[1]), unpeano(it[2])))
    return pts


def render(term: Term, w: int, h: int) -> List[List[int]]:
    pts = points(term)
    return [[1 if (x, y) in pts else 0 for x in range(w)] for y in range(h)]


def program_term(primitives: Sequence[Tuple]) -> Term:
    """A glyph program (PT/ROW/COL/RECT tuples) as one machine term: nested CATs ending in ∅."""
    t: Term = "N"
    for p in reversed(primitives):
        head = p[0]
        if head == "PT":
            item: Term = ("CONS", ("PT", p[1], p[2]), "N")
        elif head == "ROW":
            item = ("ROW", p[1], p[2], p[3])
        elif head == "COL":
            item = ("COL", p[1], p[2], p[3])
        elif head == "RECT":
            item = ("RECT", p[1], p[2], p[3], p[4])
        else:
            raise ValueError(p)
        t = item if is_zero(t) else ("CAT", item, t)
    return t


# ---- glyph names ↔ terms -------------------------------------------------------------------------------------

def tokens(term: Term) -> List[str]:
    """A term as glyph names: ( head arg arg ); ints as binary digits, with a separator
    between two numerals that would otherwise run together."""
    if isinstance(term, str):
        return [term]
    if isinstance(term, int):
        return ["O" if ch == "1" else "Z" for ch in bin(term)[2:]]
    out = ["LP"]
    prev_num = False
    for t in term:
        if isinstance(t, int) and prev_num:
            out.append("SEP")
        out += tokens(t)
        prev_num = isinstance(t, int)
    out.append("RP")
    return out


def parse(toks: Sequence[str]) -> Term:
    """Glyph names back to a term (the listener's side)."""
    pos = 0

    def rd() -> Term:
        nonlocal pos
        if toks[pos] == "LP":
            pos += 1
            items: List[Term] = []
            while toks[pos] != "RP":
                items.append(rd())
            pos += 1
            return tuple(items)
        if toks[pos] == "SEP":
            pos += 1
            return rd()
        if toks[pos] in ("Z", "O"):
            j = pos
            while j < len(toks) and toks[j] in ("Z", "O"):
                j += 1
            val = int("".join("1" if t == "O" else "0" for t in toks[pos:j]), 2)
            pos = j
            return val
        t = toks[pos]
        pos += 1
        return t

    return rd()
