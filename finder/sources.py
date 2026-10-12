import urllib.request, json, re, time
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urlparse
from html.parser import HTMLParser

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36", "Accept-Encoding": "identity"}

HN_TOP = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM = "https://hacker-news.firebaseio.com/v0/item/{}.json"
LOB = "https://lobste.rs/hottest.json"

# tag, name, feed url — newest item in each feed ranks top (score normalized per source)
RSS_FEEDS = [
    ("ars", "Ars Technica", "https://feeds.arstechnica.com/arstechnica/index"),
    ("mit", "MIT Technology Review", "https://www.technologyreview.com/feed/"),
    ("quantamag", "Quanta Magazine", "https://www.quantamagazine.org/feed/"),
    ("aeon", "Aeon", "https://aeon.co/feed.rss"),
    ("techcrunch", "TechCrunch", "https://techcrunch.com/feed/"),
    ("verge", "The Verge", "https://www.theverge.com/rss/index.xml"),
    ("wired", "Wired", "https://www.wired.com/feed/rss"),
    ("simonwillison", "Simon Willison", "https://simonwillison.net/atom/everything/"),
    ("jvns", "Julia Evans", "https://jvns.ca/atom.xml"),
]

# paywalled/aggregator roundups we never want to recommend (case-insensitive substring)
BLOCK_TITLES = ("the download",)
BLOCK_DOMAINS = ("technologyreview.com",)


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


def _rss_time(txt):
    if not txt:
        return time.time()
    txt = txt.replace("Z", "+00:00").replace("GMT", "+0000")
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f%z"):
        try:
            return datetime.strptime(txt, fmt).timestamp()
        except ValueError:
            pass
    return time.time()


def grab_rss():
    out = []
    for tag, name, url in RSS_FEEDS:
        try:
            req = urllib.request.Request(url, headers=UA)
            root = ET.fromstring(urllib.request.urlopen(req, timeout=10).read())
        except Exception:
            continue
        for i, it in enumerate(root.findall(".//item") + root.findall(".//{*}entry")):
            d = {}
            for c in it:
                ln = c.tag.split("}")[-1]
                if ln == "link":
                    d["link"] = d.get("link") or (c.get("href") or c.text or "")
                else:
                    d[ln] = (c.text or "").strip()
            title = d.get("title", "")[:300]
            link = d.get("link", "")
            if not (title and link):
                continue
            out.append(_entry(
                title=title, link=link, tag=tag,
                score=max(1, 100 - i),  # freshest item tops its source
                created=_rss_time(d.get("pubDate") or d.get("published")
                                  or d.get("updated")),
                desc=(d.get("description") or d.get("summary") or "")[:2000]))
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
