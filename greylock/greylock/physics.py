"""Relativistic bookkeeping for the time machine.

Everything here is weak-field general relativity on a rotating Earth, written
so that the numbers can be checked by hand:

    rate  =  dτ_site / dτ_geoid - 1  =  (Φ(site) - Φ(geoid)) / c²  -  v² / (2c²)

where Φ is the gravity potential (gravity + centrifugal, i.e. the geopotential)
above the geoid.  GPS time runs at the geoid rate by construction, so a clock at
height h compared against GPS time shows exactly this rate (plus the clock's own
intrinsic frequency offset, which the analysis calibrates away).

Heights are orthometric (above mean sea level / the geoid), e.g. NAVD88 values.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

C = 299_792_458.0            # m/s
C2 = C * C
FREE_AIR = 3.086e-6          # m/s² per metre of height (free-air gradient)
NS_PER_DAY = 86400.0 * 1e9   # ns in a day, for converting fractional rates


@dataclass(frozen=True)
class Site:
    name: str
    lat_deg: float
    lon_deg: float
    height_m: float              # orthometric height above the geoid
    height_sigma_m: float = 2.0  # how well we know it
    reference: bool = False      # the sea-level / home station?


def normal_gravity(lat_deg: float) -> float:
    """WGS84 normal gravity on the ellipsoid (Somigliana), m/s²."""
    s2 = math.sin(math.radians(lat_deg)) ** 2
    return 9.7803253359 * (1.0 + 0.00193185265241 * s2) / math.sqrt(1.0 - 0.00669437999014 * s2)


def gravity(lat_deg: float, h_m: float) -> float:
    """Normal gravity at height h (free-air corrected), m/s²."""
    return normal_gravity(lat_deg) - FREE_AIR * h_m


def geopotential_above_geoid(lat_deg: float, h_m: float) -> float:
    """∫₀ʰ g(z) dz, J/kg — the geopotential number of a point above the geoid."""
    return normal_gravity(lat_deg) * h_m - 0.5 * FREE_AIR * h_m * h_m


def gravitational_rate(site: Site, reference: Site) -> float:
    """Fractional rate of a clock at `site` relative to one at `reference` (both at rest).

    Positive means the clock at `site` runs fast.  The centrifugal term is already
    inside the geopotential (the geoid is an equipotential of gravity + rotation),
    so no separate Earth-rotation term appears for clocks at rest.
    """
    dphi = geopotential_above_geoid(site.lat_deg, site.height_m) - geopotential_above_geoid(
        reference.lat_deg, reference.height_m
    )
    return dphi / C2


def gravitational_rate_sigma(site: Site, reference: Site, model_frac: float = 1e-3) -> float:
    """1σ uncertainty of the predicted rate: height errors plus a model allowance."""
    g = gravity(site.lat_deg, 0.5 * site.height_m)
    sig_h = math.hypot(site.height_sigma_m, reference.height_sigma_m)
    sig_from_h = g * sig_h / C2
    rate = abs(gravitational_rate(site, reference))
    return math.hypot(sig_from_h, model_frac * rate)


def velocity_rate(speed_m_s: float) -> float:
    """Second-order Doppler: a moving clock runs slow by v²/2c² (negative rate)."""
    return -(speed_m_s ** 2) / (2.0 * C2)


def sagnac_rate(speed_east_m_s: float, lat_deg: float) -> float:
    """Sagnac term for a clock moving east (negative) / west (positive) relative to the
    rotating Earth, compared with a ground clock: -R Ω v_east cosφ / c²."""
    R, OMEGA = 6_371_000.0, 7.2921e-5
    return -(R * OMEGA * math.cos(math.radians(lat_deg)) * speed_east_m_s) / C2


def rate_to_ns_per_day(rate: float) -> float:
    return rate * NS_PER_DAY


def ns_per_day_to_rate(ns_per_day: float) -> float:
    return ns_per_day / NS_PER_DAY


def transport_offset_ns(track, reference: Site) -> float:
    """Proper-time offset accumulated by a clock carried along `track`, relative to a
    clock at rest at `reference`.

    `track` is an iterable of (t_unix_s, lat_deg, h_m, speed_m_s, speed_east_m_s);
    the integral is a sum of rate × Δt over consecutive samples.  Returns nanoseconds.
    This is what the GNSS log of the drive to the summit feeds into: the ~0.3 ns of
    the road trip, computed rather than assumed.
    """
    total = 0.0
    prev = None
    for sample in track:
        t, lat, h, v, v_east = sample
        if prev is not None:
            dt = t - prev[0]
            site = Site("moving", lat, 0.0, h)
            r = gravitational_rate(site, reference) + velocity_rate(v) + sagnac_rate(v_east, lat)
            total += r * dt
        prev = sample
    return total * 1e9


def light_metres(ns: float) -> float:
    """How far light travels in `ns` nanoseconds — the public-friendly unit."""
    return C * ns * 1e-9


# ---------------------------------------------------------------------------
# The two stations of the Massachusetts machine, for convenience and for tests.
CAMBRIDGE = Site("cambridge", 42.360, -71.092, 6.0, 2.0, reference=True)
GREYLOCK = Site("greylock_summit", 42.637, -73.166, 1063.4, 1.0)


if __name__ == "__main__":  # a quick look at the headline numbers
    r = gravitational_rate(GREYLOCK, CAMBRIDGE)
    s = gravitational_rate_sigma(GREYLOCK, CAMBRIDGE)
    print(f"Greylock vs Cambridge: {r:.4e}  = {rate_to_ns_per_day(r):.2f} ± {rate_to_ns_per_day(s):.2f} ns/day")
    print(f"per week {rate_to_ns_per_day(r)*7:.1f} ns, per 160-day season {rate_to_ns_per_day(r)*160/1000:.2f} µs")
    print(f"10 ns of lead is {light_metres(10):.1f} m of light travel")
