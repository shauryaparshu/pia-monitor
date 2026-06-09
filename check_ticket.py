#!/usr/bin/env python3
"""
PIA Ticket Checker — GitHub Actions version v3
Checks once per run. GitHub Actions calls this every 5 minutes via cron.
Secrets are passed as environment variables (set in GitHub repo Settings → Secrets).

v3 fixes:
- Detection now based on actual HTML structure from page source inspection
- SOLD OUT state:    ticketSelect__icon--close">予定枚数終了   (unique to sold-out button)
- AVAILABLE state:   absence of above + button is NOT disabled
- Zero false positives — no page-wide text matching
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
BLOCK_SIZE     = 2000           # chars to scan after CKT22 marker

# Secrets from GitHub Actions environment variables
GMAIL_USER   = os.environ.get("GMAIL_USER", "")
GMAIL_PASS   = os.environ.get("GMAIL_PASS", "")
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "")
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── Detection strings (from actual page source inspection) ───────────────────
#
# SOLD OUT:    the close/X icon span contains this exact text
SOLD_OUT_STRING   = 'ticketSelect__icon--close">予定枚数終了'

# AVAILABLE:   the button exists and is NOT disabled
# When tickets are buyable, the button tag does NOT have "disabled"
# and the span contains "枚数選択へ" instead of "予定枚数終了"
AVAILABLE_STRING  = '枚数選択へ'

# ── Notifications ─────────────────────────────────────────────────────────────

def send_email(subject, body):
    if not GMAIL_USER or not GMAIL_PASS:
        print("⚠️  Email skipped — credentials not set")
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
        print("⚠️  Telegram skipped — credentials not set")
        return
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            timeout=10,
        )
        if r.status_code == 200:
            print("✅ Telegram sent")
        else:
            print(f"❌ Telegram failed: {r.status_code} — {r.text}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")


def notify_all(title, body):
    full_message = f"🏏 {title}\n\n{body}\n\n🎟 Buy now:\n{TARGET_URL}"
    print(f"\n🚨 ALERT: {title}")
    send_email(f"🏏 {title}", full_message)
    send_telegram(full_message)


# ── Main ──────────────────────────────────────────────────────────────────────

def check():
    print(f"Fetching: {TARGET_URL}")
    try:
        r = requests.get(TARGET_URL, headers=HEADERS, timeout=20)
        r.encoding = "utf-8"
        html = r.text
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        sys.exit(0)

    # Find the CKT22 section
    idx = html.find(TARGET_SESSION)
    if idx == -1:
        print("⚠️  CKT22 marker not found — page structure may have changed")
        sys.exit(0)

    # Extract only the CKT22 block
    block = html[idx: idx + BLOCK_SIZE]

    # ── Decision logic ────────────────────────────────────────────────────────
    # Step 1: Is it still sold out?
    if SOLD_OUT_STRING in block:
        print("✅ Status: SOLD OUT (予定枚数終了). Waiting for change.")
        sys.exit(0)

    # Step 2: Has the buy button appeared?
    if AVAILABLE_STRING in block:
        notify_all(
            "CKT22 TICKETS AVAILABLE — BUY NOW!",
            "Oct 3 14:00 Gold Medal Cricket Final\n'枚数選択へ' buy button detected in CKT22 block.\n\nOpen pia.jp IMMEDIATELY and buy!"
        )
        sys.exit(0)

    # Step 3: Unknown state — print block for debugging, no alert
    print("⚠️  Unknown state — neither sold-out string nor buy-button found.")
    print(f"CKT22 block (first 500 chars):\n{block[:500]}")
    sys.exit(0)


if __name__ == "__main__":
    check()
