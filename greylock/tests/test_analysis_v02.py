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


def test_load_survives_temp_c_null(tmp_path):
    # hardware without a BME280 writes temp_c: null — one such record must not
    # take down the entire analysis (review finding, reproduced)
    from pathlib import Path

    from greylock import config
    from greylock.ledger import Ledger

    cfg = config.load(Path(__file__).parent.parent / "station.example.toml")
    led = Ledger(tmp_path, "cambridge")
    led.append({"t": T0, "site": "cambridge", "clock": "CS1", "ti_ns": 1.0,
                "qerr_ps": 0.0, "temp_c": None, "press_hpa": None, "on_battery": False})
    led.append({"t": T0 + 1, "site": "cambridge", "clock": "CS1", "ti_ns": 2.0,
                "qerr_ps": 0.0, "temp_c": 25.0, "press_hpa": 1013.0, "on_battery": False})
    led.close()
    by_clock = analysis.load(cfg, ledger_dir=tmp_path)
    temps = [r[3] for r in by_clock["CS1"]]
    assert np.isnan(temps[0]) and temps[1] == 25.0


def test_temp_coefficient_survives_partial_time_correlation():
    # a thermal term partly correlated with time must not be attenuated into the
    # slope (Frisch–Waugh fix; review finding)
    rng = np.random.default_rng(8)
    d = np.arange(14)
    temps = 25.0 + 0.3 * d + 2.0 * np.sin(d)

    def temp(day, k):
        return float(temps[day])

    def ti(day, k):
        return 10.0 * day + 5.0 * (temps[day] - 25.0) + float(rng.normal(0, 0.2))

    segs = analysis.segments_for("CS1", _recs(14, ti_fn=ti, temp_fn=temp), T0)
    assert abs(segs[0].temp_coeff_ns_per_c - 5.0) < 1.0


def test_purely_linear_temperature_drift_is_named_not_zeroed():
    d = np.arange(14)
    temps = 24.0 + 0.2 * d                 # the dangerous case: smooth drift

    def temp(day, k):
        return float(temps[day])

    def ti(day, k):
        return 10.0 * day + 5.0 * (temps[day] - 25.0)

    segs = analysis.segments_for("CS1", _recs(14, ti_fn=ti, temp_fn=temp), T0)
    assert any("indistinguishable" in n for n in segs[0].notes)


def test_clean_segment_has_no_scary_notes():
    rng = np.random.default_rng(7)

    def ti(d, k):
        return 10.0 * d + float(rng.normal(0, 2.0))

    segs = analysis.segments_for("CS1", _recs(10, ti_fn=ti), T0)
    s = segs[0]
    assert s.valid and abs(s.slope_ns_day - 10.0) < 1.0
    assert not any("phase step" in n or "thermostat" in n for n in s.notes)
