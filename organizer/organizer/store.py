"""Everything the organizer remembers, in one SQLite file.

Tasks, notes, long-term memories, your indexed documents, conversations,
actions waiting for your approval, an audit log of every tool it ran, and how
many tokens it has used.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks(
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT '',
    priority INTEGER NOT NULL DEFAULT 3,
    due TEXT,
    tags TEXT NOT NULL DEFAULT '',
    recur TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    created_at TEXT NOT NULL,
    completed_at TEXT,
    reminded_at TEXT
);
CREATE TABLE IF NOT EXISTS memories(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fact TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS notes USING fts5(title, body, created_at UNINDEXED);
CREATE VIRTUAL TABLE IF NOT EXISTS doc_chunks USING fts5(path UNINDEXED, chunk_no UNINDEXED, body);
CREATE TABLE IF NOT EXISTS doc_files(path TEXT PRIMARY KEY, mtime REAL NOT NULL);
CREATE TABLE IF NOT EXISTS messages(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS messages_conv ON messages(conversation, id);
CREATE TABLE IF NOT EXISTS pending_actions(
    id TEXT PRIMARY KEY,
    conversation TEXT NOT NULL,
    tool TEXT NOT NULL,
    args TEXT NOT NULL,
    summary TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    result TEXT,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    at TEXT NOT NULL,
    conversation TEXT,
    tool TEXT NOT NULL,
    args TEXT NOT NULL,
    risk TEXT NOT NULL,
    decision TEXT NOT NULL,
    ok INTEGER,
    result TEXT
);
CREATE TABLE IF NOT EXISTS usage(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    at TEXT NOT NULL,
    day TEXT NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS kv(key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id() -> str:
    return uuid.uuid4().hex[:6]


def fts_query(text: str) -> str:
    """Turn free text into a safe FTS5 query: each word quoted, any word may match."""
    words = re.findall(r"\w+", text.lower())
    return " OR ".join(f'"{w}"' for w in words[:20])


class Store:
    def __init__(self, path: str):
        self.path = path
        if path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with self.conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def conn(self):
        # A short-lived connection per operation keeps this safe to use from the
        # web server, the Telegram bot and the scheduler at the same time.
        c = sqlite3.connect(self.path, timeout=30)
        c.row_factory = sqlite3.Row
        try:
            c.execute("PRAGMA journal_mode=WAL")
            yield c
            c.commit()
        finally:
            c.close()

    # ---------- key/value ----------
    def get(self, key: str, default: str | None = None) -> str | None:
        with self.conn() as c:
            row = c.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
        return row["value"] if row else default

    def set(self, key: str, value: str) -> None:
        with self.conn() as c:
            c.execute("INSERT INTO kv(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                      (key, value))

    # ---------- conversations ----------
    def add_message(self, conversation: str, role: str, content) -> None:
        with self.conn() as c:
            c.execute("INSERT INTO messages(conversation,role,content,created_at) VALUES(?,?,?,?)",
                      (conversation, role, json.dumps(content), utcnow()))

    def history(self, conversation: str, limit: int = 40) -> list[dict]:
        """The most recent messages, trimmed so the history starts cleanly.

        Claude needs the history to start with a plain user message (not a tool
        result whose tool call was cut off), so the start moves forward until it does.
        """
        with self.conn() as c:
            rows = c.execute("SELECT role, content FROM messages WHERE conversation=? ORDER BY id DESC LIMIT ?",
                             (conversation, limit)).fetchall()
        msgs = [{"role": r["role"], "content": json.loads(r["content"])} for r in reversed(rows)]
        while msgs and not _is_plain_user(msgs[0]):
            msgs.pop(0)
        return msgs

    def clear_conversation(self, conversation: str) -> None:
        with self.conn() as c:
            c.execute("DELETE FROM messages WHERE conversation=?", (conversation,))

    # ---------- pending actions (waiting for your approval) ----------
    def add_pending(self, conversation: str, tool: str, args: dict, summary: str) -> str:
        pid = new_id()
        with self.conn() as c:
            c.execute("INSERT INTO pending_actions(id,conversation,tool,args,summary,created_at) VALUES(?,?,?,?,?,?)",
                      (pid, conversation, tool, json.dumps(args), summary, utcnow()))
        return pid

    def get_pending(self, pid: str) -> dict | None:
        with self.conn() as c:
            row = c.execute("SELECT * FROM pending_actions WHERE id=?", (pid,)).fetchone()
        return _pending(row) if row else None

    def list_pending(self, conversation: str | None = None) -> list[dict]:
        sql = "SELECT * FROM pending_actions WHERE status='pending'"
        params: tuple = ()
        if conversation:
            sql += " AND conversation=?"
            params = (conversation,)
        with self.conn() as c:
            rows = c.execute(sql + " ORDER BY created_at", params).fetchall()
        return [_pending(r) for r in rows]

    def resolve_pending(self, pid: str, status: str, result: str = "") -> None:
        with self.conn() as c:
            c.execute("UPDATE pending_actions SET status=?, result=? WHERE id=?", (status, result, pid))

    # ---------- audit log ----------
    def audit(self, conversation: str | None, tool: str, args: dict, risk: str, decision: str,
              ok: bool | None = None, result: str = "") -> None:
        with self.conn() as c:
            c.execute("INSERT INTO audit(at,conversation,tool,args,risk,decision,ok,result) VALUES(?,?,?,?,?,?,?,?)",
                      (utcnow(), conversation, tool, json.dumps(args)[:2000], risk, decision,
                       None if ok is None else int(ok), result[:2000]))

    def recent_audit(self, limit: int = 30) -> list[dict]:
        with self.conn() as c:
            rows = c.execute("SELECT * FROM audit ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    # ---------- usage ----------
    def record_usage(self, model: str, input_tokens: int, output_tokens: int, day: str) -> None:
        with self.conn() as c:
            c.execute("INSERT INTO usage(at,day,model,input_tokens,output_tokens) VALUES(?,?,?,?,?)",
                      (utcnow(), day, model, input_tokens, output_tokens))

    def tokens_used(self, day: str) -> int:
        with self.conn() as c:
            row = c.execute("SELECT COALESCE(SUM(input_tokens+output_tokens),0) AS n FROM usage WHERE day=?",
                            (day,)).fetchone()
        return int(row["n"])


def _is_plain_user(msg: dict) -> bool:
    if msg["role"] != "user":
        return False
    content = msg["content"]
    if isinstance(content, str):
        return True
    return not any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content)


def _pending(row) -> dict:
    d = dict(row)
    d["args"] = json.loads(d["args"])
    return d
