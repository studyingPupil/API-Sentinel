# API Sentinel / API 哨兵

AI API usage monitor. Track your OpenAI, Claude, DeepSeek, and GLM balances,
see daily burn rate, get alerts before running out, and open a live Dashboard.

监控多个 AI API 的剩余额度、消耗速度、预计耗尽时间，并在额度告急前多渠道推送预警。

---

## Two Modes / 两种部署方式

| | Docker Compose | GitHub Pages |
|---|---|---|
| **Dashboard** | `http://localhost:3000` | `https://用户名.github.io/api-sentinel/` |
| **Notifications** | Email / Telegram / Feishu / WeCom | Email only |
| **Database** | SQLite (local) | JSON file in repo |
| **Server required** | Yes (your machine) | No (GitHub runs it) |
| **Setup time** | ~5 minutes | ~3 minutes |
| **Cost** | Free (your hardware) | Free (GitHub Actions) |
| **Best for** | Full-featured, real-time | Zero-server, quick start |

---

## Mode 1: GitHub Pages (Recommended for most users)

Zero server. Zero cost. Fork, add 4 secrets, done.

### Setup / 快速配置

```
Step 1: Fork this repo
  Click "Fork" at top-right of this page.

Step 2: Add your secrets
  Your fork → Settings → Secrets and variables → Actions → New repository secret

    Name              Value (example)
    ─────────         ─────────────────────────────────
    DEEPSEEK_KEY      sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    EMAIL_PROVIDER    qq
    EMAIL_USER        yourname@qq.com
    EMAIL_AUTH        xxxxxxxxxxxxxxxx   (SMTP auth code, NOT password)

  Optional: OPENAI_KEY, CLAUDE_KEY (Admin Key required)

Step 3: Enable Pages
  Settings → Pages → Source: Deploy from a branch → Branch: main, Folder: /docs → Save

Step 4: Open Dashboard
  https://YOUR_USERNAME.github.io/api-sentinel/
  (replace YOUR_USERNAME with your GitHub username)
```

The Action runs every hour automatically. You can also trigger it manually from the Actions tab.

### Email Providers / 支持的邮箱

| Provider | SMTP | Port | Auth |
|----------|------|------|------|
| QQ Mail | smtp.qq.com | 587 | SMTP auth code / 授权码 |
| Gmail | smtp.gmail.com | 587 | App password |
| 163 Mail | smtp.163.com | 25 | SMTP auth code |
| Outlook | smtp.office365.com | 587 | Account password |
| Custom | (user-defined) | (user-defined) | — |

See [`config.example.yml`](config.example.yml) for full configuration reference.

---

## Mode 2: Docker Compose (Full-featured)

All notification channels. Real-time Dashboard with interactive charts.

```bash
git clone https://github.com/YOUR_USERNAME/api-sentinel.git
cd api-sentinel
docker compose up -d
```

Open `http://localhost:3000` → Add an API Key → Start monitoring.

### Notification Channels (Docker Mode)

| Channel | Config |
|---------|--------|
| **Email** | QQ / Gmail / 163 / Outlook / Custom SMTP |
| **Telegram** | Bot Token + Chat ID |
| **Feishu** | Webhook URL |
| **WeCom** | Webhook URL |

Three alert levels: 3 days → 24 hours → 6 hours. Same level never fires twice; upgrades always fire.

---

## Supported Providers

| Provider | Auto-refresh | Total credits | Progress bar | Prediction |
|----------|-------------|:---:|:---:|:---:|
| **OpenAI** | Billing API | Yes | Yes | Yes |
| **Claude** | Cost Report API (needs Admin Key) | Enterprise only | Enterprise only | Yes |
| **DeepSeek** | Balance API | No | No | Yes |
| **GLM** | Manual input / 手动输入 | No | No | Yes (after 2+ snapshots) |

---

## Features / 功能

- **Balance tracking** — current credits for each provider / 各 API 剩余额度
- **Burn rate** — 24h and 7-day average consumption / 日均消耗
- **Exhaustion prediction** — estimated date of depletion / 预计耗尽日期
- **Multi-channel alerts** — Email, Telegram, Feishu, WeCom / 多渠道通知
- **Dedup** — each alert level fires exactly once / 同等级不重复发送
- **Upgrade** — L1→L2→L3 always notified / 等级升级一定通知
- **Color-coded cards** — green (7d+) / yellow (3-7d) / orange (1-3d) / red (<24h)

---

## Architecture / 项目结构

```
api-sentinel/
├── .github/workflows/check.yml    # GitHub Actions (hourly check)
├── config.example.yml              # Secret reference
├── docker-compose.yml              # Docker mode
│
├── backend/                        # FastAPI (Docker mode)
│   └── app/
│       ├── adapters/               # Provider adapters (OpenAI, Claude, DeepSeek, GLM)
│       ├── notifiers/              # Notification channels (Email, Telegram, Feishu, WeCom)
│       ├── services/               # Fetcher, Predictor, Alerter
│       └── routers/                # REST API endpoints
│
├── frontend/                       # Next.js Dashboard (Docker mode)
│   └── src/components/             # ApiCard, UsageTrendChart, AddCredentialForm, etc.
│
├── scripts/
│   └── standalone.py               # Independent check script (GitHub Pages mode)
│
└── docs/                           # GitHub Pages static site
    ├── index.html                  # Bilingual Dashboard / 双语看板
    └── data.json                   # Usage data (auto-updated by Action)
```

---

## Development / 本地开发

```bash
# Backend (needs Python 3.12+)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (needs Node 18+)
cd frontend
npm install
npm run dev

# Standalone script (GitHub Pages mode test)
export DEEPSEEK_KEY=sk-xxx
export EMAIL_PROVIDER=qq
export EMAIL_USER=your@qq.com
export EMAIL_AUTH=your-auth-code
python scripts/standalone.py
```

---

## Tech Stack / 技术栈

| Layer | Tech |
|-------|------|
| Backend | FastAPI + SQLAlchemy + SQLite + APScheduler |
| Frontend | Next.js + TypeScript + TailwindCSS + Recharts |
| Standalone | Python 3.12 + stdlib (smtplib, urllib) |
| Deploy | Docker Compose / GitHub Actions + Pages |

---

## FAQ / 常见问题

<details>
<summary>Why does DeepSeek have no progress bar?</summary>
DeepSeek's API only returns current balance, not total credits. The Dashboard shows remaining credits and trend chart — just no percentage bar.
</details>

<details>
<summary>Why does Claude need an Admin Key?</summary>
Anthropic's billing API requires an Admin Key (sk-ant-admin...), not a regular API key. Create one at console.anthropic.com → Settings → Admin Keys.
</details>

<details>
<summary>Why is GLM manual input only?</summary>
Zhipu AI's open platform has no public billing REST API. Enter your balance manually from the console. The system still tracks trends across manual updates.
</details>

<details>
<summary>How do I get a QQ Mail SMTP auth code?</summary>
Login to mail.qq.com → Settings → Account → POP3/SMTP Service → Generate Authorization Code.
</details>

<details>
<summary>Can I change the check frequency?</summary>
Yes. Edit `.github/workflows/check.yml` — change the `cron` line. Default is `0 * * * *` (every hour).
</details>

---

## License / 许可证

MIT — see [LICENSE](LICENSE)
