"""CSV exports and ledger-derived series — the paper- and plot-friendly views.

Everything the analysis sees can leave the machine as a flat file:
    daily     one row per (clock, site, day): the points the fits run on
    lead      the display series: measured lead and prediction per day
    segments  one row per contiguous (clock, site) run with its fit
    raw       corrected per-pulse ti (big: a season at 1 Hz is ~14 M rows)
    track     (t, lat, h, speed, v_east) tuples from NAV-PVT fields in the
              ledger — the input to physics.transport_offset_ns for the drive
"""
from __future__ import annotations

import csv
import time
from pathlib import Path

from . import analysis
from .config import Config
from .ledger import iter_records
from .physics import Site, transport_offset_ns


def export_daily(cfg: Config, path) -> int:
    """One row per (clock, site, day).  Returns row count."""
    by_clock = analysis.load(cfg)
    epoch0 = min((r[0] for recs in by_clock.values() for r in recs), default=0.0)
    rows = 0
    with Path(path).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["clock", "site", "date", "day", "ti_ns", "sigma_ns", "n", "n_rejected",
                    "temp_c", "on_battery"])
        for clock, recs in sorted(by_clock.items()):
            for seg in analysis.segments_for(clock, recs, epoch0):
                for p in seg.points:
                    w.writerow([clock, seg.site, p.date, f"{p.day:.4f}", f"{p.ti_ns:.3f}",
                                f"{p.sigma_ns:.3f}", p.n, p.n_rejected,
                                "" if p.temp_c != p.temp_c else f"{p.temp_c:.2f}",
                                int(p.on_battery_any)])
                    rows += 1
    return rows


def export_lead(result: dict, path) -> int:
    lead = result.get("lead", {})
    days = lead.get("days", [])
    with Path(path).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["day", "date", "lead_ns", "predicted_ns"])
        for d, date, l, p in zip(days, lead["dates"], lead["lead_ns"], lead["predicted_ns"]):
            w.writerow([f"{d:.4f}", date, f"{l:.3f}", f"{p:.3f}"])
    return len(days)


def export_segments(result: dict, path) -> int:
    rows = 0
    with Path(path).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["clock", "site", "start", "end", "days", "slope_ns_day", "slope_err",
                    "rms_resid_ns", "temp_coeff_ns_per_c", "temp_coeff_err", "valid", "notes"])
        for clock, info in sorted(result.get("clocks", {}).items()):
            for s in info["segments"]:
                w.writerow([clock, s["site"], s["start_date"], s["end_date"], s["n_days"],
                            _f(s["slope_ns_day"]), _f(s["slope_err"]), _f(s["rms_resid_ns"]),
                            _f(s.get("temp_coeff_ns_per_c")), _f(s.get("temp_coeff_err")),
                            int(s["valid"]), "; ".join(s["notes"])])
                rows += 1
    return rows


def export_raw(cfg: Config, path, clock: str | None = None) -> int:
    """Corrected per-pulse ti.  Large; mostly for ADEV work off-station."""
    qerr_sign = int(cfg.hardware.get("qerr_sign", 1))
    rows = 0
    with Path(path).open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["t", "site", "clock", "ti_corrected_ns", "qerr_ps", "temp_c"])
        for rec in iter_records(cfg.ledger_dir):
            if "ti_ns" not in rec or (clock and rec.get("clock") != clock):
                continue
            ti = float(rec["ti_ns"]) + qerr_sign * float(rec.get("qerr_ps", 0.0)) / 1000.0
            w.writerow([rec["t"], rec["site"], rec["clock"], f"{ti:.3f}",
                        rec.get("qerr_ps", ""), rec.get("temp_c", "")])
            rows += 1
    return rows


def _f(v):
    if v is None:
        return ""
    try:
        return f"{float(v):.4f}"
    except (TypeError, ValueError):
        return ""


# --------------------------------------------------------------------------- transport
def track_from_ledger(cfg: Config, station: str | None = None,
                      t_start: float | None = None, t_end: float | None = None) -> list:
    """(t, lat, h, speed, v_east) samples from records that carry NAV-PVT fields.

    Records written by the acquisition daemon carry h_msl and g_speed, and (from
    v0.2) lat and vel_e.  Where lat/vel_e are missing (old records, simulations)
    the site's configured latitude and an eastward speed of zero are used — the
    Sagnac term of a drive is below 0.1 ns either way.
    """
    track = []
    for rec in iter_records(cfg.ledger_dir, station):
        if "ti_ns" not in rec or "h_msl" not in rec:
            continue
        t = float(rec["t"])
        if (t_start and t < t_start) or (t_end and t > t_end):
            continue
        site = cfg.sites.get(rec.get("site"))
        lat = float(rec.get("lat", site.lat_deg if site else 42.5))
        track.append((t, lat, float(rec["h_msl"]), float(rec.get("g_speed", 0.0)),
                      float(rec.get("vel_e", 0.0))))
    return track


def transport_report(cfg: Config, station: str | None = None,
                     t_start: float | None = None, t_end: float | None = None) -> dict:
    track = track_from_ledger(cfg, station, t_start, t_end)
    if len(track) < 2:
        return {"ok": False, "error": "fewer than 2 track samples with h_msl in the ledger",
                "n": len(track)}
    ns = transport_offset_ns(track, cfg.reference)
    dur_h = (track[-1][0] - track[0][0]) / 3600.0
    hs = [s[2] for s in track]
    return {"ok": True, "n": len(track), "hours": dur_h, "offset_ns": ns,
            "h_min_m": min(hs), "h_max_m": max(hs),
            "started": time.strftime("%Y-%m-%d %H:%M", time.gmtime(track[0][0])),
            "ended": time.strftime("%Y-%m-%d %H:%M", time.gmtime(track[-1][0]))}
