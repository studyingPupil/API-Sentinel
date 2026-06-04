"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

const CHANNEL_TYPES = [
  { value: "email", label: "Email (SMTP)" },
  { value: "telegram", label: "Telegram Bot" },
  { value: "feishu", label: "Feishu Webhook" },
  { value: "wecom", label: "WeCom Webhook" },
];

const PLACEHOLDERS: Record<string, string> = {
  telegram: '{"bot_token":"123456:abc","chat_id":"789"}',
  feishu: '{"webhook_url":"https://open.feishu.cn/open-apis/bot/v2/hook/xxx"}',
  wecom: '{"webhook_url":"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"}',
};

interface EmailProvider {
  value: string;
  label: string;
  smtp_host: string;
  smtp_port: number;
}

interface Props {
  onAdded: () => void;
}

export default function AddChannelForm({ onAdded }: Props) {
  const [type, setType] = useState("email");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Email-specific state
  const [emailProviders, setEmailProviders] = useState<EmailProvider[]>([]);
  const [emailProvider, setEmailProvider] = useState("qq");
  const [emailUser, setEmailUser] = useState("");
  const [emailPassword, setEmailPassword] = useState("");
  const [emailTo, setEmailTo] = useState("");
  const [customHost, setCustomHost] = useState("");
  const [customPort, setCustomPort] = useState("587");

  // Generic JSON state for non-email channels
  const [genericConfig, setGenericConfig] = useState(
    PLACEHOLDERS.telegram
  );

  useEffect(() => {
    if (type === "email") {
      api.getEmailProviders().then(setEmailProviders).catch(() => {});
    }
  }, [type]);

  function buildEmailConfig(): string {
    const cfg: Record<string, unknown> = {
      provider_type: emailProvider,
      username: emailUser,
      password: emailPassword,
      to_email: emailTo || emailUser,
    };
    if (emailProvider === "custom") {
      cfg.smtp_host = customHost;
      cfg.smtp_port = parseInt(customPort) || 587;
    }
    return JSON.stringify(cfg);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const configJson =
        type === "email" ? buildEmailConfig() : genericConfig;

      await api.addChannel({
        channel_type: type,
        config_json: configJson,
      });
      // Reset form
      setEmailUser("");
      setEmailPassword("");
      setEmailTo("");
      setCustomHost("");
      setCustomPort("587");
      onAdded();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed");
    }
    setLoading(false);
  }

  const isCustom = emailProvider === "custom";

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      {/* Channel Type */}
      <div>
        <label className="text-xs text-gray-500">Channel Type</label>
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          className="w-full border rounded px-3 py-1.5 text-sm mt-1"
        >
          {CHANNEL_TYPES.map((c) => (
            <option key={c.value} value={c.value}>
              {c.label}
            </option>
          ))}
        </select>
      </div>

      {/* Email-specific fields */}
      {type === "email" && (
        <>
          <div>
            <label className="text-xs text-gray-500">
              Email Provider
            </label>
            <select
              value={emailProvider}
              onChange={(e) => setEmailProvider(e.target.value)}
              className="w-full border rounded px-3 py-1.5 text-sm mt-1"
            >
              {emailProviders.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                  {p.smtp_host ? ` (${p.smtp_host}:${p.smtp_port})` : ""}
                </option>
              ))}
            </select>
          </div>

          {isCustom && (
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs text-gray-500">
                  SMTP Host
                </label>
                <input
                  type="text"
                  value={customHost}
                  onChange={(e) => setCustomHost(e.target.value)}
                  placeholder="smtp.example.com"
                  className="w-full border rounded px-3 py-1.5 text-sm mt-1"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500">
                  SMTP Port
                </label>
                <input
                  type="number"
                  value={customPort}
                  onChange={(e) => setCustomPort(e.target.value)}
                  className="w-full border rounded px-3 py-1.5 text-sm mt-1"
                />
              </div>
            </div>
          )}

          <div>
            <label className="text-xs text-gray-500">
              Email Address
            </label>
            <input
              type="email"
              value={emailUser}
              onChange={(e) => setEmailUser(e.target.value)}
              placeholder="you@qq.com"
              className="w-full border rounded px-3 py-1.5 text-sm mt-1"
            />
          </div>

          <div>
            <label className="text-xs text-gray-500">
              Auth Code / Password
            </label>
            <input
              type="password"
              value={emailPassword}
              onChange={(e) => setEmailPassword(e.target.value)}
              placeholder="SMTP authorization code"
              className="w-full border rounded px-3 py-1.5 text-sm mt-1"
            />
            <p className="text-xs text-gray-400 mt-0.5">
              Not your email login password. Use the SMTP auth code
              from your email provider settings.
            </p>
          </div>

          <div>
            <label className="text-xs text-gray-500">
              Recipient (optional, defaults to sender)
            </label>
            <input
              type="email"
              value={emailTo}
              onChange={(e) => setEmailTo(e.target.value)}
              placeholder="alerts@example.com"
              className="w-full border rounded px-3 py-1.5 text-sm mt-1"
            />
          </div>
        </>
      )}

      {/* Non-email: raw JSON config */}
      {type !== "email" && (
        <div>
          <label className="text-xs text-gray-500">Config (JSON)</label>
          <textarea
            value={genericConfig}
            onChange={(e) => setGenericConfig(e.target.value)}
            rows={4}
            className="w-full border rounded px-3 py-1.5 text-sm mt-1 font-mono"
          />
        </div>
      )}

      {error && (
        <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={
          loading ||
          (type === "email"
            ? !emailUser || !emailPassword
            : !genericConfig)
        }
        className="w-full bg-blue-500 text-white py-1.5 rounded text-sm hover:bg-blue-600 disabled:opacity-50"
      >
        {loading ? "Adding..." : "Add Channel"}
      </button>
    </form>
  );
}
