# greylock — software for a real (forward) time machine

A cesium clock on the summit of Mount Greylock, compared continuously with GPS
time, runs fast by gΔh/c² = 1.15 × 10⁻¹³: ten nanoseconds a day, 1.6 microseconds
over a May-to-October season.  This package is everything around the clock.

```
                 summit station (Raspberry Pi)                  home station (Pi)
  ┌──────────┐ 1PPS ┌──────────┐                           ┌──────────┐
  │ 5071A    ├─────►│ TAPR     │ USB   ┌────────────┐      │ same kit │
  │ cesium   │10MHz │ TICC     ├──────►│ acquire.py │      │ at sea   │
  │ clock    ├─────►│ counter  │       │  ledger    │      │ level    │
  └────┬─────┘      └────▲─────┘       │  (hash-    │      └────┬─────┘
       │ RS-232          │ 1PPS        │   chained) │           │
       │ health     ┌────┴─────┐ UBX   │            │           │
       └───────────►│ u-blox   ├──────►│            │           │
                    │ ZED-F9T  │       └─────┬──────┘           │
                    └──────────┘             │ jsonl            │ jsonl
                                             ▼                  ▼
                                   ┌──────────────────────────────────┐
                                   │ analysis.py  rate ± σ, lead, σ   │
                                   │ display.py   readout.html (live) │
                                   └──────────────────────────────────┘
```

## What kind of code

| Layer | Language | Why |
|---|---|---|
| drivers (`ticc.py`, `ublox.py`, `cesium.py`, `env.py`) | Python 3.11 + pyserial / smbus2 | serial protocols, small, testable pure parsers |
| digital twin (`clockmodel.py`, `sim.py`) | Python + numpy | the same ledger format as the hardware, so the pipeline is built before the clock arrives |
| acquisition (`acquire.py`) | Python, threads, systemd | one process per station; restarts resume the same hash chain |
| ledger (`ledger.py`) | Python, SHA-256, JSON lines | append-only, tamper-evident, daily public commitments |
| analysis (`analysis.py`, `physics.py`) | Python + numpy | weighted least squares on daily means; weak-field GR on a rotating Earth |
| readout (`display.py`, `readout.html`) | Python stdlib HTTP + vanilla HTML/JS/SVG | no external resources, runs on the Pi, restyle freely |
| time on the Pi | chrony + the GNSS PPS (`deploy/chrony.conf`) | record timestamps good to microseconds |
| precise link (optional) | RTKLIB `convbin` + a PPP service (C, external) | raw UBX → RINEX → receiver clock vs GPS time at 0.1–0.3 ns |
| physical display (optional) | C++ (Arduino) on an ESP32, `firmware/` | reads `/api/state`, shows the lead on Nixies / 7-segment |

Nothing here touches the clock's physics.  The 5071A's own firmware keeps the
second; the TICC's open firmware (TAPR, Arduino C++) timestamps pulses; the
u-blox firmware tells GPS time.  This code reads them, keeps an honest record,
and does the arithmetic.

## Run it today, with no hardware

```bash
pip install -e ".[dev,plots]"
greylock init station.toml          # example config: Cambridge 6 m ↔ Greylock summit 1,063 m
greylock predict station.toml       # the number to pre-register: +9.96 ± 0.02 ns/day
greylock simulate station.toml      # a 2027 season: two clocks, one swap, 60 s records (~30 s to run)
greylock analyse station.toml --json data/state.json --plot data/lead.png
greylock verify station.toml        # every ledger's hash chain
greylock commit station.toml        # the daily commitment hashes to post
greylock serve station.toml         # the readout at http://localhost:8080/
greylock acquire station.toml --simulate   # a live digital twin writing records at 1 Hz
pytest                              # 30 tests: parsers, chain tampering, rate recovery, ops
```

And the v0.2 operations layer, all of which runs on the simulation too:

```bash
greylock doctor station.toml --live # bring-up self-test: config, disk, chrony, ports, and
                                    # (--live) the TICC, receiver and 5071A over serial
greylock zerobase station.toml      # decides qerr_sign from data (README step 5, automated)
greylock export station.toml --what daily|lead|segments|raw    # CSVs for plots and papers
greylock report station.toml        # the operator's daily report: gaps, scatter, thermostat,
                                    # chain status, commitments, the current verdict
greylock report station.toml --post # the ≤280-char public line with the commitment hash
greylock passport station.toml --arrive 2027-07-04T15:00Z --depart 2027-07-06T15:00Z \
    --name "A Visitor" --html cert.html    # a printable certificate: 48 h = 19.93 ns banked
greylock transport station.toml     # the drive's proper-time integral from the logged track
greylock rinex station.toml         # raw UBX → RINEX via RTKLIB convbin, for PPP later
```

`serve` also exposes `/metrics` (Prometheus format), `/api/daily.csv` and `/api/report`,
so any monitoring stack can watch the machine.  The acquisition daemon is a proper
citizen now: systemd `Type=notify` with a watchdog, clean SIGTERM shutdown (the chain
resumes), daily raw-log rollover, a low-disk cutoff for the raw stream (never for the
measurement records), and event records in the ledger for pulse gaps and mains
transitions — anomalies are part of the history, not lost in a syslog.

Simulated result (spec-like noise): `+9.93 ± 0.50 ns/day vs predicted +9.96 ± 0.02
(−0.1σ); detection 20σ over 160 deployment days; lead 1,585 ns measured, 1,574
predicted (475 m of light)`.  The ±0.5 is honest: it includes the clock's flicker
floor twice (calibration and deployment are separate realisations) and half of
the before/after calibration disagreement.  The link noise alone would give ±0.03.

## Run it with the hardware

1. **Wire**: TICC chA ← cesium 1 PPS; chB ← receiver TIMEPULSE; TICC REF ← cesium 10 MHz
   (so the counter ticks on cesium time); TICC and receiver by USB to the Pi; the
   5071A's RS-232 to a USB-serial adapter (health polling only — the package never
   sends frequency or synchronisation commands).  Equal-length, shielded PPS cables,
   ferrites at both ends.  Same compass orientation of the clock case at both stations.
2. **Receiver** (once, with u-center/ubxtool): survey-in, then fixed position (timing
   mode); TIM-TP and NAV-PVT at 1 Hz; RXM-RAWX + RXM-SFRBX for the raw log.
3. **Pi time**: `deploy/chrony.conf` disciplines the Pi's clock from the PPS so record
   timestamps are right to microseconds; `deploy/greylock-acquire.service` runs the
   daemon under systemd and restarts it (the ledger chain resumes).
4. **Config**: copy `station.example.toml`; the summit copy says `site = "greylock_summit"`,
   the home copy says `site = "cambridge"`; set `clock` to the unit's label and edit it
   when clocks are swapped.  The analysis reads both stations' ledgers from one directory
   (rsync the summit's to the home machine, or run the analysis where both land).
5. **Zero-baseline test** (home, before the season): two receivers on one antenna through a
   splitter, or one receiver and the clock for two days — the corrected per-pulse jitter
   must shrink when `qerr_sign` is right; if it grows, flip the sign.  This also measures
   the link's own floor.
6. **Calibrate**: ≥ 5 days (better 10–14) with the clock at the reference site before and
   after each deployment; `min_calibration_days` enforces the minimum.
7. **Commit**: post each day's line of `*-commitments.txt` publicly the day it closes.

## The measurement, in one paragraph

Every second the TICC reports ti = (cesium pulse) − (GPS pulse) on the cesium's time
base; the receiver's reported quantisation error is added back; a day's values are
reduced to a median and a robust σ; each clock's history is cut into segments at one
site; the slope at the reference site is the clock's own rate against GPS time
(intrinsic offset plus the tiny potential of the home station); the slope at the
summit minus that is the measured gravitational rate; the prediction is the
geopotential difference over c², with the free-air gradient and the WGS84 latitude
dependence of g, and the error bar is the two fit errors, the clock's floor and the
before/after calibration spread in quadrature.  The lead on the display is the
deployment data with the clock's own rate removed, accumulated across swaps.

## Analysis honesty, v0.2 additions

The fits now clip gross per-pulse outliers (7 robust σ, count recorded in the ledger of
notes, never hidden), scan every segment's daily series for phase steps (reported for a
human decision, not averaged into the slope), and regress fit residuals against case
temperature — a significant coefficient times the temperature swing is named in the
segment notes as thermostat trouble.  `export --what segments` carries all of it.

## Roadmap (not built yet)

* `greylock ppp`: the RINEX half exists (`greylock rinex`); the PPP submission/parse half
  (CSRS-PPP or a local engine) → receiver-clock series at 0.1–0.3 ns, replacing the daily
  medians as the link.
* Galileo cross-check: the F9T can lock TIMEPULSE to Galileo system time; the same lead
  against an independent clock ensemble.
* The X bot itself — its daily payload already exists (`greylock report --post`).
* `firmware/futurometer`: the ESP32 sketch for a Nixie/7-segment "futurometer" (included,
  untested on hardware), and a stepper "hand of the future" turning once per 100 ns.
