"""The listener: a stranger's decoder, with no key.

Given only a string of bits it tries to do what a reader of the ladder would do:
find the token width, the alphabet, whether the thing looks like a language at
all (Zipf's law, conditional entropy — the tests SETI runs on whale song), the
statement delimiter, then the counting lesson, then the operators, then truth.
What it recovers is reported as "token 0x8a means +".  Running this on our own
message is the only honest test that the first rungs are decodable; it is also,
unchanged, the tool for reading someone else's.
"""
from __future__ import annotations

import math
import zlib
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Sequence, Tuple


# ---- rung 0: is it a message, and how wide are its tokens -------------------------------------

def compressibility(bits: str) -> float:
    """Compressed size over raw size (1-bit per char packed first). Noise ≈ 1, structure < 1."""
    packed = int(bits, 2).to_bytes((len(bits) + 7) // 8, "big") if bits else b""
    return len(zlib.compress(packed, 9)) / max(1, len(packed))


def find_width(bits: str, max_width: int = 32) -> Optional[int]:
    """The smallest width at which some column is constant across all tokens."""
    for w in range(2, max_width + 1):
        if len(bits) % w:
            continue
        n = len(bits) // w
        for col in range(w):
            column = bits[col::w]
            if column.count("1") in (0, n):
                return w
    return None


def tokenize(bits: str, width: int) -> List[int]:
    return [int(bits[i:i + width], 2) for i in range(0, len(bits), width)]


# ---- language-likeness --------------------------------------------------------------------------

def zipf_slope(tokens: Sequence[int]) -> float:
    counts = sorted(Counter(tokens).values(), reverse=True)
    xs = [math.log(r + 1) for r in range(len(counts))]
    ys = [math.log(c) for c in counts]
    n = len(xs)
    if n < 3:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0


def entropy(tokens: Sequence[int]) -> float:
    n = len(tokens)
    return -sum(c / n * math.log2(c / n) for c in Counter(tokens).values())


def conditional_entropy(tokens: Sequence[int]) -> float:
    pairs = Counter(zip(tokens, tokens[1:]))
    firsts = Counter(tokens[:-1])
    n = len(tokens) - 1
    return -sum(c / n * math.log2(c / firsts[a]) for (a, b), c in pairs.items())


# ---- segmentation and the counting lesson ----------------------------------------------------

def _run(seq: Sequence[int]) -> Tuple[Optional[int], int]:
    if not seq:
        return None, 0
    k = 0
    while k < len(seq) and seq[k] == seq[0]:
        k += 1
    return seq[0], k


def _counting_examples(segs: Sequence[Sequence[int]], r: int):
    out = []
    for s in segs:
        run, k = _run(s)
        tail = s[k:]
        if run == r and k >= 1 and tail and len(tail) <= 12 and r not in tail:
            out.append((k, list(tail)))
    return out


def _binary_consistent(examples) -> Optional[Tuple[int, int]]:
    symbols = set(t for _, tail in examples for t in tail)
    if len(symbols) != 2:
        return None
    a, b = sorted(symbols)
    for zero, one in ((a, b), (b, a)):
        if all("".join("1" if t == one else "0" for t in tail) == bin(n)[2:] for n, tail in examples):
            return zero, one
    return None


def find_delimiter_and_dot(tokens: Sequence[int]) -> Tuple[Optional[int], Optional[int]]:
    """The delimiter and the counting mark are the pair for which the most statements have the
    shape  mark×n  name  with the names consistent with binary — the one prior the listener
    is allowed: that the message opens by counting."""
    best = (0, None, None)
    for d, _ in Counter(tokens).most_common(25):
        segs = _split(tokens, d)
        starters = Counter(s[0] for s in segs if s)
        for r, _ in starters.most_common(6):
            if r == d:
                continue
            ex = _counting_examples(segs, r)
            if len(ex) < 6 or _binary_consistent(ex) is None:
                continue
            if len(ex) > best[0]:
                best = (len(ex), d, r)
    return best[1], best[2]


def _split(tokens: Sequence[int], d: int) -> List[List[int]]:
    out, cur = [], []
    for t in tokens:
        if t == d:
            out.append(cur)
            cur = []
        else:
            cur.append(t)
    if cur:
        out.append(cur)
    return out


def recover_counting(segs: Sequence[Sequence[int]], dot: int) -> Optional[Tuple[int, int]]:
    """Returns (zero_token, one_token) if the binary names of the dot counts are consistent."""
    ex = _counting_examples(segs, dot)
    if len(ex) < 4:
        return None
    return _binary_consistent(ex)


# ---- numbers, operators, truth ------------------------------------------------------------------

def parse_numbers(seg: Sequence[int], zero: int, one: int) -> List[Tuple[str, int]]:
    out: List[Tuple[str, int]] = []
    i = 0
    while i < len(seg):
        if seg[i] in (zero, one):
            j = i
            while j < len(seg) and seg[j] in (zero, one):
                j += 1
            out.append(("num", int("".join("1" if t == one else "0" for t in seg[i:j]), 2)))
            i = j
        else:
            out.append(("sym", seg[i]))
            i += 1
    return out


OPS = {
    "+": lambda a, b: a + b,
    "−": lambda a, b: a - b,
    "×": lambda a, b: a * b,
    "÷": lambda a, b: a // b if b and a % b == 0 else None,
}


def recover_operators(parsed: Sequence[Sequence[Tuple[str, int]]]) -> Dict[int, str]:
    """From 5-item statements  num X num Y num  infer = and the four operators;
    from 3-item statements  num X num  infer < and >."""
    meaning: Dict[int, str] = {}
    fives = [p for p in parsed if len(p) == 5 and [k for k, _ in p] == ["num", "sym", "num", "sym", "num"]]
    if fives:
        eq = Counter(p[3][1] for p in fives).most_common(1)[0][0]
        meaning[eq] = "="
        by_op: Dict[int, List[Tuple[int, int, int]]] = defaultdict(list)
        for p in fives:
            if p[3][1] == eq:
                by_op[p[1][1]].append((p[0][1], p[2][1], p[4][1]))
        for tok, triples in by_op.items():
            for sym, fn in OPS.items():
                if all(fn(a, b) == c for a, b, c in triples):
                    meaning[tok] = sym
                    break
    threes = [p for p in parsed if len(p) == 3 and [k for k, _ in p] == ["num", "sym", "num"]]
    by_cmp: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
    for p in threes:
        by_cmp[p[1][1]].append((p[0][1], p[2][1]))
    for tok, pairs in by_cmp.items():
        if tok in meaning:
            continue
        if all(a < b for a, b in pairs):
            meaning[tok] = "<"
        elif all(a > b for a, b in pairs):
            meaning[tok] = ">"
    return meaning


def recover_truth(parsed: Sequence[Sequence[Tuple[str, int]]], meaning: Dict[int, str]) -> Dict[int, str]:
    """Statements of the form  A num op num = num B T : A,B are a bracket pair and T is ⊤ or ⊥."""
    found: Dict[int, str] = {}
    verdicts: Dict[int, set] = defaultdict(set)
    brackets: Counter = Counter()
    for p in parsed:
        if len(p) != 8:
            continue
        kinds = [k for k, _ in p]
        if kinds != ["sym", "num", "sym", "num", "sym", "num", "sym", "sym"]:
            continue
        op, eq = meaning.get(p[2][1]), meaning.get(p[4][1])
        if op not in OPS or eq != "=":
            continue
        truth = OPS[op](p[1][1], p[3][1]) == p[5][1]
        verdicts[p[7][1]].add(truth)
        brackets[(p[0][1], p[6][1])] += 1
    for tok, vs in verdicts.items():
        if vs == {True}:
            found[tok] = "⊤"
        elif vs == {False}:
            found[tok] = "⊥"
    if brackets:
        (l, r), _ = brackets.most_common(1)[0]
        found[l], found[r] = "(", ")"
    return found


# ---- dialogue: good and bad are judgments the reader can check ------------------------------------

CMP = {"<": lambda a, b: a < b, ">": lambda a, b: a > b}


def _bracket_span(p):
    """The first (...) span of a parsed statement, as (start, end) indices, or None."""
    depth, start = 0, None
    for i, (k, v) in enumerate(p):
        if k != "sym":
            continue
        m = MEANING_HINT.get(v)
        if m == "(":
            if depth == 0:
                start = i
            depth += 1
        elif m == ")":
            depth -= 1
            if depth == 0 and start is not None:
                return start, i
    return None


MEANING_HINT: Dict[int, str] = {}


def _eval_relation(items, meaning, env):
    """items: a bracketed relation's inner items.  Returns True/False, or None if not evaluable."""
    vals = []
    ops = []
    for k, v in items:
        if k == "num":
            vals.append(v)
        else:
            m = meaning.get(v)
            if m in OPS or m in CMP or m == "=":
                ops.append(m)
            elif v in env:
                vals.append(env[v])
            else:
                return None
    if len(ops) == 2 and len(vals) == 3 and ops[0] in OPS and ops[1] == "=":
        r = OPS[ops[0]](vals[0], vals[1])
        return r == vals[2]
    if len(ops) == 1 and len(vals) == 2 and ops[0] in CMP:
        return CMP[ops[0]](vals[0], vals[1])
    return None


def recover_judgments(parsed, meaning: Dict[int, str]) -> Dict[int, str]:
    """Question / answer / judgment triples: the token that follows only true answers is GOOD,
    the one that follows only false answers is BAD, and the symbol that takes a value is a variable."""
    MEANING_HINT.clear()
    MEANING_HINT.update(meaning)
    verdicts: Dict[int, set] = defaultdict(set)
    variables: Counter = Counter()
    for i in range(len(parsed) - 2):
        q, a, j = parsed[i], parsed[i + 1], parsed[i + 2]
        qs, as_ = _bracket_span(q), _bracket_span(a)
        if qs is None or as_ is None or len(j) < 2 or j[-1][0] != "sym":
            continue
        q_inner = q[qs[0] + 1:qs[1]]
        a_inner = a[as_[0] + 1:as_[1]]
        # the answer has the form  var = num
        if not (len(a_inner) == 3 and a_inner[0][0] == "sym" and meaning.get(a_inner[1][1]) == "=" and a_inner[2][0] == "num"):
            continue
        var, val = a_inner[0][1], a_inner[2][1]
        if not any(k == "sym" and v == var for k, v in q_inner):
            continue
        truth = _eval_relation(q_inner, meaning, {var: val})
        if truth is None:
            continue
        verdicts[j[-1][1]].add(truth)
        variables[var] += 1
    found: Dict[int, str] = {}
    for tok, vs in verdicts.items():
        if vs == {True}:
            found[tok] = "good"
        elif vs == {False}:
            found[tok] = "bad"
    if variables:
        found[variables.most_common(1)[0][0]] = "a"
    return found


# ---- bitmaps ----------------------------------------------------------------------------------------

def factor_pairs(n: int) -> List[Tuple[int, int]]:
    out = []
    for a in range(2, int(math.isqrt(n)) + 1):
        if n % a == 0:
            out.append((a, n // a))
    return out


def unfold(bits: str) -> List[Tuple[int, int]]:
    """Ways to fold a bit string into a rectangle; a prime × prime length has exactly one."""
    return factor_pairs(len(bits))


# ---- the whole blind pass ------------------------------------------------------------------------------

def decode_blind(bits: str) -> Dict[str, object]:
    report: Dict[str, object] = {"compressibility": compressibility(bits)}
    w = find_width(bits)
    report["width"] = w
    if w is None:
        return report
    toks = tokenize(bits, w)
    report["alphabet_size"] = len(set(toks))
    report["zipf_slope"] = zipf_slope(toks)
    report["entropy_bits"] = entropy(toks)
    report["conditional_entropy_bits"] = conditional_entropy(toks)
    d, dot = find_delimiter_and_dot(toks)
    report["delimiter"], report["dot"] = d, dot
    if d is None:
        return report
    segs = _split(toks, d)
    report["statements"] = len(segs)
    zo = recover_counting(segs, dot)
    report["digits"] = zo
    if zo is None:
        return report
    zero, one = zo
    parsed = [parse_numbers(s, zero, one) for s in segs]
    meaning = recover_operators(parsed)
    meaning.update(recover_truth(parsed, meaning))
    meaning.update(recover_judgments(parsed, meaning))
    meaning[dot] = "·"
    meaning[d] = "⏎"
    meaning[zero] = "0"
    meaning[one] = "1"
    report["meaning"] = dict(sorted(meaning.items()))
    return report


def report_text(bits: str) -> str:
    r = decode_blind(bits)
    lines = [f"compressibility {r['compressibility']:.3f} (noise ≈ 1.0)"]
    if r.get("width") is None:
        lines.append("no constant column at any width up to 32: no token structure found")
        return "\n".join(lines)
    lines.append(f"token width {r['width']} bits; alphabet {r['alphabet_size']}; Zipf slope {r['zipf_slope']:.2f}; "
                 f"H1 {r['entropy_bits']:.2f} bits, H2 {r['conditional_entropy_bits']:.2f} bits")
    if r.get("delimiter") is None:
        lines.append("no counting lesson found")
        return "\n".join(lines)
    lines.append(f"{r['statements']} statements; delimiter 0x{r['delimiter']:02x}; the repeated mark is 0x{r['dot']:02x}")
    if r.get("digits") is None:
        lines.append("the counts' names are not consistent with binary")
        return "\n".join(lines)
    lines.append("recovered meanings:")
    for tok, m in r["meaning"].items():
        lines.append(f"  0x{tok:02x} → {m}")
    return "\n".join(lines)
