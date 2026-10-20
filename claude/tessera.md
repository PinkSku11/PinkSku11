# Tessera — the message that teaches itself (design and v0.1 record)

*Time Travel project · 20 October 2026. Companion to claude/time-ships.md (the ships this serves), claude/greylock-time-machine.md (the first payload) and claude/machine-catalogue.md. Status: v0.1 built, tested, delivered in chat as tessera-v0.1.zip; the first thing we say is the Greylock ledger (Shriya left the choice open; chosen because a stranger can check it).*

## 0. The premise and the limits

A time machine is a channel between epochs, and a channel needs a code both ends can learn; every ship in the catalogue has a receiver who shares no context with the sender (Vigil's sleepers, Nautilus's descendants, the Lantern's far mouth, whoever reads the Greylock ledger in 500 years). Three limits, stated: nothing is "universal" — the design spends assumptions one at a time and names each; nothing reaches the past (the audit in Where Are the Time Travellers? closes that channel) — beings from the past who arrive later are readers with older context; for other universes mathematics goes first and physics is an optional rung. The name: a tessera was a token broken in two so strangers could recognise each other later by matching the halves.

## 1. The ladder

Every glyph is defined only by examples using glyphs already taught (Freudenthal's Lincos 1960; the Cosmic Call pages 1999/2003; Minsky's 1985 argument that any problem-solving intelligence meets counting first).

0. mark and gap — 8-bit glyph codes, all 1xxxxxxx (the constant column reveals the width; sixteen zeros never occur, so 24 zeros + 1 is the frame mark)
1. counting — · ·· ··· beside binary names (assumes discreteness)
2. arithmetic — + − × ÷ < > = by example triples, brackets (assumes pattern-finding)
3. truth — ⊤ ⊥ after checkable statements; ¬ ∧ ∨ ⊃ by truth tables; a first variable law (a + b = b + a)
4. the machine — Peano ∅ and S, rewrite rules written ≝ … ⇒ …, worked reductions of add/mul/double, each cross-checked against rung 2; after this, anything written as rules is a program (assumes the reader can follow rules)
5. anchors — the hydrogen page (drawn: two atoms, the spin flip, one wavelength, the period); tick = period, wave = wavelength, so c = 1 wave/tick; the pulsar stamp (assumes shared physics; skippable)
6. payload — the Greylock ledger in hydrogen units, all integers: clock A 5,008 waves above clock B; g × 43,424,… = 1 wave/tick²; rate = g·h/c²; the summit clock gains 14.15 ticks per 122,723,056,952,755-tick day. Second payload: the ship (Proxima distance 1.9 × 10¹⁷ waves, ship and home times in ticks, the lead).
7. words — agent, target, danger, good, bad by a walk on the number line (the thinnest rung)

## 2. v0.1 (Python, standard library; 17 tests passing)

* `glyphs.py` — 55 placeholder 5×7 shapes, exported to glyphs.txt for Shriya to redraw; `load_overrides` reads them back. Pairwise Hamming distance ≥ 6.
* `message.py` — the ladder and payloads; `transcript()` for humans. 3,711 glyphs, 29,688 bits.
* `machine.py` — term rewriting (leftmost-outermost), Peano arithmetic, parse/print.
* `units.py` — hydrogen units (f_H = 1,420,405,751.768 Hz, λ = 0.211 m), Greylock and ship numbers in them.
* `stamp.py` — twelve pulsars as (period in milli-ticks, 1/Ṗ); `decode` finds the common Δt from a later catalogue: 12,345 years recovered to ±0.08 yr; 0.5 yr to ±0.01. Catalogue values approximate (replace from an ephemeris before etching).
* `bits.py` — glyphs ↔ bits, frame marks, repetition with majority vote (3 copies survive 0.1% flips, 5 copies 0.5%), Hamming(7,4) for our own archives.
* `pages.py` — 211 × 223 pages (both prime: unfold one way), 35 × 27 glyph cells, row/column parity (one flipped pixel is located), the hydrogen page, the glyph key sheet, stdlib PNG/PBM writers.
* `listen.py` — the stranger: given only bits it finds width 8, alphabet 49, Zipf slope −1.8, conditional entropy 1.6 vs 3.3 bits, then the delimiter and counting mark (the only pair giving a binary-consistent counting ladder), both digits, = + − × ÷ < >, ⊤ ⊥ and the brackets — fifteen glyphs correct with no key; random noise fails at the first step.
* `harness.py` — the blind packet (the message transliterated into an unfamiliar syllabary + the bits + a rubric) for a person or a fresh language model, and a scorer. Not yet run on anyone.
* `cli.py` — `python -m tessera {speak, listen, stamp, glyphs, packet}`.

## 3. Open threads

* Rung 7 needs Lincos-style dialogues, not a walk.
* Pictures as programs (the machine drawing bitmaps) — the step that removes the need for eyes.
* Run the blind packet on a person and on a fresh model; score rungs 4–7.
* Shriya's own glyph set (she is a visual artist; glyphs.txt is the handle).
* Etch plan: Rosetta-disk-style scale ladder, nickel or quartz; the Nautilus chambers as the carrier.
* Possible X piece: "A Message That Teaches Itself".

---

*Checked into this repository at `tessera/` on 20 October 2026 (code, tests, and the generated out/ pages), verbatim as delivered; the audit is claude/tessera-audit.md.*
