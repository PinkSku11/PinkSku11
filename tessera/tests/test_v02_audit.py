"""Regression tests from the v0.2 audit (20 Oct 2026).

1. The design trap: an artist who edits only the ART rows of glyphs.txt (the
   workflow the record describes) must be warned, not silently ignored —
   programs are authoritative, art is decoration.
2. Program edits still take, and the full 73-glyph round-trip holds.
3. The ship program really draws its decks (the shipped test asserts hull and
   engine only; the record claims decks too).
"""
import importlib

import pytest

from tessera import glyphs, machine, message


def _export(tmp_path):
    importlib.reload(glyphs)
    p = tmp_path / "glyphs.txt"
    glyphs.export(str(p))
    return p


def test_full_round_trip_replaces_all_73(tmp_path):
    p = _export(tmp_path)
    assert glyphs.load_overrides(str(p)) == len(glyphs.NAMES) == 73
    importlib.reload(glyphs)


def test_art_only_edit_warns_and_programs_stay_authoritative(tmp_path):
    p = _export(tmp_path)
    before = glyphs.bitmap("DOT")
    lines = p.read_text().split("\n")
    # repaint DOT's art solid without touching its program
    out, in_dot = [], False
    for ln in lines:
        if ln.strip() == "DOT":
            in_dot = True
        elif ln.strip() in glyphs.ID and ln.strip() != "DOT":
            in_dot = False
        if in_dot and ln.lstrip().startswith("|"):
            out.append("  | #####")
        else:
            out.append(ln)
    p.write_text("\n".join(out))
    with pytest.warns(UserWarning, match="DOT"):
        n = glyphs.load_overrides(str(p))
    assert n == 73
    assert glyphs.bitmap("DOT") == before          # the art edit changed nothing
    importlib.reload(glyphs)


def test_program_edit_takes_and_matching_art_stays_silent(tmp_path, recwarn):
    p = _export(tmp_path)
    text = p.read_text()
    # DOT's program is a single PT; move the point and delete its stale art
    assert "\nDOT\n" in text
    head, _, rest = text.partition("\nDOT\n")
    sec, _, tail = rest.partition("\n\n")
    prog_only = "\n".join(ln for ln in sec.split("\n") if not ln.lstrip().startswith("|"))
    prog_only = prog_only.replace("PT 2 3", "PT 0 0")
    p.write_text(head + "\nDOT\n" + prog_only + "\n\n" + tail)
    assert glyphs.load_overrides(str(p)) == 73
    assert glyphs.bitmap("DOT")[0][0] == 1
    assert not any("DOT" in str(w.message) for w in recwarn.list)
    importlib.reload(glyphs)


def test_ship_program_draws_its_decks():
    pts = machine.points(machine.program_term(message.SHIP_PICTURE))
    deck_rows = [y for y in range(1, 30) if (7, y) in pts]
    assert len(deck_rows) >= 4, f"expected several deck rows crossing x=7, got {deck_rows}"
    assert (7, 10) not in pts                      # the cabin stays empty
