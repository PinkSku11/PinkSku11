"""Case environment: temperature, pressure, humidity from a BME280 on the Pi's I²C bus.

Why it matters: the cesium clock's frequency moves by a few parts in 10¹⁵ per
degree.  The thermostat holds the case at the set point; this logs how well.
Humidity is logged for the dew-point check on a cold summit.

Uses the `smbus2` package if present; otherwise returns None and the acquisition
daemon records that no sensor was found (never a fake number).
"""
from __future__ import annotations

from typing import Optional


class Bme280:
    ADDR = 0x76

    def __init__(self, bus: int = 1, addr: int = ADDR):
        from smbus2 import SMBus  # optional dependency

        self.bus = SMBus(bus)
        self.addr = addr
        self._cal = self._read_calibration()
        # humidity oversampling x1, then mode normal, temp/press oversampling x1
        self.bus.write_byte_data(self.addr, 0xF2, 0x01)
        self.bus.write_byte_data(self.addr, 0xF4, 0x27)

    def _read_calibration(self):
        b = self.bus
        a = self.addr
        c = b.read_i2c_block_data(a, 0x88, 26) + b.read_i2c_block_data(a, 0xE1, 7)

        def u16(i):
            return c[i] | (c[i + 1] << 8)

        def s16(i):
            v = u16(i)
            return v - 65536 if v > 32767 else v

        cal = {
            "T1": u16(0), "T2": s16(2), "T3": s16(4),
            "P1": u16(6), "P2": s16(8), "P3": s16(10), "P4": s16(12), "P5": s16(14),
            "P6": s16(16), "P7": s16(18), "P8": s16(20), "P9": s16(22),
            "H1": c[25], "H2": (c[26] | (c[27] << 8)), "H3": c[28],
            "H4": (c[29] << 4) | (c[30] & 0x0F), "H5": (c[31] << 4) | (c[30] >> 4), "H6": c[32],
        }
        if cal["H2"] > 32767:
            cal["H2"] -= 65536
        if cal["H6"] > 127:
            cal["H6"] -= 256
        return cal

    def read(self) -> tuple[float, float, float]:
        """(temperature °C, pressure hPa, humidity %RH) — Bosch's reference integer maths."""
        d = self.bus.read_i2c_block_data(self.addr, 0xF7, 8)
        adc_p = (d[0] << 12) | (d[1] << 4) | (d[2] >> 4)
        adc_t = (d[3] << 12) | (d[4] << 4) | (d[5] >> 4)
        adc_h = (d[6] << 8) | d[7]
        c = self._cal
        var1 = (adc_t / 16384.0 - c["T1"] / 1024.0) * c["T2"]
        var2 = ((adc_t / 131072.0 - c["T1"] / 8192.0) ** 2) * c["T3"]
        t_fine = var1 + var2
        temp = t_fine / 5120.0
        var1 = t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * c["P6"] / 32768.0
        var2 = var2 + var1 * c["P5"] * 2.0
        var2 = var2 / 4.0 + c["P4"] * 65536.0
        var1 = (c["P3"] * var1 * var1 / 524288.0 + c["P2"] * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * c["P1"]
        press = 0.0
        if var1 != 0:
            p = 1048576.0 - adc_p
            p = (p - var2 / 4096.0) * 6250.0 / var1
            var1 = c["P9"] * p * p / 2147483648.0
            var2 = p * c["P8"] / 32768.0
            press = (p + (var1 + var2 + c["P7"]) / 16.0) / 100.0
        h = t_fine - 76800.0
        h = (adc_h - (c["H4"] * 64.0 + c["H5"] / 16384.0 * h)) * (
            c["H2"] / 65536.0 * (1.0 + c["H6"] / 67108864.0 * h * (1.0 + c["H3"] / 67108864.0 * h)))
        h = h * (1.0 - c["H1"] * h / 524288.0)
        hum = max(0.0, min(100.0, h))
        return temp, press, hum


def open_sensor() -> Optional[Bme280]:
    try:
        return Bme280()
    except Exception:
        return None


def dew_point_c(temp_c: float, rh: float) -> float:
    """Magnus formula; the case must stay above this."""
    import math

    a, b = 17.62, 243.12
    g = a * temp_c / (b + temp_c) + math.log(max(rh, 0.1) / 100.0)
    return b * g / (a - g)
