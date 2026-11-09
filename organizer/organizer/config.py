"""Settings, all read from environment variables (or an optional `.env` file).

Nothing here is required. With no settings at all, the organizer still manages
tasks, notes and memories from typed commands. Each setting you add switches on
one more ability.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_MODEL = "claude-sonnet-5-5"


def load_dotenv(path: str) -> None:
    """Read KEY=value lines from a .env file into os.environ (existing values win)."""
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip().removeprefix("export ").strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


def _hhmm(value: str) -> str:
    """'8:00', '8', '08:00' -> '08:00' (falls back to 08:00 if unreadable)."""
    h, _, m = value.strip().partition(":")
    try:
        h_i, m_i = int(h), int(m or 0)
        if 0 <= h_i < 24 and 0 <= m_i < 60:
            return f"{h_i:02d}:{m_i:02d}"
    except ValueError:
        pass
    return "08:00"


def _list(name: str) -> list[str]:
    return [p.strip() for p in os.environ.get(name, "").split(",") if p.strip()]


@dataclass
class Settings:
    home: str = "organizer_data"
    # The brain
    anthropic_api_key: str = ""
    model: str = DEFAULT_MODEL
    max_steps: int = 12                   # tool calls the agent may make for one message
    daily_token_limit: int = 2_000_000    # stop calling Claude after this many tokens a day
    # Who you are and where you are
    user_name: str = ""
    timezone: str = ""
    # Email (IMAP to read, SMTP to send). Use an app password, not your main password.
    imap_host: str = ""
    imap_user: str = ""
    imap_password: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""
    # Calendars: secret iCal (.ics) addresses, comma-separated
    calendar_urls: list[str] = field(default_factory=list)
    # Web search (optional; falls back to DuckDuckGo + Wikipedia)
    brave_api_key: str = ""
    # Your documents folder, searchable by the assistant
    documents_dir: str = ""
    # Telegram
    telegram_token: str = ""
    telegram_user_id: str = ""
    # Web app
    web_host: str = "127.0.0.1"
    web_port: int = 8765
    web_token: str = ""
    # Daily briefing time, HH:MM in your timezone
    briefing_time: str = "08:00"

    @property
    def db_path(self) -> str:
        return os.path.join(self.home, "organizer.db")

    @property
    def has_llm(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def has_email(self) -> bool:
        return bool(self.imap_host and self.imap_user and self.imap_password)

    @property
    def can_send_email(self) -> bool:
        return bool(self.smtp_host and (self.smtp_user or self.imap_user) and (self.smtp_password or self.imap_password))

    @property
    def has_telegram(self) -> bool:
        return bool(self.telegram_token and self.telegram_user_id)

    def tz(self) -> tzinfo:
        if self.timezone:
            try:
                return ZoneInfo(self.timezone)
            except ZoneInfoNotFoundError:
                pass
        return datetime.now().astimezone().tzinfo  # the computer's own timezone

    def now(self) -> datetime:
        return datetime.now(self.tz())

    @classmethod
    def from_env(cls, home: str | None = None) -> "Settings":
        home = home or os.environ.get("ORGANIZER_HOME", "organizer_data")
        load_dotenv(os.path.join(home, ".env"))
        load_dotenv(".env")
        e = os.environ.get
        return cls(
            home=home,
            anthropic_api_key=e("ANTHROPIC_API_KEY", ""),
            model=e("ORGANIZER_MODEL", DEFAULT_MODEL),
            max_steps=_int("ORGANIZER_MAX_STEPS", 12),
            daily_token_limit=_int("ORGANIZER_DAILY_TOKEN_LIMIT", 2_000_000),
            user_name=e("ORGANIZER_USER_NAME", ""),
            timezone=e("ORGANIZER_TIMEZONE", ""),
            imap_host=e("IMAP_HOST", ""),
            imap_user=e("IMAP_USER", ""),
            imap_password=e("IMAP_PASSWORD", ""),
            smtp_host=e("SMTP_HOST", ""),
            smtp_port=_int("SMTP_PORT", 587),
            smtp_user=e("SMTP_USER", ""),
            smtp_password=e("SMTP_PASSWORD", ""),
            email_from=e("EMAIL_FROM", ""),
            calendar_urls=_list("CALENDAR_ICS_URLS"),
            brave_api_key=e("BRAVE_API_KEY", ""),
            documents_dir=e("ORGANIZER_DOCUMENTS_DIR", ""),
            telegram_token=e("TELEGRAM_BOT_TOKEN", ""),
            telegram_user_id=e("TELEGRAM_USER_ID", ""),
            web_host=e("ORGANIZER_WEB_HOST", "127.0.0.1"),
            web_port=_int("ORGANIZER_WEB_PORT", 8765),
            web_token=e("ORGANIZER_WEB_TOKEN", ""),
            briefing_time=_hhmm(e("ORGANIZER_BRIEFING_TIME", "08:00")),
        )

    def describe(self) -> list[tuple[str, bool, str]]:
        """(ability, switched on?, how to switch it on) for the `status` command."""
        return [
            ("Natural-language assistant (Claude)", self.has_llm, "set ANTHROPIC_API_KEY"),
            ("Read email", self.has_email, "set IMAP_HOST, IMAP_USER, IMAP_PASSWORD"),
            ("Send email (asks you first)", self.can_send_email, "also set SMTP_HOST"),
            ("Calendar", bool(self.calendar_urls), "set CALENDAR_ICS_URLS to your calendar's secret iCal address"),
            ("Search your documents", bool(self.documents_dir), "set ORGANIZER_DOCUMENTS_DIR, then run `index`"),
            ("Telegram bot", self.has_telegram, "set TELEGRAM_BOT_TOKEN and TELEGRAM_USER_ID"),
            ("Web search", True, "built in (BRAVE_API_KEY optional for better results)"),
        ]
