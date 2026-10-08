"""`greylock passport` — a visitor's personal time-travel certificate.

A visitor who spends Δt at the summit banks gΔh/c² · Δt of lead over everyone
who stayed at sea level.  It is small, it is real, and it is theirs: ~0.41 ns
for a night at Bascom Lodge, 12 cm of light.  The certificate states the
number, the physics, and the measured machine rate when one is available, and
is honest about what it is: proper time, not a metaphor.

The HTML version is a single self-contained file to print at the lodge.
"""
from __future__ import annotations

from datetime import datetime, timezone

from .config import Config
from .physics import gravitational_rate, gravitational_rate_sigma, light_metres, rate_to_ns_per_day


def _parse(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def certificate(cfg: Config, site_name: str, t_in: str, t_out: str,
                name: str = "A Time Traveller", measured_ns_day: float | None = None,
                measured_sigma: float | None = None) -> dict:
    site = cfg.site(site_name)
    ref = cfg.reference
    a, b = _parse(t_in), _parse(t_out)
    hours = (b - a).total_seconds() / 3600.0
    if hours <= 0:
        raise ValueError("departure must be after arrival")
    rate = rate_to_ns_per_day(gravitational_rate(site, ref))
    sigma = rate_to_ns_per_day(gravitational_rate_sigma(site, ref))
    banked = rate * hours / 24.0
    banked_sigma = sigma * hours / 24.0
    use_measured = measured_ns_day is not None
    if use_measured:
        banked_m = measured_ns_day * hours / 24.0
        banked_m_sigma = (measured_sigma or 0.0) * hours / 24.0
    return {
        "name": name, "site": site.name, "reference": ref.name,
        "arrived_utc": a.strftime("%Y-%m-%d %H:%M"), "departed_utc": b.strftime("%Y-%m-%d %H:%M"),
        "hours": hours, "delta_h_m": site.height_m - ref.height_m,
        "rate_ns_day": rate, "rate_sigma": sigma,
        "banked_ns": banked, "banked_sigma_ns": banked_sigma,
        "banked_light_mm": light_metres(banked) * 1000.0,
        "measured_banked_ns": banked_m if use_measured else None,
        "measured_banked_sigma_ns": banked_m_sigma if use_measured else None,
    }


def text(cert: dict) -> str:
    lines = [
        "CERTIFICATE OF FORWARD TIME TRAVEL",
        "-" * 42,
        f"{cert['name']}",
        f"stayed at {cert['site']} ({cert['delta_h_m']:+.0f} m above {cert['reference']})",
        f"from {cert['arrived_utc']} to {cert['departed_utc']} UTC — {cert['hours']:.1f} hours.",
        "",
        f"At gΔh/c² = {cert['rate_ns_day']:.2f} ± {cert['rate_sigma']:.2f} ns/day, the bearer's",
        f"proper time ran ahead of sea-level time by",
        "",
        f"    {cert['banked_ns']:.3f} ± {cert['banked_sigma_ns']:.3f} nanoseconds",
        f"    ({cert['banked_light_mm']:.0f} mm of light travel)",
        "",
    ]
    if cert.get("measured_banked_ns") is not None:
        lines.append(f"The machine's measured rate over this season gives "
                     f"{cert['measured_banked_ns']:.3f} ± {cert['measured_banked_sigma_ns']:.3f} ns.")
        lines.append("")
    lines += [
        "This is proper time, per the general theory of relativity (verified on",
        "this mountain class of experiment since 1971), not a metaphor.  The bearer",
        "is, permanently, this much further into the future than those who stayed",
        "at sea level.  Effect is cumulative with subsequent visits.",
    ]
    return "\n".join(lines)


def html(cert: dict) -> str:
    m = ""
    if cert.get("measured_banked_ns") is not None:
        m = (f"<p class='m'>Measured machine rate this season: "
             f"{cert['measured_banked_ns']:.3f} ± {cert['measured_banked_sigma_ns']:.3f} ns.</p>")
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>Certificate of Forward Time Travel</title>
<style>
 body{{font-family:Georgia,serif;max-width:640px;margin:40px auto;color:#222;
      border:3px double #8a6d1a;padding:40px;text-align:center}}
 h1{{font-size:20px;letter-spacing:3px;color:#8a6d1a}}
 .big{{font-size:34px;margin:18px 0;color:#1a3a6d}}
 .small{{font-size:13px;color:#555;text-align:left;margin-top:28px}}
 .m{{color:#1a6d3a}}
</style></head><body>
<h1>CERTIFICATE OF FORWARD TIME TRAVEL</h1>
<p><b>{cert['name']}</b><br>
stayed at <b>{cert['site']}</b> ({cert['delta_h_m']:+.0f} m above {cert['reference']})<br>
{cert['arrived_utc']} → {cert['departed_utc']} UTC ({cert['hours']:.1f} h)</p>
<p>at gΔh/c² = {cert['rate_ns_day']:.2f} ± {cert['rate_sigma']:.2f} ns/day, banking</p>
<div class="big">{cert['banked_ns']:.3f} ns</div>
<p>({cert['banked_light_mm']:.0f} mm of light travel) of lead over sea-level time</p>
{m}
<p class="small">This is proper time, per the general theory of relativity, measured on
clocks of this kind since 1971 — not a metaphor.  The bearer is, permanently, this much
further into the future than those who stayed at sea level.  Cumulative with subsequent
visits.  Greylock Time Machine · greylock v0.2</p>
</body></html>"""
