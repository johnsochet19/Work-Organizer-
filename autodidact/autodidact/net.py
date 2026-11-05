"""Polite HTTP: per-host rate limits, robots.txt, size caps, and a disk cache.

Everything the agent reads from the web goes through `Net.get`. Tests swap in a
fake `transport` so the whole system can run without a network.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import dataclass

USER_AGENT = "AutodidactResearchBot/1.0 (+self-learning research agent; respects robots.txt)"
MAX_BYTES = 2_000_000


@dataclass
class Response:
    url: str
    status: int
    body: str
    content_type: str = ""

    def json(self):
        return json.loads(self.body)

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300


def urllib_transport(url: str, headers: dict, timeout: float) -> Response:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(MAX_BYTES)
            charset = r.headers.get_content_charset() or "utf-8"
            return Response(r.geturl(), r.status, raw.decode(charset, "replace"),
                            r.headers.get("Content-Type", ""))
    except urllib.error.HTTPError as e:
        return Response(url, e.code, "", "")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return Response(url, 0, str(e), "")


class Net:
    def __init__(self, cache_dir: str | None = None, min_interval: float = 1.0,
                 transport=urllib_transport, timeout: float = 15.0,
                 cache_ttl: float = 24 * 3600, respect_robots: bool = True):
        self.cache_dir = cache_dir
        self.min_interval = min_interval
        self.transport = transport
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self.respect_robots = respect_robots
        self._last_hit: dict[str, float] = {}
        self._robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
        self.requests_made = 0
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)

    # -- robots.txt -------------------------------------------------------
    def allowed(self, url: str) -> bool:
        if not self.respect_robots:
            return True
        parts = urllib.parse.urlsplit(url)
        root = f"{parts.scheme}://{parts.netloc}"
        if root not in self._robots:
            resp = self._raw(root + "/robots.txt")
            if resp.ok and resp.body:
                rp = urllib.robotparser.RobotFileParser()
                rp.parse(resp.body.splitlines())
                self._robots[root] = rp
            else:
                self._robots[root] = None  # no robots.txt => allowed
        rp = self._robots[root]
        return True if rp is None else rp.can_fetch(USER_AGENT, url)

    # -- fetching ---------------------------------------------------------
    def _cache_path(self, url: str) -> str | None:
        if not self.cache_dir:
            return None
        return os.path.join(self.cache_dir, hashlib.sha1(url.encode()).hexdigest() + ".json")

    def _raw(self, url: str, headers: dict | None = None) -> Response:
        host = urllib.parse.urlsplit(url).netloc
        wait = self.min_interval - (time.monotonic() - self._last_hit.get(host, -1e9))
        if wait > 0:
            time.sleep(wait)
        self._last_hit[host] = time.monotonic()
        self.requests_made += 1
        h = {"User-Agent": USER_AGENT, "Accept": "application/json, text/html;q=0.9, */*;q=0.5"}
        h.update(headers or {})
        return self.transport(url, h, self.timeout)

    def get(self, url: str, headers: dict | None = None, use_cache: bool = True,
            robots: bool = True) -> Response:
        """robots=True for crawling web pages. Documented public APIs are meant for programs,
        and many sites' robots.txt disallow their API paths for crawlers, so API calls pass False."""
        if not url.startswith(("http://", "https://")):
            return Response(url, 0, "unsupported scheme")
        path = self._cache_path(url)
        if use_cache and path and os.path.exists(path):
            if time.time() - os.path.getmtime(path) < self.cache_ttl:
                with open(path, encoding="utf-8") as f:
                    return Response(**json.load(f))
        if robots and not self.allowed(url):
            return Response(url, 999, "blocked by robots.txt")
        resp = self._raw(url, headers)
        if resp.ok and path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(resp.__dict__, f)
        return resp

    def get_json(self, url: str, headers: dict | None = None):
        resp = self.get(url, headers, robots=False)
        if not resp.ok:
            return None
        try:
            return resp.json()
        except ValueError:
            return None
