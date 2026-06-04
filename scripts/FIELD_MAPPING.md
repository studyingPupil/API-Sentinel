# Phase 0 — Provider API Field Mapping Summary

> 各 Provider Usage/Billing API 的端点、响应格式与 StandardUsageData 字段映射关系

---

## 摘要

| Provider | Billing API 状态 | 认证方式 | 可直接映射到 StandardUsageData |
|----------|-----------------|---------|-------------------------------|
| **OpenAI** | 完整可用 | 普通 API Key（需 billing 权限） | 是 |
| **Claude (Anthropic)** | 可用 (Public Beta) | **Admin API Key** (sk-ant-admin...) | 是（Enterprise 方案更完整） |
| **DeepSeek** | 可用 | 普通 API Key | **部分** — 只返回余额，无总额度 |
| **GLM (智谱)** | ⚠️ 待验证 | 普通 API Key | ⚠️ 待确认 |

---

## OpenAI

### 推荐端点

| 端点 | Method | 用途 |
|------|--------|------|
| `/v1/dashboard/billing/subscription` | GET | 获取订阅信息，返回 `hard_limit_usd`, `soft_limit_usd`, 计划类型 |
| `/v1/dashboard/billing/usage?start_date=X&end_date=Y` | GET | 获取累计使用量，`total_usage` 以**美分**为单位 |

### 备用端点

| 端点 | Method | 用途 |
|------|--------|------|
| `/v1/usage?date=YYYY-MM-DD` | GET | 获取 Token 用量明细（无金额信息） |

### 字段映射

```
Billing Subscription Response:
  subscription.hard_limit_usd     → StandardUsageData.total_credits
  subscription.soft_limit_usd     → (软限额，可能高于 hard_limit)

Billing Usage Response:
  billing.total_usage / 100.0     → StandardUsageData.used_credits       (美分→美元)

计算:
  total_credits - used_credits    → StandardUsageData.remaining_credits
  "USD"                           → StandardUsageData.currency
```

### 注意事项

- `total_usage` 单位是**美分**（如 `3550` = $35.50），必须除以 100
- 某些 API Key 没有 billing 权限（非 Owner/Admin 角色），会返回 404
- `hard_limit_usd` 是硬限额，超过后 API 调用会失败
- `soft_limit_usd` 是软限额，超过后会收到邮件提醒但仍可调用

---

## Claude (Anthropic)

### 推荐端点（Public Beta）

| 端点 | Method | 用途 |
|------|--------|------|
| `/v1/organizations/spend_limits/effective` | GET | Enterprise 方案：获取支出限额 + 周期已花费 |
| `/v1/organizations/cost_report` | GET | 获取美元成本报告（按工作区分组） |
| `/v1/organizations/usage_report/messages` | GET | Token 消耗报告（按模型/时间分组） |

### 字段映射（Enterprise Spend Limits 路径）

```
Spend Limits Response:
  data[].amount / 100.0                   → StandardUsageData.total_credits    (美分→美元)
  data[].period_to_date_spend             → StandardUsageData.used_credits     (已是美元)
  计算: total - used                      → StandardUsageData.remaining_credits
  data[].currency                         → StandardUsageData.currency
```

### 字段映射（Cost Report 路径，非 Enterprise）

```
Cost Report Response:
  汇总所有 data 的 total_cost              → StandardUsageData.used_credits
  ⚠️ 无总额度字段                          → total_credits = 0（仅显示已消耗金额）
```

### 注意事项

- **必须使用 Admin API Key**（`sk-ant-admin...` 前缀），普通 API Key（`sk-ant-api...`）无法访问
- Admin Key 创建路径：Console → Settings → Admin Keys
- `spend_limits/effective` 仅 Enterprise 方案可用，Pro/Max 方案需查看 Console
- `cost_report` 返回数据可能有 5 分钟延迟
- 金额格式：Admin API 中 amount 是**美分**（`"50000"` = $500.00），period_to_date_spend 已是美元
- `cost_report` 需指定 `starting_at`, `ending_at`, `group_by[]` 参数
- 数据保留 365 天

---

## DeepSeek

### 可用端点

| 端点 | Method | 用途 |
|------|--------|------|
| `/user/balance` | GET | 获取账户余额 |

### 响应格式

```json
{
  "is_available": true,
  "balance_infos": [
    {
      "currency": "CNY",
      "total_balance": "110.00",
      "granted_balance": "10.00",
      "topped_up_balance": "100.00"
    }
  ]
}
```

### 字段映射

```
Balance Response:
  balance_infos[0].total_balance          → StandardUsageData.remaining_credits
  balance_infos[0].currency               → StandardUsageData.currency

⚠️ 以下字段 DeepSeek 不提供：
  total_credits                           → 设为 0.0（无总额度概念）
  used_credits                            → 设为 0.0（需通过历史快照差值计算）
```

### 注意事项

- **DeepSeek 只返回当前账户余额，不返回总额度或已使用金额**
- 余额类型：`total_balance` = 充值余额 + 赠送余额；`granted_balance` 有有效期
- `is_available: false` 不代表余额为 0，可能账户未开通按量付费
- 试用期 30 天，到期自动冻结（余额显示不变但无法使用）
- **Impact on Dashboard**：进度条功能不可用（无法计算 xx%），只能显示剩余金额
- 历史消耗 = 上次余额快照 - 本次余额快照（通过两次快照差值累计算）
- 充值余额永不过期，赠送余额有有效期

---

## GLM (智谱 AI)

### ⚠️ 状态：待验证

智谱开放平台的 Billing/Account API 端点尚未通过公开文档确认。

### 已知信息

- 基础 URL：`https://open.bigmodel.cn`
- 认证方式：`Authorization: Bearer {api_key}`（API Key 格式可能为 `{id}.{secret}` JWT 风格）
- 已验证的推理端点：`/api/paas/v4/chat/completions`
- 账户管理通过 Web 控制台（非 API）

### 待测试端点列表（已在 verify_glm.py 中覆盖）

```
GET  /api/paas/v4/user/info
GET  /api/paas/v4/account/info
GET  /api/paas/v4/account/balance
GET  /api/paas/v4/account/resource
POST /api/paas/v4/account/resources
GET  /api/paas/v4/billing/info
GET  /api/paas/v4/billing/usage
GET  /api/paas/v4/user/usage
GET  /api/paas/v4/user/balance
GET  /api/platform/v4/account/info
GET  /api/platform/v4/account/usage
GET  /api/account/v1/info
GET  /api/billing/v1/balance
POST /api/paas/v4/token/usage/query
GET  /api/platform/v1/user/info
GET  /api/platform/v1/account/balance
GET  /api/platform/v1/billing/overview
```

### 运行验证

```bash
export GLM_API_KEY=your-api-key
pip install httpx python-dotenv
python scripts/verify_glm.py
```

如果以上端点全部返回 404，说明智谱当前没有公开的 Billing REST API，需要在 Adapter 中采取备选方案（如手动输入额度）。

---

## StandardUsageData 最终定义

```python
@dataclass
class StandardUsageData:
    total_credits: float       # 总额度（OpenAI/Claude 提供，DeepSeek=0）
    used_credits: float        # 已使用金额（OpenAI/Claude 提供，DeepSeek 通过快照差值计算）
    remaining_credits: float   # 剩余额度（所有 Provider 均可获取）
    currency: str = "USD"      # 货币类型（OpenAI/Claude=USD, DeepSeek=CNY）
    fetched_at: str = ""       # ISO 8601 时间戳
```

### 各 Provider 的实现差异

| 字段 | OpenAI | Claude (Admin) | DeepSeek | GLM |
|------|--------|---------------|----------|-----|
| total_credits | `hard_limit_usd` | `amount/100` | **0.0** (不提供) | ⚠️ |
| used_credits | `total_usage/100` | `period_to_date_spend` | **快照差值计算** | ⚠️ |
| remaining_credits | `total - used` | `total - used` | `total_balance` | ⚠️ |
| currency | USD | USD | CNY | ⚠️ |

### Adapter 实现优先级

```
1. 优先使用 Billing API（返回金额）
2. 回退到 Usage API（返回 Token 用量，需模型定价表换算）
3. 最终回退到 "手动模式"（用户手动输入额度）
```

---

## Phase 0 结论

| Provider | 结论 | V1 可用性 |
|----------|------|-----------|
| **OpenAI** | Billing API 完整可用 | Phase 3 直接开发 |
| **Claude** | Admin API Key 可用，Enterprise 方案更完整 | Phase 6 开发（需处理 Pro/Max 方案差异） |
| **DeepSeek** | Balance API 可用，但只有余额 | Phase 7 开发（进度条功能降级） |
| **GLM** | 待实际 API Key 验证 | Phase 8 开发前需重新验证 |

### 下一步 (Phase 1)

- [ ] 用户使用真实 API Key 运行 4 个验证脚本，确认结果
- [ ] 根据实际 API 响应更新字段映射
- [ ] 开始 Phase 1：项目骨架初始化
