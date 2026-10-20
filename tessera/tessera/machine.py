"""Rung 4: a tiny machine the reader can run by hand.

Terms are nested tuples: ('ADD', ('S', 'N'), 'N').  A rule is a pattern and a
replacement; pattern variables are VA, VB, VC, VD.  Reduction is leftmost-
outermost rewriting until no rule applies.  Three rules are enough for Peano
addition, two more for multiplication; after that, anything written as DEF rules
is a program, and the reader who followed the examples can run it.

The lessons cross-check against Rung 2: (ADD 1 2) reduces to the Peano form of 3,
and the message states it equals binary 11, which the reader already knows.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple, Union

Term = Union[str, Tuple]
VARS = ("VA", "VB", "VC", "VD")

# (pattern, replacement), applied in order
RULES: List[Tuple[Term, Term]] = [
    (("ADD", "VA", "N"), "VA"),
    (("ADD", "VA", ("S", "VB")), ("S", ("ADD", "VA", "VB"))),
    (("MUL", "VA", "N"), "N"),
    (("MUL", "VA", ("S", "VB")), ("ADD", ("MUL", "VA", "VB"), "VA")),
    (("DOUBLE", "VA"), ("ADD", "VA", "VA")),
]


def peano(n: int) -> Term:
    t: Term = "N"
    for _ in range(n):
        t = ("S", t)
    return t


def unpeano(t: Term) -> Optional[int]:
    n = 0
    while isinstance(t, tuple) and t[0] == "S" and len(t) == 2:
        n += 1
        t = t[1]
    return n if t == "N" else None


def match(pattern: Term, term: Term, env: Dict[str, Term]) -> bool:
    if isinstance(pattern, str):
        if pattern in VARS:
            if pattern in env:
                return env[pattern] == term
            env[pattern] = term
            return True
        return pattern == term
    if not isinstance(term, tuple) or len(term) != len(pattern):
        return False
    return all(match(p, t, env) for p, t in zip(pattern, term))


def substitute(term: Term, env: Dict[str, Term]) -> Term:
    if isinstance(term, str):
        return env.get(term, term)
    return tuple(substitute(t, env) for t in term)


def step(term: Term, rules: Sequence[Tuple[Term, Term]] = RULES) -> Optional[Term]:
    """One leftmost-outermost rewrite, or None if the term is in normal form."""
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


def reduce(term: Term, rules: Sequence[Tuple[Term, Term]] = RULES, limit: int = 10_000) -> List[Term]:
    """The whole reduction as a list of terms, first to last."""
    trace = [term]
    for _ in range(limit):
        new = step(trace[-1], rules)
        if new is None:
            return trace
        trace.append(new)
    raise RuntimeError("reduction did not terminate")


def tokens(term: Term) -> List[str]:
    """A term as glyph names: ( head arg arg )."""
    if isinstance(term, str):
        return [term]
    out = ["LP"]
    for t in term:
        out += tokens(t)
    out.append("RP")
    return out


def parse(toks: Sequence[str]) -> Term:
    """Glyph names back to a term (the listener's side)."""
    pos = 0

    def rd() -> Term:
        nonlocal pos
        if toks[pos] == "LP":
            pos += 1
            items = []
            while toks[pos] != "RP":
                items.append(rd())
            pos += 1
            return tuple(items)
        t = toks[pos]
        pos += 1
        return t

    return rd()
