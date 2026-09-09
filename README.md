# article-finder

A daily tech/business reading brief that learns your taste.

## What it does

Fetches fresh articles from Hacker News, Lobsters, and dev.to, ranks them, and
prints a top-7 brief. After the brief you can mark favorites in an interactive
checkbox picker; the tool learns the *content* of what you like (topic words,
tags, source, publisher domain) and biases future rankings toward it.

```
[finder] fetching hn…
[finder] fetching lobsters…
[finder] fetching devto…
[finder] sources: hn=60, lobsters=25, devto=40 → 54 candidates after keyword/taste gate
[finder] scoring candidates (normalized score + learned-content preference)…

============================================================
  MORNING BRIEF — Fresh Articles (personalized ranking)
============================================================
1. Muse – Meta's personal AI agent
   [hn]  score: 605
   https://ai.meta.com/muse/
...
============================================================
 [ ]  Muse – Meta's personal AI agent
 [ ]  Reverse engineering my e-scooter and rewriting the firmware in rust
 ↑/↓ move · space toggle · enter done · q cancel
Saved 1 favorite(s) → learned: rust, firmware, e-scooter
```

## Run

```
./run.sh
```

or directly:

```
python3 fetch-articles.py
```

## How ranking works

- Candidates are gated by base topics (AI, business, technology, leadership,
  startups, …) plus words you've already shown taste for.
- Raw scores are normalized per source (HN points aren't comparable to dev.to
  reactions), then a preference bonus is added from your learned model.
- For the top candidates the linked article page is fetched so *content* —
  not just the title — can re-rank them.

## Learning

Liked articles feed `prefs.json` next to the script. Features learned:

- title words (weight 3), excerpt/tags (weight 2), full body words (weight 1)
- source and publisher domain

Delete `prefs.json` to reset your taste model.

## Project layout

```
fetch-articles.py   entrypoint: gate → score → enrich → rank → brief → pick → learn
finder/
  sources.py        network: HN/Lobsters/dev.to, page-text extraction
  features.py       tokenize, excerpt, topic keywords, article features
  prefs.py          prefs.json model, learning, preference bonus
  ui.py             interactive checkbox picker
```

## Sources

- [Hacker News](https://news.ycombinator.com) — Firebase API
- [Lobsters](https://lobste.rs) — `hottest.json`
- [dev.to](https://dev.to) — public API (includes full article body)

All keyless and free.