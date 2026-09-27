# Starship Time Machines — review of the Greylock design, and the ladder above it

*Time Travel project · design note, 27 September 2026, written in answer to "read the Greylock design, tell me your opinions, and brainstorm more — spaceships that act as time machines, etc." Sibling of the Greylock Time Machine (claude/greylock-time-machine.md) and the Ooty Clock Run protocol. Part 1 is a technical review of the Greylock machine; Part 2 is the same machine scaled upward until the mountain becomes a starship. Status: analysis and brainstorm only.*

## Part 1 — Review of the Greylock design

### 1.1 What I checked and confirmed

All the load-bearing arithmetic was re-derived independently and holds:

- gΔh/c² = 9.802 × 1,057 / c² = 1.1528 × 10⁻¹³ → **9.96 ns/day**. ✓
- The link-mode statistics are exactly right: a linear fit through N daily points of σ = 3 ns has slope uncertainty σ·√(12/N(N²−1)) = 0.567, 0.199, 0.063 ns/day at N = 7, 14, 30 — the note's ±0.57/±0.2/±0.06. ✓
- "GPS time runs at the geoid rate by construction, so one clock vs GPS shows the effect" — correct, and it is the design's best cost lever. The satellite clocks are factory-offset (10.22999999543 MHz vs 10.23) precisely so that broadcast time ticks at the geoid.
- The S↔H swap cancelling intrinsic offsets in the mean of the two configurations — correct, and it is the single most professional feature of the design. So is the observation that the swap does *not* cancel a shared temperature coefficient (a symmetric systematic survives symmetric exchange); thermostatting is the right and only fix.
- The honest scope in §0 — forward only, backward closed by the negative-energy no-gos — is the correct physics and the rarest thing in amateur "time machine" projects. Keep it as the opening paragraph of everything this project publishes.

### 1.2 Weaknesses and fixes (in order of how much they threaten the result)

1. **Retrace is the real enemy, and the note never names it.** The swap cancels intrinsic offsets only if transport doesn't change them. A 5071A that is powered down, driven 215 km, and restarted can come back with its frequency shifted at the low-10⁻¹³ level (time-nuts lore and Agilent/Symmetricom application notes both say "characterise retrace yourself"); that is the same order as the 10⁻¹³ signal. The design already contains the defense — co-location before and after every move — but it should be promoted from calibration procedure to named systematic: *the error budget line is "retrace per transport event," bounded by the before/after co-locations, and the number of transport events should be minimised (install, one swap, retrieval — nothing else).* Keeping the clock powered on battery through the drive (the LiFePO4 plan) helps a lot; a run where the clock lost power mid-transport should be declared invalid in the pre-registration, not decided afterward.
2. **Pressure is a static offset at the summit, not noise.** The summit sits near 89 kPa year-round vs ~101 kPa in Cambridge — a permanent 12 kPa step that, like temperature, is common to both clocks and therefore *survives the swap*. Logging pressure (already planned) diagnoses nothing unless there's a coefficient to multiply it by. Fix: during home co-location, put one clock in a crude altitude chamber (or just cite/measure the barometric coefficient; for the 5071A it is believed to be ≪10⁻¹⁴ because the physics package is evacuated, but "believed" should become a line in the systematics table with a number or a bound on it).
3. **Separate the two ±'s.** "+9.96 ± 0.1 ns/day" is the *prediction's* uncertainty (from Δh, g, and the geoid). The *measurement's* expected uncertainty for one season with one travelling clock is more honestly ±0.5–1 ns/day once retrace and calibration are folded in — which is exactly why the falsification bar was set at ±1 ns/day. The pre-registration should state both numbers explicitly so nobody later confuses a 10% test with a 1% test.
4. **Lightning is the tail risk to the borrowed clock.** The summit is a transmitter site because it is the highest strike target in the state. A UPS does not save a $50k loaner from a surge arriving on the GNSS antenna line or the mains. Add: gas-discharge arrestor on the antenna feed, grounded bulkhead panel, opto-isolated or transformer-coupled 1PPS out, and a sentence about insurance in the loan letter — the lender will ask anyway.
5. **Redundancy on the cheapest component.** The season is unrepeatable (roads close, loan ends). Two GNSS timing boards per station is +€300 against the risk of a dead receiver eating a month of unrecoverable slope. Same logic: log everything raw at full rate, sync to two places nightly.
6. **Geopotential pedantry (harmless, worth one sentence).** gΔh with a mean g approximates the geopotential-number difference ∫g dh to ~10⁻³ — far inside the ±1% claimed, but the note should say the reference surface is the geoid and that NAVD88 orthometric heights are the right heights to use (they are), so a reviewer can't score the point.

Verdict: **this is a real experiment design, not a metaphor** — the architecture (free-running cesium vs GPS time, swap-cancelled offsets, pre-registered slope) is the same one national labs used for decades, sized to a season and a car. The two letters (§8) are the actual critical path; everything above is refinement.

## Part 2 — The spaceship ladder

The Greylock machine has two knobs: potential (gΔh/c²) and speed (v²/2c²). On the surface of the Earth the first knob stops at ~10⁻¹³ and the second at ~10⁻¹² (airliners). A spaceship is not a different machine — it is the same machine with both knobs unscrewed. The ladder below climbs nine orders of magnitude, from hardware that exists to hardware that cannot.

### 2.1 Rung 0 — spaceship time machines already flying (free calibration points)

| Vehicle | Rate vs Earth clock | Mechanism | Note |
|---|---|---|---|
| GPS satellite | **+38.6 µs/day** | +45.7 gravity, −7.1 velocity | offset built into the factory clock frequency; the Greylock display could show this live for zero hardware |
| ISS | **−25 µs/day** | −28.2 velocity, +3.7 gravity | a 6-month crew jumps ~4 ms into the future; Gennady Padalka (878 days aloft) leads all humans at ~22 ms — the current world-record time traveller |
| Galileo 5–6 | eccentric orbit → periodic signal | mis-launch turned into the best clock test of GR: 2.5 × 10⁻⁵ | already cited in the Greylock note; the lesson is that *eccentricity converts an orbit into a time-dilation waveform* |
| Parker Solar Probe | **~−36 ms/day at perihelion** | 2.0 × 10⁻⁷ velocity (192 km/s) + 2.1 × 10⁻⁷ solar potential (~6.9 M km) | the fastest time machine ever flown; nobody put a clock experiment on it |
| the Moon (Artemis/LTC) | **+56 µs/day** | +60.2 leaving Earth's well, −2.7 lunar well, −0.5 orbital speed | Coordinated Lunar Time is a live 2024–26 standards effort — a lunar clock is a *permanent* Station S |

Note the sign lesson the ISS row teaches: below ~3,200 km altitude the velocity term wins and orbiting slows your aging; above it the gravity term wins and you age faster. A "time machine to the future" spaceship therefore wants to be **fast and low, or deep in a well** — altitude alone is the wrong direction (that's why Greylock's summit clock runs *fast*: it gains potential without gaining speed).

### 2.2 Rung 1 — the buildable spaceship version of this exact project: a cubesat

The LEO signal (−2.5 × 10⁻¹⁰, i.e. −22 µs/day) is **2,200× the Greylock signal**, while a chip-scale atomic clock (Microchip SA.45s CSAC: 35 g, ~120 mW, ~$5–8k) is only ~10³ worse than a 5071A day-to-day (ADEV ~10⁻¹¹, aging ~3 × 10⁻¹¹/day). Net: the orbital signal exceeds the CSAC's daily drift by an order of magnitude — **a 1U cubesat with a CSAC and a GNSS timing receiver sees special+general relativistic time dilation within days**, using literally the Greylock architecture (free-running clock vs GPS time, offset calibrated before flight). NASA's DSAC (mercury-ion, 3 × 10⁻¹⁵/day) already flew 2019–21 and proved autonomous space clocks; the cubesat version is a student mission, not a NASA one. Massachusetts angle, as required: MIT Space Systems Lab and Draper both fly cubesats; rideshare slots run ~$85k. Natural name: **Greylock-1**. This is the honest answer to "design a spaceship that acts as a time machine": it exists at the intersection of a $6k clock and a rideshare.

(Rejected sibling: the high-altitude balloon. 30 km for 10 h accrues only ~120 ns, and any clock light enough to fly — CSAC, small rubidium — accumulates comparable noise over the flight. The signal-to-mass ratio is worse than either the mountain or the orbit. Skip.)

### 2.3 Rung 2 — the sundiver ("Oberth chronoship")

Drop a clock from rest at infinity toward the Sun and a small identity appears: on a parabolic fall, v²/2 = GM☉/r, so **the speed term equals the gravity term at every point of the dive** — the two knobs turn together, automatically. At a 4 R☉ perihelion: 309 km/s, each term 5.3 × 10⁻⁷, total ~1.1 × 10⁻⁶ → **~92 ms/day at closest approach**, a billion times Greylock. A Parker-class heat shield already survives comparable radii. A repeating eccentric solar orbit banks roughly ~0.1 s per pass against Earth and turns the returning clock into the measurement. This is the largest time machine buildable with current propulsion — chemical + Venus assists suffice; the clock, thermal shield, and telecom are the whole problem. (Cheap precursor: compute and publish how far into the future Parker Solar Probe's oscillator has already travelled — it's a data-analysis project, not a mission.)

### 2.4 Rung 3 — the 1g torchship (the canonical forward time machine)

Constant 1g acceleration to midpoint, flip, 1g deceleration. The elegance: the same 9.8 m/s² that gives the crew floors and health is the relativity engine, and c/g ≈ 0.97 years makes the numbers humane (verified with τ = (2c/g)·cosh⁻¹(1 + gd/2c²)):

| Destination | Distance | Ship time | Earth time | Photon-rocket mass ratio (one-way, perfect drive) |
|---|---|---|---|---|
| Proxima Centauri | 4.37 ly | 3.6 y | 6.0 y | 40 |
| Galactic centre | 26,000 ly | 19.8 y | 26,000 y | 7 × 10⁸ |
| Andromeda | 2.54 Mly | 28.6 y | 2.54 My | 7 × 10¹² |

Twenty-nine years of proper time buys 2.5 million years of the future — a genuine one-way time machine, and the mass-ratio column is its honest price: e^(gτ/c) even for a *perfect* antimatter photon rocket, before any engineering inefficiency. So the design rule for forward machines is: **the rocket equation punishes γ exponentially; gravity wells give dilation for free.** Every affordable rung of this ladder (mountain, orbit, sundiver, black hole) is a well, not a burn. The one propulsive concept that dodges the rocket equation — the laser-pushed sail (Starshot, 0.2c) — buys only γ = 1.02: its gram-scale probe reaches Proxima ~5 months younger than its 21-year cruise, the first artifact to time-travel by a human-noticeable margin at interstellar distance. The Bussard ramjet, the classic fictional 1g solution, fails in the modern analyses: scoop drag exceeds fusion thrust and the device is a magnificent *brake* (useful for the deceleration half, footnote-worthy).

### 2.5 Rung 4 — black-hole ships: orbit, don't hover; bigger is safer

Two counterintuitive design rules fall out of the Schwarzschild/Kerr metrics:

1. **Orbit, don't hover.** Hovering near a horizon needs proper acceleration that diverges as you approach it — a torchship problem again. But a *circular orbit* has engines off, and its clock runs at dτ/dt = √(1 − 3GM/rc²): parked at the innermost stable circular orbit (r = 6GM/c²), the crew ages **29% slower, forever, for free**. Around a near-extremal spinning (Kerr) hole, stable prograde orbits reach far deeper — Thorne's Interstellar numbers (1 hour = 7 years, a factor 61,000) are legitimate for orbits skimming a hole within ~10⁻¹⁴ of maximal spin. The dilation factor is a *parking spot*, not a fuel bill.
2. **The biggest black hole is the safest.** Tidal stress at the horizon scales as 1/M²: a stellar-mass hole shreds the ship far outside the interesting region, while at Sgr A* (4 × 10⁶ M☉) the horizon-adjacent tides are gentler than Earth's. The luxury model is the biggest hole you can reach. (Budget option, same physics smaller: a neutron-star surface runs ~20% slow — √(1 − 2GM/Rc²) ≈ 0.81 for 1.4 M☉ at 12 km — but the orbit-don't-hover rule applies doubly; nobody lands.)

The mission profile writes itself: fly to the well (rung 3's problem), spiral to the deep orbit, wait out the centuries on the clock of your choosing, spiral out. A "time machine spaceship" in the far-future limit is mostly a very good hibernation habitat with a very good ephemeris.

### 2.6 Rung 5 — backward ships, and why the ledger still says no

The one *backward* design in the serious literature that is literally a spaceship mission: **Morris–Thorne–Yurtsever (PRL 61, 1446, 1988)**. Keep one wormhole mouth home; put the other on a relativistic tug and fly a twin-paradox round trip (or park it by a neutron star). Differential aging desynchronises the mouths, and stepping through thereafter is travel to the past — but never to before commissioning, which neatly explains the empty visitor logs (Where Are the Time Travellers? already makes this argument; MTY is its mechanism). The tug is a mundane rung-3 ship. All the impossibility is in the cargo: holding the throat open takes negative energy, and the Ford–Roman quantum inequalities ration negative energy into bands ~Planck-lengths thick with galactic-scale magnitudes; Hawking's chronology protection conjecture (1992) then argues vacuum fluctuations pile up on the Cauchy horizon and detonate the machine at the instant of first closure. Warp-drive ships inherit the same ledger (Alcubierre needs the same exotic matter, and Everett 1996 showed two warp bubbles compose into a time machine, so every warp no-go is a time-machine no-go); the Tipler cylinder needs infinite length; Gott's cosmic-string pairs are closed by the project's own cited CFGO 1994. The asymmetry is worth stating on the display: **forward is continuous (every m/s and every metre of altitude buys some future); backward is all-or-nothing, and the "all" is quantum-forbidden.** A spaceship can be any amount of forward time machine and no amount of backward one.

### 2.7 Rung −1 — two cheap companions that belong in the Greylock plan now

1. **Muons on the same mountain (the best new idea in this note).** Frisch (MIT) and Smith filmed the classic muon time-dilation experiment in 1963 on Mt Washington: cosmic-ray muons (τ = 2.2 µs) made ~15 km up should mostly decay before sea level; they don't, because at γ ≈ 9 they live ninefold longer. MIT now publishes **CosmicWatch**, a ~$100 DIY desktop muon detector. Two of them — one at Bascom Lodge next to the cesium clock, one in Boston — measure the summit/sea-level flux ratio and demonstrate *special*-relativistic time dilation in the same season, on the same mountain, in the same car trips, for ~$200. The exhibit then shows both halves of relativity side by side: the clock ages faster (gravity), the muons age slower (speed). Particle-physics footnote for the display: CERN's storage-ring muons at γ = 29.3 are the most-travelled time travellers per gram ever made.
2. **The GPS live panel.** Parse the broadcast ephemeris and show "every GPS satellite overhead is gaining 38.6 µs/day on you, and your phone corrects for it" — zero hardware, and it makes rung 0 of the ladder part of the permanent display.

## 3. Additions to the next-real-steps list

1. Add retrace, pressure, and lightning lines to the Greylock systematics table (§1.2 above) before pre-registering; state prediction uncertainty and measurement uncertainty as separate numbers.
2. Put two CosmicWatch kits on the winter build list (they are soldering projects — buildable before the 2027 season opens, testable at home).
3. Write the Parker Solar Probe accumulated-proper-time calculation as a short note — the "fastest time machine flying" number is publishable from public ephemerides alone.
4. Sketch Greylock-1 (CSAC cubesat) as a one-pager for the same institutions the clock-loan letter goes to — it is the natural sequel and makes the loan request look like the first step of a program, which it is.

## 4. Sources used for this note

Greylock design record (sibling file, all its cited sources inherited); standard relativistic-rocket results (τ = (2c/g)cosh⁻¹(1 + gd/2c²), photon-rocket mass ratio e^(Δθ)), re-derived numerically for the table; GPS ICD relativistic offset (10.22999999543 MHz); ISS dilation from v = 7.66 km/s, h ≈ 420 km (net −24.5 µs/day; Padalka ≈ −22 ms over 878 d); Delva et al. & Herrmann et al., PRL 121 (2018) — Galileo 5–6 redshift test; Parker Solar Probe final-orbit parameters (≈192 km/s, ≈6.9 × 10⁶ km); NIST/JPL lunar time papers (≈+56 µs/day, 2024) and the 2024 OSTP Coordinated Lunar Time directive; Microchip SA.45s CSAC datasheet; JPL Deep Space Atomic Clock mission (2019–21); Bardeen–Press–Teukolsky / Thorne, The Science of Interstellar (Kerr orbit dilation, factor 61,000); Morris & Thorne, Am. J. Phys. 56, 395 (1988); Morris, Thorne & Yurtsever, PRL 61, 1446 (1988); Hawking, PRD 46, 603 (1992); Ford & Roman quantum inequalities (PRD 51, 4277 (1995) and sequels); Everett, PRD 53, 7365 (1996); Frisch & Smith, Am. J. Phys. 31, 342 (1963) and the MIT film; CosmicWatch (MIT, cosmicwatch.lns.mit.edu); Breakthrough Starshot published parameters (0.2c).
