# tessera v0.1 — a message that teaches itself

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
| 4 | the machine: `∅`, `S`, rewrite rules `≝ … ⇒ …`, worked reductions, a new definition; cross-checked against rung 2 | the reader can follow rules — after this, anything written as rules is a program |
| 5 | anchors: the hydrogen page (drawn); tick = its period, wave = its wavelength, so c = 1; the pulsar stamp | shared physics — readers from elsewhere skip this rung and lose nothing below it |
| 6 | the payload: the Greylock ledger (clock A is 5,008 waves above clock B; g; the rate; the summit clock gains 14.15 ticks per 122,723,056,952,755-tick day) or the ship | — |
| 7 | words: agent, target, danger, good, bad — by a short walk on the number line | the thinnest rung; needs the most work |

`python -m tessera speak` prints the whole transcript; the message is 3,711 glyphs,
29,688 bits, four glyph pages plus the hydrogen page.

## Run it

```bash
cd tessera
python -m tessera speak --payload greylock --out out   # bits, pages (PNG/PBM), transcript, key
python -m tessera listen out/message.bits               # the stranger's decode, no key
python -m tessera stamp --years 12345                   # date the message from "today's" pulsars
python -m tessera packet --prefix out/blind             # the blind-test packet for a person or a model
python -m tessera glyphs --export glyphs.txt --sheet key.png   # draw your own shapes here
python -m pytest tests                                  # 17 checks
```

Put an edited `glyphs.txt` in the working directory and every command uses your shapes.

## What the stranger recovers

`listen.decode_blind` gets only the bits.  It finds the token width (the constant
column), the alphabet (49 glyphs used), the Zipf slope (−1.8) and the conditional
entropy (1.6 bits against 3.3 unconditional — structured, not noise), then the
delimiter and the counting mark as the only pair for which the statements form a
binary-consistent counting ladder, then both digits, then `= + − × ÷ < >` from the
example triples, then `⊤ ⊥` and the bracket pair from the truth lines.  Fifteen
glyphs, correctly, with no key.  Noise fails at the first step.  That is the test
that rungs 1–3 are decodable; rungs 4–7 are not yet machine-decoded (the packet
exists so a person or a fresh language model can try them).

## The stamp

Twelve pulsars as (period in milli-ticks, 1/Ṗ).  A reader any time later measures
today's periods; `stamp.decode` finds the one Δt that fits them all — 12,345 years
recovered to ±0.08 yr in the test, 0.5 years to ±0.01.  Catalogue values are
approximate: replace them from a current ephemeris before etching anything.

## Pages

211 × 223 pixels, both prime, so a bit string of that length unfolds one way.  The
last column and row hold parities; one flipped pixel is located to its row and
column.  Three copies with majority vote survive 0.1% of bits flipped, five copies
0.5%; Hamming(7,4) is there for our own archives.

## Honest gaps

- Rung 7 is a sketch. Lincos taught behaviour with dialogues; this needs the same.
- The hydrogen page is a drawing, not a derivation; a reader must recognise an atom.
- The machine is taught but not used to *draw* — pictures-as-programs is the next step, and the step that removes the need for eyes.
- No one has yet run the blind packet. The automated listener is the only stranger so far.

## Sources

Freudenthal, *Lincos: Design of a Language for Cosmic Intercourse* (1960) · Dutil & Dumas, Cosmic Call (1999, 2003) ·
Minsky, "Communication with Alien Intelligence" (1985) · Sagan et al., the Arecibo message (1974) and the Pioneer plaque (1972) ·
Sandia report SAND92-1382, markers for the WIPP site (1993) · Long Now Foundation, the Rosetta Disk · Doyle et al., information theory and animal communication (2011) ·
Ollongren, *Astrolinguistics* (2013) · Fitzpatrick, CosmicOS.
