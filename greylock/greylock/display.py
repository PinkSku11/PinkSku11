"""The readout: a small web server that re-analyses the ledger every minute and
serves a page showing the summit's lead over sea-level time, live.

    greylock serve station.toml --port 8080

Endpoints
    /               the readout page (readout.html, no external resources)
    /api/state      analysis result as JSON (cached, recomputed every `refresh_s`)
    /api/status     the acquisition daemons' heartbeat files
    /api/daily.csv  the daily points the fits run on (export.export_daily)
    /api/report     the plain-text operations report for yesterday
    /metrics        Prometheus-style text: lead, rate, σ, heartbeat ages
A Nixie / 7-segment / e-ink display, or the ESP32 sketch in firmware/, reads
/api/state and shows summary.lead_total_ns.
"""
from __future__ import annotations

import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import analysis
from .config import Config

HERE = Path(__file__).parent


class State:
    def __init__(self, cfg: Config, refresh_s: float = 60.0):
        self.cfg = cfg
        self.refresh_s = refresh_s
        self.lock = threading.Lock()
        self.payload = b"{}"
        self.last = 0.0

    def get(self) -> bytes:
        with self.lock:
            if time.time() - self.last > self.refresh_s:
                try:
                    result = analysis.analyse(self.cfg)
                except Exception as exc:
                    result = {"ok": False, "error": repr(exc)}
                result["generated_at"] = time.time()
                self.payload = json.dumps(result, default=float).encode("utf-8")
                self.last = time.time()
            return self.payload

    def status(self) -> bytes:
        out = {}
        for p in self.cfg.ledger_dir.glob("*-status.json"):
            try:
                out[p.stem.replace("-status", "")] = json.loads(p.read_text())
            except Exception:
                pass
        return json.dumps(out).encode("utf-8")

    def metrics(self) -> bytes:
        """Prometheus exposition format, for scraping by any monitoring stack."""
        lines = []
        try:
            result = json.loads(self.get())
        except Exception:
            result = {}
        s = result.get("summary") or {}
        for key, name in (("lead_total_ns", "greylock_lead_ns"),
                          ("predicted_lead_ns", "greylock_predicted_lead_ns"),
                          ("measured_ns_day", "greylock_rate_ns_per_day"),
                          ("measured_sigma", "greylock_rate_sigma_ns_per_day"),
                          ("detection_sigma", "greylock_detection_sigma")):
            if s.get(key) is not None:
                lines.append(f"{name} {float(s[key]):.6g}")
        try:
            status = json.loads(self.status())
        except Exception:
            status = {}
        now = time.time()
        for station, st in sorted(status.items()):
            lab = f'{{station="{station}"}}'
            lines.append(f"greylock_heartbeat_age_seconds{lab} {now - float(st.get('t', 0)):.0f}")
            lines.append(f"greylock_records_total{lab} {int(st.get('records', 0))}")
            if st.get("free_gb") is not None:
                lines.append(f"greylock_disk_free_gb{lab} {float(st['free_gb']):.2f}")
            lines.append(f"greylock_errors{lab} {len(st.get('errors', []))}")
        return ("\n".join(lines) + "\n").encode("utf-8")

    def daily_csv(self) -> bytes:
        import tempfile

        from . import export
        with tempfile.NamedTemporaryFile("r", suffix=".csv", delete=False) as tmp:
            path = tmp.name
        try:
            export.export_daily(self.cfg, path)
            return Path(path).read_bytes()
        finally:
            Path(path).unlink(missing_ok=True)

    def report_text(self) -> bytes:
        from . import reportgen
        try:
            result = json.loads(self.get())
        except Exception:
            result = None
        return reportgen.daily_report(self.cfg, result=result).encode("utf-8")


def make_handler(state: State):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):  # quiet
            pass

        def _send(self, code: int, ctype: str, body: bytes):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            try:
                if self.path.startswith("/api/state"):
                    self._send(200, "application/json", state.get())
                elif self.path.startswith("/api/status"):
                    self._send(200, "application/json", state.status())
                elif self.path.startswith("/api/daily.csv"):
                    self._send(200, "text/csv; charset=utf-8", state.daily_csv())
                elif self.path.startswith("/api/report"):
                    self._send(200, "text/plain; charset=utf-8", state.report_text())
                elif self.path.startswith("/metrics"):
                    self._send(200, "text/plain; version=0.0.4; charset=utf-8", state.metrics())
                elif self.path in ("/", "/index.html"):
                    self._send(200, "text/html; charset=utf-8", (HERE / "readout.html").read_bytes())
                else:
                    self._send(404, "text/plain", b"not found")
            except BrokenPipeError:   # client went away mid-response
                pass
            except Exception as exc:
                try:
                    self._send(500, "text/plain", f"error: {exc!r}".encode())
                except Exception:
                    pass

    return Handler


def serve(cfg: Config, host: str = "0.0.0.0", port: int = 8080, refresh_s: float = 60.0):
    state = State(cfg, refresh_s)
    httpd = ThreadingHTTPServer((host, port), make_handler(state))
    print(f"readout at http://{host}:{port}/   (state refresh every {refresh_s:.0f} s)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
