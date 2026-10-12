# article-finder

A daily tech and business reading brief that learns what you like.

## What it does

It pulls fresh links from Hacker News, Lobsters, and a set of RSS feeds, drops
the ones outside your interests, ranks the rest, and prints a top 7. You mark
the good ones in a checkbox picker; it remembers the topics, words, source, and
domain behind them and biases tomorrow's ranking toward the same.

```
[finder] fetching hn…
[finder] fetching lobsters…
[finder] fetching rss…
[finder] sources: hn=60, lobsters=25, rss=75 → 54 candidates after keyword/taste gate
[finder] scoring candidates (normalized score + learned-content preference)…

============================================================
  MORNING BRIEF: Fresh Articles (personalized ranking)
============================================================
1. Muse – Meta's personal AI agent
   [hn]  score: 605
   https://ai.meta.com/muse/
...
============================================================
 [ ]  Muse – Meta's personal AI agent
 [ ]  Reverse engineering my e-scooter and rewriting the firmware in rust
 ↑/↓ move · space toggle · enter done · q cancel
Saved 1 favorite(s) → learned: ai, tech, science
```

## Run

```
./run.sh
```

or:

```
python3 fetch-articles.py
```

## How ranking works

- Gate: keep an article if it matches a base topic (AI, business, technology,
  leadership, communication, startups, management, innovation, software,
  engineering) or a topic you have liked before.
- Normalize: score each item against the best item from its own source, so HN
  points and Lobsters points are comparable.
- Bonus: add the preference bonus from your learned model.
- Enrich: fetch the linked page for the top 12 candidates and rescore on the
  page text, not just the title.
- Diversify: cap the brief at 2 picks per source.

## Learning

Every favorite is written to `prefs.json` next to the script:

- topics (weight 40): the main signal
- excerpt words (weight 2) and body words (weight 1): a light tiebreak
- source and publisher domain (weight 1 each)

At ranking time those become a preference bonus: domain x20, source x10, word
x5, topic x40. Delete `prefs.json` to reset the model.

## Project layout

```
fetch-articles.py   entrypoint: gate, score, enrich, rank, brief, pick, learn
finder/
  sources.py        HN, Lobsters, RSS, page-text extraction
  features.py       tokenize, excerpt, topic taxonomy, article features
  prefs.py          prefs.json model, learning, preference bonus
  ui.py             interactive checkbox picker
```

## Sources

- Hacker News (Firebase API)
- Lobsters (`hottest.json`)
- RSS: Ars Technica, MIT Technology Review, Quanta, Aeon, TechCrunch, The Verge,
  Wired, Simon Willison, Julia Evans. The freshest item in each feed ranks top;
  edit `RSS_FEEDS` in `finder/sources.py`.
- Blocked outright by `BLOCK_TITLES` and `BLOCK_DOMAINS`: currently
  `technologyreview.com` and "The Download".

All keyless and free. Links already shown in a past brief are filtered out, so
nothing is recommended twice.
