# Tessera — the message that teaches itself (design and record, v0.1 → v0.2)

*Time Travel project · 20 October 2026. Written in answer to "can we create a language model, or code, that intelligent beings from future or past, from different planets, worlds, universes can decipher?" Companion to claude/time-ships.md (the ships this serves), claude/greylock-time-machine.md (the first payload) and claude/machine-catalogue.md. Status: v0.2 built, tested (21 checks), delivered in chat as tessera-v0.2.zip; the first thing we say is the Greylock ledger (chosen because a stranger can check it; the ship is the second payload).*

## 0. The premise and the limits

A time machine is a channel between epochs, and a channel needs a code both ends can learn; every ship in the catalogue has a receiver who shares no context with the sender (Vigil's sleepers, Nautilus's descendants, the Lantern's far mouth, whoever reads the Greylock ledger in 500 years). Three limits, stated: nothing is "universal" — the design spends assumptions one at a time and names each; nothing reaches the past (the audit in Where Are the Time Travellers? closes that channel) — beings from the past who arrive later are readers with older context; for other universes mathematics goes first and physics is an optional rung. The name: a tessera was a token broken in two so strangers could recognise each other later by matching the halves.

## 1. The ladder (v0.2)

Every glyph is defined only by examples using glyphs already taught (Freudenthal's Lincos 1960; the Cosmic Call pages 1999/2003; Minsky's 1985 argument that any problem-solving intelligence meets counting first).

0. mark and gap — 8-bit glyph codes, all 1xxxxxxx (the constant column reveals the width; sixteen zeros never occur, so 24 zeros + 1 is the frame mark)
1. counting — · ·· ··· beside binary names (assumes discreteness)
2. arithmetic — + − × ÷ < > = by example triples, brackets (assumes pattern-finding)
3. truth — ⊤ ⊥ after checkable statements; ¬ ∧ ∨ ⊃ by truth tables; a first variable law (a + b = b + a)
4. the machine — Peano ∅ and S, rewrite rules ≝ … ⇒ …, worked reductions of add/mul/double cross-checked against rung 2; then binary numerals inside terms (( S 10 ) = 11) with a separator glyph between adjacent numerals
4b. pictures as programs — lists (cons, cat) and points (pt); row, col, rect as rewrite rules with worked reductions; then the shape of every one of the 73 glyphs stated as a program (≝ ( shape 1 ) ⇒ ( col 10 , 0 , 111 ); the delimiter's own shape as ( shape ) ⇒ …); then the ship as a program (a 15 × 31 Tower cross-section: hull, six decks, engine block, cabin). A picture is a list of pairs, so no eyes are assumed; the alphabet describes itself
5. anchors — the hydrogen page (drawn); tick = period, wave = wavelength, so c = 1; the pulsar stamp (skippable)
6. payload — the Greylock ledger in hydrogen units, all integers (clock A 5,008 waves above clock B; the summit clock gains 14.15 ticks per 122,723,056,952,755-tick day); or the ship
7. dialogue, after Lincos — Ha and Hb speak (Ha say Hb ( … )); questions ? a ( 2 + a = 5 ) and answers ( a = 3 ); good follows only true answers and bad only false ones (checkable); know (after a good answer) and the law (Ha know b ∧ Hb say Ha ? b) ⊃ Ha say Hb b; want (before a question) and its law; the walk with target and danger as wanting and not-wanting; help (what one cannot do alone, done by the other); then we and you: we want you to know the ledger, we do not know pulsar 1's period where you are, we ask you for it and want you to tell us — the message asks for the reader's epoch

## 2. The glyphs (v0.2)

Every glyph is a program of PT / ROW / COL / RECT primitives on a 5 × 7 grid; its bitmap is what the program draws, and the same primitives are machine rules, so the message states each glyph's shape in its own language. Families carry role: machine words a bar above, physics words a column either side, dialogue words four corner points; numbers, operators and logic bare. 73 glyphs, every pair at least six pixels apart. `tessera glyphs --export glyphs.txt` writes the programs with their art for Shriya to redraw; the package reads an edited file back. (The procedural inner marks of the nouns are placeholders by design; the hand set — numbers, operators, logic, machine and the key physics and dialogue words — is drawn.)

## 3. The code (Python, standard library; 21 tests passing)

* `glyphs.py` — the programs, the families, the renderer, export/import.
* `message.py` — the ladder, both payloads, the dialogues, the ship picture; `transcript()`. 10,733 glyphs, 85,864 bits.
* `machine.py` — term rewriting with ints as numerals (∅ matches 0, (S v) matches k > 0, (S k) ⇒ k + 1), arithmetic and drawing rules, `points`/`render`, `program_term`, tokens/parse with the separator.
* `units.py`, `stamp.py`, `bits.py` — as v0.1 (hydrogen units; the pulsar stamp dating 12,345 years to ±0.08; frame marks, repetition, Hamming).
* `pages.py` — 211 × 223 prime pages with parity; the hydrogen page; the pictures page (four glyph programs and the ship beside what they draw); the key sheet.
* `listen.py` — the stranger: from bits alone, width 8, alphabet 73, Zipf −1.9, H2 2.1 vs H1 3.9 bits; then · 0 1 ⏎ = + − × ÷ < > ⊤ ⊥ ( ) and, new, the variable a and good/bad by checking each answer against its question — eighteen glyphs, no key.
* Self-checks in the tests: every ⇒ chain is a valid step-by-step reduction; every glyph's shape program draws that glyph; the ship program draws a hull with decks and an engine; every good answer is true and every bad one false.
* `harness.py` — the blind packet (rubric now covers the rules, the pictures and the dialogue) and scorer. Not yet run on anyone.

## 4. Open threads

* Run the blind packet on a person and on a fresh model (the only external test); score rungs 4–7.
* The atom as a program (the hydrogen anchor without a drawing); sequences of pictures (the clocks running).
* The physical tessera: a 50-mm etched disc with the counting ladder eye-readable and the pages at microscope scale (Rosetta-disk scale ladder); nickel or quartz; a local laser engraver for the first one.
* Shriya's own glyph set via glyphs.txt.
* Possible X piece: "A Message That Teaches Itself".

---

*v0.1 checked into this repository 20 October 2026 and audited (claude/tessera-audit.md §v0.1 — one bug found and fixed in-repo); superseded in place by v0.2 the same day, re-audited in the same file's v0.2 section. Git history holds v0.1 and the fix.*
