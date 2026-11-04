"""Command line.

  python -m autodidact learn "machine learning" --cycles 10
  python -m autodidact run --forever --interval 60
  python -m autodidact ask "what is backpropagation?"
  python -m autodidact status | topics | sources | journal | discover | report
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import answer
from .agent import Agent
from .brain import Brain
from .llm import from_env
from .net import Net


def build(args) -> Agent:
    os.makedirs(args.home, exist_ok=True)
    brain = Brain(os.path.join(args.home, "brain.db"))
    net = Net(cache_dir=os.path.join(args.home, "cache"), min_interval=args.politeness)
    return Agent(brain, net, llm=from_env())


def main(argv=None):
    p = argparse.ArgumentParser(prog="autodidact", description="A research agent that teaches itself from the web.")
    p.add_argument("--home", default=os.environ.get("AUTODIDACT_HOME", "autodidact_data"),
                   help="where the brain and cache live (default ./autodidact_data)")
    p.add_argument("--politeness", type=float, default=1.0, help="seconds between hits to the same site")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("learn", help="add a topic (and optionally set the mission), then research")
    s.add_argument("topic")
    s.add_argument("--cycles", type=int, default=5)
    s.add_argument("--mission", action="store_true", help="make this topic its long-term focus")

    s = sub.add_parser("run", help="keep researching whatever it finds most interesting")
    s.add_argument("--cycles", type=int, default=10)
    s.add_argument("--forever", action="store_true")
    s.add_argument("--interval", type=float, default=0, help="seconds to rest between cycles")

    s = sub.add_parser("ask", help="answer a question from what it has learned")
    s.add_argument("question")
    s.add_argument("--learn", action="store_true", help="if it doesn't know, go research it first")

    sub.add_parser("status")
    sub.add_parser("topics", help="the research queue")
    sub.add_parser("sources", help="every source and its track record")
    s = sub.add_parser("journal", help="what it has been doing")
    s.add_argument("-n", type=int, default=15)
    s = sub.add_parser("discover", help="look for new free APIs to learn from right now")
    s.add_argument("--candidates", help="JSON file of extra APIs: [{name, link, description, category}]")
    s = sub.add_parser("report", help="write a Markdown report of everything it knows")
    s.add_argument("-o", "--out", default="-")

    args = p.parse_args(argv)
    agent = build(args)
    b = agent.brain

    if args.cmd == "learn":
        if args.mission or not b.get("mission"):
            b.set("mission", args.topic)
        b.push_topic(args.topic, 1.0, "you asked")
        agent.run(args.cycles)
        print("\n" + json.dumps(b.stats(), indent=2))
    elif args.cmd == "run":
        try:
            agent.run(None if args.forever else args.cycles, args.interval)
        except KeyboardInterrupt:
            print("\nstopped; everything learned so far is saved.")
        print(json.dumps(b.stats(), indent=2))
    elif args.cmd == "ask":
        res = answer.ask(b, args.question, agent.llm)
        if res["gap"] and args.learn:
            print("I don't know enough yet. Researching...")
            b.push_topic(args.question, 1.0, "you asked a question I couldn't answer")
            agent.run(3)
            res = answer.ask(b, args.question, agent.llm)
        print("\n" + res["answer"] + "\n")
        for title, url in res["sources"]:
            print(f"  - {title}: {url}")
    elif args.cmd == "status":
        print(json.dumps({**b.stats(), "mission": b.get("mission"),
                          "settings": {k: b.get(k) for k in ("results_per_source", "sources_per_cycle",
                                                             "explore_weight", "discover_every")},
                          "llm": bool(agent.llm)}, indent=2))
    elif args.cmd == "topics":
        for t in b.pending_topics(30):
            print(f"{t['priority']:.2f}  {t['topic']:<40} {t['reason']}")
    elif args.cmd == "sources":
        for s in b.sources(enabled_only=False):
            avg = s["reward"] / s["pulls"] if s["pulls"] else 0
            state = "on " if s["enabled"] else "off"
            print(f"{state} {s['kind']:<8} {s['name']:<22} tries={s['pulls']:<4} avg_reward={avg:.2f}"
                  + (f"  {s['spec'].get('url', '')}" if s["kind"] == "learned" else ""))
    elif args.cmd == "journal":
        for j in reversed(b.journal(args.n)):
            print(j["event"], json.dumps(j["detail"])[:200])
    elif args.cmd == "discover":
        extra = json.load(open(args.candidates)) if args.candidates else None
        agent.extend(extra)
    elif args.cmd == "report":
        md = answer.report(b)
        if args.out == "-":
            sys.stdout.write(md)
        else:
            with open(args.out, "w") as f:
                f.write(md)
            print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
