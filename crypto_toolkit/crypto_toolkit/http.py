"""Shared HTTP session: retries, timeouts, simple per-host rate limiting."""
from __future__ import annotations

import os
import threading
import time
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = "crypto-toolkit/1.0"

# Minimum seconds between calls to the same host (keeps you inside free-tier limits).
HOST_MIN_INTERVAL = {
    "api.coingecko.com": 2.1,          # Demo plan ~30/min to be safe
    "pro-api.coinmarketcap.com": 1.3,  # Basic plan 50/min
    "api.blockchain.info": 1.0,
    "mempool.space": 0.5,
}

_lock = threading.Lock()
_last_call: dict[str, float] = {}


def _session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=4, backoff_factor=1.5,
                  status_forcelist=(429, 500, 502, 503, 504),
                  allowed_methods=("GET", "POST"), respect_retry_after_header=True)
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers["User-Agent"] = USER_AGENT
    return s


SESSION = _session()


def get_json(url: str, params: dict | None = None, headers: dict | None = None,
             timeout: float = 15):
    host = urlparse(url).netloc
    wait = HOST_MIN_INTERVAL.get(host, 0)
    if wait:
        with _lock:
            elapsed = time.time() - _last_call.get(host, 0)
            if elapsed < wait:
                time.sleep(wait - elapsed)
            _last_call[host] = time.time()
    r = SESSION.get(url, params=params, headers=headers, timeout=timeout)
    if r.status_code >= 400:
        raise RuntimeError(f"{r.status_code} from {url}: {r.text[:300]}")
    return r.json()


def env(name: str, default: str | None = None) -> str | None:
    """Read a setting from the environment or a local .env file."""
    if name in os.environ:
        return os.environ[name]
    for path in (".env", os.path.join(os.path.dirname(__file__), "..", ".env")):
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() == name:
                            return v.strip().strip('"').strip("'")
    return default
