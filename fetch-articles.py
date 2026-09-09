#!/usr/bin/env python3
import sys, time
from concurrent.futures import ThreadPoolExecutor

from finder.sources import grab_hn, grab_lobsters, grab_devto, page_text
from finder.features import rich_features, excerpt, TOPIC_RE
from finder.prefs import (load_prefs, save_prefs, record_likes,
                          pref_bonus, learned_hit)
from finder.ui import pick

CUTOFF = time.time() - 30 * 86400  # 30 days ago
ENRICH = 12    # candidates whose linked page we fetch for content matching
TOP_N = 7


def log(msg):
    print(f"[finder] {msg}", file=sys.stderr, flush=True)


def gate(prefs, a):
    if a["created"] < CUTOFF:
        return False
    if a["tag"] == "hn" and not (TOPIC_RE.search(a["title"]) or learned_hit(prefs, a)):
        return False
    if a["tag"] == "lobsters":
        blob = a["title"] + " " + " ".join(a.get("tags", []))
        if not (TOPIC_RE.search(blob) or learned_hit(prefs, a)):
            return False
    return True


def score_pool(prefs, pool):
    for tag in {a["tag"] for a in pool}:
        top = max(a["score"] for a in pool if a["tag"] == tag) or 1
        for a in pool:
            if a["tag"] == tag:
                a["norm"] = round(100 * a["score"] / top)
    for a in pool:
        a["bonus"] = pref_bonus(prefs, rich_features(a), a["tag"], a.get("domain", ""))
        a["final"] = a["norm"] + a["bonus"]
    pool.sort(key=lambda a: -a["final"])


def enrich(pool):
    need_body = [a for a in pool if not a["body"] and a["link"].startswith("http")]
    todo = [a for a in pool[:ENRICH] if a in need_body]
    if not todo:
        return
    log(f"fetching article pages for content analysis ({len(todo)} top candidates)…")
    with ThreadPoolExecutor(max_workers=8) as ex:
        def get(a):
            try:
                a["body"] = page_text(a["link"])
            except Exception:
                a["body"] = ""
        list(ex.map(get, todo))


def print_brief(pool, prefs):
    words = prefs.get("words", {})
    print("=" * 60)
    print("  MORNING BRIEF — Fresh Articles (personalized ranking)")
    if prefs.get("likes"):
        src = ", ".join(f"{t}×{c}" for t, c in
                        sorted(prefs.get("sources", {}).items(), key=lambda kv: -kv[1])[:2])
        wd = ", ".join(f"{w}×{c}" for w, c in
                       sorted(words.items(), key=lambda kv: -kv[1])[:4])
        print(f"  from {prefs['likes']} liked: {wd}  [{src}]")
    print("=" * 60)
    print()
    for i, a in enumerate(pool, 1):
        print(f"{i}. {a['title']}")
        extra = f"  +{a['bonus']} pref" if a.get("bonus") else ""
        print(f"   [{a['tag']}]  score: {a['score']}{extra}")
        print(f"   {a['link']}")
        s = excerpt(a["desc"])
        if s:
            print(f"   summary: {s}")
        print()
    print("=" * 60)


def main():
    prefs = load_prefs()
    words = prefs.get("words", {})
    pool, n_src = [], {}
    grabbers = {"hn": grab_hn, "lobsters": grab_lobsters, "devto": grab_devto}

    for name, grab in grabbers.items():
        log(f"fetching {name}…")
        try:
            src = grab()
            n_src[name] = len(src)
            for a in src:
                if gate(prefs, a) and not any(x["title"] == a["title"] for x in pool):
                    pool.append(a)
        except Exception as e:
            log(f"{name} error: {e}")
            n_src[name] = 0

    log("sources: " + ", ".join(f"{k}={v}" for k, v in n_src.items())
        + f" → {len(pool)} candidates after keyword/taste gate")
    log("scoring candidates (normalized score + learned-content preference)…")
    score_pool(prefs, pool)

    # fetch linked pages for top candidates so content (not just title) can re-rank
    # ponytail: body scan limited to top ENRICH; widen if discovery beyond it matters
    enrich(pool)
    score_pool(prefs, pool)
    pool = pool[:TOP_N]
    log("top 7 picked" + (f"  |  taste words: " + ", ".join(
        sorted(words, key=lambda w: -words[w])[:3]) if words else ""))
    log("rendering brief…")
    print_brief(pool, prefs)

    chosen = pick([a["title"] for a in pool])
    if chosen is None:
        log("picker skipped (no tty) or cancelled by user")
        print("Skipped — nothing saved.")
        return
    if not chosen:
        log("no favorites marked")
        print("No favorites marked — ranking unchanged.")
        return
    record_likes(prefs, pool, chosen)
    save_prefs(prefs)
    wd = sorted(prefs["words"].items(), key=lambda kv: -kv[1])[:5]
    log(f"learned from {len(chosen)} favorite(s) → words: {', '.join(w for w, _ in wd)}")
    print(f"Saved {len(chosen)} favorite(s) → learned: {', '.join(w for w, _ in wd)}")


if __name__ == "__main__":
    main()
