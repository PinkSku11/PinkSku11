import struct

from greylock import ticc, ublox


def test_ticc_time_interval_lines():
    ev = ticc.parse_line("   0.000000012345 TI(A->B)")
    assert ev.kind == "TI(A->B)" and abs(ev.seconds - 1.2345e-8) < 1e-15
    p = ticc.TiccPairer()
    # TI(A->B) = tB - tA = +12.345 ns  ->  ti = tA - tB = -12.345 ns
    assert abs(p.feed(ev) + 12.345) < 1e-6


def test_ticc_timestamp_pairing():
    p = ticc.TiccPairer()
    assert p.feed(ticc.parse_line("  17.123456789012 chA")) is None
    ti = p.feed(ticc.parse_line("  17.123456801357 chB"))
    assert abs(ti - (-12.345)) < 1e-3
    assert ticc.parse_line("garbage line") is None
    assert ticc.parse_line("# TICC v1.4 timestamp mode") is None


def _tim_tp_payload(tow_ms=1000, sub=0, qerr=-1234, week=2400, flags=0x03, ref=0):
    return struct.pack("<IIiHBB", tow_ms, sub, qerr, week, flags, ref)


def test_ubx_frame_roundtrip_and_resync():
    payload = _tim_tp_payload()
    frame = ublox.build_frame(*ublox.CLS_ID_TIM_TP, payload)
    parser = ublox.UbxParser()
    # junk, then a frame split across two feeds, then a corrupted frame, then a good one
    out = list(parser.feed(b"\x00\x01junk" + frame[:5]))
    assert out == []
    out = list(parser.feed(frame[5:]))
    assert len(out) == 1
    cls, mid, pl = out[0]
    tp = ublox.decode(cls, mid, pl)
    assert isinstance(tp, ublox.TimTp) and tp.qerr_ps == -1234 and tp.week == 2400
    bad = bytearray(frame)
    bad[10] ^= 0xFF
    out = list(parser.feed(bytes(bad) + frame))
    assert len(out) == 1


def test_nav_pvt_decode():
    fmt = "<IHBBBBBBIiBBBBiiiiIIiiii"
    payload = struct.pack(fmt, 123000, 2027, 6, 1, 12, 0, 0, 0x07, 15, -50, 3, 0x01, 0, 14,
                          -731660000, 426370000, 1090000, 1063400, 1200, 1800, 10, -20, 0, 22) + bytes(92 - 64)
    pvt = ublox.decode(*ublox.CLS_ID_NAV_PVT, payload)
    assert isinstance(pvt, ublox.NavPvt)
    assert pvt.fix_type == 3 and pvt.num_sv == 14
    assert abs(pvt.lat_deg - 42.637) < 1e-6 and abs(pvt.h_msl_m - 1063.4) < 1e-6
    assert abs(pvt.vel_e_m_s + 0.02) < 1e-9 and abs(pvt.g_speed_m_s - 0.022) < 1e-9
