import math
import shutil
from pathlib import Path

import pytest

from greylock import analysis, config, physics, sim

EXAMPLE = Path(__file__).parent.parent / "station.example.toml"


def test_prediction_numbers():
    r = physics.gravitational_rate(physics.GREYLOCK, physics.CAMBRIDGE)
    assert abs(physics.rate_to_ns_per_day(r) - 9.96) < 0.05
    # a clock at the reference site runs at (almost) the geoid rate
    assert abs(physics.rate_to_ns_per_day(physics.gravitational_rate(physics.CAMBRIDGE, physics.CAMBRIDGE))) < 1e-9
    # moving clocks run slow; westbound Sagnac is positive
    assert physics.velocity_rate(250.0) < 0
    assert physics.sagnac_rate(-250.0, 40.0) > 0
    # transport integral: 3 h at 300 m plus 100 km/h gives a fraction of a nanosecond
    track = [(i * 60.0, 42.5, 300.0, 27.8, 0.0) for i in range(181)]
    off = physics.transport_offset_ns(track, physics.CAMBRIDGE)
    assert 0.2 < off < 0.4


def _write_cfg(tmp_path, days_cal=14, days_dep=40, cadence=600):
    text = EXAMPLE.read_text()
    text = text.replace('itinerary = [["cambridge", 14], ["greylock_summit", 80], ["cambridge", 80]]',
                        f'itinerary = [["cambridge", {days_cal}], ["greylock_summit", {days_dep}], ["cambridge", {days_cal}]]')
    text = text.replace('itinerary = [["cambridge", 94], ["greylock_summit", 80], ["cambridge", 14]]',
                        f'itinerary = [["cambridge", {days_cal + days_dep + days_cal}]]')
    text = text.replace("cadence_s = 60", f"cadence_s = {cadence}")
    p = tmp_path / "station.toml"
    p.write_text(text)
    return config.load(p)


def test_simulated_season_recovers_the_rate(tmp_path):
    cfg = _write_cfg(tmp_path)
    sim.run(cfg, quiet=True)
    result = analysis.analyse(cfg)
    assert result["ok"]
    s = result["summary"]
    assert s is not None
    pred = s["predicted_ns_day"]
    assert abs(pred - 9.96) < 0.05
    # recovered within 3σ of its own error bar, and the error bar is sub-ns/day
    assert abs(s["measured_ns_day"] - pred) < 3 * math.hypot(s["measured_sigma"], s["predicted_sigma"]) + 0.3
    assert s["measured_sigma"] < 1.0
    assert s["detection_sigma"] > 8
    # the clock's intrinsic offset (1.2e-13 = 10.4 ns/day) was calibrated away, not mistaken for gravity
    cal = result["clocks"]["CS1"]["calibration"]
    assert abs(cal["rate_ns_day"] - 1.2e-13 * 86400e9) < 1.5
    # lead accumulated over the deployment is about rate × days
    assert abs(s["lead_total_ns"] - pred * 39) < 60
    text = analysis.report(result)
    assert "combined" in text


def test_uncalibrated_clock_is_reported_not_guessed(tmp_path):
    cfg = _write_cfg(tmp_path, days_cal=2, days_dep=10)
    sim.run(cfg, quiet=True)
    result = analysis.analyse(cfg)
    assert result["ok"]
    assert result["clocks"]["CS1"]["calibration"] is None
    assert result["summary"] is None
    assert any("no calibration" in n for d in result["deployments"] for n in d["notes"])


def test_adev_white_fm_slope():
    import numpy as np

    rng = np.random.default_rng(0)
    tau0 = 1.0
    x = np.cumsum(rng.normal(0, 5e-12, 20000)) * 1e9  # white FM phase walk, ns
    out = analysis.adev(x, tau0, taus=[1, 10, 100])
    sig = dict(out)
    assert 3e-12 < sig[1] < 7e-12
    assert sig[100] < sig[1] / 5   # falls as τ^-1/2
