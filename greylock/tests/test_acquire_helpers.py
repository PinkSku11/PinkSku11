import json
import threading
import time
from pathlib import Path

from greylock import config
from greylock.acquire import RollingRawLog, free_gb, run, sd_notify
from greylock.ledger import verify

EXAMPLE = Path(__file__).parent.parent / "station.example.toml"


def test_rolling_raw_log_rolls_at_midnight_with_station_names(tmp_path):
    log = RollingRawLog(tmp_path, min_free_gb=0.0, station="summit")
    day1 = 1_800_000_000.0                      # some UTC instant
    day2 = day1 + 86400.0
    assert log.write(b"aa", day1) is None
    assert log.write(b"bb", day2) is None
    log.close()
    files = sorted(tmp_path.glob("ubx-summit-*.bin"))   # named per station: two stations'
    assert len(files) == 2                              # dirs can merge without clobbering
    assert files[0].read_bytes() == b"aa" and files[1].read_bytes() == b"bb"


def test_rolling_raw_log_suspends_on_low_disk(tmp_path):
    log = RollingRawLog(tmp_path, min_free_gb=1e9)   # nobody has an exabyte free
    ev = log.write(b"aa", 1_800_000_000.0)
    assert ev is not None and "suspended" in ev
    assert log.suspended and not list(tmp_path.glob("ubx-*.bin"))
    # once per state change, not once per write
    assert log.write(b"bb", 1_800_000_000.0 + 1) is None


def test_rolling_raw_log_rechecks_disk_within_the_day(tmp_path):
    # the reserve must not be eaten between midnights (review finding)
    log = RollingRawLog(tmp_path, min_free_gb=0.0)
    t0 = 1_800_000_000.0
    assert log.write(b"aa", t0) is None and not log.suspended
    log.min_free_gb = 1e9                            # disk "fills up" mid-day
    assert log.write(b"bb", t0 + 30) is None         # inside the 60 s check interval
    ev = log.write(b"cc", t0 + 61)                   # next periodic check catches it
    assert ev is not None and "suspended" in ev and log.suspended
    log.min_free_gb = 0.0                            # space freed: quiet retry, then resume
    ev = log.write(b"dd", t0 + 122)
    assert ev is not None and "resumed" in ev and not log.suspended
    log.close()


def test_rolling_raw_log_does_not_flood_on_persistent_open_failure(tmp_path):
    # a path blocked by a stray file must yield ONE suspend event, not one per
    # serial chunk (review finding)
    blocker = tmp_path / "blocker"
    blocker.write_text("i am a file, not a directory")
    log = RollingRawLog(blocker / "ubx", min_free_gb=0.0)
    t0 = 1_800_000_000.0
    ev = log.write(b"aa", t0)
    assert ev is not None and "suspended" in ev
    events = [log.write(b"bb", t0 + 1 + i) for i in range(120)]   # two check intervals
    assert all(e is None for e in events)            # stays suspended, quietly


def test_sd_notify_is_a_noop_outside_systemd(monkeypatch):
    monkeypatch.delenv("NOTIFY_SOCKET", raising=False)
    sd_notify("READY=1")                        # must not raise
    monkeypatch.setenv("NOTIFY_SOCKET", "/nonexistent/notify")
    sd_notify("WATCHDOG=1")                     # must swallow the OSError


def test_free_gb_positive(tmp_path):
    assert free_gb(tmp_path) > 0


def test_simulated_acquire_writes_a_valid_chain(tmp_path):
    text = EXAMPLE.read_text().replace('ledger_dir = "data/ledger"',
                                       f'ledger_dir = "{tmp_path.as_posix()}/led"')
    text = text.replace('site = "greylock_summit"', 'site = "greylock_summit"', 1)
    p = tmp_path / "station.toml"
    p.write_text(text)
    cfg = config.load(p)
    stop = threading.Event()
    n = run(cfg, simulate=True, max_records=3, stop=stop)
    assert n == 3
    ok, msg = verify(cfg.ledger_dir, "greylock_summit")
    assert ok, msg
    status = json.loads((cfg.ledger_dir / "greylock_summit-status.json").read_text())
    assert status["records"] >= 1 and status["clock"] == "CS1"
