"""Tasks: add, list, change, complete (repeating tasks come back), delete.

Due values are ISO strings in your local time: "2026-11-12" (a day) or
"2026-11-12T15:00" (a day and time; a reminder is sent when it passes).
"""
from __future__ import annotations

import calendar
import re
from datetime import date, datetime, timedelta

from .store import Store, new_id, utcnow

RECUR = ("daily", "weekdays", "weekly", "monthly", "yearly")
WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


class TaskError(Exception):
    pass


def parse_due(text: str | None, now: datetime) -> str | None:
    """Accept ISO dates/times and simple words: today, tomorrow, friday, next monday,
    in 3 days, in 2 weeks, tonight, with an optional time like 3pm or 15:30."""
    if text is None:
        return None
    s = text.strip().lower()
    if not s or s in ("none", "no", "null", "clear"):
        return None
    # ISO forms
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            d = datetime.strptime(s.upper() if "t" in s else s, fmt)
            return d.strftime("%Y-%m-%dT%H:%M") if ("%H" in fmt) else d.strftime("%Y-%m-%d")
        except ValueError:
            pass

    time_part = None
    m = re.search(r"\b(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b|\b(?:at\s+)?(\d{1,2}):(\d{2})\b", s)
    if m:
        if m.group(3):
            h, mi = int(m.group(1)), int(m.group(2) or 0)
            if m.group(3) == "pm" and h != 12:
                h += 12
            if m.group(3) == "am" and h == 12:
                h = 0
        else:
            h, mi = int(m.group(4)), int(m.group(5))
        if not (0 <= h < 24 and 0 <= mi < 60):
            raise TaskError(f"I couldn't understand the time in '{text}'.")
        time_part = (h, mi)
        s = (s[:m.start()] + s[m.end():]).strip()

    today = now.date()
    day: date | None = None
    if s in ("", "today"):
        day = today
    elif s == "tonight":
        day = today
        time_part = time_part or (20, 0)
    elif s == "tomorrow":
        day = today + timedelta(days=1)
    elif s in ("next week",):
        day = today + timedelta(days=7)
    else:
        m = re.fullmatch(r"in (\d+) (day|days|week|weeks|month|months)", s)
        if m:
            n, unit = int(m.group(1)), m.group(2)
            if unit.startswith("day"):
                day = today + timedelta(days=n)
            elif unit.startswith("week"):
                day = today + timedelta(weeks=n)
            else:
                day = add_months(today, n)
        else:
            m = re.fullmatch(r"(next |this )?(" + "|".join(WEEKDAYS) + r")", s)
            if m:
                target = WEEKDAYS.index(m.group(2))
                ahead = (target - today.weekday()) % 7
                if ahead == 0 or m.group(1) == "next ":
                    ahead = ahead or 7
                day = today + timedelta(days=ahead)
    if day is None:
        raise TaskError(f"I couldn't understand the date '{text}'. Try 2026-11-20, tomorrow, friday or 'in 3 days'.")
    if time_part:
        return datetime(day.year, day.month, day.day, *time_part).strftime("%Y-%m-%dT%H:%M")
    return day.isoformat()


def add_months(d: date, n: int) -> date:
    month = d.month - 1 + n
    year = d.year + month // 12
    month = month % 12 + 1
    return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))


def due_date(due: str | None) -> date | None:
    return date.fromisoformat(due[:10]) if due else None


def due_datetime(due: str | None) -> datetime | None:
    """The moment a reminder should go off (only for dues with a time)."""
    if due and "T" in due:
        return datetime.fromisoformat(due)
    return None


def next_due(due: str | None, recur: str, today: date) -> str:
    base = due_date(due) or today
    time_suffix = due[10:] if due and len(due) > 10 else ""
    if recur == "daily":
        nxt = base + timedelta(days=1)
    elif recur == "weekdays":
        nxt = base + timedelta(days=1)
        while nxt.weekday() >= 5:
            nxt += timedelta(days=1)
    elif recur == "weekly":
        nxt = base + timedelta(weeks=1)
    elif recur == "monthly":
        nxt = add_months(base, 1)
    else:
        nxt = add_months(base, 12)
    # If it was badly overdue, don't create a pile of instances in the past.
    while nxt < today:
        nxt = date.fromisoformat(next_due(nxt.isoformat(), recur, nxt)[:10])
    return nxt.isoformat() + time_suffix


class Tasks:
    def __init__(self, store: Store, now_fn):
        self.store = store
        self.now = now_fn

    def _row(self, task_id: str):
        with self.store.conn() as c:
            row = c.execute("SELECT * FROM tasks WHERE id=?", (task_id.strip().lstrip("#"),)).fetchone()
        if not row:
            raise TaskError(f"There's no task with id {task_id}.")
        return dict(row)

    def get(self, task_id: str) -> dict:
        return self._row(task_id)

    def add(self, title: str, priority: int = 3, due: str | None = None, tags=None,
            notes: str = "", recur: str | None = None) -> dict:
        title = (title or "").strip()
        if not title:
            raise TaskError("A task needs a title.")
        priority = _priority(priority)
        due = parse_due(due, self.now())
        recur = _recur(recur)
        tags = _tags(tags)
        tid = new_id()
        with self.store.conn() as c:
            c.execute("INSERT INTO tasks(id,title,notes,priority,due,tags,recur,created_at) VALUES(?,?,?,?,?,?,?,?)",
                      (tid, title, notes or "", priority, due, tags, recur, utcnow()))
        return self.get(tid)

    def update(self, task_id: str, **fields) -> dict:
        task = self._row(task_id)
        changes = {}
        if fields.get("title") is not None:
            if not fields["title"].strip():
                raise TaskError("A task needs a title.")
            changes["title"] = fields["title"].strip()
        if fields.get("priority") is not None:
            changes["priority"] = _priority(fields["priority"])
        if "due" in fields and fields["due"] is not None:
            changes["due"] = parse_due(fields["due"], self.now())
            changes["reminded_at"] = None
        if fields.get("tags") is not None:
            changes["tags"] = _tags(fields["tags"])
        if fields.get("notes") is not None:
            changes["notes"] = fields["notes"]
        if "recur" in fields and fields["recur"] is not None:
            changes["recur"] = _recur(fields["recur"])
        if fields.get("status") is not None:
            if fields["status"] not in ("open", "done"):
                raise TaskError("status must be 'open' or 'done'.")
            changes["status"] = fields["status"]
        if not changes:
            return task
        sets = ", ".join(f"{k}=?" for k in changes)
        with self.store.conn() as c:
            c.execute(f"UPDATE tasks SET {sets} WHERE id=?", (*changes.values(), task["id"]))
        return self.get(task["id"])

    def complete(self, task_id: str) -> tuple[dict, dict | None]:
        """Mark done. A repeating task gets its next copy, which is returned too."""
        task = self._row(task_id)
        if task["status"] == "done":
            return task, None
        with self.store.conn() as c:
            c.execute("UPDATE tasks SET status='done', completed_at=? WHERE id=?", (utcnow(), task["id"]))
        nxt = None
        if task["recur"]:
            nxt = self.add(task["title"], task["priority"], next_due(task["due"], task["recur"], self.now().date()),
                           task["tags"], task["notes"], task["recur"])
        return self.get(task["id"]), nxt

    def delete(self, task_id: str) -> dict:
        task = self._row(task_id)
        with self.store.conn() as c:
            c.execute("DELETE FROM tasks WHERE id=?", (task["id"],))
        return task

    def list(self, status: str = "open", tag: str | None = None, due_within_days: int | None = None,
             query: str | None = None, limit: int = 50) -> list[dict]:
        sql, params = "SELECT * FROM tasks WHERE 1=1", []
        if status in ("open", "done"):
            sql += " AND status=?"
            params.append(status)
        if tag:
            sql += " AND (',' || tags || ',') LIKE ?"
            params.append(f"%,{tag.strip().lstrip('#').lower()},%")
        if query:
            sql += " AND (title LIKE ? OR notes LIKE ?)"
            params += [f"%{query}%", f"%{query}%"]
        if due_within_days is not None:
            sql += " AND due IS NOT NULL AND substr(due,1,10) <= ?"
            params.append((self.now().date() + timedelta(days=int(due_within_days))).isoformat())
        with self.store.conn() as c:
            rows = [dict(r) for r in c.execute(sql, params).fetchall()]
        if status == "done":
            rows.sort(key=lambda t: t["completed_at"] or "", reverse=True)
        else:
            rows.sort(key=lambda t: (t["due"] is None, t["due"] or "", t["priority"], t["created_at"]))
        return rows[:limit]

    def overdue_and_today(self) -> tuple[list[dict], list[dict]]:
        today = self.now().date().isoformat()
        open_tasks = self.list(due_within_days=0, limit=500)
        overdue = [t for t in open_tasks if t["due"][:10] < today]
        due_today = [t for t in open_tasks if t["due"][:10] == today]
        return overdue, due_today

    def due_reminders(self) -> list[dict]:
        """Open tasks with a due time that has passed and no reminder sent yet."""
        now = self.now().replace(tzinfo=None)
        out = []
        for t in self.list(due_within_days=0, limit=500):
            when = due_datetime(t["due"])
            if when and when <= now and not t["reminded_at"]:
                out.append(t)
        return out

    def mark_reminded(self, task_id: str) -> None:
        with self.store.conn() as c:
            c.execute("UPDATE tasks SET reminded_at=? WHERE id=?", (utcnow(), task_id))


def _priority(p) -> int:
    try:
        p = int(str(p).lower().lstrip("p"))
    except ValueError:
        raise TaskError("priority must be 1 (high), 2 (medium) or 3 (low).")
    if p not in (1, 2, 3):
        raise TaskError("priority must be 1 (high), 2 (medium) or 3 (low).")
    return p


def _recur(r) -> str | None:
    if r is None:
        return None
    r = str(r).strip().lower()
    if r in ("", "none", "no", "never"):
        return None
    if r not in RECUR:
        raise TaskError(f"repeat must be one of: {', '.join(RECUR)}.")
    return r


def _tags(tags) -> str:
    if tags is None:
        return ""
    if isinstance(tags, str):
        tags = re.split(r"[,\s]+", tags)
    return ",".join(sorted({t.strip().lstrip("#").lower() for t in tags if t and t.strip().lstrip("#")}))


def format_task(t: dict, today: date | None = None) -> str:
    mark = "x" if t["status"] == "done" else " "
    parts = [f"[{mark}] #{t['id']} {t['title']}", f"(p{t['priority']}"]
    if t["due"]:
        d = due_date(t["due"])
        label = t["due"].replace("T", " ")
        if today and t["status"] == "open":
            if d < today:
                label += ", OVERDUE"
            elif d == today:
                label += ", today"
        parts.append(f"due {label}")
    if t["recur"]:
        parts.append(f"repeats {t['recur']}")
    if t["tags"]:
        parts.append(" ".join("#" + x for x in t["tags"].split(",")))
    return parts[0] + " " + ", ".join(parts[1:]) + ")"
