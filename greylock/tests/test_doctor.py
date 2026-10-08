from pathlib import Path

import numpy as np
import pytest

from greylock import config, doctor

EXAMPLE = Path(__file__).parent.parent / "station.example.toml"


def _synth_ti(n=2000, sign=+1, seed=7):
    """A ti series whose sawtooth is removed by qerr_sign = `sign` (the sim's convention:
    the pulse error subtracts from ti and the receiver reports it as qErr)."""
    rng = np.random.default_rng(seed)
    saw = rng.uniform(-4.0, 4.0, n)
    ti = 0.01 * np.arange(n) + rng.normal(0.0, 0.5, n) - sign * saw
    return ti, saw * 1000.0  # qErr in ps


def test_zero_baseline_finds_the_sign():
    ti, q = _synth_ti(sign=+1)
    out = doctor.zero_baseline(ti, q)
    assert out["recommend"] == 1
    assert out["jitter_plus_ns"] < out["jitter_uncorrected_ns"]
    ti, q = _synth_ti(sign=-1)
    assert doctor.zero_baseline(ti, q)["recommend"] == -1


def test_zero_baseline_groups_prevent_cross_clock_swamping():
    # two clocks ~1 ms apart: pooled first-differences would bury the sawtooth
    # (review finding); within-group differences recover the sign cleanly
    ti1, q1 = _synth_ti(sign=+1, seed=11)
    ti2, q2 = _synth_ti(sign=+1, seed=12)
    ti = np.concatenate([ti1, ti2 + 1e6])
    q = np.concatenate([q1, q2])
    gids = np.concatenate([np.zeros(len(ti1)), np.ones(len(ti2))])
    assert doctor.zero_baseline(ti, q, group_ids=gids)["recommend"] == 1


def test_zero_baseline_inconclusive_on_zero_qerr():
    ti, _ = _synth_ti()
    out = doctor.zero_baseline(ti, np.zeros_like(ti))
    assert out["recommend"] == 0


def test_ti_sanity_flags_swapped_channels_and_steps():
    near_second = np.random.default_rng(1).normal(-1e9 + 120.0, 2.0, 50)
    notes = doctor.ti_sanity(near_second)
    assert any("swapped" in n for n in notes)

    stepped = np.concatenate([np.zeros(20), np.full(20, 100.0)])
    notes = doctor.ti_sanity(stepped + np.random.default_rng(2).normal(0, 1, 40))
    assert any("phase step" in n for n in notes)

    clean = np.random.default_rng(3).normal(50.0, 2.0, 50)
    assert doctor.ti_sanity(clean) == []


def test_check_config_good_and_bad(tmp_path):
    cfg = config.load(EXAMPLE)
    c = doctor.check_config(cfg)
    assert c.ok is True

    bad = EXAMPLE.read_text().replace("qerr_sign = 1", "qerr_sign = 2") \
                             .replace("height_m = 1063.4", "height_m = 99999")
    p = tmp_path / "bad.toml"
    p.write_text(bad)
    c = doctor.check_config(config.load(p))
    assert c.ok is False
    assert "qerr_sign" in c.detail and "height" in c.detail


def test_check_disk(tmp_path):
    c = doctor.check_disk(tmp_path, min_free_gb=0.0)
    assert c.ok is True and "GB free" in c.detail
    c = doctor.check_disk(tmp_path, min_free_gb=1e9)
    assert c.ok is False


def test_format_checks_counts_problems():
    checks = [doctor.Check("a", True, "fine"), doctor.Check("b", False, "broken"),
              doctor.Check("c", None, "skipped")]
    text = doctor.format_checks(checks)
    assert "FAIL" in text and "1 problem" in text
