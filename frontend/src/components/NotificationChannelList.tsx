"use client";

import { useState } from "react";
import type { NotificationChannel } from "@/types";
import { api } from "@/lib/api";

const CHANNEL_LABELS: Record<string, string> = {
  email: "Email",
  telegram: "Telegram",
  feishu: "Feishu",
  wecom: "WeCom",
};

interface Props {
  channels: NotificationChannel[];
  onUpdate: () => void;
}

export default function NotificationChannelList({ channels, onUpdate }: Props) {
  const [testingId, setTestingId] = useState<number | null>(null);

  async function handleDelete(id: number) {
    if (!confirm("Delete this notification channel?")) return;
    await api.deleteChannel(id);
    onUpdate();
  }

  async function handleToggle(ch: NotificationChannel) {
    await api.updateChannel(ch.id, { enabled: !ch.enabled });
    onUpdate();
  }

  async function handleTest(id: number) {
    setTestingId(id);
    try {
      const result = await api.testChannel(id);
      alert(result.message);
    } catch {
      alert("Test failed. Check your channel config and server logs.");
    }
    setTestingId(null);
  }

  if (channels.length === 0) {
    return (
      <p className="text-sm text-gray-400">
        No notification channels configured yet.
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {channels.map((ch) => (
        <div
          key={ch.id}
          className="flex items-center justify-between rounded border border-gray-200 bg-white px-4 py-3"
        >
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium">
              {CHANNEL_LABELS[ch.channel_type] || ch.channel_type}
            </span>
            <button
              onClick={() => handleToggle(ch)}
              className={`text-xs px-2 py-0.5 rounded ${
                ch.enabled
                  ? "bg-green-100 text-green-700"
                  : "bg-gray-100 text-gray-500"
              }`}
            >
              {ch.enabled ? "On" : "Off"}
            </button>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleTest(ch.id)}
              disabled={testingId === ch.id}
              className="text-xs text-blue-500 hover:text-blue-700 disabled:text-gray-300"
            >
              {testingId === ch.id ? "..." : "Test"}
            </button>
            <button
              onClick={() => handleDelete(ch.id)}
              className="text-xs text-red-400 hover:text-red-600"
            >
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
