# Audit of "Time ships after Chrysalis" — every number re-derived

*Time Travel project · 20 October 2026, written in answer to "let's audit the whole thing." Target: the record "Time ships after Chrysalis — the designs, the spreadsheet, and timeship v0.1" (claude.ai/artifact/SjcDifk8qodP5SPGPCeyPK is its Tower Cockpit). Method: four independent auditors, each re-deriving its slice from first principles in Python with no access to the timeship code — Kerr/Cradle; the no-go ships (Harp, Wake, Mirror); kinematics, Lantern horizons and the clocks ledger; and a repo-consistency + cockpit auditor that ported the artifact's JavaScript physics to Python and flew it under Playwright. The timeship-v0.1.zip itself was not available to this session, so the code is audited through its published claims; everything else is audited directly.*

## 0. Verdict

**The record is sound.** Of ~45 numeric claims checked, **zero are wrong**. One is stale (the spreadsheet inventory — see §4), four are model-dependent with assumptions the auditors identified and judged reasonable (§3), and three of those resolve to confirmed once the sibling documents in this repository are consulted (§3.1). The flagship nontrivial finding — the 1,000-ly round-trip Lantern going critical mid-return — reproduces exactly, including a closed form the auditor derived independently.

## 1. Confirmed, with independent values

**Cradle (Kerr, Bardeen–Press–Teukolsky prograde orbits).** ISCO dt/dτ: 1.4142 (a=0), 2.6964 (a=0.9), 10.791 (a=0.998), 30.52 (a=0.9999 — the record's "×31" is +1.6% if read exactly; fine at the two figures quoted). The a=0.9 lap at Sgr A*: 3.649 ship-minutes ✓. Tides: 7.13 × 10⁻⁴ m/s² across 2 m and 2.11 g across 58 km at the a=0.9 ISCO (Newtonian 2GM·L/r³; relativistic correction O(1), as the record allows); Gaia BH1 ISCO: 8.28 × 10⁶ m/s² ✓. Dilation at r=10 GM/c²: 1.1821 ✓ (the quoted 1.18 matches the prograde a=0.9 orbit specifically). Parker perihelion: 12.72 s/yr vs an Earth clock ✓ (13.2 vs a clock at infinity — the Earth-clock convention is the record's own "whose clock you're cheating").

**Harp (Gott strings, Gμ/c² = 10⁻⁷).** μ = 1.3466 × 10²⁰ kg/m ✓; deficit 2.513 × 10⁻⁶ rad; γ_crit = 1/sin(α) = 7.958 × 10⁵ ✓; kinetic energy 0.0539 M☉/km and 8.06 × 10⁶ M☉/AU ✓.

**Wake (Alcubierre).** Pfenning–Ford with E = −(1/12)(v²c²/G)(R²/Δ), R = 100 m, Δ = 100 ℓ_P, v = 10c: |M| = 6.94 × 10⁶⁴ kg = 4.63 × 10¹¹ observable universes ✓. Van den Broeck pocket at 10⁻¹⁵ m: 3.49 M☉, still negative ✓ (matches the original paper's "few solar masses"). Everett's 0.1c boosted-observer threshold at v_warp = 10c ✓ (t′ sign flip at v > c²/v_warp).

**Mirror.** t_emit = D/v − D/c > 0 for all v < c ✓ — the light a sub-light ship intercepts always left Earth after launch; the theorem holds.

**Pennant.** 7.380 d/yr at 0.2c ✓; 21.85 yr and 5.30 months to α Cen ✓ (the 21.9 uses α Cen AB's 4.37 ly, consistent with the record saying α Centauri, not Proxima); Doppler 1.22474, dilation 1.02062 ✓; 19.35 MeV ISM protons ✓.

**Tower and baseline.** Proxima 2.3305 / 3.5421 / 5.8726 yr ✓; 1,000-ly round trip 1,976.97 yr lead / 26.897 yr aboard ✓; galactic centre 25,982.2 / 19.757 ✓; thrust 2.354 × 10¹³ N, base pressure 0.832 MPa, 7.056 × 10²¹ W = one Sun per 54,252 ships, fuel 37.7 t/t (≈38) ✓ — all also identical to the workbook's cached values. Chrysalis rim 14.141 ns/day ✓; 8.162-day lead ✓. The two prow corrections both reproduce **in the Tower itinerary where the record places them**: the 66 Gt sacrificial-ice bill (1-g Proxima proton fluence into 2.83 MJ/kg ice over the full 3-km disc; the 0.0106c coast would need only ~3.4 Mt, four orders less) and the ~300 kW/m² peak proton load (γn·v·(γ−1)m_pc² at peak β = 0.9497 = 299.4 kW/m²; a 1,500 K refractory bow re-radiates σT⁴ = 287 kW/m² — the record's numbers close on each other).

**Lantern horizons — the headline finding reproduces exactly.** Proxima one-way margin 1.916 yr ✓; galactic centre 17.820 yr ✓; Chrysalis-as-drawn 4.206 yr ✓. The 1,000-ly round trip: by numerical integration of the return leg, the accumulated lead overtakes the shrinking light-time **7.542 Earth-years after turnaround, 2.663 ship-years, at 993.4 ly from home, in Earth year 1009.5** — the record's 7.5 / 2.7 / 993 / ~1009, all four. The auditor also found the closed form (eᵘ − u = 1 + a·(d − lead_turnaround), u the return-leg rapidity-time) agreeing with the integration.

**Clocks ledger.** GPS +38.6 µs/day ✓, ISS −24.5 µs/day ("~−25" fair) ✓, Tower gradient 546.8 ns/day ✓, Chrysalis rim 14.14 ✓, Nautilus archive 7.856 ns/day and the 1.148 ms sealed-chamber figure ✓.

**The Tower Cockpit artifact (audited as code and flown).** The `advance`/`buildPlan`/`stateAt` trio reproduces closed-form hyperbolic motion at every segment boundary to 6 × 10⁻¹⁶ relative error, return-leg signs included. Fuel readout e^(−aτ/c) and the log line e^(nφ)−1 are mutually consistent and match the workbook's lead-table column. Doppler D = γ(1+β), CMB 73,157 K at the galactic flip (record: "73,000"), aberration exact (Jacobian d cosθ′/d cosθ = 1/D² verified numerically), and the footer's subtle photometry claim — point stars brighten as D², the sky as D⁴ — is the correct consequence of the invariant I_ν/ν³, and the code implements it. The Minkowski "now" line is the true simultaneity slope β, signed, so it tilts the other way coming home. Playwright flight test: zero page errors; clocks advance with Earth > ship; galactic-centre relaunch clean; calendars match the workbook (Proxima arrival AD 2130).

## 2. The one correction

**"9 tabs, 549 live formulas" is stale, not wrong.** The original nine sheets carry *exactly* 549 formulas (the auditor counted per sheet: 0+8+60+151+61+40+32+189+8), so the record describes the 8 October delivery precisely. But the repository copy (claude/chrysalis-time-ships.xlsx) gained a second wing on 9 October — More cores, Pendulum, Moult, Lighthouse, Sundiver, +136 formulas — and now holds **14 tabs, 685 formulas**. The record should be updated to mention the second wing (and §3's "open threads" partially overlap it: the Sundiver tab now exists, and a Cradle tab still does not).

## 3. Model-dependent, with the assumption named

1. **"The well is lit" (27,000 Suns / 5,000 K plate / 1,450 Suns at 10M).** Reproduced exactly by Sgr A* bolometric L = 10³⁶ erg/s (262 L☉) as a flat-space point source — the *top* of the published range (few × 10³⁵–10³⁶ erg/s); the low end cuts the numbers ~3×. The claim's spirit survives the famous ~10⁻⁹-Eddington under-luminosity because the a=0.9 ISCO sits at 0.0985 AU: proximity does the work. The 27,000 and 1,450 stand or fall together (their ratio is pure geometry ✓). Recommendation: when the Cradle sheet is built, make L_bol a blue input with the range in the note.
2. **Hiscock ~10²⁹ K.** Reproduced by the Hawking surface-gravity convention T = ħc/(2πk_BΔ) = 2.25 × 10²⁹ K; the plain ħc/(k_BΔ) scaling gives 1.4 × 10³⁰. Either way the cabin is a quark-gluon plasma; the convention should be stated.
3. **"Minus 3.3 minutes for the Sun's well."** Sun-only (IAU L_C) gives 3.11 min over 400 yr; adding Earth's geoid potential (the full L_B = 1.5505 × 10⁻⁸) gives 3.26 → 3.3 min. The L_B choice is physically right for an Earth-surface reference clock and matches the record's own ledger label — internally consistent.
4. **Nautilus archive 7.86 ns/day** requires the archive ring at r = 2,000 m — which is exactly the workbook's own blue input (Nautilus!B9 = 2,000). Resolved: **confirmed**, not merely plausible.

### 3.1 Resolved against the sibling documents (the auditors lacked them)

- **Greylock = 9.96 ns/day**: the auditor noted g·h/c² for the 1,063.4 m summit gives 10.03 and that 9.96 implies ~1,056.5 m. The unit's definition (claude/greylock-time-machine.md) is summit *minus the 6 m Cambridge home station*, Δh = 1,057.4 m, with the geopotential integral — which gives 1.1533 × 10⁻¹³ = **9.96 ns/day exactly**. Confirmed.
- **Jefferson = 0.21 ns/day**: defined in the same note as the 22.5 m Pound–Rebka tower; g·22.5 m/c² = 0.212 ns/day → 0.21. Confirmed.
- **"L_B" for the Sun's well**: consistent with the Greylock note's conventions and with §3.3 above. Confirmed as labeled.

## 4. What could not be audited here

`timeship-v0.1.zip` (voyage.py, lantern.py, cradle.py, harp.py, wake.py, clocks.py, cli.py, the examples and figures) was delivered in another session's chat and is not in this repository. Its *claims* all check out above — every number the record attributes to it reproduces independently, which is strong indirect evidence — but the code itself, its 24 tests, and the figures remain unaudited. **Recommendation: commit timeship-v0.1 into this repository next to greylock/**, so the audit can close the loop (and so the cockpit's footer claim "voyage.py gives the same numbers" becomes checkable in CI).

## 5. Scorecard

| Slice | Checked | Confirmed | Model-dependent | Corrected | Wrong |
|---|---|---|---|---|---|
| Cradle / Kerr | 13 | 10 | 3 (one L_bol assumption) | 0 | 0 |
| Harp / Wake / Mirror | 9 | 8 | 1 (Hiscock convention) | 0 | 0 |
| Kinematics / Lantern / clocks | 25 | 21 | 4 (3 resolved via siblings) | 0 | 0 |
| Repo / cockpit | 15 | 14 | 0 | 1 (stale inventory) | 0 |

The record's own sentence — "nothing is a buildable ship, and the arithmetic says so where it matters" — is accurate, and so is the arithmetic.
