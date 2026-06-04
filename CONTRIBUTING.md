# Contributing / 贡献指南

Thanks for considering contributing to API Sentinel.

## Architecture Overview / 项目架构

```
User adds API Key
     │
     ▼
Provider Adapter  ←──  fetches balance from external API
     │
     ▼
UsageSnapshot     ←──  stored in database / data.json
     │
     ▼
Predictor         ←──  calculates 24h/7d avg, predicts exhaustion
     │
     ├──→ Dashboard   (reads snapshots + metrics)
     └──→ Alerter     (checks thresholds, sends notifications)
```

## Two Deploy Modes / 两种部署模式

| Mode | Entry point | Data storage |
|------|------------|-------------|
| Docker | `backend/app/main.py` → FastAPI | SQLite |
| GitHub Pages | `scripts/standalone.py` | `docs/data.json` |

When adding features, ensure both modes work, or document the limitation.

---

## Adding a New Provider / 新增 Provider

### Step 1: Create Adapter

Create `backend/app/adapters/<provider>.py`:

```python
from app.adapters.base import BaseProviderAdapter, StandardUsageData

class NewProviderAdapter(BaseProviderAdapter):
    provider_name = "newprovider"          # unique, lowercase
    is_manual = False                      # True if no billing API

    async def fetch_usage(self, api_key):
        # Call the provider's billing API
        # Return StandardUsageData(total_credits, used_credits, remaining_credits, currency)
        pass

    async def validate_key(self, api_key):
        # Quick key validity check (e.g., list models)
        pass
```

### Step 2: Register

In `backend/app/adapters/registry.py`:

```python
from app.adapters.newprovider import NewProviderAdapter
ProviderRegistry.register(NewProviderAdapter())
```

### Step 3: Add to standalone.py (GitHub Pages mode)

In `scripts/standalone.py`, add a fetch function to the `PROVIDERS` dict:

```python
def fetch_newprovider(key):
    data = http_get("https://api.newprovider.com/v1/billing", ...)
    return {"total_credits": ..., "remaining_credits": ..., "currency": "USD"}

PROVIDERS = {
    ...
    "newprovider": (fetch_newprovider, os.getenv("NEWPROVIDER_KEY", "")),
}
```

### Step 4: Frontend

In `frontend/src/components/AddCredentialForm.tsx`:

```tsx
const PROVIDERS = [
  ...
  { value: "newprovider", label: "New Provider" },
];
```

In `docs/index.html`, add the badge style:

```css
.badge-newprovider { background:#...; color:#...; }
```

And add the label in `PROVIDER_LABELS`.

---

## Adding a New Notification Channel / 新增通知渠道

### Step 1: Create Notifier

Create `backend/app/notifiers/<channel>.py`:

```python
from app.notifiers.base import BaseNotifier

class NewChannelNotifier(BaseNotifier):
    channel_type = "newchannel"

    async def send(self, message, config):
        # Send message via the channel's API
        pass
```

### Step 2: Register

In `backend/app/notifiers/__init__.py`:

```python
from app.notifiers.newchannel import NewChannelNotifier
NOTIFIERS["newchannel"] = NewChannelNotifier()
```

### Step 3: Frontend

In `frontend/src/components/AddChannelForm.tsx`, add to `CHANNEL_TYPES`.

---

## Code Style / 代码风格

- **Python**: Keep type annotations minimal for backwards compatibility.
  Lazy-import heavy packages (`httpx`, `aiosmtplib`) inside methods.
- **TypeScript**: Use `@/` path aliases. Keep components self-contained in `src/components/`.
- **Commits**: `type: short description` (e.g., `feat: add Groq adapter`, `fix: dedup edge case`).

---

## PR Process / 提交流程

1. Fork the repo
2. Create a feature branch (`git checkout -b feat/groq-adapter`)
3. Make changes + verify:
   - Docker mode: `cd frontend && npm run build`
   - GitHub Pages mode: `python scripts/standalone.py`
4. Push and open a Pull Request
5. Describe what changed and why. If adding a provider, include a test result screenshot.

---

## Testing / 测试

### Backend (Docker mode)

```bash
cd backend
python verify_db.py          # Database schema
python verify_phase3.py       # OpenAI + predictor
python verify_deepseek_e2e.py <key>  # DeepSeek E2E
python verify_email_e2e.py    # Email notification
python phase8_audit.py        # Full system audit
```

### Standalone (GitHub Pages mode)

```bash
export DEEPSEEK_KEY=sk-xxx
export EMAIL_PROVIDER=qq EMAIL_USER=x@qq.com EMAIL_AUTH=xxx
python scripts/standalone.py
```

---

## Questions / 问题

Open a GitHub Issue. Include which mode you're using (Docker / GitHub Pages) and relevant error logs.
