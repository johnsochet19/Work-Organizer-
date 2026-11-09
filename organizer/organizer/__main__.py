"""Command line.

  python -m organizer chat                     talk to it in the terminal
  python -m organizer ask "plan my day"        one message, one answer
  python -m organizer run                      web app + Telegram bot + reminders, all together
  python -m organizer serve                    just the web app
  python -m organizer briefing                 print today's briefing
  python -m organizer index [folder]           make a documents folder searchable
  python -m organizer status                   what's switched on, usage, recent actions
  python -m organizer approvals                list, approve or decline waiting actions
"""
from __future__ import annotations

import argparse
import sys

from .agent import Agent
from .briefing import gather
from .config import Settings
from .tools import Context


def _ask_in_terminal(summary: str) -> bool:
    if not sys.stdin.isatty():
        print(f"\n[Needs approval, but there's no one to ask, so it was declined]\n{summary}\n")
        return False
    print("\n┌ Needs your approval ───────────────")
    for line in summary.splitlines():
        print("│ " + line)
    answer = input("└ Approve? [y/N] ").strip().lower()
    return answer in ("y", "yes")


def cmd_chat(agent: Agent, conversation: str) -> None:
    s = agent.ctx.settings
    mode = "" if s.has_llm else " (typed-command mode: set ANTHROPIC_API_KEY to talk in plain English)"
    print(f"Work Organizer{mode}. Type 'help' for commands, 'exit' to quit.\n")
    while True:
        try:
            text = input("you › ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if text.lower() in ("exit", "quit", "bye"):
            return
        if text.lower() == "/new":
            agent.ctx.store.clear_conversation(conversation)
            print("Started a fresh conversation.\n")
            continue
        if not text:
            continue
        reply = agent.chat(conversation, text, approve=_ask_in_terminal)
        print(f"\norganizer › {reply.text}\n")


def cmd_run(agent: Agent) -> None:
    import time

    from .scheduler import Scheduler
    from .webapp import serve
    s = agent.ctx.settings
    bot = None
    if s.has_telegram:
        from .telegram import Telegram
        bot = Telegram(agent)

    def notify(text: str) -> None:
        print(f"\n{text}\n", flush=True)
        if bot:
            bot.send(text)

    Scheduler(agent.ctx, notify).start()
    print(f"Reminders on; morning briefing at {s.briefing_time}.", flush=True)
    serve(agent, block=False)
    if bot:
        bot.poll_forever()
    else:
        print("Telegram is off (set TELEGRAM_BOT_TOKEN and TELEGRAM_USER_ID to turn it on).", flush=True)
        while True:
            time.sleep(3600)


def cmd_status(agent: Agent) -> None:
    ctx = agent.ctx
    s = ctx.settings
    print(f"Data folder: {s.home}")
    print(f"Model: {s.model}\n")
    for label, on, how in s.describe():
        print(f"  [{'on ' if on else 'off'}] {label}" + ("" if on else f"  ({how})"))
    open_tasks = ctx.tasks.list(limit=10_000)
    overdue, today = ctx.tasks.overdue_and_today()
    print(f"\nTasks: {len(open_tasks)} open, {len(overdue)} overdue, {len(today)} due today")
    print(f"Memories: {len(ctx.knowledge.memories(limit=10_000))}")
    day = s.now().date().isoformat()
    print(f"Tokens used today: {ctx.store.tokens_used(day):,} of {s.daily_token_limit:,}")
    pending = ctx.store.list_pending()
    if pending:
        print(f"\nWaiting for your approval ({len(pending)}): run `python -m organizer approvals`")
    recent = ctx.store.recent_audit(8)
    if recent:
        print("\nRecent actions:")
        for a in reversed(recent):
            ok = "" if a["ok"] is None else (" ✓" if a["ok"] else " ✗")
            print(f"  {a['at'][:16].replace('T', ' ')}  {a['tool']} [{a['risk']}, {a['decision']}]{ok}")


def cmd_approvals(agent: Agent, action: str | None, pid: str | None) -> None:
    store = agent.ctx.store
    if action in ("approve", "decline"):
        if not pid:
            raise SystemExit("Give the approval id, e.g. approvals approve a1b2c3")
        print(agent.resolve(pid, action == "approve"))
        return
    pending = store.list_pending()
    if not pending:
        print("Nothing is waiting for approval.")
        return
    for p in pending:
        print(f"[{p['id']}] {p['summary']}\n")
    print("Approve with:  python -m organizer approvals approve <id>")
    print("Decline with:  python -m organizer approvals decline <id>")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="organizer", description="Your personal AI assistant.")
    p.add_argument("--home", help="data folder (default ./organizer_data or ORGANIZER_HOME)")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("chat", help="talk to it in the terminal")
    s = sub.add_parser("ask", help="send one message and print the answer")
    s.add_argument("message", nargs="+")
    sub.add_parser("run", help="web app + Telegram bot + reminders and briefing")
    sub.add_parser("serve", help="just the web app")
    sub.add_parser("telegram", help="just the Telegram bot")
    sub.add_parser("briefing", help="print today's briefing")
    s = sub.add_parser("index", help="make a documents folder searchable")
    s.add_argument("folder", nargs="?")
    sub.add_parser("status", help="what's switched on, usage, and recent actions")
    s = sub.add_parser("approvals", help="actions waiting for your approval")
    s.add_argument("action", nargs="?", choices=["approve", "decline"])
    s.add_argument("id", nargs="?")
    args = p.parse_args(argv)

    settings = Settings.from_env(args.home)
    ctx = Context.build(settings)
    agent = Agent.from_settings(ctx)
    cmd = args.cmd or "chat"

    if cmd == "chat":
        cmd_chat(agent, "cli")
    elif cmd == "ask":
        reply = agent.chat("cli", " ".join(args.message), approve=_ask_in_terminal)
        print(reply.text)
    elif cmd == "run":
        cmd_run(agent)
    elif cmd == "serve":
        from .webapp import serve
        serve(agent)
    elif cmd == "telegram":
        if not settings.has_telegram:
            raise SystemExit("Set TELEGRAM_BOT_TOKEN and TELEGRAM_USER_ID first.")
        from .telegram import Telegram
        Telegram(agent).poll_forever()
    elif cmd == "briefing":
        text = gather(ctx)
        ctx.store.set("last_briefing", text)
        print(text)
    elif cmd == "index":
        folder = args.folder or settings.documents_dir
        if not folder:
            raise SystemExit("Give a folder, e.g. `index ~/Documents/work`, or set ORGANIZER_DOCUMENTS_DIR.")
        r = ctx.knowledge.index_folder(folder)
        print(f"Indexed {r['indexed_or_updated']} new or changed files, removed {r['removed']}, "
              f"skipped {r['too_big']} too-big files. {r['total_files']} files are searchable.")
    elif cmd == "status":
        cmd_status(agent)
    elif cmd == "approvals":
        cmd_approvals(agent, args.action, args.id)


if __name__ == "__main__":
    main()
