#!/usr/bin/env python3
"""Live link check for plans/sonnets.json.

For each unique page: HTTP 200. For each day: the #anchor (if any) exists and the passage sits inside that scene,
the opening words (first line) appear on the page, and for sonnets the
sonnet's numeral heading appears right before its opening words.
Usage: python3 scripts/check_links.py [plans/sonnets.json]
"""
import html, json, re, sys, time, urllib.request
from urllib.parse import urldefrag

PLAN = sys.argv[1] if len(sys.argv) > 1 else "plans/sonnets.json"
UA = {"User-Agent": "Mozilla/5.0 (sonnet-a-day link check)"}

def get(url, tries=4):
    err = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except Exception as e:
            err = e; time.sleep(3 * (i + 1))
    return getattr(err, "code", 0) or 0, ""

def words(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s)).replace("’", "'").replace("‘", "'")
    return re.sub(r"[^a-z0-9' ]", " ", s.lower()).split()

days = json.load(open(PLAN))["days"]
pages = {}
for d in days:
    pages.setdefault(urldefrag(d["full_text_link"])[0], []).append(d)

bad, checked = [], 0
for n, (url, ds) in enumerate(sorted(pages.items()), 1):
    status, body = get(url)
    print(f"[{n}/{len(pages)}] HTTP {status} {url} ({len(ds)} days)", flush=True)
    if status != 200:
        bad.append((url, f"HTTP {status}")); continue
    ids = set(re.findall(r'\b(?:id|name)="([^"]+)"', body))
    page = " ".join(words(body))
    for d in ds:
        frag = urldefrag(d["full_text_link"])[1]
        if frag and frag not in ids:
            bad.append((d["full_text_link"], f"day {d['day']}: anchor #{frag} missing"))
        opening = " ".join(words(d["first_line"]))
        if opening not in page:
            bad.append((url, f"day {d['day']}: opening words not found: {d['first_line']!r}"))
        if d.get("roman") and f"{d['roman'].lower()} {opening}" not in page:
            bad.append((url, f"day {d['day']}: heading {d['roman']} not followed by its opening words"))
        if frag:
            start = body.find(f'id="{frag}"')
            nxt = re.search(r'id="scene[^"]+"', body[start + 10:])
            scene = body[start: start + 10 + nxt.start()] if nxt else body[start:]
            if opening not in " ".join(words(scene)):
                bad.append((url, f"day {d['day']}: opening words not inside the scene that #{frag} opens"))
        checked += 1
    time.sleep(1)

print(f"\n{checked} days checked on {len(pages)} unique pages; {sum(1 for d in days if '#' in d['full_text_link'])} links carry an anchor")
if bad:
    print(f"{len(bad)} PROBLEMS"); [print(" ", u, why) for u, why in bad]; sys.exit(1)
print("ALL LINKS OK: every page returned 200, every anchor exists, every day's opening words are on its page")
