import os, json

from .features import tokenize

PREFS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "prefs.json")

# per-like feature weights: title ×3, excerpt/tags ×2, full body ×1, domain/source ×1
W_TITLE, W_DESC, W_BODY = 3, 2, 1
B_WORD, B_SOURCE, B_DOMAIN = 15, 10, 20

EMPTY = {"words": {}, "sources": {}, "domains": {}, "likes": 0, "recent": []}


def load_prefs():
    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return dict(EMPTY)


def save_prefs(prefs):
    prefs["words"] = dict(sorted(prefs["words"].items(), key=lambda kv: -kv[1])[:120])
    prefs["domains"] = dict(sorted(prefs["domains"].items(), key=lambda kv: -kv[1])[:15])
    prefs["recent"] = prefs["recent"][-8:]
    with open(PREFS_FILE, "w") as f:
        json.dump(prefs, f, indent=2)


def pref_bonus(prefs, features, tag, domain):
    words = prefs.get("words", {})
    return (B_WORD * sum(words.get(w, 0) for w in features)
            + B_SOURCE * prefs.get("sources", {}).get(tag, 0)
            + B_DOMAIN * prefs.get("domains", {}).get(domain, 0))


def learned_hit(prefs, a):
    words = prefs.get("words", {})
    return bool(words) and any(w in words for w in tokenize(a["title"]) | set(a.get("tags", [])))


def record_likes(prefs, pool, chosen):
    for idx in chosen:
        a = pool[idx]
        for w in tokenize(a["title"]):
            prefs["words"][w] = prefs["words"].get(w, 0) + W_TITLE
        for w in tokenize(a.get("desc", "")[:4000]):
            prefs["words"][w] = prefs["words"].get(w, 0) + W_DESC
        for w in a.get("tags", []):
            prefs["words"][w] = prefs["words"].get(w, 0) + W_DESC
        if a.get("body"):
            for w in tokenize(a["body"]):
                prefs["words"][w] = prefs["words"].get(w, 0) + W_BODY
        prefs["sources"][a["tag"]] = prefs["sources"].get(a["tag"], 0) + 1
        dom = a.get("domain", "")
        if dom:
            prefs["domains"][dom] = prefs["domains"].get(dom, 0) + 1
        prefs["recent"].append(a["link"])
    prefs["likes"] = prefs.get("likes", 0) + len(chosen)
