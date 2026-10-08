"""`greylock doctor` — the bring-up self-test, run before trusting a station.

Checks, in order of how often they bite:
  config     every key the daemon will read, with the actual values echoed back
  disk       free space under the ledger directory (raw UBX is the big consumer)
  chrony     is the Pi's clock disciplined, and by how much is it off
  ports      do the configured serial devices exist; stable /dev/serial/by-id hints
  ticc       (--live) read the TICC for a few seconds: mode, pulse rate, ti sanity
  ublox      (--live) read the receiver: TIM-TP and NAV-PVT present, fix, qErr
  cesium     (--live) *IDN? and continuous-operation flag over RS-232
  ledger     the hash chain of every station ledger present

Also here because they are diagnostics, not analysis:
  zero_baseline()  decides qerr_sign from data — the corrected per-pulse jitter
                   must shrink with the right sign (README step 5), so try both
                   and report which one wins
  ti_sanity()      catches the two classic wiring mistakes: channels swapped
                   (|ti| within a few µs of a whole second) and phase steps
"""
from __future__ import annotations

import math
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .config import Config


@dataclass
class Check:
    name: str
    ok: bool | None          # None = skipped / not applicable
    detail: str
    notes: list = field(default_factory=list)


def _skip(name: str, why: str) -> Check:
    return Check(name, None, why)


# --------------------------------------------------------------------------- config
def check_config(cfg: Config) -> Check:
    problems = []
    st, hw = cfg.station, cfg.hardware
    for key in ("site", "clock"):
        if not st.get(key):
            problems.append(f"[station] {key} missing")
    if st.get("site") and st.get("site") not in cfg.sites:
        problems.append(f"[station] site '{st.get('site')}' is not in [sites]")
    if not any(s.reference for s in cfg.sites.values()):
        problems.append("no site has reference = true")
    sign = hw.get("qerr_sign", 1)
    if sign not in (1, -1):
        problems.append(f"qerr_sign must be +1 or -1, found {sign!r}")
    for s in cfg.sites.values():
        if not (-90 <= s.lat_deg <= 90):
            problems.append(f"site {s.name}: latitude {s.lat_deg} out of range")
        if not (-500 <= s.height_m <= 9000):
            problems.append(f"site {s.name}: height {s.height_m} m looks wrong")
    detail = "; ".join(problems) if problems else (
        f"station '{st.get('name', '?')}' is clock {st.get('clock')} at {st.get('site')}; "
        f"ledger {cfg.ledger_dir}")
    return Check("config", not problems, detail)


# --------------------------------------------------------------------------- disk
def check_disk(path: Path, min_free_gb: float = 2.0) -> Check:
    p = Path(path)
    probe = p if p.exists() else p.parent if p.parent.exists() else Path(".")
    usage = shutil.disk_usage(probe)
    free_gb = usage.free / 1e9
    detail = f"{free_gb:.1f} GB free at {probe} (raw UBX ≈ 0.4 GB/day/station)"
    return Check("disk", free_gb >= min_free_gb, detail)


# --------------------------------------------------------------------------- chrony
def check_chrony() -> Check:
    try:
        out = subprocess.run(["chronyc", "tracking"], capture_output=True, text=True, timeout=10)
    except FileNotFoundError:
        return _skip("chrony", "chronyc not installed (fine off-station; required on a Pi)")
    except Exception as exc:
        return Check("chrony", False, f"chronyc failed: {exc}")
    if out.returncode != 0:
        return Check("chrony", False, out.stderr.strip() or "chronyc tracking returned non-zero")
    offset_s = None
    source = ""
    for line in out.stdout.splitlines():
        low = line.lower()
        if low.startswith("system time"):
            try:
                offset_s = float(line.split(":", 1)[1].strip().split()[0])
            except (IndexError, ValueError):
                pass
        if low.startswith("reference id"):
            source = line.split(":", 1)[1].strip()
    if offset_s is None:
        return Check("chrony", False, "could not parse 'System time' from chronyc tracking")
    ok = abs(offset_s) < 1e-3  # record timestamps only need milliseconds; PPS gives µs
    return Check("chrony", ok, f"system clock offset {offset_s * 1e6:+.0f} µs (ref {source})")


# --------------------------------------------------------------------------- serial ports
def check_ports(cfg: Config) -> Check:
    hw = cfg.hardware
    wanted = [(k, hw.get(k)) for k in ("ticc_port", "ublox_port", "cesium_port") if hw.get(k)]
    try:
        from serial.tools import list_ports
        present = {p.device: p for p in list_ports.comports()}
    except ImportError:
        return _skip("ports", "pyserial not installed (pip install -e '.[hardware]')")
    missing = [f"{k}={v}" for k, v in wanted if v not in present and not Path(v).exists()]
    notes = []
    for dev, p in present.items():
        if "/serial/by-id/" not in dev and (p.vid or p.serial_number):
            by_id = Path("/dev/serial/by-id")
            if by_id.is_dir():
                notes.append("prefer /dev/serial/by-id/* paths in station.toml: they survive replugging")
                break
    detail = ("missing: " + ", ".join(missing)) if missing else \
        f"all configured ports present ({', '.join(v for _, v in wanted)})"
    return Check("ports", not missing, detail, notes=notes[:1])


# --------------------------------------------------------------------------- live probes
def probe_ticc(port: str, baud: int, seconds: float = 10.0) -> Check:
    from . import ticc
    try:
        import serial
    except ImportError:
        return _skip("ticc", "pyserial not installed")
    kinds: dict[str, int] = {}
    tis: list[float] = []
    pairer = ticc.TiccPairer()
    try:
        with serial.Serial(port, baud, timeout=2) as ser:
            t0 = time.time()
            while time.time() - t0 < seconds:
                raw = ser.readline().decode("ascii", errors="replace")
                ev = ticc.parse_line(raw) if raw else None
                if ev is None:
                    continue
                kinds[ev.kind] = kinds.get(ev.kind, 0) + 1
                ti = pairer.feed(ev)
                if ti is not None:
                    tis.append(ti)
    except Exception as exc:
        return Check("ticc", False, f"{port}: {exc}")
    if not kinds:
        return Check("ticc", False, f"{port}: no parseable lines in {seconds:.0f} s "
                                    "(wrong port, wrong baud, or no pulses)")
    mode = "time-interval" if any(k.startswith("TI") for k in kinds) else "timestamp"
    detail = f"{mode} mode, {sum(kinds.values())} lines, {len(tis)} intervals in {seconds:.0f} s"
    notes = ti_sanity(np.array(tis)) if tis else ["no completed intervals yet"]
    return Check("ticc", True, detail, notes=notes)


def probe_ublox(port: str, baud: int, seconds: float = 10.0) -> Check:
    from . import ublox
    try:
        import serial
    except ImportError:
        return _skip("ublox", "pyserial not installed")
    n_tp = n_pvt = 0
    last_tp = last_pvt = None
    try:
        with serial.Serial(port, baud, timeout=2) as ser:
            parser = ublox.UbxParser()
            t0 = time.time()
            while time.time() - t0 < seconds:
                chunk = ser.read(512)
                for cls, mid, payload in parser.feed(chunk):
                    obj = ublox.decode(cls, mid, payload)
                    if isinstance(obj, ublox.TimTp):
                        n_tp, last_tp = n_tp + 1, obj
                    elif isinstance(obj, ublox.NavPvt):
                        n_pvt, last_pvt = n_pvt + 1, obj
    except Exception as exc:
        return Check("ublox", False, f"{port}: {exc}")
    if n_tp == 0 and n_pvt == 0:
        return Check("ublox", False, f"{port}: no UBX frames in {seconds:.0f} s "
                                     "(NMEA-only output? enable UBX-TIM-TP and UBX-NAV-PVT)")
    bits = [f"TIM-TP ×{n_tp}", f"NAV-PVT ×{n_pvt}"]
    notes = []
    if last_pvt is not None:
        bits.append(f"fix {last_pvt.fix_type}, {last_pvt.num_sv} SV, tAcc {last_pvt.t_acc_ns} ns")
        if last_pvt.fix_type < 3:
            notes.append("no 3D fix — antenna sky view?")
    if last_tp is not None:
        bits.append(f"qErr {last_tp.qerr_ps} ps")
    if n_tp == 0:
        notes.append("TIM-TP absent: qErr sawtooth cannot be removed — enable it")
    return Check("ublox", n_tp > 0 and n_pvt > 0, ", ".join(bits), notes=notes)


def probe_cesium(port: str) -> Check:
    from .cesium import Cesium5071A
    try:
        cs = Cesium5071A(port)
    except Exception as exc:
        return Check("cesium", False, f"{port}: {exc}")
    try:
        h = cs.health()
    finally:
        cs.close()
    if not h.idn and not h.fields:
        return Check("cesium", False, f"{port}: no response to *IDN? (baud? null-modem cable?)")
    detail = h.idn or "responded"
    if h.continuous_operation is not None:
        detail += f"; continuous operation: {'yes' if h.continuous_operation else 'NO'}"
    return Check("cesium", bool(h.idn), detail,
                 notes=[f"{k}={v}" for k, v in sorted(h.fields.items())][:4])


# --------------------------------------------------------------------------- ledger
def check_ledgers(cfg: Config) -> list[Check]:
    from .ledger import verify
    out = []
    d = cfg.ledger_dir
    for name in cfg.sites:
        if not any(d.glob(f"{name}-*.jsonl")):
            out.append(_skip(f"ledger:{name}", "no files yet"))
            continue
        ok, msg = verify(d, name)
        out.append(Check(f"ledger:{name}", ok, msg))
    return out


# --------------------------------------------------------------------------- data diagnostics
def ti_sanity(ti_ns: np.ndarray, step_ns: float = 50.0) -> list[str]:
    """Notes on a ti series: swapped channels, wild scatter, phase steps."""
    notes: list[str] = []
    if len(ti_ns) == 0:
        return notes
    med = float(np.median(ti_ns))
    if abs(abs(med) - 1e9) < 1e7:
        notes.append(f"|median ti| = {med / 1e9:+.3f} s ≈ 1 s: chA/chB likely swapped, or the "
                     "pairer is matching a pulse with the following second's pulse")
    if len(ti_ns) >= 3:
        d = np.diff(ti_ns)
        mad = float(np.median(np.abs(d - np.median(d)))) * 1.4826
        big = np.where(np.abs(d - np.median(d)) > max(step_ns, 10 * mad))[0]
        for i in big[:3]:
            notes.append(f"phase step of {d[i]:+.1f} ns between samples {i} and {i + 1}")
        if len(big) > 3:
            notes.append(f"... and {len(big) - 3} more steps")
    return notes


def zero_baseline(ti_ns: np.ndarray, qerr_ps: np.ndarray) -> dict:
    """Decide qerr_sign from data (the automated README step 5).

    For both candidate signs, correct the series and measure the per-pulse jitter
    as the standard deviation of first differences (differencing removes any
    frequency offset / slow drift, leaving the white part the sawtooth sits in).
    The right sign makes the jitter *smaller* than no correction; the wrong sign
    roughly doubles the sawtooth power.  Returns the numbers and a recommendation:
    +1, -1, or 0 when the difference is too small to call (e.g. qErr all zero).
    """
    ti = np.asarray(ti_ns, float)
    q_ns = np.asarray(qerr_ps, float) / 1000.0
    if len(ti) < 10 or np.all(q_ns == 0):
        return {"recommend": 0, "reason": "not enough data or qErr all zero", "n": int(len(ti))}

    def jitter(series):
        return float(np.std(np.diff(series)))

    j0 = jitter(ti)
    jp = jitter(ti + q_ns)
    jm = jitter(ti - q_ns)
    best = min(jp, jm)
    rec = 0
    if best < j0 * 0.98 and abs(jp - jm) > 0.05 * j0:
        rec = 1 if jp < jm else -1
    return {"recommend": rec, "jitter_uncorrected_ns": j0, "jitter_plus_ns": jp,
            "jitter_minus_ns": jm, "n": int(len(ti)),
            "reason": "corrected jitter must shrink; the smaller of ±1 wins" if rec else
                      "difference too small to call — collect more data or check TIM-TP"}


def zero_baseline_from_ledger(cfg: Config, clock: str | None = None,
                              last_hours: float | None = None) -> dict:
    """Run the zero-baseline sign test on raw ledger records (uncorrected ti + qErr)."""
    from .ledger import iter_records
    cutoff = time.time() - last_hours * 3600.0 if last_hours else None
    ti, q = [], []
    for rec in iter_records(cfg.ledger_dir):
        if "ti_ns" not in rec:
            continue
        if clock and rec.get("clock") != clock:
            continue
        if cutoff and float(rec["t"]) < cutoff:
            continue
        ti.append(float(rec["ti_ns"]))
        q.append(float(rec.get("qerr_ps", 0.0)))
    out = zero_baseline(np.array(ti), np.array(q))
    out["configured_sign"] = int(cfg.hardware.get("qerr_sign", 1))
    if out["recommend"] and out["recommend"] != out["configured_sign"]:
        out["reason"] = (f"FLIP IT: data say qerr_sign = {out['recommend']}, "
                         f"config says {out['configured_sign']}")
    return out


# --------------------------------------------------------------------------- the doctor
def run(cfg: Config, live: bool = False, seconds: float = 10.0,
        min_free_gb: float = 2.0) -> list[Check]:
    checks = [check_config(cfg), check_disk(cfg.ledger_dir, min_free_gb), check_chrony(),
              check_ports(cfg)]
    hw = cfg.hardware
    if live:
        if hw.get("ticc_port"):
            checks.append(probe_ticc(hw["ticc_port"], hw.get("ticc_baud", 115200), seconds))
        if hw.get("ublox_port"):
            checks.append(probe_ublox(hw["ublox_port"], hw.get("ublox_baud", 38400), seconds))
        if hw.get("cesium_port"):
            checks.append(probe_cesium(hw["cesium_port"]))
    else:
        checks.append(_skip("ticc/ublox/cesium", "pass --live to probe the hardware"))
    checks.extend(check_ledgers(cfg))
    return checks


def format_checks(checks: list[Check]) -> str:
    mark = {True: "ok  ", False: "FAIL", None: "--  "}
    lines = []
    for c in checks:
        lines.append(f"{mark[c.ok]} {c.name:<14} {c.detail}")
        for n in c.notes:
            lines.append(f"     {'':<14} note: {n}")
    bad = sum(1 for c in checks if c.ok is False)
    lines.append(f"{bad} problem(s)" if bad else "station looks ready")
    return "\n".join(lines)
