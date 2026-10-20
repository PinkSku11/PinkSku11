"""Rung 5: the time stamp — a message that dates itself.

Pulsar periods lengthen at known rates.  The message lists several pulsars as
(period, spin-down rate) at the moment of writing, in hydrogen ticks.  A reader
anywhere in the Galaxy, any time later, measures today's periods: for the right
pulsar, (P_now − P_then) / Ṗ is the same Δt for every entry in the list.  That
common Δt both identifies the pulsars and dates the message — the Pioneer-plaque
idea turned into a clock.

Catalogue values are approximate (ATNF-style, from memory): replace them with a
current ephemeris before etching anything.  The decoding logic is what matters.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from statistics import median
from typing import Dict, List, Optional, Sequence, Tuple

from .units import F_H, YEAR


@dataclass(frozen=True)
class Pulsar:
    name: str
    period_s: float        # P
    pdot: float            # dP/dt, dimensionless (s/s)
    note: str = ""


CATALOGUE: List[Pulsar] = [
    Pulsar("PSR B0531+21 (Crab)", 0.0333924123, 4.21e-13, "young; dates to hours but glitches"),
    Pulsar("PSR B0833−45 (Vela)", 0.0893, 1.25e-13, "glitches often"),
    Pulsar("PSR B0329+54", 0.714520, 2.05e-15, "bright, steady"),
    Pulsar("PSR B1919+21", 1.337302, 1.348e-15, "the first pulsar found (1967)"),
    Pulsar("PSR B1133+16", 1.187913, 3.73e-15, ""),
    Pulsar("PSR B0950+08", 0.253065, 2.30e-16, "nearby"),
    Pulsar("PSR J0633+1746 (Geminga)", 0.237099, 1.10e-14, "gamma-ray pulsar"),
    Pulsar("PSR B1913+16 (Hulse–Taylor)", 0.059030, 8.63e-18, "the binary pulsar"),
    Pulsar("PSR J0737−3039A", 0.022699, 1.76e-18, "the double pulsar"),
    Pulsar("PSR B1821−24", 0.003054, 1.62e-18, "millisecond pulsar in M28"),
    Pulsar("PSR J0437−4715", 0.005757, 5.73e-20, "the most stable clock we know"),
    Pulsar("PSR B1937+21", 0.001558, 1.05e-19, "the first millisecond pulsar"),
]


def encode(cat: Sequence[Pulsar] = CATALOGUE, milli: int = 1000) -> List[Tuple[int, int]]:
    """Each pulsar as (period in milli-ticks, 1/Ṗ as an integer)."""
    out = []
    for p in cat:
        out.append((round(p.period_s * F_H * milli), round(1.0 / p.pdot)))
    return out


def decode(stamp: Sequence[Tuple[int, int]], today: Sequence[Pulsar], milli: int = 1000,
           max_years: float = 1e7) -> Dict[str, object]:
    """Given the stamp and today's catalogue, find the common Δt (years since the message)."""
    hits = []
    for p_milli, inv_pdot in stamp:
        P_then = p_milli / milli / F_H
        pdot = 1.0 / inv_pdot
        best: Optional[Tuple[float, Pulsar]] = None
        for q in today:
            if not (0.5 < q.pdot / pdot < 2.0):
                continue
            dt = (q.period_s - P_then) / pdot
            if -1.0 * YEAR < dt < max_years * YEAR and (best is None or abs(dt) < abs(best[0])):
                best = (dt, q)
        if best is not None:
            hits.append((best[0] / YEAR, best[1].name))
    if not hits:
        return {"years": None, "spread_years": None, "matches": []}
    years = [h[0] for h in hits]
    m = median(years)
    agreeing = [h for h in hits if abs(h[0] - m) < max(1.0, 0.05 * abs(m))]
    return {
        "years": median([h[0] for h in agreeing]),
        "spread_years": (max(h[0] for h in agreeing) - min(h[0] for h in agreeing)) if agreeing else None,
        "matches": agreeing,
    }


def aged(cat: Sequence[Pulsar], years: float, jitter: float = 0.0) -> List[Pulsar]:
    """The catalogue as a reader would measure it `years` later (a test helper)."""
    import random
    rng = random.Random(7)
    out = []
    for p in cat:
        P = p.period_s + p.pdot * years * YEAR
        if jitter:
            P *= 1.0 + rng.uniform(-jitter, jitter)
        out.append(Pulsar(p.name, P, p.pdot, p.note))
    return out


def resolution_years(p: Pulsar, period_precision_s: float = 1e-12) -> float:
    """How finely a reader with this period precision can date the message from one pulsar."""
    return period_precision_s / p.pdot / YEAR
