"""Typed commands that work without an API key (and as a fallback).

    add Call the dentist due friday p1 #health
    add Water plants every week due saturday
    list | list #work | list today | list done
    done a1b2c3 | delete a1b2c3
    remember My manager is Priya | memories | forget 3
    note Ideas for the offsite: ... | notes [words]
    find <words>          (searches notes and documents)
    web <query> | read <url>
    calendar [days] | inbox | briefing | calc 2*(3+4) | help
"""
from __future__ import annotations

import re

from .tasks import TaskError, format_task
from .tools import run_tool

HELP = __doc__.split("\n", 2)[2].rstrip() if __doc__ else ""


def _reply(text: str, actions=None):
    from .agent import Reply
    return Reply(text, [], actions or [])


def parse_add(text: str, now=None) -> dict:
    """'Call mom due friday 5pm p1 #family every week' -> add_task arguments."""
    from datetime import datetime
    from .tasks import parse_due
    now = now or datetime.now()
    args: dict = {}
    s = " " + text.strip() + " "
    m = re.search(r"\s(?:every|repeat(?:s|ing)?)\s+(day|daily|weekday|weekdays|week|weekly|month|monthly|year|yearly)\b", s, re.I)
    if m:
        word = m.group(1).lower()
        args["recur"] = {"day": "daily", "weekday": "weekdays", "week": "weekly", "month": "monthly",
                         "year": "yearly"}.get(word, word)
        s = s[:m.start()] + " " + s[m.end():]
    m = re.search(r"\s[pP]([123])\b", s)
    if m:
        args["priority"] = int(m.group(1))
        s = s[:m.start()] + " " + s[m.end():]
    tags = re.findall(r"\s#([\w-]+)", s)
    if tags:
        args["tags"] = tags
        s = re.sub(r"\s#[\w-]+", " ", s)
    # The date is whatever follows the LAST "due"/"by"/"on" and reads as a date,
    # so "Work on the report due friday" keeps "Work on the report" as the title.
    for m in reversed(list(re.finditer(r"\s(due|by|on)\s+", s, re.I))):
        candidate = s[m.end():].strip()
        try:
            parse_due(candidate, now)
        except TaskError:
            if m.group(1).lower() == "due":
                args["due"] = candidate  # let add_task explain what's wrong with it
                s = s[:m.start()]
                break
            continue
        args["due"] = candidate
        s = s[:m.start()]
        break
    args["title"] = re.sub(r"\s+", " ", s).strip()
    return args


def handle(ctx, text: str):
    cmd, _, rest = text.strip().partition(" ")
    cmd, rest = cmd.lower(), rest.strip()

    def tool(name, args, action=False):
        ok, out = run_tool(ctx, name, args)
        out = re.sub(r"</?untrusted_content[^>]*>\n?|\(Treat the text above.*\)$", "", out).strip()
        return _reply(out, [out.splitlines()[0]] if (ok and action) else [])

    if cmd in ("help", "?", "commands"):
        return _reply(HELP + ("" if ctx.settings.has_llm else
                              "\n\nAdd ANTHROPIC_API_KEY to talk to me in plain English instead."))
    if cmd in ("add", "todo", "task"):
        if not rest:
            return _reply("What should I add? e.g. add Send the report due friday p1")
        try:
            return tool("add_task", parse_add(rest, ctx.settings.now()), True)
        except TaskError as e:
            return _reply(str(e))
    if cmd in ("list", "tasks", "ls"):
        args: dict = {}
        for word in rest.split():
            if word.startswith("#"):
                args["tag"] = word[1:]
            elif word in ("done", "all", "open"):
                args["status"] = word
            elif word in ("today", "overdue"):
                args["due_within_days"] = 0
            elif word == "week":
                args["due_within_days"] = 7
            else:
                args["search"] = word
        return tool("list_tasks", args)
    if cmd in ("done", "complete", "finish", "check"):
        return tool("complete_task", {"id": rest}, True) if rest else _reply("Which task? e.g. done a1b2c3")
    if cmd in ("delete", "remove", "rm"):
        return tool("delete_task", {"id": rest}, True) if rest else _reply("Which task? e.g. delete a1b2c3")
    if cmd == "remember":
        return tool("remember", {"fact": rest}, True) if rest else _reply("What should I remember?")
    if cmd in ("memories", "recall"):
        return tool("recall", {"query": rest})
    if cmd == "forget":
        return tool("forget", {"id": rest}, True) if rest.isdigit() else _reply("Which memory number? e.g. forget 3")
    if cmd == "note":
        if not rest:
            return _reply("What should the note say?")
        title, _, body = rest.partition(":")
        return tool("add_note", {"title": title if body else "", "body": body.strip() or rest}, True)
    if cmd == "notes":
        return tool("search_notes", {"query": rest})
    if cmd in ("find", "search"):
        notes = tool("search_notes", {"query": rest}).text
        docs = tool("search_documents", {"query": rest}).text
        return _reply(f"Notes:\n{notes}\n\nDocuments:\n{docs}")
    if cmd in ("web", "google"):
        return tool("web_search", {"query": rest})
    if cmd in ("read", "open", "fetch"):
        return tool("fetch_url", {"url": rest})
    if cmd in ("calendar", "cal", "agenda"):
        return tool("calendar_events", {"days": int(rest) if rest.isdigit() else 1})
    if cmd in ("inbox", "email", "mail"):
        return tool("list_emails", {"search": rest})
    if cmd in ("briefing", "today", "summary"):
        return tool("daily_briefing", {})
    if cmd in ("calc", "calculate"):
        return tool("calculate", {"expression": rest})

    if not ctx.settings.has_llm:
        return _reply("I only understand typed commands until an ANTHROPIC_API_KEY is set. Here they are:\n\n" + HELP)
    return _reply("I didn't understand that command. Type 'help' for the list.")


__all__ = ["handle", "parse_add", "format_task"]
