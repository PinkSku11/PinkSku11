# Audit of tessera v0.1 — the first record whose code could be put on trial

*Time Travel project · 20 October 2026. Target: claude/tessera.md and the tessera/ package (checked in this repository — so unlike the timeship and machine-catalogue audits, every claim here was tested against running code). Method: four auditors — mechanical claims by execution, payload physics against both the code and the Greylock note, an adversarial honesty attack on listen.py, and a code review of the algorithmic core — writing their instruments outside the package and never modifying it. One bug was fixed after the audit (§2), with regression tests; everything else ships verbatim.*

## 0. Verdict

**The design is real and its central claim survives its hardest test.** `listen.py` imports no mapping and carries no glyph codes, and under five random bijective re-encodings of the entire alphabet — including three that kept only a *different* constant column than the shipped one — it recovered **all fifteen meanings, every time, with zero spurious entries**. The "message that teaches itself" genuinely teaches itself, down to the assumptions rung 0 declares (a fully arbitrary byte permutation with no constant column defeats width detection — exactly as the record says it should). One real bug (fixed), five overstatements worth rewording, and a set of precision-honesty recommendations before anything is etched in nickel.

## 1. Confirmed by execution (highlights)

- **Message mechanics exact:** 55 glyphs, minimum pairwise Hamming distance exactly 6 over all 1,485 pairs; 3,711 glyphs / 29,688 bits, shipped bitstream identical to a rebuild; every code 1xxxxxxx; longest zero-run in the body is 7 (so the 24-zero frame mark is unambiguous with huge margin — the record's "sixteen zeros never occur" is loose but true); Hamming(7,4) exhaustively corrects all 128 single-flip cases; pages 211 × 223 (both prime), the cell geometry closes exactly (35·6 + 1 = 211), and crossed parity located 50/50 random single-pixel flips on the real shipped page.
- **Payload physics against both code and notes:** f_H and λ ✓; "5,008 waves" matches units.py's Δh = 1,057 m, which matches the Greylock note's own rounded Δh exactly; the day is 122,723,056,952,755 ticks digit-for-digit; the 14.15 ticks/day reproduces from the message's own three integers alone (the integer cross-check closes); Proxima 1.90 × 10¹⁷ waves, and the ship/home/lead tick integers match the timeship figures (3.5421 / 5.8726 / 2.3305 yr) and peak β = 0.9497. The pulsar milli-tick convention verified on the Crab; the 12,345-yr stamp dating recovers the epoch essentially exactly with per-pulsar spread ±0.082 yr.
- **The algorithmic core:** machine.py is *genuinely* leftmost-outermost (a discarding rule fires at the root in one step where innermost diverges); 20 random Peano add/mul/double reductions all match integer arithmetic; the transcript's rung-3 truth tables are correct row-by-row, all 25 ground truth-judgements evaluate as printed, the five divisions are exact, the commutativity line really is a variable law (VA/VB glyphs, not instances), and all three rung-4 worked reduction chains are exactly what the engine produces, step by step.
- **The blind packet does not leak the key:** blind-symbols.txt is rubric + transliteration only; blind-key.txt is the scorer's answer sheet (marked as such). PNGs are structurally valid (signature, chunks, CRCs, IDAT size — parsed by hand).
- **Noise control holds:** random bits fail at width detection (compressibility ~1.0 vs the message's 0.269), 5/5 seeds.

## 2. The bug (found, fixed, regression-tested)

**`load_overrides` silently dropped 49 of 55 glyphs** — the loader treated every `#`-initial line as a comment, but 47 glyph shapes have a pixel row starting with `#` (EQ's first row is `#####`), and the resulting misalignment lost two more. Consequence: **Shriya's redraw pathway — the project's named next step and glyphs.txt's whole purpose — was broken**: an edited glyph reloaded as "6 replaced" with the edit ignored. Fixed in `tessera/glyphs.py` (a comment is now only a line that cannot be a 5-wide {#,.} row) with three regression tests in `tests/test_glyph_overrides.py`: full 55-glyph round-trip, a honoured edit to a hash-initial glyph, and real comments still ignored. Suite: 20/20.

## 3. Overstatements (true only with conditions the record omits)

1. **"3 copies survive 0.1% flips, 5 copies 0.5%"** — Monte Carlo (20,000 trials, whole framed message): P(zero residual errors) = **91.6%** and **96.5%** respectively. Passes a >90% bar, but ~1 in 12 / ~1 in 28 transmissions keep at least one bad bit; "survives" should carry the number. (Counter-intuitively the 5×/0.5% setting is the *more* reliable one.)
2. **"0.5 yr recovered to ±0.01"** — the stamp's per-pulsar spread is ±0.082 yr at *both* Δt = 12,345 and 0.5 yr (milli-tick quantization is Δt-independent); ±0.01 is only the test's tolerance on the (essentially exact) median. The record's implied tighter dating at small Δt is wrong as a spread statement.
3. **"Given only bits it finds width 8"** — true for the unframed stream; on the shipped *framed* bits `decode_blind` finds nothing (the 25-bit marks break the length divisibility), and the CLI strips frames using the sender's own constant. **The frame mark is told, not discovered** — an honest next step is teaching find_width to find it.
4. **The admitted prior is bigger than admitted.** The docstring claims one prior ("the message opens by counting"), but the whole lesson grammar of rungs 1–3 is baked into the parser shapes. The remap test proves no token identities are smuggled — but listen.py is a decoder for this dialect, not a general cryptolinguist. Relatedly, a meaningless Zipf-shaped stream passes the entire statistics battery; only the counting-lesson search rejects it. (The record's narrower noise claim is literally true.)
5. **The rubric leaks the ontology** — the subject-visible text names the full semantic inventory (which operators, that it opens by counting, that it ends in measured quantities) while withholding the mapping. Fine as a mapping-recovery test; not a true stranger test. Worth stating before the blind runs are scored.

## 4. Small corrections and nits

- **Record digit slip:** "g × 43,424,… = 1 wave/tick²" should read **43,422,…** (exact: 43,422,262,615,660,451; the code emits …448, three low in the 17th digit from float64).
- **Precision honesty before etching:** units.py rounds silently and etches 17–18-digit integers from 5–6-significant-figure inputs (g, the Proxima distance), with trailing digits that are float64 noise. Recommend exact decimal/integer arithmetic and digit counts matched to actual knowledge — a reader who checks (the design's own selling point) will find the noise.
- **Convention note:** units.py uses standard g = 9.80665 where the Greylock note's headline uses local g ≈ 9.802; 14.154 vs 14.147 ticks/day — both print "14.15," but one convention should be named.
- **Citation nit:** the f_H value 1,420,405,751.768 Hz is Hellwig et al. 1970; units.py's comment credits Essen et al. (whose figure is …751.7667).
- **machine.py edges (unreachable in the shipped message):** no non-termination *detection* (a 10,000-step cutoff raises RuntimeError); atoms literally named LP/RP break parse round-tripping; truncated input raises bare IndexError. listen.py's docstring example mislabels 0x8a as + (it is >).
- **Rung 7's STEP glyph plays two roles** (statement separator in the walk, successor-ish in the closing law) — the record's "thinnest rung" admission is accurate and arguably understated.
- **Coverage gaps (no found bugs behind them):** the reduction *strategy*, the PNG/PBM writers, and the entire CLI are untested by the shipped 17 tests.

## 5. Scorecard and standing

| Slice | Checked | Confirmed | Overstated | Corrected/bug |
|---|---|---|---|---|
| Mechanics | 11 | 8 | 2 | 1 (fixed) |
| Payload | 7 | 5 | 1 | 1 (digit slip) |
| listen honesty | 9 | 6 | 3 | 0 |
| Code core | 12 | 8 | 4 | 0 |

Tessera is the first companion record whose code arrived with it, and it is the better for it: the audit could *run* the central claim instead of trusting it. The timeship package and the Qiskit CTC bundle remain the two "existing" codebases this repository still cannot verify — same recommendation, third audit in a row.

---

# v0.2 audit addendum (same day) — the self-describing alphabet on trial

*Four auditors re-ran the full programme against v0.2 (10,733 glyphs / 85,864 bits, 73 glyphs, the pictures rung, the dialogue rung), with v0.1 kept for diffing. Scorecard: 28 confirmed, 3 overstated, 1 fixed-in-v0.2, 8 regressions (v0.1 findings still present upstream), 1 new design trap (fixed in-repo).*

## The headline claims all hold, at the strictest reading

- **"The alphabet describes itself" is true in the message's own language.** For all 73 glyphs, the shape program as stated in the message — parsed by `machine.parse`, reduced by the machine's own rewrite rules, never by the Python renderer — yields exactly the point set of the renderer AND exactly the 5×7 cells physically stamped on the shipped pages (all 10,733 cells of pages 01–12 match). The one caveat: 7 of the 73 definition left-hand sides (END, RP, LP, SEP, ARROW, Z, O — the punctuation that cannot appear quoted inside a statement it would terminate) are told-not-derivable in the message's own grammar; a bracket-aware reader disambiguates all of them, but it is the same genre as the frame-mark finding.
- **The ship is a program.** The message's `≝ (picture ship) ⇒ …` machine-reduces in 2,199 steps to a 15 × 31 picture — closed hull, six deck rows, engine block — matching the pictures page pixel-for-pixel at both scales. ("Cabin" is generous: a 3-px bar and an empty space.)
- **The dialogue is semantically honest.** An independent extractor found 11 question–answer–judgement triples; every `good` answer is arithmetically true and every `bad` false, no exceptions. The closing sequence verifies token-by-token: *we want (you know (clock A > clock B)) / we not know (pulsar 1 period = a) / we ask you / we want (we know …)* — the message really ends by asking the reader for their epoch, and its literal last line is **"we want (you good)"**.
- **Eighteen glyphs, no key, remap-proof.** `listen` recovers all 18 (now including the variable *a* and good/bad — by genuinely re-evaluating each answer against its question, no identities hardcoded) on 5/5 random code bijections and 3/3 with a different constant column. Instructive control: the Zipf slope does *not* separate the real message (−1.95) from shuffled noise (−1.95) — conditional entropy does (H₂ 2.06 vs 3.89).
- **Everything reproduces.** All 37 shipped out/ files regenerate byte-for-byte; bits/stamp/units are byte-identical to v0.1; the payload integers are unchanged digit-for-digit; min pairwise Hamming is exactly 6 over all 2,628 pairs; 21/21 shipped tests pass.

## Fixed in v0.2 (upstream) and in-repo (this commit)

- **The v0.1 loader bug is structurally gone upstream**: glyphs.txt now stores programs; art rows carry a `| ` shield and are never parsed. And the v0.2 *record* dropped all three v0.1-audit overstatements (the 0.5-yr stamp claim, the repetition percentages, the 43,424 digit).
- **New design trap, found and fixed in-repo**: art is decoration and programs are authoritative — so an artist who redraws only the art (exactly the workflow the record describes for Shriya) was silently ignored while the CLI printed "(using 73 glyph shapes from glyphs.txt)". `load_overrides` now compares each section's art against what its program draws and **warns by name** on mismatch. Regression tests added (art-only edit warns and changes nothing; program edits take silently; full 73-glyph round-trip; the ship's decks asserted). Suite: 25/25.
- Three carried nits fixed in-repo: the `listen.py` docstring example (0x8a → 0x85 for +), the f_H citation (Hellwig et al. 1970, not Essen), and the glyphs docstring's "bar above and below" (no machine glyph has a bottom bar; it is a bar above, as the record correctly says).

## Still open upstream (unchanged from the v0.1 audit, plus two new notes)

Frame mark still told-not-discovered (the CLI strips it with the sender's own constant; `decode_blind` fails on framed bits); the admitted "counting" prior still understates the hardcoded lesson grammar, which now includes the dialogue shapes; the blind-packet rubric still leaks the ontology (now including pictures and dialogue); units.py still etches float64 noise in its low digits (exact-decimal recommended before anything is engraved — the exact G_DENOMINATOR ends …451, the code's …448); machine.parse still breaks on LP/RP-named atoms and truncated input (unreachable in the shipped message). New: the family marks (bar/columns/corners) are real on every glyph but **not exclusive** — every physics glyph geometrically also contains the dialogue corners, and the numeral Z contains all three marks, so role detection by mark alone collides; and the loader does not re-check the ≥6 Hamming guarantee after user edits.
