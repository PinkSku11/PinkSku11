"""From ledger records to a number with an error bar.

Pipeline
  1. load every record of every station ledger (real or simulated)
  2. remove the GNSS sawtooth:  ti += qerr_sign · qErr
  3. daily means per (clock, site): median and a robust σ, so a bad hour
     cannot drag a day
  4. split each clock's history into contiguous segments at one site
  5. for each clock, the *calibration* segments (at the reference site) give the
     clock's own rate against GPS time: slope_ref  [ns/day]
  6. each *deployment* segment gives slope_site; the measured gravitational
     rate difference is  slope_site − slope_ref, with the two fit errors in
     quadrature; the prediction is physics.gravitational_rate(site, reference)
  7. the lead series — the number on the display — is the deployment data with
     the clock's own rate removed, accumulated across segments and swaps

Everything is weighted least squares on daily means; no model is fitted beyond a
straight line, because a straight line is the entire claim.
"""
from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .config import Config
from .ledger import commitments, iter_records
from .physics import gravitational_rate, gravitational_rate_sigma, light_metres, rate_to_ns_per_day

DAY = 86400.0


@dataclass
class DailyPoint:
    day: float            # days since epoch0 (mean time of the records in the bin)
    date: str             # UTC date
    ti_ns: float          # robust daily mean of corrected ti
    sigma_ns: float       # robust σ of the mean
    n: int
    temp_c: float
    on_battery_any: bool
    n_rejected: int = 0   # per-pulse outliers clipped before the daily statistics


@dataclass
class Segment:
    clock: str
    site: str
    start_date: str
    end_date: str
    points: list = field(default_factory=list)   # DailyPoint
    slope_ns_day: float = float("nan")
    slope_err: float = float("nan")
    intercept_ns: float = float("nan")
    rms_resid_ns: float = float("nan")
    temp_coeff_ns_per_c: float = float("nan")   # residuals vs case temperature
    temp_coeff_err: float = float("nan")
    n_days: int = 0
    valid: bool = True
    notes: list = field(default_factory=list)


def fit_line(x: np.ndarray, y: np.ndarray, w: np.ndarray | None = None):
    """Weighted least squares y = a + b x.  Returns (a, b, σ_b, rms) with σ_b scaled by
    the residual scatter (so an optimistic per-point σ cannot make the error bar lie)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if w is None:
        w = np.ones_like(x)
    W = np.sum(w)
    xm = np.sum(w * x) / W
    ym = np.sum(w * y) / W
    sxx = np.sum(w * (x - xm) ** 2)
    if sxx <= 0 or len(x) < 3:
        return ym, float("nan"), float("nan"), float("nan")
    b = np.sum(w * (x - xm) * (y - ym)) / sxx
    a = ym - b * xm
    resid = y - (a + b * x)
    dof = max(len(x) - 2, 1)
    s2 = np.sum(w * resid ** 2) / dof          # weighted residual variance
    sigma_b = math.sqrt(s2 / sxx)
    rms = math.sqrt(np.mean(resid ** 2))
    return float(a), float(b), float(sigma_b), float(rms)


def load(cfg: Config, ledger_dir=None):
    """Return dict clock -> list of record dicts (sorted by t), after sawtooth correction."""
    d = Path(ledger_dir or cfg.ledger_dir)
    qerr_sign = int(cfg.hardware.get("qerr_sign", 1))
    by_clock: dict[str, list] = defaultdict(list)
    for rec in iter_records(d):
        if "ti_ns" not in rec:
            continue  # health / event records
        ti = float(rec["ti_ns"]) + qerr_sign * float(rec.get("qerr_ps", 0.0)) / 1000.0
        tv = rec.get("temp_c")   # hardware without a BME280 writes null, not a number
        by_clock[rec["clock"]].append((float(rec["t"]), rec["site"], ti,
                                       float(tv) if tv is not None else float("nan"),
                                       bool(rec.get("on_battery", False))))
    for k in by_clock:
        by_clock[k].sort(key=lambda r: r[0])
    return by_clock


def daily_points(records, epoch0: float) -> list[DailyPoint]:
    bins: dict[int, list] = defaultdict(list)
    for t, site, ti, temp, bat in records:
        bins[int(t // DAY)].append((t, ti, temp, bat))
    out = []
    for b in sorted(bins):
        arr = np.array([(t, ti, temp) for t, ti, temp, _ in bins[b]], float)
        bat = any(x[3] for x in bins[b])
        t = arr[:, 0]
        ti = arr[:, 1]
        med = float(np.median(ti))
        mad = float(np.median(np.abs(ti - med))) * 1.4826
        # clip gross per-pulse outliers (glitched serial lines, pulse pairing slips)
        # before the daily statistics; the clip is wide (7 robust σ) so real link
        # noise is untouched, and the count is recorded, never hidden
        n_rej = 0
        if mad > 0:
            keep = np.abs(ti - med) <= 7.0 * mad
            n_rej = int(np.sum(~keep))
            if n_rej:
                t, ti = t[keep], ti[keep]
                med = float(np.median(ti))
                mad = float(np.median(np.abs(ti - med))) * 1.4826
        n = len(ti)
        # σ of the daily mean: robust scatter / √n, floored at a few hundred ps — the
        # link's own daily systematic is not visible inside one day, so the fit's
        # scaled covariance (fit_line) is what carries the real error bar.
        sigma = max(mad / math.sqrt(n), 0.3)
        date = datetime.fromtimestamp(float(np.mean(t)), tz=timezone.utc).strftime("%Y-%m-%d")
        out.append(DailyPoint((float(np.mean(t)) - epoch0) / DAY, date, med, sigma, n,
                              float(np.nanmean(arr[:, 2])), bat, n_rej))
    return out


def segments_for(clock: str, records, epoch0: float, gap_days: float = 1.5) -> list[Segment]:
    """Contiguous runs of one clock at one site."""
    segs: list[Segment] = []
    cur_site = None
    cur: list = []
    last_t = None
    for r in records:
        t, site = r[0], r[1]
        if site != cur_site or (last_t is not None and t - last_t > gap_days * DAY):
            if cur:
                segs.append(_make_segment(clock, cur_site, cur, epoch0))
            cur, cur_site = [], site
        cur.append(r)
        last_t = t
    if cur:
        segs.append(_make_segment(clock, cur_site, cur, epoch0))
    return segs


def _make_segment(clock, site, recs, epoch0) -> Segment:
    pts = daily_points(recs, epoch0)
    seg = Segment(clock=clock, site=site, start_date=pts[0].date, end_date=pts[-1].date, points=pts)
    seg.n_days = len(pts)
    if any(p.on_battery_any for p in pts):
        seg.notes.append("clock on internal battery at some point")
    n_rej = sum(p.n_rejected for p in pts)
    if n_rej:
        seg.notes.append(f"{n_rej} per-pulse outlier(s) clipped")
    if len(pts) >= 3:
        x = np.array([p.day for p in pts])
        y = np.array([p.ti_ns for p in pts])
        w = np.array([1.0 / p.sigma_ns ** 2 for p in pts])
        a, b, sb, rms = fit_line(x, y, w)
        seg.intercept_ns, seg.slope_ns_day, seg.slope_err, seg.rms_resid_ns = a, b, sb, rms
        resid = y - (a + b * x)
        # phase-step scan on the daily series: a jump that is far outside both the
        # absolute threshold and the series' own scatter is reported, not silently
        # averaged into the slope — a stepped segment needs a human decision
        d = np.diff(y)
        if len(d) >= 3:
            dmad = float(np.median(np.abs(d - np.median(d)))) * 1.4826
            thresh = max(30.0, 8.0 * dmad)
            for i in np.where(np.abs(d - np.median(d)) > thresh)[0]:
                seg.notes.append(f"possible phase step of {d[i]:+.1f} ns on {pts[i + 1].date}")
        # temperature diagnostic.  The straight-line fit absorbs any part of a thermal
        # term that is correlated with time, so regressing residuals on raw temperature
        # would understate the coefficient; detrending temperature against time first
        # (Frisch–Waugh) recovers the joint-fit coefficient.  A temperature history
        # that is purely linear in time is fundamentally indistinguishable from clock
        # drift — that case is named, not silently reported as zero.
        temps = np.array([p.temp_c for p in pts])
        good = np.isfinite(temps)
        if int(np.sum(good)) >= 5 and float(np.ptp(temps[good])) > 0.2:
            swing = float(np.ptp(temps[good]))
            ta, tb, _, _ = fit_line(x[good], temps[good])
            tres = temps[good] - (ta + tb * x[good])
            if float(np.ptp(tres)) > 0.1:
                _, tc, tc_err, _ = fit_line(tres, resid[good])
                seg.temp_coeff_ns_per_c, seg.temp_coeff_err = tc, tc_err
                if math.isfinite(tc_err) and abs(tc) > 3 * tc_err and abs(tc) * swing > 0.5:
                    seg.notes.append(f"temperature-correlated residuals: {tc:+.2f} ± {tc_err:.2f} ns/°C "
                                     f"over a {swing:.1f} °C swing — check the thermostat")
            else:
                seg.notes.append(f"case temperature drifted almost linearly with time "
                                 f"({swing:.1f} °C over the segment) — a thermal term is "
                                 f"indistinguishable from clock drift here")
    else:
        seg.valid = False
        seg.notes.append("fewer than 3 days: no rate fit")
    return seg


def analyse(cfg: Config, ledger_dir=None) -> dict:
    by_clock = load(cfg, ledger_dir)
    if not by_clock:
        return {"ok": False, "error": "no measurement records found"}
    epoch0 = min(r[0] for recs in by_clock.values() for r in recs)
    ref = cfg.reference
    min_cal_days = int(cfg.analysis.get("min_calibration_days", 5))

    # a per-clock systematic floor: the clock's own slow frequency wander (flicker floor),
    # spec-level 5e-15 for a high-performance tube ≈ 0.43 ns/day; override in [analysis]
    floor_ns_day = rate_to_ns_per_day(float(cfg.analysis.get("clock_floor", 5e-15)))

    result = {"ok": True, "reference_site": ref.name, "clocks": {}, "deployments": [],
              "clock_floor_ns_day": floor_ns_day,
              "lead": {"days": [], "dates": [], "lead_ns": [], "predicted_ns": []}}
    lead_total = 0.0
    pred_total = 0.0
    lead_days, lead_dates, lead_vals, pred_vals = [], [], [], []

    all_segments = []
    for clock, recs in by_clock.items():
        segs = segments_for(clock, recs, epoch0)
        all_segments.append((clock, segs))

    # 1. calibration: each clock's rate against GPS time at the reference site
    cal = {}
    for clock, segs in all_segments:
        cal_segs = [s for s in segs if s.site == ref.name and s.valid and s.n_days >= min_cal_days]
        if cal_segs:
            w = np.array([1.0 / s.slope_err ** 2 for s in cal_segs])
            slopes = np.array([s.slope_ns_day for s in cal_segs])
            m = float(np.sum(w * slopes) / np.sum(w))
            err_fit = float(1.0 / math.sqrt(np.sum(w)))
            spread = float(np.max(slopes) - np.min(slopes)) if len(slopes) > 1 else 0.0
            # honest error: fit error, half the before/after disagreement, and the clock's floor
            err = math.hypot(err_fit, 0.5 * spread, floor_ns_day)
            cal[clock] = {"rate_ns_day": m, "err": err, "err_fit": err_fit, "segments": len(cal_segs),
                          "before_after_spread_ns_day": spread}
        else:
            cal[clock] = None
        result["clocks"][clock] = {
            "calibration": cal[clock],
            "segments": [{k: v for k, v in asdict(s).items() if k != "points"} for s in segs],
        }

    # 2. deployments, in time order across clocks
    deployments = []
    for clock, segs in all_segments:
        for s in segs:
            if s.site != ref.name:
                deployments.append((s.points[0].day, clock, s))
    deployments.sort(key=lambda d: d[0])

    for _, clock, s in deployments:
        site = cfg.site(s.site)
        pred = rate_to_ns_per_day(gravitational_rate(site, ref))
        pred_sig = rate_to_ns_per_day(gravitational_rate_sigma(site, ref))
        entry = {"clock": clock, "site": s.site, "start": s.start_date, "end": s.end_date, "days": s.n_days,
                 "predicted_ns_day": pred, "predicted_sigma": pred_sig, "notes": list(s.notes)}
        c = cal.get(clock)
        if c is None or not s.valid:
            entry["measured_ns_day"] = None
            entry["notes"].append("no calibration for this clock yet" if c is None else "segment too short")
        else:
            meas = s.slope_ns_day - c["rate_ns_day"]
            # fit error of this segment, the calibration error, and the clock floor again
            # (the deployment is a separate realisation of the clock's slow wander)
            err = math.hypot(s.slope_err, c["err"], floor_ns_day)
            entry.update({"measured_ns_day": meas, "measured_sigma": err,
                          "sigma_from_prediction": (meas - pred) / math.hypot(err, pred_sig),
                          "fit_rms_ns": s.rms_resid_ns})
            # lead series: clock's own rate removed, accumulated across segments
            p0 = s.points[0]
            for p in s.points:
                dt = p.day - p0.day
                lead = lead_total + (p.ti_ns - p0.ti_ns) - c["rate_ns_day"] * dt
                lead_days.append(p.day)
                lead_dates.append(p.date)
                lead_vals.append(lead)
                pred_vals.append(pred_total + pred * dt)
            last = s.points[-1]
            lead_total += (last.ti_ns - p0.ti_ns) - c["rate_ns_day"] * (last.day - p0.day)
            pred_total += pred * (last.day - p0.day)
        result["deployments"].append(entry)

    result["lead"] = {"days": lead_days, "dates": lead_dates, "lead_ns": lead_vals, "predicted_ns": pred_vals}
    # 3. the combined answer: weighted mean of all measured deployments
    meas = [(d["measured_ns_day"], d["measured_sigma"], d["predicted_ns_day"], d["predicted_sigma"])
            for d in result["deployments"] if d.get("measured_ns_day") is not None]
    if meas:
        w = np.array([1 / m[1] ** 2 for m in meas])
        rate = float(np.sum(w * np.array([m[0] for m in meas])) / np.sum(w))
        err = float(1 / math.sqrt(np.sum(w)))
        pred = float(np.mean([m[2] for m in meas]))
        pred_sig = float(np.mean([m[3] for m in meas]))
        result["summary"] = {
            "measured_ns_day": rate, "measured_sigma": err,
            "predicted_ns_day": pred, "predicted_sigma": pred_sig,
            "sigma_from_prediction": (rate - pred) / math.hypot(err, pred_sig),
            "detection_sigma": rate / err if err > 0 else None,
            "lead_total_ns": lead_total, "predicted_lead_ns": pred_total,
            "lead_light_metres": light_metres(lead_total),
            "deployment_days": sum(d["days"] for d in result["deployments"]),
        }
    else:
        result["summary"] = None
    # 4. ledger commitments (last hash per day per station) for the record
    d = Path(ledger_dir or cfg.ledger_dir)
    result["commitments"] = {name: commitments(d, name)[-3:] for name in cfg.sites if (d / f"{name}-commitments.txt").exists() or any(d.glob(f"{name}-*.jsonl"))}
    return result


def adev(ti_ns: np.ndarray, tau0_s: float, taus: list[float] | None = None) -> list[tuple[float, float]]:
    """Overlapping Allan deviation of a phase series (ns) sampled every tau0_s."""
    x = np.asarray(ti_ns, float) * 1e-9
    n = len(x)
    if taus is None:
        taus = [tau0_s * 2 ** k for k in range(0, 40) if tau0_s * 2 ** k < n * tau0_s / 3]
    out = []
    for tau in taus:
        m = int(round(tau / tau0_s))
        if m < 1 or 2 * m >= n:
            continue
        d2 = x[2 * m:] - 2 * x[m:-m] + x[:-2 * m]
        sigma = math.sqrt(np.mean(d2 ** 2) / (2 * tau * tau))
        out.append((tau, sigma))
    return out


def write_state(result: dict, path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1, default=float)
    return path


def report(result: dict) -> str:
    if not result.get("ok"):
        return f"analysis failed: {result.get('error')}"
    lines = []
    lines.append(f"reference site: {result['reference_site']}")
    for clock, info in result["clocks"].items():
        c = info["calibration"]
        if c:
            lines.append(f"{clock}: own rate vs GPS time {c['rate_ns_day']:+.2f} ± {c['err']:.2f} ns/day "
                         f"from {c['segments']} calibration segment(s), before/after spread {c['before_after_spread_ns_day']:.2f} ns/day")
        else:
            lines.append(f"{clock}: not calibrated (no segment of ≥ min_calibration_days at the reference site)")
    for d in result["deployments"]:
        if d.get("measured_ns_day") is None:
            lines.append(f"  {d['clock']} at {d['site']} {d['start']}→{d['end']} ({d['days']} d): {', '.join(d['notes'])}")
        else:
            lines.append(f"  {d['clock']} at {d['site']} {d['start']}→{d['end']} ({d['days']} d): "
                         f"measured {d['measured_ns_day']:+.2f} ± {d['measured_sigma']:.2f} ns/day, "
                         f"predicted {d['predicted_ns_day']:+.2f} ± {d['predicted_sigma']:.2f}, "
                         f"difference {d['sigma_from_prediction']:+.1f}σ, fit rms {d['fit_rms_ns']:.1f} ns"
                         + (f"  [{'; '.join(d['notes'])}]" if d['notes'] else ""))
    s = result.get("summary")
    if s:
        lines.append(f"combined: {s['measured_ns_day']:+.2f} ± {s['measured_sigma']:.2f} ns/day vs predicted "
                     f"{s['predicted_ns_day']:+.2f} ± {s['predicted_sigma']:.2f} ({s['sigma_from_prediction']:+.1f}σ); "
                     f"detection {s['detection_sigma']:.0f}σ over {s['deployment_days']} deployment days")
        lines.append(f"accumulated lead: {s['lead_total_ns']:.0f} ns measured, {s['predicted_lead_ns']:.0f} ns predicted "
                     f"({s['lead_light_metres']:.0f} m of light)")
    return "\n".join(lines)
