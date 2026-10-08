"""The acquisition daemon that runs on each station's Raspberry Pi.

One record per cesium pulse (1 Hz):
    t          Pi time (chrony-disciplined from the GNSS PPS, see deploy/)
    site       where this station is (from the config)
    clock      which cesium unit is here (from the config)
    ti_ns      cesium 1PPS − GNSS 1PPS, from the TICC, on the cesium's time base
    qerr_ps    the receiver's reported quantisation error for that pulse
    fix, num_sv, h_msl, g_speed, lat, vel_e   from NAV-PVT (health and the
               transport integral during a drive)
    temp_c, press_hpa, rh         from the case sensor
    on_battery                    from the UPS (NUT) if configured

Every `cesium_health_every_s` seconds a health record (no ti_ns) is appended
with the clock's own status report.  Operational anomalies become event records
(kind = "event"): a pulse gap, a mains-power transition, low disk.  All records
go into the hash-chained ledger — the anomalies are part of the history.

Robustness (v0.2):
  * clean shutdown on SIGTERM/SIGINT — the ledger file is closed, the chain
    resumes on restart
  * systemd watchdog support: READY=1 on startup, WATCHDOG=1 with every status
    heartbeat (see deploy/greylock-acquire.service, Type=notify)
  * the raw UBX log rolls to a new file at UTC midnight, and stops (with an
    event record) when free disk falls below acquire.min_free_gb — ti records
    continue, they are tiny
  * a missing pulse for more than acquire.stale_pulse_s writes an event and
    keeps the daemon (and the watchdog) alive rather than blocking forever

Run:   greylock acquire station.toml           (hardware)
       greylock acquire station.toml --simulate (a live digital twin, for testing
                                                 the display without hardware)
"""
from __future__ import annotations

import json
import os
import queue
import shutil
import signal
import socket
import subprocess
import threading
import time
from pathlib import Path

from .config import Config
from .ledger import Ledger

STALE = object()   # sentinel from the hardware source when no pulse arrives in time


def sd_notify(message: str) -> None:
    """Tell systemd we are alive (Type=notify + WatchdogSec).  No-op elsewhere."""
    path = os.environ.get("NOTIFY_SOCKET")
    if not path:
        return
    try:
        if path.startswith("@"):
            path = "\0" + path[1:]
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as s:
            s.connect(path)
            s.send(message.encode("utf-8"))
    except OSError:
        pass


def free_gb(path: Path) -> float:
    probe = path if path.exists() else path.parent
    try:
        return shutil.disk_usage(probe).free / 1e9
    except OSError:
        return float("inf")


class RollingRawLog:
    """Daily raw UBX files with a low-disk cutoff.  write() never raises."""

    def __init__(self, directory: Path, min_free_gb: float = 1.0):
        self.dir = Path(directory)
        self.min_free_gb = min_free_gb
        self._fh = None
        self._day = None
        self.suspended = False

    def path_for(self, t_unix: float) -> Path:
        return self.dir / time.strftime("ubx-%Y-%m-%d.bin", time.gmtime(t_unix))

    def write(self, data: bytes, t_unix: float | None = None) -> str | None:
        """Returns an event string on a state change (suspended/resumed), else None."""
        t = time.time() if t_unix is None else t_unix
        day = time.strftime("%Y-%m-%d", time.gmtime(t))
        event = None
        try:
            if day != self._day:
                if self._fh:
                    self._fh.close()
                    self._fh = None
                low = free_gb(self.dir) < self.min_free_gb
                if low and not self.suspended:
                    self.suspended, event = True, "raw UBX logging suspended: low disk"
                elif not low and self.suspended:
                    self.suspended, event = False, "raw UBX logging resumed"
                if not self.suspended:
                    self.dir.mkdir(parents=True, exist_ok=True)
                    self._fh = self.path_for(t).open("ab")
                self._day = day
            if self._fh and not self.suspended:
                self._fh.write(data)
        except OSError as exc:
            if not self.suspended:
                self.suspended, event = True, f"raw UBX logging suspended: {exc}"
            self._fh = None
        return event

    def close(self):
        if self._fh:
            self._fh.close()
            self._fh = None


class Shared:
    def __init__(self):
        self.lock = threading.Lock()
        self.tim_tp = None
        self.nav_pvt = None
        self.on_battery = None
        self.cesium_health = None
        self.errors: list[str] = []
        self.events: list[str] = []      # drained into ledger event records

    def error(self, msg: str):
        with self.lock:
            self.errors.append(msg)
            del self.errors[:-20]

    def event(self, msg: str):
        with self.lock:
            self.events.append(msg)


def _ticc_thread(port, baud, q: queue.Queue, shared: Shared, stop: threading.Event):
    from . import ticc

    while not stop.is_set():
        try:
            for ti in ticc.read_serial(port, baud):
                q.put((time.time(), ti))
                if stop.is_set():
                    return
        except Exception as exc:  # reconnect loop
            shared.error(f"ticc: {exc}")
            stop.wait(5)


def _ublox_thread(port, baud, raw: RollingRawLog | None, shared: Shared, stop: threading.Event):
    from . import ublox

    while not stop.is_set():
        try:
            import serial
            parser = ublox.UbxParser()
            with serial.Serial(port, baud, timeout=2) as ser:
                while not stop.is_set():
                    chunk = ser.read(512)
                    if not chunk:
                        continue
                    if raw is not None:
                        ev = raw.write(chunk)
                        if ev:
                            shared.event(ev)
                    for cls, msg_id, payload in parser.feed(chunk):
                        obj = ublox.decode(cls, msg_id, payload)
                        with shared.lock:
                            if isinstance(obj, ublox.TimTp):
                                shared.tim_tp = obj
                            elif isinstance(obj, ublox.NavPvt):
                                shared.nav_pvt = obj
        except Exception as exc:
            shared.error(f"ublox: {exc}")
            stop.wait(5)


def _cesium_thread(port, every_s, ledger: Ledger, shared: Shared, lock: threading.Lock,
                   stop: threading.Event):
    from .cesium import Cesium5071A

    while not stop.is_set():
        try:
            cs = Cesium5071A(port)
            while not stop.is_set():
                h = cs.health()
                with shared.lock:
                    shared.cesium_health = h
                rec = {"t": h.t, "kind": "cesium_health", "idn": h.idn,
                       "continuous_operation": h.continuous_operation, "fields": h.fields,
                       "status_text": h.status_text[:4000], "errors": h.errors}
                with lock:
                    ledger.append(rec)
                stop.wait(every_s)
        except Exception as exc:
            shared.error(f"cesium: {exc}")
            stop.wait(30)


def _ups_thread(ups_name, shared: Shared, stop: threading.Event):
    while not stop.is_set():
        try:
            out = subprocess.run(["upsc", ups_name, "ups.status"], capture_output=True,
                                 text=True, timeout=10)
            status = out.stdout.strip()
            with shared.lock:
                shared.on_battery = ("OB" in status.split()) if status else None
        except Exception as exc:
            with shared.lock:
                shared.on_battery = None
            shared.error(f"ups: {exc}")
        stop.wait(60)


def run(cfg: Config, simulate: bool = False, max_records: int | None = None, status_path=None,
        stop: threading.Event | None = None):
    st = cfg.station
    hw = cfg.hardware
    ac = cfg.raw.get("acquire", {})
    stale_s = float(ac.get("stale_pulse_s", 15.0))
    min_free = float(ac.get("min_free_gb", 1.0))
    site_name = st["site"]
    clock_name = st["clock"]
    ledger = Ledger(cfg.ledger_dir, site_name)
    lock = threading.Lock()
    shared = Shared()
    q: queue.Queue = queue.Queue()
    stop = stop or threading.Event()
    status_path = Path(status_path or (cfg.ledger_dir / f"{site_name}-status.json"))

    # SIGTERM/SIGINT → finish the current record, close the ledger cleanly.
    def _stop_signal(signum, frame):
        stop.set()
    if threading.current_thread() is threading.main_thread():
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                signal.signal(sig, _stop_signal)
            except (ValueError, OSError):   # pragma: no cover - non-main contexts
                pass

    sensor = None
    if simulate:
        from .clockmodel import CesiumModel, EnvironmentModel, GnssPpsModel
        from .physics import gravitational_rate

        site = cfg.site(site_name)
        clock = CesiumModel(name=clock_name, intrinsic_offset=float(st.get("sim_intrinsic_offset", 1e-13)))
        rx = GnssPpsModel()
        envm = EnvironmentModel(outside_mean_c=15.0 - 0.0065 * site.height_m)
        grav = gravitational_rate(site, cfg.reference)
        cadence = float(st.get("cadence_s", 1))

        def source():
            t = time.time()
            while not stop.is_set():
                temp, outside, press = envm.sample(t)
                x = clock.step(cadence, grav, temp)
                err, qerr = rx.step(cadence)
                yield t, (x - err) * 1e9, qerr, temp, press, None
                t += cadence
                stop.wait(max(0.0, t - time.time()))
        src = source()
    else:
        from .env import open_sensor

        sensor = open_sensor()
        if sensor is None:
            shared.error("env: no BME280 found — temperature will not be logged")
        raw = RollingRawLog(cfg.ledger_dir / "ubx", min_free) if hw.get("ublox_raw_log", True) else None
        threading.Thread(target=_ticc_thread, args=(hw["ticc_port"], hw.get("ticc_baud", 115200),
                                                    q, shared, stop), daemon=True).start()
        threading.Thread(target=_ublox_thread, args=(hw["ublox_port"], hw.get("ublox_baud", 38400),
                                                     raw, shared, stop), daemon=True).start()
        if hw.get("cesium_port"):
            threading.Thread(target=_cesium_thread, args=(hw["cesium_port"], hw.get("cesium_health_every_s", 600),
                                                          ledger, shared, lock, stop), daemon=True).start()
        if hw.get("ups_name"):
            threading.Thread(target=_ups_thread, args=(hw["ups_name"], shared, stop), daemon=True).start()

        def source():
            while not stop.is_set():
                try:
                    t, ti = q.get(timeout=stale_s)
                except queue.Empty:
                    yield STALE, None, None, None, None, None
                    continue
                with shared.lock:
                    tp, pvt, bat = shared.tim_tp, shared.nav_pvt, shared.on_battery
                qerr = float(tp.qerr_ps) if tp else 0.0
                temp = press = rh = None
                if sensor is not None:
                    try:
                        temp, press, rh = sensor.read()
                    except Exception:
                        pass
                yield t, ti, qerr, temp, press, (pvt, bat, rh)
        src = source()

    sd_notify("READY=1")
    n = 0
    last_status = 0.0
    last_stale_event = 0.0
    last_bat = None
    try:
        for t, ti, qerr, temp, press, extra in src:
            now = time.time()
            if t is STALE:
                if now - last_stale_event > stale_s:   # one event per dry spell, not per timeout
                    last_stale_event = now
                    with lock:
                        ledger.append({"t": round(now, 3), "kind": "event", "site": site_name,
                                       "clock": clock_name,
                                       "event": f"no pulse from TICC for > {stale_s:.0f} s"})
                    shared.error(f"no pulse for > {stale_s:.0f} s")
            else:
                last_stale_event = 0.0
                rec = {"t": round(t, 3), "site": site_name, "clock": clock_name,
                       "ti_ns": round(ti, 3), "qerr_ps": round(qerr, 1),
                       "temp_c": None if temp is None else round(temp, 2),
                       "press_hpa": None if press is None else round(press, 1),
                       "source": "sim" if simulate else "hw"}
                if extra:
                    pvt, bat, rh = extra
                    rec["on_battery"] = bat
                    rec["rh"] = None if rh is None else round(rh, 1)
                    if pvt is not None:
                        rec.update({"fix": pvt.fix_type, "num_sv": pvt.num_sv,
                                    "h_msl": round(pvt.h_msl_m, 1), "lat": round(pvt.lat_deg, 6),
                                    "g_speed": round(pvt.g_speed_m_s, 2),
                                    "vel_e": round(pvt.vel_e_m_s, 2), "t_acc_ns": pvt.t_acc_ns})
                    if bat is not None and bat != last_bat and last_bat is not None:
                        with lock:
                            ledger.append({"t": round(t, 3), "kind": "event", "site": site_name,
                                           "clock": clock_name,
                                           "event": "mains lost — on battery" if bat else "mains restored"})
                    last_bat = bat if bat is not None else last_bat
                else:
                    rec["on_battery"] = False
                with lock:
                    h = ledger.append(rec)
                n += 1

            # drain queued events (raw-log suspensions etc.) into the ledger
            with shared.lock:
                events, shared.events = shared.events, []
            for ev in events:
                with lock:
                    ledger.append({"t": round(now, 3), "kind": "event", "site": site_name,
                                   "clock": clock_name, "event": ev})

            if now - last_status > 10:
                last_status = now
                sd_notify("WATCHDOG=1")
                with shared.lock:
                    errs = shared.errors[-5:]
                try:
                    status_path.write_text(json.dumps(
                        {"t": now, "records": n, "last_ti_ns": None if t is STALE else ti,
                         "head": ledger.prev, "errors": errs, "site": site_name,
                         "clock": clock_name, "free_gb": round(free_gb(cfg.ledger_dir), 2)}))
                except OSError as exc:
                    shared.error(f"status: {exc}")
            if max_records and n >= max_records:
                break
    finally:
        sd_notify("STOPPING=1")
        ledger.close()
    return n
