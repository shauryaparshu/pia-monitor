#!/usr/bin/env python3
"""
PIA Ticket Checker — GitHub Actions version
Checks once per run. GitHub Actions calls this every 5 minutes via cron.
Secrets are passed as environment variables (set in GitHub repo Settings → Secrets).

v2 fixes:
- Removed false-positive resale check (リセール申込 is always on the page)
- Now only checks CKT22 block specifically for buy button OR resale button
- Added Telegram support, removed dead LINE Notify
"""

import os
import sys
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── Config ────────────────────────────────────────────────────────────────────
TARGET_URL     = "https://t.pia.jp/pia/ticketInformation.do?eventCd=2610317&rlsCd=002"
TARGET_SESSION = "ＣＫＴ２２"   # Oct 3, 14:00 Gold Medal Final
# How many chars to scan after CKT22 marker (covers price + button area)
BLOCK_SIZE     = 1500

# Secrets from GitHub Actions environment variables
GMAIL_USER        = os.environ.get("GMAIL_USER", "")
GMAIL_PASS        = os.environ.get("GMAIL_PASS", "")
NOTIFY_EMAIL      = os.environ.get("NOTIFY_EMAIL", "")
TELEGRAM_TOKEN    = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID  = os.environ.get("TELEGRAM_CHAT_ID", "")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── What to look for INSIDE the CKT22 block only ─────────────────────────────
#
# TRIGGER alert if ANY of these appear inside the CKT22 block:
#   枚数選択へ  = orange "Select quantity" buy button is live
#   発売中      = "On sale" status label
#   リセール可  = "Resale available" label on THIS specific ticket
#
# DO NOT alert on:
#   リセール申込  — this is a global footer link, always on the page, NOT CKT22-specific
#   リセールチケットがあります — also a page-wide banner, unreliable
#
AVAILABLE_TRIGGERS = [
    "枚数選択へ",   # Buy button appeared — act immediately
    "発売中",       # On-sale status
    "リセール可",   # Resale available label on this ticket block
]

SOLD_OUT_MARKER = "予定枚数終了"

# ── Notification functions ────────────────────────────────────────────────────

def send_email(subject, body):
    if not GMAIL_USER or not GMAIL_PASS:
        print("⚠️  Email skipped — GMAIL_USER/GMAIL_PASS not set")
        return
    try:
        msg = MIMEMultipart()
        msg["From"]    = GMAIL_USER
        msg["To"]      = NOTIFY_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, NOTIFY_EMAIL, msg.as_string())
        print("✅ Email sent")
    except Exception as e:
        print(f"❌ Email error: {e}")


def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️  Telegram skipped — TELEGRAM_TOKEN/TELEGRAM_CHAT_ID not set")
        return
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            timeout=10,
        )
        if r.status_code == 200:
            print("✅ Telegram notification sent")
        else:
            print(f"❌ Telegram failed: {r.status_code} — {r.text}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")


def notify_all(title, body):
    full_message = f"🏏 {title}\n\n{body}\n\n🎟 Buy now:\n{TARGET_URL}"
    print(f"\n🚨 ALERT: {title}")
    send_email(f"🏏 {title}", full_message)
    send_telegram(full_message)


# ── Main check ────────────────────────────────────────────────────────────────

def check():
    print(f"Fetching: {TARGET_URL}")
    try:
        r = requests.get(TARGET_URL, headers=HEADERS, timeout=20)
        r.encoding = "utf-8"
        html = r.text
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        sys.exit(0)

    # Find the CKT22 block
    idx = html.find(TARGET_SESSION)
    if idx == -1:
        print("⚠️  CKT22 block not found — page structure may have changed")
        sys.exit(0)

    # Extract only the CKT22 section (not the whole page)
    block = html[idx: idx + BLOCK_SIZE]

    print(f"📄 CKT22 block snippet (first 300 chars):\n{block[:300]}\n")

    # Check for sold out first
    if SOLD_OUT_MARKER in block:
        print("✅ Status: Still sold out (予定枚数終了). No action needed.")
        sys.exit(0)

    # Check for any availability trigger
    for trigger in AVAILABLE_TRIGGERS:
        if trigger in block:
            print(f"🔔 Trigger found: '{trigger}'")
            notify_all(
                "CKT22 TICKETS AVAILABLE — BUY NOW!",
                f"Oct 3 14:00 Gold Medal Cricket Final\nTrigger detected: {trigger}\n\nOpen pia.jp immediately and buy!",
            )
            sys.exit(0)

    # Neither sold out nor available — unknown state
    print("⚠️  Unknown status — neither sold-out nor buy-button found in CKT22 block.")
    print(f"Full block for debugging:\n{block}")
    sys.exit(0)


if __name__ == "__main__":
    check()
