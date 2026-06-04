# GitHub Actions Output Example / 输出示例

First run after Fork / Fork 后首次运行:

```
======================================================================
  API Sentinel — GitHub Actions Check
  2026-06-04 14:00:00 UTC
======================================================================

[deepseek] Fetching... / 获取数据...
  Balance / 余额: CNY 6.93
  avg_24h: 2.314   avg_7d: 1.8462   predicted: 3.75 days   status: ok
  Alert: L1 — SENDING / 发送中...
  Email sent: 1809345139@qq.com -> 1809345139@qq.com via smtp.qq.com:587

[openai] Fetching... / 获取数据...
  Balance / 余额: USD 45.20
  avg_24h: 3.20   avg_7d: 2.80   predicted: 16.14 days   status: ok

[claude] Skipped — no API key configured / 未配置密钥

======================================================================
  CHECK COMPLETE / 检查完成
  Providers: 2 checked   Alerts: 1 sent
  Dashboard: https://alex.github.io/api-sentinel/
======================================================================
```

## Email Content / 邮件内容预览

```
Subject: [API Sentinel] DeepSeek (Test Key) — Low Balance / 额度不足

Your DeepSeek API key "Test Key" will run out around 2026-06-08
(approx. 3.8 days).

DeepSeek API Key "Test Key" 预计在 2026-06-08 左右耗尽
(约 3.8 天)。

Remaining / 剩余: CNY 6.93
Daily avg / 日均消耗: CNY 1.85

— API Sentinel
```

## data.json Example / 数据文件示例

```json
{
  "providers": {
    "deepseek": {
      "alias": "Test Key",
      "currency": "CNY",
      "snapshots": [
        {
          "fetched_at": "2026-06-04T14:00:00+00:00",
          "total_credits": 0.0,
          "used_credits": 0.0,
          "remaining_credits": 6.93,
          "currency": "CNY"
        }
      ],
      "metrics": {
        "avg_24h": null,
        "avg_7d": null,
        "predicted_days": null,
        "predicted_date": null,
        "status": "insufficient_data"
      }
    }
  },
  "alerts_sent": {},
  "updated_at": "2026-06-04T14:00:00+00:00",
  "deploy_url": "https://alex.github.io/api-sentinel/"
}
```
