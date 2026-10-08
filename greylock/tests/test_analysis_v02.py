"""v0.2 analysis rigor: outlier clipping, step detection, temperature diagnostic."""
import numpy as np

from greylock import analysis

DAY = 86400.0
T0 = 20834 * DAY * 1000 / 1000               # a UTC midnight, so d counts whole bins


def _recs(days, per_day=24, ti_fn=lambda d, k: 0.0, temp_fn=lambda d, k: 25.0, site="cambridge"):
    out = []
    for d in range(days):
        for k in range(per_day):
            t = T0 + d * DAY + k * (DAY / per_day)
            out.append((t, site, ti_fn(d, k), temp_fn(d, k), False))
    return out


def test_outliers_are_clipped_and_counted():
    rng = np.random.default_rng(5)

    def ti(d, k):
        if d == 1 and k == 3:
            return 1e6                      # one glitched serial line
        return float(rng.normal(0.0, 2.0))

    pts = analysis.daily_points(_recs(3, ti_fn=ti), T0)
    assert len(pts) == 3
    assert pts[1].n_rejected >= 1
    assert abs(pts[1].ti_ns) < 10.0          # the day survived the 1 ms spike
    segs = analysis.segments_for("CS1", _recs(3, ti_fn=ti), T0)
    assert any("outlier" in n for n in segs[0].notes)


def test_phase_step_is_reported_not_averaged():
    def ti(d, k):
        return 100.0 if d >= 5 else 0.0      # a 100 ns step between day 4 and 5

    segs = analysis.segments_for("CS1", _recs(10, ti_fn=ti), T0)
    assert len(segs) == 1
    assert any("phase step" in n for n in segs[0].notes)


def test_temperature_coefficient_recovered():
    rng = np.random.default_rng(6)
    temps = 25.0 + 2.0 * np.sin(np.arange(14))

    def temp(d, k):
        return float(temps[d])

    def ti(d, k):
        return 10.0 * d + 5.0 * (temps[d] - 25.0) + float(rng.normal(0, 0.2))

    segs = analysis.segments_for("CS1", _recs(14, ti_fn=ti, temp_fn=temp), T0)
    s = segs[0]
    assert abs(s.temp_coeff_ns_per_c - 5.0) < 1.0
    assert any("thermostat" in n for n in s.notes)


def test_clean_segment_has_no_scary_notes():
    rng = np.random.default_rng(7)

    def ti(d, k):
        return 10.0 * d + float(rng.normal(0, 2.0))

    segs = analysis.segments_for("CS1", _recs(10, ti_fn=ti), T0)
    s = segs[0]
    assert s.valid and abs(s.slope_ns_day - 10.0) < 1.0
    assert not any("phase step" in n or "thermostat" in n for n in s.notes)
