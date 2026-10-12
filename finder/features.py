import re
from html import unescape

TOPICS = [r"\bai\b", r"\bbusiness\b", r"\btechnology\b", r"\bleadership\b",
          r"\bcommunication\b", r"\bstartup\b", r"\bmanagement\b",
          r"\binnovation\b", r"\bsoftware\b", r"\bengineering\b"]
TOPIC_RE = re.compile("|".join(TOPICS), re.IGNORECASE)

# topic taxonomy for content-based taste (substring-safe, word-boundary matched)
TOPIC_TAXONOMY = {
    "ai": ["ai", "artificial intelligence", "machine learning", "llm",
           "language model", "neural", "gpt", "openai", "anthropic", "chatbot",
           "deep learning", "inference", "agent"],
    "business": ["business", "company", "startup", "funding", "venture", "ipo",
                 "acquisition", "revenue", "profit", "market", "pricing",
                 "customer", "saas", "enterprise", "founder"],
    "tech": ["software", "hardware", "cloud", "chip", "semiconductor",
             "database", "api", "browser", "linux", "security", "privacy",
             "encryption", "network", "compiler", "programming", "developer"],
    "leadership": ["leadership", "management", "manager", "hiring", "culture",
                   "executive", "ceo", "remote work", "productivity", "team"],
    "science": ["research", "physics", "quantum", "biology", "climate",
                "space", "astronomy", "neuroscience", "study"],
}
_TOPIC_PAT = {t: re.compile(r"\b(?:" + "|".join(map(re.escape, kws)) + r")", re.I)
              for t, kws in TOPIC_TAXONOMY.items()}


def topics_of(*texts):
    blob = " ".join(t for t in texts if t)
    return {t for t, pat in _TOPIC_PAT.items() if pat.search(blob)}

STOP = set("""the and for with how what why your from you are new into that this have
has not get our all any each every who whom when where which while then than more most
much many some do does did done make makes making use used using build built based way
ways thing things stuff code codes coding day days week year years app web site story
stories post posts article articles one two via also even only just like over under can
will should would could about after before there their they them these those don dont
youre it's its let lets want wants need needs know know know youll im dont think things""".split())


def tokenize(text):
    ws = re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", (text or "").lower())
    ws = [w.rstrip("'s") for w in ws]
    return {w for w in ws if w not in STOP and not w.isdigit()
            and (len(w) >= 3 or w in {"ai", "ml", "api", "yc", "os", "ui", "ux"})}


def rich_features(a):
    s = tokenize(a["title"]) | tokenize(a.get("desc", "")[:3000]) | set(a.get("tags", []))
    if a.get("body"):
        s |= tokenize(a["body"])
    return s


def excerpt(text, limit=170):
    if not text:
        return ""
    text = unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = max(text[:limit].rfind(s) for s in (". ", "! ", "? "))
    if cut > 40:
        return text[:cut + 1] + "..."
    return text[:limit].rsplit(" ", 1)[0] + "..."
