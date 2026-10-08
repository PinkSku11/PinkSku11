"""`greylock report` — the daily operations report, and the one-line public post.

The report is what the operator reads with coffee: did both stations run all
night, how noisy was the link, did the thermostat hold, is the chain intact,
what is the lead this morning.  Plain text, written to stdout or a file, cron-
friendly.  `post_text()` is the ≤ 280-character version with the day's
commitment hash — the X bot's payload, generated even before the bot exists.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from . import analysis
from .config import Config
from .ledger import commitments, iter_records, verify

DAY = 86400.0


def _day_str(t: float) -> str:
    return datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d")


def station_day_stats(cfg: Config, station: str, day: str) -> dict | None:
    """Record counts, gaps, ti scatter, qErr, temperature for one station-day."""
    ts, tis, qs, temps, bats = [], [], [], [], 0
    fixes, svs = [], []
    for rec in iter_records(cfg.ledger_dir, station):
        if _day_str(float(rec["t"])) != day:
            continue
        ts.append(float(rec["t"]))
        if "ti_ns" in rec:
            tis.append(float(rec["ti_ns"]) +
                       int(cfg.hardware.get("qerr_sign", 1)) * float(rec.get("qerr_ps", 0)) / 1e3)
            qs.append(float(rec.get("qerr_ps", 0.0)))
        if rec.get("temp_c") is not None:
            temps.append(float(rec["temp_c"]))
        if rec.get("on_battery"):
            bats += 1
        if rec.get("fix") is not None:
            fixes.append(int(rec["fix"]))
            svs.append(int(rec.get("num_sv", 0)))
    if not ts:
        return None
    ts.sort()
    gaps = [b - a for a, b in zip(ts, ts[1:]) if b - a > 5.0]
    out = {"records": len(ts), "first": ts[0], "last": ts[-1],
           "gaps_over_5s": len(gaps), "longest_gap_s": max(gaps) if gaps else 0.0,
           "battery_records": bats}
    if tis:
        med = float(np.median(tis))
        out["ti_median_ns"] = med
        out["ti_mad_ns"] = float(np.median(np.abs(np.array(tis) - med))) * 1.4826
    if qs:
        out["qerr_rms_ps"] = float(np.sqrt(np.mean(np.square(qs))))
    if temps:
        out["temp_min_c"], out["temp_max_c"] = float(min(temps)), float(max(temps))
    if fixes:
        out["fix_bad"] = sum(1 for f in fixes if f < 3)
        out["num_sv_min"] = min(svs)
    return out


def _read_status(cfg: Config) -> dict:
    out = {}
    for p in cfg.ledger_dir.glob("*-status.json"):
        try:
            out[p.stem.replace("-status", "")] = json.loads(p.read_text())
        except Exception:
            pass
    return out


def daily_report(cfg: Config, day: str | None = None, result: dict | None = None) -> str:
    day = day or _day_str(time.time() - DAY)        # default: yesterday (a closed day)
    result = result or analysis.analyse(cfg)
    lines = [f"greylock daily report — {day} (UTC)", "=" * 44]

    for name in cfg.sites:
        st = station_day_stats(cfg, name, day)
        if st is None:
            lines.append(f"{name}: no records")
            continue
        bits = [f"{st['records']} records",
                f"{st['gaps_over_5s']} gaps >5 s" +
                (f" (longest {st['longest_gap_s']:.0f} s)" if st["gaps_over_5s"] else "")]
        if "ti_mad_ns" in st:
            bits.append(f"ti {st['ti_median_ns']:+.1f} ns ± {st['ti_mad_ns']:.1f} (MAD)")
        if "qerr_rms_ps" in st:
            bits.append(f"qErr rms {st['qerr_rms_ps']:.0f} ps")
        if "temp_min_c" in st:
            bits.append(f"case {st['temp_min_c']:.1f}–{st['temp_max_c']:.1f} °C")
        if st["battery_records"]:
            bits.append(f"ON BATTERY for {st['battery_records']} records")
        if st.get("fix_bad"):
            bits.append(f"{st['fix_bad']} records without 3D fix")
        lines.append(f"{name}: " + ", ".join(bits))

    lines.append("")
    for name in cfg.sites:
        if any(cfg.ledger_dir.glob(f"{name}-*.jsonl")):
            ok, msg = verify(cfg.ledger_dir, name)
            lines.append(f"chain {name}: {'OK' if ok else 'BROKEN'} — {msg}")
            com = [c for c in commitments(cfg.ledger_dir, name) if c[0] == day]
            if com:
                lines.append(f"commitment {name} {day}: {com[0][1]}  ({com[0][2]} records)")

    hb = _read_status(cfg)
    if hb:
        lines.append("")
        for name, s in sorted(hb.items()):
            age = time.time() - float(s.get("t", 0))
            lines.append(f"heartbeat {name}: {age:.0f} s ago, last ti {s.get('last_ti_ns', float('nan')):.1f} ns"
                         + (f", errors: {'; '.join(s['errors'])}" if s.get("errors") else ""))

    lines.append("")
    lines.append(analysis.report(result))
    return "\n".join(lines)


def post_text(cfg: Config, day: str | None = None, result: dict | None = None) -> str:
    """The public one-liner: lead, prediction, and the day's commitment hash."""
    day = day or _day_str(time.time() - DAY)
    result = result or analysis.analyse(cfg)
    s = result.get("summary")
    com_hash = ""
    for name in cfg.sites:
        if not cfg.sites[name].reference:
            com = [c for c in commitments(cfg.ledger_dir, name) if c[0] == day]
            if com:
                com_hash = com[0][1]
                break
    if s:
        txt = (f"Greylock Time Machine, {day}: the summit clock leads sea level by "
               f"{s['lead_total_ns']:,.0f} ns (predicted {s['predicted_lead_ns']:,.0f}). "
               f"Rate {s['measured_ns_day']:+.2f} ± {s['measured_sigma']:.2f} ns/day vs "
               f"gΔh/c² = {s['predicted_ns_day']:+.2f}.")
    else:
        txt = f"Greylock Time Machine, {day}: calibrating."
    if com_hash:
        txt += f" Ledger {com_hash[:16]}…"
    return txt
