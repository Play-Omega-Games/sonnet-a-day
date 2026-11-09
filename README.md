# 🎭 Sonnet a Day

151 of the 154 Shakespeare sonnets in the order of the 1609 Quarto, in a modernized public-domain text (Quarto 1, 4 and 72 omitted where Early Modern wording reads badly today), plus 9 optional bonus days, for the Sonnet a Day reading bot.

- `plans/sonnets.json`: the plan. Each day holds the full text, first line, couplet, traditional group, a short note for a few sonnets, and a link to the full text in the linked edition.
- `scripts/build.py`: `python3 scripts/build.py --fetch` downloads the source texts into `./src` and rebuilds `plans/sonnets.json`. Every text is copied from the source, never typed.
- `scripts/schedule.py`: the reading calendar for a start date and pace (daily, weekdays, every other day).
- `scripts/check_links.py`: live link check (HTTP 200, anchors, each day's opening words on its page).
- `tests/`: offline checks (`python3 tests/test_plan.py`, `python3 tests/test_schedule.py`).

All texts are in the public domain in the United States. Questions or ideas? Contact Omega Games at john@playomega.games.
