"""Text understanding with no ML dependencies: HTML -> text, tokenizing,
keyphrase extraction (RAKE-style), and extractive summaries."""
from __future__ import annotations

import html
import re
from collections import Counter
from html.parser import HTMLParser

STOPWORDS = set("""
a about above after again against all also am an and any are as at be because been before
being below between both but by can could did do does doing down during each either else
etc even ever every few for from further get got had has have having he her here hers him
his how however i if in into is it its itself just like made make many may me might more
most much must my no nor not now of off often on once one only or other our ours out over
own per rather same see seen she should since so some such than that the their theirs them
then there these they this those though through thus to too under until up upon us use used
using very via was way we well were what when where whether which while who whom whose why
will with within without would yet you your yours also new first two three can't don't
one's many several various among including include includes known called based
""".split())

WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9+#\-']*[A-Za-z0-9+#]|[A-Za-z]")
SENT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


def tokens(text: str) -> list[str]:
    return [w.lower() for w in WORD_RE.findall(text)]


def content_tokens(text: str) -> list[str]:
    return [w for w in tokens(text) if w not in STOPWORDS and len(w) > 2]


def sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    return [s.strip() for s in SENT_RE.split(text) if len(s.strip()) > 20]


class _TextExtractor(HTMLParser):
    SKIP = {"script", "style", "nav", "footer", "header", "noscript", "svg", "form", "aside"}
    BLOCK = {"p", "div", "li", "h1", "h2", "h3", "h4", "br", "tr", "section", "article"}

    def __init__(self, base_url: str = ""):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[str] = []
        self.title = ""
        self._skip = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip += 1
        if tag == "title":
            self._in_title = True
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip:
            self._skip -= 1
        if tag == "title":
            self._in_title = False
        if tag in self.BLOCK:
            self.parts.append("\n")

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self._skip:
            self.parts.append(data)


def html_to_text(raw: str) -> tuple[str, str, list[str]]:
    """Return (title, readable_text, hrefs)."""
    p = _TextExtractor()
    try:
        p.feed(raw)
    except Exception:  # malformed HTML: fall back to tag stripping
        return "", re.sub(r"<[^>]+>", " ", raw), []
    text = "".join(p.parts)
    lines = [re.sub(r"\s+", " ", ln).strip() for ln in text.split("\n")]
    # keep lines that look like prose, not menus
    lines = [ln for ln in lines if len(ln) > 40 or (ln.endswith(".") and len(ln) > 15)]
    return html.unescape(p.title.strip()), "\n".join(lines), p.links


def strip_tags(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s or ""))


def keyphrases(text: str, top: int = 15) -> list[tuple[str, float]]:
    """RAKE-style: split on stopwords/punctuation, score phrases by word degree/frequency."""
    phrases: list[list[str]] = []
    for chunk in re.split(r"[.,;:!?()\[\]\"\n]|\s-\s", text.lower()):
        cur: list[str] = []
        for w in WORD_RE.findall(chunk):
            if w in STOPWORDS or len(w) < 3 or w.isdigit():
                if cur:
                    phrases.append(cur)
                cur = []
            else:
                cur.append(w)
        if cur:
            phrases.append(cur)
    phrases = [p for p in phrases if 1 <= len(p) <= 4]
    freq: Counter = Counter()
    degree: Counter = Counter()
    for p in phrases:
        for w in p:
            freq[w] += 1
            degree[w] += len(p) - 1
    word_score = {w: (degree[w] + freq[w]) / freq[w] for w in freq}
    counts = Counter(" ".join(p) for p in phrases)
    scored = {}
    for phrase, n in counts.items():
        words = phrase.split()
        s = sum(word_score[w] for w in words) * (1 + 0.5 * (n - 1))
        scored[phrase] = s
    # prefer phrases that repeat or are multi-word: single rare words are noise
    best = sorted(scored.items(), key=lambda kv: -kv[1])
    out = [(p, round(s, 2)) for p, s in best if counts[p] > 1 or " " in p]
    return out[:top]


def summarize(text: str, n: int = 3, query: str = "") -> list[str]:
    """Extractive summary: score sentences by content-word frequency (+ query overlap)."""
    sents = sentences(text)
    if len(sents) <= n:
        return sents
    freq = Counter(content_tokens(text))
    q = set(content_tokens(query))
    top = max(freq.values()) if freq else 1
    scored = []
    for i, s in enumerate(sents):
        toks = content_tokens(s)
        if not toks:
            continue
        score = sum(freq[t] / top for t in toks) / (len(toks) ** 0.6)
        score += 2.0 * len(q & set(toks))
        score += 0.3 if i < 3 else 0  # lead sentences usually carry the definition
        scored.append((score, i, s))
    keep = sorted(sorted(scored, reverse=True)[:n], key=lambda t: t[1])
    return [s for _, _, s in keep]
