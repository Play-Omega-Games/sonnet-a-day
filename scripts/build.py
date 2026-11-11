#!/usr/bin/env python3
"""Build plans/sonnets.json: 151 of the 154 sonnets (1609 Quarto order,
modernized public-domain text; Quarto 1, 4 and 72 omitted) plus optional
bonus days, from the stored source files.

Usage: python3 scripts/build.py [--fetch]
  --fetch downloads any missing source file into src/ first.
Every text is copied exactly from its source file (line breaks kept, leading
indentation and the source's italic markers removed). Nothing is typed by hand.
"""
import html, json, os, re, sys, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
OUT = os.path.join(ROOT, "plans", "sonnets.json")
BASE = "https://www.gutenberg.org/cache/epub/{n}/pg{n}{s}"
BOOKS = [1041, 1513, 1510, 1521, 1543, 1525]   # sonnets, R&J, LLL, Henry V, A Lover's Complaint, Phoenix
UA = {"User-Agent": "Mozilla/5.0 (sonnet-a-day build)"}
# Quarto numbers omitted: wording that reads badly today.
SKIP = {1, 4, 72}

def fetch(n, suffix):
    path = os.path.join(SRC, f"pg{n}{suffix}")
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return
    url = BASE.format(n=n, s=suffix)
    for i in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90) as r:
                data = r.read()
            open(path, "wb").write(data); return
        except Exception as e:
            err = e; time.sleep(3 * (i + 1))
    raise SystemExit(f"could not download {url}: {err}")

def read(n, suffix=".txt"):
    return open(os.path.join(SRC, f"pg{n}{suffix}"), encoding="utf-8").read().replace("\r\n", "\n").replace("\ufeff", "")

def body(t):
    a = t.index("*** START OF"); a = t.index("\n", a) + 1
    return t[a:t.index("*** END OF")]

def clean(lines):
    out = []
    for l in lines:
        l = l.strip().replace("_", "")
        out.append(l)
    while out and not out[0]: out.pop(0)
    while out and not out[-1]: out.pop()
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out))

HEADING = re.compile(r"^[A-Z][A-Z ’']+\.?$")   # speaker names and section headings such as THRENOS
def roman(n):
    vals = [(100, "C"), (90, "XC"), (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    s = ""
    for v, r in vals:
        while n >= v: s += r; n -= v
    return s

def groups(n):
    g = []
    if n <= 126: g.append("Fair Youth")
    if n <= 17: g.append("Marriage sonnets")
    if 78 <= n <= 86: g.append("Rival Poet")
    if 127 <= n <= 152: g.append("Dark Lady")
    if n >= 153: g.append("Cupid sonnets")
    return g

# Short background facts and plain-English word glosses. Our own words, no em dashes.
# Medium-flag glosses explain archaic or loaded words for modern readers.
NOTES = {
    99: "This sonnet has 15 lines, one more than the usual 14.",
    126: "Twelve lines in six rhymed couplets. The 1609 Quarto prints two empty pairs of brackets where lines 13 and 14 would be. It closes the Fair Youth group.",
    138: "A different version of this sonnet was printed in The Passionate Pilgrim in 1599, ten years before the Quarto.",
    145: "Written in eight-syllable lines instead of the usual ten. Some readers hear a pun on the name Hathaway in \"hate away\".",
    153: "Sonnets 153 and 154 are two versions of one old Greek epigram about Cupid's torch.",
    154: "Sonnets 153 and 154 are two versions of one old Greek epigram about Cupid's torch. This is the last sonnet in the 1609 Quarto.",
    78: "Sonnets 78 to 86 are often read together as the Rival Poet sonnets, about another poet competing for the young man's favour.",
    20: "\"Prick’d\" here means marked or chosen; the line also plays on a bawdy sense of the word.",
    37: "\"Lame\" here is a metaphor for being held back by bad luck, not a judgment of disability.",
    55: "\"Sluttish\" here means dirty or neglected, not a slur about a person.",
    57: "\"Slave\" is a love metaphor for devoted service.",
    58: "\"Slave\" is a love metaphor for devoted service.",
    66: "\"Strumpeted\" means treated like a prostitute; the line is about virtue being abused.",
    68: "\"Bastard\" here means false or illegitimate (fake beauty), not a personal insult.",
    89: "\"Lameness\" here is figurative: the speaker offers to limp if the beloved finds fault.",
    124: "\"Bastard\" here means a child of chance, not a personal insult.",
    127: "The first of the Dark Lady sonnets (127 to 152). \"Black\" and \"foul\" contrast dark features with the older fashion for fair skin.",
    129: "A frank poem about lust and its aftermath.",
    130: "\"Black wires\" describes dark hair against the usual fair-haired ideal.",
    131: "\"Black\" here moves from complexion to a charge about her deeds.",
    132: "The couplet praises a dark complexion and calls fair ones \"foul\" by contrast.",
    133: "\"Slave to slavery\" is a love metaphor for being bound twice over.",
    135: "One of the \"Will\" sonnets: the word plays on a name, a wish, and sexual desire.",
    136: "One of the \"Will\" sonnets: the word plays on a name, a wish, and sexual desire.",
    143: "Ends with a lighter play on the name \"Will\".",
    144: "Also printed in The Passionate Pilgrim (1599). \"Hell\" here is a sexual image as well as a moral one.",
    147: "\"Black as hell\" is an insult aimed at the beloved, not a neutral color word.",
    151: "\"Flesh\" and \"rising\" are a bawdy image of arousal.",
}

def sonnets():
    t = body(read(1041))
    t = t[t.index("THE SONNETS"):]
    parts = re.split(r"\n([CLXVI]+)\n", "\n" + t)
    out = []
    for i in range(1, len(parts), 2):
        rn, txt = parts[i], parts[i + 1]
        n = len(out) + 1
        assert rn == roman(n), (rn, n)
        text = clean(txt.split("\n"))
        out.append((n, rn, text))
    assert len(out) == 154, len(out)
    return out

def anchor_before(n, first_line):
    """The id of the nearest scene anchor before the passage's first line in the HTML edition."""
    h = read(n, "-images.html")
    i = h.index(first_line.split(",")[0])
    ids = list(re.finditer(r'id="([^"]+)"', h[:i]))
    for m in reversed(ids):
        if not m.group(1).startswith(("pg-", "id-", "img_")):
            return m.group(1)
    return None

def passage(n, first, last, drop=r"^\[.*\]$"):
    t = body(read(n))
    a = t.index(first); a = t.rindex("\n", 0, a) + 1
    b = t.index(last, a); b = t.index("\n", b)
    lines = [l for l in t[a:b].split("\n") if not re.match(drop, l.strip())]
    lines = [re.sub(r"^\[_[^\]]*_\]\s*", "", l.strip()) for l in lines]
    return clean(lines)

def bonus():
    B = []
    rj = 1513
    B.append(dict(title="Romeo and Juliet: the Prologue", source=rj, form="Sonnet spoken by the Chorus",
                  text=passage(rj, "Two households, both alike in dignity", "our toil shall strive to mend."),
                  published="Romeo and Juliet (play first printed 1597)",
                  note="The play opens with a full Shakespearean sonnet: three quatrains and a couplet."))
    B.append(dict(title="Romeo and Juliet: the first meeting", source=rj, form="Shared sonnet, Act 1, Scene 5",
                  text="ROMEO.\n" + passage(rj, "If I profane with my unworthiest hand", "Then move not while my prayer"),
                  published="Romeo and Juliet (play first printed 1597)",
                  note="Romeo and Juliet's first fourteen lines together form one sonnet, split between the two speakers."))
    B.append(dict(title="Romeo and Juliet: Chorus to Act 2", source=rj, form="Sonnet spoken by the Chorus",
                  text=passage(rj, "Now old desire doth in his deathbed lie", "Tempering extremities with extreme sweet."),
                  published="Romeo and Juliet (play first printed 1597)", note=None))
    B.append(dict(title="Love's Labour's Lost: Longaville's sonnet", source=1510, form="Sonnet read aloud, Act 4, Scene 3",
                  text=passage(1510, "Did not the heavenly rhetoric of thine eye", "To lose an oath to win a paradise?"),
                  published="Love's Labour's Lost (play first printed 1598)",
                  note="A lord who has sworn off love reads out the love sonnet he has written, while his friends overhear."))
    B.append(dict(title="Henry V: the Epilogue", source=1521, form="Sonnet spoken by the Chorus",
                  text=passage(1521, "Thus far, with rough and all-unable pen", "In your fair minds let this acceptance take."),
                  published="Henry V (Epilogue first printed 1623)", note=None))
    lac = body(read(1543))
    lac = clean(lac[lac.index("From off a hill"):].split("\n"))
    stanzas = [s for s in lac.split("\n\n") if s.strip()]
    assert len(stanzas) == 47 and all(len(s.split("\n")) == 7 for s in stanzas), [len(s.split("\n")) for s in stanzas]
    cuts = [(0, 16), (16, 32), (32, 47)]
    for k, (a, b) in enumerate(cuts, 1):
        if k == 1:
            note = "A Lover's Complaint is the long poem printed after the sonnets in the 1609 Quarto."
        elif k == 2:
            note = "\"Bastards\" here means false offspring of a corrupt heart."
        else:
            note = None
        B.append(dict(title=f"A Lover's Complaint, part {k} of 3", source=1543, form=f"Stanzas {a+1} to {b}, in rhyme royal",
                      text="\n\n".join(stanzas[a:b]), published="Shake-speares Sonnets (1609 Quarto), where it follows Sonnet 154",
                      note=note))
    ph = body(read(1525))
    ph = clean(ph[ph.index("Let the bird of loudest lay"):].split("\n"))
    B.append(dict(title="The Phoenix and the Turtle", source=1525, form="Poem in quatrains, ending in a Threnos (a lament)",
                  text=ph, published="Love's Martyr (1601)",
                  note="First printed in 1601 in a collection of poems by several writers."))
    return B

def main():
    os.makedirs(SRC, exist_ok=True)
    if "--fetch" in sys.argv:
        for n in BOOKS:
            fetch(n, ".txt"); fetch(n, "-images.html")
    days = []
    for n, rn, text in sonnets():
        if n in SKIP:
            continue
        lines = text.split("\n")
        days.append(dict(day=len(days) + 1, kind="sonnet", number=n, roman=rn, title=f"Sonnet {n}",
                         first_line=lines[0], groups=groups(n), lines=len(lines), text=text,
                         couplet="\n".join(lines[-2:]), note=NOTES.get(n),
                         published="Shake-speares Sonnets (1609 Quarto), modernized spelling",
                         full_text_link=BASE.format(n=1041, s="-images.html"), link_lands_on_poem=False,
                         look_for=rn, verified=True,
                         source_notes="Text copied exactly from the linked edition; leading indentation removed."))
    n_sonnets = len(days)
    for b in bonus():
        lines = b["text"].split("\n")
        n = b["source"]
        nonblank = [l for l in lines if l.strip()]
        verse = [l for l in nonblank if not HEADING.match(l)]
        anchor = anchor_before(n, verse[0]) if n in (1513, 1510, 1521) else None
        link = BASE.format(n=n, s="-images.html") + (f"#{anchor}" if anchor else "")
        days.append(dict(day=len(days) + 1, kind="bonus", number=None, roman=None, title=b["title"],
                         first_line=verse[0], groups=["Bonus"],
                         form=b["form"], lines=len(verse),
                         text=b["text"], couplet=None, note=b["note"], published=b["published"],
                         full_text_link=link, link_lands_on_poem=bool(anchor) or n in (1543, 1525),
                         look_for=None, verified=True,
                         source_notes="Text copied exactly from the linked edition; stage directions and leading indentation removed."))
    meta = dict(
        title="Sonnet a Day",
        days=len(days), sonnets=n_sonnets, bonus=len(days) - n_sonnets,
        omitted=[1, 4, 72],
        order="1609 Quarto order, 151 of the 154 sonnets (Quarto 1, 4 and 72 omitted), then optional bonus days",
        groups={"Fair Youth": "Quarto sonnets 2 to 126 (1, 4 and 72 omitted), addressed to a young man",
                "Marriage sonnets": "Quarto sonnets 2, 3 and 5 to 17, urging the young man to marry",
                "Rival Poet": "Sonnets 78 to 86, about a rival poet",
                "Dark Lady": "Sonnets 127 to 152, about a woman with dark eyes and hair",
                "Cupid sonnets": "Sonnets 153 and 154, two versions of one Greek epigram",
                "Bonus": "Optional days after Sonnet 154"},
        groups_note="These group names are traditional labels used by later readers. The 1609 Quarto prints the sonnets with numbers only.",
        built=time.strftime("%Y-%m-%d"),
    )
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({"meta": meta, "days": days}, open(OUT, "w"), ensure_ascii=False, indent=1)
    print(f"wrote {OUT}: {len(days)} days ({n_sonnets} sonnets, {meta['bonus']} bonus)")

if __name__ == "__main__":
    main()
