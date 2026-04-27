"""
services/mail_service.py
Lightweight SMTP email sender — no Flask-Mail dependency.

Uses Python's built-in smtplib + ssl.
Configured entirely via environment variables (see .env).

Required .env keys:
    MAIL_SENDER_EMAIL   — Gmail address used to send  (e.g. yourapp@gmail.com)
    MAIL_SENDER_PASSWORD— Gmail App Password (NOT your normal Gmail password)
    MAIL_RECIPIENT      — Where contact form emails are delivered

Optional:
    MAIL_SMTP_HOST      — default: smtp.gmail.com
    MAIL_SMTP_PORT      — default: 587  (STARTTLS)

How to get a Gmail App Password:
  1. Enable 2-Step Verification on the sender Gmail account.
  2. Go to https://myaccount.google.com/apppasswords
  3. Create an app password → copy the 16-char code into MAIL_SENDER_PASSWORD.
"""
import os
import ssl
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from datetime             import datetime, timezone

logger = logging.getLogger(__name__)


def _cfg(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


def send_contact_email(sender_name: str, sender_email: str, message: str) -> bool:
    """
    Send a contact-form submission to the configured recipient.

    Returns True on success, False on any failure.
    Caller should treat False as non-fatal (submission is already persisted
    to MongoDB) and still show the user a success message.
    """
    smtp_host  = _cfg("MAIL_SMTP_HOST",      "smtp.gmail.com")
    smtp_port  = int(_cfg("MAIL_SMTP_PORT",  "587"))
    from_addr  = _cfg("MAIL_SENDER_EMAIL")
    password   = _cfg("MAIL_SENDER_PASSWORD")
    to_addr    = _cfg("MAIL_RECIPIENT")

    # ── Guard: skip silently if SMTP is not configured ────────────────────────
    if not all([from_addr, password, to_addr]):
        logger.warning(
            "[Mail] SMTP not configured — skipping email. "
            "Set MAIL_SENDER_EMAIL, MAIL_SENDER_PASSWORD, MAIL_RECIPIENT in .env"
        )
        return False

    # ── Build message ─────────────────────────────────────────────────────────
    submitted_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    subject = f"[MSTA Contact] New message from {sender_name}"

    # Plain-text body
    plain_body = (
        f"You have a new contact form submission on MSTA.\n\n"
        f"Name:    {sender_name}\n"
        f"Email:   {sender_email}\n"
        f"Time:    {submitted_at}\n\n"
        f"Message:\n{message}\n\n"
        f"---\nReply directly to this email to respond to {sender_name}."
    )

    # HTML body — clean, readable in Gmail
    html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"></head>
<body style="font-family:Inter,Arial,sans-serif;background:#f8fafc;margin:0;padding:32px 16px">
  <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:12px;
              border:1px solid #e2e8f0;box-shadow:0 2px 8px rgba(0,0,0,.06);overflow:hidden">

    <!-- Header -->
    <div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);padding:24px 28px">
      <h1 style="margin:0;color:#fff;font-size:1.1rem;font-weight:700;letter-spacing:-.02em">
        📬 New Contact Message — MSTA
      </h1>
    </div>

    <!-- Body -->
    <div style="padding:28px">
      <table style="width:100%;border-collapse:collapse;font-size:.9rem;color:#334155">
        <tr>
          <td style="padding:8px 0;font-weight:600;color:#64748b;width:80px">Name</td>
          <td style="padding:8px 0">{sender_name}</td>
        </tr>
        <tr>
          <td style="padding:8px 0;font-weight:600;color:#64748b">Email</td>
          <td style="padding:8px 0">
            <a href="mailto:{sender_email}" style="color:#6366f1;text-decoration:none">{sender_email}</a>
          </td>
        </tr>
        <tr>
          <td style="padding:8px 0;font-weight:600;color:#64748b">Time</td>
          <td style="padding:8px 0">{submitted_at}</td>
        </tr>
      </table>

      <hr style="border:none;border-top:1px solid #e2e8f0;margin:20px 0">

      <p style="font-weight:600;color:#64748b;font-size:.85rem;margin:0 0 10px">Message</p>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
                  padding:16px;font-size:.9rem;color:#1e293b;line-height:1.65;
                  white-space:pre-wrap">{message}</div>
    </div>

    <!-- Footer -->
    <div style="padding:16px 28px;background:#f8fafc;border-top:1px solid #e2e8f0;
                font-size:.78rem;color:#94a3b8">
      Sent from the MSTA contact form · Reply to this email to respond directly.
    </div>
  </div>
</body>
</html>
"""

    # ── Assemble MIME ─────────────────────────────────────────────────────────
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"MSTA Contact <{from_addr}>"
    msg["To"]      = to_addr
    msg["Reply-To"] = f"{sender_name} <{sender_email}>"   # reply goes to submitter

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body,  "html",  "utf-8"))

    # ── Send via STARTTLS ─────────────────────────────────────────────────────
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(from_addr, password)
            server.sendmail(from_addr, to_addr, msg.as_string())

        logger.info(
            "[Mail] Contact email sent to %s from %s <%s>",
            to_addr, sender_name, sender_email
        )
        return True

    except smtplib.SMTPAuthenticationError:
        logger.error(
            "[Mail] SMTP authentication failed. "
            "Make sure MAIL_SENDER_PASSWORD is a Gmail App Password, "
            "not your regular Gmail password."
        )
    except smtplib.SMTPException as exc:
        logger.error("[Mail] SMTP error: %s", exc)
    except OSError as exc:
        logger.error("[Mail] Network error sending email: %s", exc)

    return False
