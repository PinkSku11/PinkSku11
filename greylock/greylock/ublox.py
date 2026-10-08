"""u-blox UBX protocol — frame parser and the two messages the machine needs.

    UBX-TIM-TP  (0x0D 0x01)  time-pulse info: GPS week/TOW of the *next* pulse and
                             qErr, the quantisation error of that pulse in picoseconds.
                             Adding it back removes the receiver's clock-granularity
                             sawtooth from each 1 PPS measurement.
    UBX-NAV-PVT (0x01 0x07)  position/velocity/time: fix type, satellites, lat/lon/
                             height, speed — logged for the transport integral and
                             as a health check that the antenna sees the sky.

Receiver setup (once, with u-center or ubxtool): enable TIM-TP and NAV-PVT at 1 Hz,
survey-in then fixed position ("timing mode"), TIMEPULSE locked to GPS time (or
Galileo, see the cross-check idea in the README).  Log the raw UBX stream to a
daily file as well (RXM-RAWX, RXM-SFRBX) so that RTKLIB's convbin can make RINEX
for precise-point-positioning afterwards.

Sign of qErr: conventions differ between firmware notes and scripts.  The package
applies   ti_corrected = ti_measured + qerr_sign * qErr   with qerr_sign from the
station config (default +1).  The zero-baseline test tells you which is right:
the corrected per-pulse jitter must shrink; if it grows, flip the sign.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Iterator, Optional

SYNC = b"\xb5\x62"
CLS_ID_TIM_TP = (0x0D, 0x01)
CLS_ID_NAV_PVT = (0x01, 0x07)


def checksum(payload_with_header: bytes) -> tuple[int, int]:
    ck_a = ck_b = 0
    for b in payload_with_header:
        ck_a = (ck_a + b) & 0xFF
        ck_b = (ck_b + ck_a) & 0xFF
    return ck_a, ck_b


def build_frame(cls: int, msg_id: int, payload: bytes) -> bytes:
    body = bytes([cls, msg_id]) + struct.pack("<H", len(payload)) + payload
    a, b = checksum(body)
    return SYNC + body + bytes([a, b])


@dataclass
class TimTp:
    tow_ms: int
    tow_sub_ms: int      # units of 2^-32 ms
    qerr_ps: int
    week: int
    flags: int
    ref_info: int

    @property
    def tow_s(self) -> float:
        return self.tow_ms * 1e-3 + self.tow_sub_ms * (2 ** -32) * 1e-3


@dataclass
class NavPvt:
    itow_ms: int
    year: int
    month: int
    day: int
    hour: int
    minute: int
    second: int
    valid: int
    t_acc_ns: int
    nano: int
    fix_type: int
    flags: int
    flags2: int
    num_sv: int
    lon_deg: float
    lat_deg: float
    height_m: float       # above ellipsoid
    h_msl_m: float        # above mean sea level
    h_acc_m: float
    v_acc_m: float
    vel_n_m_s: float
    vel_e_m_s: float
    vel_d_m_s: float
    g_speed_m_s: float


def parse_tim_tp(payload: bytes) -> TimTp:
    tow_ms, tow_sub, qerr, week, flags, ref = struct.unpack("<IIiHBB", payload[:16])
    return TimTp(tow_ms, tow_sub, qerr, week, flags, ref)


_NAV_PVT_FMT = "<IHBBBBBBIiBBBBiiiiIIiiii"   # the first 64 of NAV-PVT's 92 bytes
NAV_PVT_MIN_LEN = struct.calcsize(_NAV_PVT_FMT)


def parse_nav_pvt(payload: bytes) -> NavPvt:
    (itow, year, month, day, hour, minute, second, valid, tacc, nano, fix, flags, flags2,
     numsv, lon, lat, height, hmsl, hacc, vacc, veln, vele, veld, gspeed) = struct.unpack(
        _NAV_PVT_FMT, payload[:NAV_PVT_MIN_LEN])
    return NavPvt(itow, year, month, day, hour, minute, second, valid, tacc, nano, fix, flags,
                  flags2, numsv, lon * 1e-7, lat * 1e-7, height * 1e-3, hmsl * 1e-3,
                  hacc * 1e-3, vacc * 1e-3, veln * 1e-3, vele * 1e-3, veld * 1e-3, gspeed * 1e-3)


class UbxParser:
    """Feed bytes in any chunking; get back (cls, id, payload) tuples."""

    def __init__(self):
        self._buf = bytearray()

    def feed(self, data: bytes) -> Iterator[tuple[int, int, bytes]]:
        self._buf.extend(data)
        while True:
            i = self._buf.find(SYNC)
            if i < 0:
                self._buf.clear()
                return
            if i > 0:
                del self._buf[:i]
            if len(self._buf) < 8:
                return
            cls, msg_id = self._buf[2], self._buf[3]
            length = struct.unpack("<H", bytes(self._buf[4:6]))[0]
            end = 6 + length + 2
            if len(self._buf) < end:
                return
            body = bytes(self._buf[2:6 + length])
            a, b = checksum(body)
            if (a, b) == (self._buf[6 + length], self._buf[7 + length]):
                yield cls, msg_id, bytes(self._buf[6:6 + length])
                del self._buf[:end]
            else:
                del self._buf[:2]   # bad checksum: skip this sync and resynchronise


def decode(cls: int, msg_id: int, payload: bytes) -> Optional[object]:
    if (cls, msg_id) == CLS_ID_TIM_TP and len(payload) >= 16:
        return parse_tim_tp(payload)
    if (cls, msg_id) == CLS_ID_NAV_PVT and len(payload) >= NAV_PVT_MIN_LEN:
        return parse_nav_pvt(payload)
    return None


def read_serial(port: str, baud: int = 38400, raw_log=None) -> Iterator[object]:
    """Yield decoded TimTp / NavPvt objects from a live receiver; optionally tee the
    raw bytes to `raw_log` (a binary file object) for RINEX conversion later."""
    import serial

    parser = UbxParser()
    with serial.Serial(port, baud, timeout=2) as ser:
        while True:
            chunk = ser.read(512)
            if not chunk:
                continue
            if raw_log is not None:
                raw_log.write(chunk)
            for cls, msg_id, payload in parser.feed(chunk):
                obj = decode(cls, msg_id, payload)
                if obj is not None:
                    yield obj
