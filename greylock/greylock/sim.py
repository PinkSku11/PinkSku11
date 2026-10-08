"""The digital twin: generates the same ledger records the real stations will,
from the noise models in clockmodel.py and the physics in physics.py.

A simulation is a set of clocks, each with an itinerary of (site, days).  Every
clock is measured against GPS time wherever it is, by a TICC fed from its own
10 MHz, exactly as in the real machine; the record goes into the ledger of the
station (site) it is at.  So a season with two clocks and one swap produces a
'cambridge' ledger and a 'greylock_summit' ledger that the analysis reads just
as it would read the real ones.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

import numpy as np

from .clockmodel import CesiumModel, EnvironmentModel, GnssPpsModel
from .config import Config
from .ledger import Ledger
from .physics import gravitational_rate


def _parse_time(s: str) -> float:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def run(cfg: Config, out_dir=None, cadence_s: float | None = None, quiet: bool = False) -> dict:
    sim = cfg.sim
    if not sim:
        raise ValueError("config has no [sim] section")
    start = _parse_time(sim.get("start", "2027-05-23T00:00:00Z"))
    cadence = float(cadence_s or sim.get("cadence_s", 60))
    out_dir = out_dir or cfg.ledger_dir
    reference = cfg.reference

    # one GNSS receiver and one environment per site
    receivers = {name: GnssPpsModel(seed=100 + i) for i, name in enumerate(cfg.sites)}
    envs = {}
    for i, (name, site) in enumerate(cfg.sites.items()):
        outside = 15.0 - 0.0065 * site.height_m * 1.0  # crude lapse rate
        envs[name] = EnvironmentModel(outside_mean_c=outside, pressure_hpa=1013.0 * math.exp(-site.height_m / 8400.0), seed=200 + i)
    ledgers = {name: Ledger(out_dir, name) for name in cfg.sites}

    clocks = {}
    itineraries = {}
    for i, (cname, c) in enumerate(sim.get("clocks", {}).items()):
        clocks[cname] = CesiumModel(
            name=cname,
            intrinsic_offset=float(c.get("intrinsic_offset", 1e-13)),
            sigma_y_1s=float(c.get("sigma_y_1s", 5e-12)),
            floor=float(c.get("floor", 5e-15)),
            temp_coeff_per_c=float(c.get("temp_coeff_per_c", 2e-15)),
            seed=300 + i,
        )
        # expand itinerary into (t_start, t_end, site)
        t = start
        segs = []
        for site_name, days in c["itinerary"]:
            segs.append((t, t + float(days) * 86400.0, site_name))
            t += float(days) * 86400.0
        itineraries[cname] = segs

    t_end = max(seg[-1][1] for seg in itineraries.values())
    n_steps = int(round((t_end - start) / cadence))
    counts = {name: 0 for name in cfg.sites}
    qerr_sign = int(cfg.hardware.get("qerr_sign", 1))

    def site_of(cname: str, t: float):
        for a, b, s in itineraries[cname]:
            if a <= t < b:
                return s
        return None

    for k in range(n_steps):
        t = start + k * cadence
        for cname, clock in clocks.items():
            sname = site_of(cname, t)
            if sname is None:
                continue
            site = cfg.site(sname)
            temp_c, outside_c, press = envs[sname].sample(t)
            grav = gravitational_rate(site, reference)
            x_cs = clock.step(cadence, grav, temp_c)
            pps_err, qerr_ps = receivers[sname].step(cadence)
            ti_ns = (x_cs - pps_err) * 1e9
            rec = {
                "t": round(t, 3),
                "site": sname,
                "clock": cname,
                "ti_ns": round(ti_ns, 3),
                "qerr_ps": round(qerr_sign * qerr_ps, 1),   # as the receiver would report it
                "temp_c": round(temp_c, 2),
                "outside_c": round(outside_c, 1),
                "press_hpa": round(press, 1),
                "fix": 3,
                "num_sv": 14,
                "on_battery": False,
                "source": "sim",
            }
            ledgers[sname].append(rec)
            counts[sname] += 1
        if not quiet and k % max(1, n_steps // 10) == 0:
            print(f"  sim {100 * k // n_steps:3d}%  {datetime.fromtimestamp(t, tz=timezone.utc):%Y-%m-%d}")
    for lg in ledgers.values():
        lg.close()
    return {"records": counts, "start": start, "end": t_end, "cadence_s": cadence, "ledger_dir": str(out_dir)}
