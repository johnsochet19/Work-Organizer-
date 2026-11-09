"""Read calendars from their secret iCal (.ics) address.

Google Calendar: Settings → your calendar → "Secret address in iCal format".
Outlook: Settings → Calendar → Shared calendars → Publish a calendar → ICS link.
Apple iCloud: share the calendar as a public calendar and use the webcal link
(change webcal:// to https://).

Supports single events, all-day events, time zones, and the common repeat rules
(daily / weekly with days / monthly / yearly, with INTERVAL, COUNT, UNTIL and
cancelled occurrences).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .tasks import add_months
from .web import WebError, http_get

DAY_CODES = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]
MAX_OCCURRENCES = 2000


@dataclass
class Event:
    title: str
    start: datetime
    end: datetime
    all_day: bool
    location: str = ""
    calendar: str = ""

    def as_dict(self) -> dict:
        if self.all_day:
            when = self.start.date().isoformat() + " (all day)"
        else:
            when = f"{self.start:%Y-%m-%d %H:%M}–{self.end:%H:%M}"
        d = {"title": self.title, "when": when}
        if self.location:
            d["location"] = self.location
        if self.calendar:
            d["calendar"] = self.calendar
        return d


def unfold(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        if raw.startswith((" ", "\t")) and lines:
            lines[-1] += raw[1:]
        else:
            lines.append(raw)
    return lines


def _unescape(v: str) -> str:
    return v.replace("\\n", "\n").replace("\\N", "\n").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")


def _parse_line(line: str) -> tuple[str, dict, str]:
    head, _, value = line.partition(":")
    name, *params = head.split(";")
    p = {}
    for item in params:
        k, _, v = item.partition("=")
        p[k.upper()] = v.strip('"')
    return name.upper(), p, value


def _parse_dt(value: str, params: dict, local_tz: tzinfo) -> tuple[datetime, bool]:
    value = value.strip()
    if params.get("VALUE") == "DATE" or re.fullmatch(r"\d{8}", value):
        d = datetime.strptime(value[:8], "%Y%m%d")
        return d.replace(tzinfo=local_tz), True
    if value.endswith("Z"):
        return datetime.strptime(value[:15], "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc), False
    dt = datetime.strptime(value[:15], "%Y%m%dT%H%M%S")
    tz = local_tz
    if "TZID" in params:
        try:
            tz = ZoneInfo(params["TZID"])
        except (ZoneInfoNotFoundError, ValueError):
            tz = local_tz
    return dt.replace(tzinfo=tz), False


def parse_ics(text: str, local_tz: tzinfo, calendar_name: str = "") -> list[dict]:
    """Return raw event records (with their repeat rule) from an .ics file."""
    events, cur = [], None
    for line in unfold(text):
        if line == "BEGIN:VEVENT":
            cur = {"exdates": [], "calendar": calendar_name}
            continue
        if line == "END:VEVENT":
            if cur and "start" in cur and cur.get("status") != "CANCELLED":
                events.append(cur)
            cur = None
            continue
        if cur is None:
            if line.startswith("X-WR-CALNAME:") and not calendar_name:
                calendar_name = _unescape(line.split(":", 1)[1])
            continue
        name, params, value = _parse_line(line)
        if name == "SUMMARY":
            cur["title"] = _unescape(value)
        elif name == "LOCATION":
            cur["location"] = _unescape(value)
        elif name == "DTSTART":
            cur["start"], cur["all_day"] = _parse_dt(value, params, local_tz)
        elif name == "DTEND":
            cur["end"], _ = _parse_dt(value, params, local_tz)
        elif name == "DURATION":
            cur["duration"] = _parse_duration(value)
        elif name == "RRULE":
            cur["rrule"] = dict(part.split("=", 1) for part in value.split(";") if "=" in part)
        elif name == "EXDATE":
            for v in value.split(","):
                cur["exdates"].append(_parse_dt(v, params, local_tz)[0])
        elif name == "STATUS":
            cur["status"] = value.upper()
        elif name == "RECURRENCE-ID":
            cur["recurrence_id"] = _parse_dt(value, params, local_tz)[0]
        elif name == "UID":
            cur["uid"] = value
    for e in events:
        if not e.get("calendar"):
            e["calendar"] = calendar_name
    return events


def _parse_duration(value: str) -> timedelta:
    m = re.fullmatch(r"(-)?P(?:(\d+)W)?(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?", value.strip())
    if not m:
        return timedelta(hours=1)
    sign = -1 if m.group(1) else 1
    w, d, h, mi, s = (int(x or 0) for x in m.groups()[1:])
    return sign * timedelta(weeks=w, days=d, hours=h, minutes=mi, seconds=s)


def expand(raw_events: list[dict], start: datetime, end: datetime) -> list[Event]:
    """Turn raw events (including repeating ones) into concrete events between start and end."""
    out: list[Event] = []
    overrides = {(e.get("uid"), e["recurrence_id"]) for e in raw_events if e.get("recurrence_id")}
    for e in raw_events:
        s = e["start"]
        length = (e["end"] - s) if "end" in e else e.get("duration", timedelta(days=1) if e.get("all_day") else timedelta(hours=1))
        title = e.get("title", "(no title)")
        excluded = set(e["exdates"])
        occurrences = _occurrences(s, e.get("rrule"), end) if (e.get("rrule") and not e.get("recurrence_id")) else [s]
        for occ in occurrences:
            if occ in excluded or (not e.get("recurrence_id") and (e.get("uid"), occ) in overrides):
                continue
            occ_end = occ + length
            if occ_end > start and occ < end:
                out.append(Event(title, occ, occ_end, bool(e.get("all_day")), e.get("location", ""), e.get("calendar", "")))
    out.sort(key=lambda ev: ev.start)
    return out


def _occurrences(first: datetime, rule: dict, window_end: datetime) -> list[datetime]:
    freq = rule.get("FREQ", "").upper()
    interval = max(1, int(rule.get("INTERVAL", "1") or 1))
    count = int(rule["COUNT"]) if rule.get("COUNT", "").isdigit() else None
    until = None
    if rule.get("UNTIL"):
        until, until_is_date = _parse_dt(rule["UNTIL"], {}, first.tzinfo or timezone.utc)
        if until_is_date:
            until += timedelta(days=1) - timedelta(seconds=1)  # the whole UNTIL day counts
    by_day = [d[-2:] for d in rule.get("BYDAY", "").split(",") if d[-2:] in DAY_CODES]
    tz = first.tzinfo

    def at(d: date) -> datetime:
        return datetime.combine(d, time(first.hour, first.minute, first.second), tzinfo=tz)

    results: list[datetime] = []
    n = 0
    step = 0
    while len(results) < MAX_OCCURRENCES:
        if freq == "DAILY":
            candidates = [at(first.date() + timedelta(days=step * interval))]
        elif freq == "WEEKLY":
            week_start = first.date() - timedelta(days=first.weekday()) + timedelta(weeks=step * interval)
            days = by_day or [DAY_CODES[first.weekday()]]
            candidates = sorted(at(week_start + timedelta(days=DAY_CODES.index(d))) for d in days)
        elif freq == "MONTHLY":
            try:
                candidates = [at(add_months(first.date(), step * interval))]
            except ValueError:
                candidates = []
        elif freq == "YEARLY":
            candidates = [at(add_months(first.date(), 12 * step * interval))]
        else:
            return [first]
        stop = False
        for c in candidates:
            if c < first:
                continue
            if (until and c > until) or (count is not None and n >= count) or c >= window_end:
                stop = True
                break
            results.append(c)
            n += 1
        if stop:
            break
        step += 1
    return results


def fetch_events(urls: list[str], local_tz: tzinfo, start: datetime, end: datetime) -> list[Event]:
    events: list[Event] = []
    errors = []
    for url in urls:
        url = url.replace("webcal://", "https://", 1)
        try:
            status, body, _ = http_get(url, timeout=30)
        except WebError as e:
            errors.append(str(e))
            continue
        if status != 200 or "BEGIN:VCALENDAR" not in body:
            errors.append(f"a calendar link answered with error {status}")
            continue
        events += expand(parse_ics(body, local_tz), start, end)
    if errors and not events:
        raise WebError("; ".join(errors))
    events.sort(key=lambda ev: ev.start)
    return events
