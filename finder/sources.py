import urllib.request, json, re
from datetime import datetime
from urllib.parse import urlparse
from html.parser import HTMLParser

UA = {"User-Agent": "article-finder/1.0", "Accept-Encoding": "identity"}

HN_TOP = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{}.json"
LOB = "https://lobste.rs/hottest.json"
DEVTO = "https://dev.to/api/articles?per_page=40"


def fetch(url, timeout=10):
    req = urllib.request.Request(url, headers=UA)
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read())


def epoch(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def _entry(link="", **kw):
    e = dict(title="", link="", tag="", score=0, created=0,
             desc="", tags=[], body="", domain="")
    e["link"] = link
    e["domain"] = urlparse(link).netloc
    e.update(kw)
    return e


def grab_hn():
    out = []
    for sid in fetch(HN_TOP)[:60]:
        s = fetch(HN_ITEM.format(sid))
        out.append(_entry(
            title=s.get("title", ""),
            link=s.get("url") or f"https://news.ycombinator.com/item?id={sid}",
            tag="hn", score=s.get("score", 0),
            created=s.get("time", 0), desc=s.get("text", "")))
    return out


def grab_lobsters():
    out = []
    for p in fetch(LOB):
        out.append(_entry(
            title=p.get("title", ""),
            link=p.get("url") or f"https://lobste.rs/{p['short_id']}",
            tag="lobsters", score=p.get("score", 0),
            created=epoch(p["created_at"]),
            desc=p.get("description", ""),
            tags=p.get("tags", [])))
    return out


def grab_devto():
    out = []
    for p in fetch(DEVTO):
        out.append(_entry(
            title=p.get("title", ""), link=p.get("url", ""),
            tag="dev.to", score=p.get("positive_reactions_count", 0),
            created=epoch(p["published_at"]),
            desc=p.get("description", ""),
            tags=p.get("tag_list", []),
            body=p.get("body_markdown", "")))  # full content, free
    return out


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.out = []; self.skip = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def page_text(url):
    req = urllib.request.Request(url, headers=UA)
    html = urllib.request.urlopen(req, timeout=8).read()
    p = _Text(); p.feed(html.decode("utf-8", "ignore"))
    return re.sub(r"\s+", " ", " ".join(p.out))[:30000]
