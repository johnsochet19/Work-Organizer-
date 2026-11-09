"""Long-term memory, notes, and full-text search over your own documents."""
from __future__ import annotations

import os
import re

from .store import Store, fts_query, utcnow

DOC_EXTENSIONS = {".txt", ".md", ".markdown", ".rst", ".csv", ".json", ".html", ".htm", ".org", ".log", ".py"}
CHUNK_CHARS = 1200
MAX_FILE_BYTES = 2_000_000


class Knowledge:
    def __init__(self, store: Store):
        self.store = store

    # ---------- memories: short facts about you, shown to the assistant every time ----------
    def remember(self, fact: str) -> dict:
        fact = (fact or "").strip()
        if not fact:
            raise ValueError("Nothing to remember.")
        with self.store.conn() as c:
            cur = c.execute("INSERT INTO memories(fact, created_at) VALUES(?,?)", (fact, utcnow()))
            mid = cur.lastrowid
        return {"id": mid, "fact": fact}

    def memories(self, query: str | None = None, limit: int = 100) -> list[dict]:
        with self.store.conn() as c:
            rows = [dict(r) for r in c.execute("SELECT * FROM memories ORDER BY id").fetchall()]
        if query:
            words = set(re.findall(r"\w+", query.lower()))
            rows = [r for r in rows if words & set(re.findall(r"\w+", r["fact"].lower()))]
        return rows[-limit:]

    def forget(self, memory_id: int) -> dict:
        with self.store.conn() as c:
            row = c.execute("SELECT * FROM memories WHERE id=?", (int(memory_id),)).fetchone()
            if not row:
                raise ValueError(f"There's no memory with id {memory_id}.")
            c.execute("DELETE FROM memories WHERE id=?", (int(memory_id),))
        return dict(row)

    # ---------- notes ----------
    def add_note(self, title: str, body: str) -> dict:
        title, body = (title or "").strip(), (body or "").strip()
        if not (title or body):
            raise ValueError("A note needs a title or some text.")
        with self.store.conn() as c:
            cur = c.execute("INSERT INTO notes(title, body, created_at) VALUES(?,?,?)",
                            (title or body[:60], body, utcnow()))
        return {"id": cur.lastrowid, "title": title or body[:60]}

    def search_notes(self, query: str, limit: int = 8) -> list[dict]:
        q = fts_query(query)
        if not q:
            return self.recent_notes(limit)
        with self.store.conn() as c:
            rows = c.execute("SELECT rowid AS id, title, body, created_at FROM notes WHERE notes MATCH ? "
                             "ORDER BY bm25(notes) LIMIT ?", (q, limit)).fetchall()
        return [dict(r) for r in rows]

    def recent_notes(self, limit: int = 8) -> list[dict]:
        with self.store.conn() as c:
            rows = c.execute("SELECT rowid AS id, title, body, created_at FROM notes ORDER BY rowid DESC LIMIT ?",
                             (limit,)).fetchall()
        return [dict(r) for r in rows]

    # ---------- documents ----------
    def index_folder(self, folder: str) -> dict:
        """(Re)index text files under `folder`. Only changed files are re-read."""
        folder = os.path.abspath(os.path.expanduser(folder))
        if not os.path.isdir(folder):
            raise ValueError(f"{folder} is not a folder.")
        seen, added, skipped = set(), 0, 0
        with self.store.conn() as c:
            known = {r["path"]: r["mtime"] for r in c.execute("SELECT * FROM doc_files")}
        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__")]
            for name in files:
                path = os.path.join(root, name)
                if os.path.splitext(name)[1].lower() not in DOC_EXTENSIONS:
                    continue
                try:
                    st = os.stat(path)
                except OSError:
                    continue
                if st.st_size > MAX_FILE_BYTES:
                    skipped += 1
                    continue
                seen.add(path)
                if known.get(path) == st.st_mtime:
                    continue
                with open(path, encoding="utf-8", errors="replace") as f:
                    text = f.read()
                if name.lower().endswith((".html", ".htm")):
                    from .web import html_to_text
                    text = html_to_text(text)
                with self.store.conn() as c:
                    c.execute("DELETE FROM doc_chunks WHERE path=?", (path,))
                    for i, chunk in enumerate(chunk_text(text)):
                        c.execute("INSERT INTO doc_chunks(path, chunk_no, body) VALUES(?,?,?)", (path, i, chunk))
                    c.execute("INSERT INTO doc_files(path, mtime) VALUES(?,?) "
                              "ON CONFLICT(path) DO UPDATE SET mtime=excluded.mtime", (path, st.st_mtime))
                added += 1
        removed = 0
        with self.store.conn() as c:
            for path in set(known) - seen:
                if path.startswith(folder + os.sep):
                    c.execute("DELETE FROM doc_chunks WHERE path=?", (path,))
                    c.execute("DELETE FROM doc_files WHERE path=?", (path,))
                    removed += 1
            total = c.execute("SELECT COUNT(*) AS n FROM doc_files").fetchone()["n"]
        return {"indexed_or_updated": added, "removed": removed, "too_big": skipped, "total_files": total}

    def search_documents(self, query: str, limit: int = 6) -> list[dict]:
        q = fts_query(query)
        if not q:
            return []
        with self.store.conn() as c:
            rows = c.execute("SELECT path, chunk_no, body FROM doc_chunks WHERE doc_chunks MATCH ? "
                             "ORDER BY bm25(doc_chunks) LIMIT ?", (q, limit)).fetchall()
        return [dict(r) for r in rows]


def chunk_text(text: str, size: int = CHUNK_CHARS) -> list[str]:
    """Split on blank lines, then pack paragraphs into chunks of about `size` characters."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        while len(p) > size:
            if cur:
                chunks.append(cur)
                cur = ""
            chunks.append(p[:size])
            p = p[size:]
        if len(cur) + len(p) + 2 > size and cur:
            chunks.append(cur)
            cur = p
        else:
            cur = f"{cur}\n\n{p}" if cur else p
    if cur:
        chunks.append(cur)
    return chunks
