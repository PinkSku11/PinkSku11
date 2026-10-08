"""Append-only, hash-chained measurement ledger.

Every record is a JSON object on one line.  Each carries the SHA-256 of the
previous record ("prev") and its own hash ("hash"), computed over the canonical
JSON of the record without the hash field.  Editing, deleting or reordering any
record after the fact breaks the chain from that point on, and `verify()` says
where.  One file per UTC day; the chain runs across files.

The last hash of each day is the day's *commitment*: a 64-character string to
post publicly (X, a repo, anywhere with a timestamp) so that the raw data can be
shown, later, to be the data that existed on that day.  This is the same
mechanism as the Threshold Logbook, applied to clocks.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

GENESIS = "0" * 64


def canonical(record: dict) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def record_hash(prev: str, record_without_hash: dict) -> str:
    h = hashlib.sha256()
    h.update(prev.encode("utf-8"))
    h.update(canonical(record_without_hash).encode("utf-8"))
    return h.hexdigest()


def _day_of(t_unix: float) -> str:
    return datetime.fromtimestamp(t_unix, tz=timezone.utc).strftime("%Y-%m-%d")


class Ledger:
    """Writer.  `station` names the file set, e.g. 'summit' or 'home'."""

    def __init__(self, directory: str | os.PathLike, station: str):
        self.dir = Path(directory)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.station = station
        self.prev = GENESIS
        self.seq = 0
        self._fh = None
        self._day = None
        self._resume()

    # -- resume from existing files so restarts keep one unbroken chain ------
    def _files(self) -> list[Path]:
        return sorted(self.dir.glob(f"{self.station}-*.jsonl"))

    def _resume(self):
        files = self._files()
        if not files:
            return
        last = None
        with files[-1].open("rb") as fh:
            for line in fh:
                if line.strip():
                    last = line
        if last:
            rec = json.loads(last)
            self.prev = rec["hash"]
            self.seq = rec["seq"] + 1

    def _open_for(self, t_unix: float):
        day = _day_of(t_unix)
        if day != self._day:
            if self._fh:
                self._fh.close()
            self._day = day
            path = self.dir / f"{self.station}-{day}.jsonl"
            self._fh = path.open("a", encoding="utf-8")

    def append(self, record: dict) -> str:
        """Append a record (a dict without seq/prev/hash); returns its hash."""
        t = float(record.get("t", time.time()))
        self._open_for(t)
        rec = dict(record)
        rec["seq"] = self.seq
        rec["prev"] = self.prev
        rec["station"] = self.station
        h = record_hash(self.prev, rec)
        rec["hash"] = h
        self._fh.write(canonical(rec) + "\n")
        self._fh.flush()
        self.prev = h
        self.seq += 1
        return h

    def close(self):
        if self._fh:
            self._fh.close()
            self._fh = None


def iter_records(directory: str | os.PathLike, station: str | None = None) -> Iterator[dict]:
    """Yield every record of every ledger file in the directory, in chain order."""
    d = Path(directory)
    pattern = f"{station}-*.jsonl" if station else "*.jsonl"
    for path in sorted(d.glob(pattern)):
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)


def verify(directory: str | os.PathLike, station: str) -> tuple[bool, str]:
    """Walk the chain; return (ok, message)."""
    prev = GENESIS
    n = 0
    expected_seq = 0
    for rec in iter_records(directory, station):
        body = {k: v for k, v in rec.items() if k != "hash"}
        if rec.get("prev") != prev:
            return False, f"chain break before seq {rec.get('seq')}: prev mismatch"
        if rec.get("seq") != expected_seq:
            return False, f"sequence gap at seq {rec.get('seq')} (expected {expected_seq})"
        if record_hash(prev, body) != rec.get("hash"):
            return False, f"hash mismatch at seq {rec.get('seq')}"
        prev = rec["hash"]
        expected_seq += 1
        n += 1
    return True, f"{n} records, chain intact, head {prev[:16]}…"


def commitments(directory: str | os.PathLike, station: str) -> list[tuple[str, str, int]]:
    """(day, last hash of that day, record count) for every day in the ledger."""
    out: dict[str, tuple[str, int]] = {}
    for rec in iter_records(directory, station):
        day = _day_of(float(rec["t"]))
        h, n = out.get(day, ("", 0))
        out[day] = (rec["hash"], n + 1)
    return [(day, h, n) for day, (h, n) in sorted(out.items())]


def write_commitments(directory: str | os.PathLike, station: str) -> Path:
    path = Path(directory) / f"{station}-commitments.txt"
    with path.open("w", encoding="utf-8") as fh:
        fh.write("# day  sha256-of-last-record  records   (post each line publicly, the day it closes)\n")
        for day, h, n in commitments(directory, station):
            fh.write(f"{day} {h} {n}\n")
    return path
