"""Station configuration (TOML).  See station.example.toml for every key."""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from .physics import Site

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore


@dataclass
class Config:
    raw: dict
    sites: dict[str, Site]
    reference_site: str
    path: Path | None = None

    @property
    def station(self) -> dict:
        return self.raw.get("station", {})

    @property
    def hardware(self) -> dict:
        return self.raw.get("hardware", {})

    @property
    def analysis(self) -> dict:
        return self.raw.get("analysis", {})

    @property
    def sim(self) -> dict:
        return self.raw.get("sim", {})

    @property
    def ledger_dir(self) -> Path:
        d = self.station.get("ledger_dir", "data/ledger")
        base = self.path.parent if self.path else Path(".")
        p = Path(d)
        return p if p.is_absolute() else base / p

    def site(self, name: str) -> Site:
        return self.sites[name]

    @property
    def reference(self) -> Site:
        return self.sites[self.reference_site]


def load(path: str | Path) -> Config:
    path = Path(path)
    with path.open("rb") as fh:
        raw = tomllib.load(fh)
    sites: dict[str, Site] = {}
    ref = None
    for name, s in raw.get("sites", {}).items():
        site = Site(
            name=name,
            lat_deg=float(s["lat"]),
            lon_deg=float(s.get("lon", 0.0)),
            height_m=float(s["height_m"]),
            height_sigma_m=float(s.get("height_sigma_m", 2.0)),
            reference=bool(s.get("reference", False)),
        )
        sites[name] = site
        if site.reference:
            ref = name
    ref = raw.get("analysis", {}).get("reference_site", ref)
    if ref is None or ref not in sites:
        raise ValueError("config needs one site marked reference = true (or analysis.reference_site)")
    return Config(raw=raw, sites=sites, reference_site=ref, path=path)


def default_config_dict() -> dict:
    return {
        "station": {"name": "summit", "site": "greylock_summit", "clock": "CS1",
                    "ledger_dir": "data/ledger", "cadence_s": 1},
        "hardware": {"ticc_port": "/dev/ttyACM0", "ticc_baud": 115200,
                     "ublox_port": "/dev/ttyUSB0", "ublox_baud": 38400, "ublox_raw_log": True,
                     "cesium_port": "/dev/ttyUSB1", "cesium_health_every_s": 600, "qerr_sign": 1},
        "sites": {
            "cambridge": {"lat": 42.360, "lon": -71.092, "height_m": 6.0, "height_sigma_m": 2.0, "reference": True},
            "greylock_summit": {"lat": 42.637, "lon": -73.166, "height_m": 1063.4, "height_sigma_m": 1.0},
        },
        "analysis": {"reference_site": "cambridge", "min_calibration_days": 5},
    }
