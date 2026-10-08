"""greylock — command line.

    greylock predict  station.toml                 the number to pre-register
    greylock simulate station.toml [--cadence 60]  write a simulated season into the ledger
    greylock acquire  station.toml [--simulate]    run a station (hardware, or a live twin)
    greylock analyse  station.toml [--json out]    rate, error bar, lead, verdict
    greylock verify   station.toml                 walk every ledger's hash chain
    greylock commit   station.toml                 write the daily commitment files
    greylock serve    station.toml [--port 8080]   the readout page
    greylock adev     station.toml --clock CS1     Allan deviation of a clock's ti series
    greylock init     station.toml                 write an example config

    greylock doctor   station.toml [--live]        bring-up self-test (config, disk, chrony,
                                                   ports; --live probes TICC/u-blox/5071A)
    greylock zerobase station.toml [--clock CS1]   decide qerr_sign from the data
    greylock export   station.toml --what daily    CSV: daily | lead | segments | raw
    greylock report   station.toml [--post]        daily operations report; --post = the
                                                   one-line public text with the commitment
    greylock passport station.toml --arrive ... --depart ...   a visitor's certificate
    greylock transport station.toml                the drive's proper-time integral from
                                                   the NAV-PVT track in the ledger
    greylock rinex    station.toml [--day D]       raw UBX → RINEX via RTKLIB convbin
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import analysis, config
from .physics import gravitational_rate, gravitational_rate_sigma, light_metres, rate_to_ns_per_day


def cmd_predict(cfg: config.Config, args):
    ref = cfg.reference
    print(f"reference: {ref.name} ({ref.height_m:.1f} m)")
    for name, site in cfg.sites.items():
        if site.reference:
            continue
        r = gravitational_rate(site, ref)
        s = gravitational_rate_sigma(site, ref)
        nd, sd = rate_to_ns_per_day(r), rate_to_ns_per_day(s)
        print(f"{name}: Δh = {site.height_m - ref.height_m:.1f} m  rate = {r:.4e}  = {nd:+.2f} ± {sd:.2f} ns/day"
              f"  ({nd * 7:.0f} ns/week, {nd * 30:.0f} ns/30 d, {light_metres(nd):.1f} m of light per day)")


def cmd_simulate(cfg: config.Config, args):
    from . import sim

    out = sim.run(cfg, cadence_s=args.cadence, quiet=args.quiet)
    print(json.dumps(out, indent=1))


def cmd_acquire(cfg: config.Config, args):
    from . import acquire

    n = acquire.run(cfg, simulate=args.simulate, max_records=args.max_records)
    print(f"{n} records written")


def cmd_analyse(cfg: config.Config, args):
    result = analysis.analyse(cfg)
    print(analysis.report(result))
    if args.json:
        p = analysis.write_state(result, args.json)
        print(f"state written to {p}")
    if args.plot:
        _plot(result, args.plot)


def _plot(result: dict, path: str):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; skipping plot")
        return
    lead = result.get("lead", {})
    if not lead.get("days"):
        print("nothing to plot yet")
        return
    d = [x - lead["days"][0] for x in lead["days"]]
    fig, ax = plt.subplots(figsize=(9, 4.5), dpi=140)
    ax.plot(d, lead["predicted_ns"], color="#eb6834", lw=2, label="prediction gΔh/c²")
    ax.plot(d, lead["lead_ns"], "o", ms=3, color="#2a78d6", label="measured daily lead")
    ax.axhline(0, color="#c3c2b7", lw=1, ls="--")
    ax.set_xlabel("days since first deployment day")
    ax.set_ylabel("summit lead over sea-level time (ns)")
    ax.legend(frameon=False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    print(f"plot written to {path}")


def cmd_verify(cfg: config.Config, args):
    from .ledger import verify

    ok_all = True
    for name in cfg.sites:
        ok, msg = verify(cfg.ledger_dir, name)
        ok_all &= ok
        print(f"{name}: {'OK ' if ok else 'BROKEN '}{msg}")
    sys.exit(0 if ok_all else 1)


def cmd_commit(cfg: config.Config, args):
    from .ledger import write_commitments

    for name in cfg.sites:
        p = write_commitments(cfg.ledger_dir, name)
        print(f"{name}: {p}")


def cmd_serve(cfg: config.Config, args):
    from . import display

    display.serve(cfg, host=args.host, port=args.port, refresh_s=args.refresh)


def cmd_adev(cfg: config.Config, args):
    import numpy as np

    by_clock = analysis.load(cfg)
    recs = by_clock.get(args.clock)
    if not recs:
        print(f"no records for clock {args.clock}")
        return
    t = np.array([r[0] for r in recs])
    ti = np.array([r[2] for r in recs])
    tau0 = float(np.median(np.diff(t)))
    print(f"{len(ti)} samples, τ0 = {tau0:.0f} s")
    for tau, sig in analysis.adev(ti, tau0):
        print(f"  τ = {tau:10.0f} s   σ_y = {sig:.2e}")


def cmd_doctor(cfg: config.Config, args):
    from . import doctor

    checks = doctor.run(cfg, live=args.live, seconds=args.seconds)
    print(doctor.format_checks(checks))
    sys.exit(1 if any(c.ok is False for c in checks) else 0)


def cmd_zerobase(cfg: config.Config, args):
    from . import doctor

    out = doctor.zero_baseline_from_ledger(cfg, clock=args.clock, last_hours=args.last_hours)
    for k, v in out.items():
        print(f"  {k}: {v:.3f}" if isinstance(v, float) else f"  {k}: {v}")
    if out["recommend"] == 0:
        print("verdict: inconclusive")
    elif out["recommend"] == out.get("configured_sign"):
        print(f"verdict: qerr_sign = {out['recommend']} — config already right")
    else:
        print(f"verdict: set qerr_sign = {out['recommend']} in station.toml")


def cmd_export(cfg: config.Config, args):
    from . import export

    out = args.out or f"{args.what}.csv"
    if args.what == "daily":
        n = export.export_daily(cfg, out)
    elif args.what == "raw":
        n = export.export_raw(cfg, out, clock=args.clock)
    else:
        result = analysis.analyse(cfg)
        if not result.get("ok"):
            print(f"analysis failed: {result.get('error')}")
            sys.exit(1)
        n = export.export_lead(result, out) if args.what == "lead" else export.export_segments(result, out)
    print(f"{n} rows → {out}")


def cmd_report(cfg: config.Config, args):
    from . import reportgen

    if args.post:
        print(reportgen.post_text(cfg, day=args.day))
    else:
        print(reportgen.daily_report(cfg, day=args.day))


def cmd_passport(cfg: config.Config, args):
    from . import passport

    measured = sigma = None
    if args.measured:
        result = analysis.analyse(cfg)
        s = result.get("summary")
        if s:
            measured, sigma = s["measured_ns_day"], s["measured_sigma"]
        else:
            print("note: no measured rate yet; certificate uses the prediction only")
    site = args.site or next(n for n, s in cfg.sites.items() if not s.reference)
    cert = passport.certificate(cfg, site, args.arrive, args.depart, name=args.name,
                                measured_ns_day=measured, measured_sigma=sigma)
    print(passport.text(cert))
    if args.html:
        Path(args.html).write_text(passport.html(cert), encoding="utf-8")
        print(f"\ncertificate page → {args.html}")


def cmd_transport(cfg: config.Config, args):
    from . import export as exp
    from datetime import datetime, timezone

    def ts(s):
        return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() if s else None

    out = exp.transport_report(cfg, station=args.station, t_start=ts(args.start), t_end=ts(args.end))
    if not out["ok"]:
        print(out["error"])
        sys.exit(1)
    print(f"{out['n']} track samples, {out['started']} → {out['ended']} UTC ({out['hours']:.2f} h), "
          f"altitude {out['h_min_m']:.0f}–{out['h_max_m']:.0f} m")
    print(f"proper-time offset of the carried clock vs {cfg.reference.name}: {out['offset_ns']:+.3f} ns")


def cmd_rinex(cfg: config.Config, args):
    from . import rinex

    ok_all = True
    for r in rinex.convert_all(cfg, day=args.day, convbin=args.convbin):
        if r["ok"]:
            print(f"ok   {r['file']} → {r.get('obs')}" + (f"  ({r['skipped']})" if r.get("skipped") else ""))
        else:
            ok_all = False
            print(f"FAIL {r.get('file')}: {r['error']}")
    sys.exit(0 if ok_all else 1)


def cmd_init(path: str):
    p = Path(path)
    if p.exists():
        print(f"{p} exists; not overwriting")
        return
    example = Path(__file__).parent / "station.example.toml"
    p.write_text(example.read_text())
    print(f"wrote {p}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="greylock", description="software for a real (forward) time machine")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, **kw):
        s = sub.add_parser(name, **kw)
        s.add_argument("config")
        s.set_defaults(fn=fn)
        return s

    add("predict", cmd_predict, help="the number to pre-register")
    s = add("simulate", cmd_simulate, help="write a simulated season")
    s.add_argument("--cadence", type=float, default=None, help="seconds between records (default from config)")
    s.add_argument("--quiet", action="store_true")
    s = add("acquire", cmd_acquire, help="run a station")
    s.add_argument("--simulate", action="store_true", help="live digital twin instead of hardware")
    s.add_argument("--max-records", type=int, default=None)
    s = add("analyse", cmd_analyse, help="fit the rate and the lead")
    s.add_argument("--json", default=None, help="write the state JSON here")
    s.add_argument("--plot", default=None, help="write a PNG of the lead here")
    add("verify", cmd_verify, help="check every ledger's hash chain")
    add("commit", cmd_commit, help="write daily commitment files")
    s = add("serve", cmd_serve, help="serve the readout page")
    s.add_argument("--host", default="0.0.0.0")
    s.add_argument("--port", type=int, default=8080)
    s.add_argument("--refresh", type=float, default=60.0)
    s = add("adev", cmd_adev, help="Allan deviation of a clock's series")
    s.add_argument("--clock", required=True)

    s = add("doctor", cmd_doctor, help="bring-up self-test")
    s.add_argument("--live", action="store_true", help="probe TICC / u-blox / 5071A over serial")
    s.add_argument("--seconds", type=float, default=10.0, help="per-device probe time")
    s = add("zerobase", cmd_zerobase, help="decide qerr_sign from ledger data")
    s.add_argument("--clock", default=None)
    s.add_argument("--last-hours", type=float, default=None, help="only use the last N hours")
    s = add("export", cmd_export, help="CSV export")
    s.add_argument("--what", choices=("daily", "lead", "segments", "raw"), default="daily")
    s.add_argument("--out", default=None)
    s.add_argument("--clock", default=None, help="raw export: one clock only")
    s = add("report", cmd_report, help="daily operations report")
    s.add_argument("--day", default=None, help="UTC day (default: yesterday)")
    s.add_argument("--post", action="store_true", help="the one-line public text instead")
    s = add("passport", cmd_passport, help="a visitor's time-travel certificate")
    s.add_argument("--arrive", required=True, help="ISO time, e.g. 2027-07-04T15:00Z")
    s.add_argument("--depart", required=True)
    s.add_argument("--name", default="A Time Traveller")
    s.add_argument("--site", default=None, help="default: the non-reference site")
    s.add_argument("--measured", action="store_true", help="also state the measured machine rate")
    s.add_argument("--html", default=None, help="write a printable HTML certificate here")
    s = add("transport", cmd_transport, help="proper-time integral of a logged drive")
    s.add_argument("--station", default=None, help="which station's ledger holds the track")
    s.add_argument("--start", default=None, help="ISO time window start")
    s.add_argument("--end", default=None)
    s = add("rinex", cmd_rinex, help="raw UBX → RINEX via convbin")
    s.add_argument("--day", default=None, help="one UTC day, e.g. 2027-06-07")
    s.add_argument("--convbin", default="convbin")

    s = sub.add_parser("init", help="write an example config")
    s.add_argument("config")

    args = ap.parse_args(argv)
    try:
        if args.cmd == "init":
            cmd_init(args.config)
            return
        cfg = config.load(args.config)
        args.fn(cfg, args)
    except BrokenPipeError:        # `greylock ... | head` is a legitimate way to read us
        import os
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(0)


if __name__ == "__main__":
    main()
