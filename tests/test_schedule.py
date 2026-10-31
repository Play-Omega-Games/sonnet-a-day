"""Pace and calendar checks. Run: python3 tests/test_schedule.py"""
import datetime as dt, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
from schedule import calendar

D = dt.date
def test_daily_finish():
    c = calendar(D(2026, 11, 9), "daily", bonus="off")
    assert len(c) == 154 and c[0]["date"] == "2026-11-09" and c[-1]["date"] == (D(2026, 11, 9) + dt.timedelta(153)).isoformat()
    assert c[-1]["title"] == "Sonnet 154"

def test_bonus_end_adds_days():
    assert len(calendar(D(2026, 11, 9), "daily")) == len(calendar(D(2026, 11, 9), "daily", bonus="off")) + 9

def test_weekdays_skip_weekends():
    c = calendar(D(2026, 11, 7), "weekdays")   # a Saturday
    assert c[0]["date"] == "2026-11-09"          # first reading is Monday
    assert all(D.fromisoformat(x["date"]).weekday() < 5 for x in c)

def test_every_other_day():
    c = calendar(D(2026, 11, 9), "every-other-day", bonus="off")
    ds = [D.fromisoformat(x["date"]) for x in c]
    assert all((b - a).days == 2 for a, b in zip(ds, ds[1:]))

def test_pause_pushes_back_without_skipping():
    p = [D(2026, 11, 10), D(2026, 11, 11)]
    c = calendar(D(2026, 11, 9), "daily", paused=p, bonus="off")
    assert [x["day"] for x in c[:3]] == [1, 2, 3] and c[1]["date"] == "2026-11-12"

def test_start_mid_sequence():
    c = calendar(D(2026, 11, 9), "daily", start_day=127, bonus="off")
    assert c[0]["title"] == "Sonnet 127" and len(c) == 28

if __name__ == "__main__":
    fails = 0
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            try: f(); print("ok  ", n)
            except AssertionError as e: fails += 1; print("FAIL", n, e)
    print(f"{sum(1 for n in globals() if n.startswith('test_')) - fails} passed, {fails} failed")
    sys.exit(1 if fails else 0)
