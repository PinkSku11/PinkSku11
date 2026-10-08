import json

from greylock import ledger


def test_chain_verifies_and_detects_tampering(tmp_path):
    lg = ledger.Ledger(tmp_path, "summit")
    t0 = 1_800_000_000.0
    for i in range(50):
        lg.append({"t": t0 + i, "site": "greylock_summit", "clock": "CS1", "ti_ns": 100.0 + i})
    lg.close()
    ok, msg = ledger.verify(tmp_path, "summit")
    assert ok, msg

    # restart continues the same chain
    lg2 = ledger.Ledger(tmp_path, "summit")
    assert lg2.seq == 50
    lg2.append({"t": t0 + 50, "site": "greylock_summit", "clock": "CS1", "ti_ns": 150.0})
    lg2.close()
    ok, msg = ledger.verify(tmp_path, "summit")
    assert ok and "51 records" in msg

    # tamper with one value
    files = sorted(tmp_path.glob("summit-*.jsonl"))
    lines = files[0].read_text().splitlines()
    rec = json.loads(lines[10])
    rec["ti_ns"] = 999.0
    lines[10] = json.dumps(rec, sort_keys=True, separators=(",", ":"))
    files[0].write_text("\n".join(lines) + "\n")
    ok, msg = ledger.verify(tmp_path, "summit")
    assert not ok and "seq 10" in msg


def test_commitments_per_day(tmp_path):
    lg = ledger.Ledger(tmp_path, "home")
    t0 = 1_800_000_000.0
    for i in range(3 * 86400 // 3600):           # one record an hour for three days
        lg.append({"t": t0 + i * 3600, "site": "cambridge", "clock": "CS2", "ti_ns": 1.0})
    lg.close()
    c = ledger.commitments(tmp_path, "home")
    assert len(c) >= 3 and all(len(h) == 64 for _, h, _ in c)
    p = ledger.write_commitments(tmp_path, "home")
    assert p.exists() and len(p.read_text().splitlines()) >= 4
