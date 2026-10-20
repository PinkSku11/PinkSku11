"""Regression test for the load_overrides comment-stripping bug (audit, 20 Oct 2026).

The exporter writes pixel rows that can begin with '#' (EQ's first row is
'#####'); the v0.1 loader treated every '#'-initial line as a comment and so
silently dropped 49 of the 55 glyphs — including any redrawn shapes.  The fix
counts a line as a comment only when it cannot be a 5-wide {#, .} pixel row.
"""
import importlib

from tessera import glyphs


def test_export_reload_round_trips_all_glyphs(tmp_path):
    importlib.reload(glyphs)            # pristine shapes
    p = tmp_path / "glyphs.txt"
    glyphs.export(str(p))
    n = glyphs.load_overrides(str(p))
    assert n == len(glyphs.NAMES) == 55


def test_an_edit_to_a_hash_initial_glyph_is_honoured(tmp_path):
    importlib.reload(glyphs)
    p = tmp_path / "glyphs.txt"
    glyphs.export(str(p))
    text = p.read_text()
    old = "\n".join(glyphs.GLYPHS["EQ"])          # first row '#####'
    new_rows = ["#...#", ".....", "#####", ".....", "#####", ".....", "#...#"]
    assert old in text
    p.write_text(text.replace("EQ\n" + old, "EQ\n" + "\n".join(new_rows), 1))
    n = glyphs.load_overrides(str(p))
    assert n == 55
    assert glyphs.GLYPHS["EQ"] == new_rows        # the redraw took
    importlib.reload(glyphs)                      # leave pristine for other tests


def test_real_comments_are_still_ignored(tmp_path):
    importlib.reload(glyphs)
    p = tmp_path / "glyphs.txt"
    p.write_text("# a comment line\n#!shebang-ish junk that is not a row\nDOT\n"
                 + "\n".join(glyphs.GLYPHS["DOT"]) + "\n")
    assert glyphs.load_overrides(str(p)) == 1
