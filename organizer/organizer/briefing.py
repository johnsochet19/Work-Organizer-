"""The daily briefing: what's overdue, what's due today, today's calendar, unread email."""
from __future__ import annotations

from datetime import datetime, timedelta

from . import calendar_ics, mail
from .tasks import format_task


def gather(ctx) -> str:
    s = ctx.settings
    now = s.now()
    today = now.date()
    lines = [f"Briefing for {now:%A %d %B %Y, %H:%M}"]

    overdue, due_today = ctx.tasks.overdue_and_today()
    lines.append("")
    lines.append(f"Overdue ({len(overdue)}):" if overdue else "Nothing overdue.")
    lines += ["  " + format_task(t, today) for t in overdue[:15]]
    lines.append(f"Due today ({len(due_today)}):" if due_today else "Nothing else due today.")
    lines += ["  " + format_task(t, today) for t in due_today[:15]]
    soon = [t for t in ctx.tasks.list(due_within_days=3) if t["due"][:10] > today.isoformat()]
    if soon:
        lines.append(f"Coming up in the next 3 days ({len(soon)}):")
        lines += ["  " + format_task(t, today) for t in soon[:10]]
    undated = [t for t in ctx.tasks.list(limit=200) if not t["due"] and t["priority"] == 1]
    if undated:
        lines.append("High priority with no date:")
        lines += ["  " + format_task(t, today) for t in undated[:5]]

    if s.calendar_urls:
        lines.append("")
        try:
            tz = s.tz()
            start = datetime.combine(today, datetime.min.time(), tzinfo=tz)
            events = calendar_ics.fetch_events(s.calendar_urls, tz, start, start + timedelta(days=1))
            if events:
                lines.append(f"Calendar today ({len(events)}):")
                for ev in events:
                    if ev.all_day:
                        lines.append(f"  all day  {ev.title}")
                    else:
                        lines.append(f"  {ev.start.astimezone(tz):%H:%M}–{ev.end.astimezone(tz):%H:%M}  {ev.title}"
                                     + (f" @ {ev.location}" if ev.location else ""))
            else:
                lines.append("No calendar events today.")
        except Exception as e:
            lines.append(f"(Couldn't read the calendar: {e})")

    if s.has_email:
        lines.append("")
        try:
            unread = mail.list_messages(s, unread_only=True, limit=8)
            if unread:
                lines.append(f"Unread email (newest {len(unread)}):")
                lines += [f"  {m['from'][:40]} — {m['subject'][:70]}" for m in unread]
            else:
                lines.append("Inbox: no unread email.")
        except Exception as e:
            lines.append(f"(Couldn't read email: {e})")
    return "\n".join(lines)
