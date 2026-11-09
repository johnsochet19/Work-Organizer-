"""A small web app: chat with the assistant, see your tasks, approve or decline actions.

Runs on your own computer at http://127.0.0.1:8765 by default. If you open it to
other machines (ORGANIZER_WEB_HOST=0.0.0.0), an ORGANIZER_WEB_TOKEN is required:
open http://<host>:8765/?token=<your token> once and the browser remembers it.
"""
from __future__ import annotations

import hmac
import json
import os
import threading
import urllib.parse
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .agent import Agent
from .tasks import TaskError, format_task

CONVERSATION = "web"
STATIC = os.path.join(os.path.dirname(__file__), "static")


class App:
    def __init__(self, agent: Agent):
        self.agent = agent
        self.lock = threading.Lock()   # one assistant turn at a time keeps the history in order

    @property
    def settings(self):
        return self.agent.ctx.settings

    def state(self) -> dict:
        ctx = self.agent.ctx
        today = ctx.settings.now().date()
        tasks = ctx.tasks.list(limit=200)
        return {
            "tasks": [{**t, "label": format_task(t, today),
                       "overdue": bool(t["due"] and t["due"][:10] < today.isoformat()),
                       "today": bool(t["due"] and t["due"][:10] == today.isoformat())} for t in tasks],
            "pending": ctx.store.list_pending(),
            "briefing": ctx.store.get("last_briefing", ""),
            "llm": ctx.settings.has_llm,
            "history": self.history(),
        }

    def history(self, limit: int = 30) -> list[dict]:
        out = []
        for m in self.agent.ctx.store.history(CONVERSATION, limit=200):
            c = m["content"]
            if isinstance(c, str):
                if not c.startswith("[Note from the app"):
                    out.append({"role": m["role"], "text": c})
            else:
                text = "".join(b.get("text", "") for b in c if isinstance(b, dict) and b.get("type") == "text")
                if text and text != "Noted.":
                    out.append({"role": m["role"], "text": text})
        return out[-limit:]

    def chat(self, message: str) -> dict:
        with self.lock:
            r = self.agent.chat(CONVERSATION, message)
        return {"reply": r.text, "pending": r.pending, "actions": r.actions}

    def resolve(self, pid: str, approve: bool) -> dict:
        with self.lock:
            return {"result": self.agent.resolve(pid, approve)}


def make_handler(app: App):
    token = app.settings.web_token

    class Handler(BaseHTTPRequestHandler):
        server_version = "WorkOrganizer"

        def log_message(self, fmt, *args):  # quiet
            pass

        # ---------- auth ----------
        def _authed(self) -> bool:
            if not token:
                return True
            auth = self.headers.get("Authorization", "")
            if auth.startswith("Bearer ") and hmac.compare_digest(auth[7:], token):
                return True
            jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
            c = jar.get("organizer_token")
            return bool(c and hmac.compare_digest(c.value, token))

        def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, obj):
            self._send(code, json.dumps(obj, default=str).encode(), "application/json")

        # ---------- routes ----------
        def do_GET(self):
            url = urllib.parse.urlsplit(self.path)
            q = urllib.parse.parse_qs(url.query)
            if url.path == "/" and token and q.get("token") and hmac.compare_digest(q["token"][0], token):
                cookie = f"organizer_token={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=31536000"
                return self._send(302, b"", "text/plain", {"Location": "/", "Set-Cookie": cookie})
            if url.path == "/health":
                return self._json(200, {"ok": True})
            if not self._authed():
                return self._send(401, b"Not signed in. Open this page with ?token=YOUR_TOKEN once.",
                                  "text/plain; charset=utf-8")
            if url.path == "/":
                with open(os.path.join(STATIC, "index.html"), "rb") as f:
                    return self._send(200, f.read(), "text/html; charset=utf-8",
                                      {"Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; "
                                       "style-src 'self' 'unsafe-inline'; connect-src 'self'"})
            if url.path == "/api/state":
                return self._json(200, app.state())
            return self._json(404, {"error": "not found"})

        def do_POST(self):
            if not self._authed():
                return self._json(401, {"error": "not signed in"})
            # Browsers can't add this header to a cross-site form, so it blocks CSRF.
            if self.headers.get("X-Organizer") != "1":
                return self._json(403, {"error": "missing X-Organizer header"})
            try:
                length = min(int(self.headers.get("Content-Length", 0)), 100_000)
                data = json.loads(self.rfile.read(length) or b"{}")
            except (ValueError, json.JSONDecodeError):
                return self._json(400, {"error": "bad JSON"})
            try:
                return self._route_post(urllib.parse.urlsplit(self.path).path, data)
            except TaskError as e:
                return self._json(400, {"error": str(e)})
            except Exception as e:  # never leave the browser hanging
                return self._json(500, {"error": f"{type(e).__name__}: {e}"})

        def _route_post(self, path: str, data: dict):
            if path == "/api/chat":
                msg = str(data.get("message", ""))[:8000]
                return self._json(200, app.chat(msg))
            if path == "/api/approve":
                return self._json(200, app.resolve(str(data.get("id", "")), bool(data.get("approve"))))
            if path == "/api/complete":
                done, _ = app.agent.ctx.tasks.complete(str(data.get("id", "")))
                return self._json(200, {"result": format_task(done)})
            if path == "/api/clear":
                app.agent.ctx.store.clear_conversation(CONVERSATION)
                return self._json(200, {"ok": True})
            return self._json(404, {"error": "not found"})

    return Handler


def serve(agent: Agent, block: bool = True) -> ThreadingHTTPServer:
    s = agent.ctx.settings
    if s.web_host not in ("127.0.0.1", "localhost", "::1") and not s.web_token:
        raise SystemExit("Refusing to open the web app to other machines without ORGANIZER_WEB_TOKEN. "
                         "Set one (any long random text) and try again.")
    app = App(agent)
    httpd = ThreadingHTTPServer((s.web_host, s.web_port), make_handler(app))
    url = f"http://{'127.0.0.1' if s.web_host in ('0.0.0.0', '::') else s.web_host}:{httpd.server_address[1]}/"
    print(f"Web app running at {url}" + ("?token=<your token>" if s.web_token else ""), flush=True)
    if block:
        httpd.serve_forever()
    else:
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd
