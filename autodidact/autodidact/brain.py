"""The brain: one SQLite file holding everything the agent has learned.

  docs      - every page/record it has read, with source and topic
  chunks    - docs split into passages, indexed for BM25 search (postings)
  concepts  - key phrases it has seen, how often, and whether it has studied them
  edges     - concept co-occurrence graph (what relates to what)
  frontier  - the research queue: topics it wants to learn next, by priority
  sources   - every data source (built-in or self-discovered) with its track record
  journal   - a log of what it did and why
  settings  - self-tuned parameters
"""
from __future__ import annotations

import json
import math
import sqlite3
import time
from collections import Counter

from . import text as T

SCHEMA = """
CREATE TABLE IF NOT EXISTS docs(id INTEGER PRIMARY KEY, url TEXT UNIQUE, title TEXT, text TEXT,
  source TEXT, topic TEXT, fetched_at REAL);
CREATE TABLE IF NOT EXISTS chunks(id INTEGER PRIMARY KEY, doc_id INTEGER, text TEXT, n_terms INTEGER);
CREATE TABLE IF NOT EXISTS postings(term TEXT, chunk_id INTEGER, tf INTEGER);
CREATE INDEX IF NOT EXISTS postings_term ON postings(term);
CREATE TABLE IF NOT EXISTS concepts(name TEXT PRIMARY KEY, mentions INTEGER DEFAULT 0,
  docs INTEGER DEFAULT 0, score REAL DEFAULT 0, studied INTEGER DEFAULT 0, first_seen REAL, last_seen REAL);
CREATE TABLE IF NOT EXISTS edges(a TEXT, b TEXT, weight REAL, PRIMARY KEY(a, b));
CREATE TABLE IF NOT EXISTS frontier(topic TEXT PRIMARY KEY, priority REAL, reason TEXT,
  parent TEXT, status TEXT DEFAULT 'pending', added_at REAL, done_at REAL);
CREATE TABLE IF NOT EXISTS sources(name TEXT PRIMARY KEY, kind TEXT, spec TEXT, pulls INTEGER DEFAULT 0,
  reward REAL DEFAULT 0, failures INTEGER DEFAULT 0, enabled INTEGER DEFAULT 1, created_at REAL);
CREATE TABLE IF NOT EXISTS journal(id INTEGER PRIMARY KEY, ts REAL, event TEXT, detail TEXT);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
"""

DEFAULT_SETTINGS = {
    "results_per_source": 4,     # how many items to pull from each source per topic
    "sources_per_cycle": 3,      # how many sources to consult per research cycle
    "explore_weight": 1.2,       # UCB exploration constant for choosing sources
    "spawn_per_cycle": 4,        # how many follow-up topics each cycle may add
    "discover_every": 10,        # run API discovery every N cycles
    "min_source_reward": 0.15,   # sources whose average yield falls below this get retired
}


class Brain:
    def __init__(self, path: str = "brain.db"):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        for k, v in DEFAULT_SETTINGS.items():
            self.db.execute("INSERT OR IGNORE INTO settings VALUES(?,?)", (k, json.dumps(v)))
        self.db.commit()

    # -- settings / journal ----------------------------------------------
    def get(self, key):
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else DEFAULT_SETTINGS.get(key)

    def set(self, key, value):
        self.db.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, json.dumps(value)))
        self.db.commit()

    def log(self, event: str, **detail):
        self.db.execute("INSERT INTO journal(ts, event, detail) VALUES(?,?,?)",
                        (time.time(), event, json.dumps(detail, default=str)))
        self.db.commit()

    def journal(self, limit: int = 20):
        rows = self.db.execute("SELECT * FROM journal ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r, detail=json.loads(r["detail"])) for r in rows]

    # -- documents ---------------------------------------------------------
    def has_url(self, url: str) -> bool:
        return self.db.execute("SELECT 1 FROM docs WHERE url=?", (url,)).fetchone() is not None

    def add_doc(self, url: str, title: str, body: str, source: str, topic: str) -> dict:
        """Store a document, index it, and grow the concept graph.
        Returns {'new_concepts': [...], 'phrases': [...]} or {} if it was a duplicate/empty."""
        body = (body or "").strip()
        if len(body) < 80 or self.has_url(url):
            return {}
        now = time.time()
        cur = self.db.execute("INSERT INTO docs(url,title,text,source,topic,fetched_at) VALUES(?,?,?,?,?,?)",
                              (url, title, body, source, topic, now))
        doc_id = cur.lastrowid
        for chunk in _chunk(body):
            terms = Counter(T.content_tokens(chunk))
            c = self.db.execute("INSERT INTO chunks(doc_id,text,n_terms) VALUES(?,?,?)",
                                (doc_id, chunk, sum(terms.values())))
            self.db.executemany("INSERT INTO postings VALUES(?,?,?)",
                                [(t, c.lastrowid, n) for t, n in terms.items()])
        phrases = T.keyphrases(f"{title}. {title}. {body}", top=20)
        new = []
        for name, score in phrases:
            row = self.db.execute("SELECT mentions FROM concepts WHERE name=?", (name,)).fetchone()
            if row is None:
                new.append(name)
                self.db.execute("INSERT INTO concepts(name,mentions,docs,score,first_seen,last_seen) "
                                "VALUES(?,?,?,?,?,?)", (name, 1, 1, score, now, now))
            else:
                self.db.execute("UPDATE concepts SET mentions=mentions+1, docs=docs+1, "
                                "score=score+?, last_seen=? WHERE name=?", (score, now, name))
        names = [p for p, _ in phrases[:10]]
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                a2, b2 = sorted((a, b))
                self.db.execute("INSERT INTO edges VALUES(?,?,1) ON CONFLICT(a,b) DO UPDATE "
                                "SET weight=weight+1", (a2, b2))
        self.db.commit()
        return {"new_concepts": new, "phrases": phrases, "doc_id": doc_id}

    # -- search (BM25) ------------------------------------------------------
    def search(self, query: str, k: int = 8) -> list[dict]:
        q = list(dict.fromkeys(T.content_tokens(query)))
        if not q:
            return []
        n_chunks = self.db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0] or 1
        avg = self.db.execute("SELECT AVG(n_terms) FROM chunks").fetchone()[0] or 1
        scores: Counter = Counter()
        for term in q:
            rows = self.db.execute("SELECT p.chunk_id, p.tf, c.n_terms FROM postings p "
                                   "JOIN chunks c ON c.id=p.chunk_id WHERE p.term=?", (term,)).fetchall()
            if not rows:
                continue
            idf = math.log(1 + (n_chunks - len(rows) + 0.5) / (len(rows) + 0.5))
            for cid, tf, n in rows:
                scores[cid] += idf * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * n / avg))
        out = []
        for cid, s in scores.most_common(k):
            r = self.db.execute("SELECT c.text, d.title, d.url, d.source FROM chunks c "
                                "JOIN docs d ON d.id=c.doc_id WHERE c.id=?", (cid,)).fetchone()
            out.append({"score": round(s, 3), **dict(r)})
        return out

    # -- concepts / graph ----------------------------------------------------
    def related(self, concept: str, k: int = 10) -> list[tuple[str, float]]:
        rows = self.db.execute("SELECT CASE WHEN a=? THEN b ELSE a END AS other, weight FROM edges "
                               "WHERE a=? OR b=? ORDER BY weight DESC LIMIT ?",
                               (concept, concept, concept, k)).fetchall()
        return [(r[0], r[1]) for r in rows]

    def top_concepts(self, k: int = 20, unstudied: bool = False):
        where = "WHERE studied=0" if unstudied else ""
        return [dict(r) for r in self.db.execute(
            f"SELECT name, mentions, docs, score, studied FROM concepts {where} "
            "ORDER BY docs DESC, score DESC LIMIT ?", (k,))]

    def mark_studied(self, name: str):
        self.db.execute("UPDATE concepts SET studied=1 WHERE name=?", (name,))
        self.db.commit()

    # -- frontier (research queue) -------------------------------------------
    def push_topic(self, topic: str, priority: float, reason: str = "", parent: str | None = None):
        topic = topic.strip().lower()
        if not topic:
            return
        self.db.execute("INSERT INTO frontier(topic,priority,reason,parent,added_at) VALUES(?,?,?,?,?) "
                        "ON CONFLICT(topic) DO UPDATE SET priority=MAX(priority, excluded.priority) "
                        "WHERE status='pending'", (topic, priority, reason, parent, time.time()))
        self.db.commit()

    def pop_topic(self) -> dict | None:
        row = self.db.execute("SELECT * FROM frontier WHERE status='pending' "
                              "ORDER BY priority DESC, added_at LIMIT 1").fetchone()
        if row:
            self.db.execute("UPDATE frontier SET status='active' WHERE topic=?", (row["topic"],))
            self.db.commit()
        return dict(row) if row else None

    def finish_topic(self, topic: str):
        self.db.execute("UPDATE frontier SET status='done', done_at=? WHERE topic=?", (time.time(), topic))
        self.db.commit()

    def pending_topics(self, k: int = 20):
        return [dict(r) for r in self.db.execute(
            "SELECT topic, priority, reason FROM frontier WHERE status='pending' "
            "ORDER BY priority DESC LIMIT ?", (k,))]

    # -- sources -------------------------------------------------------------
    def register_source(self, name: str, kind: str, spec: dict | None = None):
        self.db.execute("INSERT OR IGNORE INTO sources(name,kind,spec,created_at) VALUES(?,?,?,?)",
                        (name, kind, json.dumps(spec or {}), time.time()))
        self.db.commit()

    def sources(self, enabled_only: bool = True):
        where = "WHERE enabled=1" if enabled_only else ""
        return [dict(r, spec=json.loads(r["spec"])) for r in
                self.db.execute(f"SELECT * FROM sources {where} ORDER BY reward DESC")]

    def score_source(self, name: str, reward: float, failed: bool = False):
        self.db.execute("UPDATE sources SET pulls=pulls+1, reward=reward+?, failures=failures+? "
                        "WHERE name=?", (reward, int(failed), name))
        self.db.commit()

    def disable_source(self, name: str, why: str):
        self.db.execute("UPDATE sources SET enabled=0 WHERE name=?", (name,))
        self.db.commit()
        self.log("source_retired", source=name, why=why)

    # -- stats ----------------------------------------------------------------
    def stats(self) -> dict:
        q = lambda sql: self.db.execute(sql).fetchone()[0]
        return {
            "documents": q("SELECT COUNT(*) FROM docs"),
            "passages": q("SELECT COUNT(*) FROM chunks"),
            "concepts": q("SELECT COUNT(*) FROM concepts"),
            "connections": q("SELECT COUNT(*) FROM edges"),
            "topics_done": q("SELECT COUNT(*) FROM frontier WHERE status='done'"),
            "topics_queued": q("SELECT COUNT(*) FROM frontier WHERE status='pending'"),
            "sources_active": q("SELECT COUNT(*) FROM sources WHERE enabled=1"),
            "sources_self_discovered": q("SELECT COUNT(*) FROM sources WHERE kind='learned' AND enabled=1"),
            "cycles": q("SELECT COUNT(*) FROM journal WHERE event='cycle'"),
        }


def _chunk(body: str, size: int = 700) -> list[str]:
    out, cur = [], ""
    for s in T.sentences(body) or [body]:
        if len(cur) + len(s) > size and cur:
            out.append(cur.strip())
            cur = ""
        cur += " " + s
    if cur.strip():
        out.append(cur.strip())
    return out
