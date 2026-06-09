# 🏏 PIA Cricket Ticket Monitor — GitHub Actions Setup

Runs **every 5 minutes for free**, 24/7, with zero PC required.  
Sends alerts via **Email + LINE** the moment CKT22 (Oct 3 14:00 Final) becomes available.

---

## Files in this repo

```
pia-monitor/
├── check_ticket.py              ← The checker script
└── .github/
    └── workflows/
        └── monitor.yml          ← GitHub Actions schedule config
```

---

## Setup (one-time, ~10 minutes)

### Step 1 — Create a free GitHub account
https://github.com → Sign up (free)

---

### Step 2 — Create a new repository

1. Click **"New repository"**
2. Name it: `pia-monitor`
3. Set to **Private** (keeps your secrets safe)
4. Click **"Create repository"**

---

### Step 3 — Upload the files

Option A — GitHub web UI (no Git needed):
1. Click **"Add file"** → **"Upload files"**
2. Upload `check_ticket.py`
3. Then create `.github/workflows/monitor.yml` by clicking **"Add file"** → **"Create new file"**,
   type `.github/workflows/monitor.yml` as the filename, paste the contents

Option B — Git (if you have it):
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/pia-monitor.git
git push -u origin main
```

---

### Step 4 — Add your secrets

This is how you pass credentials WITHOUT putting them in code.

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"** for each of these:

| Secret Name   | Value                                      |
|---------------|--------------------------------------------|
| `GMAIL_USER`  | your Gmail address                         |
| `GMAIL_PASS`  | your Gmail App Password (16-char)          |
| `NOTIFY_EMAIL`| email to receive alerts (same as above OK) |
| `LINE_TOKEN`  | your LINE Notify token                     |

**To get Gmail App Password:**
1. https://myaccount.google.com/security
2. Enable 2-Step Verification
3. Search "App passwords" → create one → copy the 16 characters

**To get LINE Notify token:**
1. https://notify-bot.line.me/my/
2. "Generate token" → name it "PIA Monitor" → select "1-on-1 chat with LINE Notify"
3. Copy the token

---

### Step 5 — Enable Actions (if needed)

Go to your repo → **Actions** tab → click **"I understand my workflows, go ahead and enable them"**

---

### Step 6 — Test it manually

1. Go to **Actions** tab
2. Click **"PIA Cricket Ticket Monitor"** on the left
3. Click **"Run workflow"** → **"Run workflow"**
4. Watch the logs — you should see "Still sold out" and receive a test... 

Actually, the script only notifies when tickets are found. To confirm it's working,
check the Actions run log — it should say:
`✅ Status: Still sold out (予定枚数終了). No action needed.`

---

## How to stop monitoring

Go to **Actions** → **"PIA Cricket Ticket Monitor"** → **"..."** → **Disable workflow**

---

## Important limits

- GitHub Actions free tier: **2,000 minutes/month**
- Each run takes ~20–30 seconds
- At 5-min intervals: ~8,640 runs/month = ~4,320 minutes/month

⚠️  This slightly exceeds the 2,000 min free limit for private repos.

**Solutions:**
- Use a **public repo** (unlimited minutes) — just don't put secrets in the code, use GitHub Secrets ✅
- OR change the cron to `*/10 * * * *` (every 10 min) → ~1,440 min/month ✅ (well within limit)

Recommendation: **public repo + every 10 minutes** = completely free, no limits hit.

---

## Cron schedule reference

Change this line in `monitor.yml`:
```yaml
- cron: '*/5 * * * *'   # every 5 minutes
- cron: '*/10 * * * *'  # every 10 minutes (recommended for free tier)
- cron: '*/15 * * * *'  # every 15 minutes
```
