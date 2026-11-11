"""Offline checks on plans/sonnets.json and the shipped skill drafts.
Run: python3 tests/test_plan.py (or python3 -m pytest tests -q)."""
import json, os, re, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PLAN = json.load(open(os.path.join(ROOT, "plans", "sonnets.json")))
DAYS = PLAN["days"]
SON = [e for e in DAYS if e["kind"] == "sonnet"]
BON = [e for e in DAYS if e["kind"] == "bonus"]
EM, EN = "\u2014", "\u2013"
SRC = os.path.join(ROOT, "src")
SKIP = {1, 4, 72}
KEPT = [n for n in range(1, 155) if n not in SKIP]

try:
    import pytest; Skip = pytest.skip.Exception
except ImportError:
    class Skip(Exception): pass

def need(path, why):
    """Skip a check whose inputs are not in this checkout (the source texts or the bot's skill drafts)."""
    if not os.path.exists(path):
        raise Skip(why)

def roman(n):
    s = ""
    for v, r in [(100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]:
        while n >= v: s += r; n -= v
    return s

def norm(s):
    return re.sub(r"\s+", " ", s.replace("_", "")).strip()

def test_151_in_quarto_order_with_skips():
    assert [e["number"] for e in SON] == KEPT
    assert [e["day"] for e in DAYS] == list(range(1, len(DAYS) + 1))
    assert all(e["roman"] == roman(e["number"]) for e in SON)
    assert DAYS[:151] == SON, "bonus days must come after the last kept sonnet"
    assert PLAN["meta"]["sonnets"] == 151 and PLAN["meta"]["omitted"] == [1, 4, 72]
    assert SON[0]["number"] == 2 and SON[0]["day"] == 1

# Assembled so the omitted word is not spelled out in the repo.
OMITTED = "nig" + "gard"

def test_omitted_wording_absent_from_served_data():
    blob = json.dumps(PLAN)
    assert OMITTED not in blob.lower()

def test_bonus_is_a_few_days():
    assert 3 <= len(BON) <= 10
    assert PLAN["meta"]["bonus"] == len(BON)

def test_line_counts():
    c = {e["number"]: e["lines"] for e in SON}
    assert c[99] == 15 and c[126] == 12
    assert all(v == 14 for k, v in c.items() if k not in (99, 126))
    for e in SON:
        assert e["lines"] == len(e["text"].split("\n")) == len([l for l in e["text"].split("\n") if l.strip()])
    assert [e["lines"] for e in BON if "Complaint" in e["title"]] and sum(e["lines"] for e in BON if "Complaint" in e["title"]) == 329
    assert [e for e in BON if "Phoenix" in e["title"]][0]["lines"] == 67

def test_text_is_exact_copy_of_source():
    need(SRC, "source texts not downloaded; run python3 scripts/build.py --fetch")
    src = norm(open(os.path.join(SRC, "pg1041.txt"), encoding="utf-8").read().replace("\r\n", "\n"))
    for e in SON:
        assert norm(e["text"]) in src, e["number"]
    for e in BON:
        n = re.search(r"pg(\d+)-images", e["full_text_link"]).group(1)
        s = norm(re.sub(r"\[_[^\]]*_\]", " ", open(os.path.join(SRC, f"pg{n}.txt"), encoding="utf-8").read()))
        for chunk in e["text"].split("\n\n"):
            for line in chunk.split("\n"):
                assert norm(line) in s, (e["title"], line)

def test_couplet_and_first_line():
    for e in SON:
        lines = e["text"].split("\n")
        assert e["first_line"] == lines[0]
        assert e["couplet"] == "\n".join(lines[-2:]) and e["couplet"] in e["text"]

def test_famous_lines_present():
    t = {e["number"]: e["text"] for e in SON}
    assert t[18].startswith("Shall I compare thee to a summer’s day?")
    assert "Let me not to the marriage of true minds" in t[116]
    assert t[130].startswith("My mistress’ eyes are nothing like the sun")
    assert "When in disgrace with fortune and men’s eyes" in t[29]
    assert 1 not in t and 4 not in t and 72 not in t

def test_groups():
    g = {e["number"]: e["groups"] for e in SON}
    for n in KEPT:
        if n <= 126:
            assert "Fair Youth" in g[n], n
        if n <= 17:
            assert "Marriage sonnets" in g[n], n
    assert all("Rival Poet" in g[n] for n in range(78, 87)) and "Rival Poet" not in g[77] + g[87]
    assert all("Dark Lady" in g[n] for n in range(127, 153))
    assert "Marriage sonnets" not in g[18]
    assert g[153] == g[154] == ["Cupid sonnets"]
    assert all(e["groups"] == ["Bonus"] for e in BON)
    assert set(x for e in DAYS for x in e["groups"]) <= set(PLAN["meta"]["groups"])

def test_notes_quote_only_real_words():
    def fold(s):
        return s.lower().replace("\u2019", "'").replace("\u2018", "'")
    for e in DAYS:
        if e.get("note"):
            for q in re.findall(r'"([^"]+)"', e["note"]):
                if q not in ("Will", "Bastards"):
                    assert fold(q) in fold(e["text"]), (e["day"], q)

def test_medium_notes_present():
    need_notes = {
        20: "Prick", 37: "Lame", 55: "Sluttish", 57: "Slave", 58: "Slave",
        66: "Strumpeted", 68: "Bastard", 89: "Lameness", 124: "Bastard",
        127: "Black", 129: "lust", 130: "Black wires", 131: "Black", 132: "foul",
        133: "Slave to slavery", 135: "Will", 136: "Will", 143: "Will",
        144: "Hell", 147: "Black as hell", 151: "Flesh",
    }
    by_num = {e["number"]: e for e in SON}
    for n, needle in need_notes.items():
        note = by_num[n].get("note") or ""
        assert needle.lower() in note.lower(), (n, note)
    lac2 = [e for e in BON if e["title"].endswith("part 2 of 3")][0]
    assert "Bastards" in (lac2.get("note") or "")

def test_links_are_gutenberg_html():
    for e in DAYS:
        assert re.match(r"^https://www\.gutenberg\.org/cache/epub/\d+/pg\d+-images\.html(#[\w.]+)?$", e["full_text_link"]), e["day"]
        assert e["verified"] is True
    assert all(e["look_for"] == e["roman"] for e in SON)

def test_no_em_dash_or_source_names_in_our_words():
    banned = re.compile(r"gutenberg|folger|wikisource|project", re.I)
    for e in DAYS:
        for k in ("title", "published", "source_notes", "note", "form"):
            v = e.get(k) or ""
            assert EM not in v and EN not in v, (e["day"], k)
            assert not banned.search(v), (e["day"], k)
    m = json.dumps(PLAN["meta"], ensure_ascii=False)
    assert EM not in m and not banned.search(m)

def test_no_junk_in_text():
    junk = re.compile(r"Project Gutenberg|\[Illustration|\bFootnote\b|CONTENTS|^\s*[CLXVI]+\s*$|\[_|_|\bExit\b|\bEnter\b", re.M)
    for e in DAYS:
        assert not junk.search(e["text"]), (e["day"], junk.search(e["text"]).group(0))

def test_skills_rules():
    need(os.path.join(ROOT, "skills"), "skill drafts live with the bot, not in this repo")
    for f in os.listdir(os.path.join(ROOT, "skills")):
        if not f.endswith(".md"):
            continue
        s = open(os.path.join(ROOT, "skills", f), encoding="utf-8").read()
        assert EM not in s and EN not in s, f
        assert "Questions or ideas? Contact Omega Games at john@playomega.games." in s, f
        assert not re.search(r"gutenberg\.org|folger|wikisource", s, re.I), f
        urls = re.findall(r"https?://[^\s)\"'`]+", s)
        assert ("getting-started" not in f or urls) and all(u.startswith("https://raw.githubusercontent.com/Play-Omega-Games/sonnet-a-day/main/") for u in urls), (f, urls)
        assert "allowCustom" in s, f
        assert "**This bot never...**" in s, f

def test_names_and_ids():
    need(os.path.join(ROOT, "skills"), "skill drafts live with the bot, not in this repo")
    files = sorted(f for f in os.listdir(os.path.join(ROOT, "skills")) if f.endswith(".md"))
    assert files == ["sonnet-a-day-daily.md", "sonnet-a-day-getting-started.md"], files
    for f in files:
        s = open(os.path.join(ROOT, "skills", f), encoding="utf-8").read()
        assert re.search(r"^name: " + re.escape(f[:-3]) + r"$", s, re.M), f
        assert "Shakespeare's Sonnets" not in s and "shakespeare-sonnets" not in s, f
        assert "of 151" in s or "151 sonnets" in s or "151 of the 154" in s, f
        assert OMITTED not in s.lower(), f
    assert PLAN["meta"]["title"] == "Sonnet a Day"
    g = open(os.path.join(ROOT, "skills", "sonnet-a-day-getting-started.md"), encoding="utf-8").read()
    assert 'titled "Sonnet a Day"' in g and "Bonus is on by default" in g
    assert "Sonnet 2" in g and "Start over at Sonnet 2" in g

if __name__ == "__main__":
    import sys
    fails = skips = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try: fn(); print("ok  ", name)
            except Skip as ex: skips += 1; print("skip", name, ex)
            except AssertionError as ex: fails += 1; print("FAIL", name, ex)
    print(f"{sum(1 for n in globals() if n.startswith('test_')) - fails - skips} passed, {fails} failed, {skips} skipped")
    sys.exit(1 if fails else 0)
