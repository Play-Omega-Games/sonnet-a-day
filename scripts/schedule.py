#!/usr/bin/env python3
"""Reading calendar for a Sonnet a Day owner.

python3 scripts/schedule.py START_DATE PACE [--start-day N] [--bonus end|off] [--paused D1,D2..]
  PACE: daily | weekdays | every-other-day
Prints JSON: [{"date": "YYYY-MM-DD", "day": N, "title": ...}, ...] and the finish date.
Rules (same as the daily skill):
- daily: every calendar date from START_DATE.
- weekdays: Monday to Friday only.
- every-other-day: START_DATE, then every second calendar date (even offsets).
- paused dates deliver nothing and push the rest back; they never count as missed.
- bonus off: the plan ends after the last kept sonnet (Quarto 154).
"""
import datetime as dt, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACES = ("daily", "weekdays", "every-other-day")

def is_reading_day(date, start, pace):
    if pace == "daily": return True
    if pace == "weekdays": return date.weekday() < 5
    if pace == "every-other-day": return (date - start).days % 2 == 0
    raise ValueError(pace)

def calendar(start, pace, start_day=1, bonus="end", paused=(), plan=None):
    plan = plan or json.load(open(os.path.join(ROOT, "plans", "sonnets.json")))
    days = [d for d in plan["days"] if bonus == "end" or d["kind"] == "sonnet"]
    days = [d for d in days if d["day"] >= start_day]
    out, date, paused = [], start, set(paused)
    while len(out) < len(days):
        if date not in paused and is_reading_day(date, start, pace):
            d = days[len(out)]
            out.append({"date": date.isoformat(), "day": d["day"], "title": d["title"]})
        date += dt.timedelta(days=1)
    return out

if __name__ == "__main__":
    a = sys.argv[1:]
    start = dt.date.fromisoformat(a[0]); pace = a[1]
    sd = int(a[a.index("--start-day") + 1]) if "--start-day" in a else 1
    bonus = a[a.index("--bonus") + 1] if "--bonus" in a else "end"
    paused = [dt.date.fromisoformat(x) for x in a[a.index("--paused") + 1].split(",")] if "--paused" in a else []
    cal = calendar(start, pace, sd, bonus, paused)
    print(json.dumps({"finish": cal[-1]["date"], "count": len(cal), "days": cal}, indent=1))
