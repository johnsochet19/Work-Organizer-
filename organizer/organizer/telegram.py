"""Talk to the assistant from your phone with a Telegram bot.

1. In Telegram, message @BotFather, send /newbot, and copy the token it gives you.
2. Message @userinfobot to get your numeric user id.
3. Set TELEGRAM_BOT_TOKEN and TELEGRAM_USER_ID, then run `python -m organizer run`.

The bot only ever answers your user id; messages from anyone else are ignored.
Risky actions arrive with Approve / Decline buttons.
"""
from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request

from .agent import Agent


class Telegram:
    def __init__(self, agent: Agent):
        self.agent = agent
        s = agent.ctx.settings
        self.token = s.telegram_token
        self.user_id = str(s.telegram_user_id)
        self.offset = int(agent.ctx.store.get("telegram_offset", "0") or 0)
        self.lock = threading.Lock()

    def api(self, method: str, timeout: float = 70, **params) -> dict:
        req = urllib.request.Request(f"https://api.telegram.org/bot{self.token}/{method}",
                                     data=json.dumps(params).encode(), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            try:
                return json.loads(e.read().decode())
            except Exception:
                return {"ok": False, "description": str(e)}
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            return {"ok": False, "description": str(e)}

    def send(self, text: str, chat_id: str | None = None, buttons: list | None = None) -> None:
        chat_id = chat_id or self.user_id
        for i in range(0, max(len(text), 1), 4000):   # Telegram's message limit is 4096 characters
            params = {"chat_id": chat_id, "text": text[i:i + 4000] or "(empty)"}
            if buttons and i + 4000 >= len(text):
                params["reply_markup"] = {"inline_keyboard": buttons}
            self.api("sendMessage", timeout=30, **params)

    def _send_pending(self, chat_id: str, pending: list[dict]) -> None:
        for p in pending:
            self.send(f"Approve this?\n\n{p['summary']}", chat_id,
                      [[{"text": "✅ Approve", "callback_data": f"ok:{p['id']}"},
                        {"text": "✖ Decline", "callback_data": f"no:{p['id']}"}]])

    def handle_update(self, u: dict) -> None:
        if "callback_query" in u:
            cq = u["callback_query"]
            if str(cq.get("from", {}).get("id")) != self.user_id:
                return
            verdict, _, pid = (cq.get("data") or "").partition(":")
            with self.lock:
                result = self.agent.resolve(pid, verdict == "ok")
            self.api("answerCallbackQuery", timeout=30, callback_query_id=cq["id"],
                     text="Approved" if verdict == "ok" else "Declined")
            msg = cq.get("message") or {}
            if msg:
                self.api("editMessageReplyMarkup", timeout=30, chat_id=msg["chat"]["id"],
                         message_id=msg["message_id"], reply_markup={"inline_keyboard": []})
            self.send(result, str(msg.get("chat", {}).get("id", self.user_id)))
            return
        msg = u.get("message") or {}
        if str(msg.get("from", {}).get("id")) != self.user_id or "text" not in msg:
            return
        chat_id = str(msg["chat"]["id"])
        text = msg["text"].strip()
        if text in ("/start", "/help"):
            return self.send("Hi! Tell me what you need: add tasks, plan your day, check email, look things up.\n"
                             "Shortcuts: /tasks /briefing /new (start a fresh conversation)", chat_id)
        if text == "/new":
            self.agent.ctx.store.clear_conversation(f"tg:{chat_id}")
            return self.send("Started a fresh conversation.", chat_id)
        if text == "/tasks":
            text = "list"
        if text == "/briefing":
            text = "briefing"
        self.api("sendChatAction", timeout=10, chat_id=chat_id, action="typing")
        with self.lock:
            if text in ("list", "briefing"):
                from . import offline
                reply = offline.handle(self.agent.ctx, text)
            else:
                reply = self.agent.chat(f"tg:{chat_id}", text)
        self.send(reply.text or "Done.", chat_id)
        self._send_pending(chat_id, reply.pending)

    def poll_forever(self) -> None:
        me = self.api("getMe", timeout=30)
        if not me.get("ok"):
            print(f"Telegram: couldn't connect ({me.get('description')}). Check TELEGRAM_BOT_TOKEN.", flush=True)
            return
        print(f"Telegram bot @{me['result'].get('username')} is listening (only to user {self.user_id}).", flush=True)
        while True:
            r = self.api("getUpdates", offset=self.offset, timeout=60,
                         allowed_updates=["message", "callback_query"])
            if not r.get("ok"):
                time.sleep(5)
                continue
            for u in r.get("result", []):
                self.offset = u["update_id"] + 1
                self.agent.ctx.store.set("telegram_offset", str(self.offset))
                try:
                    self.handle_update(u)
                except Exception as e:  # one bad message must not stop the bot
                    print(f"Telegram: error handling a message: {e}", flush=True)
