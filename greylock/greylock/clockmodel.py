"""Noise models for the hardware, used by the digital twin (sim.py).

The point of simulating is not realism for its own sake: it lets the whole
pipeline — ledger, analysis, display — run and be tested before a single clock
is borrowed, and it says in advance what a good run and a bad run look like.

Models (all amplitudes are spec-like, not measured; replace with measured ADEV
from the co-location weeks once the real clocks are in hand):

  Cesium beam clock (5071A-class):
    * white frequency noise  σ_y(1 s) ≈ 5e-12 (high-performance tube)
    * flicker/floor          σ_y(≥1 d) ≈ 5e-15, modelled as a slowly wandering
                             frequency (Ornstein–Uhlenbeck, 2-day correlation)
    * intrinsic offset       a fixed fractional frequency error per unit,
                             up to the ±5e-13 accuracy spec (typically ~1e-13)
    * temperature            ~2e-15 per °C of case temperature
  GNSS timing receiver (ZED-F9T / NEO-F10T-class) 1 PPS vs GPS time:
    * sawtooth               the pulse is quantised to the receiver clock; the
                             receiver reports the residual (qErr) so it can be
                             removed; amplitude ±4 ns here
    * white jitter           2 ns per pulse
    * daily systematic       multipath/ephemeris/ionosphere, ~2 ns, 1-day correlation
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np


@dataclass
class CesiumModel:
    name: str = "CS1"
    sigma_y_1s: float = 5e-12
    floor: float = 5e-15
    floor_tau_s: float = 2 * 86400.0
    intrinsic_offset: float = 1.0e-13      # fractional frequency error of this unit
    temp_coeff_per_c: float = 2e-15
    temp_setpoint_c: float = 25.0
    seed: int = 1
    # state
    _x: float = field(default=0.0, repr=False)        # phase, seconds
    _y_floor: float = field(default=0.0, repr=False)  # slow frequency wander
    _rng: np.random.Generator = field(default=None, repr=False)

    def __post_init__(self):
        self._rng = np.random.default_rng(self.seed)
        self._y_floor = self._rng.normal(0.0, self.floor)

    def step(self, dt: float, grav_rate: float, temp_c: float) -> float:
        """Advance the clock by dt seconds under fractional rate grav_rate; return phase (s)."""
        # Ornstein–Uhlenbeck wander for the floor
        a = math.exp(-dt / self.floor_tau_s)
        self._y_floor = a * self._y_floor + math.sqrt(1 - a * a) * self._rng.normal(0.0, self.floor)
        y = (
            self.intrinsic_offset
            + grav_rate
            + self._y_floor
            + self.temp_coeff_per_c * (temp_c - self.temp_setpoint_c)
        )
        # white FM: phase random walk with variance σ_y(1s)² · dt (dt in seconds)
        self._x += y * dt + self._rng.normal(0.0, self.sigma_y_1s * math.sqrt(dt))
        return self._x


@dataclass
class GnssPpsModel:
    """Error of the receiver's 1 PPS relative to true GPS (geoid-rate) time, seconds."""
    sawtooth_ns: float = 4.0
    white_ns: float = 2.0
    systematic_ns: float = 2.0
    systematic_tau_s: float = 86400.0
    seed: int = 2
    _sys: float = field(default=0.0, repr=False)
    _rng: np.random.Generator = field(default=None, repr=False)

    def __post_init__(self):
        self._rng = np.random.default_rng(self.seed)

    def step(self, dt: float) -> tuple[float, float]:
        """Return (pulse_error_s, reported_qerr_ps)."""
        a = math.exp(-dt / self.systematic_tau_s)
        self._sys = a * self._sys + math.sqrt(1 - a * a) * self._rng.normal(0.0, self.systematic_ns)
        saw = self._rng.uniform(-self.sawtooth_ns, self.sawtooth_ns)
        white = self._rng.normal(0.0, self.white_ns)
        err_ns = saw + white + self._sys
        # the receiver knows the quantisation part exactly and reports it in ps
        return err_ns * 1e-9, saw * 1e3


@dataclass
class EnvironmentModel:
    """Case temperature held by a thermostat around the set point, with weather leaking in."""
    setpoint_c: float = 25.0
    control_sigma_c: float = 0.5
    outside_mean_c: float = 15.0
    outside_swing_c: float = 6.0
    leak: float = 0.03   # fraction of outside swing that reaches the clock
    pressure_hpa: float = 1013.0
    seed: int = 3
    _rng: np.random.Generator = field(default=None, repr=False)

    def __post_init__(self):
        self._rng = np.random.default_rng(self.seed)

    def sample(self, t_unix: float) -> tuple[float, float, float]:
        day_phase = 2 * math.pi * ((t_unix % 86400.0) / 86400.0)
        outside = self.outside_mean_c + self.outside_swing_c * math.sin(day_phase - 2.0)
        case = self.setpoint_c + self.leak * (outside - self.setpoint_c) + self._rng.normal(0.0, self.control_sigma_c)
        return case, outside, self.pressure_hpa
