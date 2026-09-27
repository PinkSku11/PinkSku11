# The Greylock Time Machine — a real, buildable time machine for Massachusetts (design record)

*Time Travel project · design note, 27 September 2026, written in answer to "if I want to make a real physical time machine in Massachusetts, how would you design it?" Sibling of the Ooty Clock Run protocol (claude/ooty-clock-run-protocol.md), which is the one-shot road-trip version of the same physics. This is the permanent-installation version. Status: design only — nothing has been ordered, borrowed or asked for yet.*

## 0. Scope, in three sentences

Backward travel: no design exists, and not for want of engineering — every backward route in general relativity needs negative energy in quantities quantum theory forbids (Where Are the Time Travellers? has the ledger; the MIT and Tufts no-go results are Carroll–Farhi–Guth–Olum 1994 and Olum–Everett 2005). Forward travel: measured to 7 × 10⁻⁵ (Gravity Probe A, 1976), corrected in every GPS fix, and the machine that does it is a clock. So the only real time machine anyone can build today is a device whose contents provably age at a different rate from the reference station — and this is that device, sized for Massachusetts.

## 1. Why Massachusetts is the right state for it

Ramsey's separated-oscillatory-fields method (inside every cesium clock) — Harvard. Pound–Rebka 1959, first laboratory measurement of gravitational time dilation, 22.5 m tower, Jefferson Laboratory, Harvard. Gravity Probe A 1976, hydrogen maser on a Scout rocket to 10,000 km, Smithsonian Astrophysical Observatory, Cambridge (Vessot & Levine; agreement with GR to 70 ppm). The 5071A cesium clock — the clock that supplies the bulk of the data behind International Atomic Time, and the one Van Baak took up Mt Rainier — is manufactured by Microchip in Beverly, MA (also the newer 5071B). MIT Haystack Observatory (Westford) runs hydrogen masers for geodetic VLBI. The P-CTC "quantum time machine" theory is Seth Lloyd's (MIT). The backward no-go theorems are MIT and Tufts.

## 2. The machine

Two stations, one link, one display.

- Station S (the traveller): a 5071A cesium clock in a thermostatted, insulated case on the summit of Mount Greylock (1,063 m NAVD88, 42°38′14″N 73°09′58″W), inside Bascom Lodge or another powered summit building, with a GNSS timing receiver, a TICC counter and a Raspberry Pi logging clock-1PPS minus GNSS-1PPS every second.
- Station H (home): the same kit at sea level in Greater Boston (numbers below use Cambridge, 6 m); either a second (and third) 5071A, or GPS time alone as the reference — GPS time runs at the geoid rate by construction, so a single clock vs GPS shows the effect directly.
- Link: GNSS common-view / GPS-time comparison (daily means good to a few ns with ZED-F9T/NEO-F10T-class receivers; sub-ns with carrier-phase processing), plus physical transport of a clock (Van Baak's method) as the independent check.
- Display: "the summit is now X ns in Boston's future" — measured difference (intrinsic offset removed) beside the prediction, growing 10 ns/day.

### Headline numbers (g_mean 9.802 m/s², Δh 1,057 m)

- Rate: gΔh/c² = 1.153 × 10⁻¹³ → 9.96 ns/day; 19.9 ns per 48 h; 69.7 ns/week; 299 ns/30 days; 1.59 µs over a 160-day season (roads open ~16 May, close ~30 Oct).
- War Memorial Tower top adds 0.27 ns/day (not worth it).
- Each 3-hour drive leg: +0.35 ns gravity, −0.05 ns speed — negligible.
- For 1 µs of lead: 100 days at the summit. 1 ms: 275 years. 1 s: 275,000 years.
- Cross-check: per-metre rate 1.091 × 10⁻¹⁶ agrees with the Ooty protocol's 2.36 × 10⁻¹³ over 2,167 m.

### Modes and expected results

- Transport mode (Van Baak / Ooty design): 3 travelling 5071A (high-performance tubes) vs a home ensemble; 48 h stay → 20 ± 3 ns; 7 days → 70 ± 5 ns; 14 days → 139 ± 8 ns. Rates measured before and after by co-location on the TICC.
- Link mode (the permanent machine): with 3 ns daily scatter the slope is fixed to ±0.57 ns/day after a week, ±0.2 after two, ±0.06 after a month (statistical). The real limit is the co-location calibration of the summit clock's intrinsic offset (spec: two 5071As may differ by up to 5 × 10⁻¹³ = 43 ns/day; typically a few ns/day), so calibrate ≥10 days before and after, and swap S↔H once mid-season — the mean of the two configurations cancels the intrinsic offsets exactly.
- Prediction to be pre-registered: +9.96 ± 0.1 ns/day, summit clock ahead. Falsified (on a valid run) by a fitted rate outside ±1 ns/day of that after one month, or the wrong sign. A discrepancy is a fault in the run before a fault in Einstein (GP-A 7 × 10⁻⁵, Galileo 2.5 × 10⁻⁵, Skytree 9 × 10⁻⁵).

### Systematics

- Intrinsic frequency offsets: co-location + swap (above).
- Temperature: the 5071A's frequency-vs-temperature spec is at the 10⁻¹³ level across 0–50 °C, i.e. a few 10⁻¹⁴ (a few ns/day) per 10 °C — so hold both clocks at the same set point (25 ± 1 °C) in insulated cases with a PID-controlled heater/fan, and log temperature and pressure. The swap does not remove a shared temperature coefficient; thermostatting does.
- Magnetics/RF: the summit is a transmitter site (WAMC 90.3 FM, a TV repeater, NOAA weather radio, NoBARC's five repeaters and a 10 GHz beacon) — good for power, bad for interference; keep the clock in the lodge, away from the transmitter building and large iron; shielded coax and ferrites on 1PPS lines.
- Power: 5071A ≈ 50 W, 22–30 V DC input, 45-minute internal battery; LiFePO4 100 Ah + DC-DC for the drive (~20 h); UPS at both stations. A power loss invalidates a transport run.
- GNSS: fixed surveyed antenna position (timing mode), open sky, dual-band antenna; constant receiver/antenna delays cancel in a rate measurement.

## 3. Materials (excluding clocks)

| Item | Role | Approx. cost |
|---|---|---|
| Microchip 5071A cesium clock (×1 minimum, ×3 full) | the heart; cesium beam tube, mu-metal shields, quartz flywheel | loan / rent / used ~US$40–60k each (2026 listings: $42,550 used, $60,000 open-box /001) |
| GNSS timing receiver ×2 (u-blox ZED-F9T or NEO-F10T board) + dual-band timing antenna ×2 | the link | ~€150–300 per board; antennas $100–300 |
| TAPR TICC two-channel timestamping counter ×2 | 60 ps comparison of 1PPS signals | $249 each (in stock) |
| Raspberry Pi ×2, storage, 4G modem or lodge Wi-Fi | logging, upload, display | ~$200 |
| Insulated case (Pelican-class or rack case + polyisocyanurate foam), 12 V heater pad, fan, PID thermostat ×2 | thermal control | ~$500–700 |
| LiFePO4 12.8 V 100 Ah battery, 24 V DC-DC converter, charger; UPS ×2 | power for transport and outages | ~$700–900 |
| Shielded coax (LMR-240/RG-316), ferrites, 1PPS distribution, temperature/pressure loggers | plumbing | ~$300 |
| Display (tablet or e-ink panel) | the readout | ~$150–300 |
| Bascom Lodge nights for install, swap, retrieval (6–8 nights) | site | $155–210/night private, ~$50–55/bed bunk |
| Fuel, Boston–Greylock ×3 round trips (~215 km each way) | logistics | ~$300 |
| **Total without clocks** | | **≈ US$4,000–5,500 (≈ ₹3.3–4.6 lakh)** |

Minimum viable machine: one borrowed 5071A + one GNSS timing board + one TICC + one Pi, thermostatted case, 14 days of home calibration before and after: ≈ US$1,500 excluding the clock.

## 4. Clocks: where they can come from (loan first)

Microchip Frequency and Time Systems, Beverly MA (manufacturer — ask about a demo/loan/refurbished unit for a public science exhibit); MIT Haystack Observatory, Westford (masers and cesium for VLBI/geodesy); MIT Lincoln Laboratory, Lexington; Draper, Cambridge; Harvard–Smithsonian CfA (maser heritage); an MIT/Harvard/BU atomic-physics group (UROP-scale project); the time-nuts community (several members own 5071As and Van Baak's run is their founding legend). Buying used is a lab budget, not a student one, and used tubes may be near end of life.

## 5. Calendar and timeline

- 2026 season is over for a summit install (roads close 30 Oct 2026). First possible season: 2027 (roads ~mid-May, lodge late May, close ~30 Oct).
- Now → winter 2026–27: pre-register the prediction; write the two letters (clock loan; summit hosting — Bascom Lodge concessionaire + DCR Mount Greylock State Reservation, with NoBARC as a possible ally/host); find the home station.
- From loan date L: L+0–4 weeks co-location, characterisation, enclosure and link tests at home; L+4 install at the summit; L+5 first-week result (~70 ns); L+8 first swap; season end: retrieval, post-calibration, write-up. Eight weeks loan-to-first-result; one season for the full machine (1.6 µs).
- If Shriya is not in Massachusetts until later, the plan slides one season; the design does not change.

## 6. Variants and upgrades

- Tower mode (indoor, year-round): floor vs roof of a tall building. Harvard Jefferson tower 22.5 m → 0.21 ns/day; MIT Green Building ~90 m → 0.85 ns/day (25 ns/month); Prudential ~228 m → 2.1 ns/day. Cesium cannot see these in a season (floor noise ~65 ns per clock over 150 days vs 127 ns signal); hydrogen masers see the Green Building in a month (25 ns signal vs ~0.5 ns noise), with a top/bottom swap to cancel maser drift. Needs a maser loan (Haystack) — an institutional project.
- Flight mode: Boston–LA, 6 h at 11 km, 250 m/s: gravity +25.9 ns, speed −7.5 ns, Sagnac ±21.4 ns → westbound +40 ns, eastbound −3 ns, round trip +37 ns. The Hafele–Keating miniature.
- Optical mode: a transportable optical lattice clock (10⁻¹⁸) would resolve the Jefferson tower in seconds and reach ~2 × 10⁻⁵ on Greylock (Skytree 2020 did 450 m at 9 × 10⁻⁵; JILA 2022 resolved 1 mm in one lab). MIT has optical-clock expertise; million-dollar instrument.
- Indoor companion (winter, "as real as a computer"): the post-selected closed-timelike-curve simulator — Lloyd et al., PRL 106, 040403 (2011; theory MIT, photonic experiment Toronto) and Ringbauer et al., Nat. Commun. 5, 4145 (2014). Runs the mathematics of a time loop (grandfather paradox suppressed as gun fidelity → 1) via teleportation + post-selection; moves nothing backward. Photonic BOM ≈ US$25–45k (405 nm pump, BBO/ppKTP, polarization optics, 2–4 SPADs, time tagger); free version as a Qiskit circuit on IBM Quantum. Not yet written.

## 7. Sources used for this note

Mount Greylock (Wikipedia: elevation, coordinates, tower, lodge, summit transmitters); Berkshire Eagle 2026 opening article (roads 16 May, lodge 23 May, roads close 30 Oct 2026); bascomlodge.net rates; mass.gov Mount Greylock camping page (lodge season late May–mid/late Oct); Leonard Cutler (Wikipedia: 5071A/5071B made by Microchip in Beverly MA); Chronos 5071A page (5 × 10⁻¹³ accuracy, <1 × 10⁻¹⁴ at ≥5 days, 45-min battery, MTBF >160,000 h); eBay listings (5071A prices, Sept 2026); TAPR TICC product page ($249, in stock, <60 ps); ArduSimple simpleGNSS Timing (€149, NEO-F10T); NoBARC repeaters page; MIT Haystack Westford handout (hydrogen maser); leapsecond.com Project GREAT (2005, +1,340 m, 40 h, three cesium clocks, 22 predicted / 23 measured ns); APS PRL 106, 040403.

## 8. Next real steps (none taken yet)

1. Decide the home station and the target season.
2. Draft and send the loan letter and the hosting letter (Claude offered to draft both).
3. Pre-register the number (+9.96 ± 0.1 ns/day) publicly — the X series is the natural place.
