"""export / reportgen / passport / transport / rinex on a small simulated run."""
import csv
import math
from pathlib import Path

import pytest

from greylock import analysis, config, export, passport, physics, reportgen, rinex, sim
from greylock.ledger import Ledger

EXAMPLE = Path(__file__).parent.parent / "station.example.toml"


@pytest.fixture(scope="module")
def season(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("season")
    text = EXAMPLE.read_text()
    text = text.replace('itinerary = [["cambridge", 14], ["greylock_summit", 80], ["cambridge", 80]]',
                        'itinerary = [["cambridge", 6], ["greylock_summit", 10], ["cambridge", 6]]')
    text = text.replace('itinerary = [["cambridge", 94], ["greylock_summit", 80], ["cambridge", 14]]',
                        'itinerary = [["cambridge", 22]]')
    text = text.replace("cadence_s = 60", "cadence_s = 3600")
    p = tmp / "station.toml"
    p.write_text(text)
    cfg = config.load(p)
    sim.run(cfg, quiet=True)
    return cfg, analysis.analyse(cfg)


def _rows(path):
    with open(path, newline="") as fh:
        return list(csv.reader(fh))


def test_exports(season, tmp_path):
    cfg, result = season
    n = export.export_daily(cfg, tmp_path / "daily.csv")
    rows = _rows(tmp_path / "daily.csv")
    assert rows[0][:3] == ["clock", "site", "date"]
    assert n == len(rows) - 1 > 20

    n = export.export_lead(result, tmp_path / "lead.csv")
    assert n == len(_rows(tmp_path / "lead.csv")) - 1 > 5

    n = export.export_segments(result, tmp_path / "segments.csv")
    rows = _rows(tmp_path / "segments.csv")
    assert n == len(rows) - 1 >= 4            # CS1: cal+dep+cal, CS2: cal
    assert "temp_coeff_ns_per_c" in rows[0]

    n = export.export_raw(cfg, tmp_path / "raw.csv", clock="CS1")
    assert n > 400                            # 22 days of hourly records


def test_report_and_post(season):
    cfg, result = season
    text = reportgen.daily_report(cfg, day="2027-05-24", result=result)
    assert "cambridge" in text and "chain cambridge: OK" in text
    assert "commitment" in text or "records" in text
    post = reportgen.post_text(cfg, day="2027-06-05", result=result)
    assert "Greylock Time Machine" in post and "ns" in post
    assert len(post) < 300


def test_passport_math(season):
    cfg, _ = season
    cert = passport.certificate(cfg, "greylock_summit",
                                "2027-07-01T12:00Z", "2027-07-03T12:00Z", name="Shriya")
    assert abs(cert["banked_ns"] - 2 * 9.96) < 0.1       # 48 h at ~9.96 ns/day
    assert cert["banked_light_mm"] == pytest.approx(cert["banked_ns"] * 299.792458, rel=1e-6)
    text = passport.text(cert)
    assert "Shriya" in text and "nanoseconds" in text
    page = passport.html(cert)
    assert "CERTIFICATE" in page and f"{cert['banked_ns']:.3f}" in page
    with pytest.raises(ValueError):
        passport.certificate(cfg, "greylock_summit", "2027-07-02T12:00Z", "2027-07-01T12:00Z")


def test_transport_from_ledger(tmp_path):
    # a 3 h drive from 6 m to 1063 m at 20 m/s, logged the way acquire.py logs it
    text = EXAMPLE.read_text().replace('ledger_dir = "data/ledger"',
                                       f'ledger_dir = "{tmp_path.as_posix()}/led"')
    p = tmp_path / "station.toml"
    p.write_text(text)
    cfg = config.load(p)
    led = Ledger(cfg.ledger_dir, "drive")
    t0, n = 1_800_000_000.0, 181
    track = []
    for i in range(n):
        t = t0 + i * 60.0
        h = 6.0 + (1063.0 - 6.0) * i / (n - 1)
        led.append({"t": t, "site": "greylock_summit", "clock": "CS1", "ti_ns": 0.0,
                    "h_msl": round(h, 1), "g_speed": 20.0, "lat": 42.5, "vel_e": 10.0})
        track.append((t, 42.5, h, 20.0, 10.0))
    led.close()
    out = export.transport_report(cfg, station="drive")
    assert out["ok"] and out["n"] == n
    direct = physics.transport_offset_ns(track, cfg.reference)
    assert out["offset_ns"] == pytest.approx(direct, abs=1e-6)
    assert 0.1 < out["offset_ns"] < 0.6       # the design note's ~0.35 ns drive leg


def test_transport_refuses_interleaved_stations(tmp_path):
    # both stations' ledgers in one directory (the normal analysis layout) must
    # not be read as one non-monotonic track (review finding)
    text = EXAMPLE.read_text().replace('ledger_dir = "data/ledger"',
                                       f'ledger_dir = "{tmp_path.as_posix()}/led"')
    p = tmp_path / "station.toml"
    p.write_text(text)
    cfg = config.load(p)
    for station, h in (("a_station", 6.0), ("b_station", 1063.0)):
        led = Ledger(cfg.ledger_dir, station)
        for i in range(5):
            led.append({"t": 1_800_000_000.0 + i * 60.0, "site": "cambridge", "clock": "CS1",
                        "ti_ns": 0.0, "h_msl": h, "g_speed": 0.0})
        led.close()
    out = export.transport_report(cfg)
    assert not out["ok"] and "--station" in out["error"]
    assert export.transport_report(cfg, station="a_station")["ok"]


def test_report_survives_stale_heartbeat(season):
    # a status file written during a TICC outage holds last_ti_ns: null — the
    # report (and /api/report) must render, not crash (review finding)
    cfg, result = season
    status = cfg.ledger_dir / "greylock_summit-status.json"
    status.write_text('{"t": 1800000000.0, "records": 5, "last_ti_ns": null, '
                      '"errors": ["no pulse for > 15 s"], "site": "greylock_summit", "clock": "CS1"}')
    try:
        text = reportgen.daily_report(cfg, day="2027-06-05", result=result)
        assert "n/a (stale)" in text
    finally:
        status.unlink()


def test_rinex_graceful_without_convbin(tmp_path):
    text = EXAMPLE.read_text().replace('ledger_dir = "data/ledger"',
                                       f'ledger_dir = "{tmp_path.as_posix()}/led"')
    p = tmp_path / "station.toml"
    p.write_text(text)
    cfg = config.load(p)
    out = rinex.convert_all(cfg)
    assert not out[0]["ok"] and "no raw UBX" in out[0]["error"]

    ubx = cfg.ledger_dir / "ubx"
    ubx.mkdir(parents=True)
    (ubx / "ubx-2027-06-01.bin").write_bytes(b"\xb5\x62")
    out = rinex.convert_all(cfg, convbin="definitely-not-a-real-binary")
    assert not out[0]["ok"] and "not found" in out[0]["error"]
