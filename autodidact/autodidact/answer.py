"""Answer questions from what the brain has learned, always citing where it came from."""
from __future__ import annotations

from collections import Counter

from . import text as T
from .brain import Brain


def ask(brain: Brain, question: str, llm=None, k: int = 8) -> dict:
    hits = brain.search(question, k=k)
    if not hits:
        return {"answer": "I haven't learned anything about that yet. Try: "
                          f"python -m autodidact learn \"{question}\"", "sources": [], "gap": True}
    sources = list(dict.fromkeys((h["title"], h["url"]) for h in hits))[:6]
    if llm is not None:
        context = "\n\n".join(f"[{i + 1}] {h['title']} ({h['url']}):\n{h['text']}" for i, h in enumerate(hits))
        reply = llm.complete(
            f"Question: {question}\n\nAnswer using ONLY these notes. Cite like [1]. "
            f"If the notes don't cover it, say what's missing.\n\n{context}",
            system="You are the voice of a self-taught research agent. Be accurate and concise.")
        if not reply.startswith("[llm error"):
            return {"answer": reply, "sources": [(h["title"], h["url"]) for h in hits], "gap": False}
    joined = " ".join(h["text"] for h in hits)
    summary = T.summarize(joined, n=4, query=question)
    covered = set(T.content_tokens(question)) & set(T.content_tokens(joined))
    gap = len(covered) < max(1, len(set(T.content_tokens(question))) // 2)
    return {"answer": " ".join(summary), "sources": sources, "gap": gap}


def report(brain: Brain, top: int = 25) -> str:
    """A Markdown snapshot of the brain: what it knows, how it's connected, where it learned it."""
    s = brain.stats()
    lines = ["# What I've learned", "",
             f"{s['documents']} documents · {s['concepts']} concepts · {s['connections']} connections · "
             f"{s['topics_done']} topics studied · {s['sources_active']} sources "
             f"({s['sources_self_discovered']} discovered by me)", ""]
    mission = brain.get("mission")
    if mission:
        lines += [f"**Mission:** {mission}", ""]
    lines += ["## Core concepts", ""]
    for c in brain.top_concepts(top):
        rel = ", ".join(r for r, _ in brain.related(c["name"], 5))
        lines.append(f"- **{c['name']}** (in {c['docs']} docs){' — related: ' + rel if rel else ''}")
    lines += ["", "## Topic notes", ""]
    for j in reversed([j for j in brain.journal(500) if j["event"] == "cycle"][:top]):
        d = j["detail"]
        if d.get("note"):
            lines.append(f"### {d['topic']}\n{d['note']}\n")
    lines += ["## Sources by usefulness", "", "| source | kind | tries | avg reward |", "|---|---|---|---|"]
    for src in brain.sources(enabled_only=False):
        avg = src["reward"] / src["pulls"] if src["pulls"] else 0
        flag = "" if src["enabled"] else " (retired)"
        lines.append(f"| {src['name']}{flag} | {src['kind']} | {src['pulls']} | {avg:.2f} |")
    by_source = Counter(r[0] for r in brain.db.execute("SELECT source FROM docs"))
    lines += ["", "Documents per source: " + ", ".join(f"{k} {v}" for k, v in by_source.most_common())]
    lines += ["", "## Up next", ""] + [f"- {t['topic']} ({t['priority']:.2f}) — {t['reason']}"
                                       for t in brain.pending_topics(15)]
    return "\n".join(lines) + "\n"
