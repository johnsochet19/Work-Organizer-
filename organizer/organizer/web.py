"""Web search and page reading.

Search uses Brave Search if BRAVE_API_KEY is set, otherwise DuckDuckGo's HTML
page with Wikipedia as a backup. Page fetching refuses private network
addresses, so a web page or email can't trick the assistant into poking at your
router or other machines on your network.
"""
from __future__ import annotations

import ipaddress
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

USER_AGENT = "Mozilla/5.0 (compatible; WorkOrganizer/1.0; personal assistant)"
MAX_BYTES = 1_500_000


class WebError(Exception):
    pass


def http_get(url: str, headers: dict | None = None, timeout: float = 20) -> tuple[int, str, str]:
    """GET a URL. Returns (status, body text, final url)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(MAX_BYTES)
            charset = r.headers.get_content_charset() or "utf-8"
            return r.status, raw.decode(charset, "replace"), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, "", url
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise WebError(f"couldn't reach {urllib.parse.urlsplit(url).hostname}: {e}") from e


def check_public_url(url: str) -> None:
    """Only http(s) URLs that resolve to public internet addresses are allowed."""
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        raise WebError("Only http:// and https:// web addresses can be opened.")
    try:
        infos = socket.getaddrinfo(parts.hostname, parts.port or (443 if parts.scheme == "https" else 80))
    except socket.gaierror as e:
        raise WebError(f"couldn't find {parts.hostname}") from e
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise WebError(f"{parts.hostname} points to a private or local address, which I won't open.")


class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "head", "template", "iframe"}
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "pre", "td"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip = 0
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        if tag == "title":
            self._in_title = True
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1
        if tag == "title":
            self._in_title = False
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self.skip:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    p = _TextExtractor()
    try:
        p.feed(html)
    except Exception:
        pass
    text = "".join(p.parts)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def page_title(html: str) -> str:
    p = _TextExtractor()
    try:
        p.feed(html)
    except Exception:
        pass
    return p.title.strip()


def fetch_page(url: str, max_chars: int = 12000) -> dict:
    check_public_url(url)
    status, body, final = http_get(url)
    if status >= 400 or status == 0:
        raise WebError(f"the page answered with error {status}")
    check_public_url(final)  # a redirect must not land on a private address either
    if body.lstrip().startswith(("{", "[")):
        text = body
    else:
        text = html_to_text(body)
    truncated = len(text) > max_chars
    return {"url": final, "title": page_title(body), "text": text[:max_chars], "truncated": truncated}


def search(query: str, brave_api_key: str = "", limit: int = 6) -> list[dict]:
    query = (query or "").strip()
    if not query:
        raise WebError("Empty search.")
    errors = []
    engines = ([_brave] if brave_api_key else []) + [_duckduckgo, _wikipedia]
    for engine in engines:
        try:
            results = engine(query, limit, brave_api_key)
            if results:
                return results[:limit]
        except WebError as e:
            errors.append(str(e))
    if errors:
        raise WebError("search failed: " + "; ".join(errors))
    return []


def _brave(query, limit, key):
    url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode({"q": query, "count": limit})
    status, body, _ = http_get(url, {"Accept": "application/json", "X-Subscription-Token": key})
    if status != 200:
        raise WebError(f"Brave search error {status}")
    data = json.loads(body)
    return [{"title": r.get("title", ""), "url": r.get("url", ""),
             "snippet": html_to_text(r.get("description", ""))} for r in data.get("web", {}).get("results", [])]


class _DDGParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.results: list[dict] = []
        self._field = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "") or ""
        if tag == "a" and "result__a" in cls:
            self.results.append({"title": "", "url": _ddg_url(a.get("href", "")), "snippet": ""})
            self._field = "title"
        elif "result__snippet" in cls and self.results:
            self._field = "snippet"

    def handle_endtag(self, tag):
        if tag in ("a", "td", "div"):
            self._field = None

    def handle_data(self, data):
        if self._field and self.results:
            self.results[-1][self._field] += data


def _ddg_url(href: str) -> str:
    if href.startswith("//"):
        href = "https:" + href
    q = urllib.parse.parse_qs(urllib.parse.urlsplit(href).query)
    return q.get("uddg", [href])[0]


def _duckduckgo(query, limit, _key):
    url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": query})
    status, body, _ = http_get(url)
    if status != 200:
        raise WebError(f"DuckDuckGo error {status}")
    p = _DDGParser()
    p.feed(body)
    return [{**r, "title": r["title"].strip(), "snippet": r["snippet"].strip()} for r in p.results if r["url"]]


def _wikipedia(query, limit, _key):
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "query", "list": "search", "srsearch": query, "format": "json", "srlimit": limit})
    status, body, _ = http_get(url)
    if status != 200:
        raise WebError(f"Wikipedia error {status}")
    hits = json.loads(body).get("query", {}).get("search", [])
    return [{"title": h["title"], "url": "https://en.wikipedia.org/wiki/" + urllib.parse.quote(h["title"].replace(" ", "_")),
             "snippet": html_to_text(h.get("snippet", ""))} for h in hits]
