# tessera v0.2 — a message that teaches itself

*A tessera was a token broken in two so that strangers could recognise each other
years later by matching the halves.*  This is the protocol layer of the time
machines: the code a reader who shares nothing with us — not language, not
culture, not era, maybe not physics — can learn from the message alone.

Pure Python 3 standard library. No installs. (`pytest` for the tests.)

## The ladder

Every glyph is defined only by examples that use glyphs already taught.

| rung | lesson | the one new assumption it spends |
|---|---|---|
| 0 | mark and gap: 8-bit glyph codes, all `1xxxxxxx`; frame = 24 zeros then a 1 | the reader can tell a thing from its absence |
| 1 | `·` `··` `···` beside their binary names | discreteness: things can be counted |
| 2 | `+ − × ÷ < > =` by example triples; brackets | the reader finds patterns |
| 3 | `⊤ ⊥` after statements it can check; `¬ ∧ ∨ ⊃` by truth tables | — |
| 4 | the machine: `∅`, `S`, rewrite rules `≝ … ⇒ …`, worked reductions cross-checked against rung 2; then binary numerals inside terms (`( S 10 ) = 11`) | the reader can follow rules — after this, anything written as rules is a program |
| 4b | **pictures as programs**: lists (`cons`, `cat`), points (`pt`), `row`, `col`, `rect` as rules; worked reductions; then **the shape of every glyph as a program** — `≝ ( shape 1 ) ⇒ ( col 10 , 0 , 111 )` — and the ship as a program | nothing new: a picture is a list of pairs, which any 2-D sense can realise. The alphabet describes itself; the reader who runs the rules gets the typeface back |
| 5 | anchors: the hydrogen page (drawn); tick = its period, wave = its wavelength, so c = 1; the pulsar stamp | shared physics — readers from elsewhere skip this rung and lose nothing below it |
| 6 | the payload: the Greylock ledger (clock A is 5,008 waves above clock B; g; the rate; the summit clock gains 14.15 ticks per 122,723,056,952,755-tick day) or the ship | — |
| 7 | **dialogue, after Lincos**: Ha and Hb speak; questions `? a ( 2 + a = 5 )` and answers `( a = 3 )`; `good` follows only true answers and `bad` only false ones, so a reader can check them; `know` (after a good answer), `want` (before a question), the walk with `target` and `danger`, `help` (what one cannot do alone); then `we` and `you`: we want you to know the ledger, we do not know when you are, and we ask you for pulsar 1's period | the thinnest rung is now a story the reader can verify line by line |

`python -m tessera speak` prints the whole transcript; the message is 10,733 glyphs,
85,864 bits, twelve glyph pages plus the hydrogen page and the pictures page.

## The glyphs are programs

A glyph is a list of primitives — `PT x y`, `ROW y x n`, `COL x y n`, `RECT x y w h` — on a
5 × 7 grid, and its bitmap is what the program draws.  The families carry role: machine
words have a bar above, physics words a column either side, dialogue words four corner
points; numbers, operators and logic are bare.  Every pair of glyphs differs in at least
six pixels.  `python -m tessera glyphs --export glyphs.txt` writes the programs with their
art; edit the program lines (keep the names) and every command reads them back.

## Run it

```bash
cd tessera
python -m tessera speak --payload greylock --out out   # bits, pages (PNG/PBM), transcript, key
python -m tessera listen out/message.bits               # the stranger's decode, no key
python -m tessera stamp --years 12345                   # date the message from "today's" pulsars
python -m tessera packet --prefix out/blind             # the blind-test packet for a person or a model
python -m tessera glyphs --export glyphs.txt --sheet key.png   # draw your own shapes here
python -m pytest tests                                  # 21 checks
```

Put an edited `glyphs.txt` in the working directory and every command uses your shapes.

## What the stranger recovers

`listen.decode_blind` gets only the bits.  It finds the token width (the constant
column), the alphabet (73 glyphs), the Zipf slope (−1.9) and the conditional entropy
(2.1 bits against 3.9 unconditional — structured, not noise), then the delimiter and the
counting mark as the only pair for which the statements form a binary-consistent
counting ladder, then both digits, then `= + − × ÷ < >` from the example triples, `⊤ ⊥`
and the bracket pair from the truth lines, and — new in v0.2 — the variable `a` and
`good` and `bad` from the dialogues, by checking each answer against its question.
Eighteen glyphs, correctly, with no key.  Noise fails at the first step.  Rungs 4–6 are
not yet machine-decoded; the packet exists so a person or a fresh language model can try.

The tests also check the message against itself: every `⇒` chain is a real step-by-step
reduction, every glyph's `shape` program draws that glyph, the ship program draws a hull
with decks and an engine, and every answer judged `good` is true and every `bad` false.

## The stamp

Twelve pulsars as (period in milli-ticks, 1/Ṗ).  A reader any time later measures
today's periods; `stamp.decode` finds the one Δt that fits them all — 12,345 years
recovered to ±0.08 yr in the test, 0.5 years to ±0.01.  Catalogue values are
approximate: replace them from a current ephemeris before etching anything.

## Pages

211 × 223 pixels, both prime, so a bit string of that length unfolds one way.  The
last column and row hold parities; one flipped pixel is located to its row and
column.  The pictures page shows four glyph programs and the ship program beside what
they draw, for a reader with eyes.  Three copies with majority vote correct any error
that hits one copy (the test flips 0.03% of bits across three copies and 0.3% across
five); Hamming(7,4) is there for our own archives.

## Honest gaps

- Rung 7 is checkable but small: nine exchanges, one law each for knowing, wanting and helping. Lincos spent a hundred pages here.
- The hydrogen page is a drawing, not a derivation; a reader must recognise an atom. The next step is the atom as a program too.
- The pictures are static. Sequences of pictures (time as a list of lists) would let the machine show the clocks running.
- No one has yet run the blind packet. The automated listener is the only stranger so far.

## Sources

Freudenthal, *Lincos: Design of a Language for Cosmic Intercourse* (1960) · Dutil & Dumas, Cosmic Call (1999, 2003) ·
Minsky, "Communication with Alien Intelligence" (1985) · Sagan et al., the Arecibo message (1974) and the Pioneer plaque (1972) ·
Sandia report SAND92-1382, markers for the WIPP site (1993) · Long Now Foundation, the Rosetta Disk · Doyle et al., information theory and animal communication (2011) ·
Ollongren, *Astrolinguistics* (2013) · Fitzpatrick, CosmicOS.
