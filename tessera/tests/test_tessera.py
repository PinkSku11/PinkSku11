"""tessera v0.1: the message round-trips, the stranger decodes it, the stamp dates it."""
import pytest

from tessera import bits as B
from tessera import glyphs, harness, listen, machine, message, pages, stamp, units


@pytest.fixture(scope="module")
def msg():
    return message.build("both")


# ---- glyphs and bits --------------------------------------------------------------------------

def test_glyphs_are_distinct_and_sized():
    shapes = list(glyphs.GLYPHS.values())
    assert all(len(g) == 7 and all(len(r) == 5 for r in g) for g in shapes)
    for i, a in enumerate(shapes):
        for b in shapes[i + 1:]:
            assert glyphs._distance(a, b) >= 6


def test_codes_have_leading_one_and_round_trip(msg):
    raw = B.encode(msg.tokens)
    assert len(raw) == 8 * len(msg.tokens)
    assert all(raw[i] == "1" for i in range(0, len(raw), 8))
    assert B.decode(raw) == msg.tokens
    assert "0" * 16 not in raw                      # so the frame mark is unambiguous
    assert B.unframe(B.frame(raw)) == raw


def test_repetition_and_hamming_survive_noise(msg):
    raw = B.frame(B.encode(msg.tokens))
    noisy = B.corrupt(B.repeat(raw, 3), 0.001, seed=3)
    assert B.vote(noisy, 3) == raw                      # three copies: survives 0.1% of bits flipped
    noisy5 = B.corrupt(B.repeat(raw, 5), 0.005, seed=4)
    assert B.vote(noisy5, 5) == raw                     # five copies: survives 0.5%
    h = B.corrupt(B.hamming_encode(raw), 0.0005, seed=5)
    assert B.hamming_decode(h)[:len(raw)] == raw


# ---- the ladder -----------------------------------------------------------------------------------

def test_every_statement_ends_and_numbers_are_binary(msg):
    assert msg.tokens[-1] == "END"
    assert message.value(message.number(1415)) == 1415


def test_arithmetic_lessons_are_true(msg):
    """Every  a op b = c  the message states must be true (the reader will check)."""
    ops = {"PLUS": lambda a, b: a + b, "MINUS": lambda a, b: a - b, "TIMES": lambda a, b: a * b, "DIV": lambda a, b: a // b}
    checked = 0
    for line in msg.lines():
        if len(line) >= 5 and "EQ" in line and line[0] in ("Z", "O"):
            parsed = listen.parse_numbers([glyphs.code(t) for t in line], glyphs.code("Z"), glyphs.code("O"))
            if len(parsed) == 5 and [k for k, _ in parsed] == ["num", "sym", "num", "sym", "num"]:
                op = glyphs.name_of(parsed[1][1])
                if op in ops:
                    assert ops[op](parsed[0][1], parsed[2][1]) == parsed[4][1]
                    checked += 1
    assert checked >= 20


def test_machine_agrees_with_arithmetic():
    for a in range(0, 6):
        for b in range(0, 6):
            assert machine.unpeano(machine.reduce(("ADD", machine.peano(a), machine.peano(b)))[-1]) == a + b
            assert machine.unpeano(machine.reduce(("MUL", machine.peano(a), machine.peano(b)))[-1]) == a * b
    t = ("DOUBLE", machine.peano(7))
    assert machine.unpeano(machine.reduce(t)[-1]) == 14
    assert machine.parse(machine.tokens(t)) == t


def test_greylock_numbers_in_hydrogen_units():
    assert units.GREYLOCK_HEIGHT_WAVES == 5008
    assert units.DAY_TICKS == 122_723_056_952_755
    assert units.LEAD_PER_DAY_CENTITICKS == 1415
    # the ledger is self-consistent: g × h × day = 14.15 ticks (c = 1)
    lead = (1.0 / units.G_DENOMINATOR) * units.GREYLOCK_HEIGHT_WAVES * units.DAY_TICKS
    assert lead == pytest.approx(14.15, abs=0.02)


# ---- the stranger ---------------------------------------------------------------------------------

def test_blind_decode_recovers_the_first_three_rungs(msg):
    r = listen.decode_blind(B.encode(msg.tokens))
    assert r["width"] == 8
    assert r["compressibility"] < 0.6
    m = r["meaning"]
    expect = {"DOT": "·", "Z": "0", "O": "1", "END": "⏎", "EQ": "=", "PLUS": "+", "MINUS": "−", "TIMES": "×",
              "DIV": "÷", "LT": "<", "GT": ">", "TRUE": "⊤", "FALSE": "⊥", "LP": "(", "RP": ")"}
    for name, sym in expect.items():
        assert m.get(glyphs.code(name)) == sym, name


def test_blind_decode_rejects_noise():
    import random
    rng = random.Random(1)
    noise = "".join(rng.choice("01") for _ in range(20000))
    r = listen.decode_blind(noise)
    assert r["compressibility"] > 0.9
    assert r.get("width") is None or r.get("digits") is None


def test_language_statistics(msg):
    toks = listen.tokenize(B.encode(msg.tokens), 8)
    assert -3.0 < listen.zipf_slope(toks) < -0.5
    assert listen.conditional_entropy(toks) < listen.entropy(toks)


# ---- pages ------------------------------------------------------------------------------------------

def test_pages_are_prime_sized_with_parity(msg):
    pgs = pages.paginate(msg.tokens)
    assert len(pgs) >= 4
    assert listen.unfold(pages.to_bits(pgs[0])) == [(211, 223)]
    assert pages.check_parity(pgs[0]) == ([], [])
    pgs[0][10][10] ^= 1
    assert pages.check_parity(pgs[0]) == ([10], [10])
    assert pages.check_parity(pages.hydrogen_page()) == ([], [])


# ---- the stamp ----------------------------------------------------------------------------------------

@pytest.mark.parametrize("years", [0.5, 100, 12_345, 1_000_000])
def test_stamp_dates_itself(years):
    enc = stamp.encode()
    r = stamp.decode(enc, stamp.aged(stamp.CATALOGUE, years))
    assert r["years"] == pytest.approx(years, rel=1e-3, abs=0.01)
    assert len(r["matches"]) >= 10


def test_stamp_tolerates_measurement_jitter():
    enc = stamp.encode()
    r = stamp.decode(enc, stamp.aged(stamp.CATALOGUE, 5000, jitter=1e-9))
    assert r["years"] == pytest.approx(5000, rel=0.02)


# ---- harness -------------------------------------------------------------------------------------------

def test_packet_and_score(tmp_path, msg):
    tr = harness.packet(msg.tokens, str(tmp_path / "blind"))
    assert (tmp_path / "blind-symbols.txt").exists()
    answer = {tr["PLUS"]: "+", tr["EQ"]: "=", tr["TIMES"]: "÷"}
    s = harness.score(answer, tr)
    assert s["hits"] == 2 and tr["TIMES"] in s["misses"]
