#!/usr/bin/env python3
"""
PIA Ticket Checker — GitHub Actions version
Checks once per run. GitHub Actions calls this every 5 minutes via cron.
Secrets are passed as environment variables (set in GitHub repo Settings → Secrets).
"""

import os
import sys
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── Config ────────────────────────────────────────────────────────────────────
TARGET_URL  = "https://t.pia.jp/pia/ticketInformation.do?eventCd=2610317&rlsCd=002"
RESALE_URL  = TARGET_URL + "#Y15-resale"
TARGET_SESSION = "ＣＫＴ２２"           # Oct 3, 14:00 Gold Medal Final

# Secrets come from GitHub Actions environment variables
GMAIL_USER   = os.environ.get("GMAIL_USER", "")
GMAIL_PASS   = os.environ.get("GMAIL_PASS", "")
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "")
LINE_TOKEN   = os.environ.get("LINE_TOKEN", "")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── Notification functions ────────────────────────────────────────────────────

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


def send_line(message):
    if not LINE_TOKEN:
        print("⚠️  LINE skipped — token not set")
        return
    try:
        r = requests.post(
            "https://notify-api.line.me/api/notify",
            headers={"Authorization": f"Bearer {LINE_TOKEN}"},
            data={"message": message},
            timeout=10,
        )
        if r.status_code == 200:
            print("✅ LINE notification sent")
        else:
            print(f"❌ LINE failed: {r.status_code} — {r.text}")
    except Exception as e:
        print(f"❌ LINE error: {e}")


def notify_all(title, body, url):
    full_body = f"{body}\n\n🎟 Buy now:\n{url}"
    print(f"\n🚨 ALERT: {title}")
    send_email(f"🏏 {title}", full_body)
    send_line(f"\n🏏 {title}\n{full_body}")


# ── Main check ────────────────────────────────────────────────────────────────

def check():
    print(f"Fetching: {TARGET_URL}")
    try:
        r = requests.get(TARGET_URL, headers=HEADERS, timeout=20)
        r.encoding = "utf-8"
        html = r.text
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        sys.exit(0)  # Exit cleanly — don't fail the Action on network errors

    # 1. Check for resale section appearing anywhere on the page
    if "リセールチケットがあります" in html or "リセール申込" in html:
        notify_all(
            "🚨 RESALE TICKETS APPEARED — ACT NOW!",
            "Resale section is live on pia.jp for Cricket T20 Asian Games.",
            RESALE_URL,
        )
        sys.exit(0)

    # 2. Find the CKT22 session block
    idx = html.find(TARGET_SESSION)
    if idx == -1:
        print("⚠️  CKT22 block not found — page may have changed structure")
        sys.exit(0)

    # Extract ~1500 chars after the CKT22 marker (covers price + status button)
    block = html[idx: idx + 1500]

    # 3. Check if a buy button appeared
    if "枚数選択へ" in block or "発売中" in block:
        notify_all(
            "🚨 CKT22 TICKETS AVAILABLE — BUY NOW!",
            "Oct 3 14:00 Gold Medal Cricket Final — buy button is LIVE on pia.jp!",
            TARGET_URL,
        )
        sys.exit(0)

    # 4. Still sold out — log and exit cleanly
    if "予定枚数終了" in block:
        print("✅ Status: Still sold out (予定枚数終了). No action needed.")
    else:
        print("⚠️  Unknown status — no known markers found in CKT22 block.")

    sys.exit(0)


if __name__ == "__main__":
    check()
