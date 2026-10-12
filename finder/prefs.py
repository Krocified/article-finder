import os, json

from .features import tokenize, topics_of

PREFS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                          "prefs.json")

# learning weights. topics carry the taste signal; content words are a weak tiebreak.
T_TOPIC, W_DESC, W_BODY = 40, 2, 1
B_TOPIC, B_WORD, B_SOURCE, B_DOMAIN = 1, 5, 10, 20

EMPTY = {"topics": {}, "words": {}, "sources": {}, "domains": {},
         "likes": 0, "recent": [], "seen": []}


def load_prefs():
    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return dict(EMPTY)


def save_prefs(prefs):
    prefs["topics"] = dict(sorted(prefs["topics"].items(), key=lambda kv: -kv[1])[:12])
    prefs["words"] = dict(sorted(prefs["words"].items(), key=lambda kv: -kv[1])[:120])
    prefs["domains"] = dict(sorted(prefs["domains"].items(), key=lambda kv: -kv[1])[:15])
    prefs["recent"] = prefs["recent"][-8:]
    prefs["seen"] = prefs["seen"][-300:]
    with open(PREFS_FILE, "w") as f:
        json.dump(prefs, f, indent=2)


def pref_bonus(prefs, features, tag, domain, topics=frozenset()):
    return (B_TOPIC * T_TOPIC * sum(prefs.get("topics", {}).get(t, 0) for t in topics)
            + B_WORD * sum(prefs.get("words", {}).get(w, 0) for w in features)
            + B_SOURCE * prefs.get("sources", {}).get(tag, 0)
            + B_DOMAIN * prefs.get("domains", {}).get(domain, 0))


def learned_hit(prefs, a):
    topt = prefs.get("topics", {})
    return bool(topt) and bool(topics_of(a["title"], a.get("desc", "")) & set(topt))


def record_likes(prefs, pool, chosen):
    for idx in chosen:
        a = pool[idx]
        body = a.get("body", "")
        for t in topics_of(a["title"], a.get("desc", ""), body):
            prefs["topics"][t] = prefs["topics"].get(t, 0) + T_TOPIC
        for w in tokenize(a.get("desc", "")[:4000]):
            prefs["words"][w] = prefs["words"].get(w, 0) + W_DESC
        if body:
            for w in tokenize(body):
                prefs["words"][w] = prefs["words"].get(w, 0) + W_BODY
        prefs["sources"][a["tag"]] = prefs["sources"].get(a["tag"], 0) + 1
        dom = a.get("domain", "")
        if dom:
            prefs["domains"][dom] = prefs["domains"].get(dom, 0) + 1
        prefs["recent"].append(a["link"])
    prefs["likes"] = prefs.get("likes", 0) + len(chosen)
