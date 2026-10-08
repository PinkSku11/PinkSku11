"""5071A cesium standard — health polling over its RS-232 (SCPI) port.

The clock's physics is not ours to touch; this module only *asks it how it is*
and writes the answers into the ledger, so that a run can be judged valid: beam
current, oven and electronics temperatures, lock status, power source (mains or
internal battery), and the event log.  A run in which the clock was ever on its
internal battery, or ever lost lock, is flagged.

Port: 9600 baud, 8N1, CR/LF line endings, command/response.  The commands below
are the standard SCPI set documented in the 5071A operating manual; confirm the
exact spellings against the manual of the unit you borrow (firmware revisions
differ), and if a query errors the module just logs the error text.

Nothing here can change the clock's frequency: the package never sends
:SOURce:FREQuency or :SYNChronization commands.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Optional

QUERIES = {
    "idn": "*IDN?",
    "status": ":SYSTem:PRINt?",          # full status report (multi-line)
    "log": ":DIAGnostic:LOG:PRINt?",     # event log (multi-line)
    "cont_oper": ":DIAGnostic:CONTinuous?",  # 1 while in continuous (locked) operation
}

# lenient parsers for the free-text status report; each returns a float or None
_PATTERNS = {
    "beam_current_ua": re.compile(r"beam\s*current[^0-9\-]*(-?\d+(?:\.\d+)?)", re.I),
    "cfield_ma": re.compile(r"c[- ]?field[^0-9\-]*(-?\d+(?:\.\d+)?)", re.I),
    "oven_temp_c": re.compile(r"oven[^0-9\-]*(-?\d+(?:\.\d+)?)", re.I),
    "internal_temp_c": re.compile(r"internal\s*temp[^0-9\-]*(-?\d+(?:\.\d+)?)", re.I),
    "supply_v": re.compile(r"supply[^0-9\-]*(-?\d+(?:\.\d+)?)", re.I),
}


@dataclass
class CesiumHealth:
    t: float
    idn: str = ""
    continuous_operation: Optional[bool] = None
    on_battery: Optional[bool] = None
    fields: dict = field(default_factory=dict)
    status_text: str = ""
    errors: list = field(default_factory=list)


def parse_status(text: str) -> dict:
    out = {}
    for key, pat in _PATTERNS.items():
        m = pat.search(text)
        if m:
            try:
                out[key] = float(m.group(1))
            except ValueError:
                pass
    low = text.lower()
    if "battery" in low:
        out["mentions_battery"] = True
    return out


class Cesium5071A:
    def __init__(self, port: str, baud: int = 9600, timeout: float = 3.0):
        import serial

        self.ser = serial.Serial(port, baud, timeout=timeout)

    def query(self, cmd: str, multiline_wait_s: float = 1.5) -> str:
        self.ser.reset_input_buffer()
        self.ser.write((cmd.strip() + "\r\n").encode("ascii"))
        time.sleep(multiline_wait_s)
        chunks = []
        while True:
            data = self.ser.read(4096)
            if not data:
                break
            chunks.append(data)
        return b"".join(chunks).decode("ascii", errors="replace").strip()

    def health(self) -> CesiumHealth:
        h = CesiumHealth(t=time.time())
        for name, cmd in QUERIES.items():
            try:
                resp = self.query(cmd, multiline_wait_s=0.5 if name in ("idn", "cont_oper") else 2.0)
            except Exception as exc:  # pragma: no cover - hardware path
                h.errors.append(f"{name}: {exc}")
                continue
            if name == "idn":
                h.idn = resp
            elif name == "status":
                h.status_text = resp
                h.fields.update(parse_status(resp))
            elif name == "cont_oper":
                h.continuous_operation = resp.strip().startswith("1")
        return h

    def close(self):
        self.ser.close()
