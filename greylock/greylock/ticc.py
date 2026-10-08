"""TAPR TICC timestamping counter — serial reader and line parser.

Wiring for the time machine:
    TICC REF IN  <- cesium 10 MHz        (the counter ticks on cesium time)
    TICC chA     <- cesium 1 PPS
    TICC chB     <- GNSS receiver TIMEPULSE (1 PPS)
    USB          -> Raspberry Pi

In *Time Interval* mode the TICC prints one line per pulse pair, e.g.
    "   0.000000012345 TI(A->B)"
which is the interval from the cesium pulse to the GNSS pulse, in seconds.
In *Timestamp* mode it prints one line per pulse on each channel, e.g.
    "  17.123456789012 chA"
    "  17.123456801357 chB"
and the interval is formed here by pairing each chA with the next chB.

The parser accepts both, so the TICC can be left in whichever mode it is in.
Sign convention used throughout the package:
    ti_ns = (cesium 1PPS time) - (GNSS 1PPS time)   in nanoseconds
so TI(A->B) = tB - tA is negated.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterator, Optional

_LINE = re.compile(r"^\s*(-?\d+\.\d+)\s+(chA|chB|TI\(A->B\)|TI\(B->A\))\s*$")


@dataclass
class TiccEvent:
    kind: str          # 'chA', 'chB', 'TI(A->B)', 'TI(B->A)'
    seconds: float     # timestamp (channel modes) or interval (TI modes)


def parse_line(line: str) -> Optional[TiccEvent]:
    m = _LINE.match(line)
    if not m:
        return None
    return TiccEvent(kind=m.group(2), seconds=float(m.group(1)))


class TiccPairer:
    """Turns a stream of TiccEvents into ti_ns = tA - tB values."""

    def __init__(self):
        self._last_a: Optional[float] = None

    def feed(self, ev: TiccEvent) -> Optional[float]:
        if ev.kind == "TI(A->B)":
            return -ev.seconds * 1e9
        if ev.kind == "TI(B->A)":
            return ev.seconds * 1e9
        if ev.kind == "chA":
            self._last_a = ev.seconds
            return None
        if ev.kind == "chB" and self._last_a is not None:
            ti = (self._last_a - ev.seconds) * 1e9
            self._last_a = None
            return ti
        return None


def read_serial(port: str, baud: int = 115200) -> Iterator[float]:
    """Yield ti_ns values from a live TICC.  Requires pyserial."""
    import serial  # imported here so the rest of the package works without it

    pairer = TiccPairer()
    with serial.Serial(port, baud, timeout=5) as ser:
        while True:
            raw = ser.readline().decode("ascii", errors="replace")
            if not raw:
                continue
            ev = parse_line(raw)
            if ev is None:
                continue
            ti = pairer.feed(ev)
            if ti is not None:
                yield ti
