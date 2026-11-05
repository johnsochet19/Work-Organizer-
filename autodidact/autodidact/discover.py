"""Self-extension: find new free APIs, learn how to read them, keep the ones that work.

1. Read the community directory of free public APIs (github.com/public-apis/public-apis).
2. Keep APIs that need no key and use HTTPS; rank them by how well their description
   matches what the brain already cares about.
3. Probe each candidate with a real query. If the answer is JSON containing a list of
   records with real text, infer which fields are the title / body / link and save that
   as a declarative spec. Optionally an LLM reads the API's docs and proposes the spec.
4. A new source starts with no track record; the agent's bandit decides whether it earns
   its keep, and self-tuning retires it if it doesn't.
"""
from __future__ import annotations

import json
import re

from . import text as T
from .brain import Brain
from .net import Net
from .sources import BUILTIN, run_spec

DIRECTORY_URL = "https://raw.githubusercontent.com/public-apis/public-apis/master/README.md"
ROW_RE = re.compile(r"^\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*([^|]*)\|\s*([^|]*)\|\s*([^|]*)\|")

TITLE_KEYS = ("title", "name", "headline", "label", "term", "word", "heading")
URL_KEYS = ("url", "link", "href", "permalink", "html_url", "web_url")


def parse_directory(markdown: str) -> list[dict]:
    out, category = [], ""
    for line in markdown.splitlines():
        if line.startswith("### "):
            category = line[4:].strip()
        m = ROW_RE.match(line.strip())
        if not m:
            continue
        name, link, desc, auth, https = (s.strip() for s in m.groups())
        if auth.strip("`").lower() in ("no", "") and https.lower() == "yes":
            out.append({"name": name, "link": link, "description": desc, "category": category})
    return out


def _lists_of_dicts(obj, path=""):
    """Yield (path, list) for every list of dicts anywhere in a JSON value."""
    if isinstance(obj, list) and obj and all(isinstance(x, dict) for x in obj[:5]):
        yield path, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _lists_of_dicts(v, f"{path}.{k}" if path else k)


def infer_spec(name: str, url_template: str, data) -> dict | None:
    """Work out which fields of an unknown JSON answer hold the useful text."""
    candidates = list(_lists_of_dicts(data))
    if isinstance(data, dict) and not candidates:
        candidates = [("", [data])]
    best = None
    for path, items in candidates:
        sample = items[:10]
        keys = {k for it in sample for k, v in it.items() if isinstance(v, (str, int, float))}
        avg_len = {k: sum(len(str(it.get(k, ""))) for it in sample) / len(sample) for k in keys}
        text_fields = sorted([k for k in keys if avg_len[k] >= 40 and not str(sample[0].get(k, "")).startswith("http")],
                             key=lambda k: -avg_len[k])[:3]
        if not text_fields:
            continue
        title = next((k for k in keys if k.lower() in TITLE_KEYS), None) or \
            next((k for k in keys if any(t in k.lower() for t in TITLE_KEYS)), "")
        link = next((k for k in keys if k.lower() in URL_KEYS), "")
        score = sum(avg_len[k] for k in text_fields) * len(items)
        if best is None or score > best[0]:
            best = (score, {"name": name, "url": url_template, "items_path": path,
                            "title_field": title, "text_fields": text_fields, "url_field": link})
    return best[1] if best else None


def templates_for(link: str) -> list[str]:
    if "{query}" in link:
        return [link]
    base = link.split("#")[0].rstrip("/")
    return [f"{base}/search?q={{query}}", f"{base}?q={{query}}", f"{base}/api/search?query={{query}}"]


def probe(net: Net, name: str, template: str, topic: str) -> dict | None:
    url = template.replace("{query}", topic.replace(" ", "+")).replace("{n}", "5")
    data = net.get_json(url)
    if data is None:
        return None
    spec = infer_spec(name, template, data)
    if not spec:
        return None
    items = run_spec(net, spec, topic, 5)
    good = [i for i in items if len(i.text) >= 60]
    return spec if good else None


def llm_spec(llm, net: Net, api: dict, topic: str) -> dict | None:
    """Ask an LLM to read the API's documentation and propose a query URL template."""
    resp = net.get(api["link"])
    if not resp.ok:
        return None
    _, docs, _ = T.html_to_text(resp.body) if "<" in resp.body[:500] else ("", resp.body, [])
    prompt = (
        f"Here is the documentation for the free public API '{api['name']}' ({api['description']}).\n"
        "If it has an endpoint that searches or looks up records by a free-text query and returns JSON, "
        "reply with ONLY a JSON object: {\"url\": \"https://...{query}...\"} where {query} marks the search "
        "text. If there is no such endpoint or it needs an API key, reply {\"url\": null}.\n\n"
        f"DOCS:\n{docs[:12000]}")
    reply = llm.complete(prompt, max_tokens=300)
    m = re.search(r"\{.*\}", reply or "", re.S)
    try:
        url = json.loads(m.group(0)).get("url") if m else None
    except ValueError:
        return None
    if not url or "{query}" not in url or not url.startswith("https://"):
        return None
    return probe(net, api["name"], url, topic)


def discover(brain: Brain, net: Net, llm=None, max_probe: int = 6, extra_candidates: list[dict] | None = None):
    """One round of self-extension. Returns the names of sources it added."""
    resp = net.get(DIRECTORY_URL, robots=False)
    apis = parse_directory(resp.body) if resp.ok else []
    apis += extra_candidates or []
    tried = set(brain.get("tried_apis") or [])
    known = {s["name"] for s in brain.sources(enabled_only=False)} | set(BUILTIN)
    interests = set(T.content_tokens(" ".join(
        [c["name"] for c in brain.top_concepts(60)] + [brain.get("mission") or ""])))

    def relevance(api):
        words = set(T.content_tokens(f"{api['description']} {api['category']} {api['name']}"))
        return len(words & interests) + (0.5 if api["category"].lower() in
                                          ("science & math", "books", "open data", "dictionaries", "news") else 0)

    fresh = [a for a in apis if a["name"] not in tried and a["name"] not in known]
    fresh.sort(key=relevance, reverse=True)
    topic = (brain.top_concepts(1) or [{"name": brain.get("mission") or "science"}])[0]["name"]
    added = []
    for api in fresh[:max_probe]:
        tried.add(api["name"])
        spec = None
        for template in templates_for(api["link"]):
            spec = probe(net, api["name"], template, topic)
            if spec:
                break
        if not spec and llm is not None:
            spec = llm_spec(llm, net, api, topic)
        if spec:
            spec["description"] = api["description"]
            brain.register_source(api["name"], "learned", spec)
            brain.log("source_learned", source=api["name"], url=spec["url"], fields=spec["text_fields"])
            added.append(api["name"])
    brain.set("tried_apis", sorted(tried))
    brain.log("discovery", probed=min(len(fresh), max_probe), added=added, candidates=len(fresh))
    return added
