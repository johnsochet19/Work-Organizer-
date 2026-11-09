"""Email over IMAP (read) and SMTP (send).

Reading opens your inbox read-only, so nothing gets marked as read. Sending is
always held for your approval first (see tools.py).

For Gmail: turn on 2-step verification, create an app password at
myaccount.google.com/apppasswords, then set IMAP_HOST=imap.gmail.com,
SMTP_HOST=smtp.gmail.com, IMAP_USER=you@gmail.com, IMAP_PASSWORD=<app password>.
"""
from __future__ import annotations

import email
import email.policy
import email.utils
import imaplib
import re
import smtplib
import ssl
from email.message import EmailMessage

from .config import Settings
from .web import html_to_text


class MailError(Exception):
    pass


def _imap(s: Settings) -> imaplib.IMAP4_SSL:
    if not s.has_email:
        raise MailError("Email isn't set up. Set IMAP_HOST, IMAP_USER and IMAP_PASSWORD.")
    try:
        conn = imaplib.IMAP4_SSL(s.imap_host, ssl_context=ssl.create_default_context(), timeout=30)
        conn.login(s.imap_user, s.imap_password)
    except (imaplib.IMAP4.error, OSError) as e:
        raise MailError(f"couldn't sign in to {s.imap_host}: {e}") from e
    return conn


def _summary(uid: str, msg) -> dict:
    return {
        "id": uid,
        "from": str(msg.get("From", "")),
        "subject": str(msg.get("Subject", "")),
        "date": str(msg.get("Date", "")),
    }


def list_messages(s: Settings, unread_only: bool = True, search: str = "", limit: int = 10,
                  mailbox: str = "INBOX") -> list[dict]:
    conn = _imap(s)
    try:
        conn.select(mailbox, readonly=True)
        criteria = ["UNSEEN"] if unread_only else ["ALL"]
        if search:
            safe = re.sub(r'["\\\r\n]', " ", search)[:100]
            criteria += ["TEXT", f'"{safe}"']
        typ, data = conn.uid("SEARCH", None, *criteria)
        if typ != "OK":
            raise MailError("the mail server refused the search")
        uids = data[0].split()[-limit:][::-1]
        out = []
        for uid in uids:
            typ, parts = conn.uid("FETCH", uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
            if typ == "OK" and parts and isinstance(parts[0], tuple):
                msg = email.message_from_bytes(parts[0][1], policy=email.policy.default)
                out.append(_summary(uid.decode(), msg))
        return out
    finally:
        try:
            conn.logout()
        except Exception:
            pass


def read_message(s: Settings, uid: str, max_chars: int = 8000, mailbox: str = "INBOX") -> dict:
    if not str(uid).isdigit():
        raise MailError("That isn't a valid email id.")
    conn = _imap(s)
    try:
        conn.select(mailbox, readonly=True)
        typ, parts = conn.uid("FETCH", str(uid), "(BODY.PEEK[])")
        if typ != "OK" or not parts or not isinstance(parts[0], tuple):
            raise MailError(f"There's no email with id {uid}.")
        msg = email.message_from_bytes(parts[0][1], policy=email.policy.default)
    finally:
        try:
            conn.logout()
        except Exception:
            pass
    body = _body_text(msg)
    attachments = [p.get_filename() for p in msg.iter_attachments() if p.get_filename()] if msg.is_multipart() else []
    return {**_summary(str(uid), msg), "to": str(msg.get("To", "")), "message_id": str(msg.get("Message-ID", "")),
            "body": body[:max_chars], "truncated": len(body) > max_chars, "attachments": attachments}


def _body_text(msg) -> str:
    part = msg.get_body(preferencelist=("plain", "html"))
    if part is None:
        return ""
    try:
        text = part.get_content()
    except (LookupError, ValueError):
        text = part.get_payload(decode=True).decode("utf-8", "replace")
    if part.get_content_type() == "text/html":
        text = html_to_text(text)
    return text.strip()


def send_message(s: Settings, to: str, subject: str, body: str, cc: str = "", in_reply_to: str = "") -> str:
    if not s.can_send_email:
        raise MailError("Sending email isn't set up. Set SMTP_HOST (and IMAP_USER/IMAP_PASSWORD or SMTP_USER/SMTP_PASSWORD).")
    addresses = [a for _, a in email.utils.getaddresses([to, cc]) if a]
    if not addresses or not all(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", a) for a in addresses):
        raise MailError(f"'{to}' doesn't look like a valid email address.")
    user = s.smtp_user or s.imap_user
    msg = EmailMessage()
    msg["From"] = s.email_from or user
    msg["To"] = to
    if cc:
        msg["Cc"] = cc
    msg["Subject"] = subject
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg["Message-ID"] = email.utils.make_msgid()
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to
    msg.set_content(body)
    ctx = ssl.create_default_context()
    try:
        if s.smtp_port == 465:
            server = smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, context=ctx, timeout=30)
        else:
            server = smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=30)
            server.starttls(context=ctx)
        with server:
            server.login(user, s.smtp_password or s.imap_password)
            server.send_message(msg)
    except (smtplib.SMTPException, OSError) as e:
        raise MailError(f"sending failed: {e}") from e
    return f"Sent to {', '.join(addresses)}."
