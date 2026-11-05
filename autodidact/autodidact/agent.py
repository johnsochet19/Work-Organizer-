"""The research loop. Each cycle:

  1. Pick the most valuable topic from the frontier (or invent one from what it knows).
  2. Choose sources with a multi-armed bandit (UCB1): favour sources that have taught it
     the most, but keep trying under-used ones, including APIs it discovered itself.
  3. Read, index, and extract concepts. Reward each source by how much NEW it learned.
  4. Spawn follow-up topics from the concepts it just met, weighted by how strongly they
     connect to the current topic and to its mission.
  5. Every few cycles: tune its own settings, retire useless sources, and go looking for
     new APIs to learn from.
"""
from __future__ import annotations

import math
import time

from . import discover as D
from . import text as T
from .brain import Brain
from .net import Net
from .sources import BUILTIN, fetch


class Agent:
    def __init__(self, brain: Brain, net: Net, llm=None, log=print):
        self.brain, self.net, self.llm, self.say = brain, net, llm, log
        for name in BUILTIN:
            brain.register_source(name, "builtin")

    # ------------------------------------------------------------ choosing
    def choose_sources(self, k: int) -> list[dict]:
        srcs = self.brain.sources()
        total = sum(s["pulls"] for s in srcs) + 1
        c = self.brain.get("explore_weight")

        def ucb(s):
            if s["pulls"] == 0:
                return float("inf")
            return s["reward"] / s["pulls"] + c * math.sqrt(math.log(total) / s["pulls"])

        return sorted(srcs, key=ucb, reverse=True)[:k]

    def next_topic(self) -> dict | None:
        t = self.brain.pop_topic()
        if t:
            return t
        # frontier empty: become curious about well-connected concepts it hasn't studied
        for c in self.brain.top_concepts(5, unstudied=True):
            self.brain.push_topic(c["name"], 0.5, "curiosity: seen often, never studied")
        return self.brain.pop_topic()

    # ------------------------------------------------------------ one cycle
    def cycle(self) -> dict | None:
        topic_row = self.next_topic()
        if not topic_row:
            self.say("Nothing to research. Give me a topic: python -m autodidact learn \"<topic>\"")
            return None
        topic = topic_row["topic"]
        self.say(f"\n== Researching: {topic}  (priority {topic_row['priority']:.2f}; {topic_row['reason']})")
        n = self.brain.get("results_per_source")
        learned_phrases: list[tuple[str, float]] = []
        new_concepts: list[str] = []
        docs_added = 0
        per_source = {}
        for src in self.choose_sources(self.brain.get("sources_per_cycle")):
            try:
                items = fetch(self.net, src, topic, n)
                failed = not items
            except Exception as e:  # a broken source must never stop the loop
                items, failed = [], True
                self.brain.log("source_error", source=src["name"], error=repr(e))
            added = new = 0
            for it in items:
                res = self.brain.add_doc(it.url, it.title, it.text, src["name"], topic)
                if res:
                    added += 1
                    new += len(res["new_concepts"])
                    new_concepts += res["new_concepts"]
                    learned_phrases += res["phrases"]
            # reward = novelty: new documents and, above all, new concepts
            reward = min(1.0, 0.15 * added + 0.03 * new)
            self.brain.score_source(src["name"], reward, failed)
            per_source[src["name"]] = {"docs": added, "new_concepts": new, "reward": round(reward, 2)}
            self.say(f"   {src['name']:<14} +{added} docs, +{new} new concepts")
            docs_added += added

        if not any(v["docs"] for v in per_source.values()) and self.brain.search(topic, k=1) == []:
            # learned nothing and knows nothing: retry later at lower priority instead of dropping it
            if all(not v["docs"] and not v["new_concepts"] for v in per_source.values()) and self.net.requests_made:
                self.say("   no source answered. Check the internet connection, or try different wording.")
            pr = topic_row["priority"] * 0.5
            self.brain.db.execute("UPDATE frontier SET status=?, priority=? WHERE topic=?",
                                  ("pending" if pr > 0.1 else "done", pr, topic))
            self.brain.db.commit()
            self.brain.log("cycle", topic=topic, docs=0, new_concepts=0, sources=per_source,
                           spawned=[], note="", retry=pr > 0.1)
            return {"topic": topic, "docs": 0, "new_concepts": 0, "spawned": []}
        self.brain.mark_studied(topic)
        spawned = self.spawn_followups(topic, topic_row["priority"], learned_phrases)
        note = self.note(topic)
        self.brain.finish_topic(topic)
        self.brain.log("cycle", topic=topic, docs=docs_added, new_concepts=len(new_concepts),
                       sources=per_source, spawned=spawned, note=note)
        if note:
            self.say("   learned: " + note[:300])
        if spawned:
            self.say("   next up: " + ", ".join(spawned))

        cycles = self.brain.stats()["cycles"]
        if cycles % 5 == 0:
            self.self_tune()
        if cycles % self.brain.get("discover_every") == 0:
            self.extend()
        return {"topic": topic, "docs": docs_added, "new_concepts": len(new_concepts), "spawned": spawned}

    def spawn_followups(self, topic: str, parent_priority: float, phrases) -> list[str]:
        mission = set(T.content_tokens(self.brain.get("mission") or ""))
        topic_words = set(T.content_tokens(topic))
        related = dict(self.brain.related(topic, 30))
        # never queue a near-duplicate ("neural networks" after "neural network")
        seen = {_norm(r[0]) for r in self.brain.db.execute("SELECT topic FROM frontier")}
        topic_words = topic_words | {_norm(w) for w in topic_words}
        scored = {}
        for phrase, score in phrases:
            words = set(phrase.split())
            if _norm(phrase) in seen or {_norm(w) for w in words} <= topic_words or len(phrase) < 4:
                continue
            row = self.brain.db.execute("SELECT studied, docs FROM concepts WHERE name=?", (phrase,)).fetchone()
            if row and row["studied"]:
                continue
            seen_in = row["docs"] if row else 1
            s = (math.log1p(score) * 0.3 + math.log1p(seen_in) * 0.5 + 0.2 * related.get(phrase, 0)
                 + 0.6 * len(words & mission) + 0.3 * len(words & topic_words))
            scored[phrase] = max(scored.get(phrase, 0), s)
        uniq = {}
        for phrase, s in sorted(scored.items(), key=lambda kv: -kv[1]):
            uniq.setdefault(_norm(phrase), (phrase, s))
        best = list(uniq.values())[: self.brain.get("spawn_per_cycle")]
        top = best[0][1] if best else 1
        out = []
        for phrase, s in best:
            pr = round(parent_priority * 0.85 * (0.5 + 0.5 * s / top), 3)
            self.brain.push_topic(phrase, pr, f"came up while studying '{topic}'", parent=topic)
            out.append(phrase)
        return out

    def note(self, topic: str) -> str:
        hits = self.brain.search(topic, k=6)
        return " ".join(T.summarize(" ".join(h["text"] for h in hits), n=2, query=topic))

    # ------------------------------------------------------------ self-improvement
    def self_tune(self):
        """Adjust its own parameters from its track record."""
        b = self.brain
        changes = {}
        for s in b.sources():
            if s["pulls"] >= 6 and s["reward"] / s["pulls"] < b.get("min_source_reward"):
                b.disable_source(s["name"], f"avg reward {s['reward'] / s['pulls']:.2f} after {s['pulls']} tries")
                changes[f"retired:{s['name']}"] = True
        recent = [j for j in b.journal(40) if j["event"] == "cycle"][:5]
        if recent:
            avg_new = sum(j["detail"]["new_concepts"] for j in recent) / len(recent)
            n = b.get("results_per_source")
            if avg_new < 5 and n < 8:      # learning little: cast a wider net
                b.set("results_per_source", n + 1); changes["results_per_source"] = n + 1
                b.set("sources_per_cycle", min(6, b.get("sources_per_cycle") + 1))
            elif avg_new > 40 and n > 2:   # drinking from a firehose: go deeper, slower
                b.set("results_per_source", n - 1); changes["results_per_source"] = n - 1
            # explore more when the frontier is drying up, exploit more when it's rich
            ew = 1.6 if b.stats()["topics_queued"] < 5 else 0.9
            if ew != b.get("explore_weight"):
                b.set("explore_weight", ew); changes["explore_weight"] = ew
        b.log("self_tune", changes=changes)
        if changes:
            self.say(f"   [self-tune] {changes}")

    def extend(self, extra_candidates=None) -> list[str]:
        self.say("   [self-extend] looking for new free APIs to learn from...")
        added = D.discover(self.brain, self.net, self.llm, extra_candidates=extra_candidates)
        self.say(f"   [self-extend] added {len(added)} new source(s): {', '.join(added) or 'none this time'}")
        return added

    # ------------------------------------------------------------ running
    def run(self, cycles: int | None = None, interval: float = 0.0):
        done = 0
        while cycles is None or done < cycles:
            if self.cycle() is None:
                break
            done += 1
            if interval:
                time.sleep(interval)
        return done


def _norm(phrase: str) -> str:
    """Crude singular form so 'networks' and 'network' count as the same topic."""
    out = []
    for w in phrase.lower().split():
        if w.endswith("ies") and len(w) > 4:
            w = w[:-3] + "y"
        elif w.endswith("s") and not w.endswith("ss") and len(w) > 3:
            w = w[:-1]
        out.append(w)
    return " ".join(out)
