"""The alphabet: every glyph is a 5 × 7 bitmap and an 8-bit code.

Codes are 1xxxxxxx — the leading 1 is what lets a stranger find the token width
(at the right width one column is all ones), and it means a run of sixteen zeros
can never occur inside a message, so it can serve as the frame mark.

The shapes are placeholders.  `tessera glyphs --export` writes them to glyphs.txt
as '#' and '.' art; edit that file (or draw your own) and the package reads it back
with `load_overrides`.  Nothing in the ladder depends on the shapes — only on the
order of the lessons that define them.
"""
from __future__ import annotations

import os
import random
from typing import Dict, List

# order fixes the ids; append new names at the end so old messages keep decoding
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
]
ID: Dict[str, int] = {n: i for i, n in enumerate(NAMES)}

# how a human reads the transcript
PRETTY: Dict[str, str] = {
    "DOT": "·", "Z": "0", "O": "1", "END": "⏎", "EQ": "=", "PLUS": "+", "MINUS": "−", "TIMES": "×",
    "DIV": "÷", "LT": "<", "GT": ">", "TRUE": "⊤", "FALSE": "⊥", "NOT": "¬", "AND": "∧", "OR": "∨",
    "IMP": "⊃", "LP": "(", "RP": ")", "ARROW": "⇒", "DEF": "≝", "VA": "a", "VB": "b", "VC": "c", "VD": "d",
    "N": "∅", "S": "S", "ADD": "add", "MUL": "mul", "DOUBLE": "double", "TICK": "tick", "WAVE": "wave",
    "H": "H", "LIGHT": "light", "CLOCK_A": "clockA", "CLOCK_B": "clockB", "HEIGHT": "height", "G": "g",
    "RATE": "rate", "PER": "per", "PULSAR": "pulsar", "PERIOD": "period", "DRIFT": "drift", "STAMP": "now",
    "SHIP": "ship", "DISTANCE": "distance", "TIME_SHIP": "shiptime", "TIME_HOME": "hometime", "SPEED": "speed",
    "AGENT": "agent", "TARGET": "target", "DANGER": "danger", "STEP": "step", "GOOD": "good", "BAD": "bad",
}

HAND: Dict[str, List[str]] = {
    "DOT":   [".....", ".....", ".....", "..#..", ".....", ".....", "....."],
    "Z":     [".###.", ".#.#.", ".#.#.", ".#.#.", ".#.#.", ".#.#.", ".###."],
    "O":     ["..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "END":   ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "EQ":    [".....", ".....", "#####", ".....", "#####", ".....", "....."],
    "PLUS":  [".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."],
    "MINUS": [".....", ".....", "#####", "#####", ".....", ".....", "....."],
    "TIMES": [".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "....."],
    "DIV":   [".....", ".###.", ".....", "#####", ".....", ".###.", "....."],
    "LT":    [".....", "...#.", "..#..", ".#...", "..#..", "...#.", "....."],
    "GT":    [".....", ".#...", "..#..", "...#.", "..#..", ".#...", "....."],
    "TRUE":  ["..#..", "..#..", ".###.", ".###.", "#####", "#####", "....."],
    "FALSE": ["#####", "#####", ".###.", ".###.", "..#..", "..#..", "....."],
    "NOT":   [".....", "#####", "....#", "....#", "....#", ".....", "....."],
    "AND":   [".....", "..#..", "..#..", ".#.#.", ".#.#.", "#...#", "....."],
    "OR":    [".....", "#...#", ".#.#.", ".#.#.", "..#..", "..#..", "....."],
    "IMP":   [".....", "###..", "...#.", "....#", "...#.", "###..", "....."],
    "LP":    ["...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."],
    "RP":    [".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."],
    "ARROW": [".....", "...#.", "....#", "#####", "....#", "...#.", "....."],
    "DEF":   ["..#..", ".#.#.", "#####", ".....", "#####", ".....", "#####"],
    "N":     [".....", ".....", ".###.", ".#.#.", ".###.", ".....", "....."],
    "S":     [".....", "..#..", ".#.#.", "#...#", ".....", ".....", "....."],
    "TICK":  [".....", "#.#.#", "#.#.#", "#.#.#", ".....", ".....", "....."],
    "WAVE":  [".....", ".#...", "#.#.#", "...#.", ".....", ".#...", "#.#.#"],
    "H":     ["#...#", "#...#", "#####", "#...#", "#...#", ".....", "....."],
    "LIGHT": ["..#..", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "..#.."],
}


def _procedural(name: str) -> List[str]:
    """A deterministic, left-right symmetric 5 × 7 shape for a glyph with no hand drawing."""
    rng = random.Random(f"tessera:{name}")
    while True:
        rows = []
        for _ in range(7):
            left = [rng.random() < 0.45 for _ in range(2)]
            mid = rng.random() < 0.5
            r = left + [mid] + left[::-1]
            rows.append("".join("#" if b else "." for b in r))
        on = sum(row.count("#") for row in rows)
        if 10 <= on <= 22 and rows[0] != "....." and rows[6] != ".....":
            return rows


def _distance(a: List[str], b: List[str]) -> int:
    return sum(x != y for ra, rb in zip(a, b) for x, y in zip(ra, rb))


def build() -> Dict[str, List[str]]:
    glyphs: Dict[str, List[str]] = {}
    for name in NAMES:
        if name in HAND:
            glyphs[name] = HAND[name]
            continue
        cand = _procedural(name)
        salt = 0
        while any(_distance(cand, g) < 6 for g in glyphs.values()):
            salt += 1
            cand = _procedural(f"{name}#{salt}")
        glyphs[name] = cand
    return glyphs


GLYPHS: Dict[str, List[str]] = build()


def code(name: str) -> int:
    return 0x80 | ID[name]


def name_of(code_byte: int) -> str:
    return NAMES[code_byte & 0x7F]


def bitmap(name: str) -> List[List[int]]:
    return [[1 if ch == "#" else 0 for ch in row] for row in GLYPHS[name]]


def export(path: str) -> None:
    with open(path, "w") as f:
        f.write("# tessera glyphs — 5 x 7, '#' on, '.' off. Edit freely; keep the names.\n\n")
        for name in NAMES:
            f.write(name + "\n" + "\n".join(GLYPHS[name]) + "\n\n")


def load_overrides(path: str) -> int:
    """Read a glyphs.txt and replace shapes in place; returns how many were replaced."""
    if not os.path.exists(path):
        return 0
    n = 0

    def is_comment(ln: str) -> bool:
        # '#' also opens pixel rows ('#....'), so a line only counts as a comment
        # when it cannot be a 5-wide row of the {#, .} alphabet
        return ln.startswith("#") and not (len(ln) == 5 and set(ln) <= {"#", "."})

    with open(path) as f:
        lines = [ln.rstrip("\n") for ln in f if not is_comment(ln.rstrip("\n"))]
    i = 0
    while i < len(lines):
        if lines[i].strip() in ID:
            name = lines[i].strip()
            rows = lines[i + 1:i + 8]
            if len(rows) == 7 and all(len(r) == 5 and set(r) <= {"#", "."} for r in rows):
                GLYPHS[name] = rows
                n += 1
            i += 8
        else:
            i += 1
    return n


def pretty(name: str) -> str:
    return PRETTY.get(name, name.lower())
