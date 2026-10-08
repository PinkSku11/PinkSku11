"""`greylock rinex` — turn the daily raw UBX logs into RINEX for PPP later.

The acquisition daemon tees the receiver's raw stream (RXM-RAWX + RXM-SFRBX)
into data/ledger/ubx/ubx-YYYY-MM-DD.bin.  RTKLIB's `convbin` (apt: rtklib)
turns each day into RINEX observation + navigation files; a PPP service (e.g.
CSRS-PPP) or a local PPP run then yields the receiver clock against GPS time
at 0.1–0.3 ns, replacing the daily medians as the link.  This module only
drives convbin and keeps the bookkeeping; it never rewrites the raw files.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from .config import Config


def ubx_files(cfg: Config, day: str | None = None) -> list[Path]:
    d = cfg.ledger_dir / "ubx"
    # matches both the station-named ubx-<station>-YYYY-MM-DD.bin and the plain form
    pattern = f"ubx-*{day}.bin" if day else "ubx-*.bin"
    return sorted(d.glob(pattern))


def convert(ubx_path: Path, out_dir: Path, convbin: str = "convbin") -> dict:
    """Run convbin on one daily file.  Returns a result dict; never raises on a
    missing binary (the message says how to install it)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = ubx_path.stem                     # ubx-YYYY-MM-DD
    obs = out_dir / f"{stem}.obs"
    nav = out_dir / f"{stem}.nav"
    cmd = [convbin, "-r", "ubx", "-od", "-os", "-oi", "-ot",
           "-o", str(obs), "-n", str(nav), str(ubx_path)]
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    except FileNotFoundError:
        return {"ok": False, "file": str(ubx_path),
                "error": f"'{convbin}' not found — install RTKLIB (apt install rtklib) "
                         "or pass --convbin /path/to/convbin"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "file": str(ubx_path), "error": "convbin timed out (600 s)"}
    ok = run.returncode == 0 and obs.exists()
    return {"ok": ok, "file": str(ubx_path), "obs": str(obs) if obs.exists() else None,
            "nav": str(nav) if nav.exists() else None,
            "error": None if ok else (run.stderr.strip() or run.stdout.strip() or
                                      f"convbin exit {run.returncode}")}


def convert_all(cfg: Config, day: str | None = None, convbin: str = "convbin") -> list[dict]:
    files = ubx_files(cfg, day)
    if not files:
        return [{"ok": False, "file": None,
                 "error": "no raw UBX files found (hardware.ublox_raw_log = true writes them)"}]
    out_dir = cfg.ledger_dir / "rinex"
    results = []
    for f in files:
        obs = out_dir / f"{f.stem}.obs"
        if obs.exists() and obs.stat().st_mtime >= f.stat().st_mtime:
            results.append({"ok": True, "file": str(f), "obs": str(obs), "skipped": "up to date"})
            continue
        results.append(convert(f, out_dir, convbin))
    return results
