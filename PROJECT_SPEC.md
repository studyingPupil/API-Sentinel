# API Sentinel — Project Specification v2.0

> Self-hosted · Single-user · Zero-config · 5-minute deploy
>
> 面向个人开发者与 AI 创业团队的轻量级 API 额度监控工具

---

## 1. 项目定位

| 维度 | 说明 |
|------|------|
| **是什么** | 一个自部署的 AI API 额度监控面板，跑在本地或服务器上 |
| **面向谁** | 个人开发者、AI 创业团队、重度 API 用户 |
| **不是** SaaS / 多租户平台 / 企业管理系统 |
| **部署方式** | `git clone` → `docker compose up -d` → 浏览器打开 → 填入 API Key |
| **核心能力** | 查看余额、了解消耗速度、预测耗尽时间、收到预警通知 |

## 2. 设计原则

```
原则 1 — 极简
  删掉一切非必要功能。一个功能要么 V1 有，要么明确标注"不做"。

原则 2 — 5 分钟部署
  git clone → docker compose up -d → 浏览器打开，整个过程不超过 5 分钟。

原则 3 — 轻量技术栈
  禁止：Kubernetes / Redis / RabbitMQ / Elasticsearch / 微服务
  只用：FastAPI + SQLite + Next.js + Docker Compose

原则 4 — 单用户模式
  V1 不做注册、登录、JWT、用户管理、多租户。
  部署者即管理员，所有数据本地存储。

原则 5 — 开源优先
  所有设计考虑 GitHub 开源、社区贡献、可维护性。
  不依赖任何商业 SaaS 服务。
```

---

## 3. MVP 功能范围

### 3.1 Provider 支持

| 版本 | Provider | 状态 |
|------|----------|------|
| **V1 (MVP)** | OpenAI | Phase 3 |
| **V1 (MVP)** | Claude (Anthropic) | Phase 6 |
| V1.1 | DeepSeek | Phase 7 |
| V1.2 | GLM (智谱) | Phase 8 |
| Future | Gemini / Azure OpenAI / Groq / OpenRouter | 社区贡献 |

### 3.2 Dashboard 功能

首页展示每个 Provider 的卡片：

| 数据项 | 说明 |
|--------|------|
| 当前余额 | `total - used`，精确到 $0.01 |
| 最近 24h 消耗 | 过去 24 小时内使用量之和 |
| 最近 7d 平均消耗 | 过去 7 天日均消耗 |
| 预计耗尽时间 | `剩余额度 / 7d日均消耗`，输出具体日期 |

**颜色规则**：

| 颜色 | 条件 | 含义 |
|------|------|------|
| 🟢 绿色 | 预计 > 7 天耗尽 | 正常 |
| 🟡 黄色 | 预计 3~7 天耗尽 | 关注 |
| 🟠 橙色 | 预计 24h~3 天耗尽 | 警告 |
| 🔴 红色 | 预计 < 24h 耗尽 | 紧急 |

### 3.3 通知系统

**支持渠道**：

| 渠道 | V1 包含 |
|------|---------|
| Email (SMTP) | 是 |
| 飞书 Webhook | 是 |
| 企业微信 Webhook | 是 |
| Telegram Bot | 是 |

**预警等级**：

| 等级 | 触发条件 | 行为 |
|------|----------|------|
| Level 1 | 预计 3 天耗尽 | 通知一次 |
| Level 2 | 预计 24 小时耗尽 | 通知一次 |
| Level 3 | 预计 6 小时耗尽 | 通知一次 |

**防重复规则**：同一 (Provider + Level + Channel) 只发送一次。状态升级（如 Level 1 → Level 2）时再次发送。

### 3.4 数据同步

- 默认每 **1 小时**同步一次
- 用户可在设置中修改：30 分钟 / 1 小时 / 6 小时 / 12 小时
- 每次同步：遍历所有已配置的 API Key → 调用对应 Provider Adapter → 存储 UsageSnapshot

### 3.5 预测逻辑

```
仅使用：最近 7 天移动平均

预计耗尽时间 (天) = 剩余额度 / 7天日均消耗

特殊情况处理：
- 数据不足 7 天：使用已有数据的日均消耗
- 数据不足 24 小时：显示 "数据收集中，预计 24h 后显示预测"
- 无消耗数据：显示 "暂无消耗数据"

明确禁止：AI 预测 / 机器学习 / LSTM / 时间序列模型 / 任何高级统计方法
```

---

## 4. 删除项清单

以下功能 **明确不做**，列入此清单以防止范围蔓延：

| 删除项 | 原因 |
|--------|------|
| 用户注册 / 登录 | 单用户模式，不需要 |
| JWT 认证 | 无用户系统，不需要 |
| 多租户 | 单用户模式 |
| OAuth / SSO | 无用户系统 |
| 角色权限 (RBAC) | 单用户 = 唯一管理员 |
| API Key 用量图表共享 | 本地工具，不分享 |
| AI 预测模型 | 只用 7 天移动平均 |
| 自定义预警阈值 | V1 使用固定三级阈值 |
| 多语言 / i18n | V1 仅中文 + 英文 |
| 暗黑模式 | V2 考虑 |
| 移动端 App | 仅 Web Dashboard |
| 账单导出 / PDF 报告 | V2 考虑 |
| 多 Provider 聚合视图 | V2 考虑 |
| Kubernetes / Helm Chart | 仅 Docker Compose |
| Redis / Celery | 使用 APScheduler 内存调度 |
| PostgreSQL / MySQL | 仅 SQLite |

---

## 5. 系统架构图

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Compose                        │
│                                                         │
│  ┌──────────────────┐     ┌─────────────────────┐       │
│  │   Frontend       │     │   Backend            │       │
│  │   (Next.js)      │────▶│   (FastAPI :8000)    │       │
│  │   :3000          │     │                      │       │
│  │                  │     │  ┌────────────────┐  │       │
│  │  - Dashboard     │     │  │ Scheduler      │  │       │
│  │  - Settings      │     │  │ (APScheduler)  │──┼───────┼──▶ OpenAI API
│  │  - Charts        │     │  └────────────────┘  │       │   Claude API
│  │                  │     │                      │       │   DeepSeek API
│  └──────────────────┘     │  ┌────────────────┐  │       │   GLM API
│                           │  │ Notifiers      │──┼───────┼──▶ SMTP / Telegram
│                           │  │ - Email        │  │       │   飞书 / 企业微信
│                           │  │ - Telegram     │  │       │
│                           │  │ - Feishu       │  │       │
│                           │  │ - WeCom        │  │       │
│                           │  └────────────────┘  │       │
│                           │                      │       │
│                           │  ┌────────────────┐  │       │
│                           │  │ SQLite          │  │       │
│                           │  │ (api_sentinel   │  │       │
│                           │  │  .db)           │  │       │
│                           │  └────────────────┘  │       │
│                           └─────────────────────┘       │
└─────────────────────────────────────────────────────────┘
```

**组件说明**：

| 组件 | 端口 | 职责 |
|------|------|------|
| Frontend (Next.js) | 3000 | Web Dashboard，通过 `/api/*` 代理到 Backend |
| Backend (FastAPI) | 8000 | REST API + 定时任务 + 通知发送 |
| SQLite | 文件 | 所有数据存储在 `data/api_sentinel.db` |
| APScheduler | 内存 | 定时触发 Usage 同步 + 预警检查 |

---

## 6. 数据流图

```
                        ┌─────────────┐
                        │   User      │
                        └──────┬──────┘
                               │
                    ┌──────────▼──────────┐
                    │   Dashboard (Web)   │
                    │   添加 API Key       │
                    │   查看余额 & 预测    │
                    │   管理通知渠道       │
                    └──────────┬──────────┘
                               │ HTTP REST
                    ┌──────────▼──────────┐
                    │   FastAPI Backend   │
                    └──┬───────┬───────┬──┘
                       │       │       │
         ┌─────────────▼─┐ ┌──▼────┐ ┌▼────────────┐
         │  Scheduler    │ │  API  │ │  Notifier   │
         │  (每小时)      │ │Routes │ │  (预警触发)  │
         └───────┬───────┘ └──┬────┘ └──────┬──────┘
                 │            │             │
    ┌────────────▼────┐       │    ┌────────▼────────┐
    │ Provider Adapter│       │    │ Email / Telegram│
    │ - OpenAI        │       │    │ 飞书 / 企业微信  │
    │ - Claude        │       │    └─────────────────┘
    │ - DeepSeek      │       │
    │ - GLM           │       │
    └────────┬────────┘       │
             │                │
    ┌────────▼────────────────▼──────┐
    │          SQLite                 │
    │  api_credentials               │
    │  usage_snapshots               │
    │  notification_channels         │
    │  notification_logs             │
    │  settings                      │
    └────────────────────────────────┘
```

**数据流步骤**：

```
步骤 1 — 用户添加 API Key
  Browser → POST /api/credentials → 存入 api_credentials 表

步骤 2 — 定时同步 Usage
  Scheduler 触发 → fetch_all_usage()
    → 遍历 credentials → Adapter.fetch_usage(api_key)
    → 存入 usage_snapshots 表

步骤 3 — 前端查询
  Browser → GET /api/credentials → 返回列表含最新快照
  Browser → GET /api/credentials/{id}/metrics → 返回计算指标
  Browser → GET /api/credentials/{id}/history → 返回历史数据（用于图表）

步骤 4 — 预警检查
  Scheduler 触发 → check_alerts()
    → 遍历 credentials → calculate_prediction()
    → 比对预警阈值 → 查 notification_logs 去重
    → 调用 Notifier.send() → 写入 notification_logs
```

---

## 7. 数据库设计

### 7.1 ER 图

```
┌──────────────────┐       ┌────────────────────┐
│ api_credentials   │       │ usage_snapshots     │
├──────────────────┤       ├────────────────────┤
│ id (PK)          │──┐    │ id (PK)            │
│ provider         │  │    │ credential_id (FK) │◀┐
│ api_key (加密)    │  └───▶│ total_credits      │ │
│ alias            │       │ used_credits       │ │
│ is_active        │       │ remaining_credits  │ │
│ created_at       │       │ fetched_at         │ │
│ updated_at       │       └────────────────────┘ │
└──────────────────┘                              │
                                                  │
┌──────────────────────┐                          │
│ notification_channels│                          │
├──────────────────────┤                          │
│ id (PK)              │                          │
│ channel_type         │                          │
│ config_json          │                          │
│ enabled              │                          │
│ created_at           │                          │
└──────────────────────┘                          │
                                                  │
┌──────────────────────┐                          │
│ notification_logs    │                          │
├──────────────────────┤                          │
│ id (PK)              │                          │
│ channel_id (FK)      │──▶ notification_channels │
│ credential_id (FK)   │──┘                       │
│ alert_level          │                          │
│ message              │                          │
│ sent_at              │                          │
└──────────────────────┘                          │
                                                  │
┌──────────────────────┐                          │
│ settings             │                          │
├──────────────────────┤                          │
│ key (PK)             │                          │
│ value                │                          │
└──────────────────────┘                          │
```

### 7.2 表结构

**api_credentials** — 存储用户添加的 API Key

| 列 | 类型 | 说明 |
|----|------|------|
| id | INTEGER PK | 自增主键 |
| provider | VARCHAR(20) | openai / claude / deepseek / glm |
| api_key | TEXT | 加密存储的 API Key |
| alias | VARCHAR(100) | 用户自定义别名，如 "公司 OpenAI 账号" |
| is_active | BOOLEAN | 是否启用同步，默认 TRUE |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 最后更新时间 |

**usage_snapshots** — 每次同步的使用量快照

| 列 | 类型 | 说明 |
|----|------|------|
| id | INTEGER PK | 自增主键 |
| credential_id | INTEGER FK | 关联 api_credentials.id |
| total_credits | FLOAT | 总额度 |
| used_credits | FLOAT | 已使用额度 |
| remaining_credits | FLOAT | 剩余额度 |
| currency | VARCHAR(10) | 币种，默认 USD |
| fetched_at | DATETIME | 数据获取时间 |

**notification_channels** — 通知渠道配置

| 列 | 类型 | 说明 |
|----|------|------|
| id | INTEGER PK | 自增主键 |
| channel_type | VARCHAR(20) | email / telegram / feishu / wecom |
| config_json | TEXT | JSON 配置，如 `{"smtp_host":"...","to":"..."}` |
| enabled | BOOLEAN | 是否启用 |
| created_at | DATETIME | 创建时间 |

**notification_logs** — 通知发送记录（用于去重）

| 列 | 类型 | 说明 |
|----|------|------|
| id | INTEGER PK | 自增主键 |
| channel_id | INTEGER FK | 关联 notification_channels.id |
| credential_id | INTEGER FK | 关联 api_credentials.id |
| alert_level | INTEGER | 1 / 2 / 3 |
| message | TEXT | 通知内容 |
| sent_at | DATETIME | 发送时间 |

**settings** — 系统设置（Key-Value）

| 列 | 类型 | 说明 |
|----|------|------|
| key | VARCHAR(100) PK | 设置键名 |
| value | TEXT | 设置值 |

**预设 Settings**：

| Key | 默认值 | 说明 |
|-----|--------|------|
| sync_interval_minutes | 60 | 同步间隔（30/60/360/720） |
| data_retention_days | 90 | 历史数据保留天数 |

---

## 8. Provider Adapter 架构

### 8.1 抽象基类

```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class StandardUsageData:
    """所有 Provider Adapter 必须返回此统一格式"""
    total_credits: float
    used_credits: float
    remaining_credits: float
    currency: str = "USD"
    fetched_at: str = ""  # ISO 8601

class BaseProviderAdapter:
    """Provider Adapter 抽象基类"""

    provider_name: str  # "openai" / "claude" / "deepseek" / "glm"

    async def fetch_usage(self, api_key: str) -> StandardUsageData:
        raise NotImplementedError

    async def validate_key(self, api_key: str) -> bool:
        """验证 API Key 是否有效"""
        raise NotImplementedError
```

### 8.2 各 Provider 实现说明

**OpenAI Adapter**：
- 调用 `GET https://api.openai.com/v1/usage?date={today}`
- 或从 Dashboard Billing API 获取
- 返回总额度 (hard_limit) / 已用量 (total_usage) / 剩余

**Claude Adapter**：
- 调用 Anthropic Console API 或解析 Billing 页面
- Anthropic 目前 Usage API 有限，可能需要解析 organization 级别的 usage endpoint
- **Phase 0 必须先验证 API 可用性**

**DeepSeek Adapter**：
- 调用 DeepSeek Platform API
- `GET https://api.deepseek.com/v1/billing/usage`
- **Phase 0 需验证**

**GLM Adapter**：
- 调用智谱开放平台 API
- **Phase 0 需验证**

### 8.3 ProviderRegistry

```python
class ProviderRegistry:
    """Provider 注册中心，用于按名称查找 Adapter"""

    _adapters: dict[str, BaseProviderAdapter] = {}

    @classmethod
    def register(cls, adapter: BaseProviderAdapter):
        cls._adapters[adapter.provider_name] = adapter

    @classmethod
    def get(cls, provider_name: str) -> BaseProviderAdapter:
        if provider_name not in cls._adapters:
            raise ValueError(f"Unknown provider: {provider_name}")
        return cls._adapters[provider_name]

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._adapters.keys())
```

---

## 9. Dashboard 页面设计

### 9.1 页面结构

```
┌──────────────────────────────────────────────┐
│  API Sentinel                    [设置 ⚙]    │
├──────────────────────────────────────────────┤
│                                              │
│  ┌──────────────┐  ┌──────────────┐          │
│  │   OpenAI     │  │   Claude     │          │
│  │   my-key-1   │  │   pro-key    │          │
│  │              │  │              │          │
│  │ $45.20 /100 │  │ $8.50 /500  │          │
│  │ ██████░░░ 45%│  │ ██░░░░░░░ 2%│          │
│  │              │  │              │          │
│  │ 24h: $3.20  │  │ 24h: $12.50 │          │
│  │ 7d avg: $2.80│  │ 7d avg: $10.20│        │
│  │              │  │              │          │
│  │ 🟢 预计16天  │  │ 🔴 预计20小时│          │
│  └──────────────┘  └──────────────┘          │
│                                              │
│  ┌──────────────────────────────────────┐    │
│  │  + 添加 API Key                       │    │
│  └──────────────────────────────────────┘    │
│                                              │
│  ┌──────────────────────────────────────┐    │
│  │  OpenAI 消耗趋势 (7天)                │    │
│  │  📈 折线图                           │    │
│  │  [7天] [30天]                        │    │
│  └──────────────────────────────────────┘    │
└──────────────────────────────────────────────┘
```

### 9.2 页面路由

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | Dashboard 首页 | API 额度卡片 + 消耗趋势图 |
| `/settings` | 设置页面 | 通知渠道管理 + 同步间隔设置 |

### 9.3 设置页面内容

```
设置页面:
├── 同步设置
│   └── 同步间隔: [30分钟] [1小时] [6小时] [12小时]
│
├── 通知渠道
│   ├── [已配置列表]
│   │   ├── Email → user@example.com  [启用开关] [删除]
│   │   └── 飞书 → webhook-url        [启用开关] [删除]
│   └── [+ 添加通知渠道]
│       ├── 类型: [Email] [Telegram] [飞书] [企业微信]
│       ├── 配置表单 (根据类型动态切换)
│       └── [测试发送] [保存]
│
└── API Key 管理
    ├── [已配置 Key 列表]
    │   ├── OpenAI (my-key-1)    [启用开关] [删除]
    │   └── Claude (pro-key)     [启用开关] [删除]
    └── [+ 添加 API Key]
        ├── Provider: [OpenAI] [Claude] [DeepSeek] [GLM]
        ├── API Key: [输入框]
        ├── 别名: [输入框]
        └── [保存]
```

### 9.4 前端组件树

```
Layout
├── Navbar (Logo + 设置入口)
├── DashboardPage
│   ├── ApiCardGrid
│   │   └── ApiCard (×N)
│   │       ├── ProviderBadge
│   │       ├── BalanceBar (进度条)
│   │       ├── StatsRow (24h / 7d avg)
│   │       └── PredictionBadge (颜色标签)
│   ├── AddApiKeyButton
│   └── UsageTrendChart (Recharts 折线图)
│       └── TimeRangeToggle [7天 | 30天]
│
└── SettingsPage
    ├── SyncIntervalSelector
    ├── NotificationChannelList
    │   └── NotificationChannelItem (×N)
    ├── AddChannelForm
    │   └── ChannelConfigFields (动态表单)
    ├── CredentialList
    │   └── CredentialItem (×N)
    └── AddCredentialForm
```

---

## 10. 通知系统设计

### 10.1 状态机模型

```
               ┌──────────┐
               │  NORMAL  │  (无需通知)
               └────┬─────┘
                    │ 剩余天数 ≤ 3
                    ▼
               ┌──────────┐
               │ LEVEL_1  │  (发送 3 天预警)
               └────┬─────┘
                    │ 剩余天数 ≤ 1
                    ▼
               ┌──────────┐
               │ LEVEL_2  │  (发送 24 小时预警)
               └────┬─────┘
                    │ 剩余天数 ≤ 0.25
                    ▼
               ┌──────────┐
               │ LEVEL_3  │  (发送 6 小时预警)
               └──────────┘
```

**状态转换规则**：
- 只能从低级别升级到高级别（NORMAL → L1 → L2 → L3）
- 不会降级（充值后额度恢复，状态重置为 NORMAL）

### 10.2 去重逻辑

```python
async def should_send_alert(
    credential_id: int,
    channel_id: int,
    alert_level: int
) -> bool:
    """
    检查是否应该发送通知。
    同一 (credential_id, channel_id, alert_level) 只发送一次。
    如果已存在更高等级的记录，低等级不再发送。
    """
    existing = await db.query(NotificationLog).filter(
        NotificationLog.credential_id == credential_id,
        NotificationLog.channel_id == channel_id,
        NotificationLog.alert_level >= alert_level,
    ).first()

    return existing is None
```

### 10.3 通知渠道实现

**Email**：
- 使用 `aiosmtplib`
- 配置项：SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, TO_EMAIL
- 模板：`[API Sentinel] {provider} ({alias}) 额度预计 {days} 天后耗尽`

**Telegram**：
- 使用 `httpx` 调用 Bot API
- 配置项：BOT_TOKEN, CHAT_ID
- 发送 `sendMessage`

**飞书**：
- 使用 `httpx` 调用 Webhook
- 配置项：WEBHOOK_URL
- 发送 Markdown 格式卡片消息

**企业微信**：
- 使用 `httpx` 调用 Webhook
- 配置项：WEBHOOK_URL
- 发送 Markdown 格式消息

### 10.4 消息模板

```
标题: [API Sentinel] {provider} ({alias}) 额度预警

Level 1 (3天):
  你的 {provider} API Key "{alias}" 预计在 {date} 耗尽（约 3 天后）。
  建议提前充值以确保服务不中断。

Level 2 (24小时):
  ⚠️ 你的 {provider} API Key "{alias}" 预计在 {date} 耗尽（约 24 小时内）。
  请尽快充值！

Level 3 (6小时):
  🚨 紧急！你的 {provider} API Key "{alias}" 预计在 {date} 耗尽（约 6 小时内）。
  请立即充值，否则服务将中断！

当前余额: ${remaining}
7天日均消耗: ${daily_avg}
```

---

## 11. API Endpoints

### 11.1 Credential API

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/credentials` | 获取所有 API Key 列表（含最新快照数据） |
| POST | `/api/credentials` | 添加 API Key，立即触发首次同步 |
| DELETE | `/api/credentials/{id}` | 删除 API Key 及关联的历史数据 |
| PUT | `/api/credentials/{id}` | 更新 API Key / alias / is_active |
| POST | `/api/credentials/{id}/sync` | 手动触发该 Key 的 Usage 同步 |

### 11.2 Usage & Metrics API

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/credentials/{id}/metrics` | 获取消耗指标与预测 |
| GET | `/api/credentials/{id}/history?days=7` | 获取历史消耗数据（用于折线图） |

### 11.3 Notification API

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/notifications/channels` | 获取所有通知渠道 |
| POST | `/api/notifications/channels` | 添加通知渠道 |
| DELETE | `/api/notifications/channels/{id}` | 删除通知渠道 |
| PUT | `/api/notifications/channels/{id}` | 更新通知渠道配置 |
| POST | `/api/notifications/channels/{id}/test` | 发送测试通知 |

### 11.4 Settings API

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/settings` | 获取所有系统设置 |
| PUT | `/api/settings/{key}` | 更新指定设置 |

### 11.5 Health API

| Method | Path | 说明 |
|--------|------|------|
| GET | `/api/health` | 健康检查，返回版本号与运行状态 |

---

## 12. 开发阶段规划

### Phase 0 — API 可行性验证 (当前)

**目标**：确认目标 Provider 是否存在可用的 Usage / Billing 接口，并提供可调通的 Python 脚本。

| 任务 | 产出 |
|------|------|
| 0.1 验证 OpenAI Usage API | 可运行的 Python 脚本，成功返回 usage 数据 |
| 0.2 验证 Claude Usage API | 可运行的 Python 脚本，明确 Anthropic 的 usage 获取方式 |
| 0.3 验证 DeepSeek Usage API | 可运行的 Python 脚本 |
| 0.4 验证 GLM Usage API | 可运行的 Python 脚本 |
| 0.5 确认各 API 返回字段映射表 | 文档：每个 Provider 的字段 → StandardUsageData 的映射关系 |

**Phase 0 完成的标志**：4 个 Python 脚本均可独立运行并成功获取 usage 数据。

### Phase 1 — 项目骨架

| 任务 | 说明 |
|------|------|
| 1.1 初始化 `backend/` 目录结构 | FastAPI + SQLAlchemy + APScheduler 骨架 |
| 1.2 初始化 `frontend/` 目录结构 | `create-next-app` + TypeScript + TailwindCSS |
| 1.3 编写 `docker-compose.yml` | Frontend :3000 + Backend :8000 + SQLite volume |
| 1.4 编写 `README.md` | 项目介绍 + 本地开发指南 + Docker 部署指南 |
| 1.5 配置 `Dockerfile` (backend + frontend) | 多阶段构建，生产镜像尽量小 |
| 1.6 添加 `.gitignore` / `.dockerignore` | |
| 1.7 添加 `LICENSE` (MIT) | |

### Phase 2 — 数据库

| 任务 | 说明 |
|------|------|
| 2.1 实现 SQLAlchemy Base + engine + session | `database.py` |
| 2.2 实现所有 Model | api_credentials / usage_snapshots / notification_channels / notification_logs / settings |
| 2.3 实现 `init_db()` 启动时自动建表 | `create_all()` |
| 2.4 实现 API Key 加密存储 | 使用 `cryptography.fernet` 加密 |
| 2.5 编写 DB 初始化 seed 数据（可选） | 方便开发测试 |

### Phase 3 — OpenAI Provider

| 任务 | 说明 |
|------|------|
| 3.1 实现 `BaseProviderAdapter` 抽象基类 | `adapters/base.py` |
| 3.2 实现 `OpenAIAdapter` | `adapters/openai.py`，基于 Phase 0 验证的 API |
| 3.3 实现 `ProviderRegistry` | `adapters/registry.py` |
| 3.4 实现 `UsageFetcher` service | 调用 Adapter → 写入 UsageSnapshot |
| 3.5 实现 Credential API | CRUD endpoints for api_credentials |
| 3.6 实现定时同步（APScheduler） | 每小时自动同步所有 active 的 credentials |

### Phase 4 — Dashboard

| 任务 | 说明 |
|------|------|
| 4.1 搭建 Next.js 基础页面 | Layout + Navbar + 路由 |
| 4.2 实现 ApiCard 组件 | 余额 / 进度条 / 24h+7d 消耗 / 预测 / 颜色标签 |
| 4.3 实现 Dashboard 首页 | 卡片网格 + 添加 Key 入口 |
| 4.4 实现 Metrics API | `GET /api/credentials/{id}/metrics` |
| 4.5 实现 History API | `GET /api/credentials/{id}/history` |
| 4.6 实现 UsageTrendChart 组件 | Recharts 折线图，7d / 30d 切换 |
| 4.7 实现 AddCredential 表单 | 前端表单 + 调用 POST API |
| 4.8 实现 Settings 页面基础结构 | |

### Phase 5 — 通知系统

| 任务 | 说明 |
|------|------|
| 5.1 实现 `BaseNotifier` 抽象基类 | `notifiers/base.py` |
| 5.2 实现 Email Notifier | SMTP + HTML 模板 |
| 5.3 实现 Telegram Notifier | Bot API |
| 5.4 实现飞书 Notifier | Webhook |
| 5.5 实现企业微信 Notifier | Webhook |
| 5.6 实现预警检查逻辑 | `check_alerts()` + 状态机 + 去重 |
| 5.7 实现通知渠道 CRUD API | |
| 5.8 实现设置页面前端 | 通知渠道管理 + 测试发送 |

### Phase 6 — Claude Provider

| 任务 | 说明 |
|------|------|
| 6.1 实现 `ClaudeAdapter` | `adapters/claude.py` |
| 6.2 注册到 ProviderRegistry | |
| 6.3 前端添加 Claude 选项 | AddCredential 表单 + Card 展示 |
| 6.4 端到端测试 Claude 同步流程 | |

### Phase 7 — DeepSeek Provider

| 任务 | 说明 |
|------|------|
| 7.1 实现 `DeepSeekAdapter` | `adapters/deepseek.py` |
| 7.2 注册 + 前端接入 | |

### Phase 8 — GLM Provider

| 任务 | 说明 |
|------|------|
| 8.1 实现 `GLMAdapter` | `adapters/glm.py` |
| 8.2 注册 + 前端接入 | |

### Phase 9 — 开源发布

| 任务 | 说明 |
|------|------|
| 9.1 后端单元测试 (pytest) | Adapter / Predictor / Notifier 核心逻辑测试 |
| 9.2 前端组件测试 | |
| 9.3 端到端集成测试 | Docker Compose 环境完整流程测试 |
| 9.4 完善 README | 功能说明 + 截图 + 部署指南 + 开发者指南 + FAQ |
| 9.5 添加 `CONTRIBUTING.md` | |
| 9.6 添加 GitHub Issue / PR 模板 | |
| 9.7 创建 GitHub Release v1.0.0 | |
| 9.8 准备社区推广内容 | |

---

## 13. 目录结构

```
api-sentinel/
├── docker-compose.yml
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── .gitignore
├── .dockerignore
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                 # FastAPI 入口，注册路由与启动事件
│   │   ├── config.py               # 配置管理（环境变量 + settings 表）
│   │   ├── database.py             # SQLAlchemy engine & session
│   │   ├── models.py               # 所有 SQLAlchemy 模型
│   │   ├── schemas.py              # 所有 Pydantic schemas
│   │   ├── crypto.py               # API Key 加密/解密工具
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # BaseProviderAdapter + StandardUsageData
│   │   │   ├── registry.py         # ProviderRegistry
│   │   │   ├── openai.py
│   │   │   ├── claude.py
│   │   │   ├── deepseek.py
│   │   │   └── glm.py
│   │   ├── notifiers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # BaseNotifier
│   │   │   ├── email.py
│   │   │   ├── telegram.py
│   │   │   ├── feishu.py
│   │   │   └── wecom.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── fetcher.py          # Usage 抓取核心逻辑
│   │   │   ├── predictor.py        # 消耗计算与预测
│   │   │   └── alerter.py          # 预警检查与通知触发
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── credentials.py
│   │   │   ├── notifications.py
│   │   │   ├── settings.py
│   │   │   └── health.py
│   │   └── scheduler.py            # APScheduler 配置与任务注册
│   ├── data/                       # SQLite 数据文件目录 (volume mount)
│   └── tests/
│       ├── test_adapters.py
│       ├── test_predictor.py
│       └── test_notifier.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx            # Dashboard 首页
│   │   │   └── settings/
│   │   │       └── page.tsx        # 设置页
│   │   ├── components/
│   │   │   ├── Navbar.tsx
│   │   │   ├── ApiCard.tsx
│   │   │   ├── ApiCardGrid.tsx
│   │   │   ├── UsageTrendChart.tsx
│   │   │   ├── AddCredentialForm.tsx
│   │   │   ├── NotificationChannelList.tsx
│   │   │   └── AddChannelForm.tsx
│   │   ├── lib/
│   │   │   └── api.ts              # fetch 封装，统一调用 Backend
│   │   └── types/
│   │       └── index.ts            # TypeScript 类型定义
│   └── public/
│
└── scripts/                        # Phase 0 验证脚本
    ├── verify_openai.py
    ├── verify_claude.py
    ├── verify_deepseek.py
    └── verify_glm.py
```

---

## 14. 环境变量

| 变量 | 说明 | 默认值 |
|------|------|------|
| `ENCRYPTION_KEY` | API Key 加密密钥（Fernet key） | 首次启动自动生成 |
| `DATABASE_PATH` | SQLite 文件路径 | `data/api_sentinel.db` |
| `SYNC_INTERVAL_MINUTES` | 默认同步间隔 | `60` |
| `DATA_RETENTION_DAYS` | 历史数据保留天数 | `90` |
| `BACKEND_PORT` | FastAPI 监听端口 | `8000` |
| `FRONTEND_PORT` | Next.js 监听端口 | `3000` |

---

## 15. MVP 完成标准

Phase 0 ~ 6 完成后，项目应达到以下状态：

- [ ] `docker compose up -d` 一键启动
- [ ] 浏览器打开 `http://localhost:3000` 可见 Dashboard
- [ ] 可添加 OpenAI + Claude API Key
- [ ] 系统自动每小时同步 Usage 数据
- [ ] Dashboard 显示余额、24h 消耗、7d 平均、预计耗尽时间
- [ ] 额度接近耗尽时通过配置的通知渠道发送预警
- [ ] 通知去重正常（同等级不重复发送）
- [ ] 消耗趋势折线图可正常展示
- [ ] 设置页面可管理通知渠道与同步间隔
- [ ] README 完整，新用户可在 5 分钟内完成部署
