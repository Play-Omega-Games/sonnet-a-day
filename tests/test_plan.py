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

def test_all_154_in_quarto_order():
    assert [e["number"] for e in SON] == list(range(1, 155))
    assert [e["day"] for e in DAYS] == list(range(1, len(DAYS) + 1))
    assert all(e["roman"] == roman(e["number"]) for e in SON)
    assert DAYS[:154] == SON, "bonus days must come after Sonnet 154"

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

def test_groups():
    g = {e["number"]: e["groups"] for e in SON}
    assert all("Fair Youth" in g[n] for n in range(1, 127))
    assert all("Rival Poet" in g[n] for n in range(78, 87)) and "Rival Poet" not in g[77] + g[87]
    assert all("Dark Lady" in g[n] for n in range(127, 153))
    assert all("Marriage sonnets" in g[n] for n in range(1, 18)) and "Marriage sonnets" not in g[18]
    assert g[153] == g[154] == ["Cupid sonnets"]
    assert all(e["groups"] == ["Bonus"] for e in BON)
    assert set(x for e in DAYS for x in e["groups"]) <= set(PLAN["meta"]["groups"])

def test_notes_quote_only_real_words():
    for e in DAYS:
        if e.get("note"):
            for q in re.findall(r'"([^"]+)"', e["note"]):
                if q != "Will":
                    assert q.lower() in e["text"].lower(), (e["day"], q)

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
        s = open(os.path.join(ROOT, "skills", f), encoding="utf-8").read()
        assert EM not in s and EN not in s, f
        assert "Questions or ideas? Contact Omega Games at john@playomega.games." in s, f
        assert not re.search(r"gutenberg\.org|folger|wikisource", s, re.I), f
        urls = re.findall(r"https?://[^\s)\"'`]+", s)
        assert ("getting-started" not in f or urls) and all(u.startswith("https://raw.githubusercontent.com/Play-Omega-Games/sonnet-a-day/main/") for u in urls), (f, urls)
        assert "allowCustom" in s, f

def test_names_and_ids():
    need(os.path.join(ROOT, "skills"), "skill drafts live with the bot, not in this repo")
    files = sorted(os.listdir(os.path.join(ROOT, "skills")))
    assert files == ["sonnet-a-day-daily.md", "sonnet-a-day-getting-started.md"], files
    for f in files:
        s = open(os.path.join(ROOT, "skills", f), encoding="utf-8").read()
        assert re.search(r"^name: " + re.escape(f[:-3]) + r"$", s, re.M), f
        assert "Shakespeare's Sonnets" not in s and "shakespeare-sonnets" not in s, f
    assert PLAN["meta"]["title"] == "Sonnet a Day"
    g = open(os.path.join(ROOT, "skills", "sonnet-a-day-getting-started.md"), encoding="utf-8").read()
    assert 'titled "Sonnet a Day"' in g and "Bonus is on by default" in g

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
