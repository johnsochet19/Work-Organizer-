# Section 2: Working with Data and APIs — Complete Study Guide

Section 1 taught you how to make a basic `GET` and `POST` request. This section teaches you how the web
*actually* works underneath those calls, and how to talk to real-world APIs reliably: authenticating with
OAuth, surviving rate limits and flaky networks, walking through thousands of results page by page,
validating every response, and testing all of it without touching the internet.

Why this matters for an AI assistant: **every "tool" your assistant uses is an API call.** Checking a
calendar, reading email, getting the weather, creating a GitHub issue: each one is an HTTP request your
code makes on the AI's behalf. If those calls are fragile, your assistant is fragile.

Each lesson has:

- **Concepts**: what to understand
- **Code**: examples to type out yourself (don't copy-paste; typing builds memory)
- **Common mistakes**: errors people hit in real projects
- **Exercises**: do them before moving on
- **Check yourself**: you should be able to answer these without looking

**Prerequisites:** all of Section 1. In particular you should already be comfortable with: `requests.get`/`post`,
status codes (Section 1, Lesson 20), `.env` files and `python-dotenv` (Lesson 19), the `json` module (Lesson 16),
Pydantic basics (Lesson 22), `async`/`await` with `httpx` (Lesson 23) and pytest (Lesson 24). This guide builds
on those and does not repeat them.

Total time: roughly **8–10 weeks at 1–2 hours a day**.

---

## Table of Contents

- [Part 0: Setting Up Your Project](#part-0-setting-up-your-project)
- [Part A: How the Web Works](#part-a-how-the-web-works)
  - [Lesson 1: URLs and DNS](#lesson-1-urls-and-dns)
  - [Lesson 2: Anatomy of an HTTP Request and Response](#lesson-2-anatomy-of-an-http-request-and-response)
  - [Lesson 3: Methods, Safety, and Idempotency](#lesson-3-methods-safety-and-idempotency)
- [Part B: REST APIs and How to Explore Them](#part-b-rest-apis-and-how-to-explore-them)
  - [Lesson 4: REST Design and Reading API Docs](#lesson-4-rest-design-and-reading-api-docs)
  - [Lesson 5: Exploring APIs with curl, HTTPie, Postman, and Bruno](#lesson-5-exploring-apis-with-curl-httpie-postman-and-bruno)
- [Part C: httpx in Depth](#part-c-httpx-in-depth)
  - [Lesson 6: httpx Clients: Sync, Async, and Connection Reuse](#lesson-6-httpx-clients-sync-async-and-connection-reuse)
  - [Lesson 7: Timeouts, Retries, and Handling 429](#lesson-7-timeouts-retries-and-handling-429)
  - [Lesson 8: Pagination Patterns](#lesson-8-pagination-patterns)
- [Part D: Data Formats](#part-d-data-formats)
  - [Lesson 9: JSON in Depth](#lesson-9-json-in-depth)
  - [Lesson 10: JSON Schema](#lesson-10-json-schema)
  - [Lesson 11: Validating API Responses with Pydantic](#lesson-11-validating-api-responses-with-pydantic)
  - [Lesson 12: CSV, YAML, and XML](#lesson-12-csv-yaml-and-xml)
- [Part E: Authentication and Secrets](#part-e-authentication-and-secrets)
  - [Lesson 13: API Keys, Bearer Tokens, and Basic Auth](#lesson-13-api-keys-bearer-tokens-and-basic-auth)
  - [Lesson 14: OAuth 2.0 Explained](#lesson-14-oauth-20-explained)
  - [Lesson 15: Worked Example: Google OAuth with google-auth-oauthlib](#lesson-15-worked-example-google-oauth-with-google-auth-oauthlib)
  - [Lesson 16: Secrets Management Beyond .env](#lesson-16-secrets-management-beyond-env)
- [Part F: Webhooks, Rate Limits, and Caching](#part-f-webhooks-rate-limits-and-caching)
  - [Lesson 17: Webhooks and HMAC Signatures](#lesson-17-webhooks-and-hmac-signatures)
  - [Lesson 18: Client-Side Rate Limiting and Concurrency](#lesson-18-client-side-rate-limiting-and-concurrency)
  - [Lesson 19: Caching](#lesson-19-caching)
- [Part G: Testing API Code](#part-g-testing-api-code)
  - [Lesson 20: Mocking HTTP with respx and pytest-httpx](#lesson-20-mocking-http-with-respx-and-pytest-httpx)
- [Capstone Project: Typed API Client Library](#capstone-project-typed-api-client-library)
- [Weekly Schedule](#weekly-schedule)
- [Final Checklist](#final-checklist)
- [Exercise Solutions](#exercise-solutions)
- [Recommended Resources](#recommended-resources)

---

## Part 0: Setting Up Your Project

Create a fresh project folder and virtual environment for this section (see Section 1, Lesson 18 if you need a refresher).

```bash
mkdir data-and-apis
```
```bash
cd data-and-apis
```
```bash
python -m venv .venv
```
```bash
source .venv/bin/activate
```

(On Windows use `.venv\Scripts\Activate.ps1`.) Then install everything this section uses:

```bash
pip install httpx tenacity pydantic pydantic-settings jsonschema pyyaml defusedxml requests requests-cache keyring
```
```bash
pip install google-auth-oauthlib google-api-python-client fastapi uvicorn
```
```bash
pip install pytest respx pytest-httpx httpie ruff
```

| Package | What it's for | Lesson |
|---|---|---|
| `httpx` | Modern HTTP client, sync **and** async | 6–8 |
| `tenacity` | Retry decorators with backoff | 7 |
| `pydantic`, `pydantic-settings` | Validating data and loading settings | 11, 16 |
| `jsonschema` | Validating data against a JSON Schema | 10 |
| `pyyaml`, `defusedxml` | Reading YAML; parsing XML safely | 12 |
| `requests-cache` | Drop-in HTTP cache for `requests` | 19 |
| `keyring` | Store secrets in your OS's password store | 16 |
| `google-auth-oauthlib`, `google-api-python-client` | Google OAuth and Google APIs | 15 |
| `fastapi`, `uvicorn` | A small web server to receive webhooks | 17 |
| `respx`, `pytest-httpx` | Fake HTTP responses in tests | 20 |
| `httpie` | A friendly command-line HTTP client | 5 |

Also install two command-line tools if you don't have them: **curl** (preinstalled on macOS, Linux and Windows 10+)
and **jq** (a JSON processor: `brew install jq`, `sudo apt install jq`, or `winget install jqlang.jq`).

Add this `.gitignore` before you write any code:

```
.venv/
__pycache__/
.env
credentials.json
token.json
*.sqlite
.cache/
```

`credentials.json` and `token.json` will hold OAuth secrets in Lesson 15. They must never be committed.

---

## Part A: How the Web Works

### Lesson 1: URLs and DNS

**Concepts**

A **URL** (Uniform Resource Locator) tells a client *where* a resource is and *how* to reach it.

```
https://api.github.com:443/repos/python/cpython/issues?state=open&per_page=5#top
└─┬─┘   └─────┬──────┘└┬┘└──────────────┬──────────┘└─────────┬──────────┘└┬┘
scheme       host    port             path                   query      fragment
```

| Part | Meaning | Notes |
|---|---|---|
| **scheme** | Protocol: `https` or `http` | Always use `https` for APIs. |
| **host** | The server's name | Turned into an IP address by DNS. |
| **port** | Which "door" on the server | Default 443 for https, 80 for http, so usually omitted. |
| **path** | Which resource | `/repos/python/cpython/issues` |
| **query** | Extra options as `key=value` pairs joined by `&` | Filters, sorting, pagination. |
| **fragment** | Part of a page (`#top`) | Never sent to the server. Browsers only. |

Some characters (spaces, `&`, `?`, `/`, non-ASCII letters) have special meaning in URLs and must be
**percent-encoded**: a space becomes `%20` (or `+` in query strings), `&` becomes `%26`, `é` becomes `%C3%A9`.
httpx and requests do this for you when you pass `params=`. Building URLs by gluing strings together is how
bugs (and security holes) get in.

**DNS** (Domain Name System) is the internet's phone book. Before your program can connect to
`api.github.com`, it asks a DNS resolver "what IP address is this?" and gets back something like `140.82.112.6`.

What happens when you call `httpx.get("https://api.open-meteo.com/v1/forecast?...")`:

1. **Parse** the URL into scheme, host, path, query.
2. **DNS lookup**: `api.open-meteo.com` → IP address (cached by your OS for a while).
3. **TCP connect** to that IP on port 443 (a "handshake" of three small packets).
4. **TLS handshake**: the server proves its identity with a certificate; both sides agree on encryption keys.
   This is what the "s" in https buys you: nobody in between can read or change the traffic.
5. **Send the HTTP request** (Lesson 2) over the encrypted connection.
6. **Receive the HTTP response.**
7. **Keep the connection open** for reuse, or close it. Steps 2–4 are slow (often 50–300 ms), which is why
   reusing connections matters (Lesson 6).

**Code**

```python
from urllib.parse import parse_qs, quote, urlencode, urljoin, urlparse

url = "https://api.github.com/repos/python/cpython/issues?state=open&per_page=5"
parts = urlparse(url)
print(parts.scheme, parts.netloc, parts.path)   # https api.github.com /repos/python/cpython/issues
print(parse_qs(parts.query))                    # {'state': ['open'], 'per_page': ['5']}

# Build a query string safely
print(urlencode({"q": "tasks & notes", "city": "São Paulo"}))
# q=tasks+%26+notes&city=S%C3%A3o+Paulo

# Encode a single path segment (safe="" also encodes "/")
print(quote("reports/2026 Q4", safe=""))         # reports%2F2026%20Q4

# Resolve a relative link against a base URL (common with pagination links)
print(urljoin("https://api.example.com/v1/items", "/v1/items?page=2"))
```

Look up an IP address yourself:

```python
import socket

for family, _, _, _, address in socket.getaddrinfo("api.github.com", 443, proto=socket.IPPROTO_TCP):
    print(family.name, address[0])
```

From the terminal:

```bash
nslookup api.github.com
```
```bash
dig +short api.open-meteo.com
```

**Common mistakes**
- Building URLs with f-strings that contain user input: `f"{base}/search?q={text}"` breaks the moment `text` contains `&` or `#`. Use `params=`.
- Forgetting that a path segment like a file name can contain `/`. Encode it with `quote(name, safe="")`.
- Using `http://` for an API. Many APIs redirect to https, but your API key may already have been sent in plain text.

**Exercises**
1. Use `urlparse` and `parse_qs` to print every query parameter in `https://www.google.com/search?q=python+httpx&hl=en&num=20`.
2. Write `build_url(base: str, path: str, **params) -> str` that joins `base` and `path` with `urljoin` and appends an encoded query string. Test it with a city name containing a space and an accent.
3. Time a DNS lookup using `time.perf_counter()` around `socket.getaddrinfo`. Run it twice. Why is the second one usually faster?

**Check yourself**
- Which part of a URL is never sent to the server?
- What are the four network steps that happen before the first byte of your HTTP request is sent?
- Why should you prefer `params={"q": text}` over putting `text` into the URL yourself?

---

### Lesson 2: Anatomy of an HTTP Request and Response

**Concepts**

HTTP is just **text with a fixed layout** (HTTP/2 and HTTP/3 send it in a binary form, but the structure is identical).
A request looks like this:

```
POST /v1/messages HTTP/1.1                    <- request line: METHOD PATH VERSION
Host: api.example.com                         <- headers: "Name: value", one per line
User-Agent: work-organizer/0.1
Content-Type: application/json
Accept: application/json
Authorization: Bearer sk-xxxx
Content-Length: 39
                                              <- blank line = end of headers
{"title": "Write report", "priority": 1}      <- body (optional)
```

And a response:

```
HTTP/1.1 201 Created                          <- status line: VERSION CODE REASON
Content-Type: application/json; charset=utf-8
Location: /v1/tasks/42
X-RateLimit-Remaining: 4999
ETag: "a1b2c3"

{"id": 42, "title": "Write report", "priority": 1}
```

**Headers you'll meet constantly**

| Header | Sent by | Meaning |
|---|---|---|
| `Host` | client | Which website on this server (one IP can host many sites). |
| `User-Agent` | client | Who is calling. Many APIs (e.g. GitHub) reject requests without one; set a descriptive one. |
| `Accept` | client | Formats you can read, e.g. `application/json`. |
| `Content-Type` | both | Format of the body being sent: `application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`. |
| `Content-Length` | both | Size of the body in bytes. Set automatically by your library. |
| `Authorization` | client | Credentials, e.g. `Bearer <token>` or `Basic <base64>` (Lesson 13). |
| `Accept-Encoding` / `Content-Encoding` | both | Compression (`gzip`, `br`). httpx decompresses for you. |
| `Cache-Control`, `ETag`, `Last-Modified` | server | How long you may cache, and a fingerprint of the content (Lesson 19). |
| `If-None-Match`, `If-Modified-Since` | client | "Only send it if it changed" (Lesson 19). |
| `Location` | server | Where a new resource was created, or where a redirect points. |
| `Retry-After` | server | How long to wait before retrying (Lesson 7). |
| `Link` | server | Pagination links (Lesson 8). |
| `X-RateLimit-*`, `RateLimit-*` | server | Your remaining quota (names vary by API). |

Header names are **case-insensitive**: `content-type` and `Content-Type` are the same header. httpx's
`response.headers` handles that for you.

**Status codes beyond Section 1's table**

| Code | Name | When you'll see it |
|---|---|---|
| 200 | OK | Normal success with a body. |
| 201 | Created | A `POST` created something; often has a `Location` header. |
| 202 | Accepted | Request queued; work happens later (check back or wait for a webhook). |
| 204 | No Content | Success with **no body** (common for `DELETE`). Don't call `.json()` on it. |
| 301 / 308 | Moved Permanently | Update your URL. |
| 302 / 307 | Temporary redirect | Follow it this time. |
| 304 | Not Modified | Your cached copy is still good (Lesson 19). |
| 400 | Bad Request | Malformed request. Read the error body. |
| 401 | Unauthorized | Missing/expired/invalid credentials. Refresh or fix your token. |
| 403 | Forbidden | Credentials are fine but not allowed (wrong scope), **or** rate-limited (GitHub does this). |
| 404 | Not Found | Wrong URL, or a private resource you can't see (APIs often say 404 instead of 403 to hide existence). |
| 409 | Conflict | Clashes with current state (e.g. duplicate name, edit conflict). |
| 422 | Unprocessable Content | Well-formed but invalid data (validation failed). |
| 429 | Too Many Requests | Slow down. Check `Retry-After`. |
| 502 / 503 / 504 | Bad Gateway / Unavailable / Gateway Timeout | Temporary server problems. Retry with backoff. |

**Code**

See the exact request and response httpx sends, using **event hooks**:

```python
import httpx


def log_request(request: httpx.Request) -> None:
    print(f">>> {request.method} {request.url}")
    for name, value in request.headers.items():
        print(f">>> {name}: {value}")


def log_response(response: httpx.Response) -> None:
    print(f"<<< {response.http_version} {response.status_code} {response.reason_phrase}")
    for name in ("content-type", "etag", "cache-control", "x-ratelimit-remaining"):
        if name in response.headers:
            print(f"<<< {name}: {response.headers[name]}")


with httpx.Client(event_hooks={"request": [log_request], "response": [log_response]}) as client:
    r = client.get("https://api.github.com/repos/python/cpython", timeout=10)
    print(r.json()["full_name"])
```

Different ways to send a body, and what `Content-Type` each produces:

```python
import httpx

with httpx.Client(base_url="https://httpbin.org", timeout=10) as client:
    # JSON body -> Content-Type: application/json
    print(client.post("/post", json={"title": "gym"}).json()["json"])

    # Form body -> Content-Type: application/x-www-form-urlencoded (classic HTML forms, OAuth token calls)
    print(client.post("/post", data={"title": "gym"}).json()["form"])

    # File upload -> Content-Type: multipart/form-data
    files = {"file": ("notes.txt", b"hello file", "text/plain")}
    print(client.post("/post", files=files).json()["files"])

    # Raw bytes -> you choose the Content-Type
    print(client.post("/post", content=b"<task/>", headers={"Content-Type": "application/xml"}).status_code)
```

**Common mistakes**
- Calling `.json()` on a `204` response or on an HTML error page from a proxy. Check `response.status_code` and `response.headers.get("content-type")` first.
- Sending `json=` to an endpoint that expects form data (OAuth token endpoints usually want `data=`).
- Logging all request headers in production. `Authorization` is in there.

**Exercises**
1. Using the event hooks above, call `https://httpbin.org/headers` and compare the headers httpbin says it received with what you logged.
2. Request `https://httpbin.org/status/204` and `https://httpbin.org/status/418`. Print status code, reason phrase and the length of the body.
3. Request `https://httpbin.org/redirect/2` with a plain `httpx.get`. What status do you get? Now pass `follow_redirects=True` and print `response.history`.

**Check yourself**
- What separates the headers from the body in an HTTP message?
- What's the difference between `401` and `403`?
- Which `Content-Type` does `json=` produce, and which does `data=` produce?

---

### Lesson 3: Methods, Safety, and Idempotency

**Concepts**

Two properties of HTTP methods decide **whether it's safe to retry** a failed call. That makes them critical
for an AI assistant that will retry things automatically.

- **Safe**: the request doesn't change anything on the server (it only reads).
- **Idempotent**: sending the same request twice has the same effect as sending it once.

| Method | Purpose | Safe | Idempotent | Body? |
|---|---|---|---|---|
| `GET` | Read a resource | Yes | Yes | No |
| `HEAD` | Like GET but headers only (check size/existence) | Yes | Yes | No |
| `OPTIONS` | Ask what's allowed (used by browsers for CORS) | Yes | Yes | No |
| `PUT` | Replace a resource completely at a known URL | No | **Yes** | Yes |
| `DELETE` | Remove a resource | No | **Yes** | Usually no |
| `POST` | Create something / trigger an action | No | **No** | Yes |
| `PATCH` | Change part of a resource | No | Not guaranteed | Yes |

Why `PUT` is idempotent but `POST` is not:

- `PUT /tasks/42 {"title": "Gym", "done": true}` twice → task 42 ends up the same. Harmless.
- `POST /tasks {"title": "Gym"}` twice → **two** tasks. `POST /payments` twice → **charged twice**.
- `DELETE /tasks/42` twice → task is gone either way (the second call may return 404, but the *state* is the same).

**The retry problem.** Your request times out. Did the server receive it and act, or not? You can't know.
For idempotent methods, just retry. For `POST`, retrying blindly can duplicate actions.

**Idempotency keys** are the fix many APIs offer (Stripe is the best-known example): you generate a unique key
per *logical* action and send it in a header. If the server sees the same key twice, it returns the original
result instead of doing the work again.

**Code**

```python
import uuid

import httpx


def create_task_safely(client: httpx.Client, title: str) -> httpx.Response:
    # One key per logical action - reuse the SAME key on every retry of this action.
    key = str(uuid.uuid4())
    for attempt in range(3):
        try:
            return client.post("/tasks", json={"title": title}, headers={"Idempotency-Key": key})
        except httpx.TimeoutException:
            print(f"Timeout on attempt {attempt + 1}; retrying with the same key")
    raise RuntimeError("Could not create task")
```

(Only APIs that document idempotency-key support honour this header. For APIs that don't, a safer pattern is:
before retrying a `POST`, `GET` to check whether the thing was already created.)

A `HEAD` request is a cheap way to check something exists or how big it is without downloading it:

```python
import httpx

r = httpx.head("https://www.python.org/static/img/python-logo.png", timeout=10, follow_redirects=True)
print(r.status_code, r.headers.get("content-type"), r.headers.get("content-length"), "bytes")
```

**Common mistakes**
- Automatically retrying every failed request, including `POST`s. (The capstone only retries idempotent methods.)
- Using `GET` for an action that changes data (`GET /tasks/42/delete`). Crawlers, link previews and caches will trigger it.
- Generating a new idempotency key on every retry, which defeats the purpose.

**Exercises**
1. For each of these, say which method you'd use and whether a timeout can be retried blindly: list today's calendar events; send an email; mark task 7 done; rename a file; delete a draft.
2. Send the same `PUT https://httpbin.org/put` request twice and compare responses. Then explain why httpbin can't show you the difference between PUT and POST semantics (hint: it stores nothing).

**Check yourself**
- Define "safe" and "idempotent" in one sentence each.
- Your AI assistant's "send email" tool timed out. Should it retry? What would make retrying safe?

---

## Part B: REST APIs and How to Explore Them

### Lesson 4: REST Design and Reading API Docs

**Concepts**

**REST** is a style for designing web APIs around **resources** (nouns) that you act on with HTTP **methods** (verbs).
Most APIs your assistant will use are "RESTish".

| Action | Method + path | Typical success |
|---|---|---|
| List tasks | `GET /tasks` | 200 + array |
| Filter / sort / page | `GET /tasks?status=open&sort=due&page=2` | 200 |
| Get one task | `GET /tasks/42` | 200 / 404 |
| Create a task | `POST /tasks` + JSON body | 201 + `Location` |
| Replace a task | `PUT /tasks/42` + full JSON | 200 |
| Update fields | `PATCH /tasks/42` + partial JSON | 200 |
| Delete a task | `DELETE /tasks/42` | 204 |
| Sub-resources | `GET /projects/7/tasks` | 200 |
| Actions that aren't CRUD | `POST /tasks/42/archive` | 200 / 202 |

Conventions you'll see:
- **Plural nouns** for collections (`/repos`, `/issues`), IDs for single items.
- **Versioning** in the path (`/v1/`), in a header (GitHub's `X-GitHub-Api-Version`), or in a date (`2023-06-01`).
- **Errors as JSON**, e.g. GitHub: `{"message": "Not Found", "documentation_url": "..."}`; Open-Meteo: `{"error": true, "reason": "..."}`.
- **Timestamps** in ISO 8601 / RFC 3339 format: `2026-11-04T09:30:00Z` (`Z` = UTC).

Not everything is REST. **GraphQL** (one endpoint, you send a query describing exactly the fields you want;
GitHub and Shopify offer it) and **RPC-style** APIs (`POST /chat.postMessage` in Slack) are common too. The HTTP
skills in this section apply to all of them.

**How to read API docs (a checklist)**

Spend 15 minutes with the docs before writing any code. Find:

1. **Base URL** (and whether there are several: Open-Meteo has separate hosts for forecast and geocoding).
2. **Authentication**: none, API key (header or query?), bearer token, OAuth (which scopes?).
3. **Rate limits**: how many requests per minute/hour, and which headers report them.
4. **Pagination**: page numbers, offsets, cursors or `Link` headers? Maximum page size?
5. **Error format**: what does a 400 or 422 body look like?
6. **The endpoint itself**: method, path, required/optional parameters, an example response.
7. **Versioning and deprecations**: is there a version header you should pin?
8. **Terms of use**: commercial use, attribution, caching rules.

Many APIs publish an **OpenAPI** (formerly Swagger) specification: a machine-readable JSON/YAML file describing
every endpoint, parameter and response schema. GitHub publishes one at `github.com/github/rest-api-description`.
Tools can generate client code, docs and test collections from it, and AI frameworks can turn it into tools.

**Worked example: reading the Open-Meteo forecast docs** (open-meteo.com/en/docs)

| Question | Answer from the docs |
|---|---|
| Base URL | `https://api.open-meteo.com/v1/forecast` |
| Auth | None for non-commercial use |
| Required params | `latitude`, `longitude` |
| Useful params | `current=temperature_2m,weather_code`, `daily=temperature_2m_max,...`, `timezone=auto`, `forecast_days=1..16` |
| Response shape | `current` is an object; `daily` is **columnar**: `{"time": [...], "temperature_2m_max": [...]}` |
| Errors | HTTP 400 with `{"error": true, "reason": "..."}` |
| Weather codes | WMO codes: 0 clear, 1–3 cloudy, 45/48 fog, 51–55 drizzle, 61–65 rain, 71–75 snow, 95 thunderstorm |

Note: Section 1 used the older `current_weather=true` parameter, which still works. The `current=` parameter
shown here lets you choose exactly which variables you want.

**Common mistakes**
- Skipping the rate-limit and pagination sections, then wondering why you only ever get 30 results or get blocked after an hour.
- Assuming field names: always look at a real example response.
- Not pinning a version header, then having the response shape change under you.

**Exercises**
1. Fill in the 8-point checklist for the GitHub REST API "List repository issues" endpoint (docs.github.com/rest/issues/issues).
2. Design (on paper) REST endpoints for your Section 1 Work Organizer: list, filter by tag, get, create, complete, delete. Choose methods, paths and status codes.

**Check yourself**
- What's the difference between `PUT` and `PATCH` in a REST API?
- Name four things you should find in API docs before writing code.
- What is an OpenAPI spec and why is it useful for AI tools?

---

### Lesson 5: Exploring APIs with curl, HTTPie, Postman, and Bruno

**Concepts**

Before writing Python, poke the API by hand. You'll see the real response shape, headers and errors in seconds.

| Tool | Type | Best for |
|---|---|---|
| **curl** | Command line, installed everywhere | Quick checks, sharing exact reproducible requests ("copy as cURL") |
| **HTTPie** (`http`, `https`) | Command line, friendlier syntax, coloured output | Day-to-day exploration |
| **Postman** | Desktop/web app | Saved collections, environments, team sharing, generating code |
| **Bruno** | Open-source desktop app, offline | Collections stored as plain-text files in your Git repo |
| **jq** | Command line JSON processor | Filtering and reshaping JSON output |

**curl**

Basic GET (`-s` silences the progress bar):
```bash
curl -s "https://api.github.com/repos/python/cpython"
```
Show response headers too (`-i`), or the full conversation including TLS and request headers (`-v`):
```bash
curl -i "https://api.github.com/repos/python/cpython"
```
```bash
curl -v "https://api.open-meteo.com/v1/forecast?latitude=51.5&longitude=-0.12&current=temperature_2m"
```
Send headers (`-H`):
```bash
curl -s -H "Accept: application/vnd.github+json" -H "X-GitHub-Api-Version: 2022-11-28" "https://api.github.com/rate_limit"
```
Send JSON (`--json` sets the method to POST and both JSON headers; needs curl 7.82+):
```bash
curl -s --json '{"title": "gym", "priority": 2}' "https://httpbin.org/post"
```
Older curl equivalent:
```bash
curl -s -X POST -H "Content-Type: application/json" -d '{"title": "gym"}' "https://httpbin.org/post"
```
Use a token from an environment variable (never paste the token itself into a command you'll save or share):
```bash
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" "https://api.github.com/user"
```
Pipe into **jq** to extract fields:
```bash
curl -s "https://api.github.com/repos/python/cpython" | jq '.stargazers_count'
```
```bash
curl -s "https://api.github.com/users/python/repos?per_page=5" | jq '.[] | {name, stars: .stargazers_count}'
```

**HTTPie**

`https` is HTTPie's command for https URLs. `key=value` sends a JSON string field, `key:=value` sends raw JSON
(numbers, booleans), `key==value` adds a query parameter, and `Header:value` sets a header.

```bash
https api.github.com/repos/python/cpython
```
```bash
https api.open-meteo.com/v1/forecast latitude==51.5 longitude==-0.12 current==temperature_2m
```
```bash
https POST httpbin.org/post title=gym priority:=2 done:=false
```
```bash
https -v api.github.com/rate_limit Accept:application/vnd.github+json
```

**Postman and Bruno**

Both give you a GUI to build requests, save them into **collections**, and switch between **environments**
(e.g. a `base_url` and `token` variable for "dev" vs "prod"). Useful features:

- **Import a cURL command** (paste the output of your browser's DevTools → Network → right-click → "Copy as cURL").
- **Generate code**: turn a working request into Python (`requests`/`httpx`) or curl.
- **Tests/scripts**: small JavaScript checks that run after each request.
- **Bruno** stores each request as a small text file, so your API collection lives in Git next to your code and is
  reviewed like code. Postman stores collections in its cloud workspace by default (you can export them as JSON).

Whichever you use, keep tokens in environment variables inside the tool, never typed into the saved request.

**Common mistakes**
- Forgetting quotes around URLs containing `&` in the shell. The shell treats `&` as "run in background".
- Pasting real tokens into shared Postman collections or shell history. Use variables.
- Treating "works in Postman" as "works in my code": compare headers carefully (User-Agent, Content-Type).

**Exercises**
1. Using curl and jq, print the names of the 5 most recently updated repositories of the `python` GitHub user.
2. Using HTTPie, call the Open-Meteo geocoding API (`geocoding-api.open-meteo.com/v1/search`, parameter `name`) for your city and find its latitude and longitude.
3. Run `curl -i https://api.github.com/rate_limit` and find your remaining requests in both the headers and the body.
4. Install Bruno or Postman. Create a collection with your two requests from exercises 1 and 2, using a `{{city}}` variable.

**Check yourself**
- What does `curl -v` show that `curl -i` doesn't?
- In HTTPie, what's the difference between `priority=2` and `priority:=2`?
- Why is Bruno's "collections as files" approach useful for a team?

---

## Part C: httpx in Depth

### Lesson 6: httpx Clients: Sync, Async, and Connection Reuse

**Concepts**

Section 1 used `requests.get(...)` and briefly met `httpx.AsyncClient`. From now on, use **httpx** with a
**Client** object. Why a client instead of `httpx.get(...)`?

- **Connection reuse (keep-alive / pooling).** Each top-level `httpx.get()` opens a new connection: DNS + TCP + TLS
  every time. A `Client` keeps connections open and reuses them, often making repeated calls **several times faster**.
- **Shared configuration**: `base_url`, default headers, auth, timeouts, all set once.
- **Same API sync and async**: `httpx.Client` and `httpx.AsyncClient` have the same methods.

| `requests` | `httpx` |
|---|---|
| `requests.Session()` | `httpx.Client()` |
| No default timeout (waits forever!) | **5 second default timeout** |
| Follows redirects by default | Does **not** follow redirects unless `follow_redirects=True` |
| Sync only | Sync and async |
| HTTP/1.1 only | HTTP/1.1 and HTTP/2 (`pip install "httpx[http2]"`, `http2=True`) |

**Code**

```python
import time

import httpx

USERS = ["python", "pallets", "psf", "pydantic", "encode"]

# No client: a new connection for every request
start = time.perf_counter()
for user in USERS:
    httpx.get(f"https://api.github.com/users/{user}", timeout=10)
print(f"no client:   {time.perf_counter() - start:.2f}s")

# One client: connection reused
start = time.perf_counter()
with httpx.Client(timeout=10) as client:
    for user in USERS:
        client.get(f"https://api.github.com/users/{user}")
print(f"with client: {time.perf_counter() - start:.2f}s")
```

A properly configured client:

```python
import httpx

client = httpx.Client(
    base_url="https://api.github.com",
    headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "work-organizer/0.1 (you@example.com)",
    },
    timeout=httpx.Timeout(10.0, connect=5.0),   # 10s for everything, but give up connecting after 5s
    limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
    follow_redirects=True,
)

try:
    r = client.get("/repos/python/cpython")          # relative to base_url
    r.raise_for_status()
    repo = r.json()
    print(repo["full_name"], repo["stargazers_count"])
    print(r.url, r.http_version, r.elapsed.total_seconds())
finally:
    client.close()      # or use "with httpx.Client(...) as client:"
```

**Timeouts in detail.** `httpx.Timeout` has four parts:

| Part | Limits how long we wait to... |
|---|---|
| `connect` | establish the connection (DNS + TCP + TLS) |
| `read` | receive each chunk of the response |
| `write` | send each chunk of the request |
| `pool` | get a free connection from the pool (when all are busy) |

`httpx.Timeout(10.0, connect=5.0)` means 5s for connect and 10s for the other three. For AI model APIs that can
take a minute to answer, raise `read` (e.g. `httpx.Timeout(10.0, read=120.0)`).

**The httpx exception tree** (catch the most specific thing you can handle):

```
httpx.HTTPError
├── httpx.HTTPStatusError        <- raised by response.raise_for_status() for 4xx/5xx
└── httpx.RequestError           <- the request never got a response
    ├── httpx.TransportError
    │   ├── httpx.TimeoutException  (ConnectTimeout, ReadTimeout, WriteTimeout, PoolTimeout)
    │   ├── httpx.NetworkError      (ConnectError, ReadError, ...)
    │   └── ...
    ├── httpx.DecodingError
    └── httpx.TooManyRedirects
```

```python
import httpx


def fetch_repo(client: httpx.Client, full_name: str) -> dict | None:
    try:
        r = client.get(f"/repos/{full_name}")
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None                       # a normal, expected outcome
        raise                                 # anything else is a real problem
    except httpx.TimeoutException:
        print("GitHub is slow right now")
        raise
```

**Async client.** Same methods, add `await`. Use it when you have several independent calls:

```python
import asyncio

import httpx


async def get_temperature(client: httpx.AsyncClient, name: str, lat: float, lon: float) -> str:
    r = await client.get(
        "/v1/forecast",
        params={"latitude": lat, "longitude": lon, "current": "temperature_2m"},
    )
    r.raise_for_status()
    return f"{name}: {r.json()['current']['temperature_2m']}°C"


async def main() -> None:
    cities = {"London": (51.51, -0.13), "Tokyo": (35.69, 139.69), "Lagos": (6.45, 3.39)}
    async with httpx.AsyncClient(base_url="https://api.open-meteo.com", timeout=10) as client:
        results = await asyncio.gather(
            *(get_temperature(client, name, lat, lon) for name, (lat, lon) in cities.items()),
            return_exceptions=True,
        )
    for result in results:
        print(result if not isinstance(result, Exception) else f"failed: {result!r}")


asyncio.run(main())
```

**Streaming large downloads** without loading them into memory:

```python
import httpx

url = "https://www.python.org/ftp/python/3.13.0/Python-3.13.0.tgz"
with httpx.Client(timeout=30, follow_redirects=True) as client:
    with client.stream("GET", url) as r:
        r.raise_for_status()
        with open("python.tgz", "wb") as f:
            for chunk in r.iter_bytes(chunk_size=65536):
                f.write(chunk)
```

**Common mistakes**
- Creating a new `Client` inside a loop or inside every function call. Create it once and pass it around (or keep it on a class).
- Forgetting to close clients (use `with` / `async with`). Unclosed clients leak connections and print warnings.
- Using the sync `Client` inside `async def` code: it blocks the whole event loop.
- Setting `timeout=None` "to fix timeouts". Now your assistant can hang forever.

**Exercises**
1. Run the timing comparison above. How much faster is the client version for you? Try `http2=True` (after installing `httpx[http2]`) and print `r.http_version`.
2. Write `fetch_users(usernames: list[str]) -> list[dict]` with `AsyncClient` and `gather`. Make it return results in the same order as the input and skip (but log) users that 404.
3. Set `timeout=httpx.Timeout(0.001)` and call any API. Catch the exception and print its class name. Which subclass did you get?

**Check yourself**
- Name two benefits of using a `Client` over top-level `httpx.get`.
- What are the four timeout types and what does each limit?
- Which exception do you get for a 500 response after `raise_for_status()`, and which for a DNS failure?

---

### Lesson 7: Timeouts, Retries, and Handling 429

**Concepts**

Network calls fail for two very different reasons:

| Failure | Examples | Retry? |
|---|---|---|
| **Transient** (temporary) | timeout, connection reset, 429, 500, 502, 503, 504 | Yes, with backoff |
| **Permanent** | 400, 401, 403 (permission), 404, 422 | No: retrying won't change the answer |

**Exponential backoff with jitter.** Wait longer after each failure (1s, 2s, 4s, 8s...), plus a random extra
amount ("jitter") so that a thousand clients that failed at the same moment don't all retry at the same moment
and knock the server over again. Always cap the number of attempts and the maximum wait.

**Respect `Retry-After`.** On a 429 (and often 503), servers tell you how long to wait, either as seconds
(`Retry-After: 30`) or as a date (`Retry-After: Wed, 04 Nov 2026 09:30:00 GMT`). Use it instead of your own guess.

**Rate-limit headers.** Many APIs tell you your budget on *every* response so you can slow down *before* hitting 429:

| API | Headers |
|---|---|
| GitHub | `x-ratelimit-limit`, `x-ratelimit-remaining`, `x-ratelimit-reset` (Unix time), `x-ratelimit-used` |
| IETF draft standard | `RateLimit-Limit`, `RateLimit-Remaining`, `RateLimit-Reset` (seconds) |

GitHub specifics: unauthenticated requests get 60/hour per IP; authenticated ones 5,000/hour. When you exceed the
primary limit you get **403 or 429** with `x-ratelimit-remaining: 0`. "Secondary" limits (too many requests too fast)
return 403/429 with a `retry-after` header.

**Code: a manual retry loop**

```python
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def parse_retry_after(value: str | None) -> float | None:
    """Return seconds to wait from a Retry-After header, or None if absent/invalid."""
    if value is None:
        return None
    try:
        return max(0.0, float(value))               # "30"
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(value)         # "Wed, 04 Nov 2026 09:30:00 GMT"
    except (TypeError, ValueError):
        return None
    return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())


def get_with_retries(client: httpx.Client, url: str, max_attempts: int = 5, **kwargs) -> httpx.Response:
    for attempt in range(max_attempts):
        last = attempt == max_attempts - 1
        try:
            response = client.get(url, **kwargs)
        except httpx.TransportError:
            if last:
                raise
            wait = min(30, 2**attempt) + random.uniform(0, 1)
        else:
            if response.status_code not in RETRYABLE_STATUS or last:
                response.raise_for_status()
                return response
            wait = parse_retry_after(response.headers.get("Retry-After"))
            if wait is None:
                wait = min(30, 2**attempt) + random.uniform(0, 1)
        print(f"attempt {attempt + 1} failed; sleeping {wait:.1f}s")
        time.sleep(wait)
    raise AssertionError("unreachable")
```

**Code: the same with tenacity**

`tenacity` turns retry logic into a decorator. You describe *what* to retry, *when* to stop and *how long* to wait:

```python
import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential_jitter
from tenacity.wait import wait_base

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, httpx.TransportError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS
    return False


class wait_retry_after(wait_base):
    """Wait as long as the server's Retry-After header says; otherwise use the fallback."""

    def __init__(self, fallback: wait_base) -> None:
        self.fallback = fallback

    def __call__(self, retry_state) -> float:
        exc = retry_state.outcome.exception()
        if isinstance(exc, httpx.HTTPStatusError):
            header = exc.response.headers.get("Retry-After")
            if header and header.isdigit():
                return float(header)
        return self.fallback(retry_state)


@retry(
    retry=retry_if_exception(is_retryable),
    stop=stop_after_attempt(5),
    wait=wait_retry_after(wait_exponential_jitter(initial=1, max=30)),
    reraise=True,                      # raise the real error at the end, not tenacity.RetryError
)
def get_json(client: httpx.Client, url: str, **params) -> dict:
    response = client.get(url, params=params)
    response.raise_for_status()
    return response.json()


with httpx.Client(timeout=10) as client:
    data = get_json(client, "https://api.open-meteo.com/v1/forecast",
                    latitude=48.85, longitude=2.35, current="temperature_2m")
    print(data["current"])
    print(get_json.statistics)          # attempt_number, idle_for, ...
```

tenacity works with `async def` functions too: decorate them the same way and it uses `asyncio.sleep`.

**Transport-level retries.** httpx can retry *connection failures only* (not status codes) for you:

```python
transport = httpx.HTTPTransport(retries=3)        # httpx.AsyncHTTPTransport for async
client = httpx.Client(transport=transport, timeout=10)
```

**Reading rate-limit headers to slow down early**

```python
import time

import httpx

with httpx.Client(base_url="https://api.github.com", timeout=10) as client:
    r = client.get("/rate_limit")              # this endpoint doesn't count against your limit
    core = r.json()["resources"]["core"]
    reset_in = core["reset"] - time.time()
    print(f"{core['remaining']}/{core['limit']} left, resets in {reset_in / 60:.0f} min")
```

**Common mistakes**
- Retrying 400/401/404. They will fail again; you just waste quota and time.
- Retrying without a cap. An outage turns into an infinite loop.
- No jitter: all your parallel tasks retry in lock-step.
- Swallowing the final error and returning `None`, so the caller (or AI) never learns something failed.
- Retrying non-idempotent `POST`s (see Lesson 3).

**Exercises**
1. Use `https://httpbin.org/status/503` to test `get_with_retries`. Lower the waits to make it quick. Confirm it gives up after `max_attempts`.
2. Test `parse_retry_after` with `"0"`, `"120"`, `"soon"`, `None`, and an HTTP date 30 seconds in the future (hint: `email.utils.format_datetime(dt, usegmt=True)`).
3. Add a check to `get_with_retries`: if a GitHub response has `x-ratelimit-remaining` of `"0"`, raise a custom `RateLimitExhausted` error that includes how many seconds until `x-ratelimit-reset`.

**Check yourself**
- Which status codes are worth retrying and why?
- Why add jitter to exponential backoff?
- What two formats can `Retry-After` take?

---

### Lesson 8: Pagination Patterns

**Concepts**

APIs never return thousands of items in one response; they split results into **pages**. If you forget to
paginate, your assistant will confidently report "you have 30 open issues" when you have 400.

| Pattern | Request looks like | Response tells you there's more by... | Real examples |
|---|---|---|---|
| **Page number** | `?page=3&per_page=50` | a total count, or a full page came back | GitHub search, many simple APIs |
| **Offset/limit** | `?offset=100&limit=50` | `count` total, or a `next` URL | PokeAPI, many SQL-backed APIs |
| **Cursor** | `?cursor=abc123` | `next_cursor` / `has_more` fields | Slack, Notion, Stripe, most modern APIs |
| **Link header** | follow the URL given | `Link: <...>; rel="next"` header | GitHub REST |

**Why cursors?** With offsets, if someone adds an item while you're paging, everything shifts and you see an item
twice or miss one. A cursor is a bookmark that says "continue after *this* item", so it's stable and fast for
huge datasets. Treat cursors as **opaque**: never try to decode or construct them.

**Code: page numbers (GitHub search)**

```python
import httpx


def search_repos(query: str, max_results: int = 200) -> list[dict]:
    results: list[dict] = []
    per_page = 100                                     # GitHub's maximum page size
    with httpx.Client(base_url="https://api.github.com", timeout=10) as client:
        page = 1
        while len(results) < max_results:
            r = client.get("/search/repositories",
                           params={"q": query, "per_page": per_page, "page": page})
            r.raise_for_status()
            items = r.json()["items"]
            results.extend(items)
            if len(items) < per_page:                  # a short page means it was the last one
                break
            page += 1
    return results[:max_results]


repos = search_repos("topic:todo language:python", max_results=150)
print(len(repos), repos[0]["full_name"])
```

**Code: offset with a `next` URL (PokeAPI)**

```python
import httpx

url: str | None = "https://pokeapi.co/api/v2/pokemon"
params: dict | None = {"limit": 100, "offset": 0}
names: list[str] = []
with httpx.Client(timeout=10) as client:
    while url and len(names) < 300:
        r = client.get(url, params=params)
        r.raise_for_status()
        data = r.json()                 # {"count": ..., "next": "...", "previous": ..., "results": [...]}
        names += [p["name"] for p in data["results"]]
        url = data["next"]              # already contains limit & offset
        params = None                   # so don't send ours again
print(len(names), names[:5])
```

**Code: Link headers (GitHub REST), as a generator**

A **generator** (`yield`) is the natural shape for pagination: the caller loops over items and pages are fetched
lazily, only as needed. httpx parses `Link` headers for you into `response.links`:

```python
from collections.abc import Iterator

import httpx


def paginate(client: httpx.Client, url: str, params: dict | None = None,
             max_pages: int = 20) -> Iterator[dict]:
    """Yield every item from a GitHub-style list endpoint, following Link: rel="next"."""
    next_url: str | None = url
    for _ in range(max_pages):                       # a safety limit
        if next_url is None:
            return
        r = client.get(next_url, params=params)
        r.raise_for_status()
        yield from r.json()
        next_url = r.links.get("next", {}).get("url")
        params = None                                # the next URL has the query string built in


with httpx.Client(base_url="https://api.github.com", timeout=10) as client:
    for i, issue in enumerate(paginate(client, "/repos/psf/requests/issues",
                                       {"state": "open", "per_page": 100})):
        if i >= 250:                                 # stop early: later pages are never fetched
            break
        print(issue["number"], issue["title"][:60])
```

`r.links` looks like `{"next": {"url": "...page=2", "rel": "next"}, "last": {"url": "...page=9", "rel": "last"}}`.

**Code: cursors (a generic helper)**

Cursor APIs differ in field names, so pass in small functions describing them. Notion, for example, takes
`start_cursor` in the request and returns `results`, `has_more` and `next_cursor`:

```python
from collections.abc import Callable, Iterator
from typing import Any


def paginate_cursor(
    fetch_page: Callable[[str | None], dict[str, Any]],
    items_key: str = "results",
    cursor_key: str = "next_cursor",
) -> Iterator[Any]:
    """fetch_page(cursor) returns one page as a dict. cursor is None for the first page."""
    cursor: str | None = None
    while True:
        page = fetch_page(cursor)
        yield from page[items_key]
        cursor = page.get(cursor_key)
        if not cursor or page.get("has_more") is False:
            return


# Usage with Notion's database query endpoint (needs a token; shown for shape):
# def fetch(cursor):
#     body = {"page_size": 100} | ({"start_cursor": cursor} if cursor else {})
#     r = client.post(f"/v1/databases/{database_id}/query", json=body)
#     r.raise_for_status()
#     return r.json()
# for row in paginate_cursor(fetch): ...
```

**Async pagination** uses an `async def` generator and `async for`:

```python
import httpx


async def paginate_async(client: httpx.AsyncClient, url: str, params: dict | None = None):
    next_url: str | None = url
    while next_url:
        r = await client.get(next_url, params=params)
        r.raise_for_status()
        for item in r.json():
            yield item
        next_url = r.links.get("next", {}).get("url")
        params = None

# async for repo in paginate_async(client, "/users/python/repos", {"per_page": 100}): ...
```

**Common mistakes**
- Only reading page 1.
- Re-sending your original `params` along with a `next` URL that already contains them (you may get `page=1&page=2`).
- No page limit: one bad cursor and you loop forever, burning your rate limit.
- Building a giant list in memory when you only need the first 10 matches. Use a generator and `break`.
- Offset-paging data that changes while you read it, then being surprised by duplicates.

**Exercises**
1. Using `paginate`, count how many open issues (excluding pull requests: items with a `pull_request` key) `psf/requests` has.
2. Change `search_repos` to stop early using the `total_count` field in the response, and note that GitHub search only returns the first 1,000 results no matter how many pages you ask for.
3. Write a fake `fetch_page(cursor)` that serves the numbers 1–25 in pages of 10 with string cursors, and check `list(paginate_cursor(fake))` returns all 25.

**Check yourself**
- Name the four pagination styles and one advantage of cursors over offsets.
- Why is a generator a good fit for pagination?
- Where does httpx put parsed `Link` header data?

---

## Part D: Data Formats

### Lesson 9: JSON in Depth

**Concepts**

You know `json.loads`/`json.dumps` (Section 1, Lesson 16). Now the details that bite in real systems.

**JSON's rules (stricter than Python):**
- Strings use **double quotes** only. No comments. No trailing commas.
- Only these types: object, array, string, number, `true`, `false`, `null`.
- **No dates, no decimals, no sets, no bytes.** Everything else must be converted, and *both sides must agree how*.
- Numbers have no size limit in the spec, but many languages read them as 64-bit floats. IDs larger than
  2^53 (9,007,199,254,740,992) lose precision in JavaScript, which is why APIs like X/Twitter also send IDs as strings (`id_str`).
- Text must be Unicode (UTF-8 in practice).

**Dates and times: use ISO 8601 / RFC 3339, always with a timezone.**
- Good: `"2026-11-04T09:30:00Z"`, `"2026-11-04T10:30:00+01:00"`, `"2026-11-04"` (a date).
- Ambiguous: `"2026-11-04T09:30:00"` (whose 9:30?), `"04/11/2026"` (April or November?), `1762248600` (seconds or ms?).
- Python 3.11+: `datetime.fromisoformat("2026-11-04T09:30:00Z")` understands the `Z`.
- Store and send **UTC**; convert to the user's timezone only when displaying.

**Code: useful `json.dumps` options**

```python
import json

data = {"city": "Zürich", "b": 1, "a": [1, 2]}
print(json.dumps(data))                                   # {"city": "Zürich", ...}  (escaped)
print(json.dumps(data, ensure_ascii=False))               # {"city": "Zürich", ...}       (readable)
print(json.dumps(data, sort_keys=True, separators=(",", ":")))   # compact & stable: good for hashing/caching
print(json.dumps(data, indent=2))                         # pretty, for humans and logs
```

**Code: encoding types JSON doesn't know**

```python
import json
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class Priority(Enum):
    HIGH = 1
    LOW = 3


def to_jsonable(obj):
    """json.dumps calls this for any object it can't encode itself."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, Decimal):
        return str(obj)            # keep exact money values as strings, not floats
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, set):
        return sorted(obj)
    raise TypeError(f"Can't serialize {type(obj).__name__}")


task = {
    "id": uuid4(),
    "due": date(2026, 11, 10),
    "created": datetime(2026, 11, 4, 9, 30, tzinfo=timezone.utc),
    "priority": Priority.HIGH,
    "budget": Decimal("19.99"),
    "tags": {"work", "urgent"},
}
print(json.dumps(task, default=to_jsonable, indent=2))
```

Decoding the other way: JSON has no type information, so `"2026-11-10"` comes back as a plain `str`. You must
convert it yourself, which is exactly what Pydantic does for you (Lesson 11).

```python
import json
from datetime import datetime
from decimal import Decimal

print(json.loads('{"price": 0.1}', parse_float=Decimal))      # {'price': Decimal('0.1')}  exact
print(datetime.fromisoformat("2026-11-04T09:30:00Z"))         # 2026-11-04 09:30:00+00:00
```

**JSON Lines** (`.jsonl`): one JSON object per line. Great for logs and large datasets because you can append
and stream line by line. AI providers use it for batch jobs and fine-tuning data.

```python
import json
from pathlib import Path

path = Path("events.jsonl")
with path.open("a", encoding="utf-8") as f:
    f.write(json.dumps({"event": "task_added", "title": "gym"}) + "\n")

with path.open(encoding="utf-8") as f:
    events = [json.loads(line) for line in f if line.strip()]
print(events)
```

**Common mistakes**
- `json.dumps(datetime.now())` → `TypeError: Object of type datetime is not JSON serializable`. Use `default=` or Pydantic.
- Naive datetimes (no timezone) in APIs. Always attach `timezone.utc`.
- Money as floats (`0.1 + 0.2`). Use `Decimal` or integer cents.
- Trusting that a big integer ID survives a trip through JavaScript.

**Exercises**
1. Extend `to_jsonable` to handle `pathlib.Path` and `bytes` (as base64 text with `base64.b64encode(b).decode()`).
2. Write `from_jsonable(d: dict) -> dict` that converts any string value matching `YYYY-MM-DD` back to a `date`. (Then appreciate why Pydantic exists.)
3. Write 1,000 fake events to a `.jsonl` file and count events by type while reading it line by line.

**Check yourself**
- Name four Python types JSON can't represent directly.
- What does the `Z` in `2026-11-04T09:30:00Z` mean?
- Why use `sort_keys=True` when you hash JSON for a cache key?

---

### Lesson 10: JSON Schema

**Concepts**

**JSON Schema** is a standard JSON document that *describes* what valid JSON looks like: types, required fields,
allowed values, string formats, numeric ranges. It matters to you for two reasons:

1. **AI tool definitions are JSON Schema.** When you give an AI model a tool, you describe its inputs with a JSON
   Schema (the `input_schema` / `parameters` field). The model reads it to decide what arguments to send.
2. **Validating data** you receive or produce, in any language, from one shared definition.

| Keyword | Meaning | Example |
|---|---|---|
| `type` | `object`, `array`, `string`, `integer`, `number`, `boolean`, `null` | `{"type": "string"}` |
| `properties` | Schemas for each key of an object | `{"title": {"type": "string"}}` |
| `required` | Keys that must be present | `["title"]` |
| `additionalProperties` | Allow unknown keys? | `false` |
| `enum` | One of a fixed list | `{"enum": ["todo", "done"]}` |
| `minimum` / `maximum` | Number range | `{"minimum": 1, "maximum": 3}` |
| `minLength` / `maxLength` / `pattern` | String rules | `{"pattern": "^[A-Z]{3}$"}` |
| `format` | Semantic hint: `date`, `date-time`, `email`, `uri` | `{"format": "date"}` |
| `items` | Schema for each array element | `{"type": "array", "items": {"type": "string"}}` |
| `description` | Human (and AI!) readable explanation | `"description": "1 = high"` |
| `$ref` / `$defs` | Reuse a sub-schema | `{"$ref": "#/$defs/Task"}` |
| `anyOf` / `oneOf` | Alternatives | `{"anyOf": [{"type": "string"}, {"type": "null"}]}` |

**Code**

```python
from jsonschema import Draft202012Validator

TASK_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "title": {"type": "string", "minLength": 1, "description": "What needs doing"},
        "priority": {"type": "integer", "minimum": 1, "maximum": 3, "description": "1 = high"},
        "due": {"type": "string", "format": "date"},
        "tags": {"type": "array", "items": {"type": "string"}, "uniqueItems": True},
        "status": {"enum": ["todo", "doing", "done"]},
    },
    "required": ["title", "priority"],
    "additionalProperties": False,
}

validator = Draft202012Validator(TASK_SCHEMA)

print(validator.is_valid({"title": "Email Sam", "priority": 1}))   # True

bad = {"title": "", "priority": 5, "colour": "red"}
for error in sorted(validator.iter_errors(bad), key=lambda e: list(e.path)):
    where = "/".join(map(str, error.path)) or "(root)"
    print(f"{where}: {error.message}")
# (root): Additional properties are not allowed ('colour' was unexpected)
# priority: 5 is greater than the maximum of 3
# title: '' should be non-empty
```

`iter_errors` reports **all** problems at once, which is much friendlier than stopping at the first. (`jsonschema.validate(data, schema)`
also exists; it raises on the first error.)

Note: `format` is only an annotation by default. To actually check dates and emails, pass a format checker:
`Draft202012Validator(TASK_SCHEMA, format_checker=Draft202012Validator.FORMAT_CHECKER)`.

**You rarely write schemas by hand in Python.** Pydantic generates them from your models (Section 1 showed
`model_json_schema()`). Write the model, get the schema for free, and you have one source of truth:

```python
import json

from pydantic import BaseModel, Field


class AddTaskInput(BaseModel):
    """Add a task to the user's to-do list."""

    title: str = Field(min_length=1, description="What needs doing")
    priority: int = Field(3, ge=1, le=3, description="1 = high, 3 = low")


print(json.dumps(AddTaskInput.model_json_schema(), indent=2))
```

**Common mistakes**
- Forgetting `"additionalProperties": false`, so typos like `"titel"` pass validation silently.
- Assuming `format: date` is enforced without a format checker.
- Hand-writing a schema *and* a Pydantic model that slowly drift apart.

**Exercises**
1. Write a JSON Schema for a calendar event: `summary` (required string), `start` and `end` (required date-time strings), `attendees` (array of emails), `location` (optional string). Validate one good and two bad examples.
2. Generate the schema for the same event from a Pydantic model and compare the two.

**Check yourself**
- Why do AI tool definitions use JSON Schema?
- What does `additionalProperties: false` protect you from?
- What's the advantage of `iter_errors` over `validate`?

---

### Lesson 11: Validating API Responses with Pydantic

**Concepts**

In Section 1 you used Pydantic to validate *your own* data. The bigger win is validating **data that comes from
outside**: API responses (and later, AI model outputs). Without validation, a missing field becomes a `KeyError`
three functions later, far from the cause. With validation, you fail **at the boundary**, with a clear message.

The pattern: **raw JSON → Pydantic model at the edge of your code → only typed objects inside.**

Tools you'll use:

| Feature | What it does |
|---|---|
| `ConfigDict(extra="ignore")` | Drop fields you didn't declare (default). `"forbid"` errors on unknown fields; `"allow"` keeps them. |
| `Field(validation_alias="stargazers_count")` | Read the API's name, expose your own name. |
| `AliasPath("owner", "login")` | Pull a value from deep inside nested JSON into a flat field. |
| `TypeAdapter(list[Repo])` | Validate things that aren't a single model (lists, dicts, unions). |
| `@field_validator` | Custom rule for one field. |
| `@model_validator(mode="before")` | Reshape the raw input before field validation. |
| `@field_serializer` | Control how a field is written out. |
| `model_dump(mode="json")` | Convert to JSON-safe Python (dates → strings, enums → values). |
| Discriminated unions | Pick the right model based on a `type` field. |
| `StrEnum` fields | Restrict a string to known values and get a real enum. |

**Code: a model for a GitHub repository**

```python
from datetime import datetime

from pydantic import (
    AliasPath, BaseModel, ConfigDict, Field, TypeAdapter, ValidationError,
    field_serializer, field_validator,
)


class Repo(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)   # frozen = read-only after creation

    full_name: str
    stars: int = Field(validation_alias="stargazers_count", ge=0)
    owner_login: str = Field(validation_alias=AliasPath("owner", "login"))
    topics: list[str] = []
    pushed_at: datetime                                       # ISO strings parsed automatically

    @field_validator("full_name")
    @classmethod
    def must_have_slash(cls, v: str) -> str:
        if "/" not in v:
            raise ValueError("expected 'owner/name'")
        return v

    @field_serializer("pushed_at")
    def iso_z(self, v: datetime) -> str:
        return v.strftime("%Y-%m-%dT%H:%M:%SZ")


raw = {   # a trimmed real GitHub response (the real one has ~80 fields)
    "id": 1, "full_name": "python/cpython", "stargazers_count": 70000,
    "owner": {"login": "python", "id": 2}, "pushed_at": "2026-11-03T22:10:05Z",
    "topics": ["python"], "lots_of": "other fields",
}

repo = Repo.model_validate(raw)
print(repo.stars, repo.owner_login, repo.pushed_at.year)
print(repo.model_dump(mode="json"))
# {'full_name': 'python/cpython', 'stars': 70000, 'owner_login': 'python', 'topics': ['python'],
#  'pushed_at': '2026-11-03T22:10:05Z'}

# A whole page of results:
repos = TypeAdapter(list[Repo]).validate_python([raw, raw])
```

**Code: useful error reports**

```python
try:
    Repo.model_validate({"full_name": "nope", "stargazers_count": -1, "owner": {}, "pushed_at": "yesterday"})
except ValidationError as e:
    for err in e.errors():
        print(err["loc"], "->", err["msg"])
# ('full_name',) -> Value error, expected 'owner/name'
# ('stargazers_count',) -> Input should be greater than or equal to 0
# ('owner', 'login') -> Field required
# ('pushed_at',) -> Input should be a valid datetime or date, input is too short
```

**Code: enums and reshaping input**

```python
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, model_validator


class IssueState(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class Issue(BaseModel):
    number: int
    title: str
    state: IssueState
    is_pull_request: bool = False

    @model_validator(mode="before")
    @classmethod
    def mark_pull_requests(cls, data: Any) -> Any:
        # GitHub's issues endpoint also returns PRs; they have a "pull_request" key.
        if isinstance(data, dict) and "pull_request" in data:
            data = {**data, "is_pull_request": True}
        return data


i = Issue.model_validate({"number": 5, "title": "Fix", "state": "open", "pull_request": {}})
print(i.state is IssueState.OPEN, i.is_pull_request, i.model_dump(mode="json"))
# True True {'number': 5, 'title': 'Fix', 'state': 'open', 'is_pull_request': True}
```

**Code: discriminated unions** (you'll use this to parse AI responses, which mix block types)

```python
from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter


class TextBlock(BaseModel):
    type: Literal["text"]
    text: str


class ToolUseBlock(BaseModel):
    type: Literal["tool_use"]
    name: str
    input: dict


Block = Annotated[TextBlock | ToolUseBlock, Field(discriminator="type")]

blocks = TypeAdapter(list[Block]).validate_python([
    {"type": "text", "text": "Let me check the weather."},
    {"type": "tool_use", "name": "get_weather", "input": {"city": "Oslo"}},
])
for b in blocks:
    match b:
        case TextBlock(text=text):
            print("Says:", text)
        case ToolUseBlock(name=name, input=args):
            print("Wants to call", name, "with", args)
```

**How strict should response models be?** Use `extra="ignore"` for API responses: APIs add new fields all the time
and that shouldn't break you. Make fields you truly need **required**, and give optional ones defaults. Use
`extra="forbid"` for **inputs** (e.g. tool arguments from an AI) so typos are caught.

**Common mistakes**
- Validating with `Repo(**raw)` when you use aliases: use `Repo.model_validate(raw)`.
- Marking everything optional "to be safe", which turns validation into a no-op.
- Using `model_dump()` then `json.dumps()` and getting a `datetime` error; use `model_dump(mode="json")` or `model_dump_json()`.
- Catching `ValidationError` and continuing silently. Log it with the raw data (minus secrets) so you can fix the model.

**Exercises**
1. Write a `User` model for `https://api.github.com/users/<name>` with `login`, `name` (optional), `public_repos`, `followers`, `created_at` (datetime), and `blog` (optional; GitHub sends `""` when empty, so convert `""` to `None` with a `field_validator(mode="before")`).
2. Model Open-Meteo's geocoding response: a `GeocodingResponse` with `results: list[Place] = []` (the key is **missing** entirely when nothing matches).
3. Write a `parse_or_report(model, items)` that validates a list item by item and returns `(valid_items, errors)` instead of failing on the first bad item.

**Check yourself**
- Why validate API responses at the boundary instead of reading dicts deep inside your code?
- What's the difference between `validation_alias` and `AliasPath`?
- When would you use `extra="forbid"` versus `extra="ignore"`?

---

### Lesson 12: CSV, YAML, and XML

**Concepts**

JSON dominates APIs, but you'll meet these three regularly.

| Format | Where you'll see it | Python tool |
|---|---|---|
| **CSV** | Spreadsheet exports, bank statements, reports | `csv` (standard library), `pandas` for analysis |
| **YAML** | Config files (GitHub Actions, Docker Compose, OpenAPI specs) | `pyyaml` (`yaml.safe_load`) |
| **XML** | RSS/Atom feeds, older enterprise and government APIs, office files | `defusedxml.ElementTree` (safe wrapper around `xml.etree`) |

**CSV: reading robustly**

Section 1 wrote CSV with `DictWriter`. Real-world CSV files vary: different delimiters (`;` in much of Europe),
quoted fields with commas inside, a byte-order mark at the start from Excel.

```python
import csv
import io

raw = 'date;description;amount\n2026-11-01;"Coffee; large";-3,50\n2026-11-02;Salary;2500,00\n'

dialect = csv.Sniffer().sniff(raw.splitlines()[0])          # guesses the delimiter
print("delimiter:", repr(dialect.delimiter))

rows = list(csv.DictReader(io.StringIO(raw), dialect=dialect))
for row in rows:
    amount = float(row["amount"].replace(",", "."))         # every value in CSV is a string
    print(row["date"], row["description"], amount)
```

When reading files exported from Excel, open them with `encoding="utf-8-sig"` (it strips the invisible BOM that
would otherwise end up glued to your first column name) and `newline=""` (the `csv` module handles line endings).

**YAML: always `safe_load`**

```python
import yaml

text = """
assistant:
  name: Organizer
  timezone: Europe/London
  apis:
    - name: weather
      base_url: https://api.open-meteo.com
      cache_minutes: 15
    - name: github
      base_url: https://api.github.com
"""

config = yaml.safe_load(text)
print(config["assistant"]["apis"][0]["cache_minutes"])     # 15 (an int, not a string)
print(yaml.safe_dump(config, sort_keys=False))
```

YAML guesses types, sometimes wrongly. Quote anything ambiguous:

```python
print(yaml.safe_load("country: NO"))       # {'country': False}   <- the "Norway problem"
print(yaml.safe_load("version: 3.10"))     # {'version': 3.1}     <- a float, not "3.10"
print(yaml.safe_load('version: "3.10"'))   # {'version': '3.10'}
```

**Never use `yaml.load` without a safe loader on untrusted input**: the full loader can construct arbitrary
Python objects. `yaml.safe_load` only builds plain dicts, lists, strings and numbers.

**XML: namespaces and safe parsing**

The European Central Bank publishes daily exchange rates as XML at
`https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml`. Its structure (shortened):

```python
import httpx
from defusedxml.ElementTree import fromstring   # pip install defusedxml - safe for data from the internet

SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<gesmes:Envelope xmlns:gesmes="http://www.gesmes.org/xml/2002-08-01"
                 xmlns="http://www.ecb.int/vocabulary/2002-08-01/eurofxref">
  <gesmes:subject>Reference rates</gesmes:subject>
  <Cube>
    <Cube time="2026-11-03">
      <Cube currency="USD" rate="1.0812"/>
      <Cube currency="GBP" rate="0.8423"/>
    </Cube>
  </Cube>
</gesmes:Envelope>"""

NS = {"ecb": "http://www.ecb.int/vocabulary/2002-08-01/eurofxref"}   # the default namespace needs a prefix


def parse_rates(xml_text: str) -> tuple[str, dict[str, float]]:
    root = fromstring(xml_text)
    day = root.find("ecb:Cube/ecb:Cube", NS)
    rates = {c.get("currency"): float(c.get("rate")) for c in day.findall("ecb:Cube", NS)}
    return day.get("time"), rates


print(parse_rates(SAMPLE))

# The real thing:
r = httpx.get("https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml", timeout=10)
r.raise_for_status()
day, rates = parse_rates(r.text)
print(day, "1 EUR =", rates["USD"], "USD")
```

The most common XML confusion: elements in a **namespace** (`xmlns="..."`) can't be found by their bare name.
`root.find("Cube")` returns `None`; you must use the namespace map as above.

Why `defusedxml` instead of `xml.etree.ElementTree.fromstring`? XML has features (entities, external references)
that a malicious document can abuse, e.g. the "billion laughs" attack that expands a tiny file into gigabytes.
`defusedxml` returns the same `Element` objects but refuses those tricks. Use it for any XML that comes over the network.

**Common mistakes**
- Splitting CSV lines with `line.split(",")`. Quoted fields with commas break it. Use the `csv` module.
- `yaml.load(text)` instead of `yaml.safe_load(text)`.
- Forgetting XML namespaces, then getting `None` from `find`.
- Treating every CSV value as a number: CSV has no types; convert explicitly.

**Exercises**
1. Download any bank-style CSV you have (or make one) and compute total spending per month with `csv.DictReader` and a `defaultdict(float)`.
2. Move your Work Organizer settings (data file path, default priority, timezone) into a `config.yaml` and load them into a Pydantic `Settings` model.
3. Fetch the ECB rates and write a function `convert(amount, from_ccy, to_ccy)` that converts between any two listed currencies via EUR.

**Check yourself**
- Why is `csv.Sniffer` useful?
- Why is `yaml.safe_load` safe and `yaml.load` not?
- Why does `root.find("Cube")` return `None` on the ECB document?

---

## Part E: Authentication and Secrets

### Lesson 13: API Keys, Bearer Tokens, and Basic Auth

**Concepts**

**Authentication** = proving who you are. **Authorization** = what you're allowed to do. APIs use a few schemes:

| Scheme | How it's sent | Typical use |
|---|---|---|
| **API key** | A header (`X-API-Key: ...`, `x-api-key: ...`) or, worse, a query param (`?appid=...`) | Simple server-to-server APIs, AI model APIs |
| **Bearer token** | `Authorization: Bearer <token>` | Personal access tokens, OAuth access tokens |
| **Basic auth** | `Authorization: Basic base64(username:password)` | Older APIs, some token APIs (Jira uses email + API token) |
| **OAuth 2.0** | Bearer tokens obtained via a consent flow | Acting on behalf of a user (Gmail, Calendar, GitHub apps) |
| **Signed requests (HMAC)** | A signature computed from the request and a secret | AWS, webhooks (Lesson 17) |

Basic auth is **not encryption**: base64 is reversible by anyone (`base64.b64encode(b"alice:wonderland")` gives
`YWxpY2U6d29uZGVybGFuZA==`, and decoding it gives the password back). It's only safe over https. Prefer headers to
query parameters for keys: URLs end up in server logs, browser history and proxies.

**GitHub personal access tokens.** Create one at GitHub → Settings → Developer settings → Personal access tokens →
**Fine-grained tokens**. Give it the minimum: one repository, read-only "Issues" and "Metadata", an expiry date.
Put it in `.env` as `GITHUB_TOKEN=...` (Section 1, Lesson 19).

**Code**

```python
import os

import httpx
from dotenv import load_dotenv

load_dotenv()
token = os.environ["GITHUB_TOKEN"]          # KeyError at startup beats a confusing 401 later

# Bearer token as a default header on the client
with httpx.Client(
    base_url="https://api.github.com",
    headers={"Authorization": f"Bearer {token}", "X-GitHub-Api-Version": "2022-11-28"},
    timeout=10,
) as client:
    me = client.get("/user").json()
    print("Logged in as", me["login"])
    print("Remaining:", client.get("/rate_limit").json()["resources"]["core"]["remaining"])   # 5000/hour now

# Basic auth: pass a (username, password) tuple; httpx builds the header
r = httpx.get("https://httpbin.org/basic-auth/alice/wonderland", auth=("alice", "wonderland"), timeout=10)
print(r.status_code, r.json())             # 200 {'authenticated': True, 'user': 'alice'}
```

**Custom auth classes.** httpx lets you package auth logic in an `httpx.Auth` subclass. Its `auth_flow` is a
generator: it can modify the request, `yield` it, look at the response, and retry. Here, refreshing an expired
token once on a 401:

```python
from collections.abc import Callable

import httpx


class RefreshingBearerAuth(httpx.Auth):
    """Add a bearer token; on a 401, refresh it once and retry the request."""

    def __init__(self, get_token: Callable[[], str], refresh: Callable[[], None]) -> None:
        self._get_token = get_token
        self._refresh = refresh

    def auth_flow(self, request: httpx.Request):
        request.headers["Authorization"] = f"Bearer {self._get_token()}"
        response = yield request
        if response.status_code == 401:
            self._refresh()
            request.headers["Authorization"] = f"Bearer {self._get_token()}"
            yield request

# client = httpx.Client(auth=RefreshingBearerAuth(store.get_access_token, store.refresh))
```

**Common mistakes**
- Committing a token, or printing it in a log or exception message. Redact: `token[:4] + "…"`.
- Creating "god tokens" with every permission and no expiry. Least privilege, short expiry.
- Hard-coding `"Bearer "` without the space, or sending `Bearer: token`.
- Treating 401 and 403 the same: 401 means fix/refresh credentials, 403 means you lack permission (or, on GitHub, rate limit).

**Exercises**
1. Create a fine-grained GitHub token with read-only access to one repo. Call `/user` and `/rate_limit` with and without it and compare limits.
2. Write an `httpx.Auth` subclass `ApiKeyAuth(header_name, key)` that adds a key header, and test it against `https://httpbin.org/headers`.

**Check yourself**
- Why is Basic auth only safe over https?
- Why should API keys go in headers rather than query strings?
- What does a 401 tell you that a 403 doesn't?

---

### Lesson 14: OAuth 2.0 Explained

**Concepts**

API keys identify *your app*. But your assistant needs to read *your user's* Gmail or calendar. You can't ask
users for their Google password (and Google wouldn't allow it anyway). **OAuth 2.0** solves this: the user logs in
**at Google**, approves a specific set of permissions, and Google gives your app a **token** limited to those permissions.

**The four roles**

| Role | In our example |
|---|---|
| **Resource owner** | The user (you) |
| **Client** | Your assistant app |
| **Authorization server** | Google's login/consent service (`accounts.google.com`, `oauth2.googleapis.com/token`) |
| **Resource server** | The API holding the data (Google Calendar API) |

**Key vocabulary**

| Term | Meaning |
|---|---|
| **Client ID** | Public identifier of your app. |
| **Client secret** | App password. Only truly secret for server-side apps; desktop/mobile apps can't hide it. |
| **Scope** | A specific permission, e.g. `https://www.googleapis.com/auth/calendar.readonly`. Ask for the fewest. |
| **Redirect URI** | Where the authorization server sends the user back, with a `code`. Must be registered in advance. |
| **Authorization code** | Short-lived, single-use code exchanged for tokens. |
| **Access token** | Sent as `Authorization: Bearer ...` to call the API. Short-lived (Google: about 1 hour). |
| **Refresh token** | Long-lived; exchanged for new access tokens without bothering the user. **Guard it like a password.** |
| **State** | Random value you send and check on return; prevents cross-site request forgery. |
| **PKCE** | "Proof Key for Code Exchange": proves the app that *finishes* the flow is the one that *started* it. |

**Grant types (flows)**

| Flow | Use it for |
|---|---|
| **Authorization code + PKCE** | Apps acting for a user: web, desktop, mobile, CLI. **The default choice.** |
| **Client credentials** | Machine-to-machine; no user involved. |
| **Device authorization** | Devices with no browser/keyboard (TVs, some CLIs: GitHub CLI's "enter this code" login). |
| ~~Implicit~~, ~~Password~~ | Deprecated by the OAuth 2.0 Security Best Current Practice (RFC 9700). Don't use. |

**Authorization code flow with PKCE, step by step**

```
 Your app                          Browser / User                 Google
    |  1. make code_verifier (random) + code_challenge = SHA256(verifier)
    |  2. open auth URL ----------------> |                           |
    |     (client_id, redirect_uri,       | 3. user logs in, sees     |
    |      scope, state, code_challenge)  |    "Allow Organizer to    |
    |                                     |    view your calendar?" -->|
    |  4. redirect to redirect_uri?code=XYZ&state=... <---------------|
    |  5. check state matches                                         |
    |  6. POST /token (code, code_verifier, client_id, ...) --------->|
    |                                         Google checks SHA256(verifier) == challenge
    |  7. <------------- {access_token, expires_in, refresh_token, scope}
    |  8. GET calendar API with "Authorization: Bearer <access_token>"
    |  ...an hour later the access token expires...
    |  9. POST /token (grant_type=refresh_token, refresh_token) ----->|
    | 10. <------------- {access_token (new), expires_in}
```

Why PKCE? If an attacker intercepts the `code` in step 4 (e.g. via a malicious app registered for the same
redirect URI), they still can't exchange it, because they don't have the `code_verifier` that only lives in your
app's memory.

**Code: what a library does for you** (for understanding; Lesson 15 uses a library)

```python
import base64
import hashlib
import secrets
from urllib.parse import urlencode


def make_pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) using the S256 method from RFC 7636."""
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


verifier, challenge = make_pkce_pair()
state = secrets.token_urlsafe(16)

auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode({
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "redirect_uri": "http://127.0.0.1:8765/",
    "response_type": "code",
    "scope": "https://www.googleapis.com/auth/calendar.readonly",
    "state": state,
    "code_challenge": challenge,
    "code_challenge_method": "S256",
    "access_type": "offline",        # Google-specific: ask for a refresh token
})
print(auth_url)

# After the redirect brings back ?code=...&state=..., you would:
#   assert returned_state == state
#   httpx.post("https://oauth2.googleapis.com/token", data={      <- form data, not JSON
#       "grant_type": "authorization_code", "code": code, "redirect_uri": ...,
#       "client_id": ..., "client_secret": ..., "code_verifier": verifier})
# Refreshing later:
#   httpx.post("https://oauth2.googleapis.com/token", data={
#       "grant_type": "refresh_token", "refresh_token": ..., "client_id": ..., "client_secret": ...})
```

**OpenID Connect (OIDC)** is a layer on top of OAuth 2.0 for *login* ("Sign in with Google"): add the `openid`
scope and you also get an **ID token** (a signed JWT saying who the user is). OAuth alone is about *access*, not identity.

**Common mistakes**
- Requesting broad scopes (`https://mail.google.com/` = full Gmail access) when `gmail.readonly` would do. Users (and Google's review) will notice.
- Not checking `state`.
- Storing refresh tokens in plain text in your repo folder (see Lesson 16).
- Assuming refresh tokens last forever: users can revoke them, and providers expire unused ones.

**Exercises**
1. Verify `make_pkce_pair` with the RFC 7636 test vector: verifier `dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk` must give challenge `E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM`.
2. Draw the flow from memory, labelling where the code, verifier, challenge, access token and refresh token each travel.

**Check yourself**
- What's the difference between an access token and a refresh token?
- What attack does PKCE prevent? What attack does `state` prevent?
- Which flow would you use for a script that syncs two of *your company's* systems with no user present?

---

### Lesson 15: Worked Example: Google OAuth with google-auth-oauthlib

**Concepts**

Google's `google-auth-oauthlib` package runs the whole authorization-code flow for a desktop/CLI app: it starts a
tiny local web server, opens the browser, catches the redirect, and exchanges the code (recent versions generate
the PKCE verifier automatically). `google-auth` then refreshes the access token for you.

**One-time setup in Google Cloud Console** (console.cloud.google.com):

1. **Create a project** (top bar → project picker → New project), e.g. "work-organizer".
2. **Enable the API**: APIs & Services → Library → search "Google Calendar API" → Enable.
3. **Configure consent** (shown as "Google Auth Platform" / "OAuth consent screen"): app name and support email;
   audience **External**; while the app is in **Testing**, add your own Google account under **Test users**.
4. **Create credentials**: Clients (or Credentials → Create credentials → OAuth client ID) → application type
   **Desktop app** → download the JSON and save it as `credentials.json` in your project. (It's already in `.gitignore`.)

Note: for apps in Testing mode with an External audience, Google expires refresh tokens after **7 days**, so you'll
re-consent weekly until you publish the app. That's normal for a personal project.

**Code**

```python
# google_calendar.py
from datetime import datetime, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CLIENT_SECRETS = Path("credentials.json")
TOKEN_FILE = Path("token.json")


def get_credentials() -> Credentials:
    creds: Credentials | None = None
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())                     # silent: uses the refresh token
    else:
        flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
        creds = flow.run_local_server(port=0)        # opens the browser; port=0 = any free port

    TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    TOKEN_FILE.chmod(0o600)                          # owner-only (no effect on Windows)
    return creds


def upcoming_events(max_results: int = 10) -> list[dict]:
    service = build("calendar", "v3", credentials=get_credentials())
    now = datetime.now(timezone.utc).isoformat()
    result = service.events().list(
        calendarId="primary",
        timeMin=now,
        maxResults=max_results,
        singleEvents=True,          # expand recurring events into individual ones
        orderBy="startTime",        # only allowed with singleEvents=True
    ).execute()
    return result.get("items", [])


if __name__ == "__main__":
    for event in upcoming_events():
        start = event["start"].get("dateTime", event["start"].get("date"))   # all-day events only have "date"
        print(start, event.get("summary", "(no title)"))
```

Run it:

```bash
python google_calendar.py
```

The first run opens a browser for consent ("Google hasn't verified this app" is expected in Testing mode: click
Continue). Later runs are silent until the refresh token expires or is revoked.

**Same call with plain httpx.** The Google client library is convenient, but the API is ordinary REST. Using the
same credentials with httpx shows there's no magic, and lets you reuse everything from Part C (retries, pagination with
`pageToken`/`nextPageToken`, validation):

```python
import httpx

creds = get_credentials()
r = httpx.get(
    "https://www.googleapis.com/calendar/v3/calendars/primary/events",
    headers={"Authorization": f"Bearer {creds.token}"},
    params={"maxResults": 5, "singleEvents": "true", "orderBy": "startTime",
            "timeMin": datetime.now(timezone.utc).isoformat()},
    timeout=10,
)
r.raise_for_status()
data = r.json()
print([e.get("summary") for e in data.get("items", [])], "next page:", data.get("nextPageToken"))
```

**Changing scopes** means asking for consent again: delete `token.json` after editing `SCOPES`, or you'll get
`403 insufficient permissions`. You (or a user) can revoke access any time at myaccount.google.com → Security →
Third-party connections.

**Common mistakes**
- Choosing "Web application" instead of "Desktop app" for a local script, then fighting `redirect_uri_mismatch` errors.
- Forgetting to add yourself as a test user (`access_denied` / "app is blocked").
- Committing `credentials.json` or `token.json`. `token.json` contains your refresh token.
- Forgetting to enable the API in the console (`403 accessNotConfigured` / "API has not been used in project").

**Exercises**
1. Complete the setup and print your next 10 events. Then change `SCOPES` to include `https://www.googleapis.com/auth/tasks.readonly`, re-consent, and list your Google Tasks lists with `build("tasks", "v1", ...)` and `.tasklists().list().execute()`.
2. Write a Pydantic `CalendarEvent` model (`id`, `summary`, `start`, `end`, `html_link` from `htmlLink`) that handles both timed (`dateTime`) and all-day (`date`) events.
3. Using httpx, fetch **all** events in the next 30 days, following `nextPageToken` (pass it back as the `pageToken` parameter).

**Check yourself**
- What two files does this flow use, and which one contains a refresh token?
- What does `creds.refresh(Request())` do and when is it called?
- Why must you re-consent after changing scopes?

---

### Lesson 16: Secrets Management Beyond .env

**Concepts**

A `.env` file (Section 1) is fine for learning, but it's a plain-text file on disk: any program running as you
can read it, it gets copied into backups, and it's one `git add .` away from a leak. Options, from simplest up:

| Option | How it works | Good for |
|---|---|---|
| `.env` + `.gitignore` | Plain text file | Learning, local dev |
| **OS keychain** via `keyring` | macOS Keychain, Windows Credential Locker, Linux Secret Service | Personal tools and desktop assistants |
| **Password manager CLI** | 1Password `op run`, Bitwarden `bws run`, Doppler `doppler run` inject secrets as env vars at launch | Teams, keeping secrets off disk |
| **Cloud secret manager** | AWS Secrets Manager, Google Secret Manager, Azure Key Vault, HashiCorp Vault | Deployed services; access controlled by IAM, audited, rotatable |
| **Platform secrets** | GitHub Actions secrets, Render/Vercel/Fly environment settings | CI/CD and hosting |

**Principles that apply everywhere**
- **Least privilege**: each token gets the minimum scopes and access to the minimum resources.
- **Short lifetimes and rotation**: expiring tokens limit damage. Rotate keys on a schedule and immediately after any suspected leak.
- **Never log secrets**: redact in logs, exceptions and error messages sent to an AI model.
- **Separate per environment**: different keys for dev and production.

**Code: `keyring`**

Store a secret once from the terminal (it prompts for the value, so it never lands in shell history):

```bash
keyring set work-organizer github-token
```

Use it from Python:

```python
import keyring

SERVICE = "work-organizer"

keyring.set_password(SERVICE, "openweather-key", "abc123")      # store (or update)
print(keyring.get_password(SERVICE, "github-token") is not None)  # read (None if missing)
keyring.delete_password(SERVICE, "openweather-key")               # remove
```

Storing the Google OAuth token in the keychain instead of `token.json`:

```python
import json

import keyring
from google.oauth2.credentials import Credentials

SERVICE, KEY = "work-organizer", "google-oauth-token"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def load_google_creds() -> Credentials | None:
    raw = keyring.get_password(SERVICE, KEY)
    return Credentials.from_authorized_user_info(json.loads(raw), SCOPES) if raw else None


def save_google_creds(creds: Credentials) -> None:
    keyring.set_password(SERVICE, KEY, creds.to_json())
```

On a headless Linux server there may be no keyring backend (`keyring.errors.NoKeyringError`). Use a secret manager there.

**Code: one settings object, many sources** (`pydantic-settings`)

```python
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    github_token: SecretStr | None = None          # read from GITHUB_TOKEN (case-insensitive)
    weather_cache_minutes: int = 15


settings = Settings()
print(settings)                                     # github_token=SecretStr('**********')  - safe to log
if settings.github_token:
    token = settings.github_token.get_secret_value()   # the real value, only where needed
```

Real environment variables override `.env` values, so the same code works locally (`.env`) and in production
(variables injected by a secret manager or `op run --env-file=.env -- python app.py`).

**Code: cloud secret managers** (each needs the provider's SDK and credentials configured; shown so you recognise them)

```python
# Google Secret Manager:  pip install google-cloud-secret-manager
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
name = "projects/my-project/secrets/github-token/versions/latest"
token = client.access_secret_version(request={"name": name}).payload.data.decode("utf-8")
```

```python
# AWS Secrets Manager:  pip install boto3
import boto3

token = boto3.client("secretsmanager").get_secret_value(SecretId="work-organizer/github-token")["SecretString"]
```

**Common mistakes**
- Moving secrets into a "config.py" that gets committed.
- Printing `settings` or exception objects that contain tokens. Use `SecretStr`.
- Sharing one powerful key between every environment and teammate, so you can never rotate it.
- Putting secrets in a Docker image or a frontend bundle, where anyone can extract them.

**Exercises**
1. Move your GitHub token from `.env` into `keyring`, and write `get_secret(name)` that checks the environment first, then the keyring, and raises a helpful error if neither has it.
2. Convert your Lesson 15 script to store the Google token in `keyring` instead of `token.json`.

**Check yourself**
- Name three weaknesses of `.env` files.
- What does `SecretStr` protect you from?
- Why do real environment variables override `.env` in `pydantic-settings`, and why is that useful?

---

## Part F: Webhooks, Rate Limits, and Caching

### Lesson 17: Webhooks and HMAC Signatures

**Concepts**

So far your code **asks** ("any new issues?") on a schedule: **polling**. A **webhook** reverses that: the other
service **calls your URL** with an HTTP `POST` the moment something happens (an issue is opened, a payment
succeeds, a calendar event changes). Your assistant can react instantly, and you spend no rate limit on empty polls.

| | Polling | Webhooks |
|---|---|---|
| Latency | Up to your polling interval | Seconds |
| Cost | Many wasted requests | One request per real event |
| Needs | Nothing special | A public HTTPS URL that's always up |
| Risk | Missing events between polls is unlikely | Missed deliveries if your server is down (providers retry for a while) |

Because your webhook URL is public, **anyone** can POST fake events to it. Providers solve this with an **HMAC
signature**: they compute `HMAC-SHA256(shared_secret, raw_request_body)` and send it in a header. You compute the
same thing with your copy of the secret and compare. Only someone who knows the secret can produce a matching signature.

| Provider | Signature header | What's signed |
|---|---|---|
| GitHub | `X-Hub-Signature-256: sha256=<hex>` | Raw body |
| Stripe | `Stripe-Signature: t=<timestamp>,v1=<hex>` | `"<timestamp>.<raw body>"` (the timestamp lets you reject old, replayed events) |
| Standard Webhooks spec (used by several providers) | `webhook-id`, `webhook-timestamp`, `webhook-signature` | `"<id>.<timestamp>.<body>"` |

**Rules for webhook receivers**
1. **Verify the signature on the raw bytes**, before parsing JSON. Re-serialising JSON changes spacing and breaks the signature.
2. Compare with **`hmac.compare_digest`**, not `==` (constant-time comparison prevents timing attacks).
3. **Respond fast** (GitHub expects a response within 10 seconds). Acknowledge with 2xx, then do slow work in the background or a queue.
4. **Be idempotent**: providers retry, so the same event can arrive twice. Track the delivery ID (`X-GitHub-Delivery`).
5. Reject events with old timestamps when the provider signs one (replay protection).

**Code: a GitHub webhook receiver with FastAPI**

```python
# webhook_server.py
import hashlib
import hmac
import json
import logging
import os

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Request

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("webhooks")
app = FastAPI()

WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
seen_deliveries: set[str] = set()          # use a database table in a real app


def verify_github_signature(body: bytes, signature_header: str | None, secret: str) -> bool:
    """Return True if X-Hub-Signature-256 matches HMAC-SHA256(secret, body)."""
    if not secret or not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def handle_event(event: str, payload: dict) -> None:
    """Slow work goes here; it runs after the response has been sent."""
    if event == "issues":
        log.info("Issue %s: %s", payload["action"], payload["issue"]["title"])
    elif event == "push":
        log.info("Push to %s with %d commits", payload["ref"], len(payload["commits"]))


@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
    background: BackgroundTasks,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str = Header(default="unknown"),
    x_github_delivery: str = Header(default=""),
):
    body = await request.body()                           # RAW bytes, before any JSON parsing
    if not verify_github_signature(body, x_hub_signature_256, WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="bad signature")
    if x_github_delivery in seen_deliveries:               # a redelivery: already handled
        return {"status": "duplicate"}
    seen_deliveries.add(x_github_delivery)
    background.add_task(handle_event, x_github_event, json.loads(body))
    return {"status": "accepted"}
```

Generate a strong secret, export it, and start the server:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
```bash
export GITHUB_WEBHOOK_SECRET=paste-the-value-here
```
```bash
uvicorn webhook_server:app --reload --port 8000
```

**Test it locally by signing a request yourself** (in a second terminal, with the same variable exported):

```python
# send_test_webhook.py
import hashlib
import hmac
import json
import os
import uuid

import httpx

secret = os.environ["GITHUB_WEBHOOK_SECRET"]
body = json.dumps({"action": "opened", "issue": {"title": "Test from my laptop"}}).encode()
signature = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

response = httpx.post(
    "http://127.0.0.1:8000/webhooks/github",
    content=body,                                   # send exactly the bytes we signed
    headers={
        "Content-Type": "application/json",
        "X-Hub-Signature-256": signature,
        "X-GitHub-Event": "issues",
        "X-GitHub-Delivery": str(uuid.uuid4()),
    },
)
print(response.status_code, response.json())       # 200 {'status': 'accepted'}
```

**Receiving real GitHub events on your laptop.** GitHub can't reach `127.0.0.1`, so use a tunnel that gives you a
temporary public URL: **smee.io** (recommended in GitHub's docs; `npx smee-client --url <your smee URL> --target http://127.0.0.1:8000/webhooks/github`),
**ngrok** (`ngrok http 8000`), or **Cloudflare Tunnel** (`cloudflared tunnel --url http://localhost:8000`). Then in
your repo: Settings → Webhooks → Add webhook → Payload URL = the tunnel URL, Content type = `application/json`,
Secret = your secret, choose the "Issues" event. GitHub's webhook page shows every delivery and lets you redeliver it.

**Common mistakes**
- Verifying `json.dumps(await request.json())` instead of the raw body.
- Using `==` to compare signatures.
- Doing slow work (calling an AI model!) before responding, so the provider times out and retries, causing duplicates.
- Skipping verification "just for now" on a public URL.

**Exercises**
1. Verify your function against GitHub's documented test case: secret `It's a Secret to Everybody`, body `Hello, World!`, expected signature `sha256=757107ea0eb2509fc211221cce984b8a37570b6d7586c22c46f4379c8b043e17`.
2. Send a request with a wrong signature and with no signature; confirm both get 401. Send the same delivery ID twice; confirm the second is a duplicate.
3. Write `verify_stripe_style(body, header, secret, tolerance=300)` that parses `t=...,v1=...`, signs `f"{t}.".encode() + body`, compares, and rejects timestamps older than `tolerance` seconds.

**Check yourself**
- Why must the signature be computed over the raw body?
- Why respond quickly and do the work in the background?
- How does a timestamp in the signature prevent replay attacks?

---

### Lesson 18: Client-Side Rate Limiting and Concurrency

**Concepts**

Lesson 7 handled the server saying "slow down" (429). Better still: **never hit the limit**. Two separate controls:

| Control | Limits | Python tool |
|---|---|---|
| **Concurrency limit** | How many requests are *in flight at once* | `asyncio.Semaphore(n)` |
| **Rate limit** | How many requests *start per time window* | A limiter (token bucket / sliding window) |

Async code makes it dangerously easy to fire 500 requests at once with `gather`. Most APIs will throttle or ban
you. Read the documented limit and stay under it. Also identify yourself with a descriptive `User-Agent`
(Open-Meteo, Wikipedia and GitHub all ask for this) and respect the API's terms (Open-Meteo's free tier is
for non-commercial use and has a daily call limit).

**Code**

```python
import asyncio
import time

import httpx


class AsyncRateLimiter:
    """Allow at most `rate` calls per `per` seconds (a sliding window)."""

    def __init__(self, rate: int, per: float = 1.0) -> None:
        self.rate = rate
        self.per = per
        self._calls: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                self._calls = [t for t in self._calls if now - t < self.per]   # forget old calls
                if len(self._calls) < self.rate:
                    self._calls.append(now)
                    return
                await asyncio.sleep(self.per - (now - self._calls[0]))        # wait for the oldest to expire


async def fetch_user(client: httpx.AsyncClient, limiter: AsyncRateLimiter,
                     sem: asyncio.Semaphore, username: str) -> dict:
    async with sem:                       # at most N in flight
        await limiter.acquire()           # at most R starts per second
        r = await client.get(f"/users/{username}")
        r.raise_for_status()
        return r.json()


async def main(usernames: list[str]) -> None:
    limiter = AsyncRateLimiter(rate=5, per=1.0)
    sem = asyncio.Semaphore(3)
    async with httpx.AsyncClient(base_url="https://api.github.com", timeout=10) as client:
        start = time.perf_counter()
        users = await asyncio.gather(*(fetch_user(client, limiter, sem, u) for u in usernames),
                                     return_exceptions=True)
        print(f"{len(users)} users in {time.perf_counter() - start:.1f}s")


asyncio.run(main(["python", "pallets", "psf", "pydantic", "encode", "astral-sh", "pypa"]))
```

`time.monotonic()` is used because it never jumps backwards (unlike the wall clock, which can change when your
computer syncs its time).

**Common mistakes**
- `gather` over thousands of URLs with no semaphore.
- A rate limiter per request instead of one shared limiter per API.
- Using `time.sleep` inside async code (freezes everything).

**Exercises**
1. Run `main` with 12 usernames and `rate=2`. Predict the duration before running it.
2. Write a synchronous `RateLimiter` with the same logic using `time.sleep` and `threading.Lock`, for your sync clients.

**Check yourself**
- What's the difference between a concurrency limit and a rate limit?
- Why `time.monotonic()` instead of `time.time()` for measuring intervals?

---

### Lesson 19: Caching

**Concepts**

The fastest, cheapest, most rate-limit-friendly request is the one you **don't make**. If your assistant asks
for Berlin's weather three times in a minute, the answer won't change. Caching also makes AI tool calls feel instant.

**HTTP's built-in caching headers**

| Header | Meaning |
|---|---|
| `Cache-Control: max-age=300` | This response is fresh for 300 seconds. |
| `Cache-Control: no-store` | Don't cache at all (private or always-changing data). |
| `ETag: "abc123"` | A fingerprint of this version. Send it back as `If-None-Match: "abc123"`. |
| `Last-Modified: <date>` | Send it back as `If-Modified-Since: <date>`. |
| `304 Not Modified` | Your copy is still current; the body is empty, so it's cheap. |

**Conditional requests with ETags** (GitHub documents that a 304 to a properly authenticated conditional request
does not count against your primary rate limit):

```python
import httpx

with httpx.Client(base_url="https://api.github.com", timeout=10) as client:
    first = client.get("/repos/python/cpython")
    etag = first.headers.get("ETag")
    second = client.get("/repos/python/cpython", headers={"If-None-Match": etag})
    print(first.status_code, second.status_code)        # 200 304
    data = first.json() if second.status_code == 304 else second.json()
```

**Option 1: `requests-cache`** (for code using `requests`): a drop-in session that stores responses in SQLite.

```python
from datetime import timedelta

import requests_cache

session = requests_cache.CachedSession(
    "http_cache",                          # creates http_cache.sqlite
    expire_after=timedelta(minutes=10),
    cache_control=True,                    # honour the server's Cache-Control headers when present
)
for _ in range(3):
    r = session.get("https://api.github.com/repos/python/cpython", timeout=10)
    print(r.status_code, "from cache:", r.from_cache)    # False, True, True
```

(For httpx, the `hishel` library plays the same role. In the capstone you'll write your own small cache instead,
so you understand exactly what's happening.)

**Option 2: a simple disk cache.** Cache the *parsed JSON* under a key built from the URL and parameters, with a
time-to-live (TTL):

```python
import hashlib
import json
import time
from pathlib import Path


def cache_key(url: str, params: dict) -> str:
    raw = json.dumps({"url": url, "params": params}, sort_keys=True)   # sort_keys: same params, same key
    return hashlib.sha256(raw.encode()).hexdigest()


def cached_get_json(client, url: str, params: dict, ttl: float = 600, folder: Path = Path(".cache")):
    path = folder / f"{cache_key(url, params)}.json"
    if path.exists():
        entry = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - entry["stored_at"] < ttl:
            return entry["data"]                                         # fresh: no request
    r = client.get(url, params=params)
    r.raise_for_status()
    folder.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"stored_at": time.time(), "data": r.json()}), encoding="utf-8")
    return r.json()
```

**What (not) to cache**

| Cache | TTL idea | Don't cache |
|---|---|---|
| Geocoding (city → lat/lon) | Days or weeks | Anything private in a shared cache |
| Weather forecast | 10–30 minutes | Responses to `POST`/`PATCH`/`DELETE` |
| Repo metadata | Minutes | Error responses (usually) |
| Exchange rates | Until the next daily update | Anything containing tokens |

For in-memory caching of pure functions within one run, `functools.lru_cache` or `functools.cache` is enough.

**Common mistakes**
- Including the API key or token in the cache key or cached data, then sharing the cache folder.
- Caching errors, so a temporary 503 sticks around for the full TTL.
- No TTL: stale data forever. "There are only two hard things in computer science: cache invalidation and naming things."
- Building keys without `sort_keys=True`, so `{a, b}` and `{b, a}` miss each other.

**Exercises**
1. Run the `requests-cache` example, delete `http_cache.sqlite`, and run it again. Then use `urls_expire_after={"*.open-meteo.com": 900}` to set per-host expiry.
2. Add a `use_cache: bool = True` parameter to `cached_get_json` and a `clear_cache()` function.
3. Make `cached_get_json` write atomically (write to a `.tmp` file then `Path.replace`), and explain why that matters if two processes run at once.

**Check yourself**
- What does an `ETag` let you do?
- Why use `sort_keys=True` when building cache keys?
- Give one thing you'd cache for a week and one you'd never cache.

---

## Part G: Testing API Code

### Lesson 20: Mocking HTTP with respx and pytest-httpx

**Concepts**

Tests that call real APIs are **slow, flaky** (the network fails), **rate-limited**, and can't easily reproduce
errors like "503 twice, then success". Instead, intercept httpx and return **fake responses** you control.

| Library | Style | Notes |
|---|---|---|
| **respx** | Decorator/context manager; define routes like a mini router | Rich matching, `side_effect` lists for sequences, works with sync and async |
| **pytest-httpx** | A pytest fixture called `httpx_mock` | Very concise; by default fails the test if a registered response is never requested |

Both patch httpx's transport, so your real client code runs unchanged; only the network is fake. What to test:

- The happy path parses into the right models.
- Errors map to your exceptions (404 → `NotFoundError`).
- Retries happen for 503/429 and stop after N attempts; `Retry-After` is respected.
- Pagination follows `next` links and stops.
- The right URL, parameters and headers are sent.

**Code: respx**

```python
# test_weather_basic.py
import httpx
import pytest
import respx

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def current_temperature(client: httpx.Client, lat: float, lon: float) -> float:
    r = client.get(FORECAST_URL, params={"latitude": lat, "longitude": lon, "current": "temperature_2m"})
    r.raise_for_status()
    return r.json()["current"]["temperature_2m"]


@respx.mock
def test_reads_temperature():
    route = respx.get(FORECAST_URL).mock(
        return_value=httpx.Response(200, json={"current": {"temperature_2m": 11.5}})
    )
    with httpx.Client() as client:
        assert current_temperature(client, 51.5, -0.12) == 11.5
    assert route.called
    assert route.calls.last.request.url.params["latitude"] == "51.5"


@respx.mock
def test_server_error_raises():
    respx.get(FORECAST_URL).mock(return_value=httpx.Response(500))
    with httpx.Client() as client, pytest.raises(httpx.HTTPStatusError):
        current_temperature(client, 0, 0)


@respx.mock
def test_sequence_of_responses():
    route = respx.get(FORECAST_URL).mock(side_effect=[
        httpx.Response(503),
        httpx.ConnectTimeout("simulated timeout"),          # exceptions can be raised too
        httpx.Response(200, json={"current": {"temperature_2m": 3.0}}),
    ])
    with httpx.Client() as client:
        for _ in range(2):
            try:
                current_temperature(client, 0, 0)
            except (httpx.HTTPStatusError, httpx.TimeoutException):
                pass
        assert current_temperature(client, 0, 0) == 3.0
    assert route.call_count == 3
```

By default respx **fails the test if your code makes a request you didn't mock**, so a test can never accidentally
hit the real internet.

**Code: pytest-httpx**

```python
# test_weather_httpx_mock.py
import httpx


def test_get_temperature(httpx_mock):
    httpx_mock.add_response(
        url="https://api.open-meteo.com/v1/forecast?latitude=51.5&longitude=-0.12&current=temperature_2m",
        json={"current": {"temperature_2m": 11.5}},
    )
    with httpx.Client() as client:
        r = client.get("https://api.open-meteo.com/v1/forecast",
                       params={"latitude": 51.5, "longitude": -0.12, "current": "temperature_2m"})
    assert r.json()["current"]["temperature_2m"] == 11.5
```

Run the tests:

```bash
pytest -v
```

**Make code testable: inject what you'd otherwise hard-code.** If your client calls `time.sleep(8)` on a retry, your
test takes 8 seconds. Pass `sleep` in as a parameter (default `time.sleep`) and give tests a fake that records the
waits instead. Same for clocks (`time.time`) and cache folders (pytest's `tmp_path`). The capstone does all three.

**Recording real responses.** Copy a real response into a test fixture once (e.g. `curl ... > tests/data/forecast.json`),
trim it, and load it in tests. Then your fakes match reality. Re-record occasionally, and keep a *small* number of
optional "live" tests marked with `@pytest.mark.skipif(not os.getenv("LIVE_TESTS"), reason="network")`.

**Common mistakes**
- Mocking your *own* functions instead of the HTTP layer, so the real parsing code never runs in tests.
- Fake responses that don't look like the real API (invented field names). Base them on recorded responses.
- Tests that sleep for real during retries.
- Forgetting async tests need a runner: with `pytest-asyncio` or `anyio`, mark async tests accordingly (respx works the same inside them).

**Exercises**
1. Write tests for your Lesson 7 `get_with_retries`: 503 then 200 succeeds; four 500s raise; 404 is not retried (`route.call_count == 1`).
2. Write a test for Lesson 8's `paginate` with two fake pages linked by a `Link` header.
3. Rewrite exercise 1 with `pytest-httpx` and compare the two styles.

**Check yourself**
- Give three reasons not to hit real APIs in unit tests.
- How do you make respx return a 503 first and a 200 second?
- Why inject `sleep` into a client?

---

## Capstone Project: Typed API Client Library

Build a small, typed, tested Python package that wraps two real free APIs: **Open-Meteo** (weather and
geocoding, no key needed) and **GitHub** (repositories and issues, optional token). It uses everything in this
section, and its `tools.py` functions become the first real tools your AI assistant calls in Section 3.

### Requirements

**Level 1 — works**
- `WeatherClient.geocode(name)` → a `Location` model; raises `NotFoundError` for unknown places
- `WeatherClient.forecast_for_city(city, days)` → a `Forecast` model (current conditions + one row per day)
- `GitHubClient.list_user_repos(username, limit)` → `list[Repo]`, following `Link` pagination
- `GitHubClient.list_open_issues(owner, repo)` → `list[Issue]`, excluding pull requests by default
- One shared `httpx.Client` per API client, with `base_url`, timeouts and a descriptive `User-Agent`

**Level 2 — reliable**
- Retries with exponential backoff + jitter for timeouts, connection errors, 429 and 5xx, **only for idempotent methods**
- `Retry-After` respected; GitHub's `403` + `x-ratelimit-remaining: 0` raises `RateLimitedError`
- A disk cache with TTL for GET requests (geocoding and forecasts)
- All responses validated with Pydantic; validation failures raise `ResponseValidationError`
- Every error the caller sees is a subclass of `ApiError`

**Level 3 — professional**
- At least 15 pytest tests using **respx**, none touching the network, all running in under a second
- `sleep` and cache folder injected so tests are instant and isolated
- `ruff check` passes; type hints everywhere; docstrings on every public function
- Optional `GITHUB_TOKEN` loaded via `pydantic-settings` or `keyring`, never logged
- `tools.py` exposes plain functions returning JSON-friendly dicts and never raising (errors become `{"error": ...}`)

### Suggested structure
```
api_clients/
├── .gitignore
├── README.md
├── pyproject.toml           # or requirements.txt: httpx, pydantic, pytest, respx
├── apis/
│   ├── __init__.py
│   ├── errors.py            # exception hierarchy
│   ├── cache.py             # DiskCache with TTL
│   ├── http.py              # BaseApiClient: retries, Retry-After, caching, pagination
│   ├── weather.py           # Open-Meteo models + WeatherClient
│   ├── github.py            # GitHub models + GitHubClient
│   └── tools.py             # simple functions: future AI tools
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_http.py
    ├── test_weather.py
    └── test_github.py
```

### Starter skeleton (fill in the TODOs)

```python
# apis/errors.py  (complete - no TODOs)
class ApiError(Exception):
    """Base class for every error raised by this package."""


class NotFoundError(ApiError):
    """The resource does not exist (HTTP 404, or no search results)."""


class RateLimitedError(ApiError):
    """The API told us to slow down and we ran out of retries."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ServerError(ApiError):
    """The API failed on its side (HTTP 5xx) and retries did not help."""


class ResponseValidationError(ApiError):
    """The API answered, but the data did not match our Pydantic models."""
```

```python
# apis/cache.py
import hashlib
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any


class DiskCache:
    def __init__(self, directory: Path, ttl_seconds: float = 600,
                 clock: Callable[[], float] = time.time) -> None:
        self.directory = Path(directory)
        self.ttl_seconds = ttl_seconds
        self._clock = clock                  # injectable so tests can fake the passing of time

    @staticmethod
    def make_key(url: str, params: dict[str, Any] | None = None) -> str:
        raw = json.dumps({"url": url, "params": params or {}}, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Any | None:
        # TODO: return None if the file is missing or unreadable (json.JSONDecodeError, OSError)
        # TODO: if self._clock() - entry["stored_at"] > self.ttl_seconds: delete it and return None
        # TODO: otherwise return entry["data"]
        ...

    def set(self, key: str, data: Any) -> None:
        # TODO: mkdir, write {"stored_at": self._clock(), "data": data} to a .tmp file, then .replace()
        ...
```

```python
# apis/http.py
import logging
import random
import time
from collections.abc import Callable, Iterator
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from apis.cache import DiskCache
from apis.errors import ApiError, NotFoundError, RateLimitedError, ServerError

log = logging.getLogger(__name__)

RETRYABLE_STATUS = {429, 500, 502, 503, 504}
IDEMPOTENT_METHODS = {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"}
USER_AGENT = "work-organizer-assistant/0.1 (learning project)"


def parse_retry_after(value: str | None) -> float | None:
    """Turn a Retry-After header (seconds or an HTTP date) into seconds to wait."""
    # TODO: reuse your solution from Lesson 7 (treat a date without timezone as UTC)
    ...


class BaseApiClient:
    def __init__(
        self,
        base_url: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float = 10.0,
        max_retries: int = 3,
        backoff_base: float = 0.5,
        cache: DiskCache | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.cache = cache
        self._sleep = sleep
        self._client = httpx.Client(
            base_url=base_url,
            headers={"User-Agent": USER_AGENT, **(headers or {})},
            timeout=httpx.Timeout(timeout, connect=5.0),
            follow_redirects=True,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def _backoff(self, attempt: int) -> float:
        return self.backoff_base * 2**attempt + random.uniform(0, self.backoff_base)

    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        """Send a request, retrying transient failures for idempotent methods."""
        method = method.upper()
        retries = self.max_retries if method in IDEMPOTENT_METHODS else 0
        for attempt in range(retries + 1):
            is_last = attempt == retries
            # TODO: call self._client.request(method, url, **kwargs)
            # TODO: on httpx.TransportError: if is_last raise ApiError(...) from exc,
            #       else self._sleep(self._backoff(attempt)) and continue
            # TODO: if status in RETRYABLE_STATUS and not is_last: sleep for Retry-After
            #       (or backoff if absent) and continue
            # TODO: otherwise self._raise_for_status(response) and return response
            ...
        raise AssertionError("unreachable")

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Convert HTTP errors into our own exception types."""
        status = response.status_code
        if status < 400:
            return
        url = str(response.request.url)
        if status == 404:
            raise NotFoundError(f"Not found: {url}")
        if status == 429:
            raise RateLimitedError(f"Rate limited by {url}",
                                   parse_retry_after(response.headers.get("Retry-After")))
        if status >= 500:
            raise ServerError(f"Server error {status} from {url}")
        raise ApiError(f"HTTP {status} from {url}: {response.text[:200]}")

    def get_json(self, url: str, params: dict[str, Any] | None = None, *,
                 use_cache: bool = True) -> Any:
        """GET a URL and return decoded JSON, using the disk cache when configured."""
        key = DiskCache.make_key(str(self._client.base_url.join(url)), params)
        # TODO: return the cached value if use_cache and self.cache has it
        # TODO: otherwise self.request("GET", ...).json(), store it in the cache, return it
        ...

    def paginate(self, url: str, params: dict[str, Any] | None = None, *,
                 max_pages: int = 10) -> Iterator[Any]:
        """Yield items from every page, following Link: rel="next" headers."""
        # TODO: Lesson 8's paginate(), but using self.request(...) so retries apply
        ...
```

```python
# apis/weather.py
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from apis.cache import DiskCache
from apis.errors import NotFoundError, ResponseValidationError
from apis.http import BaseApiClient

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

WEATHER_CODES: dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog", 51: "Light drizzle", 53: "Moderate drizzle",
    55: "Dense drizzle", 61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow", 80: "Slight rain showers",
    81: "Moderate rain showers", 82: "Violent rain showers", 95: "Thunderstorm",
    96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
}


class Location(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    latitude: float
    longitude: float
    country: str | None = None
    admin1: str | None = None
    timezone: str | None = None


class CurrentWeather(BaseModel):
    time: datetime
    temperature_c: float = Field(validation_alias="temperature_2m")
    wind_speed_kmh: float = Field(validation_alias="wind_speed_10m")
    weather_code: int

    @property
    def description(self) -> str:
        return WEATHER_CODES.get(self.weather_code, f"Code {self.weather_code}")


class DailyForecast(BaseModel):
    day: date
    temp_max_c: float | None
    temp_min_c: float | None
    precipitation_mm: float | None
    weather_code: int | None


class _DailyColumns(BaseModel):
    """Open-Meteo returns daily data as parallel lists ("columns")."""

    time: list[date]
    temperature_2m_max: list[float | None]
    temperature_2m_min: list[float | None]
    precipitation_sum: list[float | None]
    weather_code: list[int | None]

    def to_rows(self) -> list[DailyForecast]:
        # TODO: zip(..., strict=True) the five lists into DailyForecast objects
        ...


class _ForecastResponse(BaseModel):
    current: CurrentWeather
    daily: _DailyColumns


class Forecast(BaseModel):
    location: Location
    current: CurrentWeather
    days: list[DailyForecast]


class WeatherClient(BaseApiClient):
    def __init__(self, cache: DiskCache | None = None, **kwargs: Any) -> None:
        super().__init__("https://api.open-meteo.com", cache=cache, **kwargs)

    def geocode(self, name: str) -> Location:
        data = self.get_json(GEOCODING_URL,
                             {"name": name, "count": 1, "language": "en", "format": "json"})
        # TODO: "results" is MISSING when nothing matches -> raise NotFoundError
        # TODO: validate results[0] as Location; wrap ValidationError in ResponseValidationError
        ...

    def forecast(self, location: Location, days: int = 3) -> Forecast:
        if not 1 <= days <= 16:
            raise ValueError("days must be between 1 and 16")
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "current": "temperature_2m,wind_speed_10m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
            "timezone": "auto",
            "forecast_days": days,
        }
        # TODO: get_json, validate as _ForecastResponse, return Forecast(..., days=raw.daily.to_rows())
        ...

    def forecast_for_city(self, city: str, days: int = 3) -> Forecast:
        return self.forecast(self.geocode(city), days)
```

```python
# apis/github.py
import time
from datetime import datetime
from typing import Any, Literal

import httpx
from pydantic import AliasPath, BaseModel, Field, TypeAdapter, ValidationError, model_validator

from apis.errors import RateLimitedError, ResponseValidationError
from apis.http import BaseApiClient


class Repo(BaseModel):
    name: str
    full_name: str
    description: str | None = None
    stars: int = Field(validation_alias="stargazers_count")
    language: str | None = None
    html_url: str
    updated_at: datetime
    fork: bool = False
    archived: bool = False


class Issue(BaseModel):
    number: int
    title: str
    state: Literal["open", "closed"]
    author: str = Field(validation_alias=AliasPath("user", "login"))
    created_at: datetime
    html_url: str
    is_pull_request: bool = False

    @model_validator(mode="before")
    @classmethod
    def _mark_pull_requests(cls, data: Any) -> Any:
        if isinstance(data, dict) and "pull_request" in data:
            data = {**data, "is_pull_request": True}
        return data


_repos = TypeAdapter(list[Repo])


class GitHubClient(BaseApiClient):
    def __init__(self, token: str | None = None, **kwargs: Any) -> None:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        super().__init__("https://api.github.com", headers=headers, **kwargs)

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.status_code == 403 and response.headers.get("x-ratelimit-remaining") == "0":
            reset = float(response.headers.get("x-ratelimit-reset", "0"))
            raise RateLimitedError("GitHub rate limit exhausted",
                                   retry_after=max(0.0, reset - time.time()))
        super()._raise_for_status(response)

    def list_user_repos(self, username: str, limit: int = 30) -> list[Repo]:
        """Most recently updated public repos of a user, at most `limit`."""
        params = {"per_page": min(limit, 100), "sort": "updated"}
        # TODO: collect items from self.paginate(f"/users/{username}/repos", params)
        #       and stop as soon as you have `limit` (so no extra pages are fetched)
        # TODO: validate with _repos.validate_python(...), wrapping ValidationError
        ...

    def list_open_issues(self, owner: str, repo: str, *,
                         include_pull_requests: bool = False, limit: int = 30) -> list[Issue]:
        """Open issues of a repository (pull requests skipped unless asked for)."""
        # TODO: paginate /repos/{owner}/{repo}/issues with state=open, per_page=100
        # TODO: validate each item, skip PRs unless include_pull_requests, stop at limit
        ...
```

```python
# apis/tools.py  (complete - these are your future AI tools)
"""Plain functions with simple inputs and JSON-friendly outputs. They never raise."""

import os
from pathlib import Path

from apis.cache import DiskCache
from apis.errors import ApiError
from apis.github import GitHubClient
from apis.weather import WeatherClient

CACHE_DIR = Path(".cache/apis")


def get_weather_forecast(city: str, days: int = 3) -> dict:
    """Get current weather and a daily forecast for a city.

    Args:
        city: City name, e.g. "Berlin" or "Austin".
        days: Number of forecast days, 1-16.

    Returns:
        A dict with "location", "current" and "days", or {"error": "..."} on failure.
    """
    try:
        with WeatherClient(cache=DiskCache(CACHE_DIR / "weather", ttl_seconds=900)) as client:
            forecast = client.forecast_for_city(city, days)
    except (ApiError, ValueError) as exc:
        return {"error": str(exc)}
    result = forecast.model_dump(mode="json")
    result["current"]["description"] = forecast.current.description
    return result


def list_github_repos(username: str, limit: int = 10) -> list[dict] | dict:
    """List a GitHub user's most recently updated public repositories.

    Args:
        username: GitHub login, e.g. "torvalds".
        limit: Maximum number of repositories to return.
    """
    try:
        with GitHubClient(token=os.getenv("GITHUB_TOKEN")) as client:
            repos = client.list_user_repos(username, limit)
    except ApiError as exc:
        return {"error": str(exc)}
    fields = {"full_name", "stars", "language", "html_url"}
    return [r.model_dump(mode="json", include=fields) for r in repos]


if __name__ == "__main__":
    import json

    print(json.dumps(get_weather_forecast("Berlin", 2), indent=2))
    print(json.dumps(list_github_repos("python", 3), indent=2))
```

### Tests (these define "done")

```python
# tests/conftest.py
import pytest

from apis.cache import DiskCache
from apis.github import GitHubClient
from apis.weather import WeatherClient


class SleepRecorder:
    """Stands in for time.sleep: tests run instantly and can check the waits."""

    def __init__(self) -> None:
        self.calls: list[float] = []

    def __call__(self, seconds: float) -> None:
        self.calls.append(seconds)


@pytest.fixture
def sleeps() -> SleepRecorder:
    return SleepRecorder()


@pytest.fixture
def weather(sleeps, tmp_path):
    with WeatherClient(cache=DiskCache(tmp_path / "cache"), sleep=sleeps) as client:
        yield client


@pytest.fixture
def github(sleeps):
    with GitHubClient(token="test-token", sleep=sleeps) as client:
        yield client
```

```python
# tests/test_weather.py
import httpx
import pytest
import respx

from apis.errors import NotFoundError, ServerError
from apis.weather import FORECAST_URL, GEOCODING_URL

BERLIN = {"results": [{"id": 2950159, "name": "Berlin", "latitude": 52.52437, "longitude": 13.41053,
                       "country": "Germany", "admin1": "Land Berlin", "timezone": "Europe/Berlin"}]}
FORECAST = {
    "latitude": 52.52, "longitude": 13.42, "timezone": "Europe/Berlin",
    "current": {"time": "2026-11-04T14:00", "interval": 900, "temperature_2m": 9.3,
                "wind_speed_10m": 14.2, "weather_code": 3},
    "daily": {"time": ["2026-11-04", "2026-11-05"], "temperature_2m_max": [10.1, 8.7],
              "temperature_2m_min": [4.2, 3.9], "precipitation_sum": [0.0, 2.4],
              "weather_code": [3, 61]},
}


@respx.mock
def test_geocode_returns_first_result(weather):
    route = respx.get(GEOCODING_URL).mock(return_value=httpx.Response(200, json=BERLIN))
    place = weather.geocode("Berlin")
    assert (place.name, place.country) == ("Berlin", "Germany")
    assert route.calls.last.request.url.params["name"] == "Berlin"


@respx.mock
def test_geocode_unknown_place_raises_not_found(weather):
    respx.get(GEOCODING_URL).mock(return_value=httpx.Response(200, json={"generationtime_ms": 0.5}))
    with pytest.raises(NotFoundError):
        weather.geocode("Nowhereville")


@respx.mock
def test_forecast_turns_columns_into_rows(weather):
    respx.get(GEOCODING_URL).mock(return_value=httpx.Response(200, json=BERLIN))
    respx.get(FORECAST_URL).mock(return_value=httpx.Response(200, json=FORECAST))
    forecast = weather.forecast_for_city("Berlin", days=2)
    assert forecast.current.description == "Overcast"
    assert [d.precipitation_mm for d in forecast.days] == [0.0, 2.4]


@respx.mock
def test_retries_503_then_succeeds(weather, sleeps):
    route = respx.get(GEOCODING_URL).mock(
        side_effect=[httpx.Response(503), httpx.Response(503), httpx.Response(200, json=BERLIN)])
    assert weather.geocode("Berlin").name == "Berlin"
    assert route.call_count == 3 and len(sleeps.calls) == 2


@respx.mock
def test_respects_retry_after(weather, sleeps):
    respx.get(GEOCODING_URL).mock(side_effect=[
        httpx.Response(429, headers={"Retry-After": "7"}), httpx.Response(200, json=BERLIN)])
    weather.geocode("Berlin")
    assert sleeps.calls == [7.0]


@respx.mock
def test_gives_up_after_max_retries(weather):
    route = respx.get(GEOCODING_URL).mock(return_value=httpx.Response(500))
    with pytest.raises(ServerError):
        weather.geocode("Berlin")
    assert route.call_count == 4                     # 1 try + 3 retries


@respx.mock
def test_network_errors_are_retried(weather):
    respx.get(GEOCODING_URL).mock(
        side_effect=[httpx.ConnectTimeout("slow"), httpx.Response(200, json=BERLIN)])
    assert weather.geocode("Berlin").name == "Berlin"


@respx.mock
def test_second_call_is_served_from_cache(weather):
    route = respx.get(GEOCODING_URL).mock(return_value=httpx.Response(200, json=BERLIN))
    weather.geocode("Berlin")
    weather.geocode("Berlin")
    assert route.call_count == 1
```

```python
# tests/test_github.py
import httpx
import pytest
import respx

from apis.errors import ApiError, NotFoundError, RateLimitedError

API = "https://api.github.com"


def repo(name: str) -> dict:
    return {"name": name, "full_name": f"octocat/{name}", "stargazers_count": 1,
            "language": "Python", "html_url": f"https://github.com/octocat/{name}",
            "updated_at": "2026-10-01T12:00:00Z"}


def issue(number: int, pr: bool = False) -> dict:
    data = {"number": number, "title": f"Issue {number}", "state": "open",
            "user": {"login": "octocat"}, "created_at": "2026-10-01T12:00:00Z",
            "html_url": f"https://github.com/octocat/hello/issues/{number}"}
    return data | ({"pull_request": {}} if pr else {})


@respx.mock
def test_follows_link_header(github):
    page2 = f"{API}/user/1/repos?page=2"
    respx.get(f"{API}/users/octocat/repos").mock(return_value=httpx.Response(
        200, json=[repo("a"), repo("b")], headers={"Link": f'<{page2}>; rel="next"'}))
    respx.get(f"{API}/user/1/repos").mock(return_value=httpx.Response(200, json=[repo("c")]))
    assert [r.name for r in github.list_user_repos("octocat", limit=10)] == ["a", "b", "c"]


@respx.mock
def test_stops_at_limit_without_fetching_more_pages(github):
    respx.get(f"{API}/users/octocat/repos").mock(return_value=httpx.Response(
        200, json=[repo("a"), repo("b")], headers={"Link": f'<{API}/user/1/repos?page=2>; rel="next"'}))
    second = respx.get(f"{API}/user/1/repos")
    assert len(github.list_user_repos("octocat", limit=2)) == 2
    assert not second.called


@respx.mock
def test_sends_auth_and_version_headers(github):
    route = respx.get(f"{API}/users/octocat/repos").mock(return_value=httpx.Response(200, json=[]))
    github.list_user_repos("octocat")
    headers = route.calls.last.request.headers
    assert headers["Authorization"] == "Bearer test-token"
    assert headers["X-GitHub-Api-Version"] == "2022-11-28"


@respx.mock
def test_pull_requests_filtered_out(github):
    respx.get(f"{API}/repos/octocat/hello/issues").mock(
        return_value=httpx.Response(200, json=[issue(1), issue(2, pr=True), issue(3)]))
    issues = github.list_open_issues("octocat", "hello")
    assert [i.number for i in issues] == [1, 3] and issues[0].author == "octocat"


@respx.mock
def test_missing_user_raises_not_found(github):
    respx.get(f"{API}/users/ghost-xyz/repos").mock(return_value=httpx.Response(404))
    with pytest.raises(NotFoundError):
        github.list_user_repos("ghost-xyz")


@respx.mock
def test_exhausted_rate_limit_raises(github):
    respx.get(f"{API}/users/octocat/repos").mock(return_value=httpx.Response(
        403, headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "0"}))
    with pytest.raises(RateLimitedError):
        github.list_user_repos("octocat")


@respx.mock
def test_post_is_never_retried(github):
    route = respx.post(f"{API}/repos/octocat/hello/issues").mock(return_value=httpx.Response(502))
    with pytest.raises(ApiError):
        github.request("POST", "/repos/octocat/hello/issues", json={"title": "x"})
    assert route.call_count == 1
```

Write `tests/test_http.py` yourself: `parse_retry_after` with seconds, an HTTP date, `None` and garbage; the
cache expiring after its TTL (pass a fake `clock`); and cache keys ignoring parameter order.

Run everything:

```bash
pytest -v
```
```bash
ruff check .
```
```bash
python -m apis.tools
```

**Why `tools.py` matters:** in Section 3 you'll hand `get_weather_forecast` and `list_github_repos` to an AI model.
The model only sees each function's name, docstring and a JSON Schema of its arguments, and it only ever receives
the returned dict. That's why these functions take simple arguments, return JSON-friendly data, and turn every
failure into `{"error": "..."}` the model can read and explain, instead of crashing your assistant. All the
complexity (retries, caching, validation, pagination) stays hidden in the layers you built underneath.

---

## Weekly Schedule

| Week | Lessons | Mini-project |
|---|---|---|
| 1 | Part 0, Lessons 1–3 | Log every header of 5 different APIs with event hooks; classify methods by idempotency |
| 2 | Lessons 4–5 | Fill the docs checklist for GitHub and Open-Meteo; build a Bruno/Postman collection |
| 3 | Lessons 6–7 | A sync + async weather fetcher with timeouts and retries |
| 4 | Lesson 8 | Count all open issues of a big repo with Link pagination |
| 5 | Lessons 9–12 | Pydantic models for GitHub and Open-Meteo; load settings from YAML |
| 6 | Lessons 13–14 | GitHub token client; PKCE by hand |
| 7 | Lessons 15–16 | Google Calendar "next 10 events" with tokens in the keychain |
| 8 | Lessons 17–19 | Webhook receiver + rate limiter + cache |
| 9 | Lesson 20, Capstone Levels 1–2 | Typed clients with retries and caching |
| 10 | Capstone Level 3 | Full test suite, `tools.py`, README, pushed to GitHub |

**Daily routine (1–2 hours):** 15 min reading → 15 min exploring the real API with curl/HTTPie → 40 min typing
examples → 30 min exercises → 5 min notes. Always look at a real response before writing code that parses it.

---

## Final Checklist

Before starting Section 3 (AI models and tool calling), you should be able to do all of this **without looking things up**:

**How the web works**
- [ ] Break a URL into its parts and build query strings safely
- [ ] Explain DNS, TCP, TLS and keep-alive in a few sentences each
- [ ] Read a raw HTTP request/response and name the common headers
- [ ] Say which methods are safe and idempotent, and when a retry could duplicate an action

**APIs and tools**
- [ ] Read API docs for auth, rate limits, pagination and error format before coding
- [ ] Explore an API with curl + jq and HTTPie; save requests in Bruno or Postman

**httpx**
- [ ] Use `httpx.Client`/`AsyncClient` with `base_url`, headers and a `Timeout`
- [ ] Handle the httpx exception hierarchy correctly
- [ ] Retry transient failures with backoff + jitter (by hand and with tenacity), honouring `Retry-After`
- [ ] Paginate page/offset, cursor and `Link`-header APIs with generators

**Data**
- [ ] Serialise dates, enums and decimals to JSON and back
- [ ] Write and validate a JSON Schema
- [ ] Validate API responses with Pydantic: aliases, `AliasPath`, `TypeAdapter`, validators, discriminated unions
- [ ] Read CSV, YAML (`safe_load`) and namespaced XML (`defusedxml`)

**Auth and secrets**
- [ ] Use API keys, bearer tokens and Basic auth; write an `httpx.Auth` class
- [ ] Explain the OAuth authorization-code flow with PKCE, scopes and refresh tokens
- [ ] Run a Google OAuth flow with `google-auth-oauthlib` and call a Google API
- [ ] Keep secrets in `keyring` or a secret manager, and out of logs (`SecretStr`)

**Webhooks, limits, caching, testing**
- [ ] Receive a webhook and verify its HMAC signature with `hmac.compare_digest`
- [ ] Limit concurrency and request rate in async code
- [ ] Use ETags, `requests-cache`, and a TTL disk cache
- [ ] Test HTTP code with respx and pytest-httpx, including retries and pagination

---

## Exercise Solutions

Try every exercise yourself first. Look here only after a real attempt (at least 20 minutes).

**Lesson 1, Exercise 2**
```python
from urllib.parse import urlencode, urljoin


def build_url(base: str, path: str, **params) -> str:
    url = urljoin(base.rstrip("/") + "/", path.lstrip("/"))
    return f"{url}?{urlencode(params)}" if params else url


print(build_url("https://geocoding-api.open-meteo.com/v1", "search", name="São Paulo", count=1))
# https://geocoding-api.open-meteo.com/v1/search?name=S%C3%A3o+Paulo&count=1
```

**Lesson 3, Exercise 1**

| Action | Method | Retry a timeout blindly? |
|---|---|---|
| List today's events | `GET` | Yes |
| Send an email | `POST` | No: check "sent" first or use an idempotency key |
| Mark task 7 done | `PATCH`/`PUT` with `{"done": true}` | Yes (setting a value is repeatable) |
| Rename a file | `PATCH` with the new name | Usually yes (same final state) |
| Delete a draft | `DELETE` | Yes (a 404 on retry means it's already gone) |

**Lesson 7, Exercise 3**
```python
import time

import httpx


class RateLimitExhausted(Exception):
    def __init__(self, seconds_until_reset: float) -> None:
        super().__init__(f"Rate limit exhausted; resets in {seconds_until_reset:.0f}s")
        self.seconds_until_reset = seconds_until_reset


def check_github_budget(response: httpx.Response) -> None:
    if response.headers.get("x-ratelimit-remaining") == "0":
        reset = float(response.headers.get("x-ratelimit-reset", time.time()))
        raise RateLimitExhausted(max(0.0, reset - time.time()))

# Call check_github_budget(response) in get_with_retries right after each response arrives.
```

**Lesson 8, Exercise 1**
```python
import httpx

with httpx.Client(base_url="https://api.github.com", timeout=10) as client:
    items = paginate(client, "/repos/psf/requests/issues", {"state": "open", "per_page": 100})
    print(sum(1 for item in items if "pull_request" not in item))
```

**Lesson 8, Exercise 3**
```python
def fake_fetch(cursor: str | None) -> dict:
    start = int(cursor) if cursor else 1
    numbers = list(range(start, min(start + 10, 26)))
    next_start = start + 10
    return {"results": numbers, "next_cursor": str(next_start) if next_start <= 25 else None}


assert list(paginate_cursor(fake_fetch)) == list(range(1, 26))
```

**Lesson 11, Exercise 1**
```python
from datetime import datetime

from pydantic import BaseModel, field_validator


class User(BaseModel):
    login: str
    name: str | None = None
    public_repos: int
    followers: int
    created_at: datetime
    blog: str | None = None

    @field_validator("blog", mode="before")
    @classmethod
    def empty_to_none(cls, v):
        return v or None
```

**Lesson 11, Exercise 3**
```python
from pydantic import BaseModel, ValidationError


def parse_or_report[M: BaseModel](model: type[M], items: list[dict]) -> tuple[list[M], list[str]]:
    valid: list[M] = []
    errors: list[str] = []
    for index, item in enumerate(items):
        try:
            valid.append(model.model_validate(item))
        except ValidationError as e:
            errors.append(f"item {index}: {e.error_count()} error(s): {e.errors()[0]['msg']}")
    return valid, errors
```
(`def f[M: BaseModel](...)` is Python 3.12's type-parameter syntax: `M` is "some subclass of BaseModel".)

**Lesson 16, Exercise 1**
```python
import os

import keyring


def get_secret(name: str, service: str = "work-organizer") -> str:
    value = os.getenv(name.upper().replace("-", "_")) or keyring.get_password(service, name)
    if not value:
        raise RuntimeError(f"Secret {name!r} not found. Run: keyring set {service} {name}")
    return value
```

**Lesson 17, Exercise 3**
```python
import hashlib
import hmac
import time


def verify_stripe_style(body: bytes, header: str, secret: str, tolerance: int = 300) -> bool:
    try:
        parts = dict(item.split("=", 1) for item in header.split(","))
        timestamp = int(parts["t"])
        signature = parts["v1"]
    except (KeyError, ValueError):
        return False
    if abs(time.time() - timestamp) > tolerance:
        return False                                   # too old: possible replay
    signed = f"{timestamp}.".encode() + body
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

**Lesson 20, Exercise 1**
```python
import httpx
import pytest
import respx

URL = "https://api.example.test/items"


@respx.mock
def test_retries_then_succeeds(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)          # no real waiting
    respx.get(URL).mock(side_effect=[httpx.Response(503), httpx.Response(200, json={"ok": True})])
    with httpx.Client() as client:
        assert get_with_retries(client, URL).json() == {"ok": True}


@respx.mock
def test_404_not_retried():
    route = respx.get(URL).mock(return_value=httpx.Response(404))
    with httpx.Client() as client, pytest.raises(httpx.HTTPStatusError):
        get_with_retries(client, URL)
    assert route.call_count == 1
```
(`api.example.test` is a reserved name that can never be a real site, which makes it ideal for fakes.)

**Capstone: the `request()` retry loop**
```python
for attempt in range(retries + 1):
    is_last = attempt == retries
    try:
        response = self._client.request(method, url, **kwargs)
    except httpx.TransportError as exc:
        if is_last:
            raise ApiError(f"Network error calling {url}: {exc}") from exc
        self._sleep(self._backoff(attempt))
        continue
    if response.status_code in RETRYABLE_STATUS and not is_last:
        wait = parse_retry_after(response.headers.get("Retry-After"))
        self._sleep(wait if wait is not None else self._backoff(attempt))
        continue
    self._raise_for_status(response)
    return response
```

---

## Recommended Resources

| Resource | Type | Best for |
|---|---|---|
| MDN Web Docs: "HTTP" (developer.mozilla.org) | Reference | Methods, headers, status codes, caching |
| *HTTP: The Definitive Guide* (Gourley & Totty) | Book | Deep understanding of HTTP |
| httpx docs (python-httpx.org) | Official docs | Clients, timeouts, transports, auth |
| tenacity docs (tenacity.readthedocs.io) | Official docs | Retry strategies |
| Pydantic docs (docs.pydantic.dev) | Official docs | Models, validators, aliases, JSON Schema |
| json-schema.org "Understanding JSON Schema" | Free book | Writing schemas |
| oauth.com "OAuth 2.0 Simplified" (Aaron Parecki) | Free book/site | OAuth flows and PKCE explained clearly |
| RFC 6749 (OAuth 2.0), RFC 7636 (PKCE), RFC 9700 (OAuth security BCP) | Standards | The authoritative sources |
| Google Identity: "OAuth 2.0 for Mobile & Desktop Apps" | Official docs | Google-specific details |
| GitHub REST API docs (docs.github.com/rest) | Official docs | Pagination, rate limits, webhooks |
| Open-Meteo docs (open-meteo.com/en/docs) | Official docs | Weather variables and parameters |
| respx docs (lundberg.github.io/respx) | Official docs | Mocking httpx |
| public-apis list (github.com/public-apis/public-apis) | List | Free APIs to practise with |

**Next:** Section 3 — AI Models and Tool Calling (your first model API call, then giving the model the tools you built in this capstone).
