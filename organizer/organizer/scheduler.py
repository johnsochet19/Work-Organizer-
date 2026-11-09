"""Background jobs: task reminders when a due time passes, and the morning briefing."""
from __future__ import annotations

import threading
import time
from typing import Callable

from .briefing import gather
from .tasks import format_task
from .tools import Context


class Scheduler:
    def __init__(self, ctx: Context, notify: Callable[[str], None], interval: float = 30):
        self.ctx = ctx
        self.notify = notify
        self.interval = interval

    def tick(self) -> list[str]:
        """Run whatever is due right now. Returns the messages sent (handy for tests)."""
        sent = []
        s, store = self.ctx.settings, self.ctx.store
        now = s.now()
        for t in self.ctx.tasks.due_reminders():
            msg = "⏰ Reminder: " + format_task(t, now.date())
            self.notify(msg)
            self.ctx.tasks.mark_reminded(t["id"])
            sent.append(msg)
        today = now.date().isoformat()
        if now.strftime("%H:%M") >= s.briefing_time and store.get("briefing_sent") != today:
            text = gather(self.ctx)
            store.set("last_briefing", text)
            store.set("briefing_sent", today)
            self.notify("☀️ " + text)
            sent.append(text)
        return sent

    def run_forever(self) -> None:
        while True:
            try:
                self.tick()
            except Exception as e:
                print(f"Scheduler error: {e}", flush=True)
            time.sleep(self.interval)

    def start(self) -> threading.Thread:
        t = threading.Thread(target=self.run_forever, daemon=True)
        t.start()
        return t
