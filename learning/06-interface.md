# Section 6: Interface (How You Talk to It) — Complete Study Guide

Your Work Organizer agent can already read email, check your calendar, post to Slack, browse the web and remember things.
But right now you probably talk to it by running a Python script in a terminal. This section gives it real **front doors**:
a polished terminal app, a Telegram bot in your pocket, a web API, a browser chat page that streams replies word by word,
and even a voice you can talk to.

Work through it in order. Each lesson has:

- **Concepts**: what to understand
- **Code**: examples to type out yourself (don't copy-paste; typing builds memory)
- **Common mistakes**: errors beginners hit
- **Exercises**: do them before moving on
- **Check yourself**: you should be able to answer these without looking

Total time: roughly **5–7 weeks at 1–2 hours a day**. The Telegram bot (Lessons 3–4) is the fastest win; if you only have
one weekend, do those two lessons first.

**What you need from earlier sections:** your `organizer` package with a working agent loop (Section 3), a memory layer
(Section 4) and a few real tools (Section 5). In this guide your agent is assumed to expose:

```python
def run_agent(user_id: str, message: str) -> str:
    """Run the agent loop for one user message and return the final reply text."""
```

If your function has a different name or signature, adapt the examples; the ideas are identical.

---

## Table of Contents

- [Part 0: Setup and Project Layout](#part-0-setup-and-project-layout)
- [Part A: Choosing an Interface](#part-a-choosing-an-interface)
  - [Lesson 1: Choosing an Interface](#lesson-1-choosing-an-interface)
- [Part B: The Terminal](#part-b-the-terminal)
  - [Lesson 2: A Polished CLI with Rich and Typer](#lesson-2-a-polished-cli-with-rich-and-typer)
- [Part C: Chat Bots](#part-c-chat-bots)
  - [Lesson 3: Telegram Bot Basics](#lesson-3-telegram-bot-basics)
  - [Lesson 4: Telegram Buttons, Confirmations, and Allow-Listing](#lesson-4-telegram-buttons-confirmations-and-allow-listing)
  - [Lesson 5: Discord and Slack Bots (Briefly)](#lesson-5-discord-and-slack-bots-briefly)
- [Part D: Backend API with FastAPI](#part-d-backend-api-with-fastapi)
  - [Lesson 6: FastAPI Fundamentals](#lesson-6-fastapi-fundamentals)
  - [Lesson 7: Dependencies, Authentication, and CORS](#lesson-7-dependencies-authentication-and-cors)
  - [Lesson 8: A Streaming Agent Core](#lesson-8-a-streaming-agent-core)
  - [Lesson 9: Streaming with Server-Sent Events (SSE)](#lesson-9-streaming-with-server-sent-events-sse)
- [Part E: Web Frontend](#part-e-web-frontend)
  - [Lesson 10: A Plain HTML and JavaScript Chat Page](#lesson-10-a-plain-html-and-javascript-chat-page)
  - [Lesson 11: React Basics](#lesson-11-react-basics)
  - [Lesson 12: Next.js App Router](#lesson-12-nextjs-app-router)
  - [Lesson 13: WebSockets (Overview)](#lesson-13-websockets-overview)
- [Part F: Voice](#part-f-voice)
  - [Lesson 14: Speech-to-Text](#lesson-14-speech-to-text)
  - [Lesson 15: Text-to-Speech and a Push-to-Talk Loop](#lesson-15-text-to-speech-and-a-push-to-talk-loop)
- [Part G: UX for Agents](#part-g-ux-for-agents)
  - [Lesson 16: UX for Agents](#lesson-16-ux-for-agents)
- [Capstone Project: Two Front Doors to One Agent](#capstone-project-two-front-doors-to-one-agent)
- [Weekly Schedule](#weekly-schedule)
- [Final Checklist](#final-checklist)
- [Exercise Solutions](#exercise-solutions)
- [Recommended Resources](#recommended-resources)

---

## Part 0: Setup and Project Layout

### 0.1 Install the Python packages

Activate your project's virtual environment (from Section 1), then install what this section uses. You don't need all of
them on day one; install each group when you reach its lesson.

| Group | Packages | Used in |
|---|---|---|
| Terminal | `rich`, `typer` | Lesson 2 |
| Telegram | `python-telegram-bot` (v21 or newer) | Lessons 3–4 |
| Discord / Slack | `discord.py`, `slack_bolt` | Lesson 5 |
| Backend | `fastapi[standard]`, `pydantic-settings`, `pyjwt` | Lessons 6–9 |
| Voice | `openai`, `faster-whisper`, `pyttsx3`, `sounddevice`, `soundfile`, `numpy` | Lessons 14–15 |

```bash
pip install rich typer "python-telegram-bot>=21" "fastapi[standard]" pydantic-settings
```

With `uv`:
```bash
uv add rich typer "python-telegram-bot>=21" "fastapi[standard]" pydantic-settings
```

`fastapi[standard]` also installs **uvicorn** (the web server that runs FastAPI apps) and the `fastapi` command-line tool.

### 0.2 Install Node.js (for Lessons 11–12)

Download the **LTS** version from nodejs.org (or use `nvm`). Check it worked:

```bash
node --version
```

```bash
npm --version
```

### 0.3 Project layout

By the end of this section your project will look like this. New files are marked `(new)`.

```
work_organizer/
├── .env                       # secrets (gitignored)
├── organizer/
│   ├── agent.py               # run_agent(...) from Section 3
│   ├── memory.py              # Section 4
│   ├── tools.py               # tool schemas + functions (Sections 3 and 5)
│   ├── confirmations.py       # (new) pending risky actions, stored in SQLite
│   └── streaming.py           # (new) stream_agent(...) — yields events as they happen
├── cli/
│   └── main.py                # (new) Rich + Typer terminal app
├── bots/
│   ├── telegram_bot.py        # (new)
│   ├── discord_bot.py         # (new, optional)
│   └── slack_bot.py           # (new, optional)
├── server/
│   ├── main.py                # (new) FastAPI app
│   ├── settings.py            # (new)
│   └── static/
│       ├── index.html         # (new) plain web chat page
│       └── app.js             # (new)
├── voice/
│   └── talk.py                # (new) push-to-talk loop
└── web/                       # (new, optional) Next.js app
```

### 0.4 Add new secrets to `.env`

```
ANTHROPIC_API_KEY=your-anthropic-key
TELEGRAM_BOT_TOKEN=123456:replace-me
TELEGRAM_ALLOWED_USER_IDS=111111111
API_KEY=replace-with-a-long-random-string
OPENAI_API_KEY=your-openai-key-for-voice
```

Generate a strong random value for `API_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Remember the rule from Section 1: `.env` is in `.gitignore`, and you commit a `.env.example` with fake values only.

---

## Part A: Choosing an Interface

### Lesson 1: Choosing an Interface

**Concepts**

An **interface** (or "front end", or "front door") is how a human gets messages into your agent and replies out of it.
The single most important design idea in this section:

> **One brain, many front doors.** The agent (model calls, tools, memory) lives in one place. Every interface is a thin
> adapter that turns "something the human did" into `run_agent(user_id, message)` and turns the reply into "something the
> human sees".

```
 Terminal (Rich/Typer) ─┐
 Telegram bot ──────────┤
 Slack / Discord bot ───┼──►  organizer.run_agent / stream_agent  ──►  Claude + tools + memory
 Web page ──► FastAPI ──┤
 Voice loop ────────────┘
```

If you find yourself copying tool logic or prompts into a bot file, stop: that logic belongs in `organizer/`.

**Comparison of interface options**

| Option | Effort to build | Works on phone | Push notifications | Rich UI (buttons, forms) | Good for |
|---|---|---|---|---|---|
| CLI (Rich + Typer) | Very low | No | No | Limited (prompts, tables) | Development, power users, scripting |
| Telegram bot | Low | Yes | Yes (free) | Inline buttons, files, voice notes | **Personal assistant you use daily** |
| Discord bot | Low | Yes | Yes | Buttons, slash commands | Hobby communities, friends |
| Slack bot | Medium (app setup, scopes) | Yes | Yes | Block Kit (rich) | Work teams already in Slack |
| Web app (FastAPI + HTML/React) | Medium–High | Yes (browser) | Hard (needs PWA/web push) | Unlimited | Dashboards, sharing with others, full control |
| Voice | Medium | Possible | N/A | None (audio only) | Hands-free use, accessibility |

**Questions to ask before you choose**

| Question | If yes, lean towards |
|---|---|
| Will I use it mostly from my phone? | Telegram |
| Do I need the assistant to message *me* first (reminders, morning briefing)? | Telegram / Slack / Discord |
| Will other people use it? | Web app with proper login, or Slack for a team |
| Do I need custom screens (task board, calendar view)? | Web app |
| Am I still changing the agent every day? | CLI first, then add others |

**Recommendation for this course:** build the CLI polish (Lesson 2) for development, a **Telegram bot** as your daily
driver (easiest path to a phone app with buttons and notifications), and a **FastAPI backend + web page** to learn how
real products are built. Voice is a fun extra.

**Bots don't need a server you host on the internet (at first).** Telegram, Discord and Slack (in Socket Mode) all let
your bot make an *outgoing* connection to their servers and pull messages. That means your laptop can run the bot with
no domain, no HTTPS certificate and no open ports. A web app, in contrast, needs to be reachable — locally that's
`localhost`, and publicly it needs hosting.

**Common mistakes**
- Building the web app first. It's the most work, and you'll spend weeks on CSS instead of on the assistant.
- Duplicating agent logic per interface, so the Telegram bot and web app slowly behave differently.
- Forgetting that every interface is a way *in*. A public bot without an allow-list is a public, free, credit-card-backed AI that can read your email.

**Exercises**
1. Write down the three situations in a typical week where you'd want to talk to your assistant (e.g. "walking to a meeting"). For each, pick the best interface from the table and say why.
2. Draw the "one brain, many front doors" diagram for *your* project, with your real module and function names.

**Check yourself**
- Why can a Telegram bot run on your laptop without a public URL, while a web app cannot be used from your phone without hosting?
- What belongs in an interface file, and what belongs in `organizer/`?

---

## Part B: The Terminal

### Lesson 2: A Polished CLI with Rich and Typer

**Concepts**
- **Typer** builds command-line apps from normal Python functions. Type hints become argument parsing and `--help` text.
  It replaces the `argparse` code you wrote in Section 1.
- **Rich** prints colour, tables, panels, Markdown, spinners and live-updating text in the terminal.
- Claude often answers in Markdown (lists, **bold**, code). `rich.markdown.Markdown` renders it properly instead of showing raw `**` symbols.

**Code — Rich and Typer in one small file**
```python
# rich_typer_demo.py
from typing import Annotated
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="Demo of Rich + Typer.")
console = Console()

@app.command()
def show(
    name: Annotated[str, typer.Argument(help="Who to greet")],
    tasks: Annotated[bool, typer.Option(help="Also show a task table")] = False,
) -> None:
    """Greet someone with a Markdown panel, and optionally show a table."""
    console.print(Panel(Markdown(f"Hello **{name}**!\n\n- one\n- two"), title="Assistant"))
    if tasks:
        table = Table(title="Pending tasks")
        table.add_column("Title")
        table.add_column("Priority", justify="right")
        table.add_row("Write report", "1", style="bold red")
        table.add_row("Book dentist", "3")
        console.print(table)

@app.command()
def wait() -> None:
    """Show a spinner for two seconds."""
    import time
    with console.status("Thinking...", spinner="dots"):
        time.sleep(2)
    console.print("[bold green]Done![/bold green]")

if __name__ == "__main__":
    app()
```

```bash
python rich_typer_demo.py --help
```

```bash
python rich_typer_demo.py show John --tasks
```

Typer turned the type hints into arguments (`name` is required because it has no default) and options (`--tasks` is a
flag because it's a `bool`), and generated `--help` from the docstrings. `rich.prompt.Prompt.ask(...)` and
`Confirm.ask(...)` give you nicer `input()` replacements.

**Code — the polished CLI wrapping your agent**
```python
# cli/main.py
from typing import Annotated
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from organizer.agent import run_agent

app = typer.Typer(help="Talk to your Work Organizer.")
console = Console()

def show_reply(reply: str) -> None:
    console.print(Panel(Markdown(reply), title="Assistant", border_style="cyan"))

@app.command()
def ask(question: str, user: Annotated[str, typer.Option()] = "owner") -> None:
    """Ask one question and exit (handy for scripts and shortcuts)."""
    with console.status("Thinking..."):
        reply = run_agent(user, question)
    show_reply(reply)

@app.command()
def chat(user: Annotated[str, typer.Option()] = "owner") -> None:
    """Interactive chat. Type 'exit' or press Ctrl+C to quit."""
    console.print("[bold]Work Organizer[/bold] — type [cyan]exit[/cyan] to quit.\n")
    while True:
        try:
            text = Prompt.ask("[bold green]You[/bold green]")
        except (KeyboardInterrupt, EOFError):
            break
        if text.strip().lower() in {"exit", "quit"}:
            break
        if not text.strip():
            continue
        try:
            with console.status("Thinking..."):
                reply = run_agent(user, text)
        except Exception as e:                       # show, don't crash the session
            console.print(f"[red]Something went wrong:[/red] {e}")
            continue
        show_reply(reply)
    console.print("Bye!")

if __name__ == "__main__":
    app()
```

Run it from the project root (so `organizer` can be imported):

```bash
python -m cli.main chat
```

```bash
python -m cli.main ask "Summarise my unread email"
```

(`cli/` needs an empty `__init__.py` file for `python -m cli.main` to work.)

In Lesson 8 you'll upgrade this to **stream** replies word by word with `rich.live.Live`.

**Common mistakes**
- Running `python cli/main.py` and getting `ModuleNotFoundError: No module named 'organizer'`. Run from the project root with `python -m cli.main`.
- Printing with `print()` inside a `console.status(...)` block — the spinner and your text fight. Use `console.print`.
- Rich markup in user text: if a reply contains `[red]`, Rich treats it as a style tag. Rendering through `Markdown(...)` avoids this; for plain strings use `console.print(text, markup=False)`.
- A single-command Typer app runs that command directly without a subcommand name; with two or more commands you must type the command name.

**Exercises**
1. Add a `tasks` command that prints your pending tasks (from your Section 1/3 task functions) as a Rich table, with priority 1 in red.
2. Add a `--plain` option to `chat` that prints replies without panels or Markdown (useful when piping output to a file).
3. Add a `/clear` command inside the chat loop that clears the screen (`console.clear()`) without exiting.

**Check yourself**
- How does Typer know that `question` is required but `--user` is optional?
- Why render replies with `Markdown(...)` instead of printing the raw string?

---

## Part C: Chat Bots

### Lesson 3: Telegram Bot Basics

**Concepts**
- A **Telegram bot** is a special Telegram account controlled by your code. You create it by chatting with **@BotFather**
  in the Telegram app, which gives you a **bot token** (a secret, like an API key).
- Your code talks to the **Telegram Bot API**. The library `python-telegram-bot` (v21+) wraps it with an **async** API
  (everything is `async def` and `await`, which you learned in Section 1, Lesson 23).
- **Polling vs webhooks**: with **polling**, your program repeatedly asks Telegram "any new messages?" — works on a laptop,
  no public URL needed. With **webhooks**, Telegram pushes messages to an HTTPS URL you host. Start with polling.
- **Handlers** connect kinds of updates to your functions: `CommandHandler("start", ...)` for `/start`,
  `MessageHandler(filters.TEXT, ...)` for normal text, `CallbackQueryHandler` for button presses (Lesson 4).
- Each handler receives `update` (what happened: message, user, chat) and `context` (the bot, user/chat data, errors).

**Create your bot (one-time)**
1. In Telegram, open a chat with **@BotFather** and send `/newbot`.
2. Choose a display name ("Work Organizer") and a username ending in `bot` (e.g. `john_work_organizer_bot`).
3. BotFather replies with a token like `123456789:AA...`. Put it in `.env` as `TELEGRAM_BOT_TOKEN`. **Never commit it.**
4. Optional: send `/setcommands` to BotFather and paste:
   ```
   start - Say hello
   help - What I can do
   today - Summary of today
   ```
   These appear in the Telegram menu.

**Code — the bot, connected to your agent**

Your `run_agent` is a normal (synchronous) function that can take 5–30 seconds. If you call it directly inside an
`async def` handler, the whole bot freezes for every user until it finishes. Run it in a worker thread with
`asyncio.to_thread`:

```python
# bots/telegram_bot.py (first version)
import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from organizer.agent import run_agent

load_dotenv()
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("telegram_bot")

TELEGRAM_LIMIT = 4096   # max characters in one Telegram message

def split_message(text: str, limit: int = TELEGRAM_LIMIT) -> list[str]:
    """Split long text into chunks, preferring to break at newlines."""
    chunks = []
    while len(text) > limit:
        cut = text.rfind("\n", 0, limit)
        if cut <= 0:
            cut = limit
        chunks.append(text[:cut])
        text = text[cut:].lstrip("\n")
    if text:
        chunks.append(text)
    return chunks

async def keep_typing(bot, chat_id: int, stop: asyncio.Event) -> None:
    """Telegram's 'typing...' indicator lasts ~5 seconds, so refresh it until stopped."""
    while not stop.is_set():
        await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        try:
            await asyncio.wait_for(stop.wait(), timeout=4)
        except TimeoutError:
            pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"Hi {user.first_name}! I'm your Work Organizer. (Your Telegram user id is {user.id}.)"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Try:\n- What's on my calendar today?\n- Summarise unread email\n- Add a task: call the bank"
    )

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    stop = asyncio.Event()
    typing_task = asyncio.create_task(keep_typing(context.bot, chat_id, stop))
    try:
        reply = await asyncio.to_thread(run_agent, "owner", update.message.text)
    except Exception:
        log.exception("Agent failed")
        reply = "Sorry, something went wrong on my side. Please try again in a minute."
    finally:
        stop.set()
        await typing_task
    for chunk in split_message(reply):
        await update.message.reply_text(chunk)

async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.error("Unhandled error", exc_info=context.error)

def main() -> None:
    app = Application.builder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_error_handler(on_error)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
```

```bash
python -m bots.telegram_bot
```

Open your bot in Telegram, press **Start**, and note the **user id** it shows — you'll need it for the allow-list in
Lesson 4. Then ask it something real. `run_polling()` blocks until Ctrl+C and manages the asyncio event loop for you,
so you don't call `asyncio.run` yourself. (`bots/` needs an empty `__init__.py`.)

**Why `"owner"` and not the Telegram user id?** Your memory (Section 4) is keyed by `user_id`. If the Telegram bot uses
`"123456789"` and the web app uses `"owner"`, your assistant has two separate memories of you. Map every interface's
identity to **one internal user id**. For a personal assistant that's simply `"owner"`; for a multi-user app you'd keep a
table mapping `telegram:123456789 → user_42`.

**Formatting replies.** Telegram can render Markdown or HTML (`parse_mode=...`), but its parser is strict: one
unmatched `_` or `*` in the model's reply causes a `BadRequest` error and the message is not sent. Start with **plain text**
(no `parse_mode`). If you want formatting later, use `ParseMode.HTML` and escape the text with `html.escape` first.

**Common mistakes**
- Calling a slow synchronous function directly in an `async` handler — the bot stops responding to everyone. Use `await asyncio.to_thread(...)`.
- Forgetting `await` on `reply_text(...)` — nothing is sent, and Python warns "coroutine was never awaited".
- Running two copies of the bot with the same token — Telegram returns `Conflict: terminated by other getUpdates request`. Stop the old one.
- `filters.TEXT` without `& ~filters.COMMAND` — your text handler also catches `/start`.
- Leaving `httpx` logging at INFO — the log lines contain your bot token in the URL. Anyone you send logs to can hijack your bot.

**Exercises**
1. Add a `/today` command that calls `run_agent("owner", "Give me a short summary of today: calendar, top tasks, urgent email.")`.
2. Add a `/ping` command that replies with how long the bot has been running (hint: store `time.monotonic()` at startup in `app.bot_data`).
3. Handle **voice notes** later in Lesson 14 — for now, add a handler for `filters.PHOTO` that replies "I can't read images yet."

**Check yourself**
- What does `run_polling()` do, and why doesn't the bot need a public URL?
- Why is `asyncio.to_thread` needed around `run_agent`?
- What is the difference between `update.effective_user.id` and `update.effective_chat.id`?

---

### Lesson 4: Telegram Buttons, Confirmations, and Allow-Listing

**Concepts**
- **Allow-listing**: anyone on Earth can find and message your bot. Your bot can read your email and spend your API
  credits, so it must **only respond to your own Telegram user id**. Telegram user ids can't be faked by the sender —
  they're set by Telegram's servers.
- **Inline keyboards** are buttons attached under a message. Each button has a `callback_data` string (max **64 bytes**).
  When pressed, your bot receives a **callback query** containing that string.
- **Confirmations for risky actions**: the agent should never send an email, delete an event or post to a public channel
  just because the model decided to. Instead, the risky tool creates a **pending action** and the interface asks you
  **Approve / Cancel**. Only an explicit tap runs it.

**Code — allow-listing with filters**
```python
import os
from telegram.ext import filters

ALLOWED_IDS = {
    int(x) for x in os.environ["TELEGRAM_ALLOWED_USER_IDS"].split(",") if x.strip()
}
ALLOWED = filters.User(user_id=ALLOWED_IDS)

# Only allowed users reach the real handlers:
app.add_handler(CommandHandler("start", start, filters=ALLOWED))
app.add_handler(MessageHandler(ALLOWED & filters.TEXT & ~filters.COMMAND, on_text))

# Everyone else falls through to this one (added LAST):
async def unauthorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.warning("Blocked user %s", update.effective_user.id if update.effective_user else "?")
    if update.effective_message:
        await update.effective_message.reply_text("Sorry, this is a private assistant.")

app.add_handler(MessageHandler(filters.ALL, unauthorized))
```

Handlers in the same group are checked **in the order you add them**, and the first one whose filter matches handles the
update. That's why the catch-all goes last.

**Code — a shared confirmations store**

The confirmation logic must work in *every* interface (Telegram, web, CLI), and the Telegram bot and web server may run
as separate processes. So pending actions live in **SQLite** (Section 4), not in a Python dict.

```python
# organizer/confirmations.py
"""Pending risky actions that need a human 'Approve' before they run."""
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from organizer.tools import run_tool

DB_PATH = Path("data/organizer.db")
EXPIRES_AFTER_SECONDS = 15 * 60

@dataclass
class PendingAction:
    id: str
    user_id: str
    tool_name: str
    args: dict
    summary: str
    status: str
    created_at: float

def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS pending_actions (
               id TEXT PRIMARY KEY,
               user_id TEXT NOT NULL,
               tool_name TEXT NOT NULL,
               args_json TEXT NOT NULL,
               summary TEXT NOT NULL,
               status TEXT NOT NULL DEFAULT 'pending',
               created_at REAL NOT NULL
           )"""
    )
    return conn

def describe(tool_name: str, args: dict) -> str:
    """A human-readable summary shown next to the Approve button."""
    if tool_name == "send_email":
        body = str(args.get("body", ""))
        preview = body if len(body) <= 300 else body[:300] + "..."
        return f"Send email to {args.get('to')}\nSubject: {args.get('subject')}\n\n{preview}"
    return f"{tool_name}({json.dumps(args, ensure_ascii=False)[:300]})"

def create(user_id: str, tool_name: str, args: dict) -> PendingAction:
    action = PendingAction(
        id=uuid.uuid4().hex[:12],
        user_id=user_id,
        tool_name=tool_name,
        args=args,
        summary=describe(tool_name, args),
        status="pending",
        created_at=time.time(),
    )
    with _connect() as conn:
        conn.execute(
            "INSERT INTO pending_actions (id, user_id, tool_name, args_json, summary, status, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (action.id, user_id, tool_name, json.dumps(args), action.summary, "pending", action.created_at),
        )
    return action

def get(action_id: str) -> PendingAction | None:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM pending_actions WHERE id = ?", (action_id,)).fetchone()
    if row is None:
        return None
    return PendingAction(
        id=row["id"], user_id=row["user_id"], tool_name=row["tool_name"],
        args=json.loads(row["args_json"]), summary=row["summary"],
        status=row["status"], created_at=row["created_at"],
    )

def list_pending(user_id: str) -> list[PendingAction]:
    cutoff = time.time() - EXPIRES_AFTER_SECONDS
    with _connect() as conn:
        ids = [r["id"] for r in conn.execute(
            "SELECT id FROM pending_actions WHERE user_id = ? AND status = 'pending' AND created_at > ?"
            " ORDER BY created_at",
            (user_id, cutoff),
        )]
    return [a for a in (get(i) for i in ids) if a is not None]

def _claim(action_id: str, user_id: str, new_status: str) -> bool:
    """Atomically move pending -> new_status. Returns False if already handled, expired, or not yours."""
    cutoff = time.time() - EXPIRES_AFTER_SECONDS
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE pending_actions SET status = ?"
            " WHERE id = ? AND user_id = ? AND status = 'pending' AND created_at > ?",
            (new_status, action_id, user_id, cutoff),
        )
        return cur.rowcount == 1

def approve(action_id: str, user_id: str) -> str:
    """Run the action if it is still pending. Safe to call twice: the second call does nothing."""
    if not _claim(action_id, user_id, "running"):
        return "This action was already handled or has expired."
    action = get(action_id)
    try:
        result = run_tool(action.tool_name, action.args)
    except Exception as e:
        with _connect() as conn:
            conn.execute("UPDATE pending_actions SET status = 'failed' WHERE id = ?", (action_id,))
        return f"Failed: {e}"
    with _connect() as conn:
        conn.execute("UPDATE pending_actions SET status = 'done' WHERE id = ?", (action_id,))
    return f"Done. {result}"

def reject(action_id: str, user_id: str) -> str:
    if _claim(action_id, user_id, "rejected"):
        return "Cancelled. Nothing was sent."
    return "This action was already handled or has expired."
```

Key ideas in that file:
- `_claim` uses a single `UPDATE ... WHERE status = 'pending'` and checks `rowcount`. If you double-tap Approve, or tap it on your phone and in the browser at the same moment, **only one** call wins. The action can never run twice.
- Actions **expire** after 15 minutes, so an old button in your chat history can't fire an email next week.
- The check `user_id = ?` means one user can't approve another user's action, even if they guess the id.

**Code — making risky tools go through confirmations**

In your agent loop (Section 3), find the place where you execute a tool the model asked for. Add a gate in front of it:

```python
# organizer/tools.py — add this set next to your tool functions
RISKY_TOOLS = {"send_email", "delete_calendar_event", "post_slack_message"}
```

```python
# inside your agent loop, where you handle each tool_use block
from organizer import confirmations
from organizer.tools import RISKY_TOOLS, run_tool

if block.name in RISKY_TOOLS:
    action = confirmations.create(user_id, block.name, block.input)
    output = (
        f"Not executed yet. Action {action.id} is waiting for the user to tap Approve. "
        "Tell the user briefly what you prepared and that it needs their approval."
    )
else:
    output = run_tool(block.name, block.input)
```

The model gets an honest tool result ("waiting for approval"), so it tells you "I've drafted the email to Dana — tap
Approve to send it" instead of falsely claiming it was sent.

**Code — showing Approve / Cancel buttons in Telegram**
```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from organizer import confirmations

OWNER = "owner"

def confirm_keyboard(action_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("Approve", callback_data=f"approve:{action_id}"),
        InlineKeyboardButton("Cancel", callback_data=f"reject:{action_id}"),
    ]])

async def send_pending_confirmations(update: Update) -> None:
    for action in confirmations.list_pending(OWNER):
        await update.effective_message.reply_text(
            f"Needs your approval:\n\n{action.summary}",
            reply_markup=confirm_keyboard(action.id),
        )

async def on_confirm_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query.from_user.id not in ALLOWED_IDS:            # buttons need their own allow-list check
        await query.answer("Not allowed.", show_alert=True)
        return
    await query.answer()
    decision, action_id = query.data.split(":", 1)
    if decision == "approve":
        await query.edit_message_text(f"{query.message.text}\n\nRunning...")
        result = await asyncio.to_thread(confirmations.approve, action_id, OWNER)
    else:
        result = await asyncio.to_thread(confirmations.reject, action_id, OWNER)
    await query.edit_message_text(f"{query.message.text}\n\n{result}")

app.add_handler(CallbackQueryHandler(on_confirm_button, pattern=r"^(approve|reject):"))
```

How inline keyboards work: `InlineKeyboardMarkup` takes a list of **rows**, each a list of buttons. When a button is
tapped, the `CallbackQueryHandler` whose `pattern` matches `callback_data` runs. You must `await query.answer()` (it stops
the button's loading spinner), and `edit_message_text` replaces the message, which also removes the buttons so they
can't be tapped twice by accident.

Call `await send_pending_confirmations(update)` at the end of `on_text`, after sending the agent's reply. (In the capstone
you'll show only the actions created by *this* message, using the streaming events from Lesson 8.)

Note that `query.message.text` is the message text *at the time the button was pressed*, so the second
`edit_message_text` builds on the original text, not on the "Running..." version.

**Common mistakes**
- Not calling `await query.answer()` — the user sees a loading spinner on the button for ~15 seconds.
- Putting the whole action (email body, JSON args) in `callback_data` — it's limited to 64 bytes. Store the action and put only its id in the button.
- Allow-listing messages but not callback queries. `CallbackQueryHandler` doesn't use your message filters; check `query.from_user.id` yourself.
- Executing the tool and *then* asking for confirmation. The gate must be in front of the side effect.
- Storing allowed ids as strings and comparing to an `int` user id — `"111" != 111`, so nobody gets in (or worse, the check is skipped).

**Exercises**
1. Add a `/pending` command that lists all pending actions with their buttons (useful if you scrolled past them).
2. Add a third button, **Edit**, that replies "Tell me what to change" and stores the action id in `context.user_data["editing"]`. Your next text message should be sent to the agent as "Revise pending action <id>: <your text>".
3. Make expired actions show a clear message: when `approve` returns the "expired" text, edit the message to remove the buttons and say "Expired — ask me again."

**Check yourself**
- Why are pending actions stored in SQLite instead of a Python dictionary?
- How does `_claim` guarantee an action runs at most once?
- Why must the tool result say "not executed yet" instead of pretending the email was sent?

---

### Lesson 5: Discord and Slack Bots (Briefly)

The pattern is identical to Telegram: receive a message → check the sender is allowed → `run_agent` in a thread → reply.
Only the setup and event names differ.

**Discord with `discord.py`**

Setup: go to the Discord Developer Portal → **New Application** → **Bot** → copy the token, and enable the
**Message Content Intent** (otherwise your bot receives empty message text). Under **OAuth2 → URL Generator**, tick
`bot` and the "Send Messages" and "Read Message History" permissions, open the generated URL, and add the bot to your
own server.

```bash
pip install discord.py
```

```python
# bots/discord_bot.py
import asyncio
import os

import discord
from dotenv import load_dotenv

from organizer.agent import run_agent

load_dotenv()
ALLOWED_IDS = {int(x) for x in os.environ["DISCORD_ALLOWED_USER_IDS"].split(",") if x.strip()}
DISCORD_LIMIT = 2000

intents = discord.Intents.default()
intents.message_content = True          # must also be enabled in the Developer Portal
client = discord.Client(intents=intents)

@client.event
async def on_ready() -> None:
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message: discord.Message) -> None:
    if message.author == client.user or message.author.bot:
        return                                            # never reply to yourself or other bots
    if message.author.id not in ALLOWED_IDS:
        return
    is_dm = isinstance(message.channel, discord.DMChannel)
    if not (is_dm or client.user in message.mentions):
        return                                            # in servers, only answer when @mentioned
    text = message.content.replace(f"<@{client.user.id}>", "").strip()
    async with message.channel.typing():
        reply = await asyncio.to_thread(run_agent, "owner", text)
    for i in range(0, len(reply), DISCORD_LIMIT):
        await message.channel.send(reply[i:i + DISCORD_LIMIT])

client.run(os.environ["DISCORD_BOT_TOKEN"])
```

Discord also has **buttons** (`discord.ui.View` with `discord.ui.Button`) that work like Telegram's inline keyboards, and
**slash commands** (`discord.app_commands`). Use them once the basic bot works.

**Slack with `slack_bolt` (Socket Mode)**

You met the Slack Web API in Section 5 for *posting* messages. To *receive* messages your app needs events. **Socket
Mode** lets your laptop receive them over a WebSocket without a public URL.

Setup at api.slack.com/apps: create an app → enable **Socket Mode** (this creates an **app-level token** starting
`xapp-`, scope `connections:write`) → under **OAuth & Permissions** add bot scopes `app_mentions:read`, `chat:write`,
`im:history` → under **Event Subscriptions** subscribe to bot events `app_mention` and `message.im` → under **App
Home** enable the Messages tab → install to your workspace to get the **bot token** (`xoxb-`).

```bash
pip install slack_bolt
```

```python
# bots/slack_bot.py
import os

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from organizer.agent import run_agent

load_dotenv()
ALLOWED_USERS = set(os.environ["SLACK_ALLOWED_USER_IDS"].split(","))   # e.g. U0123ABCD

app = App(token=os.environ["SLACK_BOT_TOKEN"])

def handle(event: dict, say) -> None:
    if event.get("bot_id") or event.get("user") not in ALLOWED_USERS:
        return
    reply = run_agent("owner", event.get("text", ""))
    say(text=reply, thread_ts=event.get("thread_ts") or event.get("ts"))   # answer in a thread

@app.event("app_mention")
def on_mention(event, say):
    handle(event, say)

@app.event("message")
def on_message(event, say):
    if event.get("channel_type") == "im" and not event.get("subtype"):
        handle(event, say)

if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
```

Bolt runs listeners in worker threads, so a synchronous `run_agent` is fine here. Slack's rich buttons are built with
**Block Kit**; button clicks arrive via `@app.action("approve")`, where you must call `ack()` within 3 seconds.

**Platform comparison**

| | Telegram | Discord | Slack |
|---|---|---|---|
| Library | `python-telegram-bot` | `discord.py` | `slack_bolt` |
| Receive without public URL | Polling | Gateway (WebSocket) | Socket Mode |
| Message length limit | 4096 chars | 2000 chars | ~40,000 chars (keep it much shorter) |
| Buttons | Inline keyboard | `discord.ui.View` | Block Kit actions |
| User id example | `111111111` (int) | `222222222222222222` (int) | `U0123ABCD` (str) |
| Setup effort | 2 minutes | 10 minutes | 20 minutes |

**Common mistakes**
- Discord: forgetting `intents.message_content = True` (or the portal toggle) — `message.content` is always empty.
- Discord/Slack: replying to your own bot's messages, causing an infinite loop. Always ignore bot authors.
- Slack: subscribing to `message.channels` instead of `message.im` and getting every message in every channel.
- Slack: confusing the two tokens. `xoxb-` is the bot token (`App(token=...)`); `xapp-` is the app-level token (`SocketModeHandler`).

**Exercises**
1. Pick Discord *or* Slack and get the bot answering your DMs with your agent.
2. Make the Slack bot add a `:hourglass:` reaction while it's thinking (`app.client.reactions_add(...)`) and remove it when done.

**Check yourself**
- What three things does every bot adapter do, regardless of platform?
- Why does Slack Socket Mode need two different tokens?

---

## Part D: Backend API with FastAPI

### Lesson 6: FastAPI Fundamentals

**Concepts**
- A **backend API** is a program that listens for HTTP requests (Section 2) and returns JSON. Your web page, a phone
  app, a shortcut on your phone, or another program can all use the same API.
- **FastAPI** is the most popular modern Python web framework for APIs. It uses **type hints and Pydantic models**
  (Section 1, Lesson 22) to validate requests, convert data and generate documentation automatically.
- **Routes** (also called endpoints or path operations) connect an HTTP method + path to a function:
  `@app.get("/tasks")`, `@app.post("/chat")`.
- **Path parameters** are part of the URL (`/tasks/42`); **query parameters** come after `?` (`/tasks?status=done&limit=5`);
  the **request body** is JSON sent with POST/PUT.
- **Uvicorn** is the server that actually runs your app. `fastapi dev` starts it with auto-reload.

**Code — your first API**
```python
# server/hello.py
from fastapi import FastAPI

app = FastAPI(title="Work Organizer API", version="0.1.0")

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/greet/{name}")
async def greet(name: str, excited: bool = False) -> dict[str, str]:
    message = f"Hello, {name}" + ("!" if excited else ".")
    return {"message": message}
```

```bash
fastapi dev server/hello.py
```

Now open these in your browser:
- `http://127.0.0.1:8000/health` → `{"status":"ok"}`
- `http://127.0.0.1:8000/greet/John?excited=true` → `{"message":"Hello, John!"}`
- `http://127.0.0.1:8000/greet/John?excited=maybe` → a **422** error explaining `excited` must be a boolean
- `http://127.0.0.1:8000/docs` → interactive **Swagger UI** documentation, generated for free. Click "Try it out".
- `http://127.0.0.1:8000/redoc` → the same docs in another style
- `http://127.0.0.1:8000/openapi.json` → the machine-readable **OpenAPI** schema

In `greet`, `name` matches `{name}` in the path, so it's a path parameter. `excited` isn't in the path, so FastAPI
treats it as a query parameter, and because it has a default it's optional.

**Code — request and response models**
```python
# server/tasks_api.py
from datetime import datetime
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Path, Query, status
from pydantic import BaseModel, Field

app = FastAPI(title="Tasks API")

class TaskCreate(BaseModel):
    """What the client sends to create a task."""
    title: str = Field(min_length=1, max_length=200, examples=["Write report"])
    priority: int = Field(default=3, ge=1, le=3, description="1 = high, 3 = low")

class Task(TaskCreate):
    """What the API returns."""
    id: int
    done: bool = False
    created_at: datetime

TASKS: dict[int, Task] = {}
_next_id = 1

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(body: TaskCreate) -> Task:
    global _next_id
    task = Task(id=_next_id, created_at=datetime.now(), **body.model_dump())
    TASKS[task.id] = task
    _next_id += 1
    return task

@app.get("/tasks")
async def list_tasks(
    status_filter: Annotated[Literal["all", "pending", "done"], Query(alias="status")] = "pending",
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[Task]:
    tasks = list(TASKS.values())
    if status_filter == "pending":
        tasks = [t for t in tasks if not t.done]
    elif status_filter == "done":
        tasks = [t for t in tasks if t.done]
    return sorted(tasks, key=lambda t: t.priority)[:limit]

@app.get("/tasks/{task_id}")
async def get_task(task_id: Annotated[int, Path(ge=1)]) -> Task:
    task = TASKS.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task
```

```bash
fastapi dev server/tasks_api.py
```

Test from the terminal with `curl` (or use the `/docs` page):

```bash
curl -X POST http://127.0.0.1:8000/tasks -H "Content-Type: application/json" -d '{"title": "Write report", "priority": 1}'
```

```bash
curl "http://127.0.0.1:8000/tasks?status=all&limit=5"
```

What FastAPI did for you:
- Parsed the JSON body into a `TaskCreate` object and **rejected invalid data with a 422** (try `"priority": 7`).
- Converted the returned `Task` (including the `datetime`) to JSON.
- Used the **return type annotation** (`-> Task`) as the response model: extra fields are filtered out and the docs show the exact shape.
- Generated docs that show every field, its limits and examples.

**Async vs sync endpoints**

| You write | FastAPI does | Use when |
|---|---|---|
| `async def endpoint()` | Runs it on the event loop | The code inside only `await`s async libraries (`httpx.AsyncClient`, `AsyncAnthropic`) |
| `def endpoint()` | Runs it in a thread pool automatically | The code calls blocking things (`requests`, `sqlite3`, your sync `run_agent`) |

The dangerous combination is `async def` + blocking call: one slow request freezes the whole server.

```python
import asyncio
from organizer.agent import run_agent

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)

class ChatResponse(BaseModel):
    reply: str

# Option 1: plain def -> FastAPI runs it in a thread for you
@app.post("/chat-once")
def chat_once(body: ChatRequest) -> ChatResponse:
    return ChatResponse(reply=run_agent("owner", body.message))

# Option 2: async def + explicitly move the blocking call to a thread
@app.post("/chat-once-async")
async def chat_once_async(body: ChatRequest) -> ChatResponse:
    reply = await asyncio.to_thread(run_agent, "owner", body.message)
    return ChatResponse(reply=reply)
```

**Common mistakes**
- `time.sleep()`, `requests.get()` or a sync `run_agent()` directly inside `async def` — the server stops responding to everyone.
- Naming a query parameter `status` and also importing `fastapi.status` — the parameter shadows the module. That's why the example uses `status_filter` with `alias="status"`.
- Defining `/tasks/{task_id}` *before* `/tasks/summary` — FastAPI matches routes in order, so `"summary"` is treated as a `task_id` and fails validation. Put fixed paths first.
- Returning a huge internal object and leaking fields (like password hashes). Always declare a response model.
- Running `fastapi dev` in production. Use `fastapi run` (no auto-reload, listens on all interfaces).

**Exercises**
1. Add `GET /tasks/summary` returning `{"total": ..., "pending": ..., "done": ...}` using a Pydantic response model. Make sure it isn't swallowed by `/tasks/{task_id}`.
2. Add an optional `tag` query parameter to `GET /tasks` that accepts **multiple** values (`?tag=work&tag=urgent`). Hint: `Annotated[list[str] | None, Query()] = None`.
3. Replace the in-memory `TASKS` dict with your real task storage from Section 1/3.

**Check yourself**
- How does FastAPI decide whether a function parameter is a path parameter, a query parameter or the request body?
- What does a 422 response mean, and who produces it?
- When should an endpoint be `def` instead of `async def`?

---

### Lesson 7: Dependencies, Authentication, and CORS

**Concepts**
- **Dependency injection** (`Depends`) lets an endpoint declare "I need X" and FastAPI provides X before the endpoint
  runs. X can be settings, a database connection, or **the current authenticated user**. If the dependency raises an
  `HTTPException`, the endpoint never runs.
- **Authentication** answers "who is calling?". For a personal assistant, a single secret **API key** sent in a header is
  enough. For apps with several users, you need logins with **sessions** or **JWTs**.
- **CORS** (Cross-Origin Resource Sharing) is a *browser* rule: a page loaded from `http://localhost:3000` can't read
  responses from `http://localhost:8000` unless the API says that origin is allowed. It doesn't apply to `curl`,
  Python, or bots — only browsers.

**Code — settings as a dependency**
```python
# server/settings.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_key: str                                   # read from API_KEY in .env (case-insensitive)
    allowed_origins: list[str] = ["http://localhost:3000"]
    model: str = "claude-sonnet-5-5"

@lru_cache
def get_settings() -> Settings:
    return Settings()                              # read .env once, then reuse
```

`pydantic-settings` reads environment variables (and `.env`), converts types and **fails at startup** if a required one
like `API_KEY` is missing — much better than discovering it on the first request. List values are written as JSON in
`.env`, e.g. `ALLOWED_ORIGINS=["http://localhost:3000","http://127.0.0.1:5500"]`.

**Code — API key authentication**
```python
# server/auth.py
import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from server.settings import Settings, get_settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def require_user(
    api_key: Annotated[str | None, Security(api_key_header)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> str:
    """Return the internal user id for a valid key, or reject the request with 401."""
    if api_key is None or not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return "owner"

CurrentUser = Annotated[str, Depends(require_user)]
```

```python
# using it in an endpoint
from server.auth import CurrentUser

@app.get("/me")
async def me(user_id: CurrentUser) -> dict[str, str]:
    return {"user_id": user_id}
```

```bash
curl http://127.0.0.1:8000/me
```

```bash
curl http://127.0.0.1:8000/me -H "X-API-Key: paste-your-key-here"
```

The first returns 401, the second returns `{"user_id":"owner"}`. On the `/docs` page there's now an **Authorize** button
where you paste the key once.

Why `secrets.compare_digest` instead of `==`? A normal `==` stops at the first different character, so it's very slightly
faster for wrong guesses that share a prefix. Attackers can measure that ("timing attack"). `compare_digest` always takes
the same time.

You can also protect **every** route of a router or app at once:
```python
from fastapi import APIRouter, Depends
from server.auth import require_user

router = APIRouter(dependencies=[Depends(require_user)])
```

**Code — CORS**
```python
from fastapi.middleware.cors import CORSMiddleware
from server.settings import get_settings

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,   # exact origins; never ["*"] for an API that does things
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key"],
)
```

If you serve your web page **from the same FastAPI app** (Lesson 10), the page and API share an origin and you don't need
CORS at all. You need it when the frontend runs on a different port or domain, like the Next.js dev server on port 3000.

**Overview — sessions and JWTs (for multi-user apps)**

| | API key (this course) | Session cookie | JWT (JSON Web Token) |
|---|---|---|---|
| What the client holds | A long secret string | A random session id in a cookie | A signed token containing claims (`sub`, `exp`) |
| Where state lives | Server config | Server-side session store | Inside the token itself |
| Revoking access | Change the key | Delete the session | Hard until it expires (keep expiry short) |
| Best for | One person, scripts, bots | Classic web apps with login pages | APIs used by mobile apps / several services |

A JWT is three base64 parts `header.payload.signature`. The server signs it with a secret; anyone can *read* the payload,
but nobody can *change* it without breaking the signature. In Python, the `pyjwt` package does this with
`jwt.encode(payload, secret, algorithm="HS256")` and `jwt.decode(token, secret, algorithms=["HS256"])`.

A full login system also needs password hashing (e.g. the `pwdlib` or `argon2-cffi` packages), signup, password reset and
rate limiting. That's a lot of security-critical code. If you ever open your app to other people, strongly consider a
hosted auth provider (Auth0, Clerk, Supabase Auth, or "Sign in with Google" via OAuth from Section 2) instead of
building it yourself.

**Common mistakes**
- `allow_origins=["*"]` on an API that can send email. Any website you visit could try to call it from your browser.
- Putting the API key in the URL (`?key=...`). URLs end up in logs and browser history. Use a header.
- Forgetting that a static web page's JavaScript is fully visible to whoever loads it. A key typed by the user and kept in `localStorage` is OK for a personal tool on your own machine; a key *hard-coded* in the JS file is public.
- Debugging a "CORS error" with `curl`. `curl` ignores CORS; open the browser's DevTools → Network tab instead.

**Exercises**
1. Add a `require_user` dependency to all routes in your tasks API from Lesson 6 using an `APIRouter`.
2. Support **two** keys (e.g. one for your phone shortcut, one for the web page) mapped to the same user, so you can revoke one without the other. Store them in settings as `api_keys: list[str]`.
3. Write a pytest test using FastAPI's `TestClient` that checks `/me` returns 401 without a key and 200 with one. (Hint: `app.dependency_overrides[get_settings] = lambda: Settings(api_key="test")`.)

**Check yourself**
- What happens to the endpoint function if a dependency raises `HTTPException`?
- Who enforces CORS: the server or the browser?
- Name one advantage and one disadvantage of JWTs compared with server-side sessions.

---

### Lesson 8: A Streaming Agent Core

**Concepts**
- Without streaming, the user stares at "Thinking..." for 10–30 seconds and then a wall of text appears. With
  **streaming**, the first words appear in under a second and the rest flows in, which *feels* several times faster even
  though the total time is the same.
- The Claude API can stream a response as a series of **events** (`client.messages.stream(...)` in the Python SDK). Text
  arrives in small pieces called **deltas**.
- An agent turn isn't only text. It's text, then maybe tool calls, then tool results, then more text. So instead of
  streaming raw strings, the agent core will **yield structured events** that any interface can render:

| Event | Example | Interface shows |
|---|---|---|
| `text` | `{"type": "text", "text": "You have "}` | Append to the reply bubble |
| `tool_start` | `{"type": "tool_start", "name": "list_events"}` | "Checking your calendar..." |
| `tool_end` | `{"type": "tool_end", "name": "list_events", "ok": true}` | Tick or cross next to the status |
| `confirm` | `{"type": "confirm", "action_id": "a1b2...", "summary": "Send email to..."}` | Approve / Cancel buttons |
| `error` | `{"type": "error", "message": "The AI service is busy..."}` | Friendly error message |
| `done` | `{"type": "done"}` | Re-enable the input box |

- An **async generator** (an `async def` function containing `yield`) produces these events one by one; callers consume
  it with `async for`. It's the async version of the generators you've used with `for`.

**Code — async generators in 30 seconds**
```python
import asyncio

async def countdown(n: int):
    while n > 0:
        yield n                    # hand one value to the caller, then pause here
        await asyncio.sleep(0.5)
        n -= 1

async def main():
    async for number in countdown(3):
        print(number)

asyncio.run(main())
```

**Code — streaming plain text from Claude**
```python
# stream_demo.py
import asyncio
from anthropic import AsyncAnthropic

client = AsyncAnthropic()          # reads ANTHROPIC_API_KEY from the environment

async def main():
    async with client.messages.stream(
        model="claude-haiku-5-5",
        max_tokens=500,
        messages=[{"role": "user", "content": "Give me 5 tips for a productive Monday."}],
    ) as stream:
        async for text in stream.text_stream:
            print(text, end="", flush=True)     # flush=True shows each piece immediately
        final = await stream.get_final_message()
    print("\n\nTokens used:", final.usage.output_tokens)

asyncio.run(main())
```

`stream.text_stream` gives you only the text pieces. To also see **tool calls starting**, iterate over the stream itself:
it yields helper events like `text` (with `.text`, the new piece) plus the raw API events like `content_block_start`.
After the loop, `get_final_message()` returns the complete message, exactly like a non-streaming `messages.create` call,
so the rest of your agent loop (checking `stop_reason`, running tools) doesn't change.

**Code — a minimal `tools.py` (if you want to test in isolation)**

Your real `organizer/tools.py` from Sections 3 and 5 already has tool schemas and a way to run a tool by name. If yours
is shaped differently, either adapt the names below or use this stub while learning:

```python
# organizer/tools.py (stub for testing; your real one has many more tools)
import json

TASKS = [
    {"id": "a1", "title": "Write quarterly report", "priority": 1},
    {"id": "b2", "title": "Book dentist", "priority": 3},
]

def list_tasks() -> str:
    return json.dumps(TASKS)

def send_email(to: str, subject: str, body: str) -> str:
    return f"(pretend) Email sent to {to} with subject {subject!r}."

FUNCTIONS = {"list_tasks": list_tasks, "send_email": send_email}

TOOL_SCHEMAS = [
    {
        "name": "list_tasks",
        "description": "List the user's pending tasks with id, title and priority (1 = high).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "send_email",
        "description": "Send an email on the user's behalf. The user must approve it before it is sent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient email address"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
    },
]

RISKY_TOOLS = {"send_email"}

def run_tool(name: str, args: dict) -> str:
    if name not in FUNCTIONS:
        raise ValueError(f"Unknown tool: {name}")
    return FUNCTIONS[name](**args)
```

**Code — the streaming agent core**
```python
# organizer/streaming.py
"""The agent loop from Section 3, rewritten to yield events while it works."""
import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Any

from anthropic import AsyncAnthropic

from organizer import confirmations
from organizer.tools import RISKY_TOOLS, TOOL_SCHEMAS, run_tool

MODEL = "claude-sonnet-5-5"
MAX_TOKENS = 2048
MAX_TURNS = 8                      # safety limit on model <-> tool round trips

SYSTEM_PROMPT = (
    "You are Work Organizer, a concise personal assistant. "
    "Use tools to look things up instead of guessing. "
    "Some tools (like sending email) need the user's approval: when a tool result says an action "
    "is waiting for approval, tell the user what you prepared and that they need to approve it. "
    "Never claim such an action is done."
)

Event = dict[str, Any]

client = AsyncAnthropic()
# In-memory history keeps this lesson self-contained.
# Swap these for your Section 4 memory functions so history survives restarts.
HISTORY: dict[str, list[dict[str, Any]]] = defaultdict(list)
NOTES: dict[str, list[str]] = defaultdict(list)
LOCKS: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

def add_note(user_id: str, note: str) -> None:
    """Record something the app did (e.g. 'the user approved the email') for the next turn."""
    NOTES[user_id].append(note)

async def stream_agent(user_id: str, message: str) -> AsyncIterator[Event]:
    """Run the agent for one user message, yielding events as they happen."""
    async with LOCKS[user_id]:                 # one conversation turn per user at a time
        messages = HISTORY[user_id]
        start_len = len(messages)
        notes = NOTES.pop(user_id, [])
        if notes:
            message = "\n".join(f"[App note: {n}]" for n in notes) + "\n\n" + message
        messages.append({"role": "user", "content": message})
        try:
            for _ in range(MAX_TURNS):
                turn_had_text = False
                async with client.messages.stream(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    system=SYSTEM_PROMPT,
                    tools=TOOL_SCHEMAS,
                    messages=messages,
                ) as stream:
                    async for event in stream:
                        if event.type == "text":
                            turn_had_text = True
                            yield {"type": "text", "text": event.text}
                        elif event.type == "content_block_start" and event.content_block.type == "tool_use":
                            yield {"type": "tool_start", "name": event.content_block.name}
                    final = await stream.get_final_message()

                messages.append({"role": "assistant", "content": final.content})
                if final.stop_reason != "tool_use":
                    break

                if turn_had_text:
                    yield {"type": "text", "text": "\n\n"}     # keep text from separate turns apart

                tool_results = []
                for block in final.content:
                    if block.type != "tool_use":
                        continue
                    if block.name in RISKY_TOOLS:
                        action = await asyncio.to_thread(
                            confirmations.create, user_id, block.name, block.input
                        )
                        yield {
                            "type": "confirm",
                            "action_id": action.id,
                            "tool": block.name,
                            "summary": action.summary,
                        }
                        content = (
                            f"Not executed yet. Action {action.id} is waiting for the user to approve it."
                        )
                        is_error = False
                    else:
                        try:
                            content = str(await asyncio.to_thread(run_tool, block.name, block.input))
                            is_error = False
                        except Exception as e:
                            content = f"Tool error: {e}"
                            is_error = True
                        yield {"type": "tool_end", "name": block.name, "ok": not is_error}
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": content,
                        "is_error": is_error,
                    })
                messages.append({"role": "user", "content": tool_results})
            else:
                yield {"type": "text", "text": "\n\n(I stopped after too many steps. Try a simpler request.)"}
        except BaseException:
            # Error or client disconnected mid-turn: roll back this turn so history stays valid
            # (an assistant tool_use without a matching tool_result would break every later call).
            del messages[start_len:]
            raise
    yield {"type": "done"}

async def collect_reply(user_id: str, message: str) -> tuple[str, list[Event]]:
    """For interfaces that don't stream: return (full reply text, confirm events)."""
    parts: list[str] = []
    confirms: list[Event] = []
    async for event in stream_agent(user_id, message):
        if event["type"] == "text":
            parts.append(event["text"])
        elif event["type"] == "confirm":
            confirms.append(event)
    return "".join(parts).strip(), confirms
```

Read it slowly. It's the same loop as Section 3 — call the model, if it wants tools run them and send the results back,
repeat until it stops — with four additions:
1. `yield` statements report progress as it happens.
2. Risky tools go through `confirmations` (Lesson 4) instead of running.
3. A per-user **lock** stops two messages from the same user (say, from phone and laptop at once) from interleaving their history.
4. If anything fails mid-turn, the turn is **rolled back**, so one network blip doesn't corrupt the conversation forever.

From now on this is your agent's single core. Your old `run_agent` can become a thin wrapper:
```python
# organizer/agent.py
import asyncio
from organizer.streaming import collect_reply

def run_agent(user_id: str, message: str) -> str:
    reply, _confirms = asyncio.run(collect_reply(user_id, message))
    return reply
```
(`asyncio.run` can't be called from inside a running event loop, so async code — bots, FastAPI — should
`await collect_reply(...)` or iterate `stream_agent(...)` directly instead of calling `run_agent`.)

**Code — streaming in the terminal**

The core of a streaming CLI turn with `rich.live.Live`, which redraws the reply as it grows:
```python
# cli/main.py (excerpt)
import asyncio
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from organizer.streaming import stream_agent

console = Console()

async def one_turn(user: str, text: str) -> list[dict]:
    reply, confirms = "", []
    with Live(Markdown("_thinking..._"), console=console, refresh_per_second=12) as live:
        async for event in stream_agent(user, text):
            match event["type"]:
                case "text":
                    reply += event["text"]
                    live.update(Markdown(reply))
                case "tool_start":
                    console.print(f"[dim]  using {event['name']}...[/dim]")   # prints above the live area
                case "confirm":
                    confirms.append(event)
    return confirms
```
In the `chat` loop call `confirms = asyncio.run(one_turn(user, text))`, then **after** the live display has finished,
ask about each confirm with `Confirm.ask("Approve?", default=False)` and call `confirmations.approve(...)` or
`confirmations.reject(...)`. (Prompting inside `Live` garbles the screen.)

**Common mistakes**
- Building the reply with `print(text)` instead of `print(text, end="", flush=True)` — every piece lands on a new line, or nothing shows until the end.
- Forgetting `await stream.get_final_message()` and trying to read tool calls from the text deltas. Let the SDK assemble the final message.
- Appending a new `user` message after an `assistant` message that contains `tool_use` blocks *without* the matching `tool_result`s — the API rejects every later request for that user. That's what the rollback prevents.
- Calling `run_agent` (which uses `asyncio.run`) from inside an async function — `RuntimeError: asyncio.run() cannot be called from a running event loop`.
- Holding the lock while waiting for the user to tap Approve. Confirmations are *outside* the turn on purpose; the turn ends and a new one starts later.

**Exercises**
1. Add a `usage` event at the end of `stream_agent` with the total input and output tokens across all turns, and show it dimmed in the CLI.
2. Make the CLI show a friendlier label than the raw tool name (e.g. `list_tasks` → "Looking at your tasks"). Keep the labels in one dictionary.
3. Write a test that replaces `organizer.streaming.client` with a fake object so you can test `stream_agent` without calling the real API. (This is hard — try for 30 minutes, then read the solution.)

**Check yourself**
- What's the difference between `stream.text_stream` and iterating over `stream` directly?
- Why does a risky tool's result say "not executed yet" rather than being left out?
- What would go wrong without the per-user lock?

---

### Lesson 9: Streaming with Server-Sent Events (SSE)

**Concepts**
- A normal HTTP response is sent all at once. A **streaming response** keeps the connection open and sends chunks as
  they're ready.
- **Server-Sent Events (SSE)** is a simple, standard text format for streaming events from server to browser over plain
  HTTP. Each event is one or more `data:` lines followed by a **blank line**:
  ```
  data: {"type": "text", "text": "Hello"}

  data: {"type": "text", "text": " there"}

  data: {"type": "done"}

  ```
- Content type `text/event-stream`. The connection stays open until the server finishes.
- Browsers have a built-in `EventSource` class for SSE, but it only supports **GET** with no custom headers. A chat needs
  **POST** (to send the message) and an `X-API-Key` header, so you'll read the stream with `fetch` instead (Lesson 10).
  Both read the same format.
- SSE is **one-way** (server → client). For two-way, see WebSockets in Lesson 13. For chat, SSE is usually all you need:
  the client sends each message with a normal POST, and the reply streams back.

**Code — a fake stream to see SSE work**
```python
# server/sse_demo.py
import asyncio
import json

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse

app = FastAPI()

def sse(event: dict) -> str:
    """Format one event in SSE wire format."""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

@app.get("/demo/stream")
async def demo_stream() -> StreamingResponse:
    async def generate():
        for word in "Streaming makes your assistant feel fast and alive.".split():
            yield sse({"type": "text", "text": word + " "})
            await asyncio.sleep(0.25)
        yield sse({"type": "done"})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

@app.get("/", response_class=HTMLResponse)
async def page() -> str:
    return """<!doctype html>
<p id="out"></p>
<script>
  const out = document.getElementById("out");
  const es = new EventSource("/demo/stream");
  es.onmessage = (e) => {
    const evt = JSON.parse(e.data);
    if (evt.type === "text") out.textContent += evt.text;
    if (evt.type === "done") es.close();   // otherwise EventSource reconnects and starts again!
  };
</script>"""
```

```bash
fastapi dev server/sse_demo.py
```

Open `http://127.0.0.1:8000/` and watch the words appear. Then see the raw format in the terminal (`-N` turns off
curl's buffering):

```bash
curl -N http://127.0.0.1:8000/demo/stream
```

The headers matter: `Cache-Control: no-cache` stops caches holding the stream, and `X-Accel-Buffering: no` tells nginx
(a common reverse proxy in front of servers) not to buffer the whole response before sending it.

**Code — the real streaming `/chat` endpoint**
```python
# server/main.py (first version)
import json
import logging
from typing import Annotated

import anthropic
from fastapi import Depends, FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from organizer.streaming import stream_agent
from server.auth import require_user

log = logging.getLogger("server")
app = FastAPI(title="Work Organizer API")

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)

def sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

def friendly_error(exc: Exception) -> str:
    if isinstance(exc, anthropic.RateLimitError):
        return "I'm being rate-limited right now. Please try again in a minute."
    if isinstance(exc, anthropic.APIConnectionError):
        return "I couldn't reach the AI service. Check your internet connection and try again."
    if isinstance(exc, anthropic.APIStatusError) and exc.status_code >= 500:
        return "The AI service is having trouble. Please try again shortly."
    return "Something went wrong on my side. The details are in the server log."

async def event_stream(user_id: str, message: str):
    try:
        async for event in stream_agent(user_id, message):
            yield sse(event)
    except Exception as exc:
        log.exception("Agent failed during stream")
        yield sse({"type": "error", "message": friendly_error(exc)})
        yield sse({"type": "done"})

@app.post("/chat")
async def chat(
    body: ChatRequest,
    user_id: Annotated[str, Depends(require_user)],
) -> StreamingResponse:
    return StreamingResponse(
        event_stream(user_id, body.message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
```

```bash
fastapi dev server/main.py
```

```bash
curl -N -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -H "X-API-Key: paste-your-key-here" -d '{"message": "What are my tasks?"}'
```

You should see `data:` lines arrive one by one: some `tool_start`/`tool_end`, then many small `text` events, then `done`.

**Why errors become events.** Once the first chunk is sent, the HTTP status code (200) has already gone to the client. You
can't change it to 500 halfway through. So errors that happen during the stream are sent as an `error` event, and the
client shows them nicely. Errors *before* streaming starts (bad API key → 401, invalid body → 422) still use normal status
codes, because dependencies and validation run first.

**What happens when the user closes the tab?** The server notices the disconnect and cancels the generator. Inside
`stream_agent` that raises an exception at the current `yield` or `await`, which triggers the rollback from Lesson 8 and
closes the connection to Claude, so you stop paying for tokens nobody will read.

**Common mistakes**
- Forgetting the blank line: `f"data: {x}\n"` instead of `\n\n`. The client never sees a complete event.
- Sending multi-line text in one `data:` line without JSON-encoding it. A raw newline inside the text breaks the format. `json.dumps` turns newlines into `\n` escapes.
- Testing with `curl` without `-N` and thinking streaming is broken because everything arrives at once.
- A proxy, a compression middleware (`GZipMiddleware`) or a hosting platform buffering the whole response. If streaming works locally but not deployed, look there first.
- Using `EventSource` for the chat POST. It can't send a body or headers.

**Exercises**
1. Send a comment line `: ping\n\n` every 15 seconds while a long tool runs, so proxies don't close an "idle" connection. (Lines starting with `:` are ignored by SSE clients.) Hint: wrap the agent events with `asyncio.wait_for` on the next event.
2. Add `event: <type>` lines to your SSE output (so the format becomes `event: text\ndata: {...}\n\n`) and update the demo page to use `es.addEventListener("text", ...)`.
3. Add a non-streaming `POST /chat-once` endpoint that returns `{"reply": ..., "pending_actions": [...]}` using `collect_reply`. Useful for phone shortcuts that can't read streams.

**Check yourself**
- What exactly marks the end of one SSE event?
- Why can't the server send a 500 status if the agent fails halfway through a stream?
- Why does the chat page use `fetch` instead of `EventSource`?

---

## Part E: Web Frontend

### Lesson 10: A Plain HTML and JavaScript Chat Page

**Concepts**
- Before reaching for React, build the chat page with plain HTML, CSS and JavaScript. It's ~150 lines, has no build step,
  and teaches exactly what frameworks do for you.
- The **DOM** is the browser's tree of page elements. JavaScript finds elements (`document.querySelector`), creates them
  (`document.createElement`), and changes them (`el.textContent = ...`).
- `fetch()` returns a `Response`; `response.body.getReader()` lets you read the body **chunk by chunk** as it streams.
- Network chunks don't line up with SSE events. One chunk can contain half an event or three events. So you keep a
  **buffer**, append each chunk, and cut out complete events at every `\n\n`.
- **Security**: always insert model text with `textContent`, never `innerHTML`. The model's text can contain anything
  (including text copied from a malicious email). With `innerHTML`, `<img src=x onerror=...>` would run code in your page.
- Serving the page **from FastAPI itself** means same origin → no CORS setup needed.

**Code — serve static files from FastAPI**

Add this at the **very end** of `server/main.py`, after all API routes (a mount at `/` catches everything, so routes added
after it would be hidden):
```python
from pathlib import Path
from fastapi.staticfiles import StaticFiles

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
```
`html=True` makes `/` serve `index.html`.

**Code — the page**
```html
<!-- server/static/index.html -->
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Work Organizer</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 0; background: #f5f5f7; }
    main { max-width: 760px; margin: 0 auto; height: 100vh; display: flex; flex-direction: column; }
    #log { flex: 1; overflow-y: auto; padding: 16px; }
    .msg { margin: 8px 0; padding: 10px 14px; border-radius: 12px; white-space: pre-wrap; }
    .user { background: #0b63f6; color: white; margin-left: 20%; }
    .assistant { background: white; border: 1px solid #e3e3e8; margin-right: 10%; }
    .thinking .text, .tools { color: #777; } .tools { font-size: 0.85em; }
    .confirm { margin-top: 10px; padding: 10px; border: 1px solid #f0b400; background: #fff8e1; border-radius: 8px; }
    .error { color: #b00020; }
    form { display: flex; gap: 8px; padding: 12px; border-top: 1px solid #ddd; background: white; }
    textarea { flex: 1; resize: none; font: inherit; padding: 8px; }
  </style>
</head>
<body>
  <main>
    <div id="log" aria-live="polite"></div>
    <form id="chat-form">
      <textarea id="message" rows="2" placeholder="Ask your assistant... (Enter to send, Shift+Enter for a new line)"></textarea>
      <button id="send" type="submit">Send</button>
    </form>
  </main>
  <script src="app.js"></script>
</body>
</html>
```

```javascript
// server/static/app.js
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message");
const sendButton = document.querySelector("#send");
const log = document.querySelector("#log");

function getApiKey() {
  let key = localStorage.getItem("apiKey");
  if (!key) {
    key = prompt("Enter your API key:");
    if (key) localStorage.setItem("apiKey", key);
  }
  return key;
}

function scrollToBottom() {
  log.scrollTop = log.scrollHeight;
}

function addUserMessage(text) {
  const div = document.createElement("div");
  div.className = "msg user";
  div.textContent = text;
  log.appendChild(div);
  scrollToBottom();
}

function addAssistantMessage() {
  const el = document.createElement("div");
  el.className = "msg assistant thinking";
  const tools = document.createElement("div");
  tools.className = "tools";
  const text = document.createElement("div");
  text.className = "text";
  text.textContent = "Thinking...";
  el.append(tools, text);
  log.appendChild(el);
  scrollToBottom();
  return { el, tools, text };
}

// Read a fetch() Response as a stream of SSE events.
async function* readSSE(response) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let boundary;
    while ((boundary = buffer.indexOf("\n\n")) !== -1) {
      const rawEvent = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      for (const line of rawEvent.split("\n")) {
        if (line.startsWith("data: ")) yield JSON.parse(line.slice(6));
      }
    }
  }
}

function addConfirmCard(container, evt) {
  const card = document.createElement("div");
  card.className = "confirm";
  const summary = document.createElement("div");
  summary.textContent = "Needs your approval:\n\n" + evt.summary;
  const approve = document.createElement("button");
  approve.textContent = "Approve";
  const cancel = document.createElement("button");
  cancel.textContent = "Cancel";
  const result = document.createElement("div");
  approve.onclick = () => decide(evt.action_id, "approve", card, result);
  cancel.onclick = () => decide(evt.action_id, "reject", card, result);
  card.append(summary, approve, cancel, result);
  container.appendChild(card);
  scrollToBottom();
}

async function decide(actionId, decision, card, resultEl) {
  card.querySelectorAll("button").forEach((b) => (b.disabled = true));
  resultEl.textContent = decision === "approve" ? "Running..." : "Cancelling...";
  try {
    const res = await fetch(`/actions/${encodeURIComponent(actionId)}/${decision}`, {
      method: "POST",
      headers: { "X-API-Key": getApiKey() },
    });
    const data = await res.json();
    resultEl.textContent = res.ok ? data.result : data.detail || "Failed.";
  } catch {
    resultEl.textContent = "Network error. Check the action status before trying again.";
  }
}

async function sendMessage(message) {
  addUserMessage(message);
  const reply = addAssistantMessage();
  let started = false;
  sendButton.disabled = true;
  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-API-Key": getApiKey() },
      body: JSON.stringify({ message }),
    });
    if (res.status === 401) {
      localStorage.removeItem("apiKey");
      throw new Error("Wrong API key. Send again to re-enter it.");
    }
    if (!res.ok) throw new Error(`Server error (${res.status}).`);

    for await (const evt of readSSE(res)) {
      switch (evt.type) {
        case "text":
          if (!started) {
            started = true;
            reply.text.textContent = "";
            reply.el.classList.remove("thinking");
          }
          reply.text.textContent += evt.text;
          break;
        case "tool_start": {
          const line = document.createElement("div");
          line.textContent = `Using ${evt.name}...`;
          line.dataset.tool = evt.name;
          reply.tools.appendChild(line);
          break;
        }
        case "tool_end": {
          const lines = reply.tools.querySelectorAll(`[data-tool="${evt.name}"]`);
          const line = lines[lines.length - 1];
          if (line) line.textContent = `${evt.name} ${evt.ok ? "done" : "failed"}`;
          break;
        }
        case "confirm":
          addConfirmCard(reply.el, evt);
          break;
        case "error":
          reply.el.classList.remove("thinking");
          reply.text.classList.add("error");
          reply.text.textContent += (started ? "\n\n" : "") + evt.message;
          started = true;
          break;
      }
      scrollToBottom();
    }
  } catch (err) {
    reply.el.classList.remove("thinking");
    reply.text.classList.add("error");
    reply.text.textContent = err.message;
  } finally {
    sendButton.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message || sendButton.disabled) return;
  input.value = "";
  sendMessage(message);
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});
```

You also need the two **action endpoints** the buttons call. Add them to `server/main.py` *before* the static mount:
```python
import asyncio
from fastapi import HTTPException
from organizer import confirmations
from organizer.streaming import add_note

class ActionResult(BaseModel):
    result: str

@app.post("/actions/{action_id}/approve")
async def approve_action(action_id: str, user_id: Annotated[str, Depends(require_user)]) -> ActionResult:
    action = await asyncio.to_thread(confirmations.get, action_id)
    if action is None or action.user_id != user_id:
        raise HTTPException(status_code=404, detail="Action not found")
    result = await asyncio.to_thread(confirmations.approve, action_id, user_id)
    add_note(user_id, f"The user approved action {action_id} ({action.tool_name}). Result: {result}")
    return ActionResult(result=result)

@app.post("/actions/{action_id}/reject")
async def reject_action(action_id: str, user_id: Annotated[str, Depends(require_user)]) -> ActionResult:
    result = await asyncio.to_thread(confirmations.reject, action_id, user_id)
    add_note(user_id, f"The user cancelled action {action_id}.")
    return ActionResult(result=result)
```

The `add_note` calls mean that next time you chat, the agent knows the email really was sent (or cancelled), so it
doesn't offer to send it again.

Start the server and open `http://127.0.0.1:8000/`:

```bash
fastapi dev server/main.py
```

Ask "What are my tasks?" and watch tool activity and then the reply stream in. Then ask "Email dana@example.com that the
report is late" and try both buttons.

**Common mistakes**
- Using `innerHTML` to show replies. It's an injection hole, and it also breaks on any `<` in the text.
- Splitting chunks on `\n` instead of buffering until `\n\n` — works locally, breaks randomly on slower networks.
- Not disabling the Send button during a reply — the user sends twice and the second request waits on the per-user lock.
- Mounting `StaticFiles` at `/` *before* defining API routes — every API call returns 404 or the HTML page.
- Forgetting `white-space: pre-wrap` — the model's line breaks and lists collapse into one paragraph.

**Exercises**
1. Render replies as Markdown safely: load `marked` and `DOMPurify` from a CDN and, **only after the `done` event**, set `reply.text.innerHTML = DOMPurify.sanitize(marked.parse(fullText))`.
2. Add a "Stop" button that cancels the stream using an `AbortController` (`fetch(url, { signal: controller.signal })`). Check in the server log that the agent turn was rolled back.
3. Show the time each assistant message finished, and how many seconds it took.

**Check yourself**
- Why must you buffer chunks before parsing SSE events?
- What could an attacker do if model output were inserted with `innerHTML`?
- Why does the static mount have to come after the API routes?

---

### Lesson 11: React Basics

**Concepts**
The plain-JS page works, but notice how much code is spent *finding and updating* elements by hand. As UIs grow (task
board, settings, history sidebar) that gets messy. **React** flips the approach: you describe what the screen should look
like for the current **state**, and React updates the DOM for you when the state changes.

| Concept | What it is | Plain-JS equivalent |
|---|---|---|
| **Component** | A function that returns JSX (HTML-like markup) | A function that builds DOM elements |
| **JSX** | `<div className="msg">{text}</div>` inside JavaScript/TypeScript | `createElement` + `textContent` |
| **Props** | Inputs passed to a component, like function arguments | Function parameters |
| **State** (`useState`) | Data that, when changed, re-renders the component | Variables + manual DOM updates |
| **Effect** (`useEffect`) | Code that runs *after* render to sync with the outside world (fetch, timers, scrolling) | Code you run after updating the DOM |
| **Key** | A stable id for each item in a list | — |

JSX escapes text automatically: `{reply}` is inserted like `textContent`, so the `innerHTML` danger from Lesson 10
doesn't exist unless you deliberately use `dangerouslySetInnerHTML`.

**Set up a practice project with Vite**

```bash
npm create vite@latest react-basics -- --template react-ts
```

```bash
cd react-basics
```

```bash
npm install
```

```bash
npm run dev
```

Open the URL it prints (usually `http://localhost:5173`). Edit `src/App.tsx` and the page updates instantly.

**Code — components and props**
```tsx
// src/App.tsx
type Task = { id: string; title: string; priority: 1 | 2 | 3 };

function PriorityBadge({ priority }: { priority: Task["priority"] }) {
  const labels = { 1: "High", 2: "Medium", 3: "Low" };
  return <span className={`badge p${priority}`}>{labels[priority]}</span>;
}

function TaskItem({ task }: { task: Task }) {
  return (
    <li>
      {task.title} <PriorityBadge priority={task.priority} />
    </li>
  );
}

function TaskList({ tasks }: { tasks: Task[] }) {
  if (tasks.length === 0) return <p>Nothing to do!</p>;
  return (
    <ul>
      {tasks.map((t) => (
        <TaskItem key={t.id} task={t} />
      ))}
    </ul>
  );
}

export default function App() {
  const tasks: Task[] = [
    { id: "a1", title: "Write report", priority: 1 },
    { id: "b2", title: "Book dentist", priority: 3 },
  ];
  return (
    <main>
      <h1>My tasks</h1>
      <TaskList tasks={tasks} />
    </main>
  );
}
```

Rules you just used: component names start with a **capital letter**; a component returns **one** root element; use
`className` (not `class`); JavaScript goes inside `{ }`; lists use `.map` and every item needs a unique `key`.

**Code — state with `useState`**
```tsx
import { useState } from "react";

function Counter() {
  const [count, setCount] = useState(0);          // [current value, setter]
  return <button onClick={() => setCount(count + 1)}>Clicked {count} times</button>;
}

function NewTaskForm({ onAdd }: { onAdd: (title: string) => void }) {
  const [title, setTitle] = useState("");
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (!title.trim()) return;
        onAdd(title.trim());
        setTitle("");
      }}
    >
      <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="New task" />
      <button type="submit">Add</button>
    </form>
  );
}
```

The input is **controlled**: its value always comes from state, and every keystroke updates the state. `NewTaskForm`
doesn't own the task list — it calls the `onAdd` **callback prop**, and the parent updates its own state. This is called
**lifting state up**: state lives in the closest common parent of the components that need it.

**Never mutate state.** Always create a new array or object:
```tsx
const [tasks, setTasks] = useState<Task[]>([]);

// WRONG: same array object, React doesn't see a change
tasks.push(newTask);
setTasks(tasks);

// RIGHT: new array
setTasks((prev) => [...prev, newTask]);

// Update one item: map to a new array, copy the changed object
setTasks((prev) => prev.map((t) => (t.id === id ? { ...t, priority: 1 } : t)));
```
Use the **function form** `setX(prev => ...)` whenever the new value depends on the old one. It matters during
streaming, where many updates happen quickly.

**Code — effects with `useEffect`**
```tsx
import { useEffect, useState } from "react";

function BackendStatus() {
  const [status, setStatus] = useState<"checking" | "online" | "offline">("checking");

  useEffect(() => {
    const controller = new AbortController();
    fetch("http://localhost:8000/health", { signal: controller.signal })
      .then((res) => setStatus(res.ok ? "online" : "offline"))
      .catch((err) => {
        if (err.name !== "AbortError") setStatus("offline");
      });
    return () => controller.abort();            // cleanup: runs if the component disappears
  }, []);                                       // [] = run once, after the first render

  return <p>Backend: {status}</p>;
}
```

The second argument to `useEffect` is the **dependency array**: `[]` means "once after mount", `[lines]` means "after any
render where `lines` changed (e.g. scroll to the newest message)", and leaving it out means "after every render" (rarely what you want).

For `BackendStatus` to work, your FastAPI CORS settings must allow `http://localhost:5173` (Lesson 7).

**Common mistakes**
- Mutating state (`push`, `obj.x = 1`) and wondering why the screen doesn't update.
- Missing `key` on list items, or using the array index as key for lists that get reordered or deleted from.
- An effect that sets state with no dependency array → render → effect → set state → render... an infinite loop.
- Calling `setCount(count + 1)` several times in a row expecting +3; each call sees the same old `count`. Use `setCount(c => c + 1)`.
- `useState` inside an `if` or a loop. Hooks must be called at the top level of the component, in the same order every render.

**Exercises**
1. Build a `TaskBoard` component with `NewTaskForm`, `TaskList`, and a "done" checkbox on each item. State lives in `TaskBoard`.
2. Load the tasks from your FastAPI `GET /tasks` endpoint (Lesson 6) in a `useEffect`, with a loading message and an error message.
3. Add a filter (`all` / `pending` / `done`) as state, and compute the visible list from the full list during render (don't store the filtered list in state).

**Check yourself**
- What's the difference between props and state?
- Why must you create a new array instead of pushing to the existing one?
- When does an effect with `[]` as its dependency array run? When does its cleanup run?

---

### Lesson 12: Next.js App Router

**Concepts**
- **Next.js** is a React framework: routing by folders, server-side rendering, API routes, and production builds, all set
  up for you. It's what the React docs recommend for full apps.
- The **App Router** (the `app/` folder) maps folders to URLs: `app/page.tsx` is `/`, `app/settings/page.tsx` is
  `/settings`, `app/layout.tsx` wraps every page.
- **Server Components** (the default) run on the server and send HTML. They can read secrets and databases but **can't**
  use state, effects or click handlers. **Client Components** start with `"use client"` and run in the browser; they can
  use `useState`, `useEffect` and events. A chat UI is a Client Component.
- **Route Handlers** (`app/api/.../route.ts`) are small server endpoints inside Next.js. You'll use one as a **proxy** so
  the browser never sees your backend API key: browser → Next.js (`/api/chat`) → FastAPI (`/chat`, with the key added on
  the server).

```
Browser (Chat.tsx) ──POST /api/chat──► Next.js route handler ──POST /chat + X-API-Key──► FastAPI ──► agent
        ▲                                     │
        └──────────── SSE stream piped straight through ◄─────────────────────────────┘
```

**Create the app**

```bash
npx create-next-app@latest web
```

Answer **Yes** to TypeScript and ESLint, **Yes** to the App Router, and accept the other defaults. Then:

```bash
cd web
```

```bash
npm run dev
```

Open `http://localhost:3000`.

**Code — environment variables (server-only)**
```
# web/.env.local   (gitignored by default)
BACKEND_URL=http://127.0.0.1:8000
BACKEND_API_KEY=paste-the-same-API_KEY-as-in-your-python-.env
```

Only variables prefixed with `NEXT_PUBLIC_` are sent to the browser. These two are not, so they stay on the server.

**Code — the proxy route handlers**
```typescript
// web/app/api/chat/route.ts
export async function POST(req: Request) {
  const body = await req.text();
  const upstream = await fetch(`${process.env.BACKEND_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": process.env.BACKEND_API_KEY ?? "",
    },
    body,
  });
  // Pass the SSE stream straight through to the browser.
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("Content-Type") ?? "text/event-stream",
      "Cache-Control": "no-cache",
    },
  });
}
```

Because the browser only talks to Next.js (same origin), there's **no CORS** to configure, and the API key never reaches
the browser.

**Code — SSE reader and types**
```typescript
// web/lib/sse.ts
export type ChatEvent =
  | { type: "text"; text: string }
  | { type: "tool_start"; name: string }
  | { type: "tool_end"; name: string; ok: boolean }
  | { type: "confirm"; action_id: string; tool: string; summary: string }
  | { type: "error"; message: string }
  | { type: "done" };

export async function* readSSE(res: Response): AsyncGenerator<ChatEvent> {
  if (!res.body) return;
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let boundary: number;
    while ((boundary = buffer.indexOf("\n\n")) !== -1) {
      const raw = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      for (const line of raw.split("\n")) {
        if (line.startsWith("data: ")) yield JSON.parse(line.slice(6)) as ChatEvent;
      }
    }
  }
}
```

**Code — the chat component**
```tsx
// web/components/Chat.tsx
"use client";

import { useEffect, useRef, useState } from "react";
import { readSSE } from "@/lib/sse";

type Message = { id: string; role: "user" | "assistant"; text: string; tools: string[]; error?: string };

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Update one message immutably by id (safe even when many updates arrive quickly).
  function patch(id: string, change: (m: Message) => Message) {
    setMessages((prev) => prev.map((m) => (m.id === id ? change(m) : m)));
  }

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setBusy(true);
    const replyId = crypto.randomUUID();
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: "user", text, tools: [] },
      { id: replyId, role: "assistant", text: "", tools: [] },
    ]);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      if (!res.ok) throw new Error(`Server error (${res.status})`);
      for await (const evt of readSSE(res)) {
        if (evt.type === "text") patch(replyId, (m) => ({ ...m, text: m.text + evt.text }));
        if (evt.type === "tool_start") patch(replyId, (m) => ({ ...m, tools: [...m.tools, `Using ${evt.name}...`] }));
        if (evt.type === "error") patch(replyId, (m) => ({ ...m, error: evt.message }));
        // "confirm" events: see Exercise 1
      }
    } catch (err) {
      patch(replyId, (m) => ({ ...m, error: (err as Error).message }));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="chat">
      <div className="log">
        {messages.map((m) => (
          <div key={m.id} className={`msg ${m.role}`}>
            {m.tools.map((t, i) => <div key={i} className="tools">{t}</div>)}
            <div className="text">{m.text || (m.role === "assistant" && busy && !m.error ? "Thinking..." : "")}</div>
            {m.error && <div className="error">{m.error}</div>}
          </div>
        ))}
        <div ref={endRef} />
      </div>
      <form onSubmit={(e) => { e.preventDefault(); send(); }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          placeholder="Ask your assistant..."
          rows={2}
        />
        <button type="submit" disabled={busy}>Send</button>
      </form>
    </div>
  );
}
```

```tsx
// web/app/page.tsx   (a Server Component that renders the Client Component)
import Chat from "@/components/Chat";

export default function Home() {
  return (
    <main style={{ maxWidth: 760, margin: "0 auto", padding: 16 }}>
      <h1>Work Organizer</h1>
      <Chat />
    </main>
  );
}
```

Add some CSS to `web/app/globals.css` (reuse the styles from Lesson 10: `.msg`, `.user`, `.assistant`, `.confirm`, and
`white-space: pre-wrap` on `.text`). With FastAPI running on port 8000 and `npm run dev` on 3000, open
`http://localhost:3000` and chat.

**Common mistakes**
- Forgetting `"use client"` at the top of a component that uses `useState` — Next.js errors that hooks only work in Client Components.
- Putting the backend key in `NEXT_PUBLIC_BACKEND_API_KEY` — the `NEXT_PUBLIC_` prefix ships it to every visitor's browser.
- Editing `.env.local` and not restarting `npm run dev` — environment variables are read at startup.
- Awaiting `upstream.json()` in the chat proxy instead of passing `upstream.body` through — the stream is collected into one blob and streaming is lost.
- Updating streaming state with `setMessages([...messages, ...])` using the variable captured when `send` started — later updates overwrite earlier ones. Use the function form (the `patch` helper does).

**Exercises**
1. Handle `confirm` events: store `{ actionId, summary, result? }` on the message, render Approve / Cancel buttons, and add a proxy route handler `app/api/actions/[id]/[decision]/route.ts` that forwards to FastAPI with the key. (In current Next.js, a route handler's second argument is `{ params }` where `params` is a **Promise**: `const { id, decision } = await params;`.)
2. Add a `/tasks` page (`app/tasks/page.tsx`) that is a **Server Component**: it fetches `GET {BACKEND_URL}/tasks` directly on the server (with the key) and renders the list. No `useEffect` needed.
3. Persist the visible messages in `localStorage` so a page refresh doesn't wipe them (load in a `useEffect` on mount, save in another effect when `messages` changes).

**Check yourself**
- What's the difference between a Server Component and a Client Component, and which one can hold secrets?
- Why does the browser call `/api/chat` instead of calling FastAPI directly?
- Why does the chat proxy pass `upstream.body` through instead of awaiting `upstream.json()`?

---

### Lesson 13: WebSockets (Overview)

**Concepts**
A **WebSocket** is a long-lived, **two-way** connection between browser and server. Either side can send a message at
any time, until one closes it.

| | Plain request/response | SSE | WebSocket |
|---|---|---|---|
| Direction | Client asks, server answers once | Server → client stream | Both ways, any time |
| Protocol | HTTP | HTTP | Starts as HTTP, upgrades to `ws://` / `wss://` |
| Custom headers from browser | Yes (`fetch`) | Yes with `fetch`; no with `EventSource` | No (send credentials in the first message) |
| Reconnects automatically | — | `EventSource` does | No, you write it |
| Works through most proxies | Yes | Yes | Usually, sometimes needs config |
| Good for | Normal API calls | **Streaming chat replies**, live status | Multiplayer, collaborative editing, live voice, server pushing *unprompted* updates |

**Rule of thumb:** for a chat assistant, POST + SSE is simpler and enough. Reach for WebSockets when the server must push
things the client didn't ask for (e.g. "your 3pm meeting moved" while the page is open), or for real-time audio.

**Code — a WebSocket chat endpoint in FastAPI**
```python
# add to server/main.py (before the static mount)
import secrets
from fastapi import WebSocket, WebSocketDisconnect
from server.settings import get_settings

@app.websocket("/ws")
async def websocket_chat(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        # Browsers can't set custom headers on WebSockets, so the first message must authenticate.
        hello = await websocket.receive_json()
        key = str(hello.get("api_key", ""))
        if not secrets.compare_digest(key.encode(), get_settings().api_key.encode()):
            await websocket.close(code=1008)          # 1008 = policy violation
            return
        user_id = "owner"
        await websocket.send_json({"type": "ready"})

        while True:
            data = await websocket.receive_json()
            if data.get("type") == "message":
                async for event in stream_agent(user_id, str(data.get("text", ""))):
                    await websocket.send_json(event)
            # approve / reject messages could be handled here too, over the same socket
    except WebSocketDisconnect:
        pass                                           # the user closed the tab; nothing to do
```

**Code — the browser side**
```javascript
const ws = new WebSocket(`ws://${location.host}/ws`);   // wss:// when the page is served over https

ws.onopen = () => ws.send(JSON.stringify({ api_key: localStorage.getItem("apiKey") }));

ws.onmessage = (e) => {
  const evt = JSON.parse(e.data);
  if (evt.type === "ready") ws.send(JSON.stringify({ type: "message", text: "What's on today?" }));
  if (evt.type === "text") console.log(evt.text);
};

ws.onclose = (e) => console.log("closed", e.code);
```

Notice the same event objects (`text`, `tool_start`, `confirm`, `done`) flow over the WebSocket. That's the payoff of
designing `stream_agent` around events: the transport (SSE, WebSocket, Telegram, terminal) is interchangeable.

**Common mistakes**
- Forgetting `await websocket.accept()` — the connection is rejected.
- Trusting every message after connect without authenticating first.
- Using `ws://` on an `https://` page — browsers block it as mixed content; use `wss://`.
- No reconnect logic: laptop sleeps, the socket dies silently, and messages vanish. Real apps reconnect with backoff and show a "reconnecting..." banner.

**Exercises**
1. Write a small HTML page that uses the WebSocket endpoint instead of SSE, reusing your Lesson 10 rendering code.
2. Add a server "push": a background task that sends `{"type": "notice", "text": "..."}` over each open socket every minute (keep a set of connected sockets). This is the kind of thing SSE-per-request can't do.

**Check yourself**
- Name one thing WebSockets can do that POST + SSE can't.
- Why does the WebSocket example authenticate with the first message instead of a header?

---

## Part F: Voice

### Lesson 14: Speech-to-Text

**Concepts**
- **Speech-to-text (STT)**, also called transcription or ASR, turns recorded audio into text. Then the text goes to your
  agent exactly like a typed message. Your agent stays text-in, text-out; voice is just another front door.
- Two options:

| | Cloud API (OpenAI Whisper / transcribe models) | Local (`faster-whisper`) |
|---|---|---|
| Setup | API key, `pip install openai` | `pip install faster-whisper`, downloads a model on first run |
| Cost | Small per-minute fee | Free after download |
| Speed | Fast on any machine | Fast with a GPU; OK on CPU with small models |
| Privacy | Audio leaves your machine | Audio stays local |
| Accuracy | Very good | `base` is decent; `small`/`medium` are very good but slower |

- Audio basics: **sample rate** (samples per second; 16,000 Hz is plenty for speech), **channels** (1 = mono), and
  **format** (WAV is uncompressed and simple; OGG/MP3/WebM are compressed). Telegram voice notes are OGG.

**Install**

```bash
pip install openai faster-whisper sounddevice soundfile numpy
```

On Linux, `sounddevice` also needs the PortAudio system library:

```bash
sudo apt install libportaudio2
```

**Code — transcribing a file**
```python
# voice/stt.py
from pathlib import Path

from openai import OpenAI

_openai = None
_local_model = None

def transcribe_api(path: Path) -> str:
    """Transcribe with OpenAI's hosted Whisper model (needs OPENAI_API_KEY)."""
    global _openai
    if _openai is None:
        _openai = OpenAI()
    with path.open("rb") as f:
        result = _openai.audio.transcriptions.create(model="whisper-1", file=f)
    return result.text.strip()

def transcribe_local(path: Path, model_size: str = "base") -> str:
    """Transcribe on your own machine with faster-whisper."""
    global _local_model
    if _local_model is None:
        from faster_whisper import WhisperModel
        _local_model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _info = _local_model.transcribe(str(path), vad_filter=True)
    return " ".join(segment.text.strip() for segment in segments)
```

Loading a local model takes seconds, so it's loaded **once** and reused (the `global` cache), never per request.
`vad_filter=True` (voice activity detection) skips silence, which avoids Whisper "hallucinating" words in quiet parts.

**Code — recording with push-to-talk**
```python
# voice/record.py
import queue
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf

SAMPLE_RATE = 16_000

def record_push_to_talk(path: Path) -> Path | None:
    """Press Enter to start, Enter again to stop. Saves a mono 16 kHz WAV file."""
    chunks: queue.Queue[np.ndarray] = queue.Queue()

    def callback(indata, frames, time_info, status) -> None:   # called by sounddevice on its own thread
        chunks.put(indata.copy())

    input("Press Enter and start speaking...")
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", callback=callback):
        input("Recording... press Enter to stop.")

    frames = []
    while not chunks.empty():
        frames.append(chunks.get())
    if not frames:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, np.concatenate(frames), SAMPLE_RATE)
    return path
```

```python
# quick test
from pathlib import Path
from voice.record import record_push_to_talk
from voice.stt import transcribe_api

audio = record_push_to_talk(Path("data/test.wav"))
if audio:
    print("You said:", transcribe_api(audio))
```

**Code — Telegram voice notes**

The easiest voice interface is one you already have: hold the microphone button in Telegram, and your bot transcribes
the note. Add to your Telegram bot:
```python
from pathlib import Path
from voice.stt import transcribe_api

async def on_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tg_file = await update.message.voice.get_file()
    path = Path("data/voice") / f"{update.message.message_id}.ogg"
    path.parent.mkdir(parents=True, exist_ok=True)
    await tg_file.download_to_drive(path)
    try:
        text = await asyncio.to_thread(transcribe_api, path)
    finally:
        path.unlink(missing_ok=True)                 # don't keep recordings you don't need
    if not text:
        await update.message.reply_text("I couldn't hear anything in that voice note.")
        return
    await update.message.reply_text(f"Heard: “{text}”")   # show what was understood
    # ...then run the agent with `text`, exactly like on_text does

app.add_handler(MessageHandler(ALLOWED & filters.VOICE, on_voice))
```

Echoing back what was heard is important: if the transcription is wrong ("send" vs "spend"), you see it immediately.

**Common mistakes**
- Recording at 44.1 kHz stereo and sending huge files. 16 kHz mono is enough for speech.
- Loading the local Whisper model inside the request handler, so every message waits several seconds.
- Not checking for empty transcripts. Silence or noise can come back as `""` or as a made-up phrase like "Thank you."
- Forgetting the audio is personal data. Delete files you don't need and don't log transcripts at INFO level in shared logs.

**Exercises**
1. Time `transcribe_api` and `transcribe_local` (try `base` and `small`) on the same 10-second recording. Note speed and accuracy.
2. Add the Telegram `on_voice` handler to your bot and connect it to the agent.

**Check yourself**
- What sample rate and channel count are sensible for speech, and why?
- Why should the bot echo back the transcription?

---

### Lesson 15: Text-to-Speech and a Push-to-Talk Loop

**Concepts**
- **Text-to-speech (TTS)** turns the reply into audio. Cloud voices (OpenAI's TTS models, ElevenLabs, Google, Azure) sound
  natural; local engines (`pyttsx3`, which uses your operating system's voices) are free, offline and robotic.
- Written replies and spoken replies need different styles. Markdown lists, tables and links sound awful read aloud.
  In voice mode, **tell the model** to answer in short spoken sentences, and strip leftover Markdown symbols.
- A **push-to-talk loop**: record → transcribe → agent → speak → repeat. Push-to-talk (press a key to talk) is much
  simpler and more reliable than always-listening "wake word" systems.

**Code — speaking**
```python
# voice/tts.py
import re
from pathlib import Path

import sounddevice as sd
import soundfile as sf
from openai import OpenAI

_openai = None

def clean_for_speech(text: str) -> str:
    text = re.sub(r"```.*?```", " (code omitted) ", text, flags=re.DOTALL)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)      # [label](url) -> label
    text = re.sub(r"[*_#`>|]", "", text)                       # leftover Markdown symbols
    return re.sub(r"\s+", " ", text).strip()

def speak_api(text: str, path: Path = Path("data/reply.wav")) -> None:
    """Natural-sounding cloud voice (needs OPENAI_API_KEY)."""
    global _openai
    if _openai is None:
        _openai = OpenAI()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _openai.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=clean_for_speech(text),
        response_format="wav",
    ) as response:
        response.stream_to_file(path)
    data, sample_rate = sf.read(path)
    sd.play(data, sample_rate)
    sd.wait()                                   # block until playback finishes

def speak_local(text: str) -> None:
    """Offline, free, robotic. On Linux install espeak-ng first."""
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty("rate", 180)             # words per minute
    engine.say(clean_for_speech(text))
    engine.runAndWait()
```

For `speak_local` on Linux:

```bash
sudo apt install espeak-ng
```

```bash
pip install pyttsx3
```

**Code — the push-to-talk loop**
```python
# voice/talk.py
import asyncio
from pathlib import Path

from organizer import confirmations
from organizer.streaming import collect_reply
from voice.record import record_push_to_talk
from voice.stt import transcribe_api
from voice.tts import speak_api

USER = "owner"
VOICE_STYLE = (
    "(Voice mode: the user is listening, not reading. Answer in one to three short spoken sentences. "
    "No lists, tables, Markdown or URLs.)"
)

def main() -> None:
    print("Push-to-talk assistant. Press Ctrl+C to quit.")
    while True:
        audio = record_push_to_talk(Path("data/input.wav"))
        if audio is None:
            continue
        text = transcribe_api(audio)
        if not text:
            print("(heard nothing)")
            continue
        print(f"You: {text}")
        reply, confirms = asyncio.run(collect_reply(USER, f"{VOICE_STYLE}\n\n{text}"))
        print(f"Assistant: {reply}")
        speak_api(reply)
        for c in confirms:
            print(f"\nNeeds approval:\n{c['summary']}")
            # Approve with the KEYBOARD, not by voice: a misheard "yes" must never send an email.
            if input("Type 'yes' to approve: ").strip().lower() == "yes":
                print(confirmations.approve(c["action_id"], USER))
            else:
                print(confirmations.reject(c["action_id"], USER))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nBye!")
```

```bash
python -m voice.talk
```

**Latency budget.** Voice feels broken if you wait more than ~2–3 seconds for the first sound. Rough timings:
recording stop → upload + transcription (0.5–2 s) → agent with tools (2–15 s) → TTS (0.5–2 s) → playback. Ways to cut it:
use the faster model (`claude-haiku-5-5`) for voice turns, say a short filler ("One moment, checking your calendar")
when a tool starts, and, as an advanced step, stream TTS sentence by sentence while the agent is still generating.

**Common mistakes**
- Letting the model answer with bullet lists that then get read as "asterisk asterisk".
- Approving risky actions by voice. Transcription errors are common; use a button or keyboard.
- Playing audio and recording at the same time on a laptop without headphones — the microphone hears the assistant.

**Exercises**
1. Add a `--local` flag that switches to `transcribe_local` and `speak_local` so the loop works fully offline (except the agent itself).
2. Make the loop speak "One moment" as soon as the first `tool_start` event arrives (use `stream_agent` instead of `collect_reply`).

**Check yourself**
- Why does voice mode need a different prompt style from chat?
- Why is push-to-talk easier to build reliably than always-listening?

---

## Part G: UX for Agents

### Lesson 16: UX for Agents

**Concepts**
An agent is not a normal chat bot. It **takes actions**, it's **slow** (several model calls and tools per message), and
it's **sometimes wrong**. Good agent UX is about trust: the user should always know what it's doing, what it did, and
what it's about to do.

**The six principles**

| Principle | Bad | Good |
|---|---|---|
| **Show activity** | "Thinking..." for 25 seconds | "Searching your inbox... Checking calendar... Writing reply" |
| **Stream** | Wall of text after a long wait | First words in ~1 second |
| **Confirm before side effects** | "Done! I emailed your boss." | "Here's the draft to dana@example.com. [Approve] [Cancel]" |
| **Show exactly what will happen** | "Send the email?" | Recipient, subject, full body (or a clear preview), calendar, time zone |
| **Friendly, actionable errors** | `anthropic.APIStatusError: 529` | "The AI service is overloaded. Try again in a minute." |
| **Be honest about state** | Says "sent" when it's pending | "Waiting for your approval", "Sent at 14:02", "Expired" |

**Code — friendly tool labels (one place, used by every interface)**
```python
# organizer/ux.py
TOOL_LABELS = {
    "list_tasks": "Looking at your tasks",
    "search_email": "Searching your inbox",
    "read_email": "Reading an email",
    "list_events": "Checking your calendar",
    "create_event": "Preparing a calendar event",
    "send_email": "Drafting an email",
    "browse": "Browsing the web",
    "search_memory": "Remembering",
}

def tool_label(name: str) -> str:
    return TOOL_LABELS.get(name, f"Using {name.replace('_', ' ')}")
```

**Which actions need confirmation?**

| Action | Confirm? | Why |
|---|---|---|
| Read email, list events, search memory | No | Read-only; worst case is a wrong answer |
| Create a private task or note | No (show it, allow undo) | Easy to reverse |
| Create/move a calendar event *with other attendees* | **Yes** | Sends invitations to other people |
| Send an email or Slack message | **Yes** | Can't be unsent |
| Delete anything | **Yes** | Hard or impossible to undo |
| Spend money, submit forms in the browser | **Yes, always** | Real-world consequences |

Good confirmation design: show the **full** details; make **Cancel** the safe default; **expire** old requests; make
approval **idempotent** (double-tap runs once — Lesson 4); after approval, say what happened and when.

**Loading states checklist**
- Disable Send while a reply is in progress (or queue the message visibly).
- Show something within 300 ms: "Thinking...", a typing indicator, or the first tool label.
- Replace the placeholder with real text as soon as it arrives.
- Offer Stop for long replies (Lesson 10 exercise).
- On mobile bots, refresh the "typing" indicator (Lesson 3) — it disappears after ~5 seconds.

**Error message checklist**
- Say what happened in plain words, whether anything was done, and what the user can do next.
- Never show stack traces, API keys, or raw JSON to the user. Log them on the server.
- Distinguish "try again" problems (rate limit, network, overloaded) from "fix something" problems (expired Google
  login → "Please reconnect your Google account").
- If a tool failed but the agent continued, let the model say so ("I couldn't reach your calendar, so this list may be incomplete").

**Common mistakes**
- Hiding tool activity because it looks "technical". Users trust agents *more* when they see what they're doing.
- Asking for confirmation on everything. People start tapping Approve without reading. Confirm only the risky few.
- Different behaviour on different interfaces (web asks for confirmation, Telegram doesn't). Put the rule in the agent core, not the UI.

**Exercises**
1. Replace raw tool names with `tool_label` in your CLI, Telegram bot and web page.
2. Go through every tool your agent has and decide, using the table, whether it belongs in `RISKY_TOOLS`. Write the reason as a comment next to each.
3. Unplug your internet (or use a wrong API key) and use each interface. Write down every error message the user sees and improve the bad ones.

**Check yourself**
- Why should the confirmation rule live in the agent core instead of each interface?
- What three things should every error message tell the user?

---

## Capstone Project: Two Front Doors to One Agent

Build a FastAPI backend that wraps your agent with a streaming `/chat` endpoint and serves a web chat page, plus a
Telegram bot as a second front door to the **same** agent. Risky actions require tapping Approve in either interface.

### Requirements

**Level 1 — working**
- `organizer/streaming.py` with `stream_agent` and `collect_reply` (Lesson 8), wired to your real tools
- `organizer/confirmations.py` (Lesson 4) with `send_email` and at least one other risky tool gated
- FastAPI app with `GET /health`, streaming `POST /chat` (SSE), `POST /actions/{id}/approve`, `POST /actions/{id}/reject`
- Every route except `/health` requires the `X-API-Key` header
- The web page from Lesson 10 served at `/`, showing streamed text, tool activity and Approve / Cancel buttons
- A Telegram bot, allow-listed to your user id, that answers through `stream_agent` and shows Approve / Cancel inline buttons

**Level 2 — polished**
- Friendly tool labels (`organizer/ux.py`) in both interfaces; the Telegram bot edits a status message ("Checking your calendar...") while working
- Friendly error messages in both interfaces; full details only in the logs
- `GET /actions?status=pending` lists pending actions; the Telegram bot has a `/pending` command
- Both interfaces use the same internal user id, and conversation history is stored with your Section 4 memory (so a conversation started on Telegram can continue on the web)
- Telegram voice notes are transcribed and answered (Lesson 14)

**Level 3 — professional**
- Settings via `pydantic-settings`; the app refuses to start without required secrets
- At least 10 pytest tests: auth (401/200), request validation (422), SSE formatting, confirmations (approve once, double approve, expired, wrong user), and `stream_agent` with a fake client
- A `README.md` explaining setup, the `.env` variables, and how to run each process
- Optional: the Next.js frontend from Lesson 12 talking to the same backend

### Suggested structure
```
work_organizer/
├── .env / .env.example
├── organizer/
│   ├── agent.py              # run_agent (thin wrapper over collect_reply)
│   ├── confirmations.py
│   ├── memory.py
│   ├── streaming.py
│   ├── tools.py
│   └── ux.py
├── server/
│   ├── __init__.py
│   ├── auth.py
│   ├── main.py
│   ├── settings.py
│   └── static/
│       ├── index.html
│       └── app.js
├── bots/
│   ├── __init__.py
│   └── telegram_bot.py
└── tests/
    ├── test_api.py
    ├── test_confirmations.py
    └── test_streaming.py
```

### Starter skeleton (fill in the TODOs)

```python
# server/main.py
import asyncio
import json
import logging
from pathlib import Path
from typing import Annotated, Literal

import anthropic
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from organizer import confirmations
from organizer.streaming import add_note, stream_agent
from server.auth import require_user
from server.settings import get_settings

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("server")

app = FastAPI(title="Work Organizer API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

CurrentUser = Annotated[str, Depends(require_user)]

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)

class ActionResult(BaseModel):
    result: str

class PendingActionOut(BaseModel):
    id: str
    tool_name: str
    summary: str

def sse(event: dict) -> str:
    # TODO: return the event in SSE wire format (JSON-encoded, ends with a blank line)
    ...

def friendly_error(exc: Exception) -> str:
    # TODO: map RateLimitError, APIConnectionError, 5xx APIStatusError to friendly text (Lesson 9)
    ...

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

@app.post("/chat")
async def chat(body: ChatRequest, user_id: CurrentUser) -> StreamingResponse:
    async def events():
        # TODO: iterate stream_agent(user_id, body.message) and yield sse(event)
        # TODO: on exception: log it, yield an "error" event with friendly_error(exc), then a "done" event
        ...
    # TODO: return a StreamingResponse with media_type="text/event-stream" and no-cache headers
    ...

@app.get("/actions")
async def list_actions(
    user_id: CurrentUser,
    status: Annotated[Literal["pending"], Query()] = "pending",
) -> list[PendingActionOut]:
    # TODO: use confirmations.list_pending(user_id) (in a thread) and convert to PendingActionOut
    ...

@app.post("/actions/{action_id}/approve")
async def approve_action(action_id: str, user_id: CurrentUser) -> ActionResult:
    # TODO: 404 if the action doesn't exist or belongs to someone else
    # TODO: run confirmations.approve in a thread, add_note(...) so the agent knows, return the result
    ...

@app.post("/actions/{action_id}/reject")
async def reject_action(action_id: str, user_id: CurrentUser) -> ActionResult:
    # TODO
    ...

# Must stay LAST: serves server/static/index.html at "/"
app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")
```

```python
# bots/telegram_bot.py
import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.error import BadRequest
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters,
)

from organizer import confirmations
from organizer.streaming import add_note, stream_agent
from organizer.ux import tool_label

load_dotenv()
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("telegram_bot")

OWNER = "owner"                               # same internal user id as the web app
ALLOWED_IDS = {int(x) for x in os.environ["TELEGRAM_ALLOWED_USER_IDS"].split(",") if x.strip()}
ALLOWED = filters.User(user_id=ALLOWED_IDS)

def split_message(text: str, limit: int = 4096) -> list[str]:
    # TODO: copy from Lesson 3
    ...

def confirm_keyboard(action_id: str) -> InlineKeyboardMarkup:
    # TODO: one row with "Approve" (approve:<id>) and "Cancel" (reject:<id>) buttons
    ...

async def set_status(message, text: str) -> None:
    """Edit the status message, ignoring 'message is not modified' errors."""
    try:
        await message.edit_text(text)
    except BadRequest as e:
        if "not modified" not in str(e).lower():
            raise

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    status = await update.message.reply_text("Thinking...")
    parts: list[str] = []
    confirms: list[dict] = []
    try:
        async for event in stream_agent(OWNER, update.message.text):
            match event["type"]:
                case "text":
                    parts.append(event["text"])
                case "tool_start":
                    # TODO: await set_status(status, tool_label(event["name"]) + "...")
                    ...
                case "confirm":
                    confirms.append(event)
    except Exception:
        log.exception("Agent failed")
        await set_status(status, "Sorry, something went wrong. Please try again in a minute.")
        return

    reply = "".join(parts).strip() or "(no reply)"
    # TODO: put the first chunk of the reply into `status` (set_status), send the rest as new messages
    # TODO: for each confirm event, reply with its summary and confirm_keyboard(action_id)

async def on_confirm_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    # TODO: reject users not in ALLOWED_IDS (answer with show_alert=True) and return
    # TODO: await query.answer(); parse "approve:<id>" / "reject:<id>"
    # TODO: run confirmations.approve / reject in a thread; add_note(OWNER, ...) about the outcome
    # TODO: edit the message: original text + result, which also removes the buttons
    ...

async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # TODO: list confirmations.list_pending(OWNER) with a keyboard for each, or "Nothing pending."
    ...

async def unauthorized(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_message:
        await update.effective_message.reply_text("Sorry, this is a private assistant.")

async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.error("Unhandled error", exc_info=context.error)

def main() -> None:
    app = Application.builder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()
    app.add_handler(CommandHandler("pending", pending_command, filters=ALLOWED))
    app.add_handler(MessageHandler(ALLOWED & filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(CallbackQueryHandler(on_confirm_button, pattern=r"^(approve|reject):"))
    app.add_handler(MessageHandler(filters.ALL, unauthorized))        # must be last
    app.add_error_handler(on_error)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
```

```python
# tests/test_api.py (starter)
import os

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")    # the SDK client is created at import time
os.environ.setdefault("API_KEY", "test-api-key")

from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def test_health_needs_no_key():
    assert client.get("/health").status_code == 200

def test_chat_requires_key():
    assert client.post("/chat", json={"message": "hi"}).status_code == 401

def test_chat_rejects_empty_message():
    r = client.post("/chat", json={"message": ""}, headers={"X-API-Key": "test-api-key"})
    assert r.status_code == 422

# TODO: test approve/reject: 404 for unknown id, second approve says "already handled"
# TODO: test sse({"type": "done"}) == 'data: {"type": "done"}\n\n'
```

Run everything — each in its own terminal, from the project root:

```bash
fastapi dev server/main.py
```

```bash
python -m bots.telegram_bot
```

```bash
pytest -v
```

**Manual test script** (do all of these before calling it finished):
1. Web: "What are my tasks?" — tool activity appears, then text streams in.
2. Web: "Email dana@example.com saying the report will be ready Friday" — a confirmation card appears; Approve runs it once; tapping again does nothing.
3. Telegram: the same email request — buttons appear; Cancel says nothing was sent.
4. Telegram from a second account (ask a friend): the bot refuses.
5. `curl` the `/chat` endpoint without a key → 401.
6. Set a wrong `ANTHROPIC_API_KEY`, restart, send a message in both interfaces → friendly error, details in the log.
7. Approve an action that's older than 15 minutes → "expired".

**Why this design matters:** the agent core doesn't know or care whether a message came from a browser, Telegram or a
microphone. When you later add a Slack front door, a phone shortcut or a scheduled morning briefing (Section 5), it's one
more thin adapter calling `stream_agent`, and the confirmation safety rule comes along for free.

---

## Weekly Schedule

| Week | Lessons | Mini-project |
|---|---|---|
| 1 | Part 0, Lessons 1–2 | Polished Rich/Typer CLI for your agent |
| 2 | Lessons 3–4 | Allow-listed Telegram bot with Approve / Cancel buttons |
| 3 | Lessons 5–7 | Tasks API with auth and docs; optional Discord or Slack bot |
| 4 | Lessons 8–9 | `stream_agent` + streaming `/chat` endpoint tested with `curl -N` |
| 5 | Lesson 10, Lesson 16 | Web chat page with tool activity and confirmation cards |
| 6 | Lessons 11–13 | React practice app; Next.js chat via proxy route handlers |
| 7 | Lessons 14–15, Capstone | Voice loop; capstone Levels 1–3 |

**Daily routine (1–2 hours):** 20 min reading → 40 min typing examples and experimenting → 30 min exercises → 5 min
writing notes on what confused you. Keep the Telegram bot running while you study; using your own assistant every day is
the fastest way to find what to improve.

---

## Final Checklist

Before moving on, you should be able to do all of this **without looking things up**:

**Choosing and designing**
- [ ] Compare CLI, chat bot, web app and voice interfaces and pick one for a given situation
- [ ] Explain "one brain, many front doors" and keep agent logic out of interface code
- [ ] Map every interface's identity to one internal user id

**Terminal and bots**
- [ ] Build a Typer CLI with commands, arguments and options, and render Markdown with Rich
- [ ] Create a Telegram bot with BotFather and run it with polling
- [ ] Write async handlers for commands, text, voice notes and button presses
- [ ] Allow-list your own user id for messages **and** callback queries
- [ ] Explain how Discord and Slack (Socket Mode) bots differ from Telegram

**Backend**
- [ ] Create FastAPI routes with path parameters, query parameters and Pydantic request/response models
- [ ] Decide between `def` and `async def` endpoints and avoid blocking the event loop
- [ ] Protect routes with an API-key dependency and configure CORS correctly
- [ ] Explain sessions vs JWTs and when you'd need them
- [ ] Stream agent events with SSE and handle errors that happen mid-stream

**Frontend**
- [ ] Read an SSE stream with `fetch` and a buffer, and render text safely with `textContent`
- [ ] Write React components with props, `useState` and `useEffect`, updating state immutably
- [ ] Build a Next.js App Router page with a Client Component and a proxy route handler
- [ ] Explain when WebSockets are worth it over SSE

**Voice and UX**
- [ ] Transcribe audio with a cloud API or local `faster-whisper`
- [ ] Speak replies with a TTS API or `pyttsx3`, and adapt the prompt for voice
- [ ] Show tool activity, loading states and friendly errors
- [ ] Gate risky actions behind idempotent, expiring confirmations

---

## Exercise Solutions

Try every exercise yourself first. Look here only after a real attempt (at least 20 minutes).

**Lesson 2, Exercise 1**
```python
from rich.table import Table
from organizer.tools import TASKS        # or however your project loads tasks

@app.command()
def tasks() -> None:
    """Show pending tasks."""
    table = Table(title="Pending tasks")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Priority", justify="right")
    for t in sorted(TASKS, key=lambda t: t["priority"]):
        style = "bold red" if t["priority"] == 1 else None
        table.add_row(t["id"], t["title"], str(t["priority"]), style=style)
    console.print(table)
```

**Lesson 3, Exercise 2**
```python
import time

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    seconds = int(time.monotonic() - context.bot_data["started_at"])
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    await update.message.reply_text(f"Pong! Up for {hours}h {minutes}m {secs}s.")

# in main(), after building the app:
app.bot_data["started_at"] = time.monotonic()
app.add_handler(CommandHandler("ping", ping, filters=ALLOWED))
```

**Lesson 4, Exercise 1**
```python
async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    actions = await asyncio.to_thread(confirmations.list_pending, OWNER)
    if not actions:
        await update.message.reply_text("Nothing pending.")
        return
    for action in actions:
        await update.message.reply_text(
            f"Needs your approval:\n\n{action.summary}",
            reply_markup=confirm_keyboard(action.id),
        )
```

**Lesson 6, Exercise 1**
```python
class TaskSummary(BaseModel):
    total: int
    pending: int
    done: int

@app.get("/tasks/summary")          # define this BEFORE @app.get("/tasks/{task_id}")
async def task_summary() -> TaskSummary:
    done = sum(1 for t in TASKS.values() if t.done)
    return TaskSummary(total=len(TASKS), pending=len(TASKS) - done, done=done)
```
Because `task_id` is typed `int`, a request for `/tasks/summary` that reached the `{task_id}` route would fail with a
422 ("summary" isn't an integer). Ordering the fixed path first avoids this.

**Lesson 6, Exercise 2** (assuming `Task` has `tags: list[str] = []`)
```python
@app.get("/tasks")
async def list_tasks(
    tag: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[Task]:
    tasks = list(TASKS.values())
    if tag:
        wanted = set(tag)
        tasks = [t for t in tasks if wanted & set(t.tags)]   # has at least one of the tags
    return tasks[:limit]
```
Request: `/tasks?tag=work&tag=urgent`. Without `Query()`, FastAPI would expect a list in the request *body*.

**Lesson 7, Exercise 3**
```python
# tests/test_auth.py
import os
os.environ.setdefault("API_KEY", "unused")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from fastapi.testclient import TestClient
from server.main import app
from server.settings import Settings, get_settings

app.dependency_overrides[get_settings] = lambda: Settings(api_key="secret-for-tests")
client = TestClient(app)

def test_me_without_key_is_401():
    assert client.get("/me").status_code == 401

def test_me_with_wrong_key_is_401():
    assert client.get("/me", headers={"X-API-Key": "nope"}).status_code == 401

def test_me_with_key_is_200():
    r = client.get("/me", headers={"X-API-Key": "secret-for-tests"})
    assert r.status_code == 200
    assert r.json() == {"user_id": "owner"}
```

**Lesson 8, Exercise 3**
```python
# tests/test_streaming.py
import asyncio
import os
from types import SimpleNamespace as NS

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")   # AsyncAnthropic() needs a key at import time

import organizer.streaming as streaming

class FakeStream:
    """Mimics the object returned by client.messages.stream(...)."""
    def __init__(self, texts: list[str], final):
        self.texts = texts
        self.final = final

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def __aiter__(self):
        return self._events()

    async def _events(self):
        for t in self.texts:
            yield NS(type="text", text=t)

    async def get_final_message(self):
        return self.final

class FakeMessages:
    def __init__(self, streams):
        self.streams = list(streams)

    def stream(self, **kwargs):
        return self.streams.pop(0)

def run_events(user_id: str, message: str) -> list[dict]:
    async def go():
        return [e async for e in streaming.stream_agent(user_id, message)]
    return asyncio.run(go())

def test_plain_text_reply(monkeypatch):
    final = NS(stop_reason="end_turn", content=[NS(type="text", text="Hello there")])
    fake_client = NS(messages=FakeMessages([FakeStream(["Hello", " there"], final)]))
    monkeypatch.setattr(streaming, "client", fake_client)
    streaming.HISTORY.clear()

    events = run_events("u1", "hi")

    assert [e["text"] for e in events if e["type"] == "text"] == ["Hello", " there"]
    assert events[-1] == {"type": "done"}
    assert [m["role"] for m in streaming.HISTORY["u1"]] == ["user", "assistant"]

def test_tool_call_then_answer(monkeypatch):
    tool_block = NS(type="tool_use", id="tu_1", name="list_tasks", input={})
    first = FakeStream([], NS(stop_reason="tool_use", content=[tool_block]))
    second = FakeStream(["2 tasks"], NS(stop_reason="end_turn", content=[NS(type="text", text="2 tasks")]))
    monkeypatch.setattr(streaming, "client", NS(messages=FakeMessages([first, second])))
    monkeypatch.setattr(streaming, "run_tool", lambda name, args: "[...]")
    streaming.HISTORY.clear()

    events = run_events("u2", "what are my tasks?")

    assert {"type": "tool_end", "name": "list_tasks", "ok": True} in events
    roles = [m["role"] for m in streaming.HISTORY["u2"]]
    assert roles == ["user", "assistant", "user", "assistant"]   # question, tool call, tool result, answer
```
The fake only needs the attributes `stream_agent` actually uses (`type`, `text`, `stop_reason`, `content`, `id`, `name`,
`input`). That's a general testing trick: fake the smallest surface your code touches.

**Lesson 9, Exercise 3**
```python
from organizer.streaming import collect_reply

class PendingOut(BaseModel):
    action_id: str
    summary: str

class ChatOnceResponse(BaseModel):
    reply: str
    pending_actions: list[PendingOut]

@app.post("/chat-once")
async def chat_once(body: ChatRequest, user_id: Annotated[str, Depends(require_user)]) -> ChatOnceResponse:
    reply, confirms = await collect_reply(user_id, body.message)
    return ChatOnceResponse(
        reply=reply,
        pending_actions=[PendingOut(action_id=c["action_id"], summary=c["summary"]) for c in confirms],
    )
```

**Lesson 10, Exercise 2**
```javascript
let controller = null;
const stopButton = document.querySelector("#stop");     // add <button id="stop" type="button">Stop</button>

stopButton.addEventListener("click", () => controller?.abort());

// inside sendMessage(), before fetch:
controller = new AbortController();
const res = await fetch("/chat", {
  method: "POST",
  headers: { "Content-Type": "application/json", "X-API-Key": getApiKey() },
  body: JSON.stringify({ message }),
  signal: controller.signal,
});

// in the catch block:
if (err.name === "AbortError") {
  reply.text.textContent += "\n\n(stopped)";
  return;
}
```
When the browser aborts, the server sees the disconnect, cancels the generator, and `stream_agent` rolls the turn back.

**Lesson 11, Exercise 3**
```tsx
type Filter = "all" | "pending" | "done";
type Task = { id: string; title: string; done: boolean };

function TaskBoard({ tasks }: { tasks: Task[] }) {
  const [filter, setFilter] = useState<Filter>("pending");
  const visible = tasks.filter((t) =>
    filter === "all" ? true : filter === "done" ? t.done : !t.done,
  );                                            // derived during render, not stored in state
  return (
    <>
      {(["all", "pending", "done"] as const).map((f) => (
        <button key={f} disabled={f === filter} onClick={() => setFilter(f)}>{f}</button>
      ))}
      <ul>{visible.map((t) => <li key={t.id}>{t.title}</li>)}</ul>
    </>
  );
}
```
Storing `visible` in state too would mean two sources of truth that can drift apart.

**Lesson 16, Exercise 1** (Telegram status message)
```python
from organizer.ux import tool_label

case "tool_start":
    await set_status(status, tool_label(event["name"]) + "...")
```

---

## Recommended Resources

| Resource | Type | Best for |
|---|---|---|
| fastapi.tiangolo.com (Tutorial – User Guide) | Official docs | FastAPI, step by step |
| docs.python-telegram-bot.org + the library's `examples/` folder on GitHub | Docs + examples | Telegram bots, inline keyboards |
| core.telegram.org/bots/api | Reference | What the Bot API can do (limits, message types) |
| discordpy.readthedocs.io | Docs | Discord bots |
| tools.slack.dev/bolt-python | Docs | Slack Bolt and Socket Mode |
| rich.readthedocs.io, typer.tiangolo.com | Docs | Terminal UIs |
| developer.mozilla.org (Fetch API, Streams API, Server-sent events, WebSockets) | Reference | Browser APIs used in Lessons 9–13 |
| react.dev (Learn section) | Official tutorial | React components, state, effects |
| nextjs.org/learn and nextjs.org/docs/app | Course + docs | App Router, route handlers |
| docs.anthropic.com (streaming messages, tool use) | Official docs | Streaming events and the agent loop |
| github.com/SYSTRAN/faster-whisper | README | Local transcription options |
| platform.openai.com/docs/guides/speech-to-text and text-to-speech | Docs | Cloud STT/TTS |
| OWASP Top 10 (owasp.org) | Security guide | Injection, auth, and other web risks |

**Next:** Section 7 — taking your assistant beyond your laptop (deployment, running it 24/7, monitoring, and safety in production).
