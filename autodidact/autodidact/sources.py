"""Where knowledge comes from.

Built-in sources are free, keyless public APIs. "Learned" sources are JSON specs the
agent writes for itself after discovering and testing a new API (see discover.py).
A learned source is data, never code: the agent cannot execute anything it downloads.
"""
from __future__ import annotations

import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from . import text as T
from .net import Net


@dataclass
class Item:
    url: str
    title: str
    text: str


def q(s: str) -> str:
    return urllib.parse.quote(s)


# ---------------------------------------------------------------- built-ins
def wikipedia(net: Net, topic: str, n: int) -> list[Item]:
    base = "https://en.wikipedia.org/w/api.php"
    hits = net.get_json(f"{base}?action=query&list=search&format=json&srlimit={n}&srsearch={q(topic)}")
    out = []
    for h in (hits or {}).get("query", {}).get("search", []):
        title = h["title"]
        data = net.get_json(f"{base}?action=query&prop=extracts&explaintext=1&format=json"
                            f"&redirects=1&titles={q(title)}")
        for page in (data or {}).get("query", {}).get("pages", {}).values():
            body = page.get("extract", "")
            body = body.split("\n== See also ==")[0].split("\n== References ==")[0]
            out.append(Item(f"https://en.wikipedia.org/wiki/{q(title.replace(' ', '_'))}", title, body[:20000]))
    return out


def arxiv(net: Net, topic: str, n: int) -> list[Item]:
    resp = net.get(f"https://export.arxiv.org/api/query?search_query=all:{q(topic)}"
                   f"&max_results={n}&sortBy=relevance")
    if not resp.ok or "<!DOCTYPE" in resp.body or "<!ENTITY" in resp.body:
        return []  # a normal Atom feed never declares entities; refuse anything that does
    ns ={"a": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(resp.body)
    except ET.ParseError:
        return []
    out = []
    for e in root.findall("a:entry", ns):
        title = " ".join((e.findtext("a:title", "", ns)).split())
        summary = " ".join((e.findtext("a:summary", "", ns)).split())
        out.append(Item(e.findtext("a:id", "", ns), title, f"{title}. {summary}"))
    return out


def hackernews(net: Net, topic: str, n: int) -> list[Item]:
    data = net.get_json(f"https://hn.algolia.com/api/v1/search?tags=story&hitsPerPage={n}&query={q(topic)}")
    out = []
    for h in (data or {}).get("hits", []):
        title = h.get("title") or ""
        body = T.strip_tags(h.get("story_text") or "")
        link = h.get("url")
        if not body and link:
            page = read_webpage(net, link)
            body = page.text if page else ""
        out.append(Item(link or f"https://news.ycombinator.com/item?id={h.get('objectID')}", title, body))
    return out


def stackexchange(net: Net, topic: str, n: int) -> list[Item]:
    data = net.get_json("https://api.stackexchange.com/2.3/search/advanced?order=desc&sort=relevance"
                        f"&site=stackoverflow&filter=withbody&pagesize={n}&q={q(topic)}")
    return [Item(i["link"], T.strip_tags(i["title"]), T.strip_tags(i.get("body", "")))
            for i in (data or {}).get("items", [])]


def openlibrary(net: Net, topic: str, n: int) -> list[Item]:
    data = net.get_json(f"https://openlibrary.org/search.json?limit={n}&q={q(topic)}")
    out = []
    for d in (data or {}).get("docs", []):
        first = d.get("first_sentence")
        first = first[0] if isinstance(first, list) and first else (first or "")
        subjects = ", ".join((d.get("subject") or [])[:25])
        body = (f"{d.get('title')} is a book by {', '.join(d.get('author_name', ['unknown']))}, "
                f"first published {d.get('first_publish_year', 'n/a')}. {first} Subjects: {subjects}.")
        out.append(Item(f"https://openlibrary.org{d.get('key', '')}", d.get("title", ""), body))
    return out


def crossref(net: Net, topic: str, n: int) -> list[Item]:
    data = net.get_json(f"https://api.crossref.org/works?rows={n}&query={q(topic)}"
                        "&select=DOI,title,abstract,subject,container-title")
    out = []
    for w in (data or {}).get("message", {}).get("items", []):
        title = (w.get("title") or [""])[0]
        abstract = T.strip_tags(w.get("abstract", ""))
        if abstract:
            out.append(Item(f"https://doi.org/{w['DOI']}", title, f"{title}. {abstract}"))
    return out


def github(net: Net, topic: str, n: int) -> list[Item]:
    data = net.get_json(f"https://api.github.com/search/repositories?per_page={n}&sort=stars&q={q(topic)}")
    out = []
    for r in (data or {}).get("items", []):
        body = (f"{r['full_name']} is an open-source project written in {r.get('language') or 'various languages'} "
                f"with {r.get('stargazers_count', 0)} stars. {r.get('description') or ''}. "
                f"Topics: {', '.join(r.get('topics', []))}.")
        out.append(Item(r["html_url"], r["full_name"], body))
    return out


def duckduckgo(net: Net, topic: str, n: int) -> list[Item]:
    d = net.get_json(f"https://api.duckduckgo.com/?format=json&no_html=1&skip_disambig=1&q={q(topic)}")
    if not d:
        return []
    out = []
    if d.get("AbstractText"):
        out.append(Item(d.get("AbstractURL") or f"ddg:{topic}", d.get("Heading", topic), d["AbstractText"]))
    for rt in d.get("RelatedTopics", [])[:n]:
        if isinstance(rt, dict) and rt.get("Text") and rt.get("FirstURL"):
            out.append(Item(rt["FirstURL"], rt["Text"][:80], rt["Text"]))
    return out


def pubmed(net: Net, topic: str, n: int) -> list[Item]:
    eu = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    ids = (net.get_json(f"{eu}/esearch.fcgi?db=pubmed&retmode=json&retmax={n}&term={q(topic)}") or {}) \
        .get("esearchresult", {}).get("idlist", [])
    out = []
    for pid in ids:
        r = net.get(f"{eu}/efetch.fcgi?db=pubmed&rettype=abstract&retmode=text&id={pid}")
        if r.ok and r.body:
            title = next((ln for ln in r.body.split("\n\n")[1:3] if len(ln) > 20), f"PubMed {pid}")
            out.append(Item(f"https://pubmed.ncbi.nlm.nih.gov/{pid}/", " ".join(title.split()), r.body))
    return out


def read_webpage(net: Net, url: str) -> Item | None:
    r = net.get(url)
    if not r.ok or "html" not in (r.content_type or "text/html"):
        return None
    title, body, _ = T.html_to_text(r.body)
    return Item(r.url, title or url, body[:20000]) if body else None


BUILTIN = {
    "wikipedia": (wikipedia, "Encyclopedia articles (full text)"),
    "arxiv": (arxiv, "Research paper abstracts (physics, CS, math, bio)"),
    "pubmed": (pubmed, "Biomedical paper abstracts (NIH)"),
    "crossref": (crossref, "Scholarly works with abstracts"),
    "hackernews": (hackernews, "Tech news stories and the pages they link to"),
    "stackexchange": (stackexchange, "Programming Q&A"),
    "github": (github, "Open-source projects"),
    "openlibrary": (openlibrary, "Books and their subjects"),
    "duckduckgo": (duckduckgo, "Instant-answer summaries"),
}


# ---------------------------------------------------------------- learned specs
def dig(obj, path: str):
    for part in [p for p in path.split(".") if p]:
        if isinstance(obj, dict):
            obj = obj.get(part)
        elif isinstance(obj, list) and part.isdigit() and int(part) < len(obj):
            obj = obj[int(part)]
        else:
            return None
    return obj


def run_spec(net: Net, spec: dict, topic: str, n: int) -> list[Item]:
    """Execute a learned, declarative source spec. Specs only fill a URL template and
    read named fields from the JSON answer; nothing in them is ever executed."""
    url = spec["url"].replace("{query}", q(topic)).replace("{n}", str(n))
    data = net.get_json(url)
    items = dig(data, spec.get("items_path", "")) if data is not None else None
    if not isinstance(items, list):
        return []
    out = []
    for it in items[:n]:
        if not isinstance(it, dict):
            continue
        title = str(dig(it, spec.get("title_field", "")) or spec.get("name", ""))
        parts = [str(dig(it, f) or "") for f in spec.get("text_fields", [])]
        body = T.strip_tags(". ".join(p for p in parts if p))
        link = dig(it, spec.get("url_field", "")) if spec.get("url_field") else None
        link = link if isinstance(link, str) and link.startswith("http") else f"{url}#{len(out)}"
        out.append(Item(link, title[:200], body))
    return out


def fetch(net: Net, source: dict, topic: str, n: int) -> list[Item]:
    if source["kind"] == "builtin":
        return BUILTIN[source["name"]][0](net, topic, n)
    return run_spec(net, source["spec"], topic, n)
