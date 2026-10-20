"""Hydrogen units: the one physical anchor the message spends.

The 21-cm hyperfine transition of hydrogen has frequency f_H = 1,420,405,751.768 Hz.
One TICK is its period; one WAVE is its wavelength.  Then c = 1 WAVE/TICK exactly,
and every quantity in the message is an integer or a ratio of integers.

The Greylock numbers below are the project's own clock machine
(claude/greylock-time-machine.md) rewritten in these units.
"""
from __future__ import annotations

from fractions import Fraction

C = 299_792_458.0
F_H = 1_420_405_751.768              # Hz (Essen et al. 1971; CODATA)
TICK = 1.0 / F_H                      # s
WAVE = C / F_H                        # m  (0.211 061 14 m)
G0 = 9.806_65                         # m/s²
DAY = 86_400.0
YEAR = 365.25 * DAY
LY = C * YEAR


def seconds_to_ticks(s: float) -> float:
    return s * F_H


def metres_to_waves(m: float) -> float:
    return m / WAVE


def accel_to_hydrogen(a_ms2: float) -> float:
    """m/s² → WAVE/TICK²."""
    return a_ms2 / WAVE * TICK * TICK


def as_ratio(x: float, max_den: int = 10**18) -> Fraction:
    """A float as a fraction of integers, the way the message writes it."""
    return Fraction(x).limit_denominator(max_den)


# ---- the Greylock ledger in hydrogen units ----------------------------------------
GREYLOCK_HEIGHT_M = 1063.0 - 6.0                      # summit clock above the Cambridge clock
GREYLOCK_HEIGHT_WAVES = round(metres_to_waves(GREYLOCK_HEIGHT_M))     # 5,008
G_WAVE_PER_TICK2 = accel_to_hydrogen(G0)                               # 2.303e-17
G_DENOMINATOR = round(1.0 / G_WAVE_PER_TICK2)                          # g = 1 WAVE / (D TICK²)
RATE = G0 * GREYLOCK_HEIGHT_M / C**2                                   # 1.1533e-13
DAY_TICKS = round(seconds_to_ticks(DAY))                               # 122,723,056,952,755
LEAD_PER_DAY_TICKS = RATE * DAY_TICKS                                  # 14.15 ticks per day
LEAD_PER_DAY_CENTITICKS = round(LEAD_PER_DAY_TICKS * 100)              # 1,415

# ---- the ship (Proxima torch, from timeship) ------------------------------------------
PROXIMA_LY = 4.2465
PROXIMA_WAVES = round(metres_to_waves(PROXIMA_LY * LY))                # 1.90e17
SHIP_YEARS = 3.5421                                                    # 1 g torch, from timeship
EARTH_YEARS = 5.8726
SHIP_TICKS = round(seconds_to_ticks(SHIP_YEARS * YEAR))
EARTH_TICKS = round(seconds_to_ticks(EARTH_YEARS * YEAR))
LEAD_TICKS = EARTH_TICKS - SHIP_TICKS
PEAK_BETA_PER_MILLION = 949_654                                        # β_max = 0.949654
